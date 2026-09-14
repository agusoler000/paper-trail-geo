# -*- coding: utf-8 -*-
"""La escaleta del diario: que bloques hay y CUANTO DURA CADA UNO HOY.

    python videos/DAILY/escaleta.py --autotest
    python videos/DAILY/escaleta.py --demo        # un dia tranquilo y un dia de guerra

LOS TIEMPOS NO SON FIJOS (decision de Agustin, 2026-09-11: "lo ideal seria que eso varie de
acuerdo al dia"). Y tiene razon: las noticias no se reparten parejo. Hay dias en que Oriente Medio
es todo el programa y dias en que no pasa nada ahi.

COMO SE REPARTE
  1. Lo fijo primero: cold open, intro y outro. Eso no se mueve.
  2. Cada bloque se lleva su MINIMO. Asi ningun bloque desaparece: si Latinoamerica tuvo un dia
     flojo igual tiene su minuto y medio, porque la audiencia que viene por eso vuelve manana.
  3. Lo que sobra se reparte segun el PESO DEL DIA: la suma de importancia de los acontecimientos
     de cada bloque, con tope por acontecimiento para que uno solo no se lleve el programa.
  4. Se recorta contra el MAXIMO y lo que rebalsa vuelve a repartirse entre los que tienen lugar.

Asi, un bloque puede ir de 1:30 a 6:00 segun el dia, y el programa entero queda siempre cerca del
objetivo (20 min por defecto; `feedback-limites-no-literales`: pasarse dos o tres minutos esta bien).
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
_RAIZ = os.path.dirname(os.path.dirname(BASE))
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

OBJETIVO_MIN = 20.0

# EL PRESENTADOR FIJO (decision de Agustin, 2026-09-11). Abre y cierra todos los dias.
IROLA = "A"
NOMBRE_IROLA = "IROLA"

# Lo que no se mueve nunca. El INTRO va PRIMERO: Agustin pidio que "todos los inicios de los
# videos tienen que empezar con un mini intro de 5 segundos". Despues viene el gancho.
FIJOS = {"INTRO": 0.32, "COLD OPEN": 0.75, "OUTRO": 0.08}

# El saludo NOMBRA LA FECHA, asi que no puede ser un clip pregrabado: se sintetiza cada manana.
# Con Piper eso cuesta cero, y tarda menos de un segundo.
#
# DONDE VA (Agustin, 2026-09-14): "antes de la intro del canal meter en este Y EN TODOS los videos
# de noticias una intro que diga muy buenos dias, bienvenidos a The Ledger... tenemos todas las
# noticias del dia lunes 14 de septiembre del 2026... y luego alguna insistencia en quedarse".
# O sea el orden es:  SALUDO -> intro del canal -> cold open -> programa.
# Esto encaja con `canal/INTRO_OUTRO.md` ("va al principio del video, DESPUES de la intro propia
# del episodio") y con la regla del 2026-09-08 de gancho propio antes de la intro general.
#
# QUE LLEVA Y QUE NO:
#   - saluda y nombra el programa;
#   - una linea que atrape, no una lista de temas (los temas son el cold open);
#   - la fecha hablada entera, con dia de la semana y ano;
#   - la insistencia en quedarse, apuntando a WHAT TO WATCH, que es el bloque que hace volver.
#   - NO pide like ni suscripcion: la intro del canal entra dos segundos despues y ya las pide
#     las dos. Decirlo dos veces en treinta segundos suena a ruego.
#
# Dura ~19 s. Agustin habia dicho "5 segundos" en septiembre 11 para la version corta; esta la
# pidio el 14 con contenido que no entra en cinco. Vale su regla de que los numeros son
# referencia y no especificacion (2026-09-11).
# Medido con la voz de Irola (ryan-high): 20 caracteres por segundo.
TEXTO_INTRO = ("Good morning, and welcome to The Ledger. If you have time for one programme "
               "about the world today, make it this one. Every story that matters from {fecha}, "
               "twenty twenty-six, in order, and with the source on screen. Stay with us to the "
               "end: the last block is the calendar of what moves next.")
TEXTO_OUTRO = ("Thank you. It has been a pleasure to be with you today. "
               "Don't forget to subscribe and like the video.")

_MES = ["January", "February", "March", "April", "May", "June", "July",
        "August", "September", "October", "November", "December"]
_ORD = {1: "first", 2: "second", 3: "third", 21: "twenty-first", 22: "twenty-second",
        23: "twenty-third", 31: "thirty-first"}


def fecha_hablada(fecha_iso):
    """'2026-09-11' -> 'Friday, September eleventh'. Se lee, no se deletrea."""
    from datetime import date
    d = date.fromisoformat(str(fecha_iso)[:10])
    dia = _ORD.get(d.day)
    if not dia:
        base = ["", "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth",
                "ninth", "tenth", "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth",
                "sixteenth", "seventeenth", "eighteenth", "nineteenth", "twentieth"]
        if d.day <= 20:
            dia = base[d.day]
        else:
            dia = "twenty-" + base[d.day - 20]
    return "%s, the %s of %s" % (d.strftime("%A"), dia, _MES[d.month - 1])


def texto_intro(fecha_iso):
    return TEXTO_INTRO.format(fecha=fecha_hablada(fecha_iso))


def texto_outro():
    return TEXTO_OUTRO


def beats_fijos(fecha_iso):
    """El bloque de apertura y el de cierre, ya escritos. No los redacta el LLM: son siempre iguales.

    La ficha del intro es el sello del programa; la del outro, el calendario de manana.
    """
    return (
        {"nombre": "INTRO", "presentador": IROLA, "beats": [
            {"t": 0.0, "dur": FIJOS["INTRO"] * 60, "pose": "reposo", "ficha": "titular",
             "texto": texto_intro(fecha_iso),
             "datos": {"medio": "THE LEDGER", "fecha": str(fecha_iso),
                       "titular": "THE LEDGER", "bajada": "Daily geopolitics"}}]},
        {"nombre": "OUTRO", "presentador": IROLA, "beats": [
            {"t": 0.0, "dur": FIJOS["OUTRO"] * 60, "pose": "reposo", "ficha": "titular",
             "texto": texto_outro(),
             "datos": {"medio": "THE LEDGER", "fecha": str(fecha_iso),
                       "titular": "SAME TIME TOMORROW", "bajada": "12:00 UTC"}}]},
    )

# nombre: (minimo, maximo, presentador, topics que lo alimentan, paises que lo alimentan)
# El reparto de presentadores sigue una logica: A la mesa de las potencias, B los teatros donde
# estan pasando cosas, C los numeros y el calendario.
BLOQUES = {
    "THE POWERS": (3.0, 9.0, "A",
                   {"diplomacy", "military", "elections", "legal", "sanctions"},
                   {"US", "CN", "RU", "DE", "FR", "GB", "EU", "UA", "PL", "TR", "IT", "ES", "NL",
                    "BE", "SE", "FI", "NO", "RO", "CZ", "AT", "CA"}),
    "THE MIDDLE EAST": (1.5, 6.0, "B",
                        {"military", "diplomacy", "energy"},
                        {"IL", "IR", "SA", "AE", "QA", "EG", "JO", "LB", "SY", "IQ", "YE", "PS",
                         "KW", "OM", "BH"}),
    "THE MONEY": (2.0, 6.0, "C",
                  {"finance", "trade"},
                  set()),
    "TECH & ENERGY": (1.0, 4.0, "C",
                      {"tech", "energy"},
                      set()),
    "THE SOUTH": (1.5, 5.0, "B",
                  set(),
                  {"AR", "BR", "CL", "UY", "PY", "BO", "PE", "CO", "VE", "EC", "MX", "CU", "NI",
                   "GT", "PA", "DO", "HN", "SV", "CR"}),
    "THE PACIFIC": (1.0, 4.0, "B",
                    set(),
                    {"AU", "NZ", "JP", "KR", "TW", "PH", "ID", "VN", "TH", "MY", "SG", "IN", "PG",
                     "KP", "FJ"}),
    "WHAT TO WATCH": (1.5, 2.5, "C", set(), set()),
}
ORDEN = ["INTRO", "COLD OPEN", "THE POWERS", "THE MIDDLE EAST", "THE MONEY", "TECH & ENERGY",
         "THE SOUTH", "THE PACIFIC", "WHAT TO WATCH", "OUTRO"]
ORDEN_VARIABLE = [b for b in ORDEN if b in BLOQUES]

TOPE_POR_EVENTO = 85      # un solo acontecimiento no puede pesar mas que esto
PRESENTADOR = {b: v[2] for b, v in BLOQUES.items()}
PRESENTADOR.update({"COLD OPEN": IROLA, "INTRO": IROLA, "OUTRO": IROLA})


def bloque_de(evento):
    """A que bloque va un acontecimiento. La geografia manda sobre el tema, salvo dinero y tech.

    Oriente Medio va ANTES que las potencias: un ataque en Israel con reaccion de Washington es
    del bloque de Oriente Medio, no del de las potencias, aunque EEUU aparezca en los actores.
    """
    paises = set(evento.get("paises") or [])
    topics = set(evento.get("topics") or [])

    if topics & {"finance", "trade"} and not (topics & {"military"}):
        return "THE MONEY"
    if topics & {"tech", "energy"} and not (topics & {"military"}):
        return "TECH & ENERGY"
    for nombre in ("THE MIDDLE EAST", "THE SOUTH", "THE PACIFIC", "THE POWERS"):
        _, _, _, _, geo = BLOQUES[nombre]
        if geo and (paises & geo):
            return nombre
    if topics & {"finance", "trade"}:
        return "THE MONEY"
    if topics & {"tech", "energy"}:
        return "TECH & ENERGY"
    return "THE POWERS"


def repartir(eventos, objetivo=OBJETIVO_MIN, fijos=None):
    """{bloque: minutos} segun el peso real del dia. Devuelve tambien el detalle."""
    fijos = FIJOS if fijos is None else fijos
    porBloque = {b: [] for b in BLOQUES}
    for ev in eventos or []:
        porBloque.setdefault(bloque_de(ev), []).append(ev)

    peso = {}
    for b in BLOQUES:
        if b == "WHAT TO WATCH":
            peso[b] = 0.0          # es el calendario: no depende del peso del dia
            continue
        peso[b] = float(sum(min(TOPE_POR_EVENTO, ev.get("importancia") or 0)
                            for ev in porBloque.get(b, [])))

    disponible = objetivo - sum(fijos.values())
    minimos = {b: BLOQUES[b][0] for b in BLOQUES}
    sobra = disponible - sum(minimos.values())
    reparto = dict(minimos)

    # Si no hay peso en ningun lado (dia sin eventos, o el Radar fallo), el programa no puede
    # quedar corto: se reparte por el margen que tiene cada bloque, no por el peso.
    if sum(peso.values()) <= 0:
        peso = {b: (BLOQUES[b][1] - BLOQUES[b][0]) for b in BLOQUES}

    # Reparto proporcional al peso, con recorte por maximo y redistribucion de lo que rebalsa.
    for _ in range(8):
        if sobra <= 0.01:
            break
        abiertos = [b for b in BLOQUES if reparto[b] < BLOQUES[b][1] - 0.01 and peso[b] > 0]
        total = sum(peso[b] for b in abiertos)
        if not abiertos or total <= 0:
            # Ultimo recurso: reparto parejo entre los que todavia tienen lugar.
            abiertos = [b for b in BLOQUES if reparto[b] < BLOQUES[b][1] - 0.01]
            if not abiertos:
                break
            for b in abiertos:
                reparto[b] = min(BLOQUES[b][1], reparto[b] + sobra / len(abiertos))
            break
        rebalse = 0.0
        for b in abiertos:
            cuota = sobra * peso[b] / total
            techo = BLOQUES[b][1] - reparto[b]
            dado = min(cuota, techo)
            reparto[b] += dado
            rebalse += cuota - dado
        sobra = rebalse

    detalle = {b: {"minutos": round(reparto[b], 2), "eventos": len(porBloque.get(b, [])),
                   "peso": round(peso[b], 1), "presentador": BLOQUES[b][2],
                   "min": BLOQUES[b][0], "max": BLOQUES[b][1]}
               for b in ORDEN_VARIABLE}
    total_min = sum(reparto.values()) + sum(fijos.values())
    return {"total_min": round(total_min, 2), "fijos": fijos,
            "bloques": detalle,
            "eventos_por_bloque": {b: porBloque.get(b, []) for b in ORDEN_VARIABLE}}


def resumen(rep):
    out = ["ESCALETA DE HOY — %.1f min" % rep["total_min"]]
    for b in ORDEN_VARIABLE:
        d = rep["bloques"][b]
        barra = "#" * int(d["minutos"] * 4)
        out.append("  %-16s %5.2f min  %-36s %2d ev · peso %5.1f · %s"
                   % (b, d["minutos"], barra, d["eventos"], d["peso"], d["presentador"]))
    return "\n".join(out)


# --------------------------------------------------------------------------- autotest

def _ev(paises, topics, imp):
    return {"paises": paises, "topics": topics, "importancia": imp}


def _demo():
    tranquilo = ([_ev(["US", "CN"], ["diplomacy"], 62), _ev(["DE", "EU"], ["elections"], 48)]
                 + [_ev(["IL"], ["diplomacy"], 33)]
                 + [_ev([], ["finance"], 55), _ev([], ["trade"], 44)]
                 + [_ev(["AR"], ["elections"], 58), _ev(["BR"], ["trade"], 40)]
                 + [_ev(["AU"], ["diplomacy"], 45)])
    guerra = ([_ev(["US", "CN"], ["diplomacy"], 50)]
              + [_ev(["IL", "IR"], ["military"], 92), _ev(["IL", "LB"], ["military"], 88),
                 _ev(["YE", "SA"], ["military"], 81), _ev(["IR"], ["energy"], 74),
                 _ev(["EG", "PS"], ["diplomacy"], 66)]
              + [_ev([], ["finance"], 51)]
              + [_ev(["AR"], ["finance"], 38)]
              + [_ev(["TW", "CN"], ["military"], 70)])
    for nombre, evs in (("UN DIA TRANQUILO EN ORIENTE MEDIO", tranquilo),
                        ("UN DIA DE GUERRA EN ORIENTE MEDIO", guerra)):
        print("\n=== %s ===" % nombre)
        print(resumen(repartir(evs)))


def _autotest():
    fallos = []

    def chequeo(n, c, e=""):
        print(("OK   " if c else "FALLA") + " " + n + ((" | " + e) if e else ""))
        if not c:
            fallos.append(n)

    print("--- el bloque nuevo ---")
    chequeo("existe THE MIDDLE EAST", "THE MIDDLE EAST" in BLOQUES)
    chequeo("Israel e Iran caen ahi",
            bloque_de(_ev(["IL", "IR"], ["military"], 90)) == "THE MIDDLE EAST")
    chequeo("Yemen y Arabia tambien",
            bloque_de(_ev(["YE", "SA"], ["military"], 70)) == "THE MIDDLE EAST")
    chequeo("Oriente Medio gana sobre las potencias aunque aparezca EEUU",
            bloque_de(_ev(["US", "IL"], ["military"], 80)) == "THE MIDDLE EAST",
            bloque_de(_ev(["US", "IL"], ["military"], 80)))
    chequeo("Argentina sigue en THE SOUTH", bloque_de(_ev(["AR"], ["elections"], 60)) == "THE SOUTH")
    chequeo("Taiwan en THE PACIFIC", bloque_de(_ev(["TW", "CN"], ["military"], 70)) == "THE PACIFIC")
    chequeo("Rusia y EEUU en THE POWERS", bloque_de(_ev(["US", "RU"], ["diplomacy"], 70)) == "THE POWERS")
    chequeo("mercados sin geografia van a THE MONEY",
            bloque_de(_ev([], ["finance"], 50)) == "THE MONEY")

    print("--- los tiempos VARIAN con el dia ---")
    calmo = [_ev(["IL"], ["diplomacy"], 30)] + [_ev(["US", "CN"], ["diplomacy"], 70)] * 4
    caliente = [_ev(["IL", "IR"], ["military"], 92)] * 5 + [_ev(["US"], ["diplomacy"], 45)]
    a = repartir(calmo)["bloques"]["THE MIDDLE EAST"]["minutos"]
    b = repartir(caliente)["bloques"]["THE MIDDLE EAST"]["minutos"]
    # Lo que importa no es un ratio arbitrario, sino que el dia de guerra llegue al tope y le
    # gane al tranquilo por un margen que se NOTA en pantalla (mas de minuto y medio).
    chequeo("un dia de guerra le da mucho mas aire a Oriente Medio", b - a >= 1.5 and b >= 5.5,
            "tranquilo=%.2f min · guerra=%.2f min · diferencia=%.2f" % (a, b, b - a))
    p_a = repartir(calmo)["bloques"]["THE POWERS"]["minutos"]
    p_b = repartir(caliente)["bloques"]["THE POWERS"]["minutos"]
    chequeo("y se lo saca a las potencias", p_b < p_a, "%.2f -> %.2f" % (p_a, p_b))

    print("--- las garantias ---")
    for nombre, evs in (("sin nada", []), ("todo en un bloque", caliente)):
        rep = repartir(evs)
        chequeo("con %s, ningun bloque baja de su minimo" % nombre,
                all(rep["bloques"][x]["minutos"] >= BLOQUES[x][0] - 0.01 for x in ORDEN_VARIABLE))
        chequeo("con %s, ninguno pasa su maximo" % nombre,
                all(rep["bloques"][x]["minutos"] <= BLOQUES[x][1] + 0.01 for x in ORDEN_VARIABLE))
        chequeo("con %s, el total queda cerca del objetivo" % nombre,
                abs(rep["total_min"] - OBJETIVO_MIN) <= 2.6,
                "%.1f min (objetivo %.0f)" % (rep["total_min"], OBJETIVO_MIN))
    rep = repartir(caliente)
    chequeo("Latinoamerica conserva su lugar en un dia que no le toca",
            rep["bloques"]["THE SOUTH"]["minutos"] >= 1.5,
            "%.2f min" % rep["bloques"]["THE SOUTH"]["minutos"])
    chequeo("WHAT TO WATCH no depende del peso del dia",
            abs(repartir(calmo)["bloques"]["WHAT TO WATCH"]["minutos"]
                - repartir(caliente)["bloques"]["WHAT TO WATCH"]["minutos"]) < 0.01)

    print("--- reparto de presentadores ---")
    carga = {}
    for b in ORDEN_VARIABLE:
        carga[BLOQUES[b][2]] = carga.get(BLOQUES[b][2], 0) + repartir(calmo)["bloques"][b]["minutos"]
    print("      minutos por presentador en un dia normal: %s"
          % {k: round(v, 1) for k, v in sorted(carga.items())})
    chequeo("ningun presentador se lleva mas de la mitad del programa",
            max(carga.values()) < OBJETIVO_MIN * 0.55,
            "max=%.1f min" % max(carga.values()))

    print()
    print("FALLOS: %d" % len(fallos) + (" -> " + ", ".join(fallos) if fallos else ""))
    return 1 if fallos else 0


if __name__ == "__main__":
    if "--autotest" in sys.argv:
        sys.exit(_autotest())
    if "--demo" in sys.argv:
        _demo()
        sys.exit(0)
    print(__doc__)
