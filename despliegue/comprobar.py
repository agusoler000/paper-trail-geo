# -*- coding: utf-8 -*-
"""Chequeo previo: dice EXACTAMENTE que falta para que el diario salga solo.

    python despliegue/comprobar.py            # revisa todo
    python despliegue/comprobar.py --rapido   # saltea lo que tarda (modelos, red)

Sale 0 si el sistema puede producir un video hoy, 1 si falta algo. Pensado para correr en el VPS
antes de la primera vez, y para que el vigilante lo use cuando algo se rompe.
"""
import os
import shutil
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(BASE)
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "videos", "DAILY"))
sys.path.insert(0, os.path.join(RAIZ, "videos", "DAILY", "presentador"))

VERDE, ROJO, AMAR, FIN = "\033[0;32m", "\033[0;31m", "\033[0;33m", "\033[0m"
if os.name == "nt" or not sys.stdout.isatty():
    VERDE = ROJO = AMAR = FIN = ""

_fallas, _avisos = [], []


def ok(q, extra=""):
    print("  %sOK%s   %-46s %s" % (VERDE, FIN, q, extra))


def falla(q, arreglo):
    print("  %sFALTA%s %-46s %s" % (ROJO, FIN, q, arreglo))
    _fallas.append((q, arreglo))


def aviso(q, nota):
    print("  %s..%s   %-46s %s" % (AMAR, FIN, q, nota))
    _avisos.append((q, nota))


def titulo(t):
    print("\n== %s" % t)


def cargar_env():
    """Delega en radar/entorno.py: un solo lugar que lee el .env, para que comprobar.py y
    daily.py vean EXACTAMENTE lo mismo. Tenerlo por duplicado fue lo que escondio el bug del DSN."""
    from radar import entorno
    entorno.cargar()


def main(rapido=False):
    cargar_env()

    titulo("sistema")
    print("  python %s" % sys.version.split()[0])
    ok("ffmpeg", shutil.which("ffmpeg") or "") if shutil.which("ffmpeg") else \
        falla("ffmpeg", "apt-get install -y ffmpeg")
    nucleos = os.cpu_count() or 1
    (ok if nucleos >= 4 else aviso)("nucleos", "%d (el render usa %d workers)" % (nucleos, max(1, min(3, nucleos - 2))))
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/meminfo") as fh:
                mi = {l.split(":")[0]: int(l.split()[1]) for l in fh if ":" in l}
            libre = mi.get("MemAvailable", 0) / 1048576.0
            swap = mi.get("SwapTotal", 0) / 1048576.0
            ok("RAM disponible", "%.1f GB" % libre)
            if swap >= 2:
                ok("swap", "%.1f GB" % swap)
            else:
                falla("swap", "sudo bash despliegue/instalar.sh  (sin swap el render puede tumbar Supabase y n8n)")
        except Exception:
            pass
        libres = shutil.disk_usage(RAIZ).free / 1073741824.0
        (ok if libres > 15 else falla)("disco libre", "%.0f GB" % libres) if libres > 15 else \
            falla("disco libre", "%.0f GB — un dia de cuadros pide ~8 GB" % libres)

    titulo("dependencias de Python")
    for mod, arreglo in (("numpy", "pip install numpy"), ("PIL", "pip install pillow"),
                         ("jsonschema", "pip install jsonschema"), ("sqlalchemy", "pip install sqlalchemy"),
                         ("fastembed", "pip install fastembed"), ("piper", "pip install piper-tts"),
                         ("mcp", "pip install mcp"),
                         ("googleapiclient", "pip install google-api-python-client google-auth-oauthlib")):
        try:
            __import__(mod)
            ok(mod)
        except ImportError:
            falla(mod, arreglo)

    titulo("claves")
    # La UNICA imprescindible. Sin esta no hay guion ni extraccion, y no hay video.
    if os.environ.get("OPENCODE_API_KEY"):
        ok("OPENCODE_API_KEY", "presente (%d chars)" % len(os.environ["OPENCODE_API_KEY"]))
    else:
        falla("OPENCODE_API_KEY", "ponela en %s/.env — sin esta no hay video" % RAIZ)
    # OPCIONAL: es solo la red de la cascada. Y OJO: la suscripcion de Claude Code NO es una
    # clave de API — son productos distintos y la API se paga por token aparte. Sin esta clave
    # el sistema funciona igual; si OpenCode se agota, la etapa falla y avisa el vigilante,
    # que es mejor que gastar plata sin que nadie se entere.
    if os.environ.get("ANTHROPIC_API_KEY"):
        ok("ANTHROPIC_API_KEY", "presente — la cascada tiene red")
    else:
        aviso("ANTHROPIC_API_KEY", "sin definir: OPCIONAL. Es la red si OpenCode se agota. "
                                   "Sin ella el sistema anda igual, pero ese dia no hay video.")
    if os.environ.get("RADAR_DSN"):
        ok("RADAR_DSN", os.environ["RADAR_DSN"].split("@")[-1])
    else:
        aviso("RADAR_DSN", "sin definir: se usa SQLite. Anda, pero el agrupamiento es mas lento")

    titulo("modelos y assets")
    voces = os.path.join(RAIZ, "voz", "piper")
    faltan = [v for v in ("A_ryan", "B_joe", "C_alan")
              if not os.path.exists(os.path.join(voces, v + ".onnx"))]
    if faltan:
        falla("voces de Piper", "python videos/DAILY/voz.py --bajar  (faltan: %s)" % ", ".join(faltan))
    else:
        ok("voces de Piper", "A_ryan · B_joe · C_alan")
    for k in "ABC":
        p = os.path.join(RAIZ, "videos", "DAILY", "presentador", "rig_%s.json" % k)
        d = os.path.join(RAIZ, "videos", "DAILY", "presentador", "piezas_%s" % k)
        if os.path.exists(p) and os.path.isdir(d) and len(os.listdir(d)) >= 6:
            ok("rig %s" % k, "%d piezas" % len(os.listdir(d)))
        else:
            falla("rig %s" % k, "python videos/DAILY/presentador/rig.py cortar %s" % k)
    if not rapido:
        try:
            from fastembed import TextEmbedding
            TextEmbedding("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
            ok("modelo de embeddings", "en cache")
        except Exception as e:
            falla("modelo de embeddings", "se baja solo la primera vez (%s)" % type(e).__name__)

    titulo("YouTube")
    tok = os.path.join(RAIZ, "radar", "_yt_token.json")
    if os.path.exists(tok):
        ok("token de YouTube", "presente")
    else:
        falla("token de YouTube", "python videos/DAILY/subir.py --autorizar  (una sola vez)")

    titulo("base de datos")
    try:
        from radar import almacen as A
        al = A.conectar(os.environ.get("RADAR_DSN"))
        al.init_esquema()
        n = len(al.fuentes(solo_activas=False))
        if n == 0:
            n = al.cargar_fuentes(os.path.join(RAIZ, "radar", "fuentes.json"))
        if al.pg:
            ok("motor de la base", "Postgres con pgvector (indice HNSW)")
        else:
            falla("motor de la base",
                  "esta usando SQLite: agrupar 3.000 articulos NO va a terminar. "
                  "Falta RADAR_DSN en .env")
        ok("base accesible", "%d fuentes cargadas" % n)
        activas = len([f for f in al.fuentes(solo_activas=True)])
        (ok if activas > 60 else aviso)("fuentes activas", "%d de %d" % (activas, n))
    except Exception as e:
        falla("base de datos", "%s: %s" % (type(e).__name__, str(e)[:70]))

    if not rapido:
        titulo("red (una fuente de cada bloque)")
        try:
            from radar import ingesta
            import json as _j
            reg = _j.load(open(os.path.join(RAIZ, "radar", "fuentes.json"), encoding="utf-8"))
            por_id = {f["id"]: f for f in reg["feeds"]}
            for fid in ("bbc_world", "gn_reuters", "tass_en", "aljazeera", "infobae"):
                if fid not in por_id:
                    continue
                arts, err = ingesta.leer_feed(por_id[fid], timeout=20)
                (ok if not err else aviso)(fid, "%d articulos" % len(arts) if not err else err)
        except Exception as e:
            aviso("red", "%s" % type(e).__name__)

    titulo("modulos")
    fallos_mod = []
    for m in ("radar/ingesta.py", "radar/semantica.py", "radar/agrupar.py", "radar/puntajes.py",
              "videos/DAILY/escena.py", "videos/DAILY/voz.py", "videos/DAILY/daily.py"):
        r = subprocess.run([sys.executable, os.path.join(RAIZ, m), "--autotest"],
                           capture_output=True, cwd=RAIZ, timeout=600)
        if r.returncode == 0:
            ok(os.path.basename(m), "autotest en verde")
        else:
            fallos_mod.append(m)
            falla(os.path.basename(m), "autotest en rojo: python %s --autotest" % m)

    print("\n" + "=" * 72)
    if _fallas:
        print("%sFALTAN %d COSAS%s para que el diario salga solo:" % (ROJO, len(_fallas), FIN))
        for i, (q, a) in enumerate(_fallas, 1):
            print("  %d. %-34s -> %s" % (i, q, a))
    else:
        print("%sTODO LISTO.%s El sistema puede producir un video hoy." % (VERDE, FIN))
        print("  Primera corrida sin publicar nada:")
        print("    python videos/DAILY/daily.py --correr $(date -u +%F) --solo recolectar")
    if _avisos:
        print("\n%sAvisos%s (no bloquean):" % (AMAR, FIN))
        for q, n in _avisos:
            print("  · %-34s %s" % (q, n))
    return 1 if _fallas else 0


if __name__ == "__main__":
    sys.exit(main("--rapido" in sys.argv))
