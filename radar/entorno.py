# -*- coding: utf-8 -*-
"""Carga el .env del proyecto. Un solo lugar, para que TODOS los caminos vean lo mismo.

    python radar/entorno.py --autotest
    python radar/entorno.py             # muestra que hay cargado, sin revelar las claves

POR QUE EXISTE (bug real, 2026-09-11):

Los timers de systemd leen el .env con `EnvironmentFile=`. Una corrida A MANO desde el shell, no.
Resultado: `daily.py --solo recolectar` lanzado a mano veia RADAR_DSN vacio, caia a SQLite y se
ponia a comparar 3.321 vectores uno por uno en Python en vez de usar el indice de pgvector. No
fallaba: simplemente no terminaba nunca. Y `comprobar.py` decia que RADAR_DSN estaba bien, porque
ese SI cargaba el .env por su cuenta.

Un sistema que se porta distinto segun quien lo lance es peor que uno que falla: el que falla se
nota. Por eso la carga del entorno vive aca y la llaman todos los puntos de entrada.

No pisa lo que ya este en el entorno: si exportaste una variable a mano, esa gana.
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(BASE)
RUTA = os.path.join(RAIZ, ".env")

_cargado = False


def cargar(ruta=None, forzar=False):
    """Lee el .env y lo mete en os.environ. Devuelve las claves que cargo. Idempotente."""
    global _cargado
    if _cargado and not forzar:
        return []
    ruta = ruta or RUTA
    puestas = []
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln or ln.startswith("#") or "=" not in ln:
                    continue
                k, v = ln.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                # lo que ya esta en el entorno manda: permite pisar una variable para una corrida
                if k and not os.environ.get(k):
                    os.environ[k] = v
                    puestas.append(k)
    _cargado = True
    return puestas


def resumen():
    """Que hay configurado, SIN mostrar las claves."""
    cargar()
    out = []
    for k in ("OPENCODE_API_KEY", "MISTRAL_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY",
              "GROQ_API_KEY", "ANTHROPIC_API_KEY"):
        v = os.environ.get(k)
        out.append((k, "puesta (%d chars)" % len(v) if v else "sin definir"))
    dsn = os.environ.get("RADAR_DSN") or ""
    out.append(("RADAR_DSN", dsn.split("@")[-1] if dsn else "sin definir -> SQLite (lento)"))
    out.append(("RENDER_WORKERS", os.environ.get("RENDER_WORKERS") or "3 (por defecto)"))
    return out


def _autotest():
    import tempfile
    fallos = []

    def chequeo(n, c, e=""):
        print(("OK   " if c else "FALLA") + " " + n + ((" | " + e) if e else ""))
        if not c:
            fallos.append(n)

    d = tempfile.mkdtemp()
    p = os.path.join(d, ".env")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("# un comentario\n\n"
                 "RADAR_DSN=postgresql+psycopg://u:c@127.0.0.1:5442/radar\n"
                 'MISTRAL_API_KEY="con-comillas"\n'
                 "  ESPACIOS  =  a los costados  \n"
                 "YA_PUESTA=del-archivo\n"
                 "SIN_IGUAL\n")
    for k in ("RADAR_DSN", "MISTRAL_API_KEY", "ESPACIOS", "YA_PUESTA"):
        os.environ.pop(k, None)
    os.environ["YA_PUESTA"] = "del-entorno"

    puestas = cargar(p, forzar=True)
    chequeo("lee el DSN", os.environ.get("RADAR_DSN", "").endswith("/radar"))
    chequeo("saca las comillas", os.environ.get("MISTRAL_API_KEY") == "con-comillas")
    chequeo("saca los espacios", os.environ.get("ESPACIOS") == "a los costados")
    chequeo("NO pisa lo que ya estaba en el entorno",
            os.environ.get("YA_PUESTA") == "del-entorno")
    chequeo("ignora comentarios y lineas sin '='", "SIN_IGUAL" not in os.environ)
    chequeo("informa que cargo", set(puestas) >= {"RADAR_DSN", "MISTRAL_API_KEY"}, str(puestas))
    chequeo("sin archivo no explota", cargar(os.path.join(d, "no-existe"), forzar=True) == [])

    print()
    print("-- el bug que motivo este modulo --")
    sys.path.insert(0, RAIZ)
    from radar.almacen import es_postgres
    # Se prueba la DECISION, no la conexion: asi corre igual en el VPS y en una maquina sin driver.
    chequeo("con RADAR_DSN cargado, el almacen elige POSTGRES (indice HNSW, no fuerza bruta)",
            es_postgres(os.environ.get("RADAR_DSN")) is True)
    chequeo("sin RADAR_DSN cae a SQLite — que es exactamente lo que pasaba al correr a mano",
            es_postgres(None) is False)
    chequeo("reconoce las tres formas de escribir el DSN",
            all(es_postgres(x) for x in ("postgresql://u@h/d", "postgres://u@h/d",
                                         "postgresql+psycopg://u@h/d")))

    for k in ("RADAR_DSN", "MISTRAL_API_KEY", "ESPACIOS", "YA_PUESTA"):
        os.environ.pop(k, None)
    os.remove(p)
    os.rmdir(d)
    print()
    print("FALLOS: %d" % len(fallos) + (" -> " + ", ".join(fallos) if fallos else ""))
    return 1 if fallos else 0


if __name__ == "__main__":
    if "--autotest" in sys.argv:
        sys.exit(_autotest())
    print("entorno leido de %s\n" % RUTA)
    for k, v in resumen():
        print("  %-20s %s" % (k, v))
