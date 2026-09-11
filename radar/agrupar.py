# -*- coding: utf-8 -*-
"""Agrupa articulos en acontecimientos. Clustering incremental, no k-means.

    python radar/agrupar.py --autotest

Por que incremental y no k-means: no sabemos cuantos acontecimientos hay en el dia, y llegan en
streaming. Por cada articulo nuevo se busca el vecino mas parecido de la ventana; si supera el
umbral, se pega a su evento; si no, abre uno. Es O(1) por articulo con un indice vectorial y no
hay que reprocesar nada cuando entra el articulo 3.001.

Lo que tiene que lograr (el ejemplo de RADAR.md §3):
    Reuters  "US announces new sanctions on Russia"
    BBC      "US imposes new Russia sanctions"
    TASS     "Washington introduces new sanctions against Moscow"
son UN acontecimiento, no tres.
"""
import os
import sys
from datetime import datetime, timedelta, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
_RAIZ = os.path.dirname(BASE)
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

UMBRAL = 0.78          # coseno minimo para considerar que hablan del mismo hecho
VENTANA_HORAS = 72     # no se agrupa contra algo de hace una semana
CORPUS_IDF = 3000      # articulos recientes sobre los que se ajusta el IDF

# Un acontecimiento se cierra si pasa esto sin un articulo nuevo.
HORAS_PARA_CERRAR = 48
HORAS_BREAKING = 6


def _texto_de(art):
    """Titulo + el arranque del extracto. El titulo solo a veces es demasiado corto para separar."""
    desc = (art.get("raw") or {}).get("descripcion") or ""
    return (art.get("title") or "") + " . " + desc[:180]


def agrupar(almacen, ventana=VENTANA_HORAS, limite=4000, consultar_llm=True, max_consultas=80):
    """Asigna evento a cada articulo que todavia no tenga. Devuelve el resumen.

    Tres tramos (radar/semantica.py explica por que, con los numeros medidos):
      puntaje >= 0.60  -> mismo acontecimiento, sin preguntar
      0.35 a 0.60      -> se le pregunta a un modelo Flash (son pocos pares por dia)
      < 0.35           -> acontecimiento nuevo
    Ante la duda, acontecimiento nuevo: partir es barato, fundir dos hechos distintos sale al aire.
    """
    from radar import semantica as sem

    ahora = datetime.now(timezone.utc)
    desde = ahora - timedelta(hours=ventana)

    pendientes = almacen.articulos(sin_evento=True, limite=limite)
    if not pendientes:
        return {"procesados": 0, "eventos_nuevos": 0, "adjuntados": 0, "consultas": 0}

    # El IDF de entidades se calcula sobre el corpus reciente, no sobre el lote: es lo que hace que
    # "Belgorod" pese y "Russia" no. Con un lote chico, todo parece raro y el ancla miente.
    recientes = almacen.articulos(desde=desde, limite=CORPUS_IDF)
    idf = sem.IdfEntidades([a.get("title") or "" for a in recientes] +
                           [a.get("title") or "" for a in pendientes])

    # Orden cronologico: el primero en contar algo abre el evento, los demas se le pegan.
    pendientes.sort(key=lambda a: a.get("published_at") or a.get("detected_at") or ahora)
    vecs = sem.vectorizar([_texto_de(a) for a in pendientes])

    titulo_de = {a["id"]: (a.get("title") or "") for a in recientes}
    nuevos = adjuntados = consultas = 0
    for art, vec in zip(pendientes, vecs):
        titulo_de[art["id"]] = art.get("title") or ""
        # Se pide por debajo del umbral de duda: el ancla puede levantar un candidato flojo.
        vecinos = almacen.vecinos(vec, desde=desde, umbral=sem.UMBRAL_ANCLA, limite=12)
        mejor = None
        for art_id, event_id, base in vecinos:
            if not event_id:
                continue
            anc = idf.ancla(art.get("title") or "", titulo_de.get(art_id, ""))
            # Se ordena por el combinado, pero se DECIDE con la semantica pura + el ancla aparte.
            orden = base + sem.PESO_ANCLA * anc
            if mejor is None or orden > mejor[0]:
                mejor = (orden, event_id, base, anc, art_id)

        pegar = False
        if mejor:
            _, event_id, base, anc, art_id = mejor
            fallo = sem.decidir(base, anc)
            if fallo == "si":
                pegar = True
            elif fallo == "duda" and consultar_llm and consultas < max_consultas:
                consultas += 1
                pegar = sem.mismo_hecho(art.get("title") or "", titulo_de.get(art_id, ""))
            mejor = (event_id,)

        if pegar:
            almacen.adjuntar(mejor[0], art["id"], vec)
            almacen.actualizar_evento(mejor[0], last_updated=ahora)
            adjuntados += 1
        else:
            almacen.crear_evento(art["title"], art["id"], vec)
            nuevos += 1

    res = {"procesados": len(pendientes), "eventos_nuevos": nuevos,
           "adjuntados": adjuntados, "consultas": consultas}
    almacen.registrar("agrupar", ok=True, n_in=len(pendientes), n_out=nuevos + adjuntados)
    return res


def actualizar_estados(almacen, ahora=None):
    """breaking / developing / watchlist / closed segun importancia y cuanto hace que no se mueve.

    DEVELOPING no es 'reciente': es 'la importancia SUBIO desde la ultima medicion'. Por eso hace
    falta score_history; sin el, un evento importante y quieto se confunde con uno que esta creciendo.
    """
    ahora = ahora or datetime.now(timezone.utc)
    cambios = {"breaking": 0, "developing": 0, "watchlist": 0, "closed": 0}
    for ev in almacen.buscar_eventos(limite=500):
        if ev.get("estado") == "closed":
            continue
        ultimo = ev.get("last_updated") or ev.get("first_detected")
        horas = (ahora - ultimo).total_seconds() / 3600.0 if ultimo else 999
        imp = ev.get("importancia") or 0
        previa = almacen.importancia_previa(ev["id"]) if hasattr(almacen, "importancia_previa") else None

        if horas > HORAS_PARA_CERRAR:
            estado = "closed"
        elif imp >= 80 and horas <= HORAS_BREAKING:
            estado = "breaking"
        elif previa is not None and imp > previa + 4:
            estado = "developing"
        elif imp >= 40:
            estado = "developing"
        else:
            estado = "watchlist"

        if estado != ev.get("estado"):
            almacen.actualizar_evento(ev["id"], estado=estado)
        cambios[estado] = cambios.get(estado, 0) + 1
    return cambios


# --------------------------------------------------------------------------- autotest

class _AlmacenFalso:
    """Almacen minimo en memoria, para probar la LOGICA de agrupamiento sin base ni red."""

    def __init__(self, arts):
        self.arts = {a["id"]: dict(a) for a in arts}
        self.vecs = {}
        self.eventos = {}
        self._sig = 1
        self.log = []

    def articulos(self, desde=None, sin_evento=False, limite=500):
        out = [a for a in self.arts.values() if not sin_evento or a.get("event_id") is None]
        return out[:limite]

    def vecinos(self, vec, desde, umbral=0.0, limite=20):
        from radar import semantica as v
        res = []
        for aid, otro in self.vecs.items():
            s = v.similitud(vec, otro)
            if s >= umbral:
                res.append((aid, self.arts[aid].get("event_id"), s))
        res.sort(key=lambda r: -r[2])
        return res[:limite]

    def crear_evento(self, titulo, articulo_id, vec):
        eid = self._sig
        self._sig += 1
        self.eventos[eid] = {"id": eid, "titulo": titulo, "arts": [articulo_id]}
        self.arts[articulo_id]["event_id"] = eid
        self.vecs[articulo_id] = vec
        return eid

    def adjuntar(self, evento_id, articulo_id, vec):
        self.eventos[evento_id]["arts"].append(articulo_id)
        self.arts[articulo_id]["event_id"] = evento_id
        self.vecs[articulo_id] = vec

    def actualizar_evento(self, evento_id, **campos):
        self.eventos.setdefault(evento_id, {}).update(campos)

    def registrar(self, etapa, ok, n_in=0, n_out=0, error=None):
        self.log.append((etapa, ok, n_in, n_out))


def _autotest():
    fallos = []

    def chequeo(nombre, cond, extra=""):
        print(("OK   " if cond else "FALLA") + " " + nombre + ((" | " + extra) if extra else ""))
        if not cond:
            fallos.append(nombre)

    from radar import semantica as sem
    if not sem.disponible():
        print("SALTEA: falta fastembed. Sin embeddings no hay agrupamiento util (ver semantica.py).")
        return 0

    ahora = datetime.now(timezone.utc)
    # El caso exacto de RADAR.md §3, mezclado con ruido que NO debe agruparse.
    crudos = [
        ("US announces new sanctions on Russia over Ukraine war", "reuters_gn", "sanciones"),
        ("US imposes new Russia sanctions", "bbc_world", "sanciones"),
        ("Washington introduces new sanctions against Moscow", "tass_en", "sanciones"),
        ("Taiwan reports Chinese military aircraft near its airspace", "scmp_china", "taiwan"),
        ("Taiwan detects Chinese warplanes in its air defence zone", "japantimes", "taiwan"),
        ("Argentina inflation slows for the third consecutive month", "infobae", "argentina"),
    ]
    arts = [{"id": i + 1, "title": t, "source_id": s, "raw": {"descripcion": ""},
             "published_at": ahora - timedelta(minutes=60 - i * 5), "detected_at": ahora,
             "event_id": None, "_grupo": g}
            for i, (t, s, g) in enumerate(crudos)]

    al = _AlmacenFalso(arts)
    res = agrupar(al, limite=50, consultar_llm=False)
    print("   resultado: %s" % res)

    grupos = {}
    for a in al.arts.values():
        grupos.setdefault(a["event_id"], set()).add(a["_grupo"])

    chequeo("los 6 articulos quedaron asignados",
            all(a["event_id"] is not None for a in al.arts.values()))
    chequeo("ningun evento mezcla temas distintos",
            all(len(g) == 1 for g in grupos.values()),
            "eventos=%s" % {k: sorted(v) for k, v in grupos.items()})

    ev_por_grupo = {}
    for a in al.arts.values():
        ev_por_grupo.setdefault(a["_grupo"], set()).add(a["event_id"])
    chequeo("las 3 sanciones son UN solo acontecimiento",
            len(ev_por_grupo.get("sanciones", set())) == 1,
            "eventos=%s" % ev_por_grupo.get("sanciones"))
    chequeo("los 2 de Taiwan son UN solo acontecimiento",
            len(ev_por_grupo.get("taiwan", set())) == 1,
            "eventos=%s" % ev_por_grupo.get("taiwan"))
    chequeo("Argentina no se mezclo con nada",
            len(ev_por_grupo.get("argentina", set())) == 1
            and ev_por_grupo["argentina"].isdisjoint(ev_por_grupo.get("sanciones", set())))
    chequeo("salieron 3 acontecimientos y no 6", len(al.eventos) == 3,
            "eventos=%d" % len(al.eventos))

    if len(al.eventos) != 3:
        print("      NOTA: si agrupa de mas o de menos, el umbral (%.2f) es lo que hay que mover,"
              % UMBRAL)
        print("            y el autotest de radar/vectores.py dice cuanto separa de verdad.")

    print()
    print("FALLOS: %d" % len(fallos) + (" -> " + ", ".join(fallos) if fallos else ""))
    return 1 if fallos else 0


if __name__ == "__main__":
    if "--autotest" in sys.argv:
        sys.exit(_autotest())
    print(__doc__)
