# -*- coding: utf-8 -*-
"""Los ocho renderizadores del panel derecho del formato diario (`videos/DAILY/DIARIO.md` 3).

    render_ficha(tipo, datos, size=(960,1080), t=0.0) -> PIL.Image

`t` son los segundos desde que la ficha entro en pantalla: sirve para la entrada (la hoja sube y
se asienta) y para los reveles internos (los puntos del mapa aparecen, la curva de la serie se
dibuja, los hitos de la cronologia caen de a uno). La ESTRUCTURA -- marco, titulos, tarjetas,
reglas -- se dibuja SIEMPRE completa: ninguna ficha esta vacia en t=0.

Lenguaje visual: el mismo de `layout.py` (papel, tarjetas con sombra corta, sellos, grano) y la
paleta cerrada de `ESTILO.md` 2.2. No se inventa nada nuevo; esto es el panel derecho de ese cuadro.

REGLA DEL ROJO. `ESTILO.md` 2.2: el rojo marca solo lo que esta en disputa, un elemento por plano.
Aca se hace cumplir por codigo (`_Rojo`): si un renderizador pide rojo para dos elementos distintos,
levanta ValueError en vez de salir feo. Lo que marca el rojo en cada ficha:

    mapa        el punto (o los puntos) en disputa          versus      el sello de evidencia
    titular     el subrayado del titular que se pone en cuestion
    dato        la cifra, que es lo que la ficha somete a escrutinio
    serie       el ultimo valor, el que esta en juego       cronologia  el hito mas reciente
    calendario  la fecha mas proxima                        plano       la vineta del pie

TEXTO. Nada se desborda ni se corta: `encajar()` mide, envuelve y baja el cuerpo hasta que entra
en su caja; si ni en el cuerpo minimo entra, recorta lineas y cierra con puntos suspensivos.

RENDIMIENTO. Esto corre 24 veces por segundo de video en un VPS de 6 vCPU: las fuentes y la capa
de grano van cacheadas, y todo lo aleatorio (bordes rasgados, grano) usa semilla fija para que no
titile entre cuadros.

Sin dependencias nuevas: PIL y stdlib. numpy solo en el autotest.

    python videos/DAILY/fichas.py --autotest
"""
import functools, math, os, random, shutil, sys, tempfile, zlib
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))

W_FICHA, H_FICHA = 960, 1080
TIPOS = ["mapa", "versus", "titular", "dato", "serie", "cronologia", "calendario", "plano"]

# -------------------------------------------------------------- paleta cerrada (ESTILO.md 2.2)
PAPEL = (233, 223, 203)
TINTA = (34, 32, 28)
MADERA = (107, 74, 51)
MAPA = (220, 207, 180)
ROJO = (184, 64, 47)
AZUL = (43, 76, 111)
OCRE = (217, 164, 65)
# Lavados de tinta sobre papel. NO son colores nuevos: son el mismo par en dos mezclas.
GRIS = (140, 130, 114)
TENUE = (196, 184, 162)

# Geometria del panel. El diario reserva los 96 px de arriba para la cabecera comun del cuadro
# (`layout.py`), que la dibuja `escena.py` a lo ancho de los 1920: la ficha no la pisa.
CABECERA = 96
MX = 62                       # margen lateral
ANCHO = W_FICHA - 2 * MX      # 836
Y_TOP = 132
Y_BOT = H_FICHA - 64          # 1016

ENTRADA = 0.45                # segundos de la entrada de la hoja
_MED = ImageDraw.Draw(Image.new("RGB", (8, 8)))


# ================================================================ tipografia y texto
@functools.lru_cache(maxsize=256)
def _tt(nombres, px):
    for n in nombres:
        try:
            return ImageFont.truetype(n, px)
        except Exception:
            pass
    try:                                  # VPS pelado, sin Arial ni DejaVu: al menos respetar el
        return ImageFont.load_default(px)  # cuerpo pedido (Pillow >= 10.1), si no la maqueta se
    except TypeError:                      # va al diablo porque todo sale del mismo tamano
        return ImageFont.load_default()


def f(px, bold=False):
    """Palo seco: cuerpo de texto, rotulos, datos."""
    n = (("arialbd.ttf", "Arial-Bold.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf")
         if bold else ("arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"))
    return _tt(n, int(px))


def fs(px, bold=False):
    """Serif editorial: solo para el recorte de prensa y los numeros grandes."""
    n = (("georgiab.ttf", "GeorgiaPro-Bold.ttf", "timesbd.ttf", "DejaVuSerif-Bold.ttf",
          "LiberationSerif-Bold.ttf")
         if bold else ("georgia.ttf", "GeorgiaPro-Regular.ttf", "times.ttf", "DejaVuSerif.ttf",
                       "LiberationSerif-Regular.ttf"))
    return _tt(n, int(px))


def ancho_txt(txt, fnt):
    return _MED.textlength(txt, font=fnt)


def wrap(txt, fnt, maxw):
    """Envuelve por palabras. Una palabra mas larga que la caja se parte por letras: asi una URL
       o un nombre compuesto nunca se sale del marco."""
    out, linea = [], ""
    for p in str(txt).split():
        while ancho_txt(p, fnt) > maxw and len(p) > 1:      # palabra impartible: cortarla
            # el corte se estima por ancho medio y se ajusta de a una letra: buscarlo restando
            # desde el largo total es cuadratico y cuelga el render con una palabra de 900 letras
            corte = max(1, min(len(p) - 1, int(len(p) * maxw / max(1.0, ancho_txt(p, fnt)))))
            while corte > 1 and ancho_txt(p[:corte] + "-", fnt) > maxw:
                corte -= 1
            while corte < len(p) - 1 and ancho_txt(p[:corte + 1] + "-", fnt) <= maxw:
                corte += 1
            if linea:
                out.append(linea)
                linea = ""
            out.append(p[:corte] + "-")
            p = p[corte:]
        t = (linea + " " + p).strip()
        if ancho_txt(t, fnt) <= maxw:
            linea = t
        else:
            if linea:
                out.append(linea)
            linea = p
    if linea:
        out.append(linea)
    return out or [""]


def encajar(txt, maxw, maxh, px0, pxmin=15, bold=False, serif=False, interlinea=1.20,
            max_lineas=None):
    """Baja el cuerpo hasta que el texto entra en (maxw x maxh). Devuelve (fuente, lineas, alto_linea).
       Si ni en el cuerpo minimo entra, recorta lineas y cierra la ultima con puntos suspensivos:
       preferimos una ficha con menos palabras a una ficha con palabras cortadas por el marco.

       `max_lineas` es para los rotulos de una sola linea (el medio del recorte, la unidad, el
       `cuando` del calendario, el pie del mapa): el que llama dibuja `lineas[0]` y nada mas, asi
       que sin este tope el resto del texto se perdia MUDO, sin puntos suspensivos que avisaran."""
    fam = fs if serif else f
    maxw = max(24.0, float(maxw))   # una caja negativa (una unidad larga se comia el ancho de la
    px = int(px0)                   # cifra) hacia que `wrap` partiera el texto letra por letra
    while px >= pxmin:
        fnt = fam(px, bold)
        lh = int(round(px * interlinea))
        lineas = wrap(txt, fnt, maxw)
        if len(lineas) * lh <= maxh and (max_lineas is None or len(lineas) <= max_lineas):
            return fnt, lineas, lh
        px -= 2
    fnt = fam(pxmin, bold)
    lh = int(round(pxmin * interlinea))
    lineas = wrap(txt, fnt, maxw)
    cabe = max(1, int(maxh // lh))
    if max_lineas is not None:
        cabe = min(cabe, max(1, int(max_lineas)))
    if len(lineas) > cabe:
        lineas = lineas[:cabe]
        u = lineas[-1]
        while u and ancho_txt(u + "...", fnt) > maxw:
            u = u[:-1]
        lineas[-1] = u.rstrip() + "..."
    return fnt, lineas, lh


def bloque(d, xy, lineas, fnt, fill, lh):
    x, y = xy
    for ln in lineas:
        d.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y


def versalitas(d, xy, txt, fnt, fill, sep=3):
    """Rotulo espaciado, como un pie de imprenta. Devuelve la x final."""
    x, y = xy
    for ch in str(txt):
        d.text((x, y), ch, font=fnt, fill=fill)
        x += ancho_txt(ch, fnt) + sep
    return x - sep


# ================================================================ papel, tarjetas, sellos
@functools.lru_cache(maxsize=8)
def _capa_grano(w, h, fuerza):
    """Cacheada y con semilla fija: el grano tiene que ser IDENTICO en todos los cuadros o titila."""
    r = random.Random(7)
    n = Image.new("L", (max(1, w // 2), max(1, h // 2)))
    n.putdata([r.randint(128 - fuerza, 128 + fuerza) for _ in range(n.width * n.height)])
    n = n.resize((w, h), Image.BILINEAR).filter(ImageFilter.GaussianBlur(0.4))
    return Image.merge("RGB", (n, n, n))


def grano(im, fuerza=7):
    return Image.blend(im, _capa_grano(im.width, im.height, fuerza), 0.10)


def tarjeta(im, box, fill, rot=0.0, sombra=95):
    """Tarjeta de papel con sombra corta y un grado de rotacion. Identica a layout.py."""
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    w, h = x1 - x0, y1 - y0
    pad = 50
    sh = Image.new("L", (w + pad * 2, h + pad * 2), 0)
    ImageDraw.Draw(sh).rectangle([pad + 5, pad + 9, pad + w + 5, pad + h + 9], fill=sombra)
    sh = sh.filter(ImageFilter.GaussianBlur(11))
    cap = Image.new("RGBA", sh.size, (0, 0, 0, 0))
    cap.paste(Image.new("RGB", sh.size, (60, 52, 40)), (0, 0), sh)
    ImageDraw.Draw(cap).rectangle([pad, pad, pad + w, pad + h], fill=tuple(fill) + (255,))
    if rot:
        cap = cap.rotate(rot, resample=Image.BICUBIC, expand=False)
    im.paste(cap, (x0 - pad, y0 - pad), cap)


def tarjeta_rasgada(im, box, fill, rot=0.0, semilla=3, dientes=26, prof=13):
    """Igual que `tarjeta` pero con el borde de abajo arrancado a mano. Es el recorte de prensa."""
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    w, h = x1 - x0, y1 - y0
    pad = 50
    r = random.Random(semilla)                      # semilla fija: el desgarro no cambia por cuadro
    borde = [(pad + i * w / dientes, pad + h - r.randint(0, prof)) for i in range(dientes + 1)]
    forma = [(pad, pad), (pad + w, pad)] + list(reversed(borde))
    sh = Image.new("L", (w + pad * 2, h + pad * 2), 0)
    ImageDraw.Draw(sh).polygon([(x + 5, y + 9) for x, y in forma], fill=95)
    sh = sh.filter(ImageFilter.GaussianBlur(11))
    cap = Image.new("RGBA", sh.size, (0, 0, 0, 0))
    cap.paste(Image.new("RGB", sh.size, (60, 52, 40)), (0, 0), sh)
    ImageDraw.Draw(cap).polygon(forma, fill=tuple(fill) + (255,))
    if rot:
        cap = cap.rotate(rot, resample=Image.BICUBIC, expand=False)
    im.paste(cap, (x0 - pad, y0 - pad), cap)


def sello(im, xy, lineas, color, ancho, alto, rot=-1.4, grosor=5):
    """Sello de goma: marco y texto, girado un pelo. `lineas` = [(texto, px, bold, dy)]."""
    st = Image.new("RGBA", (int(ancho), int(alto)), (0, 0, 0, 0))
    ds = ImageDraw.Draw(st)
    ds.rectangle([3, 3, int(ancho) - 4, int(alto) - 4], outline=color, width=grosor)
    for (txt, px, bold, dy) in lineas:
        ds.text((26, dy), txt, font=f(px, bold), fill=color)
    st = st.rotate(rot, resample=Image.BICUBIC, expand=False)
    im.paste(st, (int(xy[0]), int(xy[1])), st)


def regla(d, x, y, largo=116, color=TINTA, grosor=5):
    d.line([(x, y), (x + largo, y)], fill=color, width=grosor)


# ================================================================ la regla del rojo, por codigo
class _Rojo:
    """Como maximo UN elemento rojo por ficha (ESTILO.md 2.2). Los usos se agrupan por etiqueta:
       los tres puntos en disputa de un mapa son UN elemento, no tres."""

    def __init__(self):
        self.usos = set()

    def __call__(self, etiqueta):
        self.usos.add(etiqueta)
        if len(self.usos) > 1:
            raise ValueError("dos elementos rojos en la misma ficha: %s" % sorted(self.usos))
        return ROJO


# ================================================================ utilidades varias
def _eo(u):
    u = max(0.0, min(1.0, u))
    return 1 - (1 - u) ** 3


def _pop(t, t0, dur=0.24):
    """Progreso 0..1 de un elemento que entra en t0. Devuelve (alpha, escala)."""
    u = _eo((t - t0) / dur) if dur > 0 else 1.0
    return u, 0.72 + 0.28 * u


def _mezcla(c0, c1, u):
    return tuple(int(round(a + (b - a) * u)) for a, b in zip(c0, c1))


def _g(datos, clave, defecto=""):
    v = datos.get(clave, defecto) if isinstance(datos, dict) else defecto
    return defecto if v is None else v


def _semilla(datos):
    """Semilla estable a partir del contenido: el mismo dato da siempre el mismo desgarro.

       crc32 y NO `hash()`: el hash de un str esta salado por proceso (PYTHONHASHSEED), asi que el
       MISMO cuadro salia distinto en cada corrida. El render del diario es resumible (`daily.py`
       arranca desde el ultimo cuadro escrito, en otro proceso): con `hash()`, el borde rasgado del
       recorte y el subrayado rojo pegaban un salto justo en el cuadro donde se retomo."""
    try:
        crudo = repr(sorted(datos.items())) if isinstance(datos, dict) else repr(datos)
    except TypeError:                                  # claves que no se comparan entre si
        crudo = repr(datos)
    return zlib.crc32(crudo.encode("utf-8", "replace")) % 10 ** 6


def _disco(d, xy, r, fill, outline=None, grosor=4):
    x, y = xy
    d.ellipse([x - r, y - r, x + r, y + r], fill=fill, outline=outline, width=grosor)


def _rotulo(d, txt, y=Y_TOP - 34, color=GRIS):
    versalitas(d, (MX, y), str(txt).upper(), f(21, True), color, sep=3)


def _titulo(d, txt, y, maxw=ANCHO, px=52, maxh=210, color=TINTA):
    """Titulo de ficha con su regla debajo. Devuelve la y libre."""
    fnt, lineas, lh = encajar(txt, maxw, maxh, px, pxmin=26, bold=True)
    y2 = bloque(d, (MX, y), lineas, fnt, color, lh)
    regla(d, MX, y2 + 16)
    return y2 + 40


# ================================================================ FICHA 1 - mapa
# Hojas fijas, en grados (lon0, lon1, lat0, lat1). Proyeccion equirectangular con el paralelo
# medio como estandar, que es lo que hace que Europa no salga estirada a lo ancho.
HOJAS = {
    "mundo":         (-170, 180, -56, 78),
    "europa":        (-12, 46, 34, 67),
    "europa_este":   (20, 46, 44, 60),
    "americas":      (-122, -32, -56, 50),
    "sudamerica":    (-82, -33, -56, 14),
    "atlantico_sur": (-76, -52, -57, -33),
    "asia":          (26, 150, -12, 56),
    "medio_oriente": (24, 64, 11, 42),
    "africa":        (-20, 52, -36, 38),
    "pacifico":      (100, 205, -48, 32),   # llega hasta Hawai (202 E)
}

# TODO(hojas reales) --------------------------------------------------------------------------
# Aca se enganchan las hojas de `produccion/mapa_*.py`. Esas hojas ya dejan dos cosas en
# `produccion/assets/`: el PNG de la base (mapa04_base.png, mapa_mundo.png, ...) y un
# `mapa*_pts.json` con los pixeles de cada sitio, que sale de la MISMA `proj()` con la que se
# dibujo el PNG. El enganche es:
#   1) `HOJAS_REALES[hoja] = ("assets/mapa04_base.png", (LON0, LON1, LAT0, LAT1), mercator_bool)`
#      copiando los limites del encabezado del script que genero el PNG -- son la unica fuente
#      de verdad de la proyeccion y NO se deducen de la imagen;
#   2) `_proyector()` devuelve la proyeccion de esa hoja (Mercator en los mapa_*.py, no la
#      equirectangular de abajo) en vez de la generica;
#   3) `_fondo_mapa()` pega el PNG escalado al marco en lugar de dibujar el rectangulo plano.
# Hasta que eso este, `mapa` dibuja marco + graticula + puntos + etiquetas, que es todo lo que la
# ficha necesita para validarse contra el guion.
# OJO, decision pendiente: HOY una `hoja` que no esta en el catalogo NO aborta; `_limites()` le
# arma una hoja a medida con los puntos del guion. O sea que un nombre mal escrito ("mideast",
# "medio oriente ") sale igual, con los puntos exactos pero sobre un encuadre que nadie pidio. La
# regla 24 se hace cumplir sobre los PUNTOS (abajo, contra los limites de la hoja), no sobre el
# nombre de la hoja. Si se quiere que un nombre desconocido corte el render, va aca.
HOJAS_REALES = {}


def _limites(hoja, puntos):
    """Limites de la hoja. Si la hoja no esta en el catalogo, se deducen de los puntos con aire."""
    if hoja in HOJAS:
        return HOJAS[hoja]
    if not puntos:
        return HOJAS["mundo"]
    lons = [float(p.get("lon", 0.0)) for p in puntos]
    lats = [float(p.get("lat", 0.0)) for p in puntos]
    lon0, lon1 = min(lons), max(lons)
    lat0, lat1 = min(lats), max(lats)
    dl = max(lon1 - lon0, 4.0) * 0.30
    dt = max(lat1 - lat0, 3.0) * 0.30
    return (lon0 - dl, lon1 + dl, lat0 - dt, lat1 + dt)


def _proyector(lim, caja):
    """Equirectangular con correccion por el paralelo medio. Los limites se ENSANCHAN hasta la
       proporcion del marco: la hoja llena el panel en vez de dejar dos bandas de papel muerto,
       y como se ensancha (nunca se recorta), ningun punto se queda afuera.
       Devuelve (proj, limites_ajustados)."""
    lon0, lon1, lat0, lat1 = lim
    k = max(0.18, math.cos(math.radians((lat0 + lat1) / 2.0)))
    x0, y0, x1, y1 = caja
    cw, ch = float(x1 - x0), float(y1 - y0)
    dw, dh = (lon1 - lon0) * k, (lat1 - lat0)
    if dw / dh < cw / ch:
        nuevo = dh * (cw / ch) / k
        c = (lon0 + lon1) / 2.0
        lon0, lon1 = c - nuevo / 2, c + nuevo / 2
    else:
        nuevo = dw * (ch / cw)
        c = (lat0 + lat1) / 2.0
        lat0, lat1 = c - nuevo / 2, c + nuevo / 2
    s = ch / (lat1 - lat0)

    def proj(lon, lat):
        lon = float(lon)
        if lon < lon0:                       # hojas que cruzan el antimeridiano (pacifico)
            lon += 360.0
        return (x0 + (lon - lon0) * k * s, y0 + (lat1 - float(lat)) * s)

    return proj, (lon0, lon1, lat0, lat1)


def _paso_grat(span):
    for p in (2, 5, 10, 15, 20, 30, 45):
        if span / p <= 9:
            return p
    return 60


def ficha_mapa(im, d, datos, t, rojo):
    """{"hoja","puntos":[{"nombre","lat","lon","rojo"}],"flechas":[{"de","a"}]}"""
    hoja = str(_g(datos, "hoja", "mundo")).strip().lower().replace(" ", "_")
    puntos = [p for p in _g(datos, "puntos", []) if isinstance(p, dict)]
    flechas = _g(datos, "flechas", []) or []

    _rotulo(d, hoja.replace("_", " "))
    titulo = _g(datos, "titulo", "")
    y = Y_TOP
    if titulo:
        y = _titulo(d, titulo, y, px=44, maxh=112)

    caja = (MX, y + 6, MX + ANCHO, Y_BOT - 58)
    proj, lim = _proyector(_limites(hoja, puntos), caja)

    # la hoja: rectangulo de papel de mapa, graticula tenue y marcas de registro en las esquinas
    tarjeta(im, caja, MAPA, rot=0.0)
    x0, y0, x1, y1 = [int(round(v)) for v in caja]
    lon0, lon1, lat0, lat1 = lim
    pl, pt = _paso_grat(lon1 - lon0), _paso_grat(lat1 - lat0)
    lon = math.ceil(lon0 / pl) * pl
    while lon <= lon1:
        gx = proj(lon, lat0)[0]
        if x0 + 2 < gx < x1 - 2:
            d.line([(gx, y0 + 2), (gx, y1 - 2)], fill=TENUE, width=2)
        lon += pl
    lat = math.ceil(lat0 / pt) * pt
    while lat <= lat1:
        gy = proj(lon0, lat)[1]
        if y0 + 2 < gy < y1 - 2:
            d.line([(x0 + 2, gy), (x1 - 2, gy)], fill=TENUE, width=2)
        lat += pt
    d.rectangle([x0, y0, x1, y1], outline=TINTA, width=4)
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([(cx + 16 * sx, cy + 9 * sy), (cx + 58 * sx, cy + 9 * sy)], fill=GRIS, width=3)
        d.line([(cx + 9 * sx, cy + 16 * sy), (cx + 9 * sx, cy + 58 * sy)], fill=GRIS, width=3)

    # flechas primero: van por debajo de los puntos
    por_nombre = {str(p.get("nombre", "")).lower(): p for p in puntos}

    def sitio(v):
        if isinstance(v, dict):
            return proj(v.get("lon", 0), v.get("lat", 0))
        if isinstance(v, (list, tuple)) and len(v) >= 2:
            return proj(v[1], v[0])                     # [lat, lon], como el resto del repo
        p = por_nombre.get(str(v).lower())
        return proj(p["lon"], p["lat"]) if p else None

    for i, fl in enumerate(flechas):
        if isinstance(fl, (list, tuple)) and len(fl) == 2:
            a, b = sitio(fl[0]), sitio(fl[1])
        elif isinstance(fl, dict):
            a = sitio(fl.get("de", fl.get("desde", fl.get("origen"))))
            b = sitio(fl.get("a", fl.get("hasta", fl.get("destino"))))
        else:
            a = b = None
        if a and b:
            # el escalonado se topea: `render_ficha` congela la ficha en ASENTADA, asi que un
            # revel que arranque despues de eso no termina NUNCA (mapa de 6 flechas = una flecha
            # dibujada a medias durante todo el plano)
            _flecha(d, a, b, AZUL, _eo((t - 0.30 - min(0.12 * i, 0.30)) / 0.55))

    # los puntos. El rojo es UN elemento: el conjunto de lo que esta en disputa.
    for i, p in enumerate(puntos):
        nombre = str(p.get("nombre", "")).strip()
        try:
            lat, lon = float(p.get("lat", 0)), float(p.get("lon", 0))
        except (TypeError, ValueError):
            raise ValueError("regla 24: el punto %r no tiene lat/lon numericas: %r" % (nombre, p))
        px, py = proj(lon, lat)
        # REGLA 24: los puntos son exactos. Un punto que cae fuera de la hoja que pidio el guion
        # es un error de datos, y se aborta el render en vez de arrastrarlo al borde del marco:
        # una ficha que miente sobre donde queda algo es peor que una ficha que no sale.
        if not (x0 - 1 <= px <= x1 + 1 and y0 - 1 <= py <= y1 + 1):
            raise ValueError("regla 24: %r (lat %.2f, lon %.2f) cae fuera de la hoja %r %s"
                             % (nombre or "sin nombre", lat, lon, hoja,
                                tuple(round(v, 2) for v in lim)))
        es_rojo = bool(p.get("rojo"))
        col = rojo("puntos en disputa") if es_rojo else AZUL
        u, sc = _pop(t, 0.16 + min(0.07 * i, 0.56))     # topeado: ver la nota de las flechas
        r = (13 if es_rojo else 10) * sc
        if u <= 0.02:
            continue
        cf = _mezcla(MAPA, col, u)
        if es_rojo:
            d.ellipse([px - r * 2.1, py - r * 2.1, px + r * 2.1, py + r * 2.1],
                      outline=_mezcla(MAPA, col, u * 0.55), width=3)
        _disco(d, (px, py), r, cf, _mezcla(MAPA, TINTA, u), 3)
        if not nombre:
            continue
        fn = f(25, True)
        w = ancho_txt(nombre, fn)
        lx, ly = px + r + 14, py - 17
        if lx + w + 16 > x1 - 10:                        # no cabe a la derecha: va a la izquierda
            lx = px - r - 14 - w - 16
        ly = max(y0 + 8, min(y1 - 46, ly))
        d.rectangle([lx - 8, ly - 5, lx + w + 8, ly + 33], fill=MAPA)
        d.text((lx, ly), nombre, font=fn, fill=_mezcla(MAPA, TINTA, u))

    pie = _g(datos, "pie", "")
    if pie:
        fn, ln, lh = encajar(pie, ANCHO, 44, 23, pxmin=16, max_lineas=1)
        bloque(d, (MX, Y_BOT - 40), ln, fn, GRIS, lh)


def _flecha(d, a, b, color, u):
    """Arco punteado con punta. `u` 0..1 la va dibujando."""
    u = max(0.0, min(1.0, u))
    if u <= 0.01:
        return
    ax, ay = a
    bx, by = b
    mx, my = (ax + bx) / 2.0, (ay + by) / 2.0
    dx, dy = bx - ax, by - ay
    largo = math.hypot(dx, dy) or 1.0
    cx, cy = mx - dy * 0.18, my + dx * 0.18          # control del arco, perpendicular
    N = 46
    pts = []
    for i in range(N + 1):
        s = i / N
        pts.append(((1 - s) ** 2 * ax + 2 * (1 - s) * s * cx + s * s * bx,
                    (1 - s) ** 2 * ay + 2 * (1 - s) * s * cy + s * s * by))
    n = max(2, int(round((N + 1) * u)))
    for i in range(0, n - 1, 2):                     # a rayas: dos si, uno no
        d.line([pts[i], pts[min(i + 1, n - 1)]], fill=color, width=5)
    if u > 0.9 and largo > 30:
        p0, p1 = pts[-6], pts[-1]
        ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        for s in (2.6, -2.6):
            d.line([p1, (p1[0] + 24 * math.cos(ang + s), p1[1] + 24 * math.sin(ang + s))],
                   fill=color, width=5)


# ================================================================ FICHA 2 - versus (la insignia)
def ficha_versus(im, d, datos, t, rojo):
    """{"titulo","izq":{"actor","dice","fuentes"},"der":{...},"pie"}

    La ficha insignia: la separacion HECHO / AFIRMACION hecha imagen. Lo que tiene que quedar
    claro de un vistazo es QUIEN DICE QUE -- por eso el actor va arriba de cada tarjeta, con su
    color y la palabra `claims` pegada -- y en que estado esta la evidencia, que es el pie y es
    el unico rojo del cuadro."""
    izq = _g(datos, "izq", {}) or {}
    der = _g(datos, "der", {}) or {}
    _rotulo(d, "claim  vs  claim")
    y = _titulo(d, _g(datos, "titulo", "DISPUTED"), Y_TOP, px=52, maxh=200)

    # el sello del pie se dimensiona primero: el resto del alto es para las dos tarjetas
    pie = str(_g(datos, "pie", "independent evidence insufficient")).upper()
    fp, lp, lhp = encajar(pie, 560, 96, 33, pxmin=21, bold=True)
    sw = int(max(ancho_txt(l, fp) for l in lp)) + 60
    sh = len(lp) * lhp + 46
    sy = Y_BOT - sh

    top = y + 8
    hueco = 30
    alto = int((sy - 30 - top - hueco) / 2)
    alto = max(150, alto)

    for idx, (col, cara) in enumerate(((AZUL, izq), (OCRE, der))):
        cy = top + idx * (alto + hueco)
        tarjeta(im, (MX, cy, MX + ANCHO, cy + alto), MAPA, rot=(-0.4 if idx == 0 else 0.35))
        d.rectangle([MX, cy, MX + 13, cy + alto], fill=col)
        actor = str(_g(cara, "actor", "?")).upper() + "   claims"
        fa, la, lha = encajar(actor, ANCHO - 92, 40, 30, pxmin=20, bold=True, max_lineas=1)
        d.text((MX + 40, cy + 22), la[0], font=fa, fill=col)
        fuentes = str(_g(cara, "fuentes", ""))
        hf = 34 if fuentes else 0
        ft, lt, lht = encajar(_g(cara, "dice", ""), ANCHO - 92, alto - 84 - hf, 33, pxmin=19)
        bloque(d, (MX + 40, cy + 72), lt, ft, TINTA, lht)
        if fuentes:
            ff, lf, _ = encajar(fuentes, ANCHO - 92, 30, 22, pxmin=15, max_lineas=1)
            d.text((MX + 40, cy + alto - 40), lf[0], font=ff, fill=GRIS)

    # EL rojo: el estado de la evidencia. Entra a los 0,5 s, como un sello que se apoya.
    u, _ = _pop(t, 0.50, 0.28)
    if u > 0.02:
        c = _mezcla(PAPEL, rojo("sello de evidencia"), u)
        sello(im, (MX, sy), [(l, fp.size, True, 22 + i * lhp) for i, l in enumerate(lp)],
              c, sw, sh, rot=-1.5)


# ================================================================ FICHA 3 - titular
def ficha_titular(im, d, datos, t, rojo):
    """{"medio","fecha","titular","bajada"} -- recorte de prensa con el borde de abajo arrancado."""
    _rotulo(d, "in the press")
    cx0, cy0 = MX, Y_TOP + 6
    cx1, cy1 = MX + ANCHO, Y_BOT - 120
    tarjeta_rasgada(im, (cx0, cy0, cx1, cy1), MAPA, rot=-0.7, semilla=_semilla(datos))

    px, py = cx0 + 40, cy0 + 34
    pw = (cx1 - cx0) - 80
    medio = str(_g(datos, "medio", "")).upper()
    fm, lm, _ = encajar(medio, pw - 220, 48, 38, pxmin=20, bold=True, serif=True, max_lineas=1)
    d.text((px, py), lm[0], font=fm, fill=TINTA)
    fecha = str(_g(datos, "fecha", ""))
    ffe = f(23)
    d.text((px + pw - ancho_txt(fecha, ffe), py + 12), fecha, font=ffe, fill=GRIS)
    py += 58
    d.line([(px, py), (px + pw, py)], fill=TINTA, width=3)
    d.line([(px, py + 7), (px + pw, py + 7)], fill=TINTA, width=1)
    py += 30

    ft, lt, lht = encajar(_g(datos, "titular", ""), pw, 300, 54, pxmin=28, bold=True, serif=True,
                          interlinea=1.14)
    y_tit = py
    py = bloque(d, (px, py), lt, ft, TINTA, lht)

    # EL rojo: el subrayado de marcador sobre el titular, que es lo que la ficha pone en cuestion.
    u = _eo((t - 0.34) / 0.42)
    if u > 0.02:
        c = rojo("subrayado del titular")
        yy = y_tit + (len(lt) - 1) * lht + ft.size + 8
        w = int(ancho_txt(lt[-1], ft) * u)
        r = random.Random(_semilla(datos) + 1)
        xx = px
        while xx < px + w:
            paso = min(24, px + w - xx)
            d.line([(xx, yy + r.randint(-2, 2)), (xx + paso, yy + r.randint(-2, 2))], fill=c, width=6)
            xx += paso

    py += 22
    bajada = _g(datos, "bajada", "")
    if bajada:
        fb, lb, lhb = encajar(bajada, pw, 150, 30, pxmin=18)
        py = bloque(d, (px, py), lb, fb, TINTA, lhb) + 18

    # pautas de cuerpo de texto: el recorte sigue, pero no se lee. Nunca texto ajeno de verdad.
    r = random.Random(_semilla(datos) + 2)
    while py < cy1 - 46:
        d.line([(px, py), (px + int(pw * r.uniform(0.55, 1.0)), py)], fill=TENUE, width=7)
        py += 22

    pie = "clipped from the source · full link in the description"
    d.text((MX, Y_BOT - 44), pie, font=f(22), fill=GRIS)


# ================================================================ FICHA 4 - dato
def _cifra_y_unidad(numero, unidad, pw):
    """Ajusta la cifra y su unidad al ancho `pw`. Devuelve (fnum, cifra, fu, unidad, ancho_unidad).

       La unidad se lleva como mucho el 45% del ancho; lo que queda es de la cifra, y la cifra va
       ENTERA en una linea. Sin este reparto, una unidad larga ("million barrels per day
       (seaborne)") dejaba a la cifra con ancho negativo: `wrap` la partia letra por letra y la
       ficha dibujaba "1-" en rojo. La ficha que existe para poner una cifra bajo escrutinio
       mostraba otra cifra, y ningun chequeo de pixeles lo iba a notar."""
    fu, wu = f(46, True), 0
    if unidad:
        fu, lu, _ = encajar(unidad, int(pw * 0.45), 64, 46, pxmin=20, bold=True, max_lineas=1)
        unidad = lu[0]
        wu = ancho_txt(unidad, fu) + 24
    fnum, lnum, _ = encajar(numero, pw - wu, 230, 200, pxmin=30, bold=True, serif=True,
                            max_lineas=1)
    return fnum, lnum[0], fu, unidad, wu


def ficha_dato(im, d, datos, t, rojo):
    """{"numero","unidad","etiqueta","contexto"} -- la cifra es lo que la ficha somete a escrutinio,
       asi que la cifra es el rojo."""
    _rotulo(d, "the number")
    y = Y_TOP + 30
    tarjeta(im, (MX, y, MX + ANCHO, Y_BOT - 6), MAPA, rot=0.35)

    px, pw = MX + 46, ANCHO - 92
    fnum, cifra, fu, unidad, wu = _cifra_y_unidad(str(_g(datos, "numero", "0")),
                                                  str(_g(datos, "unidad", "")), pw)
    fe, le, lhe = encajar(str(_g(datos, "etiqueta", "")).upper(), pw, 130, 36, pxmin=20, bold=True)
    ctx = _g(datos, "contexto", "")
    libre = (Y_BOT - 6) - y - 120 - int(fnum.size * 1.18) - len(le) * lhe
    fc, lc, lhc = encajar(ctx, pw, max(40, libre), 32, pxmin=18) if ctx else (f(32), [], 38)

    # el bloque entero se centra en la tarjeta: una cifra pegada al borde de arriba deja el
    # panel descompensado, y este es el unico contenido de la ficha
    alto = int(fnum.size * 1.18) + 52 + len(le) * lhe + (26 + len(lc) * lhc if lc else 0)
    ny = y + max(46, ((Y_BOT - 6) - y - alto) // 2)

    u, _sc = _pop(t, 0.12, 0.34)
    c = _mezcla(MAPA, rojo("la cifra"), u)
    d.text((px, ny), cifra, font=fnum, fill=c)
    if unidad:
        d.text((px + ancho_txt(cifra, fnum) + 22, ny + max(0, fnum.size - fu.size - 4)), unidad,
               font=fu, fill=_mezcla(MAPA, TINTA, u))
    ny += int(fnum.size * 1.18) + 18
    d.line([(px, ny), (px + 140, ny)], fill=TINTA, width=6)
    ny = bloque(d, (px, ny + 34), le, fe, TINTA, lhe)
    if lc:
        bloque(d, (px, ny + 26), lc, fc, _mezcla(TINTA, GRIS, 0.35), lhc)


# ================================================================ FICHA 5 - serie
def _escala(v0, v1, n=4):
    """Ticks redondos para el eje y."""
    span = float(v1 - v0)
    if span <= 0:
        span = abs(v1) or 1.0
    bruto = span / max(1, n)
    mag = 10 ** math.floor(math.log10(bruto)) if bruto > 0 else 1.0
    paso = mag * 10
    for m in (1, 2, 2.5, 5, 10):
        if bruto <= m * mag:
            paso = m * mag
            break
    lo = math.floor(v0 / paso) * paso
    hi = math.ceil(v1 / paso) * paso
    ticks, v = [], lo
    while v <= hi + paso * 1e-6:
        ticks.append(round(v, 10))
        v += paso
    return lo, hi, ticks, paso


def _fmt(v, paso):
    """Etiqueta de un TICK del eje: la precision la manda el paso, que es lo que separa dos ticks."""
    dec = 0 if paso >= 1 else min(3, int(round(-math.log10(paso))) + 1)
    s = ("%%.%df" % dec) % v
    return s.rstrip("0").rstrip(".") if dec and "." in s else s


def _fmt_valor(v):
    """Etiqueta del DATO, que no es lo mismo: con paso 5, `_fmt` convertia 88.7 en '89' y la ficha
       terminaba diciendo un numero que la serie no dice. El valor se muestra como viene."""
    try:
        if float(v).is_integer():
            return "%d" % int(v)
    except (OverflowError, ValueError):
        return str(v)
    s = "%.2f" % v
    return s.rstrip("0").rstrip(".")


def _numero(v):
    """float(v) o None. Un '' / None / 'n/d' / inf en la serie no puede tumbar la corrida."""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def ficha_serie(im, d, datos, t, rojo):
    """{"titulo","unidad","puntos":[[x,y],...],"nota"} -- x numerico o etiqueta."""
    _rotulo(d, "the trend")
    y = _titulo(d, _g(datos, "titulo", ""), Y_TOP, px=44, maxh=112)

    crudos = [p for p in _g(datos, "puntos", []) if isinstance(p, (list, tuple)) and len(p) >= 2]
    # un valor que no es numero (None, "n/d", "", inf) tira ese punto y la serie sale con el resto:
    # a las 05:00 no hay nadie para arreglar un guion, y media serie dice mas que una ficha caida
    crudos = [p for p in crudos if _numero(p[1]) is not None]
    xs_num = all(_numero(p[0]) is not None for p in crudos) if crudos else False
    xs = [_numero(p[0]) for p in crudos] if xs_num else list(range(len(crudos)))
    ys = [_numero(p[1]) for p in crudos]
    etq = [_fmt_valor(p[0]) if xs_num else str(p[0]) for p in crudos]

    unidad = str(_g(datos, "unidad", ""))
    nota = _g(datos, "nota", "")
    hn = 0
    if nota:
        fnn, lnn, lhn = encajar(nota, ANCHO, 78, 24, pxmin=17)
        hn = len(lnn) * lhn + 16

    caja = (MX, y + 10, MX + ANCHO, Y_BOT - 50 - hn)
    tarjeta(im, caja, MAPA, rot=0.0)
    x0, y0, x1, y1 = [int(round(v)) for v in caja]
    pl, pr, pt, pb = 96, 60, 52, 62                   # margenes internos del area de dibujo
    gx0, gy0, gx1, gy1 = x0 + pl, y0 + pt, x1 - pr, y1 - pb

    if not ys:
        d.text((gx0, gy0), "no data", font=f(30), fill=GRIS)
        if nota:                       # la nota es de donde salen los datos: no se cae en silencio
            bloque(d, (MX, y1 + 22), lnn, fnn, GRIS, lhn)
        return

    lo, hi, ticks, paso = _escala(min(ys), max(ys))
    xmin, xmax = min(xs), max(xs)
    sx = (gx1 - gx0) / ((xmax - xmin) or 1.0)
    sy = (gy1 - gy0) / ((hi - lo) or 1.0)

    ft = f(22)
    for v in ticks:
        yy = gy1 - (v - lo) * sy
        d.line([(gx0, yy), (gx1, yy)], fill=TENUE, width=2)
        lb = _fmt(v, paso)
        d.text((gx0 - 14 - ancho_txt(lb, ft), yy - 13), lb, font=ft, fill=GRIS)
    d.line([(gx0, gy0 - 14), (gx0, gy1)], fill=TINTA, width=4)
    d.line([(gx0, gy1), (gx1 + 10, gy1)], fill=TINTA, width=4)
    if unidad:
        d.text((gx0 - 14 - ancho_txt(unidad, f(22, True)), gy0 - 42), unidad, font=f(22, True),
               fill=TINTA)

    pts = [(gx0 + (x - xmin) * sx, gy1 - (v - lo) * sy) for x, v in zip(xs, ys)]
    u = _eo((t - 0.18) / 0.70)
    n = max(2, int(math.ceil((len(pts) - 1) * u)) + 1) if len(pts) > 1 else 1
    vis = pts[:n]
    if len(vis) > 1:
        d.line(vis, fill=AZUL, width=6, joint="curve")
    for p in vis[:-1]:
        _disco(d, p, 7, MAPA, AZUL, 4)

    # EL rojo: el ultimo valor, que es el que esta en juego.
    if u > 0.96 and pts:
        c = rojo("ultimo valor")
        lx, ly = pts[-1]
        _disco(d, (lx, ly), 13, c, TINTA, 3)
        lb = _fmt_valor(ys[-1]) + ((" " + unidad) if unidad else "")   # el dato, no el redondeo
        fl = f(27, True)
        w = ancho_txt(lb, fl)
        bx = min(lx + 22, x1 - 20 - w - 24)
        d.rectangle([bx, ly - 24, bx + w + 24, ly + 20], fill=c)
        d.text((bx + 12, ly - 18), lb, font=fl, fill=PAPEL)

    # eje x: primera, media y ultima etiqueta, sin encimarse
    fx = f(22)
    for i in (0, len(etq) // 2, len(etq) - 1):
        if 0 <= i < len(etq):
            lb = etq[i]
            w = ancho_txt(lb, fx)
            ex = min(max(gx0, pts[i][0] - w / 2), gx1 - w)
            d.text((ex, gy1 + 16), lb, font=fx, fill=GRIS)

    if nota:
        bloque(d, (MX, y1 + 22), lnn, fnn, GRIS, lhn)


# ================================================================ FICHA 6 - cronologia
def _lista_ajustada(items, alto_total, alto_min, alto_max):
    """Cuantos items entran y con que alto cada uno. Nunca devuelve un alto menor que `alto_min`:
       si no entran todos, entran menos y el resto se resume en una linea."""
    n = len(items)
    if n == 0:
        return 0, alto_max
    h = alto_total / n
    if h >= alto_min:
        return n, min(alto_max, h)
    cabe = max(1, int(alto_total // alto_min) - 1)     # una fila se reserva para el "+N more"
    return cabe, alto_min


def ficha_cronologia(im, d, datos, t, rojo):
    """{"titulo","hitos":[{"hora","texto"}]} -- el hito mas reciente es el rojo."""
    _rotulo(d, "how the day ran")
    y = _titulo(d, _g(datos, "titulo", ""), Y_TOP, px=46, maxh=160)

    hitos = [h for h in _g(datos, "hitos", []) if isinstance(h, dict)]
    disp = (Y_BOT - 10) - (y + 20)
    n, alto = _lista_ajustada(hitos, disp, 92, 150)
    ejex = MX + 136
    y0 = y + 26
    if n:
        d.line([(ejex, y0 - 6), (ejex, y0 + (n - 1) * alto + 16)], fill=TENUE, width=5)

    marcado = max(0, len(hitos) - 1)                   # por defecto, el ultimo
    for i, h in enumerate(hitos):
        if h.get("rojo"):
            marcado = i
    if marcado >= n:                                   # el marcado no entro en la ficha: el rojo
        marcado = max(0, n - 1)                        # lo lleva el ultimo visible. Una ficha SIN
    # su elemento rojo rompe la regla del rojo igual que una con dos, y asi salia toda cronologia
    # con mas hitos de los que entran.

    for i, h in enumerate(hitos[:n]):
        cy = int(y0 + i * alto)
        u, sc = _pop(t, 0.14 + min(0.08 * i, 0.60))    # topeado: tiene que terminar en ASENTADA
        es = (i == marcado)
        col = rojo("hito mas reciente") if es else AZUL
        hora = str(_g(h, "hora", ""))
        fh = f(27, True)
        d.text((ejex - 30 - ancho_txt(hora, fh), cy - 4), hora, font=fh,
               fill=_mezcla(PAPEL, TINTA if not es else col, max(0.25, u)))
        _disco(d, (ejex, cy + 10), (13 if es else 9) * sc, _mezcla(PAPEL, col, u),
               _mezcla(PAPEL, TINTA, u), 3)
        ft, lt, lht = encajar(_g(h, "texto", ""), MX + ANCHO - (ejex + 34), alto - 20, 31, pxmin=18)
        bloque(d, (ejex + 34, cy - 8), lt, ft, _mezcla(PAPEL, TINTA, max(0.3, u)), lht)

    if n < len(hitos):
        d.text((ejex + 34, int(y0 + n * alto)), "+ %d more in the log" % (len(hitos) - n),
               font=f(26, True), fill=GRIS)


# ================================================================ FICHA 7 - calendario
def ficha_calendario(im, d, datos, t, rojo):
    """{"titulo","fechas":[{"cuando","que","donde"}]} -- la fecha mas proxima es el rojo.
       Es la firma del formato (WHAT TO WATCH): no predice, lista lo que ya tiene fecha."""
    _rotulo(d, "what to watch")
    y = _titulo(d, _g(datos, "titulo", "WHAT TO WATCH"), Y_TOP, px=46, maxh=120)

    fechas = [x for x in _g(datos, "fechas", []) if isinstance(x, dict)]
    disp = (Y_BOT - 6) - (y + 16)
    n, alto = _lista_ajustada(fechas, disp, 104, 208)
    hueco = 14
    alto = alto - hueco

    marcado = 0                                        # la primera de la lista es la mas proxima
    for i, x in enumerate(fechas):
        if x.get("rojo"):
            marcado = i
    if marcado >= n:                                   # ver la nota de `ficha_cronologia`
        marcado = max(0, n - 1)

    for i, x in enumerate(fechas[:n]):
        cy = int(y + 22 + i * (alto + hueco))
        u, _ = _pop(t, 0.12 + min(0.08 * i, 0.60), 0.30)
        es = (i == marcado)
        col = rojo("fecha mas proxima") if es else AZUL
        tarjeta(im, (MX, cy, MX + ANCHO, cy + alto), MAPA, rot=(0.3 if i % 2 else -0.3))
        cuando = str(_g(x, "cuando", "")).upper()
        fc = f(25, True)
        cw = min(214, ancho_txt(cuando, fc) + 34)
        fc, lc, _ = encajar(cuando, cw - 24, 40, 25, pxmin=15, bold=True, max_lineas=1)
        d.rectangle([MX, cy, MX + cw, cy + alto], fill=_mezcla(MAPA, col, max(0.35, u)))
        d.text((MX + 16, cy + alto // 2 - fc.size), lc[0], font=fc, fill=PAPEL)

        tx = MX + cw + 26
        tw = MX + ANCHO - tx - 24
        donde = str(_g(x, "donde", ""))
        hd = 34 if donde else 0
        fq, lq, lhq = encajar(_g(x, "que", ""), tw, alto - 34 - hd, 31, pxmin=18, bold=True)
        yy = bloque(d, (tx, cy + 18), lq, fq, TINTA, lhq)
        if donde:
            fd, ld, _ = encajar(donde, tw, 30, 23, pxmin=15, max_lineas=1)
            d.text((tx, min(yy + 4, cy + alto - 34)), ld[0], font=fd, fill=GRIS)

    if n < len(fechas):
        d.text((MX, int(y + 22 + n * (alto + hueco))), "+ %d more on the calendar" % (len(fechas) - n),
               font=f(26, True), fill=GRIS)


# ================================================================ FICHA 8 - plano
def ficha_plano(im, d, datos, t, rojo):
    """{"imagen": ruta, "pie"} -- la unica ficha con imagen generada (fal.ai), 1-2 por episodio."""
    _rotulo(d, "the scene")
    ruta = str(_g(datos, "imagen", ""))
    pie = _g(datos, "pie", "")
    fp, lp, lhp = encajar(pie, ANCHO - 48, 120, 30, pxmin=18) if pie else (f(30), [], 36)
    hp = (len(lp) * lhp + 30) if pie else 0

    caja = (MX, Y_TOP + 6, MX + ANCHO, Y_BOT - hp - 18)
    x0, y0, x1, y1 = [int(round(v)) for v in caja]
    tarjeta(im, caja, MAPA, rot=-0.5)

    src = None
    if ruta:
        try:
            src = Image.open(ruta).convert("RGB")
        except Exception:
            src = None

    if src is not None:
        cw, ch = x1 - x0 - 28, y1 - y0 - 28
        s = min(cw / src.width, ch / src.height)
        nw, nh = max(1, int(src.width * s)), max(1, int(src.height * s))
        src = src.resize((nw, nh), Image.LANCZOS)
        u = _eo(t / 0.55)
        if u < 0.999:                                  # entra revelandose sobre el papel
            src = Image.blend(Image.new("RGB", src.size, MAPA), src, max(0.12, u))
        im.paste(src, (x0 + 14 + (cw - nw) // 2, y0 + 14 + (ch - nh) // 2))
        d.rectangle([x0 + 14 + (cw - nw) // 2 - 1, y0 + 14 + (ch - nh) // 2 - 1,
                     x0 + 14 + (cw - nw) // 2 + nw, y0 + 14 + (ch - nh) // 2 + nh],
                    outline=TINTA, width=3)
        if pie:
            c = rojo("vineta del pie")
            d.rectangle([MX, Y_BOT - hp + 4, MX + 16, Y_BOT - hp + 20], fill=c)
            bloque(d, (MX + 32, Y_BOT - hp), lp, fp, TINTA, lhp)
    else:
        # sin imagen la ficha no se calla: lo dice en rojo, que aca es lo que esta en falta.
        c = rojo("falta la imagen")
        for k in range(-(y1 - y0), x1 - x0, 46):
            d.line([(x0 + k, y0), (x0 + k + (y1 - y0), y1)], fill=TENUE, width=3)
        fa, la, lha = encajar("IMAGE NOT RENDERED", ANCHO - 120, 60, 44, pxmin=24, bold=True)
        d.text((x0 + 46, y0 + 46), la[0], font=fa, fill=c)
        fr, lr, lhr = encajar(ruta or "(sin ruta)", ANCHO - 120, 120, 24, pxmin=15)
        bloque(d, (x0 + 46, y0 + 46 + lha + 12), lr, fr, GRIS, lhr)
        if pie:
            bloque(d, (MX, Y_BOT - hp), lp, fp, TINTA, lhp)


# ================================================================ despachador
_RENDER = {
    "mapa": ficha_mapa, "versus": ficha_versus, "titular": ficha_titular, "dato": ficha_dato,
    "serie": ficha_serie, "cronologia": ficha_cronologia, "calendario": ficha_calendario,
    "plano": ficha_plano,
}


ASENTADA = 1.30      # a partir de aca la ficha ya no cambia: ningun revel sigue corriendo
_CACHE = {}          # (tipo, datos, size) -> la ficha asentada. Ver la nota de rendimiento abajo.
_CACHE_MAX = 4


def render_ficha(tipo, datos, size=(W_FICHA, H_FICHA), t=0.0):
    """Dibuja una ficha del panel derecho.

    tipo  : uno de TIPOS
    datos : el dict que emite el guion (CONTRATO.md, seccion videos/DAILY/fichas.py)
    size  : la ficha se compone SIEMPRE a 960x1080 y se reescala al final, asi la maqueta no
            depende del tamano pedido
    t     : segundos desde que la ficha entro. La estructura se dibuja completa en t=0.

    RENDIMIENTO: una ficha cuesta 35-220 ms, o sea que a 24 fps no se puede redibujar siempre.
    Pero pasado `ASENTADA` la ficha es IDENTICA cuadro a cuadro, asi que a partir de ahi se
    devuelve una copia cacheada: una ficha de 18 s pasa de 430 renders a 32. El que llama no
    tiene que saber nada de esto. El cache guarda 4 fichas (~12 MB): el VPS no tiene swap.
    """
    if tipo not in _RENDER:
        raise ValueError("ficha desconocida: %r (las del catalogo son %s)" % (tipo, ", ".join(TIPOS)))
    datos = datos if isinstance(datos, dict) else {}
    t = max(0.0, float(t))

    clave = None
    if t >= ASENTADA:
        t = ASENTADA
        try:
            clave = (tipo, repr(sorted(datos.items())), tuple(size))
        except TypeError:                       # datos no ordenables: se renderiza sin cachear
            clave = None
        if clave in _CACHE:
            return _CACHE[clave].copy()

    cont = Image.new("RGB", (W_FICHA, H_FICHA), PAPEL)
    d = ImageDraw.Draw(cont)
    d.line([(0, CABECERA), (W_FICHA, CABECERA)], fill=TENUE, width=3)   # bajo la cabecera comun
    _RENDER[tipo](cont, d, datos, t, _Rojo())

    if t < ENTRADA:                       # la hoja se asienta: sube 14 px y termina de opacarse
        u = _eo(t / ENTRADA)
        marco = Image.new("RGB", (W_FICHA, H_FICHA), PAPEL)
        marco.paste(cont, (0, int(round(14 * (1 - u)))))
        cont = Image.blend(Image.new("RGB", (W_FICHA, H_FICHA), PAPEL), marco, 0.55 + 0.45 * u)

    cont = grano(cont)
    if tuple(size) != (W_FICHA, H_FICHA):
        cont = cont.resize((int(size[0]), int(size[1])), Image.LANCZOS)
    if clave is not None:
        if len(_CACHE) >= _CACHE_MAX:
            _CACHE.pop(next(iter(_CACHE)))
        _CACHE[clave] = cont.copy()
    return cont


# ================================================================ autotest
DEMO = {
    "mapa": {
        "hoja": "europa_este", "titulo": "WHERE THE NIGHT WENT",
        "puntos": [
            {"nombre": "Kyiv", "lat": 50.45, "lon": 30.52},
            {"nombre": "Belgorod", "lat": 50.60, "lon": 36.59, "rojo": True},
            {"nombre": "Moscow", "lat": 55.75, "lon": 37.62},
            {"nombre": "Minsk", "lat": 53.90, "lon": 27.56},
            {"nombre": "Warsaw", "lat": 52.23, "lon": 21.01},
        ],
        "flechas": [{"de": "Kyiv", "a": "Belgorod"}],
        "pie": "positions as reported by both general staffs · 06:12 UTC",
    },
    "versus": {
        "titulo": "DRONE STRIKE ON THE BELGOROD REFINERY",
        "izq": {"actor": "Russia", "fuentes": "MoD statement · TASS · RT",
                "dice": "Air defences destroyed 20 Ukrainian drones over the region overnight. "
                        "There is no damage on the ground and the refinery is operating normally."},
        "der": {"actor": "Ukraine", "fuentes": "General Staff · Ukrinform",
                "dice": "The strike reached its target. The Belgorod refinery is out of service and "
                        "the fire burned for four hours."},
        "pie": "independent evidence insufficient",
    },
    "titular": {
        "medio": "Financial Times", "fecha": "11 September 2026",
        "titular": "EU agrees 19th sanctions package, targeting Russian LNG for the first time",
        "bajada": "The package clears after Hungary drops its veto in exchange for a transit "
                  "carve-out that runs until the end of 2027.",
    },
    "dato": {
        "numero": "2.4", "unidad": "million b/d",
        "etiqueta": "Russian crude leaving by sea, four-week average",
        "contexto": "Down from 3.1 million in January and the lowest since the invasion began. "
                    "Two thirds of it is now lifted by tankers with no western insurance.",
    },
    "serie": {
        "titulo": "BRENT CRUDE, FRONT MONTH",
        "unidad": "USD / bbl",
        "puntos": [["Mar", 71.4], ["Apr", 68.9], ["May", 73.2], ["Jun", 79.6], ["Jul", 77.1],
                   ["Aug", 82.3], ["Sep", 88.7]],
        "nota": "Settlement prices, ICE Futures Europe. September is the month to date.",
    },
    "cronologia": {
        "titulo": "BELGOROD, HOUR BY HOUR",
        "hitos": [
            {"hora": "01:40", "texto": "Regional governor reports explosions and says air defences are working."},
            {"hora": "02:15", "texto": "Flight restrictions imposed over three airports in southern Russia."},
            {"hora": "04:30", "texto": "Russian Ministry of Defence claims 20 drones downed, no damage."},
            {"hora": "05:50", "texto": "Ukrainian General Staff claims the refinery was hit and is out of service."},
            {"hora": "06:12", "texto": "NASA FIRMS registers a thermal anomaly over the refinery site."},
        ],
    },
    "calendario": {
        "titulo": "WHAT TO WATCH",
        "fechas": [
            {"cuando": "Sep 16", "que": "Federal Reserve decision", "donde": "Washington · 18:00 UTC"},
            {"cuando": "Sep 22", "que": "UN General Assembly general debate opens", "donde": "New York"},
            {"cuando": "Oct 08", "que": "IMF and World Bank annual meetings", "donde": "Washington"},
            {"cuando": "Oct 26", "que": "Argentina legislative elections", "donde": "Buenos Aires"},
        ],
    },
    "plano": {"imagen": "", "pie": "The Kremlin press pool, minutes before the statement."},
}


def _imagen_demo(destino):
    """Un plano hero de mentira, dibujado en PIL con la misma tecnica de recorte: el autotest no
       gasta un credito de fal.ai. Es la mesa de mapas de ESTILO.md 2, vista de frente."""
    w, h = 1024, 768
    im = Image.new("RGB", (w, h), (214, 202, 176))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, int(h * 0.30)], fill=(202, 190, 166))            # pared, un tono mas
    d.rectangle([0, int(h * 0.64), w, h], fill=MADERA)                     # la mesa
    d.rectangle([0, int(h * 0.64), w, int(h * 0.665)], fill=(132, 95, 66))  # canto iluminado

    for x, sc in ((0.13, 1.0), (0.70, 0.94)):                              # dos burocratas de papel
        bx, by = int(w * x), int(h * (0.30 + (1 - sc) * 0.06))
        aw, ah = int(w * 0.17 * sc), int(h * 0.34 * sc)
        d.polygon([(bx, by + ah), (bx + int(aw * 0.14), by + int(ah * 0.22)),
                   (bx + aw - int(aw * 0.14), by + int(ah * 0.22)), (bx + aw, by + ah)], fill=AZUL)
        d.polygon([(bx - int(aw * 0.16), by + ah), (bx + int(aw * 0.12), by + int(ah * 0.26)),
                   (bx + int(aw * 0.30), by + int(ah * 0.34)), (bx + int(aw * 0.06), by + ah)],
                  fill=(33, 60, 90))                                       # el brazo, capa aparte
        d.ellipse([bx + int(aw * 0.22), by - int(ah * 0.30), bx + int(aw * 0.78), by + int(ah * 0.26)],
                  fill=(198, 168, 136), outline=TINTA, width=4)            # cabeza
        d.rectangle([bx + int(aw * 0.14), by - int(ah * 0.34), bx + int(aw * 0.86), by - int(ah * 0.16)],
                    fill=TINTA)                                            # sombrero

    mx0, my0, mx1, my1 = int(w * 0.22), int(h * 0.46), int(w * 0.84), int(h * 0.82)
    d.polygon([(mx0, my0 + 14), (mx1 - 10, my0), (mx1, my1 - 12), (mx0 + 12, my1)],
              fill=PAPEL, outline=TINTA, width=5)                          # la carta sobre la mesa
    for i in range(7):                                                     # costas esquematicas
        yy = my0 + 26 + i * 22
        d.line([(mx0 + 26, yy + (i % 3) * 4), (mx1 - 40 - (i % 4) * 60, yy)], fill=TENUE, width=4)
    d.line([(int(w * 0.34), my1 - 40), (int(w * 0.62), my0 + 54)], fill=AZUL, width=6)
    d.ellipse([int(w * 0.595), my0 + 34, int(w * 0.645), my0 + 74], fill=ROJO, outline=TINTA, width=4)
    im = grano(im)
    im.save(destino)
    return destino


def _analizar(im):
    """Devuelve (rango de luminancia, fraccion de tinta, fraccion de rojo) del area de contenido."""
    import numpy as np
    a = np.asarray(im.convert("RGB")).astype("int16")
    cuerpo = a[CABECERA + 20:H_FICHA - 10, 10:W_FICHA - 10]
    lum = cuerpo.mean(axis=2)
    r, g, b = cuerpo[:, :, 0], cuerpo[:, :, 1], cuerpo[:, :, 2]
    rojo = ((r > 120) & (r < 225) & (r - g > 55) & (r - b > 55)).mean()
    tinta = (lum < 120).mean()
    return float(lum.max() - lum.min()), float(tinta), float(rojo)


def autotest():
    ok = True

    def chequeo(cond, texto):
        nonlocal ok
        print(("OK   " if cond else "FALLA") + "  " + texto)
        if not cond:
            ok = False
        return cond

    tmp = tempfile.mkdtemp(prefix="fichas_")
    demo = dict(DEMO)
    demo["plano"] = dict(DEMO["plano"], imagen=_imagen_demo(os.path.join(tmp, "plano.png")))

    chequeo(sorted(TIPOS) == sorted(_RENDER), "el catalogo tiene los 8 tipos del contrato")

    hojas = []
    for tipo in TIPOS:
        try:
            im = render_ficha(tipo, demo[tipo], t=1.20)
        except Exception as e:
            chequeo(False, "%-11s render: %s: %s" % (tipo, type(e).__name__, e))
            hojas.append((tipo, Image.new("RGB", (W_FICHA, H_FICHA), (255, 0, 255))))
            continue
        hojas.append((tipo, im))
        rango, tint, rj = _analizar(im)
        chequeo(im.size == (W_FICHA, H_FICHA) and im.mode == "RGB",
                "%-11s devuelve 960x1080 RGB" % tipo)
        chequeo(rango > 90, "%-11s no esta vacia ni es de un solo color (rango %.0f)" % (tipo, rango))
        chequeo(0.008 < tint < 0.62, "%-11s tiene tinta dibujada (%.1f%% del panel)" % (tipo, tint * 100))
        chequeo(rj < 0.070, "%-11s el rojo es UN elemento, no un bano (%.2f%%)" % (tipo, rj * 100))

    # el rojo tiene que estar presente donde la ficha lo promete
    for tipo in ("mapa", "versus", "titular", "dato", "serie", "cronologia", "calendario", "plano"):
        im = dict(hojas)[tipo]
        _, _, rj = _analizar(im)
        chequeo(rj > 0.00015, "%-11s marca su elemento en rojo (%.3f%%)" % (tipo, rj * 100))

    # la regla del rojo la hace cumplir el codigo, no la buena voluntad
    r = _Rojo()
    r("uno")
    r("uno")
    try:
        r("dos")
        chequeo(False, "_Rojo rechaza un segundo elemento rojo")
    except ValueError:
        chequeo(True, "_Rojo rechaza un segundo elemento rojo")

    # ninguna t deja la ficha en blanco, y el tipo desconocido no pasa
    for tipo in TIPOS:
        malo = [tt for tt in (0.0, 0.12, 0.40, 6.0)
                if _analizar(render_ficha(tipo, demo[tipo], t=tt))[0] <= 60]
        chequeo(not malo, "%-11s legible en t=0.0/0.12/0.40/6.0" % tipo)
    try:
        render_ficha("infografia", {})
        chequeo(False, "un tipo fuera del catalogo levanta ValueError")
    except ValueError:
        chequeo(True, "un tipo fuera del catalogo levanta ValueError")

    # REGLA 24: un punto fuera de la hoja que pidio el guion aborta el render, no se arrastra al borde
    try:
        render_ficha("mapa", {"hoja": "medio_oriente",          # Reykjavik no esta en esa hoja
                              "puntos": [{"nombre": "Reykjavik", "lat": 64.15, "lon": -21.94}]})
        chequeo(False, "regla 24: un punto fuera de su hoja aborta el render")
    except ValueError as e:
        chequeo("regla 24" in str(e), "regla 24: un punto fuera de su hoja aborta el render")
    # Nuku'alofa esta en lon -175.2, o sea 184.8 E: la hoja cruza el antimeridiano y hay que sumarle 360
    anti = render_ficha("mapa", {"hoja": "pacifico", "puntos": [
        {"nombre": "Nuku'alofa", "lat": -21.14, "lon": -175.2, "rojo": True},
        {"nombre": "Canberra", "lat": -35.31, "lon": 149.13},
        {"nombre": "Honolulu", "lat": 21.31, "lon": -157.86}]}, t=1.5)
    chequeo(anti.size == (W_FICHA, H_FICHA) and _analizar(anti)[0] > 90,
            "una hoja que cruza el antimeridiano proyecta bien")

    # datos rotos, faltantes o gigantes: la ficha sale igual, es lo que salva la corrida de las 05:00
    duro = {
        "mapa": {"hoja": "no_existe", "puntos": [{"nombre": "X" * 60, "lat": 9, "lon": 9, "rojo": True}]},
        "versus": {"titulo": "T " * 40, "izq": {"actor": "A" * 40, "dice": "z" * 900},
                   "der": {}, "pie": "P" * 90},
        "titular": {"medio": "M" * 40, "titular": "supercalifragilisticoexpialidosoinquebrantable" * 3},
        "dato": {"numero": "1234567890", "unidad": "unidades", "etiqueta": "E " * 40, "contexto": "c " * 300},
        "serie": {"titulo": "T", "puntos": []},
        "cronologia": {"titulo": "T", "hitos": [{"hora": "%02d:00" % i, "texto": "t " * 40} for i in range(22)]},
        "calendario": {"titulo": "T", "fechas": [{"cuando": "C" * 30, "que": "q " * 40} for _ in range(18)]},
        "plano": {"imagen": "/no/existe/plano.png", "pie": "p " * 80},
    }
    for tipo in TIPOS:
        try:
            im = render_ficha(tipo, duro[tipo], t=1.0)
            chequeo(im.size == (W_FICHA, H_FICHA) and _analizar(im)[0] > 90,
                    "%-11s aguanta datos rotos o desbordados" % tipo)
        except Exception as e:
            chequeo(False, "%-11s aguanta datos rotos: %s: %s" % (tipo, type(e).__name__, e))
    # valores que no son numeros: la serie tira ese punto y sale con el resto, no tumba la corrida
    try:
        rota = render_ficha("serie", {"titulo": "T", "unidad": "USD",
                                      "puntos": [["Mar", 1.0], ["Apr", "n/d"], ["May", None],
                                                 ["Jun", float("inf")], ["Jul", 3.5]]}, t=1.2)
        chequeo(rota.size == (W_FICHA, H_FICHA) and _analizar(rota)[0] > 90,
                "serie       con 'n/d' / None / inf dibuja los puntos que si son datos")
    except Exception as e:
        chequeo(False, "serie       con 'n/d' / None / inf: %s: %s" % (type(e).__name__, e))

    chequeo(render_ficha("dato", {}).size == (W_FICHA, H_FICHA), "datos vacios no rompen el render")
    chequeo(render_ficha("mapa", demo["mapa"], size=(480, 540)).size == (480, 540),
            "respeta un size distinto del nominal")

    # determinismo: dos renders del mismo cuadro tienen que ser identicos (si no, titila)
    a = render_ficha("titular", demo["titular"], t=1.0).tobytes()
    b = render_ficha("titular", demo["titular"], t=1.0).tobytes()
    chequeo(a == b, "el render es determinista (grano y bordes rasgados con semilla fija)")

    # ...Y ENTRE PROCESOS. El render del diario es resumible: la segunda mitad del video la dibuja
    # otro proceso. Con `hash()` (salado por PYTHONHASHSEED) el mismo cuadro salia distinto en cada
    # corrida y el borde rasgado pegaba un salto justo donde se retomo; en un solo proceso no se ve.
    import subprocess
    guion = ("import sys, hashlib; sys.path.insert(0, %r); import fichas as F; "
             "print(hashlib.sha1(F.render_ficha('titular', F.DEMO['titular'], t=1.0)"
             ".tobytes()).hexdigest())" % BASE)
    firmas = set()
    for semilla_py in ("0", "1", "2"):
        ent = dict(os.environ, PYTHONHASHSEED=semilla_py)
        firmas.add(subprocess.run([sys.executable, "-c", guion], capture_output=True, text=True,
                                  env=ent).stdout.strip())
    chequeo(len(firmas) == 1 and "" not in firmas,
            "el render es determinista ENTRE PROCESOS, que es lo que pide el render resumible")

    # nada puede seguir animandose cuando el cache congela la ficha en ASENTADA
    quieto = {
        "mapa": {"hoja": "europa", "flechas": [{"de": "P%d" % i, "a": "P%d" % (i + 1)} for i in range(8)],
                 "puntos": [dict(nombre="P%d" % i, lat=40 + i * 0.7, lon=10 + i * 1.3,
                                 rojo=(i == 0)) for i in range(16)]},
        "cronologia": {"titulo": "T", "hitos": [{"hora": "%02d:00" % i, "texto": "t"} for i in range(8)]},
        "calendario": {"titulo": "T", "fechas": [{"cuando": "C%d" % i, "que": "q"} for i in range(6)]},
    }
    for tipo, dd in quieto.items():
        antes = render_ficha(tipo, dd, t=ASENTADA - 0.02).tobytes()
        chequeo(antes == render_ficha(tipo, dd, t=ASENTADA).tobytes(),
                "%-11s ya no se mueve en ASENTADA (si no, el cache la congela a medio revel)" % tipo)
    _CACHE.clear()

    # la regla del rojo tambien se rompe por defecto: una ficha SIN su elemento rojo
    largas = {
        "cronologia": {"titulo": "T", "hitos": [{"hora": "%02d:00" % i, "texto": "t " * 30}
                                                for i in range(22)]},
        "calendario": {"titulo": "T", "fechas": [{"cuando": "C%d" % i, "que": "q " * 20}
                                                 for i in range(18)]},
    }
    largas["calendario"]["fechas"][15]["rojo"] = True   # marcada fuera de lo que entra
    for tipo, dd in largas.items():
        chequeo(_analizar(render_ficha(tipo, dd, t=1.2))[2] > 0.00015,
                "%-11s recortada por altura sigue marcando su elemento en rojo" % tipo)

    # la cifra de la ficha `dato` va entera: nunca un pedazo con guion
    for numero, unidad in (("1.234.567.890.123", "million barrels per day (seaborne)"),
                           ("2.4", "million b/d"), ("-17.500", "")):
        _fn, cifra, _fu, _un, _wu = _cifra_y_unidad(numero, unidad, ANCHO - 92)
        chequeo(cifra == numero, "la cifra %r sale entera aun con unidad larga (salio %r)"
                % (numero, cifra))

    # la etiqueta del ultimo valor de la serie dice el DATO, no el redondeo del eje
    chequeo(_fmt_valor(88.7) == "88.7" and _fmt_valor(2.4) == "2.4" and _fmt_valor(149.0) == "149",
            "la serie etiqueta el ultimo valor con el dato, no con el paso del eje")
    chequeo(_fmt(88.7, 5) != _fmt_valor(88.7), "el tick del eje y el dato se formatean distinto")

    # un rotulo de una sola linea avisa cuando recorta, en vez de comerse el resto en silencio
    _fx, lx, _lhx = encajar("THE INSTITUTE FOR THE STUDY OF WAR AND FOREIGN POLICY", 300, 200, 40,
                            pxmin=20, bold=True, max_lineas=1)
    chequeo(len(lx) == 1 and lx[0].endswith("..."),
            "un rotulo de una linea que no entra cierra con puntos suspensivos (%r)" % lx[0])

    # el cache de la ficha asentada no puede cambiar el resultado ni entregar la misma imagen
    _CACHE.clear()
    sin = render_ficha("versus", demo["versus"], t=4.0)      # entra al cache
    con = render_ficha("versus", demo["versus"], t=9.0)      # sale del cache
    chequeo(sin.tobytes() == con.tobytes(), "el cache devuelve la misma ficha asentada")
    chequeo(sin is not con, "el cache entrega una copia, no la imagen que guarda")
    ImageDraw.Draw(con).rectangle([0, 0, 900, 1000], fill=(255, 0, 255))   # el que llama la pinta
    chequeo(render_ficha("versus", demo["versus"], t=9.0).tobytes() == sin.tobytes(),
            "pintar sobre una ficha devuelta no ensucia el cache")
    chequeo(len(_CACHE) <= _CACHE_MAX, "el cache no crece sin limite (%d de %d)" % (len(_CACHE), _CACHE_MAX))
    for tipo in TIPOS:                                       # llena y desaloja
        render_ficha(tipo, demo[tipo], t=3.0)
    chequeo(len(_CACHE) <= _CACHE_MAX, "el cache desaloja al llenarse (%d de %d)" % (len(_CACHE), _CACHE_MAX))
    _CACHE.clear()

    # hoja de contacto
    cols, esc, gap, rot = 4, 0.50, 20, 38
    cw, ch = int(W_FICHA * esc), int(H_FICHA * esc)
    filas = (len(hojas) + cols - 1) // cols
    hoja = Image.new("RGB", (cols * cw + (cols + 1) * gap, filas * (ch + rot) + (filas + 1) * gap),
                     (246, 241, 230))
    dh = ImageDraw.Draw(hoja)
    for i, (tipo, im) in enumerate(hojas):
        cx = gap + (i % cols) * (cw + gap)
        cy = gap + (i // cols) * (ch + rot + gap)
        dh.text((cx + 2, cy + 4), tipo.upper(), font=f(26, True), fill=TINTA)
        dh.text((cx + 2 + ancho_txt(tipo.upper(), f(26, True)) + 14, cy + 9),
                "960 x 1080", font=f(19), fill=GRIS)
        hoja.paste(im.resize((cw, ch), Image.LANCZOS), (cx, cy + rot))
        dh.rectangle([cx, cy + rot, cx + cw, cy + rot + ch], outline=TENUE, width=2)
    salida = os.path.join(BASE, "_fichas_prueba.jpg")
    hoja.save(salida, quality=92)
    chequeo(os.path.exists(salida) and os.path.getsize(salida) > 40000,
            "hoja de contacto en %s (%d x %d)" % (salida, hoja.width, hoja.height))

    shutil.rmtree(tmp, ignore_errors=True)     # el plano de mentira no queda tirado en %TEMP%
    print("RESULTADO:", "TODO OK" if ok else "HAY FALLAS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(autotest() if "--autotest" in sys.argv else autotest())
