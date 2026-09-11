# -*- coding: utf-8 -*-
"""Extraccion: de un cluster de articulos a hechos, afirmaciones y narrativas.

    python radar/extraccion.py --autotest

ESTA ES LA PIEZA EDITORIAL DEL SISTEMA. La decision de diseno que la sostiene:

    EL MODELO NO DECIDE QUE ES UN HECHO. El modelo extrae PROPOSICIONES con su atribucion;
    el codigo de aca abajo cuenta fuentes independientes y decide la etiqueta.

Por que: si la distincion hecho/afirmacion vive en un prompt, un martes cualquiera el modelo
devuelve "Rusia derribo 20 drones" como hecho y nadie se entera hasta que sale al aire. Si vive en
codigo, con el conteo de wire_origin distintos, no se puede romper sin romper un test.

Las reglas, de RADAR.md §5:
  fact      >=2 wire_origin DISTINTOS que lo reportan como reporte propio, O una fuente primaria
            oficial del actor que lo hizo (evidence='official_doc')
  claim     todo lo demas que alguien afirma -> se guarda CON el actor que lo dice
  disputed  dos claims sobre la misma proposicion con valores incompatibles

Un `fact` con una sola fuente independiente NO EXISTE. Es un claim con esa redaccion como actor.
"""
import json
import os
import re
import sys
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
_RAIZ = os.path.dirname(BASE)
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

BLOQUES = ["western", "russian", "russian_ind", "chinese", "arab", "israeli",
           "iranian", "ukrainian", "osint", "official", "latam", "apac"]

# Verbos de atribucion: si la proposicion viene con uno, es afirmacion, no hecho.
VERBOS_ATRIBUCION = re.compile(
    r"\b(says?|said|claims?|claimed|alleges?|alleged|asserts?|announced|denies|denied|"
    r"reports?|reported|accus\w+|according to|insists?|maintains?|"
    r"dice|dijo|afirma|afirmo|asegura|aseguro|niega|nego|denuncia|denuncio|segun)\b", re.I)

EVIDENCIAS = ["official_doc", "satellite", "own_reporting", "osint", "none"]


def tipo_fuente(f):
    """almacen normaliza a source_type; fuentes.json trae 'tipo'. Aceptamos los dos."""
    return (f or {}).get("source_type") or (f or {}).get("tipo")

# --------------------------------------------------------------------------- esquema

ESQUEMA_ANALISIS = {
    "type": "object",
    "properties": {
        "titulo": {
            "type": "string",
            "description": "Titulo neutro del acontecimiento, en ingles, sin adjetivos de ningun bando. Max 90 caracteres."
        },
        "paises": {"type": "array", "items": {"type": "string"},
                   "description": "Codigos ISO-3166 alfa-2 en mayusculas de los paises involucrados."},
        "actores": {"type": "array", "items": {"type": "string"},
                    "description": "Actores concretos: gobiernos, ministerios, empresas, organismos."},
        "topics": {"type": "array", "items": {"type": "string"},
                   "description": "De esta lista: military, diplomacy, trade, energy, sanctions, elections, tech, finance, migration, legal."},
        "dominio": {"type": "string",
                    "enum": ["military_escalation", "nuclear", "trade", "energy", "diplomatic",
                             "domestic_politics", "finance", "tech", "other"]},
        "riesgo_escalada": {"type": "string", "enum": ["bajo", "medio", "alto"]},
        "proposiciones": {
            "type": "array",
            "description": "Cada cosa concreta que se afirma sobre el hecho. NO evalues si es verdad.",
            "items": {
                "type": "object",
                "properties": {
                    "texto": {"type": "string", "description": "La proposicion sola, sin el verbo de atribucion. Ej: 'se derribaron 20 drones sobre Belgorod'."},
                    "atribuida_a": {"type": "string", "description": "Quien la afirma. El medio si es reporte propio; el gobierno/ministerio si la afirma un actor. Nunca vacio."},
                    "es_reporte_propio": {"type": "boolean", "description": "true si el medio lo reporta como constatacion propia; false si esta repitiendo lo que dijo otro."},
                    "evidence": {"type": "string", "enum": EVIDENCIAS},
                    "article_ids": {"type": "array", "items": {"type": "integer"}},
                    "clave": {"type": "string", "description": "Identificador corto de QUE se afirma, para juntar versiones incompatibles. Ej: 'drones_derribados_belgorod'."},
                },
                "required": ["texto", "atribuida_a", "es_reporte_propio", "evidence", "article_ids", "clave"],
            },
        },
        "narrativas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "bloque": {"type": "string", "enum": BLOQUES},
                    "resumen": {"type": "string", "description": "Como presenta el hecho este bloque, en una o dos frases."},
                    "enfasis": {"type": "string", "description": "Que destaca."},
                    "omite": {"type": "string", "description": "Que NO menciona. A menudo es lo mas revelador."},
                    "article_ids": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["bloque", "resumen", "article_ids"],
            },
        },
    },
    "required": ["titulo", "paises", "actores", "topics", "dominio", "riesgo_escalada",
                 "proposiciones", "narrativas"],
}

SISTEMA = """Sos el analista de un radar geopolitico. Tu trabajo NO es decidir quien tiene razon.

Tu trabajo es separar, con precision de escribano:
  - QUE se afirma
  - QUIEN lo afirma
  - si el medio lo constata por su cuenta o esta repitiendo lo que dijo otro

Reglas que no se negocian:
1. Si un articulo dice "Rusia afirma que derribo 20 drones", la proposicion es "se derribaron 20
   drones", atribuida_a "Ministerio de Defensa de Rusia", es_reporte_propio=false.
2. Si un articulo dice "nuestro corresponsal vio el humo sobre la refineria", la proposicion es
   "hubo humo sobre la refineria", atribuida_a el medio, es_reporte_propio=true.
3. Un comunicado oficial del propio actor sobre su propia decision (una sancion que publica la
   Comision Europea, una orden ejecutiva en el Federal Register) es evidence='official_doc'.
4. NUNCA escribas una proposicion como si fuera un hecho establecido. No es tu decision.
5. Dos versiones incompatibles del mismo asunto llevan la MISMA `clave`, para poder enfrentarlas.
6. El titulo va en ingles y en tono neutro: ni "agresion" ni "operacion especial".
7. Si un bloque no esta representado entre los articulos, NO inventes su narrativa: omitilo."""


def _prompt(evento, articulos, fuentes):
    lineas = []
    for a in articulos:
        f = fuentes.get(a["source_id"], {})
        lineas.append(
            "[%d] (%s · %s · tier %s%s) %s\n     %s" % (
                a["id"], f.get("nombre", a["source_id"]), tipo_fuente(f) or "?", f.get("tier", "?"),
                " · PRIMARIA" if f.get("primaria") else "",
                a["title"],
                (a.get("raw") or {}).get("descripcion", "")[:280]))
    return (
        "Acontecimiento agrupado a partir de %d articulos.\n\n"
        "ARTICULOS (el numero entre corchetes es su article_id, usalo en article_ids):\n\n%s\n\n"
        "Analizalo segun tus reglas. Extrae TODAS las proposiciones concretas que aparezcan, con su "
        "atribucion. Si dos fuentes dicen cosas incompatibles sobre lo mismo, dales la misma clave."
        % (len(articulos), "\n\n".join(lineas)))


# --------------------------------------------------------------------------- la regla dura

def clasificar_proposiciones(props, articulos, fuentes):
    """De proposiciones del modelo a STATEMENTs etiquetados. ACA vive la regla editorial.

    El modelo no elige la etiqueta. La elige este conteo.
    """
    por_art = {a["id"]: a for a in articulos}
    salida = []
    por_clave = defaultdict(list)

    for p in props:
        ids = [i for i in p.get("article_ids", []) if i in por_art]
        # Fuentes INDEPENDIENTES: wire_origin distintos. Veinte medios con el mismo cable de
        # Reuters son UNO. Un reporte propio cuenta con la identidad del medio.
        firmas = set()
        primaria_oficial = False
        for i in ids:
            a = por_art[i]
            f = fuentes.get(a["source_id"], {})
            firmas.add(a.get("wire_origin") or ("propio:" + a["source_id"]))
            if f.get("primaria") and p.get("evidence") == "official_doc":
                primaria_oficial = True
        n_indep = len(firmas)

        texto = (p.get("texto") or "").strip()
        actor = (p.get("atribuida_a") or "").strip() or None
        propio = bool(p.get("es_reporte_propio"))
        evidencia = p.get("evidence") if p.get("evidence") in EVIDENCIAS else "none"

        # Cinturon y tiradores: si el texto quedo con un verbo de atribucion adentro, el modelo
        # no separo bien y esto no puede ser un hecho, diga lo que diga el resto.
        sospechoso = bool(VERBOS_ATRIBUCION.search(texto))

        if primaria_oficial:
            tipo = "fact"
        elif propio and n_indep >= 2 and not sospechoso:
            tipo = "fact"
        else:
            tipo = "claim"

        if tipo == "claim" and not actor:
            # Un claim sin actor es inutilizable y la base lo rechaza. Si el modelo no lo dio,
            # se atribuye al medio que lo publico.
            actor = (fuentes.get(por_art[ids[0]]["source_id"], {}).get("nombre")
                     if ids else "fuente sin identificar")

        st = {"tipo": tipo, "texto": texto, "actor": None if tipo == "fact" else actor,
              "evidence": evidencia, "n_indep": n_indep, "article_ids": ids,
              "disputa_de": None, "_clave": p.get("clave") or texto[:40]}
        salida.append(st)
        por_clave[st["_clave"]].append(st)

    # Disputas: misma clave, actores distintos, y al menos uno es claim.
    for clave, grupo in por_clave.items():
        if len(grupo) < 2:
            continue
        actores = {g["actor"] for g in grupo if g["actor"]}
        if len(actores) < 2:
            continue
        cabeza = grupo[0]
        for otro in grupo[1:]:
            otro["tipo"] = "disputed" if otro["tipo"] != "fact" else otro["tipo"]
            otro["disputa_de"] = None      # el id real lo pone el almacen al guardar la cabeza
            otro["_disputa_clave"] = clave
        if cabeza["tipo"] != "fact":
            cabeza["tipo"] = "disputed"
    return salida


def analizar_evento(almacen, evento_id, llm=None):
    """Analiza un evento y guarda statements y narrativas. Devuelve el resumen de lo hecho."""
    if llm is None:
        from radar.llm import llm as _llm
        llm = _llm

    ev = almacen.evento(evento_id)
    articulos = ev.get("articulos", [])
    if not articulos:
        return {"evento_id": evento_id, "error": "sin articulos"}
    fuentes = {f["id"]: f for f in almacen.fuentes(solo_activas=False)}

    datos = llm("masivas", _prompt(ev, articulos, fuentes),
                esquema=ESQUEMA_ANALISIS, sistema=SISTEMA)

    statements = clasificar_proposiciones(datos.get("proposiciones", []), articulos, fuentes)

    ids_por_clave = {}
    for st in statements:
        clave = st.pop("_clave", None)
        st.pop("_disputa_clave", None)
        if clave and clave not in ids_por_clave:
            ids_por_clave[clave] = None
        sid = almacen.guardar_statement(evento_id, st)
        if clave and ids_por_clave.get(clave) is None:
            ids_por_clave[clave] = sid

    for na in datos.get("narrativas", []):
        if na.get("bloque") in BLOQUES:
            almacen.guardar_narrativa(evento_id, na)

    almacen.actualizar_evento(
        evento_id,
        titulo=datos.get("titulo") or ev.get("titulo"),
        paises=datos.get("paises", []), actores=datos.get("actores", []),
        topics=datos.get("topics", []), riesgo_escalada=datos.get("riesgo_escalada"))

    n = {"fact": 0, "claim": 0, "disputed": 0}
    for st in statements:
        n[st["tipo"]] = n.get(st["tipo"], 0) + 1
    return {"evento_id": evento_id, "titulo": datos.get("titulo"),
            "statements": n, "narrativas": len(datos.get("narrativas", [])),
            "dominio": datos.get("dominio"), "riesgo_escalada": datos.get("riesgo_escalada")}


# --------------------------------------------------------------------------- autotest

def _autotest():
    fallos = []

    def chequeo(nombre, cond, extra=""):
        print(("OK   " if cond else "FALLA") + " " + nombre + ((" | " + extra) if extra else ""))
        if not cond:
            fallos.append(nombre)

    # Escenario real: el mismo cable de Reuters republicado por tres medios, contra tres medios
    # con reporte propio. Es EL caso que el sistema tiene que distinguir.
    fuentes = {
        "reuters_gn": {"nombre": "Reuters", "tipo": "western", "tier": 1},
        "bbc": {"nombre": "BBC", "tipo": "western", "tier": 1},
        "yahoo": {"nombre": "Yahoo", "tipo": "western", "tier": 3},
        "tass": {"nombre": "TASS", "tipo": "russian", "tier": 2},
        "ukrinform": {"nombre": "Ukrinform", "tipo": "ukrainian", "tier": 3},
        "ec": {"nombre": "European Commission", "tipo": "official", "tier": 1, "primaria": True},
    }
    arts = [
        {"id": 1, "source_id": "reuters_gn", "wire_origin": "reuters", "title": "x"},
        {"id": 2, "source_id": "bbc", "wire_origin": "reuters", "title": "x"},
        {"id": 3, "source_id": "yahoo", "wire_origin": "reuters", "title": "x"},
        {"id": 4, "source_id": "bbc", "wire_origin": None, "title": "y"},
        {"id": 5, "source_id": "ukrinform", "wire_origin": None, "title": "z"},
        {"id": 6, "source_id": "tass", "wire_origin": None, "title": "w"},
        {"id": 7, "source_id": "ec", "wire_origin": None, "title": "v"},
    ]

    props = [
        {"texto": "un ataque alcanzo la refineria de Belgorod", "atribuida_a": "Reuters",
         "es_reporte_propio": True, "evidence": "own_reporting",
         "article_ids": [1, 2, 3], "clave": "ataque_refineria"},
        {"texto": "hubo humo sobre la refineria", "atribuida_a": "BBC",
         "es_reporte_propio": True, "evidence": "own_reporting",
         "article_ids": [4, 5], "clave": "humo_refineria"},
        {"texto": "se derribaron 20 drones ucranianos", "atribuida_a": "Ministerio de Defensa de Rusia",
         "es_reporte_propio": False, "evidence": "none",
         "article_ids": [6], "clave": "drones"},
        {"texto": "los drones alcanzaron su objetivo", "atribuida_a": "Estado Mayor de Ucrania",
         "es_reporte_propio": False, "evidence": "none",
         "article_ids": [5], "clave": "drones"},
        {"texto": "la UE adopto el paquete 19 de sanciones", "atribuida_a": "Comision Europea",
         "es_reporte_propio": True, "evidence": "official_doc",
         "article_ids": [7], "clave": "paquete19"},
    ]

    sts = clasificar_proposiciones(props, arts, fuentes)
    por_clave = {p["clave"]: s for p, s in zip(props, sts)}

    print("--- la regla del doble conteo ---")
    a = por_clave["ataque_refineria"]
    chequeo("3 medios con el MISMO cable de Reuters = 1 fuente independiente -> claim",
            a["n_indep"] == 1 and a["tipo"] == "claim",
            "n_indep=%d tipo=%s" % (a["n_indep"], a["tipo"]))
    chequeo("ese claim conserva su actor", bool(a["actor"]), "actor=%r" % a["actor"])

    b = por_clave["humo_refineria"]
    chequeo("2 medios con reporte PROPIO distinto = 2 independientes -> fact",
            b["n_indep"] == 2 and b["tipo"] == "fact",
            "n_indep=%d tipo=%s" % (b["n_indep"], b["tipo"]))
    chequeo("un fact no lleva actor", b["actor"] is None)

    print("--- afirmaciones y disputas ---")
    ru = sts[2]
    ua = sts[3]
    chequeo("lo que afirma un ministerio nunca es fact", ru["tipo"] in ("claim", "disputed"))
    chequeo("versiones incompatibles quedan marcadas como disputadas",
            ru["tipo"] == "disputed" and ua["tipo"] == "disputed",
            "ru=%s ua=%s" % (ru["tipo"], ua["tipo"]))
    chequeo("cada version conserva quien la dice",
            ru["actor"] and ua["actor"] and ru["actor"] != ua["actor"])

    print("--- fuente primaria oficial ---")
    ec = por_clave["paquete19"]
    chequeo("un comunicado oficial del propio actor es fact con una sola fuente",
            ec["tipo"] == "fact" and ec["evidence"] == "official_doc")

    print("--- cinturon: verbo de atribucion colado en el texto ---")
    sucia = clasificar_proposiciones(
        [{"texto": "Rusia afirma que derribo 20 drones", "atribuida_a": "BBC",
          "es_reporte_propio": True, "evidence": "own_reporting",
          "article_ids": [4, 5], "clave": "sucia"}], arts, fuentes)[0]
    chequeo("si el modelo no separo la atribucion, NO puede salir fact",
            sucia["tipo"] == "claim", "tipo=%s" % sucia["tipo"])

    print("--- el esquema que se le exige al modelo ---")
    try:
        import jsonschema
        jsonschema.Draft202012Validator.check_schema(ESQUEMA_ANALISIS)
        chequeo("ESQUEMA_ANALISIS es un JSON Schema valido", True)
        ejemplo = {"titulo": "t", "paises": ["RU"], "actores": ["a"], "topics": ["military"],
                   "dominio": "military_escalation", "riesgo_escalada": "medio",
                   "proposiciones": props, "narrativas": [
                       {"bloque": "russian", "resumen": "r", "article_ids": [6]}]}
        jsonschema.validate(ejemplo, ESQUEMA_ANALISIS)
        chequeo("una respuesta bien formada valida contra el esquema", True)
        malo = dict(ejemplo, narrativas=[{"bloque": "marciano", "resumen": "r", "article_ids": []}])
        try:
            jsonschema.validate(malo, ESQUEMA_ANALISIS)
            chequeo("un bloque inventado es rechazado", False)
        except jsonschema.ValidationError:
            chequeo("un bloque inventado es rechazado", True)
    except ImportError:
        print("SALTEA: no esta jsonschema")

    print()
    print("FALLOS: %d" % len(fallos) + (" -> " + ", ".join(fallos) if fallos else ""))
    return 1 if fallos else 0


if __name__ == "__main__":
    if "--autotest" in sys.argv:
        sys.exit(_autotest())
    print(__doc__)
