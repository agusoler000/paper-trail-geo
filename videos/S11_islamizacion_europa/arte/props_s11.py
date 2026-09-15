# -*- coding: utf-8 -*-
"""Props de papel del short S11 («La islamizacion de Europa»). 0 creditos: todo dibujado por codigo.

    cd videos/S11_islamizacion_europa/arte && python props_s11.py [--hoja]

Regla 19 (reusar antes de generar): de los 253 props compartidos de `produccion/assets` esta pieza
usa tal cual **sobre, informe, fuego, humo, flecha_arriba, bandera_uk/fr/es/us** y las fichas de
actor. Aca se dibuja lo que no existia: la mezquita, la media luna, las banderas de Turquia/Arabia/
Libia, el grafico que crece, el mapa de Europa, la sinagoga y la multitud.

El vocabulario de la pieza vuelve (leccion 10 del ep. 06): **la mezquita** (el islam politico), **el
grafico** (la demografia), **el mapa** (el territorio) y **el sello rojo** (la conclusion).
"""
import os, sys, math
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', '..', '..', 'produccion'))
from PIL import Image, ImageDraw
from props import (papel, texto, sello, FONT, FONTC,
                   TINTA, PAPEL, OCRE, AZUL, ROJO, GRIS, VERDE, BLANCO)

OUT = os.path.join(AQUI, 'assets'); os.makedirs(OUT, exist_ok=True)
NEGRO = (46, 44, 42)
VERDE_ISL = (48, 82, 62)


def mezquita(w=320):
    """Mezquita: cupula, cuerpo y dos minaretes. Se reconoce por la cupula y las torres finas."""
    h = int(w*0.92)
    im = Image.new('RGBA', (w+16, h+20), (0, 0, 0, 0))

    def cuerpo(d):
        d.rounded_rectangle([w*0.16, h*0.52, w*0.84, h*0.96], radius=8, fill=255)
        d.ellipse([w*0.34, h*0.24, w*0.66, h*0.56], fill=255)
        d.rectangle([w*0.34, h*0.40, w*0.66, h*0.54], fill=255)
    p = papel((w, h), cuerpo, (214, 199, 166))
    d = ImageDraw.Draw(p)
    d.rectangle([w*0.38, h*0.52, w*0.62, h*0.72], fill=(96, 84, 66, 255))     # puerta
    d.ellipse([w*0.40, h*0.52, w*0.60, h*0.72], fill=(96, 84, 66, 255))
    d.ellipse([w*0.40, h*0.28, w*0.60, h*0.48], outline=TINTA+(255,), width=4)
    d.line([(w*0.28, h*0.30), (w*0.34, h*0.54)], fill=TINTA+(255,), width=4)
    d.line([(w*0.66, h*0.54), (w*0.72, h*0.30)], fill=TINTA+(255,), width=4)
    im.alpha_composite(p, (0, 0))

    for fx in (0.06, 0.84):                              # minaretes
        def torre(dd):
            dd.rounded_rectangle([w*0.03, 0, w*0.11, h*0.78], radius=4, fill=255)
            dd.polygon([(w*0.01, 0), (w*0.07, -h*0.08), (w*0.13, 0)], fill=255)
        t = papel((int(w*0.14), int(h*0.80)), torre, (206, 190, 152))
        im.alpha_composite(t, (int(w*fx), int(h*0.10)))
    return im


def media_luna(w=320):
    """Media luna fina (arco) + estrella anidada en la abertura. Supersampling 4x."""
    h = int(w*0.80)
    SS = 4
    W, H = w*SS, h*SS
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = 0.44*W, 0.52*H
    R = 0.30*W
    grosor = int(0.08*R)
    d.arc([cx-R, cy-R, cx+R, cy+R], start=60, end=300, fill=VERDE_ISL+(255,), width=grosor)
    sx, sy, sr = cx + 0.50*R, cy, 0.20*R
    pts = []
    for k in range(10):                                    # estrella de 5 puntas
        a = -math.pi/2 + k*math.pi/5
        rr = sr if k % 2 == 0 else sr*0.38
        pts.append((sx + rr*math.cos(a), sy + rr*math.sin(a)))
    d.polygon(pts, fill=VERDE_ISL+(255,))
    return im.resize((w, h), Image.LANCZOS)


def _bandera(w, h, pintar, etiqueta):
    H = h+58
    def f(d): d.rounded_rectangle([1, 1, w-2, H-2], radius=10, fill=255)
    p = papel((w, H), f, PAPEL); d = ImageDraw.Draw(p)
    d.rectangle([10, 12, w-11, h-6], fill=BLANCO+(255,))
    pintar(d)
    d.rectangle([10, 12, w-11, h-6], outline=TINTA+(255,), width=3)
    texto(p, etiqueta, int(w*0.125), (w/2, h+22), color=TINTA, font=FONTC)
    return p


def bandera_tr(w=250):
    h = int(w*0.62)
    def pintar(d):
        d.rectangle([12, 14, w-13, h-8], fill=(176, 62, 50, 255))
        cx, cy, r = w*0.44, h*0.50, h*0.20
        d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=BLANCO+(255,))
        d.ellipse([cx-r*0.72, cy-r*0.78, cx+r*0.80, cy+r*0.72], fill=(176, 62, 50, 255))
        sx, sy, sr = w*0.60, h*0.48, h*0.075
        d.polygon([(sx, sy-sr), (sx+sr*0.32, sy-sr*0.32), (sx+sr, sy), (sx+sr*0.32, sy+sr*0.32),
                   (sx, sy+sr), (sx-sr*0.32, sy+sr*0.32), (sx-sr, sy), (sx-sr*0.32, sy-sr*0.32)],
                  fill=BLANCO+(255,))
    return _bandera(w, h, pintar, 'TURKEY')


def bandera_sa(w=250):
    h = int(w*0.62)
    def pintar(d):
        d.rectangle([12, 14, w-13, h-8], fill=VERDE_ISL+(255,))
        d.rectangle([w*0.30, h*0.22, w*0.70, h*0.78], fill=BLANCO+(255,))
        d.polygon([(w*0.30, h*0.22), (w*0.46, h*0.50), (w*0.30, h*0.78)], fill=VERDE_ISL+(255,))
    return _bandera(w, h, pintar, 'SAUDI')


def bandera_li(w=250):
    h = int(w*0.62)
    def pintar(d):
        d.rectangle([12, 14, w-13, h*0.36], fill=(176, 62, 50, 255))
        d.rectangle([12, h*0.36, w-13, h*0.66], fill=NEGRO+(255,))
        d.rectangle([12, h*0.66, w-13, h-8], fill=VERDE_ISL+(255,))
        cx, cy, r = w*0.44, h*0.50, h*0.13
        d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=BLANCO+(255,))
        d.ellipse([cx-r*0.72, cy-r*0.78, cx+r*0.80, cy+r*0.72], fill=VERDE_ISL+(255,))
    return _bandera(w, h, pintar, 'LIBYA')


def grafico_crece(w=360, h=340):
    """Tres barras que crecen (3.8 -> 4.9 -> 7.4) con la linea que sube. La cifra va adentro."""
    def f(d): d.rounded_rectangle([1, 1, w-2, h-2], radius=10, fill=255)
    p = papel((w, h), f, BLANCO); d = ImageDraw.Draw(p)
    base = h-56
    vals = [(3.8, OCRE), (4.9, AZUL), (7.4, ROJO)]
    for i, (v, c) in enumerate(vals):
        x0 = 40 + i*(w-80)/3
        bw = (w-80)/3*0.55
        alto = (v/8.0)*(base-50)
        d.rectangle([x0, base-alto, x0+bw, base], fill=c+(255,))
        texto(p, str(v), int(w*0.10), (x0+bw/2, base-alto-30), color=c, font=FONTC)
    pts = []
    for i, (v, _) in enumerate(vals):
        x0 = 40 + i*(w-80)/3
        pts.append((x0+(w-80)/3*0.55/2, base-(v/8.0)*(base-50)))
    d.line(pts, fill=TINTA+(255,), width=5, joint='curve')
    d.line([(30, base), (w-20, base)], fill=TINTA+(255,), width=4)
    texto(p, '2016       2050', int(w*0.065), (w/2, h-26), color=TINTA, font=FONTC)
    return p


def mapa_europa(w=560, h=470):
    """Europa esquematica de papel: peninsula iberica, la bota, Escandinavia y las islas. No pretende
    precision (no se apoya ningun sitio real con coordenadas; regla 2 no aplica a una silueta)."""
    def f(d): d.rounded_rectangle([1, 1, w-2, h-2], radius=12, fill=255)
    p = papel((w, h), f, (226, 214, 178)); d = ImageDraw.Draw(p)
    d.rounded_rectangle([12, 12, w-13, h-13], radius=10, outline=TINTA+(180,), width=4)
    mar = (168, 196, 208)
    # mar (solo un borde azul tenue para que lea como mapa)
    d.rounded_rectangle([20, 20, w-21, h-21], radius=10, outline=mar+(255,), width=6)
    def blob(pts):
        d.polygon(pts, fill=PAPEL+(255,), outline=TINTA+(255,))
    # peninsula iberica
    blob([(90, 250), (150, 330), (175, 385), (140, 405), (105, 350), (75, 300)])
    # Francia / Europa central
    blob([(150, 190), (250, 160), (330, 185), (345, 250), (290, 300), (230, 285), (170, 250)])
    # Italia (la bota)
    blob([(300, 280), (350, 285), (360, 330), (335, 400), (315, 350), (295, 310)])
    # Alemania / Polonia al este
    blob([(250, 150), (360, 130), (430, 170), (410, 230), (350, 250), (290, 230)])
    # Escandinavia
    blob([(270, 60), (310, 40), (360, 55), (370, 110), (330, 135), (285, 120)])
    # Reino Unido (isla)
    blob([(150, 110), (185, 95), (200, 135), (180, 170), (150, 155)])
    # manchas rojas: las ciudades que el guion nombra
    for (x, y, n) in ((205, 150, 'BRADFORD'), (185, 235, 'MARSEILLE'), (255, 235, 'MOLENBEEK'),
                      (305, 85, 'MALMO')):
        d.ellipse([x-7, y-7, x+7, y+7], fill=ROJO+(255,))
        texto(p, n, int(w*0.05), (x+16, y-16), color=ROJO, font=FONTC)
    texto(p, 'EUROPE', int(w*0.10), (w/2, 24), color=TINTA, font=FONTC)
    return p


def sinagoga(w=300):
    """Sinagoga esquematica: arco, estrella de David y techo a dos aguas."""
    h = int(w*0.88)
    def f(d):
        d.rounded_rectangle([w*0.10, h*0.44, w*0.90, h*0.94], radius=6, fill=255)
        d.polygon([(w*0.06, h*0.46), (w*0.50, h*0.08), (w*0.94, h*0.46)], fill=255)
    p = papel((w, h), f, (214, 199, 166)); d = ImageDraw.Draw(p)
    d.rounded_rectangle([w*0.40, h*0.62, w*0.60, h*0.94], radius=4, fill=(96, 84, 66, 255))
    # estrella de David
    cx, cy, r = w*0.50, h*0.28, h*0.13
    for k in (0, 1):
        pts = []
        for i in range(6):
            a = -math.pi/2 + k*math.pi/6 + i*math.pi/3
            pts.append((cx+r*math.cos(a), cy+r*math.sin(a)))
        d.polygon(pts, outline=AZUL+(255,), width=4)
    return p


def multitud(w=360, h=300):
    """Multitud de puntos de papel (personas) que se ralean hacia la derecha."""
    def f(d): d.rounded_rectangle([1, 1, w-2, h-2], radius=10, fill=255)
    p = papel((w, h), f, (232, 226, 208)); d = ImageDraw.Draw(p)
    rnd = __import__('random').Random(11)
    for fila in range(7):
        n = 11 - fila
        for c in range(n):
            x = w*0.10 + (w*0.80)*c/max(1, n-1)
            y = h*0.16 + h*0.70*fila/6
            d.ellipse([x-13, y-22, x+13, y+22], fill=(236, 232, 220, 255))
            d.ellipse([x-13, y-22, x+13, y-8], fill=TINTA+(200,), width=2)
    return p


PIEZAS = {
 'mezquita':     lambda: mezquita(),
 'media_luna':   lambda: media_luna(),
 'bandera_tr':   lambda: bandera_tr(),
 'bandera_sa':   lambda: bandera_sa(),
 'bandera_li':   lambda: bandera_li(),
 'grafico':      lambda: grafico_crece(),
 'mapa_europa':  lambda: mapa_europa(),
 'sinagoga':     lambda: sinagoga(),
 'multitud':     lambda: multitud(),
 'sello_islamizing':  lambda: sello('ISLAMIZING', size=54),
 'sello_trend':       lambda: sello('TREND', size=62),
 'sello_territory':   lambda: sello('TERRITORY', size=50),
 'sello_closed':      lambda: sello('CLOSED', size=58),
 'sello_denied':      lambda: sello('DENIED', size=56),
 'sello_600':         lambda: sello('600+\nORGANISATIONS', size=42),
}


if __name__ == '__main__':
    hechas = []
    for n, fn in PIEZAS.items():
        im = fn(); f = os.path.join(OUT, 'prop_%s.png' % n)
        im.save(f); hechas.append((n, im))
        print('%-18s %4dx%-4d' % (n, im.width, im.height))
    if '--hoja' in sys.argv:
        cols = 5; rows = (len(hechas)+cols-1)//cols; cw = ch = 240
        h = Image.new('RGB', (cols*cw, rows*ch), (36, 30, 24))
        for i, (n, im) in enumerate(hechas):
            k = min((cw-24)/im.width, (ch-24)/im.height)
            t = im.resize((max(1, int(im.width*k)), max(1, int(im.height*k))), Image.LANCZOS)
            h.paste(t, ((i % cols)*cw+(cw-t.width)//2, (i//cols)*ch+(ch-t.height)//2), t)
        q = os.path.join(AQUI, '_hoja_props.jpg'); h.save(q, quality=90)
        print('hoja ->', q)
