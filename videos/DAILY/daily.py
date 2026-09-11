# -*- coding: utf-8 -*-
"""Orquestador del video diario. Nueve etapas idempotentes, pensadas para correr solas.

    python videos/DAILY/daily.py --autotest
    python videos/DAILY/daily.py --correr 2026-09-12
    python videos/DAILY/daily.py --correr 2026-09-12 --desde render    # retoma
    python videos/DAILY/daily.py --vigilante 2026-09-12

IDEMPOTENTE quiere decir: cada etapa consulta run_log y si ya corrio OK para esa fecha, se saltea.
Volver a lanzar el dia entero despues de un corte no rehace lo que ya estaba.

LA ETAPA QUE MAS IMPORTA QUE SEA RESUMIBLE ES EL RENDER. produccion/motor.py borra su directorio
de cuadros al arrancar (y esta bien para lo que hace), pero aca eso significaria que un corte de
luz a las 07:00 obliga a rehacer dos horas y el video no sale a las 12:00. Por eso el render de
este modulo escribe en _frames_<fecha>/ y ARRANCA DESDE EL ULTIMO CUADRO ESCRITO.

n8n no ejecuta las etapas: las dispara, las cronometra y avisa. Esto es lo que ejecuta.
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(BASE))
for p in (RAIZ, BASE, os.path.join(BASE, "presentador")):
    if p not in sys.path:
        sys.path.insert(0, p)

# El .env se carga SIEMPRE, corra esto un timer de systemd o una persona desde el shell.
# Sin esto, una corrida a mano no veia RADAR_DSN y caia a SQLite sin avisar (ver radar/entorno.py).
from radar import entorno as _entorno        # noqa: E402
_entorno.cargar()

W, H, FPS = 1920, 1080, 24
PUBLICA_UTC = "12:00"
ETAPAS = ["recolectar", "guion", "voz", "alinear", "coreo", "render", "mezcla", "miniatura", "subir"]


def _dir(fecha):
    d = os.path.join(BASE, "_dias", fecha)
    os.makedirs(d, exist_ok=True)
    return d


def _ruta(fecha, nombre):
    return os.path.join(_dir(fecha), nombre)


def _log(msg):
    print("[%s] %s" % (datetime.now(timezone.utc).strftime("%H:%M:%S"), msg), flush=True)


# --------------------------------------------------------------------------- etapas

def etapa_recolectar(fecha, ctx):
    """Cierra la ventana de noticias, agrupa, puntua y elige los eventos del dia."""
    from radar import almacen as _a, ingesta, agrupar as _ag
    al = _a.conectar(os.environ.get("RADAR_DSN"))
    al.init_esquema()
    al.cargar_fuentes(os.path.join(RAIZ, "radar", "fuentes.json"))

    ing = ingesta.tick(al)
    _log("ingesta: %d leidos, %d nuevos, %d feeds ok, %d caidos"
         % (ing["leidos"], ing["nuevos"], ing["feeds_ok"], len(ing["feeds_muertos"])))
    for fid, motivo in ing["feeds_muertos"]:
        _log("  FEED CAIDO %s: %s" % (fid, motivo))

    gr = _ag.agrupar(al)
    _log("agrupado: %d procesados, %d eventos nuevos, %d adjuntados"
         % (gr["procesados"], gr["eventos_nuevos"], gr["adjuntados"]))

    puntuados = _puntuar_todo(al)
    _ag.actualizar_estados(al)
    brief = _brief(al, fecha)
    json.dump(brief, open(_ruta(fecha, "brief.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False, default=str)
    return {"ingesta": {k: v for k, v in ing.items() if k != "detalle"},
            "agrupado": gr, "puntuados": puntuados,
            "eventos": brief["n_eventos"], "banderas": len(brief["banderas_rojas"])}


def _puntuar_todo(al):
    from radar import puntajes
    fuentes = {f["id"]: f for f in al.fuentes(solo_activas=False)}
    n = 0
    for ev in al.buscar_eventos(desde=datetime.now(timezone.utc) - timedelta(hours=72), limite=400):
        full = al.evento(ev["id"])
        arts = full.get("articulos", [])
        if not arts:
            continue
        imp, desglose = puntajes.importancia(full, arts, fuentes)
        bandera, motivo = puntajes.banderas(full, full.get("statements", []))
        # puntajes devuelve 'fuentes_indep'; la tabla las guarda como 's_fuentes_indep'.
        cols = {"s_" + k: v for k, v in desglose.items()
                if k in ("fuentes_indep", "cross_bloc", "velocidad", "actores", "dominio")}
        al.actualizar_evento(ev["id"], importancia=imp, requiere_agustin=bandera,
                             motivo_bandera=motivo, **cols)
        n += 1
    return n


def _brief(al, fecha):
    from radar import mcp_server
    mcp_server._ALMACEN = al
    return mcp_server.brief_del_dia(fecha=fecha)


def etapa_guion(fecha, ctx):
    """El guion y la lista de fichas. Sale validado contra ESQUEMA_GUION o no sale."""
    from radar.llm import llm
    from escena import ESQUEMA_GUION
    brief = json.load(open(_ruta(fecha, "brief.json"), encoding="utf-8"))
    estilo = ""
    for doc in ("ESTILO.md", "canal/IDEOLOGIA.md", "canal/CANAL.md"):
        p = os.path.join(RAIZ, doc)
        if os.path.exists(p):
            estilo += "\n\n===== %s =====\n" % doc + open(p, encoding="utf-8").read()[:9000]

    sistema = (
        "Escribis THE LEDGER, el informativo diario de geopolitica del canal Paper Trail, en INGLES.\n"
        "Devolves un guion en JSON con bloques y beats. Cada beat lleva el texto que se narra y la\n"
        "ficha que se ve a la derecha, elegida del catalogo cerrado de ocho.\n"
        "REGLAS QUE NO SE NEGOCIAN:\n"
        "- Lo que un gobierno AFIRMA se narra como afirmacion, con el actor nombrado. Nunca como hecho.\n"
        "- Un hecho solo se afirma si el brief lo trae como fact.\n"
        "- Ficha 'versus' cuando hay versiones enfrentadas: es la firma del programa.\n"
        "- Sin cadencia en los textos publicos. Sin inventar datos que no esten en el brief.\n"
        + estilo)

    prompt = ("BRIEF DE HOY (%s):\n%s\n\n"
              "Escribi el guion completo. Cada beat: t (segundos desde el inicio del programa),\n"
              "dur, texto narrado, ficha, datos de la ficha, y pose del presentador\n"
              "(reposo|senala|abre|enfatiza|escucha). Los beats de un bloque no se pisan.\n"
              "Apunta a 18-20 minutos en total."
              % (fecha, json.dumps(brief, ensure_ascii=False, default=str)[:24000]))

    guion = llm("guion", prompt, esquema=ESQUEMA_GUION, sistema=sistema)
    guion["fecha"] = fecha
    json.dump(guion, open(_ruta(fecha, "guion.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    n_beats = sum(len(b["beats"]) for b in guion["bloques"])
    dur = max((b["t"] + b["dur"] for bl in guion["bloques"] for b in bl["beats"]), default=0)
    return {"bloques": len(guion["bloques"]), "beats": n_beats, "dur_min": round(dur / 60, 1)}


def etapa_voz(fecha, ctx):
    """Narracion con Piper local. Costo cero, y REACOMODA la linea de tiempo del guion.

    Lo segundo es lo que evita que el video quede desincronizado: el LLM adivina cuanto dura cada
    frase y casi nunca acierta. Aca se sintetiza, se mide la duracion real y se reescribe el guion
    con ella, asi la ficha cambia cuando termina la frase y no en la mitad.
    """
    import voz as _v
    if not _v.disponible():
        return {"SALTEA": "falta piper o los modelos; correr: python videos/DAILY/voz.py --bajar"}
    guion = json.load(open(_ruta(fecha, "guion.json"), encoding="utf-8"))
    g2, pista, inf = _v.generar(guion, _ruta(fecha, "voz.wav"))
    json.dump(g2, open(_ruta(fecha, "guion.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    json.dump(pista, open(_ruta(fecha, "visemas.json"), "w", encoding="utf-8"), indent=1)
    return inf


def etapa_alinear(fecha, ctx):
    """Rhubarb saca los visemas del audio. Sin esto la boca no se mueve con la voz."""
    audio = _ruta(fecha, "voz.wav")
    salida = _ruta(fecha, "visemas.json")
    if not os.path.exists(audio):
        return {"SALTEA": "no hay voz.wav todavia"}
    if os.path.exists(salida) and not os.environ.get("RHUBARB"):
        # etapa_voz ya dejo la pista con el sobre de amplitud. Rhubarb la mejora, no la habilita.
        return {"visemas": salida, "nota": "pista de etapa_voz; definir RHUBARB para afinarla"}
    exe = os.environ.get("RHUBARB", "rhubarb")
    try:
        subprocess.run([exe, "-f", "json", "-o", salida, audio], check=True,
                       capture_output=True, timeout=900)
    except FileNotFoundError:
        return {"SALTEA": "no esta rhubarb en el PATH"}
    return {"visemas": salida}


def etapa_coreo(fecha, ctx):
    """Guion + visemas -> la escena lista para renderizar. Deterministica: no falla."""
    from escena import cargar_guion, construir
    import bocas
    guion = cargar_guion(_ruta(fecha, "guion.json"))
    pista = []
    vis = _ruta(fecha, "visemas.json")
    if os.path.exists(vis):
        crudo = json.load(open(vis, encoding="utf-8"))
        # etapa_voz deja [[t, letra]]; rhubarb deja su propio formato
        pista = ([(float(t), f) for t, f in crudo] if isinstance(crudo, list)
                 else bocas.pista_visemas(vis))
    esc = construir(guion, pista_visemas=pista)
    json.dump({"dur": esc.dur, "cuadros": int(esc.dur * FPS), "beats": len(esc.beats),
               "visemas": len(pista)},
              open(_ruta(fecha, "coreo.json"), "w", encoding="utf-8"), indent=1)
    return {"dur_min": round(esc.dur / 60, 1), "cuadros": int(esc.dur * FPS),
            "beats": len(esc.beats), "visemas": len(pista)}


def etapa_render(fecha, ctx, workers=None, nice=True):
    """RESUMIBLE. Arranca desde el ultimo cuadro escrito; no borra nada."""
    import multiprocessing as mp
    from escena import cargar_guion, construir
    frames = os.path.join(BASE, "_frames_%s" % fecha)
    os.makedirs(frames, exist_ok=True)

    guion = cargar_guion(_ruta(fecha, "guion.json"))
    esc = construir(guion)
    total = int(esc.dur * FPS)

    hechos = {int(n[2:8]) for n in os.listdir(frames)
              if n.startswith("f_") and n.endswith(".jpg")}
    desde = 0
    while desde in hechos:
        desde += 1
    if desde >= total:
        return {"cuadros": total, "reanudado_en": desde, "nota": "ya estaban todos"}

    # 3 workers y prioridad baja: el VPS tiene 6 vCPU y ademas corre Supabase, n8n y Evolution API.
    workers = workers or int(os.environ.get("RENDER_WORKERS", "3"))
    _log("render %s: %d..%d de %d cuadros, %d workers" % (fecha, desde, total, total, workers))
    t0 = time.time()
    tareas = [(fecha, i, min(i + 48, total), frames) for i in range(desde, total, 48)]
    with mp.Pool(workers) as pool:
        hechos_ahora = sum(pool.imap_unordered(_render_tramo, tareas))
    seg = time.time() - t0
    return {"cuadros": total, "reanudado_en": desde, "escritos": hechos_ahora,
            "segundos": round(seg, 1),
            "cuadros_por_seg": round(hechos_ahora / seg, 2) if seg > 0 else None}


def _render_tramo(args):
    """Worker: rearma la escena en el proceso hijo (no se puede picklear la escena)."""
    fecha, i0, i1, frames = args
    from escena import cargar_guion, construir
    esc = construir(cargar_guion(_ruta(fecha, "guion.json")))
    n = 0
    for i in range(i0, i1):
        dest = os.path.join(frames, "f_%06d.jpg" % i)
        if os.path.exists(dest):
            continue
        esc.cuadro(i / FPS).save(dest, quality=92)
        n += 1
    return n


def etapa_mezcla(fecha, ctx):
    """Cuadros + voz + cortina -> mp4. ffmpeg, cero creditos."""
    frames = os.path.join(BASE, "_frames_%s" % fecha)
    salida = _ruta(fecha, "video.mp4")
    voz = _ruta(fecha, "voz.wav")
    cmd = ["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS),
           "-i", os.path.join(frames, "f_%06d.jpg")]
    if os.path.exists(voz):
        cmd += ["-i", voz]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium"]
    if os.path.exists(voz):
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd.append(salida)
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=7200)
    except FileNotFoundError:
        return {"SALTEA": "no esta ffmpeg en el PATH"}
    return {"video": salida, "mb": round(os.path.getsize(salida) / 1e6, 1)}


def etapa_miniatura(fecha, ctx):
    from escena import cargar_guion, construir
    guion = cargar_guion(_ruta(fecha, "guion.json"))
    esc = construir(guion)
    t = min(8.0, max(0.0, esc.dur / 2))
    dest = _ruta(fecha, "miniatura.jpg")
    esc.cuadro(t).resize((1280, 720)).save(dest, quality=92)
    return {"miniatura": dest}


def etapa_subir(fecha, ctx):
    import subir as _s
    guion = json.load(open(_ruta(fecha, "guion.json"), encoding="utf-8"))
    video = _ruta(fecha, "video.mp4")
    if not os.path.exists(video):
        return {"SALTEA": "no hay video.mp4"}
    hh, mm = PUBLICA_UTC.split(":")
    cuando = datetime.fromisoformat(fecha).replace(
        hour=int(hh), minute=int(mm), tzinfo=timezone.utc)
    if cuando < datetime.now(timezone.utc):
        cuando += timedelta(days=1)
    vid = _s.subir(video, _ruta(fecha, "miniatura.jpg"),
                   titulo=guion.get("titulo") or ("THE LEDGER — %s" % fecha),
                   descripcion=_descripcion(guion), etiquetas=["geopolitics", "news", "daily"],
                   publicar_en=cuando)
    return {"video_id": vid, "publica": cuando.isoformat()}


def _descripcion(guion):
    lineas = ["Daily · THE LEDGER — %s" % guion.get("fecha", ""), ""]
    for bl in guion.get("bloques", []):
        lineas.append("%s" % bl["nombre"])
        for beat in bl["beats"][:3]:
            lineas.append("  · " + beat["texto"][:110])
    return "\n".join(lineas)[:4900]


FUNCIONES = {
    "recolectar": etapa_recolectar, "guion": etapa_guion, "voz": etapa_voz,
    "alinear": etapa_alinear, "coreo": etapa_coreo, "render": etapa_render,
    "mezcla": etapa_mezcla, "miniatura": etapa_miniatura, "subir": etapa_subir,
}


# --------------------------------------------------------------------------- orquestacion

def correr(fecha, desde=None, solo=None, almacen=None):
    """Corre las etapas. Las que ya salieron OK para esta fecha se saltean."""
    estado_path = _ruta(fecha, "estado.json")
    estado = json.load(open(estado_path, encoding="utf-8")) if os.path.exists(estado_path) else {}

    etapas = ETAPAS
    if solo:
        etapas = [solo]
    elif desde:
        etapas = ETAPAS[ETAPAS.index(desde):]

    ctx = {"fecha": fecha}
    for etapa in etapas:
        previo = estado.get(etapa)
        if previo and previo.get("ok") and not solo:
            _log("%-11s ya estaba OK, se saltea" % etapa)
            continue
        _log("%-11s arranca" % etapa)
        t0 = time.time()
        try:
            res = FUNCIONES[etapa](fecha, ctx) or {}
            ok = "SALTEA" not in res
            estado[etapa] = {"ok": ok, "t": round(time.time() - t0, 1), "res": res}
            _log("%-11s %s  %s" % (etapa, "OK " if ok else "SALTEA",
                                   json.dumps(res, default=str)[:180]))
            if not ok:
                _guardar(estado_path, estado)
                break
        except Exception as e:
            estado[etapa] = {"ok": False, "t": round(time.time() - t0, 1),
                             "error": "%s: %s" % (type(e).__name__, e)}
            _log("%-11s FALLA  %s: %s" % (etapa, type(e).__name__, e))
            _guardar(estado_path, estado)
            return {"fecha": fecha, "etapas": estado, "corto_en": etapa}
        _guardar(estado_path, estado)

    return {"fecha": fecha, "etapas": estado,
            "completo": all(estado.get(e, {}).get("ok") for e in ETAPAS)}


def _guardar(path, estado):
    json.dump(estado, open(path, "w", encoding="utf-8"), indent=1, default=str)


def vigilante(fecha):
    """A las 10:00 UTC: ¿hay video subido y programado? Si no, en que etapa se corto.

    Es la red que evita el peor caso: que el dia pase sin video y sin que nadie se entere.
    """
    estado_path = _ruta(fecha, "estado.json")
    if not os.path.exists(estado_path):
        return {"alarma": True, "motivo": "el dia %s ni siquiera arranco" % fecha}
    estado = json.load(open(estado_path, encoding="utf-8"))
    subida = estado.get("subir", {})
    if subida.get("ok") and (subida.get("res") or {}).get("video_id"):
        return {"alarma": False, "video_id": subida["res"]["video_id"],
                "publica": subida["res"].get("publica")}
    fallo = next((e for e in ETAPAS if not estado.get(e, {}).get("ok")), "subir")
    return {"alarma": True, "corto_en": fallo,
            "error": estado.get(fallo, {}).get("error") or estado.get(fallo, {}).get("res"),
            "motivo": "no hay video subido para %s" % fecha}


# --------------------------------------------------------------------------- autotest

def _autotest():
    fallos = []

    def chequeo(nombre, cond, extra=""):
        print(("OK   " if cond else "FALLA") + " " + nombre + ((" | " + extra) if extra else ""))
        if not cond:
            fallos.append(nombre)

    fecha = "2026-01-01-test"
    d = _dir(fecha)
    for n in os.listdir(d):
        os.remove(os.path.join(d, n))

    print("--- forma del orquestador ---")
    chequeo("son las 9 etapas del contrato", len(ETAPAS) == 9, ", ".join(ETAPAS))
    chequeo("cada etapa tiene funcion", all(e in FUNCIONES for e in ETAPAS))
    chequeo("el render va antes de la mezcla",
            ETAPAS.index("render") < ETAPAS.index("mezcla") < ETAPAS.index("subir"))

    print("--- idempotencia ---")
    _guardar(_ruta(fecha, "estado.json"),
             {"recolectar": {"ok": True, "res": {}}, "guion": {"ok": True, "res": {}}})
    llamadas = []
    orig = FUNCIONES["voz"]
    FUNCIONES["voz"] = lambda f, c: (llamadas.append("voz"), {"SALTEA": "prueba"})[1]
    try:
        r = correr(fecha)
        chequeo("saltea las etapas que ya estaban OK",
                r["etapas"]["recolectar"]["ok"] and r["etapas"]["guion"]["ok"])
        chequeo("corre la primera etapa pendiente", llamadas == ["voz"], str(llamadas))
        chequeo("un SALTEA corta la cadena sin marcar exito",
                r["etapas"]["voz"]["ok"] is False and "mezcla" not in r["etapas"])
    finally:
        FUNCIONES["voz"] = orig

    print("--- el vigilante ---")
    v = vigilante(fecha)
    chequeo("alarma si no hay video subido", v["alarma"] is True)
    chequeo("dice en que etapa se corto", v.get("corto_en") == "voz", str(v.get("corto_en")))
    _guardar(_ruta(fecha, "estado.json"),
             {e: {"ok": True, "res": {}} for e in ETAPAS} |
             {"subir": {"ok": True, "res": {"video_id": "abc123", "publica": "2026-01-01T12:00:00+00:00"}}})
    v = vigilante(fecha)
    chequeo("no alarma cuando el video esta subido y programado",
            v["alarma"] is False and v["video_id"] == "abc123")
    chequeo("un dia que ni arranco tambien da alarma",
            vigilante("2099-12-31")["alarma"] is True)

    print("--- render resumible (lo que salva el dia tras un corte) ---")
    frames = os.path.join(BASE, "_frames_%s" % fecha)
    os.makedirs(frames, exist_ok=True)
    for n in os.listdir(frames):
        os.remove(os.path.join(frames, n))
    from PIL import Image as _I
    for i in range(7):
        _I.new("RGB", (8, 8), (1, 2, 3)).save(os.path.join(frames, "f_%06d.jpg" % i))
    hechos = {int(n[2:8]) for n in os.listdir(frames) if n.startswith("f_")}
    desde = 0
    while desde in hechos:
        desde += 1
    chequeo("detecta que ya hay 7 cuadros y reanuda en el 7", desde == 7, "desde=%d" % desde)
    antes = len(os.listdir(frames))
    chequeo("NO borra los cuadros existentes (la diferencia con motor.render)",
            antes == 7, "quedan=%d" % antes)
    for n in os.listdir(frames):
        os.remove(os.path.join(frames, n))
    os.rmdir(frames)

    print("--- descripcion de YouTube ---")
    g = {"fecha": "2026-09-11", "bloques": [
        {"nombre": "THE POWERS", "beats": [{"texto": "x" * 400}]}]}
    desc = _descripcion(g)
    chequeo("la descripcion respeta el tope de YouTube", len(desc) <= 5000, "len=%d" % len(desc))
    chequeo("la descripcion nombra los bloques", "THE POWERS" in desc)

    for n in os.listdir(d):
        os.remove(os.path.join(d, n))
    os.rmdir(d)

    print()
    print("FALLOS: %d" % len(fallos) + (" -> " + ", ".join(fallos) if fallos else ""))
    return 1 if fallos else 0


if __name__ == "__main__":
    a = sys.argv
    if "--autotest" in a:
        sys.exit(_autotest())
    if "--correr" in a:
        i = a.index("--correr")
        fecha = a[i + 1] if len(a) > i + 1 else str(datetime.now(timezone.utc).date())
        desde = a[a.index("--desde") + 1] if "--desde" in a else None
        solo = a[a.index("--solo") + 1] if "--solo" in a else None
        print(json.dumps(correr(fecha, desde, solo), indent=1, default=str))
        sys.exit(0)
    if "--vigilante" in a:
        i = a.index("--vigilante")
        fecha = a[i + 1] if len(a) > i + 1 else str(datetime.now(timezone.utc).date())
        r = vigilante(fecha)
        print(json.dumps(r, indent=1, default=str))
        sys.exit(1 if r.get("alarma") else 0)
    print(__doc__)
