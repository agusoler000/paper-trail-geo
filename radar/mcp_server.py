# -*- coding: utf-8 -*-
"""Servidor MCP del Radar: le da a Claude acceso hablado a los acontecimientos.

    python radar/mcp_server.py --autotest     # prueba las herramientas sin levantar el servidor
    python radar/mcp_server.py                # arranca por stdio (es como lo consume Claude)

Registrarlo:
    claude mcp add --transport stdio -s user radar -- python C:/.../radar/mcp_server.py

Ocho herramientas, no quince. Con quince el modelo duda entre get_events_by_country y
search_events y a veces llama a la peor; con ocho bien parametrizadas elige bien. Cada una
devuelve SIEMPRE las urls originales: el sistema existe para poder citar la fuente, no para
reemplazarla.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(BASE))

from radar import entorno as _entorno       # noqa: E402
_entorno.cargar()

_ALMACEN = None


def tipo_fuente(f):
    """almacen normaliza a source_type; fuentes.json trae 'tipo'. Aceptamos los dos."""
    return (f or {}).get("source_type") or (f or {}).get("tipo")


def almacen():
    global _ALMACEN
    if _ALMACEN is None:
        from radar import almacen as _a
        _ALMACEN = _a.conectar(os.environ.get("RADAR_DSN"))
    return _ALMACEN


def _desde(horas=None, dias=None):
    if horas is None and dias is None:
        return None
    h = (horas or 0) + (dias or 0) * 24
    return datetime.now(timezone.utc) - timedelta(hours=h)


def _ev_corto(ev):
    return {
        "event_id": ev.get("id"), "titulo": ev.get("titulo"),
        "importancia": ev.get("importancia"), "video_score": ev.get("video_score"),
        "estado": ev.get("estado"),
        "paises": ev.get("paises") or [], "actores": ev.get("actores") or [],
        "topics": ev.get("topics") or [],
        "actualizado": str(ev.get("last_updated") or ""),
        "requiere_agustin": bool(ev.get("requiere_agustin")),
        "motivo_bandera": ev.get("motivo_bandera"),
        "n_articulos": ev.get("n_articulos"),
    }


# --------------------------------------------------------------------------- las 8 herramientas

def search_events(pais=None, region=None, actor=None, topic=None, horas=None, dias=None,
                  min_importancia=None, min_video_score=None, estado=None, limite=25):
    """Busca acontecimientos. Reemplaza a get_breaking / by_country / by_topic / video_opportunities.

    estado: breaking | developing | watchlist | closed
    """
    evs = almacen().buscar_eventos(
        pais=pais, actor=actor, topic=topic, desde=_desde(horas, dias),
        min_importancia=min_importancia, min_video=min_video_score,
        estado=estado, limite=limite)
    if region:
        from radar.puntajes import REGIONES
        paises = set(REGIONES.get(region.lower(), []))
        if paises:
            evs = [e for e in evs if paises & set(e.get("paises") or [])]
    return {"n": len(evs), "eventos": [_ev_corto(e) for e in evs]}


def get_event(event_id):
    """Ficha completa: cronologia, hechos, afirmaciones, narrativas y TODAS las fuentes."""
    ev = almacen().evento(int(event_id))
    if not ev:
        return {"error": "no existe el evento %s" % event_id}
    arts = sorted(ev.get("articulos", []),
                  key=lambda a: a.get("published_at") or a.get("detected_at") or "")
    sts = ev.get("statements", [])
    return {
        **_ev_corto(ev),
        "riesgo_escalada": ev.get("riesgo_escalada"),
        "desglose_importancia": {k: ev.get(k) for k in
                                 ("s_fuentes_indep", "s_cross_bloc", "s_velocidad",
                                  "s_actores", "s_dominio") if ev.get(k) is not None},
        "cronologia": [{"cuando": str(a.get("published_at") or a.get("detected_at")),
                        "medio": a.get("source_id"), "titular": a.get("title"),
                        "url": a.get("url")} for a in arts],
        "hechos": [_st(s) for s in sts if s.get("tipo") == "fact"],
        "afirmaciones": [_st(s) for s in sts if s.get("tipo") == "claim"],
        "disputado": [_st(s) for s in sts if s.get("tipo") == "disputed"],
        "narrativas": ev.get("narrativas", []),
        "fuentes": [{"medio": a.get("source_id"), "titular": a.get("title"),
                     "fecha": str(a.get("published_at") or ""), "url": a.get("url"),
                     "wire": a.get("wire_origin")} for a in arts],
    }


def _st(s):
    return {"texto": s.get("texto"), "actor": s.get("actor"),
            "evidencia": s.get("evidence"), "fuentes_independientes": s.get("n_indep"),
            "article_ids": s.get("article_ids") or []}


def search_news(q=None, source_type=None, lang=None, horas=24, limite=40):
    """Articulos sueltos, sin agrupar. Para cuando hace falta el detalle crudo."""
    arts = almacen().articulos(desde=_desde(horas), limite=600)
    fuentes = {f["id"]: f for f in almacen().fuentes(solo_activas=False)}
    if q:
        term = q.lower()
        arts = [a for a in arts if term in (a.get("title") or "").lower()]
    if source_type:
        arts = [a for a in arts
                if tipo_fuente(fuentes.get(a.get("source_id"))) == source_type]
    if lang:
        arts = [a for a in arts if a.get("lang") == lang]
    arts = arts[:limite]
    return {"n": len(arts), "articulos": [
        {"titular": a.get("title"), "medio": fuentes.get(a.get("source_id"), {}).get("nombre",
                                                                                    a.get("source_id")),
         "perspectiva": tipo_fuente(fuentes.get(a.get("source_id"))),
         "fecha": str(a.get("published_at") or ""), "url": a.get("url"),
         "wire": a.get("wire_origin"), "event_id": a.get("event_id")} for a in arts]}


def compare_narratives(event_id):
    """Como cuenta el mismo hecho cada bloque, y —lo mas revelador— que omite cada uno."""
    ev = almacen().evento(int(event_id))
    if not ev:
        return {"error": "no existe el evento %s" % event_id}
    nas = ev.get("narrativas", [])
    return {
        "event_id": ev.get("id"), "titulo": ev.get("titulo"),
        "bloques_presentes": sorted({n.get("bloque") for n in nas}),
        "narrativas": [{"bloque": n.get("bloque"), "resumen": n.get("resumen"),
                        "enfasis": n.get("enfasis"), "omite": n.get("omite"),
                        "article_ids": n.get("article_ids") or []} for n in nas],
        "aviso": ("El sistema no dice cual narrativa es verdadera. Dice quien afirma que. "
                  "Para saber que esta respaldado, mira get_evidence."),
    }


def get_evidence(event_id, tipo=None):
    """Hechos, afirmaciones o versiones en disputa. tipo: fact | claim | disputed."""
    ev = almacen().evento(int(event_id))
    if not ev:
        return {"error": "no existe el evento %s" % event_id}
    sts = ev.get("statements", [])
    if tipo:
        sts = [s for s in sts if s.get("tipo") == tipo]
    por_actor = {}
    for s in sts:
        if s.get("tipo") in ("claim", "disputed") and s.get("actor"):
            por_actor.setdefault(s["actor"], []).append(s.get("texto"))
    return {
        "event_id": ev.get("id"), "titulo": ev.get("titulo"),
        "hechos": [_st(s) for s in sts if s.get("tipo") == "fact"],
        "afirmaciones_por_actor": por_actor,
        "disputado": [_st(s) for s in sts if s.get("tipo") == "disputed"],
        "regla": ("fact = 2+ fuentes independientes (wire_origin distintos) o documento oficial "
                  "del propio actor. Un fact con una sola fuente no existe: es claim."),
    }


def get_sources(source_type=None):
    """Estado de salud de los feeds. Sirve para saber si falta una perspectiva HOY."""
    fs = almacen().fuentes(solo_activas=False)
    if source_type:
        fs = [f for f in fs if tipo_fuente(f) == source_type]
    activas = [f for f in fs if f.get("activa")]
    caidas = [f for f in fs if not f.get("activa")]
    por_tipo = {}
    for f in activas:
        k = tipo_fuente(f)
        por_tipo[k] = por_tipo.get(k, 0) + 1
    return {
        "activas": len(activas), "caidas": len(caidas),
        "por_perspectiva": por_tipo,
        "caidas_detalle": [{"id": f["id"], "nombre": f.get("nombre"), "perspectiva": tipo_fuente(f),
                            "ultimo_error": f.get("ultimo_error"),
                            "fallos_seguidos": f.get("fallos_seguidos")} for f in caidas],
        "aviso": ("La perspectiva de una fuente NO dice si es veraz. Sirve para detectar "
                  "narrativas y para saber si falta un bloque."),
    }


def brief_del_dia(fecha=None, limite=30, min_importancia=40):
    """El insumo del video diario: los acontecimientos repartidos por bloque, CON los minutos de hoy.

    Los tiempos no son fijos: salen de videos/DAILY/escaleta.py segun el peso real del dia.
    Un dia de guerra en Oriente Medio le da 6 minutos a ese bloque; uno tranquilo, 1:30.
    """
    sys.path.insert(0, os.path.join(os.path.dirname(BASE), "videos", "DAILY"))
    import escaleta

    evs = almacen().buscar_eventos(desde=_desde(horas=28), min_importancia=min_importancia,
                                   limite=200)
    evs.sort(key=lambda e: -(e.get("importancia") or 0))
    rep = escaleta.repartir(evs)

    bloques = {}
    for b in escaleta.ORDEN_VARIABLE:
        d = rep["bloques"][b]
        propios = rep["eventos_por_bloque"].get(b, [])[:8]
        bloques[b] = {"minutos": d["minutos"], "presentador": d["presentador"],
                      "eventos": [_ev_corto(e) for e in propios]}

    banderas = [e for e in evs if e.get("requiere_agustin")]
    return {
        "fecha": fecha or str(datetime.now(timezone.utc).date()),
        "duracion_objetivo_min": rep["total_min"],
        "n_eventos": sum(len(v["eventos"]) for v in bloques.values()),
        "bloques": bloques,
        "banderas_rojas": [{"event_id": e["id"], "titulo": e.get("titulo"),
                            "motivo": e.get("motivo_bandera")} for e in banderas],
        "publica_solo": not banderas,
    }


def marcar(event_id, estado=None, video_score=None, nota=None):
    """Escribe: descartar, mandar a watchlist, aprobar para video. Es como el sistema aprende."""
    campos = {}
    if estado:
        campos["estado"] = estado
    if video_score is not None:
        campos["video_score"] = int(video_score)
    if nota:
        campos["motivo_bandera"] = nota
    if not campos:
        return {"error": "nada que marcar"}
    almacen().actualizar_evento(int(event_id), **campos)
    return {"ok": True, "event_id": int(event_id), "cambios": campos}


HERRAMIENTAS = [search_events, get_event, search_news, compare_narratives,
                get_evidence, get_sources, brief_del_dia, marcar]


# --------------------------------------------------------------------------- servidor

def servir():
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("radar")
    for fn in HERRAMIENTAS:
        mcp.tool(name=fn.__name__, description=(fn.__doc__ or "").strip())(fn)
    mcp.run()


# --------------------------------------------------------------------------- autotest

def _autotest():
    fallos = []

    def chequeo(nombre, cond, extra=""):
        print(("OK   " if cond else "FALLA") + " " + nombre + ((" | " + extra) if extra else ""))
        if not cond:
            fallos.append(nombre)

    print("--- forma del servidor ---")
    chequeo("son 8 herramientas, no 15", len(HERRAMIENTAS) == 8, "n=%d" % len(HERRAMIENTAS))
    chequeo("todas documentadas", all((f.__doc__ or "").strip() for f in HERRAMIENTAS))
    nombres = {f.__name__ for f in HERRAMIENTAS}
    chequeo("estan las del contrato",
            nombres == {"search_events", "get_event", "search_news", "compare_narratives",
                        "get_evidence", "get_sources", "brief_del_dia", "marcar"},
            ", ".join(sorted(nombres)))

    print("--- se registran en el SDK de MCP ---")
    try:
        from mcp.server.fastmcp import FastMCP
        m = FastMCP("radar-test")
        for fn in HERRAMIENTAS:
            m.tool(name=fn.__name__, description=(fn.__doc__ or "").strip())(fn)
        chequeo("FastMCP acepta las 8 sin chistar", True)
    except Exception as e:
        chequeo("FastMCP acepta las 8 sin chistar", False, "%s: %s" % (type(e).__name__, e))

    print("--- contra una base de verdad ---")
    try:
        from radar import almacen as _a
    except Exception as e:
        print("SALTEA: radar/almacen.py todavia no esta (%s)" % type(e).__name__)
        print()
        print("FALLOS: %d" % len(fallos))
        return 1 if fallos else 0

    tmp = os.path.join(BASE, "_mcp_test.db")
    if os.path.exists(tmp):
        os.remove(tmp)
    try:
        global _ALMACEN
        _ALMACEN = _a.conectar("sqlite:///" + tmp.replace("\\", "/"))
        _ALMACEN.init_esquema()
        _ALMACEN.cargar_fuentes(os.path.join(BASE, "fuentes.json"))

        r = get_sources()
        chequeo("get_sources ve las fuentes cargadas", r.get("activas", 0) > 40,
                "activas=%s" % r.get("activas"))
        chequeo("get_sources agrupa por perspectiva", len(r.get("por_perspectiva", {})) >= 5)
        r = search_events(limite=5)
        chequeo("search_events responde con base vacia sin explotar", r.get("n") == 0)
        r = brief_del_dia()
        import sys as _s, os as _o
        _s.path.insert(0, _o.path.join(_o.path.dirname(BASE), "videos", "DAILY"))
        import escaleta as _esc
        chequeo("brief_del_dia devuelve los 7 bloques (con THE MIDDLE EAST)",
                len(r.get("bloques", {})) == len(_esc.ORDEN_VARIABLE) == 7,
                "n=%d" % len(r.get("bloques", {})))
        chequeo("y trae los minutos de HOY, no fijos",
                all("minutos" in v for v in r["bloques"].values())
                and r.get("duracion_objetivo_min", 0) > 15,
                "total=%.1f min" % r.get("duracion_objetivo_min", 0))
        chequeo("brief vacio publica solo (no hay banderas)", r.get("publica_solo") is True)
        r = get_event(999999)
        chequeo("get_event de un id inexistente da error claro, no excepcion", "error" in r)
    except Exception as e:
        chequeo("la ronda contra base real corre", False, "%s: %s" % (type(e).__name__, e))
    finally:
        _ALMACEN = None
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass

    print()
    print("FALLOS: %d" % len(fallos) + (" -> " + ", ".join(fallos) if fallos else ""))
    return 1 if fallos else 0


if __name__ == "__main__":
    if "--autotest" in sys.argv:
        sys.exit(_autotest())
    servir()
