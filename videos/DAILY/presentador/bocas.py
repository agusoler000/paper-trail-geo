# -*- coding: utf-8 -*-
"""Las nueve formas de boca del lip-sync del presentador, DIBUJADAS (no generadas).

    python videos/DAILY/presentador/bocas.py --autotest    # prueba + arma _bocas.jpg
    python videos/DAILY/presentador/bocas.py --tira        # solo la hoja de contacto

POR QUE DIBUJADAS Y NO GENERADAS
    Nueve bocas pedidas a un modelo de imagen salen distintas entre si: cambia el grosor del
    trazo, el tono del papel, el centro, la iluminacion. Pegadas una tras otra a 24 fps eso no
    se lee como una boca que habla, se lee como una boca que TITILA — el ojo detecta el salto
    de estilo antes que el movimiento. Dibujadas con el mismo codigo comparten trazo, color y
    centro por construccion: lo unico que cambia entre cuadro y cuadro es la forma, que es
    justo lo que tiene que cambiar. Ademas son controlables (un numero y se corrige) y cuestan
    cero creditos, que a 24 fps por 20 minutos de video diario no es un detalle.

LOS NUEVE VISEMAS DE RHUBARB
    A  cerrada (M, B, P)          F  fruncida (U, W)
    B  levemente abierta (cons.)  G  dientes sobre labio (F, V)
    C  abierta (E)                H  lengua (L)
    D  muy abierta (A)            X  reposo (silencio)
    E  redondeada chica (O)

COMO SE PEGAN
    Cada boca es un RGBA transparente de lienzo FIJO para un `ancho` dado (no cambia con la
    letra ni con `escala`), y el CENTRO del lienzo es la linea de labios en reposo. O sea: el
    compositor pega siempre en el mismo lugar, `pivote_boca - (W/2, H/2)`, con el pivote
    "boca" de rig_<clave>.json (en A_corresponsal es [390, 296]). La boca se abre hacia abajo
    desde ese centro, como baja una mandibula; por eso el lienzo es mas alto que la boca mas
    abierta y sobra margen arriba.

    OJO, PENDIENTE DEL RIG: cabeza.png viene con la boca en reposo YA IMPRESA. Probado
    componiendo estas nueve sobre la cara: la posicion y el tamano dan, pero en las aperturas
    angostas (D, E, F) asoman las comisuras de la boca impresa por fuera de la nueva. La
    solucion no es agrandar estas bocas — es borrar la boca de cabeza.png una sola vez y
    dejar que la dibuje este modulo siempre, X incluida. dibujar_boca("X") reproduce esa misma
    linea, asi que la cara en silencio queda igual que hoy.

EL TRAZO
    Medido sobre A_corresponsal_alpha.png (768x1024): boca en reposo de 91 px de ancho, trazo
    de 3 px, comba de 3 px hacia abajo y un ganchito de 7 px hacia arriba en cada comisura.
    Esas proporciones son las que reproduce este modulo, normalizadas al `ancho` que se pida.
    La tinta real de esa cara es TINTA_CARA_A, un marron calido, no el negro neutro del repo:
    el default de `color_tinta` respeta la paleta de ESTILO.md, pero para componer sobre el
    corresponsal conviene pasarle TINTA_CARA_A.

Sin dependencias nuevas: PIL y stdlib.
"""
import bisect
import json
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))

BOCAS = "ABCDEFGHX"

# --- paleta -----------------------------------------------------------------
PAPEL = (233, 223, 203)
TINTA = (34, 32, 28)              # tinta del repo (ESTILO.md)
TINTA_CARA_A = (65, 35, 22)       # medida sobre A_corresponsal_alpha.png
INTERIOR = (104, 71, 59)          # el hueco de la boca: papel de abajo, no negro. Tiene que
                                  # quedar bastante mas claro que la tinta o el anillo del
                                  # labio se funde con el hueco y la O se vuelve una mancha.
DIENTES = (244, 238, 224)
LENGUA = (166, 98, 88)
ROJO = (184, 64, 47)
GRIS = (120, 112, 98)

# que fonema dibuja cada letra; lo usa la hoja de contacto y sirve de documentacion
FONEMAS = {
    "A": ("M · B · P", "cerrada, apretada"),
    "B": ("consonantes", "apenas abierta"),
    "C": ("E", "abierta"),
    "D": ("A", "muy abierta"),
    "E": ("O", "redondeada chica"),
    "F": ("U · W", "fruncida"),
    "G": ("F · V", "dientes sobre labio"),
    "H": ("L", "lengua arriba"),
    "X": ("silencio", "reposo"),
}

SS = 4          # supermuestreo: se dibuja a 4x y se baja con LANCZOS
ESCALA_MIN, ESCALA_MAX = 0.40, 1.40

# Medio ancho de la boca mas ancha (X: 0.50 de cuerpo + 0.018 de medio trazo) y medio alto de
# la mas abierta (D: 0.345 + 0.019), en unidades del ancho de boca. El lienzo se dimensiona con
# estos numeros por ESCALA_MAX, para que hasta la boca mas grande a la escala mas grande entre
# ENTERA: si se agranda una forma o sube ESCALA_MAX hay que subirlos, y el autotest lo caza.
MEDIO_ANCHO, MEDIO_ALTO = 0.550, 0.395

# Cierre minimo de la pista: si Rhubarb no dice donde termina el ultimo visema, la X de cierre
# va un cuadro (24 fps) despues, nunca en el mismo instante.
CIERRE_MIN = 1.0 / 24.0


# ---------------------------------------------------------------------------
# geometria: todo en unidades del ancho de boca, origen en la linea de reposo,
# y positivo hacia abajo. Asi un mismo numero significa lo mismo a cualquier px.
# ---------------------------------------------------------------------------

def _bezier(p0, p1, p2, n=24):
    """Bezier cuadratica, n+1 puntos de p0 a p2."""
    out = []
    for i in range(n + 1):
        t = i / float(n)
        u = 1.0 - t
        out.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                    u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))
    return out


def _contorno(w, h_sup, h_inf, punta=1.0, n=48):
    """Contorno cerrado de una apertura: dos medios ovalos con radios verticales distintos.

    `punta` deforma las comisuras sin tocar el alto: >1 las afila (boca de lente, para las
    aperturas chatas), <1 las redondea (boca de O). Con 1.0 es una elipse exacta.
    """
    pts = []
    for i in range(n + 1):                       # arco de arriba, de izquierda a derecha
        ang = math.pi * (1.0 - i / float(n))
        pts.append((w / 2.0 * math.cos(ang), -h_sup * math.sin(ang) ** punta))
    for i in range(1, n):                        # arco de abajo, de derecha a izquierda
        ang = math.pi * i / float(n)
        pts.append((w / 2.0 * math.cos(ang), h_inf * math.sin(ang) ** punta))
    return pts


def _reposo(w, comba, gancho, hacia=-1.0):
    """Linea de labios cerrados: comba suave + ganchito en cada comisura.

    `hacia` -1 curva los ganchos hacia arriba (reposo, como el PNG del corresponsal) y +1
    hacia abajo (labios apretados de la M).
    """
    izq = (-w / 2.0, 0.0)
    der = (w / 2.0, 0.0)
    cuerpo = _bezier(izq, (0.0, comba), der, 40)
    gi = _bezier((izq[0] + 0.030 * w, hacia * gancho),
                 (izq[0] + 0.002 * w, hacia * gancho * 0.45), izq, 8)
    gd = _bezier(der, (der[0] - 0.002 * w, hacia * gancho * 0.45),
                 (der[0] - 0.030 * w, hacia * gancho), 8)
    return gi + cuerpo[1:] + gd[1:]


# ---------------------------------------------------------------------------
# dibujo sobre mascaras: una mascara L por material (tinta, interior, dientes,
# lengua). Se bajan de escala por separado y recien despues se pintan, para que
# el antialias no arrastre el color del vecino ni deje halo en el alfa.
# ---------------------------------------------------------------------------

def _trazo(d, pts, g, P, cerrado=False):
    """Polilinea con puntas redondeadas. `g` ya viene en pixeles del lienzo supermuestreado."""
    px = [P(x, y) for x, y in pts]
    if cerrado:
        px.append(px[0])
    gp = max(2, int(round(g)))
    d.line(px, fill=255, width=gp, joint="curve")
    r = gp / 2.0
    for q in (px[0], px[-1]):
        d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=255)


def _relleno(d, pts, P):
    d.polygon([P(x, y) for x, y in pts], fill=255)


def _banda(size, P, x0, y0, x1, y1):
    """Mascara de una banda rectangular en coordenadas normalizadas."""
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rectangle([P(x0, y0), P(x1, y1)], fill=255)
    return m


def _divisiones(size, P, xs, y0, y1, g):
    """Mascara con las rayitas verticales que separan los dientes."""
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    for x in xs:
        d.line([P(x, y0), P(x, y1)], fill=255, width=max(1, int(round(g))))
    return m


def dibujar_boca(letra, ancho=120, color_tinta=TINTA, color_interior=INTERIOR, escala=1.0,
                 color_dientes=None, color_lengua=None):
    """Devuelve la boca `letra` como PIL.Image RGBA transparente, centrada en su lienzo.

    ancho  ancho de la boca en reposo, en pixeles. Fija el tamano del lienzo, que es el
           MISMO para las nueve letras y para cualquier `escala`.
    escala multiplica el dibujo dentro de ese lienzo fijo. Sirve para enfatizar o para que el
           presentador module sin que el compositor tenga que recalcular nada. Se RECORTA en
           silencio a ESCALA_MIN..ESCALA_MAX (0.40..1.40): el llamador tipico le pasa una curva
           de modulacion y prefiere un tope a una excepcion a mitad de render. El tope no es
           decorativo — el lienzo esta dimensionado para ESCALA_MAX y por encima la boca se
           saldria del borde.
    """
    letra = str(letra).strip().upper()
    if letra not in BOCAS:
        raise ValueError("visema desconocido %r; los validos son %s" % (letra, BOCAS))
    ancho = int(ancho)
    if ancho < 24:
        raise ValueError("ancho %d demasiado chico; el trazo no sobrevive abajo de 24 px" % ancho)
    escala = min(ESCALA_MAX, max(ESCALA_MIN, float(escala)))
    dientes_col = tuple(color_dientes or DIENTES)
    lengua_col = tuple(color_lengua or LENGUA)

    W, H = lienzo(ancho)
    size = (W * SS, H * SS)
    a = ancho * escala * SS
    cx, cy = W * SS / 2.0, H * SS / 2.0

    def P(x, y):
        return (cx + x * a, cy + y * a)

    m_tinta = Image.new("L", size, 0)
    m_int = Image.new("L", size, 0)
    m_dien = Image.new("L", size, 0)
    m_leng = Image.new("L", size, 0)
    d_tinta = ImageDraw.Draw(m_tinta)
    d_int = ImageDraw.Draw(m_int)

    def abrir(w, h_sup, h_inf, punta, g):
        """Hueco de la boca: rellena el interior y traza el borde. Devuelve el contorno."""
        c = _contorno(w, h_sup, h_inf, punta)
        _relleno(d_int, c, P)
        _trazo(d_tinta, c, g * a, P, cerrado=True)
        return c

    def poner_dientes(y0, y1, xs, g_div):
        """Banda de dientes recortada contra el interior, con las rayitas en tinta."""
        banda = ImageChops.darker(_banda(size, P, -0.60, y0, 0.60, y1), m_int)
        m_dien.paste(banda, (0, 0), banda)
        if xs:
            rayas = ImageChops.darker(_divisiones(size, P, xs, y0, y1, g_div * a), banda)
            m_tinta.paste(rayas, (0, 0), rayas)

    def poner_lengua(pts, arco, g):
        """Lengua recortada contra el interior, con el borde de arriba en tinta."""
        capa = Image.new("L", size, 0)
        _relleno(ImageDraw.Draw(capa), pts, P)
        capa = ImageChops.darker(capa, m_int)
        m_leng.paste(capa, (0, 0), capa)
        borde = Image.new("L", size, 0)
        _trazo(ImageDraw.Draw(borde), arco, g * a, P)
        borde = ImageChops.darker(borde, m_int)
        m_tinta.paste(borde, (0, 0), borde)

    # -- las nueve formas ---------------------------------------------------
    if letra == "X":
        # reposo: la linea del PNG original. Cuerpo casi recto con una comba minima y el
        # ganchito de la comisura marcado — si se le da mas comba deja de leerse el gancho
        # y la boca pasa a ser una sonrisa, que no es la cara del corresponsal.
        _trazo(d_tinta, _reposo(1.00, 0.048, 0.080, hacia=-1.0), 0.036 * a, P)

    elif letra == "A":
        # M/B/P: mas corta, mas gruesa, casi recta y con las comisuras hacia abajo;
        # arriba se insinua el labio superior aplastado, que es lo que la separa de X
        _trazo(d_tinta, _reposo(0.88, 0.020, 0.030, hacia=1.0), 0.052 * a, P)
        _trazo(d_tinta, _bezier((-0.24, -0.055), (0.0, -0.090), (0.24, -0.055), 20), 0.020 * a, P)

    elif letra == "B":
        abrir(0.72, 0.070, 0.090, 1.55, 0.036)
        poner_dientes(-0.078, -0.014, (-0.11, 0.0, 0.11), 0.013)

    elif letra == "C":
        abrir(0.80, 0.125, 0.170, 1.30, 0.036)
        poner_dientes(-0.135, -0.055, (-0.13, 0.0, 0.13), 0.014)

    elif letra == "D":
        abrir(0.62, 0.145, 0.345, 1.02, 0.038)
        poner_dientes(-0.155, -0.100, (-0.10, 0.0, 0.10), 0.013)
        # la lengua tiene que llegar a las dos paredes: si queda flotando en el medio
        # parece una mancha pegada, no el piso de la boca
        arco = _bezier((-0.32, 0.42), (0.0, 0.06), (0.32, 0.42), 32)
        poner_lengua(arco + [(0.36, 0.55), (-0.36, 0.55)], arco, 0.016)

    elif letra == "E":
        # la O es mas ANCHA que alta
        abrir(0.42, 0.155, 0.185, 0.92, 0.042)

    elif letra == "F":
        # el fruncido de la U es mas ALTO que ancho, mas chico, y con el labio mas gordo:
        # esa inversion de proporcion es lo que lo separa de la O. Probe marcarle los
        # pliegues del fruncido a los costados y quedaba una tuerca, asi que lo dice la forma.
        abrir(0.24, 0.115, 0.150, 0.86, 0.056)

    elif letra == "G":
        # F/V: el labio de abajo se mete y los incisivos se apoyan encima. Sale mas angosta
        # que la B a proposito: son las dos bocas chatas del set y hay que poder separarlas
        # de un vistazo, no solo por el brillo de los dientes.
        c = abrir(0.58, 0.125, 0.026, 1.45, 0.034)
        poner_dientes(-0.135, 0.010, (-0.145, -0.048, 0.048, 0.145), 0.013)
        # solo el arco de abajo, mas grueso. El corte se saca del propio contorno y no de un
        # 49 escrito a mano: _contorno devuelve 2n puntos con el arco de abajo desde n+1, y si
        # alguien le toca la `n` el 49 dejaba de ser el arco de abajo sin que nada avisara
        inf = c[len(c) // 2 + 1:] + [c[0]]
        _trazo(d_tinta, inf, 0.062 * a, P)

    elif letra == "H":
        abrir(0.58, 0.115, 0.215, 1.15, 0.036)
        poner_dientes(-0.125, -0.062, (-0.12, 0.0, 0.12), 0.013)
        arco = (_bezier((-0.20, 0.32), (-0.13, -0.06), (0.0, -0.105), 24) +
                _bezier((0.0, -0.105), (0.13, -0.06), (0.20, 0.32), 24)[1:])
        poner_lengua(arco + [(0.26, 0.42), (-0.26, 0.42)], arco, 0.016)

    # -- bajar de escala y pintar -------------------------------------------
    m_tinta = m_tinta.resize((W, H), Image.LANCZOS)
    m_int = m_int.resize((W, H), Image.LANCZOS)
    m_dien = m_dien.resize((W, H), Image.LANCZOS)
    m_leng = m_leng.resize((W, H), Image.LANCZOS)

    # el fondo lleva el RGB de la tinta con alfa 0: asi el borde que se desvanece no
    # arrastra un halo oscuro de un RGB (0,0,0) invisible
    im = Image.new("RGBA", (W, H), tuple(color_tinta) + (0,))
    im.paste(tuple(color_interior) + (255,), (0, 0), m_int)
    im.paste(dientes_col + (255,), (0, 0), m_dien)
    im.paste(lengua_col + (255,), (0, 0), m_leng)
    im.paste(tuple(color_tinta) + (255,), (0, 0), m_tinta)
    return im


def lienzo(ancho):
    """Tamano del lienzo para ese ancho de boca. Igual para las nueve letras y toda `escala`.

    Sale de MEDIO_ANCHO/MEDIO_ALTO por ESCALA_MAX y no de un numero suelto: el lienzo tiene
    que contener la boca mas grande a la escala mas grande, si no las comisuras de X y de A
    salen cortadas en plano justo cuando el presentador enfatiza.
    """
    W = int(round(ancho * 2.0 * MEDIO_ANCHO * ESCALA_MAX))
    H = int(round(ancho * 2.0 * MEDIO_ALTO * ESCALA_MAX))
    return (W + W % 2, H + H % 2)


# ---------------------------------------------------------------------------
# la pista de Rhubarb
# ---------------------------------------------------------------------------

def pista_visemas(path_json_rhubarb):
    """Lee la salida de `rhubarb -f json` y devuelve [(t_segundos, letra), ...] ordenada.

    Acepta el documento completo ({"metadata":..., "mouthCues":[...]}) o la lista de cues
    sola. Colapsa cues consecutivos con el mismo visema (no aportan nada y multiplican el
    trabajo del compositor) y, si la pista no termina en X, le agrega el cierre en el `end`
    mas tardio: una boca que se queda abierta en el ultimo cuadro se nota muchisimo.
    """
    with open(path_json_rhubarb, "r", encoding="utf-8") as fh:
        doc = json.load(fh)
    cues = doc.get("mouthCues") if isinstance(doc, dict) else doc
    if cues is None:
        raise ValueError("%s no tiene 'mouthCues'" % path_json_rhubarb)
    if not isinstance(cues, list):
        raise ValueError("'mouthCues' de %s no es una lista" % path_json_rhubarb)

    crudo, fin = [], 0.0
    for c in cues:
        try:
            t = float(c["start"])
            v = str(c["value"]).strip().upper()
            fin = max(fin, float(c.get("end", t)))   # el 'end' tambien se valida aca, para que
        except (KeyError, TypeError, ValueError):    # el error diga que archivo y que cue
            raise ValueError("cue mal formado en %s: %r" % (path_json_rhubarb, c))
        if v not in BOCAS:
            raise ValueError("visema %r fuera de %s en %s" % (v, BOCAS, path_json_rhubarb))
        crudo.append((t, v))

    crudo.sort(key=lambda p: p[0])
    pista = []
    for t, v in crudo:
        if pista and pista[-1][1] == v:
            continue
        pista.append((t, v))
    if not pista:
        return [(0.0, "X")]
    if pista[-1][1] != "X":
        # el cierre va ESTRICTAMENTE despues del ultimo visema. Si cae en el mismo instante
        # —Rhubarb sin 'end', o un 'end' que no supera al 'start'— la X tapa al ultimo cue en
        # boca_en y esa boca no se dibuja nunca: el video termina la frase con la cara ya en
        # reposo. Solo se inventa el instante cuando el archivo no lo dice.
        cierre = fin if fin > pista[-1][0] else pista[-1][0] + CIERRE_MIN
        pista.append((cierre, "X"))
    return pista


def boca_en(pista, t):
    """Que visema toca en el segundo `t`. Antes del primer cue y con pista vacia, reposo."""
    if not pista:
        return "X"
    t = float(t)
    if t < pista[0][0]:
        return "X"
    # (t, '￿') queda despues de (t, cualquier_letra): bisect_right da el cue vigente
    i = bisect.bisect_right(pista, (t, "￿")) - 1
    return pista[i][1]


# ---------------------------------------------------------------------------
# hoja de contacto
# ---------------------------------------------------------------------------

def _f(px, bold=False):
    for n in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(n, px)
        except Exception:
            pass
    return ImageFont.load_default()


def tira(destino=None, ancho_grande=210, ancho_real=120):
    """Arma _bocas.jpg: las nueve rotuladas, y debajo la misma boca al tamano de uso."""
    destino = destino or os.path.join(BASE, "_bocas.jpg")
    CW, GAP, MARG, CAB = 252, 14, 44, 132
    GW, GH = lienzo(ancho_grande)
    RW, RH = lienzo(ancho_real)
    fila_rotulo = 118
    H = CAB + GH + fila_rotulo + RH + 46 + MARG
    W = MARG * 2 + 9 * CW + 8 * GAP

    hoja = Image.new("RGB", (W, H), PAPEL)
    d = ImageDraw.Draw(hoja)
    d.text((MARG, 40), "LAS NUEVE BOCAS · LIP-SYNC DEL PRESENTADOR", font=_f(46, True), fill=TINTA)
    d.text((MARG, 96), "dibujadas, no generadas: mismo trazo, mismo centro, cero creditos  ·  "
                       "visemas de Rhubarb", font=_f(24), fill=GRIS)

    for i, L in enumerate(BOCAS):
        x = MARG + i * (CW + GAP)
        d.rectangle([x - 2, CAB - 2, x + CW + 2, H - MARG + 2], outline=(203, 192, 170), width=2)

        g = dibujar_boca(L, ancho=ancho_grande, color_tinta=TINTA_CARA_A)
        hoja.paste(g, (x + (CW - GW) // 2, CAB + 10), g)

        y = CAB + GH + 22
        d.line([x + 18, y, x + CW - 18, y], fill=(203, 192, 170), width=2)
        d.text((x + 18, y + 14), L, font=_f(54, True), fill=ROJO)
        fon, nota = FONEMAS[L]
        d.text((x + 68, y + 26), fon, font=_f(26, True), fill=TINTA)
        d.text((x + 18, y + 78), nota, font=_f(20), fill=GRIS)

        r = dibujar_boca(L, ancho=ancho_real, color_tinta=TINTA_CARA_A)
        ry = y + fila_rotulo
        hoja.paste(r, (x + (CW - RW) // 2, ry), r)
        d.text((x + 18, ry + RH + 6), "%d px, tamano de uso" % ancho_real, font=_f(17), fill=GRIS)

    hoja.save(destino, quality=93)
    return destino, hoja.size


# ---------------------------------------------------------------------------
# autotest
# ---------------------------------------------------------------------------

JSON_EJEMPLO = {
    "metadata": {"soundFile": "voz_2026-09-11.wav", "duration": 2.36},
    "mouthCues": [
        {"start": 0.00, "end": 0.21, "value": "X"},
        {"start": 0.21, "end": 0.33, "value": "B"},
        {"start": 0.33, "end": 0.48, "value": "C"},
        {"start": 0.48, "end": 0.57, "value": "B"},
        {"start": 0.57, "end": 0.72, "value": "A"},
        {"start": 0.72, "end": 0.95, "value": "D"},
        {"start": 0.95, "end": 1.04, "value": "G"},
        {"start": 1.04, "end": 1.23, "value": "E"},
        {"start": 1.23, "end": 1.31, "value": "E"},   # repetido: se tiene que colapsar
        {"start": 1.31, "end": 1.52, "value": "F"},
        {"start": 1.52, "end": 1.68, "value": "H"},
        {"start": 1.68, "end": 1.90, "value": "C"},
        {"start": 1.90, "end": 2.36, "value": "X"},
    ],
}


def _autotest():
    import tempfile

    fallas = []

    def ok(cond, texto, detalle=""):
        print(("OK    " if cond else "FALLA ") + texto + (("  ·  " + detalle) if detalle else ""))
        if not cond:
            fallas.append(texto)
        return cond

    print("== bocas.py · autotest ==")

    # 1 · se dibujan las nueve, mismo lienzo, RGBA, con tinta suficiente
    W, H = lienzo(120)
    ims, tinta_px = {}, {}
    for L in BOCAS:
        im = dibujar_boca(L, ancho=120)
        ims[L] = im
        alfa = im.split()[3]
        tinta_px[L] = sum(1 for v in alfa.tobytes() if v > 200)
    ok(all(im.mode == "RGBA" for im in ims.values()), "las 9 salen en RGBA")
    ok(all(im.size == (W, H) for im in ims.values()),
       "las 9 comparten el lienzo fijo", "%dx%d" % (W, H))
    flaca = min(tinta_px, key=tinta_px.get)
    ok(min(tinta_px.values()) >= 150,
       "ninguna queda en un hilo a 120 px",
       "la mas flaca es %s con %d px opacos" % (flaca, tinta_px[flaca]))

    # borde transparente: el lienzo tiene que sobrar por los cuatro lados, y NO solo a escala
    # 1.0 — el que enfatiza usa las escalas grandes, que son las que se salen del lienzo
    def toca_borde(im):
        a = im.split()[3]
        w, h = im.size
        return max(a.crop((0, 0, w, 1)).tobytes() + a.crop((0, h - 1, w, h)).tobytes() +
                   a.crop((0, 0, 1, h)).tobytes() + a.crop((w - 1, 0, w, h)).tobytes())

    peor, quien = 0, ""
    for esc in (ESCALA_MIN, 0.7, 1.0, 1.2, ESCALA_MAX):
        for L in BOCAS:
            b = toca_borde(dibujar_boca(L, ancho=120, escala=esc))
            if b > peor:
                peor, quien = b, "%s a escala %.2f" % (L, esc)
    ok(peor == 0, "ninguna toca el borde en todo el rango de escala",
       "peor: %s con alfa %d en el borde" % (quien or "-", peor))

    # el compositor pega en pivote-(W/2,H/2) y no recalcula nada: las nueve tienen que estar
    # centradas en la misma columna, a cualquier escala, o la boca se le corre al presentador
    centros = []
    for esc in (ESCALA_MIN, 1.0, ESCALA_MAX):
        for L in BOCAS:
            x0, _, x1, _ = dibujar_boca(L, ancho=120, escala=esc).split()[3].getbbox()
            centros.append(((x0 + x1) / 2.0, "%s@%.2f" % (L, esc)))
    desvio = max(abs(c - W / 2.0) for c, _ in centros)
    ok(desvio <= 1.0, "las 9 comparten el eje vertical del lienzo",
       "desvio maximo %.1f px sobre un lienzo de %d" % (desvio, W))

    # 2 · las nueve distintas entre si (bytes, como pide el encargo) y con margen real
    iguales, pares = [], []
    letras = list(BOCAS)
    for i in range(len(letras)):
        for j in range(i + 1, len(letras)):
            a, b = letras[i], letras[j]
            if ims[a].tobytes() == ims[b].tobytes():
                iguales.append(a + b)
            aa = ims[a].split()[3].tobytes()
            bb = ims[b].split()[3].tobytes()
            dif = sum(abs(x - y) for x, y in zip(aa, bb)) / float(len(aa))
            pares.append((dif, a + b))
    ok(not iguales, "las 9 son distintas byte a byte",
       "iguales: %s" % (", ".join(iguales) if iguales else "ninguna"))
    pares.sort()
    ok(pares[0][0] >= 4.0, "el par mas parecido igual se distingue",
       "%s difiere %.1f/255 de alfa medio" % (pares[0][1], pares[0][0]))

    # 3 · la tira rotulada
    try:
        ruta, size = tira()
        ok(os.path.exists(ruta) and os.path.getsize(ruta) > 20000,
           "_bocas.jpg escrita", "%s %dx%d" % (ruta, size[0], size[1]))
    except Exception as e:
        ok(False, "_bocas.jpg escrita", repr(e))

    # 4 · ancho y escala
    im240 = dibujar_boca("D", ancho=240)
    ok(im240.size == lienzo(240), "el lienzo sigue al ancho", "%s" % (im240.size,))
    chica = dibujar_boca("D", ancho=120, escala=0.6)
    grande = dibujar_boca("D", ancho=120, escala=1.3)
    n_ch = sum(1 for v in chica.split()[3].tobytes() if v > 200)
    n_gr = sum(1 for v in grande.split()[3].tobytes() if v > 200)
    ok(chica.size == grande.size == (W, H), "escala no toca el tamano del lienzo")
    ok(n_ch < tinta_px["D"] < n_gr, "escala si cambia el dibujo",
       "0.6 -> %d px, 1.0 -> %d, 1.3 -> %d" % (n_ch, tinta_px["D"], n_gr))
    ok(dibujar_boca("d").tobytes() == dibujar_boca("D").tobytes(), "la letra no distingue caja")

    # 5 · errores que tienen que doler
    for arg, texto in ((("Z", 120), "visema invalido"), (("A", 12), "ancho ridiculo")):
        try:
            dibujar_boca(*arg)
            ok(False, "rechaza %s" % texto)
        except ValueError:
            ok(True, "rechaza %s" % texto)

    # 6 · pista_visemas sobre un JSON de Rhubarb de ejemplo
    tmp = os.path.join(tempfile.gettempdir(), "_rhubarb_ejemplo.json")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(JSON_EJEMPLO, fh)
    p = pista_visemas(tmp)
    ok(isinstance(p, list) and all(isinstance(x, tuple) and len(x) == 2 for x in p),
       "pista_visemas devuelve [(t, letra)]", "%d cues" % len(p))
    ok(all(v in BOCAS for _, v in p), "todos los visemas son validos")
    ok(all(p[i][0] <= p[i + 1][0] for i in range(len(p) - 1)), "la pista sale ordenada")
    ok(len(p) == 12, "colapsa el E repetido", "13 cues en el JSON -> %d en la pista" % len(p))
    ok(p[0] == (0.0, "X") and p[-1][1] == "X", "abre y cierra en reposo")

    # el orden de los cues no depende del orden del archivo
    revuelto = {"mouthCues": list(reversed(JSON_EJEMPLO["mouthCues"]))}
    tmp2 = os.path.join(tempfile.gettempdir(), "_rhubarb_revuelto.json")
    with open(tmp2, "w", encoding="utf-8") as fh:
        json.dump(revuelto, fh)
    ok(pista_visemas(tmp2) == p, "ordena un JSON desordenado")

    # cierre agregado cuando Rhubarb no termina en X
    tmp3 = os.path.join(tempfile.gettempdir(), "_rhubarb_sin_cierre.json")
    with open(tmp3, "w", encoding="utf-8") as fh:
        json.dump([{"start": 0.0, "end": 0.4, "value": "D"}], fh)
    p3 = pista_visemas(tmp3)
    ok(p3 == [(0.0, "D"), (0.4, "X")], "agrega el cierre en X", "%r" % (p3,))

    # cue final SIN 'end': el cierre no puede caer en el mismo instante que el ultimo visema,
    # porque lo tapa y esa boca no se dibuja jamas
    tmp3b = os.path.join(tempfile.gettempdir(), "_rhubarb_sin_end.json")
    with open(tmp3b, "w", encoding="utf-8") as fh:
        json.dump([{"start": 0.0, "end": 0.4, "value": "B"}, {"start": 0.4, "value": "D"}], fh)
    p3b = pista_visemas(tmp3b)
    ok(p3b[-1][0] > p3b[-2][0] and boca_en(p3b, 0.41) == "D",
       "el ultimo visema sobrevive aunque falte su 'end'", "%r" % (p3b,))

    try:
        tmp4 = os.path.join(tempfile.gettempdir(), "_rhubarb_roto.json")
        with open(tmp4, "w", encoding="utf-8") as fh:
            json.dump({"mouthCues": [{"start": 0.0, "end": 0.2, "value": "Q"}]}, fh)
        pista_visemas(tmp4)
        ok(False, "rechaza un visema que Rhubarb no emite")
    except ValueError:
        ok(True, "rechaza un visema que Rhubarb no emite")

    # 7 · boca_en
    casos = [(-1.0, "X"), (0.0, "X"), (0.20, "X"), (0.21, "B"), (0.30, "B"),
             (0.40, "C"), (0.60, "A"), (0.80, "D"), (1.00, "G"), (1.10, "E"),
             (1.40, "F"), (1.60, "H"), (1.80, "C"), (2.00, "X"), (99.0, "X")]
    malos = [(t, e, boca_en(p, t)) for t, e in casos if boca_en(p, t) != e]
    ok(not malos, "boca_en acierta en %d instantes" % len(casos), "%r" % (malos,))
    ok(boca_en([], 1.0) == "X", "boca_en con pista vacia da reposo")

    # barrido a 24 fps: ningun cuadro se queda sin visema valido
    cuadros = [boca_en(p, k / 24.0) for k in range(int(2.4 * 24) + 1)]
    ok(all(c in BOCAS for c in cuadros), "barrido a 24 fps", "%d cuadros" % len(cuadros))

    # 8 · lo que no se puede probar aca
    print("SALTEA: comparar contra la cara real del corresponsal compuesta por el rig — "
          "eso lo verifica rig.py cuando exista la pose con boca")

    print("== %s ==" % ("TODO OK" if not fallas else "%d FALLAS" % len(fallas)))
    return 0 if not fallas else 1


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "--autotest"
    if arg == "--autotest":
        sys.exit(_autotest())
    elif arg == "--tira":
        print("%s  %dx%d" % ((lambda r: (r[0], r[1][0], r[1][1]))(tira())))
    else:
        print(__doc__)
