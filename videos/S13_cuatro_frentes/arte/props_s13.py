# -*- coding: utf-8 -*-
"""Props de papel de la serie S13 («FOUR LINES», 2026-09-16). 0 creditos: todo por codigo.

    cd videos/S13_cuatro_frentes/arte && python props_s13.py [--hoja]

Regla 19 (reusar antes de generar). **Se reusan tal cual**, mirados en la hoja del 16-sep
(`_qc/hoja_props_candidatos.jpg`): `dron_grande`, `deposito_fuel` (dice FUEL), `capitolio`, `buque_us`,
`martillo_juez`, `bandera_rusa`, `bandera_us`, `bandera_cn`, `bandera_uk`.

**Se descartaron por lo que DICEN** (la trampa de `urna`/`ticket`):
`torre_petroleo` (es una torre de extraccion, no una refineria) · `calendario` (dice «11», del 11-S) ·
`doc_contrato` (dice ASYLUM ACCOMMODATION CONTRACTS) · `carpetas` (dice 3 OF 12 PASSED) ·
`urna` (dice YES) · `sello_no_precedent` (dice lo contrario de la pieza 2).

Se dibuja aca, cada uno a su tamaño de pantalla (leccion del ep. 09: un prop se dibuja al tamaño al
que se ve; una SECUENCIA ocupa el 30 % del alto, un DOC el 50 %):

  pieza 1  `refineria`, `refineria_off`, `refinerias_d00..12`, `doc_iea`, `bandera_ua`
  pieza 2  `lancha`, `votos_d00..12`, `doc_memo`, `estante`, `bandera_ve`
  pieza 3  `calendario_24`, `balanza_d00..12`, `guardacostas`, `bandera_tw`
  pieza 4  `gilt_30`, `pilas_d00..12`

**Todo prop con letras declara su texto** en `assets/prop_<nombre>.txt` (regla h de `compo.check`). Los
que no tienen letras tambien (texto vacio): `compo` marca como fallo un prop sin declarar.
"""
import math, os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', '..', '..', 'produccion'))
from PIL import Image, ImageDraw
from props import papel, texto, FONT, FONTC, TINTA, PAPEL, OCRE, AZUL, ROJO

BLANCO = (245, 241, 230)
GRIS = (120, 115, 105)
GRIS_C = (168, 163, 152)
HUMO = (132, 128, 120)
LLAMA = (236, 128, 40)          # naranja: NO cuenta como rojo en la regla d (g > 90)
LLAMA_C = (250, 208, 92)
ACERO = (150, 156, 160)
MADERA = (120, 84, 56)
LIBRA = (122, 92, 138)          # billete de papel morado: no es un dolar
AMARILLO_UA = (255, 213, 0)
AZUL_UA = (0, 87, 183)

OUT = os.path.join(AQUI, 'assets'); os.makedirs(OUT, exist_ok=True)
PASOS = 13
TEXTOS = {}                     # nombre -> texto horneado (se escribe a prop_<n>.txt)


def guardar(nombre, im, txt=''):
    im.save(os.path.join(OUT, 'prop_%s.png' % nombre))
    TEXTOS[nombre] = txt


def _d(p): return ImageDraw.Draw(p)
def _c(col, a=255): return tuple(col) + (a,)


# ============================================================ banderas (molde de la S12)
def _bandera(w, h, pintar, etiqueta):
    H = h + 64
    def f(d): d.rounded_rectangle([1, 1, w - 2, H - 2], radius=12, fill=255)
    p = papel((w, H), f, PAPEL); d = _d(p)
    d.rectangle([12, 14, w - 13, h - 6], fill=_c(BLANCO))
    pintar(d)
    d.rectangle([12, 14, w - 13, h - 6], outline=_c(TINTA), width=4)
    texto(p, etiqueta, int(w * 0.105), (w / 2, h + 26), color=TINTA, font=FONTC)
    return p


def bandera_ua(w=360, h=228):
    def pintar(d):
        x0, y0, x1, y1 = 12, 14, w - 13, h - 6
        m = (y0 + y1) / 2
        d.rectangle([x0, y0, x1, m], fill=_c(AZUL_UA))
        d.rectangle([x0, m, x1, y1], fill=_c(AMARILLO_UA))
    return _bandera(w, h, pintar, 'UKRAINE')


def _estrella(d, cx, cy, r, col):
    pts = []
    for k in range(10):
        ang = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.42
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon(pts, fill=_c(col))


def bandera_ve(w=360, h=228):
    """Amarillo, azul y rojo con el arco de ocho estrellas. Sin el escudo (a este tamaño es una mancha:
    la misma decision que la bandera de Iran en la S12)."""
    def pintar(d):
        x0, y0, x1, y1 = 12, 14, w - 13, h - 6
        t = (y1 - y0) / 3
        d.rectangle([x0, y0, x1, y0 + t], fill=_c((252, 209, 22)))
        d.rectangle([x0, y0 + t, x1, y0 + 2 * t], fill=_c((0, 36, 125)))
        d.rectangle([x0, y0 + 2 * t, x1, y1], fill=_c((207, 20, 43)))
        cx, cy = (x0 + x1) / 2, y0 + 2 * t + t * 0.05
        R = t * 1.05
        for k in range(8):
            ang = math.radians(200 + k * (140 / 7))
            _estrella(d, cx + R * math.cos(ang), cy + R * math.sin(ang), t * 0.13, BLANCO)
    return _bandera(w, h, pintar, 'VENEZUELA')


def bandera_tw(w=360, h=228):
    def pintar(d):
        x0, y0, x1, y1 = 12, 14, w - 13, h - 6
        d.rectangle([x0, y0, x1, y1], fill=_c((254, 0, 0)))
        cw, ch = (x1 - x0) / 2, (y1 - y0) / 2
        d.rectangle([x0, y0, x0 + cw, y0 + ch], fill=_c((0, 0, 149)))
        cx, cy = x0 + cw / 2, y0 + ch / 2
        r = ch * 0.30
        for k in range(12):
            a = math.radians(k * 30)
            pts = [(cx + r * 1.55 * math.cos(a), cy + r * 1.55 * math.sin(a)),
                   (cx + r * 0.80 * math.cos(a + 0.26), cy + r * 0.80 * math.sin(a + 0.26)),
                   (cx + r * 0.80 * math.cos(a - 0.26), cy + r * 0.80 * math.sin(a - 0.26))]
            d.polygon(pts, fill=_c(BLANCO))
        d.ellipse([cx - r * 0.86, cy - r * 0.86, cx + r * 0.86, cy + r * 0.86], fill=_c((0, 0, 149)))
        d.ellipse([cx - r * 0.72, cy - r * 0.72, cx + r * 0.72, cy + r * 0.72], fill=_c(BLANCO))
    return _bandera(w, h, pintar, 'TAIWAN')



def bandera_china(w=360, h=228):
    """Rojo con la estrella grande y cuatro chicas en arco. Molde de ficha, como las demas (la `bandera_cn`
    del indice es de mastil y mide 166 px: a media pantalla se emborrona)."""
    def pintar(d):
        x0, y0, x1, y1 = 12, 14, w - 13, h - 6
        d.rectangle([x0, y0, x1, y1], fill=_c((222, 41, 16)))
        u = (y1 - y0) / 20
        _estrella(d, x0 + 5 * u, y0 + 5 * u, 3.2 * u, (255, 222, 0))
        for cx, cy in ((10, 2), (12, 4), (12, 7), (10, 9)):
            _estrella(d, x0 + cx * u, y0 + cy * u, 1.1 * u, (255, 222, 0))
    return _bandera(w, h, pintar, 'CHINA')


def bandera_rusia(w=360, h=228):
    def pintar(d):
        x0, y0, x1, y1 = 12, 14, w - 13, h - 6
        tt = (y1 - y0) / 3
        d.rectangle([x0, y0, x1, y0 + tt], fill=_c(BLANCO))
        d.rectangle([x0, y0 + tt, x1, y0 + 2 * tt], fill=_c((0, 57, 166)))
        d.rectangle([x0, y0 + 2 * tt, x1, y1], fill=_c((213, 43, 30)))
    return _bandera(w, h, pintar, 'RUSSIA')


def bandera_eeuu(w=360, h=228):
    """Trece franjas y el canton con estrellas en rejilla (simplificado: a 260 px cincuenta estrellas son
    ruido; la rejilla se lee como la bandera)."""
    def pintar(d):
        x0, y0, x1, y1 = 12, 14, w - 13, h - 6
        fh = (y1 - y0) / 13
        for k in range(13):
            d.rectangle([x0, y0 + k * fh, x1, y0 + (k + 1) * fh], fill=_c((178, 34, 52) if k % 2 == 0 else BLANCO))
        cw, ch = (x1 - x0) * 0.40, fh * 7
        d.rectangle([x0, y0, x0 + cw, y0 + ch], fill=_c((60, 59, 110)))
        for fila in range(5):
            for col in range(6):
                cx = x0 + cw * (col + 0.5) / 6
                cy = y0 + ch * (fila + 0.5) / 5
                _estrella(d, cx, cy, ch * 0.07, BLANCO)
    return _bandera(w, h, pintar, 'UNITED STATES')

# ============================================================ pieza 1 · refinerias
def _refineria_dibujo(p, w, h, estado, ox=0, oy=0):
    """Dibuja una refineria dentro de `p` en (ox, oy), tamaño w x h.
    estado: 1.0 = encendida · 0.25 = a un cuarto (llama chica) · 0.0 = parada (humo gris)."""
    d = _d(p)
    X = lambda f: ox + w * f
    Y = lambda f: oy + h * f
    suelo = Y(0.94)
    # dos columnas de destilacion
    for cx, top, ancho in ((0.22, 0.20, 0.13), (0.40, 0.34, 0.11)):
        d.rounded_rectangle([X(cx - ancho / 2), Y(top), X(cx + ancho / 2), suelo], radius=int(w * 0.03),
                            fill=_c(ACERO if estado > 0 else GRIS_C), outline=_c(TINTA), width=max(3, int(w * 0.008)))
        for k in range(1, 6):
            yy = Y(top) + (suelo - Y(top)) * k / 6
            d.line([(X(cx - ancho / 2), yy), (X(cx + ancho / 2), yy)], fill=_c(TINTA, 150), width=max(2, int(w * 0.005)))
    # tanques
    for cx, ancho, alto in ((0.63, 0.20, 0.26), (0.84, 0.17, 0.20)):
        d.rounded_rectangle([X(cx - ancho / 2), suelo - h * alto, X(cx + ancho / 2), suelo],
                            radius=int(w * 0.02), fill=_c(BLANCO if estado > 0 else GRIS_C),
                            outline=_c(TINTA), width=max(3, int(w * 0.008)))
        d.ellipse([X(cx - ancho / 2), suelo - h * alto - h * 0.035, X(cx + ancho / 2), suelo - h * alto + h * 0.035],
                  fill=_c(BLANCO if estado > 0 else GRIS_C), outline=_c(TINTA), width=max(3, int(w * 0.008)))
    # tuberia
    d.line([(X(0.29), Y(0.62)), (X(0.53), Y(0.62)), (X(0.53), Y(0.74))], fill=_c(TINTA), width=max(4, int(w * 0.012)))
    # antorcha
    fx = 0.93
    d.rectangle([X(fx - 0.012), Y(0.10), X(fx + 0.012), suelo], fill=_c(TINTA))
    if estado >= 0.99:
        d.ellipse([X(fx - 0.055), Y(-0.04), X(fx + 0.055), Y(0.13)], fill=_c(LLAMA))
        d.ellipse([X(fx - 0.028), Y(0.02), X(fx + 0.028), Y(0.12)], fill=_c(LLAMA_C))
    elif estado > 0:
        d.ellipse([X(fx - 0.026), Y(0.045), X(fx + 0.026), Y(0.115)], fill=_c(LLAMA))
    else:
        for k, (dx, dy, rr) in enumerate(((0.0, 0.02, 0.05), (-0.05, -0.05, 0.06), (0.03, -0.12, 0.045))):
            d.ellipse([X(fx + dx - rr), Y(dy - rr), X(fx + dx + rr), Y(dy + rr)], fill=_c(HUMO, 225))
    d.line([(X(0.02), suelo), (X(0.99), suelo)], fill=_c(TINTA), width=max(4, int(w * 0.012)))


def refineria(w=760, estado=1.0):
    """v2: tarjeta entera con aire arriba. En la v1 la llama (y el humo de la apagada) caia por encima
    de la mascara y se veia cortada en la hoja del 16-sep."""
    h = int(w * 0.80)
    H = int(h * 1.22)
    def f(d): d.rounded_rectangle([1, 1, w - 2, H - 2], radius=16, fill=255)
    p = papel((w, H), f, PAPEL)
    _refineria_dibujo(p, w * 0.94, h, estado, ox=w * 0.03, oy=H - h * 1.02)
    return p


def _barra_cuarto(p, x0, y0, w, h, pct):
    d = _d(p)
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=_c(BLANCO), outline=_c(TINTA), width=3)
    d.rectangle([x0 + 3, y0 + 3, x0 + 3 + (w - 6) * pct, y0 + h - 3], fill=_c(OCRE))


NOMBRES6 = ('OMSK', 'KIRISHI', 'VOLGOGRAD', 'PERM', 'NORSI', 'TANECO')


def refinerias(j, W=1000):
    """Seis refinerias en 3x2 con su nombre (F3). v3 (16-sep): el horario sale de las palabras de la voz.
    La secuencia corre de «Kirishi» (39,24 s) a «capacity» (44,40 s): 13 cuadros de 0,40 s.
      j0      las seis encendidas
      j1-j2   la llama de KIRISHI baja
      j3+     KIRISHI parada, velada, SHUT DOWN          (j3 = 40,43 s; «completely» = 40,38 s)
      j6-j10  VOLGOGRAD y NORSI: aparece la barra y baja  (j6 = 41,62 s; «Volgograd» = 41,50 s)
      j11+    las dos veladas a un cuarto                 (j11 = 43,61 s; «quarter» = 43,96 s)
    En la linea 6 se muestra el cuadro 0 quieto (PROP): el ancla de fin de una SECUENCIA solo se busca
    hasta 4 s despues de su linea, y estirada desde la linea 6 se comprimia y adelantaba la voz 3 s."""
    H = int(W * 0.86)
    def f(d): d.rounded_rectangle([1, 1, W - 2, H - 2], radius=18, fill=255)
    p = papel((W, H), f, PAPEL)
    cw, chh = W / 3, H / 2
    kir_estado = 1.0 if j == 0 else (0.6 if j == 1 else (0.25 if j == 2 else 0.0))
    barra = {6: 1.0, 7: 0.80, 8: 0.60, 9: 0.45, 10: 0.35}.get(j, 0.25 if j >= 11 else None)
    for i, nom in enumerate(NOMBRES6):
        cx, cy = (i % 3) * cw, (i // 3) * chh
        est = 1.0
        if nom == 'KIRISHI':
            est = 1.0 if kir_estado >= 0.99 else (0.25 if kir_estado > 0 else 0.0)
        if nom in ('VOLGOGRAD', 'NORSI') and barra is not None and barra < 0.99:
            est = 0.25
        _refineria_dibujo(p, cw * 0.86, chh * 0.56, est, ox=cx + cw * 0.07, oy=cy + chh * 0.16)
        afectada = (nom == 'KIRISHI' and j >= 3) or (nom in ('VOLGOGRAD', 'NORSI') and j >= 11)
        if afectada:
            velo = Image.new('RGBA', p.size, (0, 0, 0, 0))
            ImageDraw.Draw(velo).rounded_rectangle([cx + cw * 0.05, cy + chh * 0.05, cx + cw * 0.95, cy + chh * 0.74],
                                                   radius=10, fill=(34, 32, 28, 92))
            p.alpha_composite(velo)
        texto(p, nom, int(W * 0.047), (cx + cw / 2, cy + chh * 0.81), color=TINTA, font=FONTC)
        if nom in ('VOLGOGRAD', 'NORSI') and barra is not None:
            _barra_cuarto(p, cx + cw * 0.20, cy + chh * 0.88, cw * 0.60, chh * 0.07, barra)
        if nom == 'KIRISHI' and j >= 3:
            d = _d(p)
            d.rounded_rectangle([cx + cw * 0.16, cy + chh * 0.87, cx + cw * 0.84, cy + chh * 0.97], radius=6,
                                outline=_c(TINTA), width=4, fill=_c(GRIS_C))
            texto(p, 'SHUT DOWN', int(W * 0.034), (cx + cw / 2, cy + chh * 0.92), color=TINTA, font=FONTC)
    return p


def doc_iea(w=860):
    h = int(w * 1.28)
    def f(d): d.rounded_rectangle([1, 1, w - 2, h - 2], radius=10, fill=255)
    p = papel((w, h), f, BLANCO); d = _d(p)
    d.rounded_rectangle([12, 12, w - 13, h - 13], radius=8, outline=_c(TINTA), width=5)
    d.rectangle([12, 12, w - 13, h * 0.20], fill=_c(AZUL))
    texto(p, 'INTERNATIONAL', int(w * 0.085), (w / 2, h * 0.075), color=PAPEL, font=FONTC)
    texto(p, 'ENERGY AGENCY', int(w * 0.085), (w / 2, h * 0.145), color=PAPEL, font=FONTC)
    # grafico: una linea que cae
    gx0, gy0, gx1, gy1 = w * 0.12, h * 0.28, w * 0.88, h * 0.58
    d.rectangle([gx0, gy0, gx1, gy1], outline=_c(TINTA, 120), width=3)
    pts = [(gx0 + (gx1 - gx0) * k / 7, gy0 + (gy1 - gy0) * v) for k, v in
           enumerate((0.22, 0.25, 0.20, 0.30, 0.42, 0.55, 0.70, 0.82))]
    d.line(pts, fill=_c(TINTA), width=9, joint='curve')
    for i, y in enumerate(range(int(h * 0.66), int(h * 0.92), int(h * 0.045))):
        d.line([(w * 0.12, y), (w * 0.88 - (i % 3) * w * 0.14, y)], fill=_c((150, 145, 130)), width=6)
    return p


# ============================================================ pieza 2 · las lanchas y el voto
def lancha(w=780):
    h = int(w * 0.42)
    def f(d):
        d.polygon([(0, h * 0.50), (w * 0.86, h * 0.50), (w * 0.99, h * 0.36), (w * 0.93, h * 0.82), (w * 0.08, h * 0.82)], fill=255)
        d.polygon([(w * 0.34, h * 0.50), (w * 0.44, h * 0.20), (w * 0.66, h * 0.20), (w * 0.70, h * 0.50)], fill=255)
        d.rectangle([0, h * 0.44, w * 0.10, h * 0.95], fill=255)
    p = papel((w, h), f, BLANCO); d = _d(p)
    d.polygon([(0, h * 0.50), (w * 0.86, h * 0.50), (w * 0.99, h * 0.36), (w * 0.93, h * 0.82), (w * 0.08, h * 0.82)],
              outline=_c(TINTA), width=5)
    d.line([(w * 0.06, h * 0.64), (w * 0.93, h * 0.62)], fill=_c(AZUL), width=10)
    d.polygon([(w * 0.34, h * 0.50), (w * 0.44, h * 0.20), (w * 0.66, h * 0.20), (w * 0.70, h * 0.50)],
              fill=_c(GRIS_C), outline=_c(TINTA), width=5)
    d.polygon([(w * 0.47, h * 0.26), (w * 0.63, h * 0.26), (w * 0.66, h * 0.44), (w * 0.42, h * 0.44)], fill=_c((70, 90, 110)))
    for k in range(3):                                  # tres motores fuera de borda
        x = w * (0.005 + k * 0.032)
        d.rounded_rectangle([x, h * 0.44, x + w * 0.028, h * 0.93], radius=6, fill=_c(TINTA))
    return p


def _votos(n, etiquetas, caida=None, W=820):
    """Dos columnas de fichas: `n` por columna (de 10), `etiquetas` (izq, der) o None, y `caida` = posicion
    0..1 de la ficha ocre que cae sobre la derecha (None = no hay)."""
    H = int(W * 1.10)
    def f(d): d.rounded_rectangle([1, 1, W - 2, H - 2], radius=18, fill=255)
    p = papel((W, H), f, PAPEL); d = _d(p)
    base = H * 0.80
    n_max = 10
    ficha_h = (H * 0.62) / (n_max + 1.6)
    for col, cx in enumerate((W * 0.30, W * 0.70)):
        for k in range(n):
            y1 = base - k * ficha_h
            d.ellipse([cx - W * 0.16, y1 - ficha_h * 0.9, cx + W * 0.16, y1], fill=_c((150, 146, 136)),
                      outline=_c(TINTA), width=5)
        d.line([(cx - W * 0.20, base + 4), (cx + W * 0.20, base + 4)], fill=_c(TINTA), width=6)
        if col == 1 and caida is not None:
            yb = (H * 0.08 + ficha_h) + (base - n * ficha_h - H * 0.08 - ficha_h) * caida
            d.ellipse([cx - W * 0.16, yb - ficha_h * 0.9, cx + W * 0.16, yb], fill=_c(OCRE), outline=_c(TINTA), width=5)
        if etiquetas:
            texto(p, etiquetas[col], int(W * 0.13), (cx, base + H * 0.10), color=TINTA, font=FONTC)
    return p


def votos_a(j):
    """Linea 9, de «Senate» (44,20 s) a «fifty» (48,19 s): 9 cuadros de 0,44 s. El 50-50 aparece en j8 (47,74 s)."""
    return _votos(min(10, int(round(10 * j / 7))), ('50', '50') if j >= 8 else None)


def votos_b(j):
    """Linea 10, de «Vice» (50,00 s) a «attempt» (52,23 s): 5 cuadros de 0,45 s.
    j1 la ficha arriba · j2 cayendo («broke» 50,79 s) · j3 apoyada («tie» 51,33 s) · j4 el rotulo pasa a 51."""
    caida = {0: None, 1: 0.0, 2: 0.55, 3: 1.0, 4: 1.0}[j]
    return _votos(10, ('50', '51') if j >= 4 else ('50', '50'), caida)


def doc_memo(w=860):
    h = int(w * 1.28)
    def f(d): d.rounded_rectangle([1, 1, w - 2, h - 2], radius=8, fill=255)
    p = papel((w, h), f, BLANCO); d = _d(p)
    d.rounded_rectangle([12, 12, w - 13, h - 13], radius=6, outline=_c(TINTA), width=5)
    texto(p, 'LAW ENFORCEMENT', int(w * 0.090), (w / 2, h * 0.11), color=TINTA, font=FONTC)
    texto(p, 'ACTION', int(w * 0.090), (w / 2, h * 0.19), color=TINTA, font=FONTC)
    d.line([(w * 0.12, h * 0.245), (w * 0.88, h * 0.245)], fill=_c(TINTA), width=6)
    texto(p, 'WITH MILITARY SUPPORT', int(w * 0.058), (w / 2, h * 0.30), color=AZUL, font=FONTC)
    for i, y in enumerate(range(int(h * 0.38), int(h * 0.80), int(h * 0.055))):
        d.line([(w * 0.12, y), (w * 0.88 - (i % 3) * w * 0.15, y)], fill=_c((150, 145, 130)), width=6)
    # la casilla de la autorizacion, VACIA
    d.rectangle([w * 0.12, h * 0.84, w * 0.26, h * 0.93], outline=_c(TINTA), width=5)
    d.line([(w * 0.32, h * 0.93), (w * 0.86, h * 0.93)], fill=_c(TINTA), width=4)
    return p


def estante(w=860):
    h = int(w * 0.78)
    def f(d): d.rectangle([0, 0, w, h], fill=255)
    p = papel((w, h), f, (205, 190, 160)); d = _d(p)
    for y in (h * 0.46, h * 0.94):
        d.rectangle([0, y - h * 0.045, w, y], fill=_c(MADERA), outline=_c(TINTA), width=3)
    colores = [(92, 120, 150), (170, 150, 110), (120, 140, 100), (150, 110, 95), (110, 110, 130), (180, 160, 120)]
    for fila, ybase in ((0, h * 0.415), (1, h * 0.895)):
        x = w * 0.04
        for k in range(7):
            ancho = w * (0.085 + (k * 7 % 5) * 0.008)
            alto = h * (0.34 - (k * 3 % 4) * 0.012)
            dx = w * 0.05 if (fila == 1 and k == 3) else 0
            d.rectangle([x + dx, ybase - alto, x + dx + ancho, ybase], fill=_c(colores[(k + fila) % 6]),
                        outline=_c(TINTA), width=3)
            if fila == 1 and k == 3:
                d.rectangle([x + dx + ancho * 0.12, ybase - alto * 0.80, x + dx + ancho * 0.88, ybase - alto * 0.18],
                            fill=_c(BLANCO), outline=_c(TINTA), width=2)
            x += ancho + w * 0.022
    # el rotulo de la carpeta que sobresale, grande y fuera del lomo para que se lea
    d.rounded_rectangle([w * 0.52, h * 0.52, w * 0.97, h * 0.70], radius=8, fill=_c(PAPEL), outline=_c(TINTA), width=4)
    texto(p, 'NEVER', int(w * 0.055), (w * 0.745, h * 0.575), color=TINTA, font=FONTC)
    texto(p, 'AUTHORIZED', int(w * 0.055), (w * 0.745, h * 0.645), color=TINTA, font=FONTC)
    d.line([(w * 0.52, h * 0.61), (w * 0.43, h * 0.66)], fill=_c(TINTA), width=4)
    return p


# ============================================================ pieza 3 · la fecha
def calendario_24(w=640):
    h = int(w * 1.12)
    def f(d): d.rounded_rectangle([1, 1, w - 2, h - 2], radius=14, fill=255)
    p = papel((w, h), f, BLANCO); d = _d(p)
    d.rounded_rectangle([10, 10, w - 11, h * 0.27], radius=10, fill=_c(TINTA))
    for k in range(5):
        x = w * (0.18 + k * 0.16)
        d.ellipse([x - 12, h * 0.03, x + 12, h * 0.03 + 24], fill=_c(PAPEL), outline=_c(GRIS), width=3)
    texto(p, 'SEPTEMBER', int(w * 0.12), (w / 2, h * 0.17), color=PAPEL, font=FONTC)
    texto(p, '24', int(w * 0.46), (w / 2, h * 0.63), color=TINTA, font=FONT)
    d.rounded_rectangle([10, 10, w - 11, h - 11], radius=12, outline=_c(TINTA), width=5)
    return p


def _mini_cal(p, cx, cy, s):
    d = _d(p)
    d.rounded_rectangle([cx - s / 2, cy - s * 0.56, cx + s / 2, cy + s * 0.56], radius=8, fill=_c(BLANCO), outline=_c(TINTA), width=4)
    d.rectangle([cx - s / 2 + 3, cy - s * 0.56 + 3, cx + s / 2 - 3, cy - s * 0.26], fill=_c(TINTA))
    texto(p, 'SEPTEMBER', int(s * 0.15), (cx, cy - s * 0.41), color=PAPEL, font=FONTC)
    texto(p, '24', int(s * 0.50), (cx, cy + s * 0.16), color=TINTA, font=FONT)


def _mini_contrato(p, cx, cy, s):
    d = _d(p)
    d.rectangle([cx - s * 0.42, cy - s * 0.56, cx + s * 0.42, cy + s * 0.56], fill=_c(BLANCO), outline=_c(TINTA), width=4)
    texto(p, 'ARMS', int(s * 0.19), (cx, cy - s * 0.34), color=TINTA, font=FONTC)
    texto(p, 'SALES', int(s * 0.19), (cx, cy - s * 0.14), color=TINTA, font=FONTC)
    for k in range(3):
        y = cy + s * (0.06 + k * 0.13)
        d.line([(cx - s * 0.30, y), (cx + s * 0.30, y)], fill=_c((150, 145, 130)), width=5)


def balanza(j, W=900):
    """Cuadros 0-5: la balanza oscila y queda pareja (el calendario pesa lo mismo que el contrato).
    6-9: baja el plato del contrato. 10-12: el calendario se levanta del plato y sale volando."""
    H = int(W * 1.05)
    def f(d): d.rounded_rectangle([1, 1, W - 2, H - 2], radius=18, fill=255)
    p = papel((W, H), f, PAPEL); d = _d(p)
    cx, piv = W / 2, H * 0.36
    if j <= 5:
        ang = math.radians(4.5 * math.sin(j * 1.25) * (1 - j / 6))
    else:
        ang = math.radians(min(15.0, (j - 5) * 3.8))
    L = W * 0.36
    ax, ay = cx - L * math.cos(ang), piv - L * math.sin(ang)
    bx, by = cx + L * math.cos(ang), piv + L * math.sin(ang)
    d.polygon([(cx - W * 0.10, H * 0.93), (cx + W * 0.10, H * 0.93), (cx + W * 0.03, piv), (cx - W * 0.03, piv)],
              fill=_c(MADERA), outline=_c(TINTA))
    d.line([(ax, ay), (bx, by)], fill=_c(TINTA), width=12)
    d.ellipse([cx - 18, piv - 18, cx + 18, piv + 18], fill=_c(OCRE), outline=_c(TINTA), width=4)
    s = W * 0.22
    for (px, py), lado in (((ax, ay), 'cal'), ((bx, by), 'arm')):
        plato_y = py + H * 0.34
        d.line([(px, py), (px - W * 0.10, plato_y)], fill=_c(TINTA), width=4)
        d.line([(px, py), (px + W * 0.10, plato_y)], fill=_c(TINTA), width=4)
        d.chord([px - W * 0.14, plato_y - H * 0.05, px + W * 0.14, plato_y + H * 0.06], 0, 180, fill=_c(ACERO), outline=_c(TINTA), width=4)
        if lado == 'arm':
            _mini_contrato(p, px, plato_y - s * 0.56, s)
        else:
            vuela = 0.0 if j < 10 else (j - 9) / 3
            _mini_cal(p, px - W * 0.04 * vuela, plato_y - s * 0.56 - H * 0.18 * vuela, s)
    return p


def guardacostas(w=900):
    h = int(w * 0.42)
    def f(d):
        d.polygon([(0, h * 0.48), (w * 0.97, h * 0.48), (w * 0.90, h * 0.86), (w * 0.05, h * 0.86)], fill=255)
        d.rectangle([w * 0.18, h * 0.20, w * 0.62, h * 0.48], fill=255)
        d.rectangle([w * 0.30, h * 0.02, w * 0.36, h * 0.20], fill=255)
    p = papel((w, h), f, BLANCO); d = _d(p)
    d.polygon([(0, h * 0.48), (w * 0.97, h * 0.48), (w * 0.90, h * 0.86), (w * 0.05, h * 0.86)], outline=_c(TINTA), width=5)
    # la franja de la librea: roja y azul, en diagonal, hacia la proa
    d.polygon([(w * 0.70, h * 0.48), (w * 0.76, h * 0.48), (w * 0.70, h * 0.86), (w * 0.64, h * 0.86)], fill=_c(ROJO))
    d.polygon([(w * 0.78, h * 0.48), (w * 0.81, h * 0.48), (w * 0.75, h * 0.86), (w * 0.72, h * 0.86)], fill=_c(AZUL))
    d.rectangle([w * 0.18, h * 0.20, w * 0.62, h * 0.48], fill=_c(BLANCO), outline=_c(TINTA), width=5)
    for k in range(5):
        x = w * (0.22 + k * 0.08)
        d.rectangle([x, h * 0.27, x + w * 0.05, h * 0.36], fill=_c((70, 90, 110)))
    d.rectangle([w * 0.30, h * 0.02, w * 0.36, h * 0.20], fill=_c(GRIS_C), outline=_c(TINTA), width=4)
    texto(p, 'COAST GUARD', int(w * 0.055), (w * 0.33, h * 0.66), color=AZUL, font=FONTC)
    return p


# ============================================================ pieza 4 · la subasta
def gilt_30(w=1000):
    h = int(w * 0.68)
    def f(d): d.rounded_rectangle([1, 1, w - 2, h - 2], radius=10, fill=255)
    p = papel((w, h), f, (238, 230, 208)); d = _d(p)
    d.rounded_rectangle([14, 14, w - 15, h - 15], radius=8, outline=_c(TINTA), width=6)
    d.rounded_rectangle([34, 34, w - 35, h - 35], radius=6, outline=_c(OCRE), width=4)
    texto(p, 'TREASURY', int(w * 0.060), (w / 2, h * 0.17), color=TINTA, font=FONTC)
    texto(p, '30-YEAR GILT', int(w * 0.105), (w / 2, h * 0.36), color=TINTA, font=FONT)
    d.line([(w * 0.20, h * 0.47), (w * 0.80, h * 0.47)], fill=_c(TINTA), width=4)
    texto(p, '£4.25BN', int(w * 0.090), (w * 0.30, h * 0.66), color=TINTA, font=FONTC)
    texto(p, '5.82%', int(w * 0.110), (w * 0.70, h * 0.66), color=AZUL, font=FONT)
    d.ellipse([w * 0.44, h * 0.76, w * 0.56, h * 0.92], outline=_c(OCRE), width=6)
    return p


def _pila(p, x0, base, w, alto, col):
    d = _d(p)
    n = max(0, int(alto / 22))
    for k in range(n):
        y1 = base - k * 22
        d.rectangle([x0, y1 - 18, x0 + w, y1], fill=_c(col), outline=_c(TINTA), width=3)
        d.ellipse([x0 + w * 0.42, y1 - 15, x0 + w * 0.58, y1 - 3], outline=_c(PAPEL, 200), width=2)


def pilas(j, W=900):
    """Izquierda: la pila del margen, fija (£13bn · HEADROOM, F19). Derecha: crece de 0 al 91 % en
    los cuadros 0-10 (£11.8bn · JUNE, F20). 11,8 / 13 = 0,908: la altura es la aritmetica, no un gusto."""
    H = int(W * 1.12)
    def f(d): d.rounded_rectangle([1, 1, W - 2, H - 2], radius=18, fill=255)
    p = papel((W, H), f, PAPEL); d = _d(p)
    base = H * 0.78
    alto_max = H * 0.60
    pw = W * 0.30
    _pila(p, W * 0.12, base, pw, alto_max, LIBRA)
    frac = min(1.0, j / 10) * (11.8 / 13.0)
    _pila(p, W * 0.58, base, pw, alto_max * frac, (150, 118, 162))
    d.line([(W * 0.06, base + 3), (W * 0.94, base + 3)], fill=_c(TINTA), width=6)
    texto(p, '£13BN', int(W * 0.085), (W * 0.27, base + H * 0.075), color=TINTA, font=FONTC)
    texto(p, 'HEADROOM', int(W * 0.050), (W * 0.27, base + H * 0.145), color=GRIS, font=FONTC)
    if j >= 10:
        texto(p, '£11.8BN', int(W * 0.085), (W * 0.73, base + H * 0.075), color=TINTA, font=FONTC)
        texto(p, 'JUNE', int(W * 0.050), (W * 0.73, base + H * 0.145), color=GRIS, font=FONTC)
    return p



# ============================================================ v2 (16-sep): los reusados que eran chicos
# Mirando la hoja de 16 cuadros reales: `dron_grande` (186 px), `deposito_fuel` (156), `martillo_juez`
# (166) y `capitolio` (226) se ven diminutos en un cuadro de 1080 de ancho, y agrandarlos 2-3 veces los
# emborrona. Se redibujan al tamaño al que se ven (leccion del ep. 09).
def dron_largo(w=820):
    """Dron de ataque de largo alcance: fuselaje, ala recta, cola en V y helice atras. Sin letras."""
    h = int(w * 0.46)
    def f(d):
        d.rounded_rectangle([w * 0.10, h * 0.40, w * 0.86, h * 0.60], radius=int(h * 0.10), fill=255)
        d.polygon([(w * 0.86, h * 0.40), (w * 0.99, h * 0.50), (w * 0.86, h * 0.60)], fill=255)
        d.polygon([(w * 0.40, h * 0.42), (w * 0.52, h * 0.42), (w * 0.47, h * 0.02), (w * 0.36, h * 0.02)], fill=255)
        d.polygon([(w * 0.40, h * 0.58), (w * 0.52, h * 0.58), (w * 0.47, h * 0.98), (w * 0.36, h * 0.98)], fill=255)
        d.polygon([(w * 0.10, h * 0.44), (w * 0.20, h * 0.44), (w * 0.12, h * 0.20), (w * 0.05, h * 0.20)], fill=255)
        d.polygon([(w * 0.10, h * 0.56), (w * 0.20, h * 0.56), (w * 0.12, h * 0.80), (w * 0.05, h * 0.80)], fill=255)
    p = papel((w, h), f, (150, 152, 140)); d = _d(p)
    d.rounded_rectangle([w * 0.10, h * 0.40, w * 0.86, h * 0.60], radius=int(h * 0.10), outline=_c(TINTA), width=5)
    d.polygon([(w * 0.40, h * 0.42), (w * 0.52, h * 0.42), (w * 0.47, h * 0.02), (w * 0.36, h * 0.02)], outline=_c(TINTA), width=4)
    d.polygon([(w * 0.40, h * 0.58), (w * 0.52, h * 0.58), (w * 0.47, h * 0.98), (w * 0.36, h * 0.98)], outline=_c(TINTA), width=4)
    d.ellipse([w * 0.015, h * 0.30, w * 0.075, h * 0.70], fill=_c(TINTA))
    d.line([(w * 0.60, h * 0.50), (w * 0.84, h * 0.50)], fill=_c(TINTA, 160), width=4)
    return p


def cisterna(w=920):
    """Camion cisterna de diesel. Dice DIESEL, que la voz dice (linea 11)."""
    h = int(w * 0.44)
    def f(d):
        d.rounded_rectangle([w * 0.02, h * 0.10, w * 0.72, h * 0.74], radius=int(h * 0.30), fill=255)
        d.rounded_rectangle([w * 0.74, h * 0.30, w * 0.99, h * 0.80], radius=int(h * 0.06), fill=255)
        d.rectangle([w * 0.02, h * 0.70, w * 0.99, h * 0.84], fill=255)
    p = papel((w, h), f, (205, 200, 190)); d = _d(p)
    d.rounded_rectangle([w * 0.02, h * 0.10, w * 0.72, h * 0.74], radius=int(h * 0.30), outline=_c(TINTA), width=6)
    d.rounded_rectangle([w * 0.74, h * 0.30, w * 0.99, h * 0.80], radius=int(h * 0.06), fill=_c(AZUL), outline=_c(TINTA), width=6)
    d.rectangle([w * 0.80, h * 0.36, w * 0.95, h * 0.54], fill=_c((150, 180, 200)), outline=_c(TINTA), width=4)
    d.rectangle([w * 0.02, h * 0.74, w * 0.99, h * 0.84], fill=_c(TINTA))
    for cx in (0.14, 0.30, 0.62, 0.88):
        d.ellipse([w * cx - h * 0.12, h * 0.72, w * cx + h * 0.12, h * 0.98], fill=_c(TINTA), outline=_c(GRIS), width=4)
    d.rounded_rectangle([w * 0.18, h * 0.28, w * 0.56, h * 0.56], radius=10, fill=_c(OCRE), outline=_c(TINTA), width=5)
    texto(p, 'DIESEL', int(w * 0.075), (w * 0.37, h * 0.42), color=TINTA, font=FONTC)
    return p


def martillo_subasta(w=760):
    """Martillo de subasta con su taco. Sin letras."""
    h = int(w * 0.72)
    def f(d):
        d.rounded_rectangle([w * 0.08, h * 0.78, w * 0.92, h * 0.98], radius=14, fill=255)
    base = papel((w, h), f, MADERA)
    d = _d(base)
    d.rounded_rectangle([w * 0.08, h * 0.78, w * 0.92, h * 0.98], radius=14, outline=_c(TINTA), width=5)
    cab = Image.new('RGBA', (int(w * 0.52), int(h * 0.36)), (0, 0, 0, 0)); dc = ImageDraw.Draw(cab)
    dc.rounded_rectangle([4, 4, cab.width - 5, cab.height - 5], radius=int(cab.height * 0.22), fill=_c((140, 96, 60)), outline=_c(TINTA), width=6)
    for fx in (0.22, 0.78):
        dc.rectangle([cab.width * fx - 8, 4, cab.width * fx + 8, cab.height - 5], fill=_c(OCRE))
    mango = Image.new('RGBA', (int(w * 0.66), int(h * 0.08)), (0, 0, 0, 0)); dm = ImageDraw.Draw(mango)
    dm.rounded_rectangle([2, 2, mango.width - 3, mango.height - 3], radius=int(mango.height / 2), fill=_c((120, 82, 50)), outline=_c(TINTA), width=4)
    g = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    g.alpha_composite(mango, (int(w * 0.30), int(h * 0.44)))
    g.alpha_composite(cab, (int(w * 0.06), int(h * 0.30)))
    g = g.rotate(-14, resample=Image.BICUBIC, center=(w * 0.5, h * 0.5))
    base.alpha_composite(g, (0, -int(h * 0.12)))
    return base


def capitolio_g(w=880):
    """El Capitolio de los EE. UU.: escalinata, columnata, cupula con tambor y linterna. Sin letras."""
    h = int(w * 0.80)
    def f(d):
        d.rectangle([0, h * 0.62, w, h * 0.99], fill=255)
        d.rectangle([w * 0.26, h * 0.40, w * 0.74, h * 0.64], fill=255)
        d.pieslice([w * 0.32, h * 0.10, w * 0.68, h * 0.62], 180, 360, fill=255)
        d.rectangle([w * 0.47, h * 0.00, w * 0.53, h * 0.14], fill=255)
    p = papel((w, h), f, BLANCO); d = _d(p)
    d.rectangle([0, h * 0.62, w, h * 0.99], outline=_c(TINTA), width=5)
    for k in range(17):
        x = w * (0.04 + k * 0.058)
        d.rectangle([x, h * 0.68, x + w * 0.022, h * 0.92], fill=_c(GRIS_C), outline=_c(TINTA), width=2)
    d.line([(0, h * 0.925), (w, h * 0.925)], fill=_c(TINTA), width=5)
    d.rectangle([w * 0.26, h * 0.40, w * 0.74, h * 0.64], outline=_c(TINTA), width=5)
    for k in range(9):
        x = w * (0.29 + k * 0.05)
        d.rectangle([x, h * 0.44, x + w * 0.018, h * 0.61], fill=_c(GRIS_C))
    d.pieslice([w * 0.32, h * 0.10, w * 0.68, h * 0.62], 180, 360, outline=_c(TINTA), width=6)
    for k in range(1, 6):
        x = w * (0.32 + k * 0.06)
        d.line([(x, h * 0.37), (w * 0.50, h * 0.12)], fill=_c(TINTA, 120), width=3)
    d.rectangle([w * 0.47, h * 0.00, w * 0.53, h * 0.14], fill=_c(BLANCO), outline=_c(TINTA), width=4)
    return p

# ============================================================ salida
def todo():
    guardar('bandera_ua', bandera_ua(), 'UKRAINE')
    guardar('bandera_ve', bandera_ve(), 'VENEZUELA')
    guardar('bandera_tw', bandera_tw(), 'TAIWAN')
    guardar('bandera_china', bandera_china(), 'CHINA')
    guardar('bandera_rusia', bandera_rusia(), 'RUSSIA')
    guardar('bandera_eeuu', bandera_eeuu(), 'UNITED STATES')
    guardar('refineria', refineria(), '')
    guardar('refineria_off', refineria(estado=0.0), '')
    for j in range(PASOS):
        txt = ' '.join(NOMBRES6) + (' SHUT DOWN' if j >= 3 else '')
        guardar('refinerias_d%02d' % j, refinerias(j), txt)
    guardar('doc_iea', doc_iea(), 'INTERNATIONAL ENERGY AGENCY')
    guardar('lancha', lancha(), '')
    for j in range(9):
        guardar('votos_a%02d' % j, votos_a(j), '50 50' if j >= 8 else '')
    for j in range(5):
        guardar('votos_b%02d' % j, votos_b(j), '50 51' if j >= 4 else '50 50')
    guardar('doc_memo', doc_memo(), 'LAW ENFORCEMENT ACTION WITH MILITARY SUPPORT')
    guardar('estante', estante(), 'NEVER AUTHORIZED')
    guardar('calendario_24', calendario_24(), 'SEPTEMBER 24')
    for j in range(PASOS):
        guardar('balanza_d%02d' % j, balanza(j), 'SEPTEMBER 24 ARMS SALES')
    guardar('guardacostas', guardacostas(), 'COAST GUARD')
    guardar('gilt_30', gilt_30(), 'TREASURY 30-YEAR GILT £4.25BN 5.82%')
    guardar('dron_largo', dron_largo(), '')
    guardar('cisterna', cisterna(), 'DIESEL')
    guardar('martillo_subasta', martillo_subasta(), '')
    guardar('capitolio_g', capitolio_g(), '')
    for j in range(PASOS):
        txt = '£13BN HEADROOM' + (' £11.8BN JUNE' if j >= 10 else '')
        guardar('pilas_d%02d' % j, pilas(j), txt)
    # reusados sin letras (o con las que ya se miraron): se declaran igual, compo lo exige
    for nom, txt in (('dron_grande', ''), ('deposito_fuel', 'FUEL'), ('capitolio', ''), ('buque_us', ''),
                     ('bandera_rusa', ''), ('bandera_us', ''), ('bandera_cn', ''), ('bandera_uk', ''),
                     ('humo', '')):
        TEXTOS[nom] = txt
    for nom, txt in TEXTOS.items():
        with open(os.path.join(OUT, 'prop_%s.txt' % nom), 'w', encoding='utf-8') as fh:
            fh.write(txt)
    print('props S13: %d nombres declarados, PNG en %s' % (len(TEXTOS), OUT))


def hoja():
    nombres = ['bandera_ua', 'bandera_ve', 'bandera_tw', 'refineria', 'refineria_off', 'refinerias_d00',
               'refinerias_d06', 'refinerias_d12', 'doc_iea', 'lancha', 'votos_d04', 'votos_d08', 'votos_d12',
               'doc_memo', 'estante', 'calendario_24', 'balanza_d03', 'balanza_d08', 'balanza_d12',
               'guardacostas', 'gilt_30', 'pilas_d00', 'pilas_d06', 'pilas_d12']
    cel, cols = 380, 6
    rows = (len(nombres) + cols - 1) // cols
    H = Image.new('RGB', (cols * cel, rows * (cel + 34)), (206, 196, 176))
    dd = ImageDraw.Draw(H)
    for i, n in enumerate(nombres):
        im = Image.open(os.path.join(OUT, 'prop_%s.png' % n)).convert('RGBA')
        t = im.copy(); t.thumbnail((cel - 20, cel - 20))
        x, y = (i % cols) * cel, (i // cols) * (cel + 34)
        H.paste(t, (x + (cel - t.width) // 2, y + (cel - t.height) // 2), t)
        dd.text((x + 8, y + cel + 6), n, fill=(30, 25, 20), font=FONTC(22))
    ruta = os.path.join(AQUI, '..', '_qc', 'hoja_props_s13.jpg')
    H.save(ruta, quality=86)
    print('hoja:', os.path.abspath(ruta))


if __name__ == '__main__':
    todo()
    if '--hoja' in sys.argv:
        hoja()
