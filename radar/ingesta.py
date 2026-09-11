# -*- coding: utf-8 -*-
"""Ingesta de feeds del Radar: baja, normaliza, deduplica y vigila la salud de las fuentes.

    python radar/ingesta.py --autotest        # prueba contra la red real, sin base
    python radar/ingesta.py --tick            # una pasada completa contra la base

Sin feedparser a proposito: xml.etree alcanza, y una dependencia menos en el VPS.

DOS COSAS QUE NO SON OBVIAS Y SOSTIENEN TODO LO DEMAS:

1. wire_origin. BBC, Yahoo y veinte medios mas publican el mismo cable de Reuters. Si el contador
   de fuentes independientes no lo sabe, el sistema etiqueta como HECHO cosas que dijo una sola
   redaccion. Aca se detecta y se guarda; radar/puntajes.py lo usa para contar.

2. Los feeds puente de Google News. Reuters, AP, NATO, ISW y Xinhua ya no publican RSS
   (verificado 2026-09-11, ver radar/fuentes.json). Se leen via news.google.com, que devuelve el
   titular con " - Medio" pegado atras y el medio real en <source>. Hay que desarmarlo o la base
   se llena de titulares sucios y con el medio equivocado.

Legal (RADAR.md §12): se guarda titular, link, fecha y un extracto corto del propio feed.
NUNCA el texto completo del articulo. El campo `summary` queda para el resumen que escribimos
nosotros; lo que baja del feed vive en `raw["descripcion"]` recortado.
"""
import hashlib
import html
import json
import os
import re
import ssl
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

BASE = os.path.dirname(os.path.abspath(__file__))
_RAIZ = os.path.dirname(BASE)
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)
FUENTES_JSON = os.path.join(BASE, "fuentes.json")

FRESCURA_HORAS = 72          # un feed cuyo item mas nuevo sea mas viejo que esto esta zombie
FALLOS_PARA_APAGAR = 3
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
MAX_BYTES = 800_000
MAX_DESC = 600               # recorte del extracto del feed

_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE

ATOM = "{http://www.w3.org/2005/Atom}"
DC = "{http://purl.org/dc/elements/1.1/}"
CONTENT = "{http://purl.org/rss/1.0/modules/content/}"

# Agencias cuyo cable republican otros. El orden importa: la primera que matchea gana.
_WIRES = [
    ("reuters", re.compile(r"\breuters\b", re.I)),
    ("ap", re.compile(r"\bassociated press\b|\(\s*AP\s*\)|\bAP\s+(?:News|Photo)\b")),
    ("afp", re.compile(r"\bagence france[- ]presse\b|\bAFP\b")),
    ("efe", re.compile(r"\bagencia efe\b|\bEFE\b")),
    ("bloomberg", re.compile(r"\bbloomberg\b", re.I)),
]
_TAGS = re.compile(r"<[^>]+>")
_ESPACIOS = re.compile(r"\s+")


# --------------------------------------------------------------------------- utilidades

def _texto(el):
    """Texto plano de un elemento, sin markup ni entidades."""
    if el is None:
        return ""
    crudo = "".join(el.itertext()) if len(el) else (el.text or "")
    return _ESPACIOS.sub(" ", html.unescape(_TAGS.sub(" ", crudo))).strip()


def _primero(item, *nombres):
    for n in nombres:
        el = item.find(n)
        if el is not None:
            return el
    return None


def url_hash(url):
    """sha1 de la url normalizada. Saca utm_* y el fragmento, que son ruido que duplica."""
    u = (url or "").strip()
    u = u.split("#", 1)[0]
    if "?" in u:
        base, cola = u.split("?", 1)
        partes = [p for p in cola.split("&")
                  if p and not p.lower().startswith(("utm_", "fbclid", "gclid", "ref=", "ocid="))]
        u = base + ("?" + "&".join(partes) if partes else "")
    return hashlib.sha1(u.rstrip("/").lower().encode("utf-8")).hexdigest()


def _normalizar(texto):
    t = unicodedata.normalize("NFKD", (texto or "").lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return _ESPACIOS.sub(" ", re.sub(r"[^\w\s]", " ", t)).strip()


def title_simhash(titulo, bits=64):
    """Simhash de 64 bits sobre palabras. Dos titulares casi iguales dan hashes a pocos bits.

    Sirve para el caso que url_hash no agarra: el MISMO cable publicado en dos urls distintas.
    """
    palabras = _normalizar(titulo).split()
    if not palabras:
        return 0
    v = [0] * bits
    for p in palabras:
        h = int.from_bytes(hashlib.md5(p.encode("utf-8")).digest()[:8], "big")
        for i in range(bits):
            v[i] += 1 if (h >> i) & 1 else -1
    n = 0
    for i in range(bits):
        if v[i] > 0:
            n |= (1 << i)
    return n - (1 << 63) if n >= (1 << 63) else n     # a con signo, para que entre en un BIGINT


def distancia_simhash(a, b):
    return bin((a ^ b) & ((1 << 64) - 1)).count("1")


def _fecha(txt):
    """RSS trae RFC 822, Atom trae ISO 8601, y siempre hay alguno que trae cualquier cosa."""
    if not txt:
        return None
    txt = txt.strip()
    try:
        d = parsedate_to_datetime(txt)
        if d:
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    try:
        d = datetime.fromisoformat(txt.replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            return datetime.strptime(txt, fmt).replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None


def detectar_wire(*textos):
    """De que agencia es el cable, si es de alguna. None = reporte propio del medio."""
    junto = " ".join(t for t in textos if t)
    for nombre, patron in _WIRES:
        if patron.search(junto):
            return nombre
    return None


def _es_google_news(url):
    return "news.google.com" in (url or "")


def _desarmar_google(titulo, item):
    """Google News pega ' - Medio' al titular y pone el medio real en <source>.

    Devuelve (titulo_limpio, medio_real|None). Sin esto la base guarda el medio equivocado.
    """
    src = _primero(item, "source", ATOM + "source")
    medio = _texto(src) if src is not None else ""
    if medio and titulo.endswith(" - " + medio):
        titulo = titulo[: -(len(medio) + 3)].strip()
    elif " - " in titulo:
        cabeza, cola = titulo.rsplit(" - ", 1)
        if 2 <= len(cola) <= 40 and not cola.endswith("."):
            titulo, medio = cabeza.strip(), medio or cola.strip()
    return titulo, (medio or None)


# --------------------------------------------------------------------------- lectura

def _bajar(url, timeout):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as r:
        return r.read(MAX_BYTES)


def leer_feed(feed, timeout=20, ahora=None):
    """Baja y normaliza un feed. Devuelve (articulos, error).

    `feed` es una entrada de radar/fuentes.json. error None = todo bien.
    """
    ahora = ahora or datetime.now(timezone.utc)
    try:
        crudo = _bajar(feed["url"], timeout)
    except urllib.error.HTTPError as e:
        return [], "HTTP %s" % e.code
    except Exception as e:
        return [], "%s: %s" % (type(e).__name__, str(e)[:80])

    try:
        raiz = ET.fromstring(crudo)
    except ET.ParseError as e:
        return [], "XML invalido: %s" % str(e)[:60]

    items = raiz.findall(".//item") or raiz.findall(".//" + ATOM + "entry")
    if not items:
        return [], "0 items"

    puente = _es_google_news(feed["url"])
    salida = []
    for it in items:
        titulo = _texto(_primero(it, "title", ATOM + "title"))
        if not titulo:
            continue

        enlace = ""
        el = _primero(it, "link", ATOM + "link")
        if el is not None:
            enlace = (el.text or "").strip() or (el.get("href") or "").strip()
        if not enlace:
            enlace = _texto(_primero(it, "guid", "id", ATOM + "id"))
        if not enlace:
            continue

        desc = _texto(_primero(it, "description", "summary", ATOM + "summary",
                               CONTENT + "encoded", ATOM + "content"))[:MAX_DESC]
        fecha = None
        for tag in ("pubDate", DC + "date", "published", "updated",
                    ATOM + "published", ATOM + "updated"):
            e2 = it.find(tag)
            if e2 is not None and e2.text:
                fecha = _fecha(e2.text)
                if fecha:
                    break

        medio = None
        if puente:
            titulo, medio = _desarmar_google(titulo, it)

        autor = _texto(_primero(it, "author", DC + "creator", ATOM + "author"))
        # El wire se busca en el titulo, el extracto, el autor y el medio del puente.
        # OJO: no se busca en la url, porque "reuters.com" haria que TODO Reuters sea "cable de
        # Reuters" republicado, cuando en realidad es su reporte propio.
        wire = detectar_wire(titulo, desc, autor, medio or "")
        if wire is None and feed.get("wire_propio") is False:
            wire = "desconocido"     # el feed avisa que republica, pero no sabemos de quien

        salida.append({
            "source_id": feed["id"],
            "url": enlace,
            "url_hash": url_hash(enlace),
            "title_simhash": title_simhash(titulo),
            "wire_origin": wire,
            "title": titulo,
            "summary": None,                  # lo escribimos nosotros, no el medio (RADAR.md §12)
            "published_at": fecha,
            "detected_at": ahora,
            "lang": feed.get("lang"),
            "event_id": None,
            "raw": {"descripcion": desc, "autor": autor or None,
                    "medio_puente": medio, "tipo": feed.get("tipo")},
        })
    return salida, None


def frescura(articulos, ahora=None):
    """Horas desde el item mas nuevo. None si ninguno trae fecha."""
    ahora = ahora or datetime.now(timezone.utc)
    fechas = [a["published_at"] for a in articulos if a.get("published_at")]
    if not fechas:
        return None
    return (ahora - max(fechas)).total_seconds() / 3600.0


# --------------------------------------------------------------------------- tick

def tick(almacen, solo=None, workers=12, timeout=20):
    """Una pasada por todas las fuentes activas. Guarda lo nuevo y vigila la salud de los feeds.

    El chequeo de frescura no es un lujo: hay feeds que devuelven HTTP 200 con contenido de 2016
    (verificado: csis.org/rss.xml y el de WSJ). Un 200 no significa que el feed este vivo.
    """
    ahora = datetime.now(timezone.utc)
    fuentes = [f for f in almacen.fuentes(solo_activas=True)
               if not solo or f["id"] in solo]
    if not fuentes:
        return {"leidos": 0, "nuevos": 0, "feeds_ok": 0, "feeds_muertos": [], "detalle": []}

    with ThreadPoolExecutor(max_workers=workers) as ex:
        resultados = list(ex.map(lambda f: (f,) + leer_feed(f, timeout, ahora), fuentes))

    leidos = nuevos = ok = 0
    muertos, detalle = [], []
    for feed, articulos, error in resultados:
        fid = feed["id"]
        if error:
            almacen.marcar_fuente(fid, False, error)
            f2 = next((x for x in almacen.fuentes(solo_activas=False) if x["id"] == fid), {})
            if (f2.get("fallos_seguidos") or 0) >= FALLOS_PARA_APAGAR:
                muertos.append((fid, "%d fallos seguidos: %s" % (f2["fallos_seguidos"], error)))
            detalle.append({"id": fid, "error": error, "n": 0})
            continue

        h = frescura(articulos, ahora)
        if h is not None and h > FRESCURA_HORAS:
            # Feed zombie: responde bien pero hace dias que no publica.
            almacen.marcar_fuente(fid, False, "zombie: item mas nuevo hace %.0f h" % h)
            muertos.append((fid, "zombie: %.0f h sin publicar" % h))
            detalle.append({"id": fid, "error": "zombie", "n": len(articulos), "frescura_h": h})
            continue

        almacen.marcar_fuente(fid, True)
        ok += 1
        leidos += len(articulos)
        n_nuevos = 0
        for art in articulos:
            if almacen.guardar_articulo(art) is not None:
                n_nuevos += 1
        nuevos += n_nuevos
        detalle.append({"id": fid, "error": None, "n": len(articulos),
                        "nuevos": n_nuevos, "frescura_h": h})

    res = {"leidos": leidos, "nuevos": nuevos, "feeds_ok": ok,
           "feeds_muertos": muertos, "detalle": detalle}
    almacen.registrar("ingesta", ok=not muertos or ok > 0, n_in=leidos, n_out=nuevos,
                      error=("feeds caidos: %s" % ", ".join(m[0] for m in muertos)) if muertos else None)
    return res


# --------------------------------------------------------------------------- autotest

def _autotest():
    fallos = []

    def chequeo(nombre, cond, extra=""):
        print(("OK   " if cond else "FALLA") + " " + nombre + ((" | " + extra) if extra else ""))
        if not cond:
            fallos.append(nombre)

    print("--- url_hash y simhash ---")
    chequeo("url_hash ignora utm_ y el fragmento",
            url_hash("https://x.com/a?utm_source=rss&id=3") == url_hash("https://x.com/a?id=3#top"))
    chequeo("url_hash distingue urls distintas",
            url_hash("https://x.com/a") != url_hash("https://x.com/b"))
    a = title_simhash("US announces new sanctions on Russia")
    b = title_simhash("US imposes new sanctions on Russia")
    c = title_simhash("Argentina inflation slows for the third month")
    chequeo("simhash acerca titulares parecidos y separa los distintos",
            distancia_simhash(a, b) < distancia_simhash(a, c),
            "parecidos=%d distinto=%d" % (distancia_simhash(a, b), distancia_simhash(a, c)))
    chequeo("simhash entra en un BIGINT con signo",
            all(-(2 ** 63) <= v < 2 ** 63 for v in (a, b, c)))

    print("--- deteccion de wire (el anti doble conteo) ---")
    chequeo("detecta Reuters", detectar_wire("Something happened", "(Reuters) - ...") == "reuters")
    chequeo("detecta AP", detectar_wire("Vote held", "WASHINGTON (AP) — ...") == "ap")
    chequeo("detecta AFP", detectar_wire("Strike reported", "", "AFP") == "afp")
    chequeo("reporte propio devuelve None",
            detectar_wire("BBC investigation finds", "Our correspondent reports") is None)
    chequeo("no confunde 'apoyo' con AP", detectar_wire("El apoyo del gobierno", "") is None)

    print("--- fechas ---")
    chequeo("RFC 822", _fecha("Fri, 11 Sep 2026 09:30:00 GMT") is not None)
    chequeo("ISO 8601 con Z", _fecha("2026-09-11T10:40:53Z") is not None)
    chequeo("con offset", _fecha("Fri, 11 Sep 2026 18:05:26 +1000") is not None)
    chequeo("todas aware", all(_fecha(s).tzinfo is not None for s in
                               ("Fri, 11 Sep 2026 09:30:00 GMT", "2026-09-11T10:40:53Z")))
    chequeo("basura devuelve None", _fecha("ayer a la tarde") is None)

    print("--- feeds reales (red) ---")
    if not os.path.exists(FUENTES_JSON):
        print("SALTEA: no esta radar/fuentes.json")
        return 1 if fallos else 0
    reg = json.load(open(FUENTES_JSON, encoding="utf-8"))
    por_id = {f["id"]: f for f in reg["feeds"]}
    muestra = [por_id[k] for k in ("bbc_world", "gn_reuters", "tass_en", "infobae", "aljazeera")
               if k in por_id]
    for feed in muestra:
        arts, err = leer_feed(feed, timeout=25)
        if err:
            print("SALTEA: %-12s no respondio (%s) — puede ser la red de aca" % (feed["id"], err))
            continue
        h = frescura(arts)
        chequeo("%s trae articulos" % feed["id"], len(arts) > 0, "n=%d" % len(arts))
        if arts:
            chequeo("%s: url y titulo no vacios" % feed["id"],
                    all(a["url"] and a["title"] for a in arts))
            chequeo("%s: fechas aware" % feed["id"],
                    all(a["published_at"] is None or a["published_at"].tzinfo for a in arts))
            chequeo("%s: no guarda texto completo" % feed["id"],
                    all(len(a["raw"]["descripcion"]) <= MAX_DESC for a in arts))
            if h is not None:
                chequeo("%s esta fresco (%.0f h)" % (feed["id"], h), h <= FRESCURA_HORAS)
            if feed["id"] == "gn_reuters":
                sucios = [a for a in arts if re.search(r" - [A-Z][\w .]{2,30}$", a["title"])]
                chequeo("gn_reuters: titulos sin ' - Medio' pegado", len(sucios) == 0,
                        "sucios=%d de %d" % (len(sucios), len(arts)))
                chequeo("gn_reuters: identifica el medio real",
                        sum(1 for a in arts if a["raw"]["medio_puente"]) > len(arts) // 2)
                print("      ejemplo: %r  medio=%r  wire=%r"
                      % (arts[0]["title"][:62], arts[0]["raw"]["medio_puente"], arts[0]["wire_origin"]))

    print()
    print("FALLOS: %d" % len(fallos) + (" -> " + ", ".join(fallos) if fallos else ""))
    return 1 if fallos else 0


if __name__ == "__main__":
    if "--autotest" in sys.argv:
        sys.exit(_autotest())
    if "--tick" in sys.argv:
        from radar import almacen as _a
        al = _a.conectar(os.environ.get("RADAR_DSN"))
        al.init_esquema()
        al.cargar_fuentes(FUENTES_JSON)
        r = tick(al)
        print(json.dumps({k: v for k, v in r.items() if k != "detalle"}, indent=1, default=str))
        sys.exit(0)
    print(__doc__)
