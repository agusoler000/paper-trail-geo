# -*- coding: utf-8 -*-
"""Miniaturas candidatas v2 para los largos 01-05 (2026-09-13). 0 creditos: todo render local.

    python miniaturas_v2.py   -> out/miniaturas_v2/miniatura_0N_v2.png + _hoja_v2.jpg (actual vs. nueva, a 320 px)

Esto es una PROPUESTA del asistente, no una regla del canal (`CANAL.md` §7.2 y `STUDIO_ARREGLOS_2026-09-13.md` §5.4).
Sale de la evidencia externa (`_anexo_evidencia_titulos_2026-09-13.md` §4): las miniaturas que rinden en el nicho tienen
2-3 elementos — una cara reconocible del protagonista, el mapa con la zona en disputa marcada y dos o tres palabras —
y nada de sello de marca ni bandas de texto chico. Se mantiene el papel, la paleta y el elenco del canal.
"""
import os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..'))
sys.path.insert(0, os.path.join(RAIZ, 'produccion')); sys.path.insert(0, AQUI)
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import marca as MK
import props as PR

A = os.path.join(RAIZ, 'produccion', 'assets')
S01 = os.path.join(RAIZ, 'videos', 'S01_11s', 'arte', 'assets')
EP05 = os.path.join(RAIZ, 'videos', '05_11s', 'arte', 'assets')
OUT = os.path.join(AQUI, 'out', 'miniaturas_v2'); os.makedirs(OUT, exist_ok=True)
W, H = 1280, 720
ROJO, TINTA, PAPEL, OCRE = MK.ROJO, MK.TINTA, MK.PAPEL, MK.OCRE


def bbox_alpha(layer):
    a = layer.split()[3].point(lambda v: 255 if v > 40 else 0)
    return a.getbbox()


def cover(base, layer=None, foco=None, pad=1.6, min_frac=0.55, zx=0.5, zy=0.5):
    """Recorta la hoja en 16:9 alrededor de la zona (bbox del layer o `foco` en fracciones) y la escala a 1280x720.
    Devuelve (fondo RGBA, layer recortado o None)."""
    bw, bh = base.size
    if layer is not None and bbox_alpha(layer):
        x0, y0, x1, y1 = bbox_alpha(layer)
    elif foco:
        fx, fy, fw = foco; x0, y0, x1, y1 = (fx-fw/2)*bw, (fy-fw*9/32)*bh, (fx+fw/2)*bw, (fy+fw*9/32)*bh
    else:
        x0, y0, x1, y1 = 0, 0, bw, bh
    cx, cy = (x0+x1)/2, (y0+y1)/2
    cw = max((x1-x0)*pad, bw*min_frac); ch = cw*9/16
    if ch > bh: ch = bh; cw = ch*16/9
    if cw > bw: cw = bw; ch = cw*9/16
    L = min(max(0, cx-cw*zx), bw-cw); T = min(max(0, cy-ch*zy), bh-ch)   # zx: en que fraccion del cuadro cae la zona (la cara va a la derecha)
    box = (int(L), int(T), int(L+cw), int(T+ch))
    f = base.convert('RGBA').crop(box).resize((W, H), Image.LANCZOS)
    l = layer.crop(box).resize((W, H), Image.LANCZOS) if layer is not None else None
    return f, l


def zona_roja(im, layer, fuerza=190):
    """Pinta la zona en el rojo del canal (unico rojo del cuadro) con un borde suave."""
    if layer is None: return im
    a = layer.split()[3].point(lambda v: min(255, int(v*fuerza/255)))
    solid = Image.new('RGBA', (W, H), ROJO + (255,)); solid.putalpha(a)
    im.alpha_composite(solid)
    borde = a.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(1.2)).point(lambda v: min(255, v*3))
    tinta = Image.new('RGBA', (W, H), TINTA + (255,)); tinta.putalpha(borde)
    im.alpha_composite(tinta)
    return im


def cara(im, nombre, alto=880, dx=70, dy=40):
    """La figura del protagonista, grande, apoyada abajo y sangrando por el borde inferior."""
    p = MK.personaje(nombre, alto)
    x = W - p.width + dx
    MK.pegar(im, p, (x, dy), blur=16, alpha=150, off=(18, 24))
    return x


def texto(im, lineas, x=48, y=52, alto=176, maxw=0.56, rojo=-1):
    """Dos o tres palabras en tarjetas de papel, enormes; la ultima (o `rojo`) en rojo. Se mide con textbbox."""
    for i, t in enumerate(lineas):
        col = ROJO if i == (len(lineas)-1 if rojo < 0 else rojo) else TINTA
        s = alto
        while s > 70:
            c = PR.card(t, size=s, color=PAPEL, tcolor=col)
            if c.width <= W*maxw: break
            s -= 6
        c = c.rotate(-1.4 if i % 2 == 0 else 1.1, resample=Image.BICUBIC, expand=True)
        MK.pegar(im, c, (x, y), blur=14, alpha=150)
        y += c.height + 6
    return im


def fondo(base, layer=None, foco=None, **kw):
    f, l = cover(base, layer, foco, **kw)
    MK.vineta(f, color=(60, 45, 30), fuerza=0.55, blur=170, margen=170)
    return f, l


def m01():
    """Ep. 01 · Rusia en tierra. Cara: Putin. Zona: Rusia. Texto: GROUNDED. / NO SHOT."""
    base = Image.open(os.path.join(A, 'mapa_base.png')); rus = Image.open(os.path.join(A, 'mapa_rusia.png')).convert('RGBA')
    im, l = fondo(base, rus, pad=1.05, min_frac=0.9)
    im = zona_roja(im, l, fuerza=165)
    cara(im, '10_lider_b_v2.png', alto=900, dx=90, dy=30)
    texto(im, ['GROUNDED.', 'NO SHOT.'])
    return MK.acabado(im)


def m02():
    """Ep. 02 · AfD. Cara: Weidel. Zona: Sajonia-Anhalt. Texto: HALF A STATE. / AfD."""
    base = Image.open(os.path.join(A, 'mapa02_base.png')); sa = Image.open(os.path.join(A, 'mapa02_sa.png')).convert('RGBA')
    im, l = fondo(base, sa, pad=3.2, min_frac=0.34, zx=0.36, zy=0.62)
    im = zona_roja(im, l)
    cara(im, '12_weidel.png', alto=900, dx=80, dy=30)
    texto(im, ['HALF A STATE.', 'AfD.'])
    return MK.acabado(im)


def m03():
    """Ep. 03 · Kiev no es el objetivo. Cara: Putin. Zona: Donbas. Texto: THE REAL / TARGET."""
    base = Image.open(os.path.join(A, 'mapa03_base.png')); don = Image.open(os.path.join(A, 'mapa03_donbas.png')).convert('RGBA')
    im, l = fondo(base, don, pad=2.6, min_frac=0.42, zx=0.36)
    im = zona_roja(im, l)
    cara(im, '10_lider_b_v2.png', alto=900, dx=90, dy=30)
    texto(im, ['THE REAL', 'TARGET.'])
    return MK.acabado(im)


def m04():
    """Ep. 04 · Malvinas. Cara: Milei. Zona: las islas. Texto: GIVE THEM / BACK?"""
    base = Image.open(os.path.join(A, 'mapa04_base.png')); isl = Image.open(os.path.join(A, 'mapa04_islas.png')).convert('RGBA')
    im, l = fondo(base, isl, pad=2.0, min_frac=0.22, zx=0.30, zy=0.70)
    im = zona_roja(im, l)
    quien = '14_milei_v3.png' if os.path.exists(os.path.join(MK.E, '14_milei_v3.png')) else '14_milei.png'
    cara(im, quien, alto=780, dx=150, dy=110)
    texto(im, ['GIVE THEM', 'BACK?'], alto=160)
    return MK.acabado(im)


def m05():
    """Ep. 05 · 11-S. Cara: el busto de bin Laden de la serie. Fondo: la hoja de Eurasia. Texto: THE WRONG / WAR."""
    base = Image.open(os.path.join(EP05, 'mapa05_base.png'))
    im, _ = fondo(base, None, foco=(0.55, 0.5, 0.62), min_frac=0.62)
    bl = Image.open(os.path.join(S01, 'prop_bl_busto.png')).convert('RGBA')
    alto = 760; bl = bl.resize((int(bl.width*alto/bl.height), alto), Image.LANCZOS)
    MK.pegar(im, bl, (W-bl.width+40, H-alto+120), blur=16, alpha=150, off=(18, 24))
    texto(im, ['THE WRONG', 'WAR.'])
    return MK.acabado(im)


ACTUALES = {
    '01': os.path.join(AQUI, 'out', 'miniatura_01.png'),
    '02': os.path.join(AQUI, 'out', 'miniatura_02A.png'),
    '03': os.path.join(AQUI, 'out', 'miniatura_03A.png'),
    '04': os.path.join(AQUI, 'out', 'miniatura_04A.png'),
    '05': os.path.join(RAIZ, 'videos', '05_11s', 'publicar', 'miniatura_A.png'),
}

if __name__ == '__main__':
    hechas = {}
    for n, fn in (('01', m01), ('02', m02), ('03', m03), ('04', m04), ('05', m05)):
        im = fn(); p = os.path.join(OUT, 'miniatura_%s_v2.png' % n); im.convert('RGB').save(p); hechas[n] = p; print('ok', p)
    # hoja: actual vs nueva, al ancho real del feed (320 px)
    fila = 200; hoja = Image.new('RGB', (2*330+30, len(hechas)*(fila+10)+40), (24, 24, 24))
    d = ImageDraw.Draw(hoja); f = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 16)
    d.text((20, 8), 'ACTUAL', fill=(200, 200, 200), font=f); d.text((360, 8), 'NUEVA (propuesta)', fill=(200, 200, 200), font=f)
    for i, n in enumerate(sorted(hechas)):
        y = 34 + i*(fila+10)
        for j, p in enumerate((ACTUALES[n], hechas[n])):
            if os.path.exists(p):
                t = Image.open(p).convert('RGB').resize((320, 180), Image.LANCZOS); hoja.paste(t, (20+j*340, y))
        d.text((20, y+182), 'ep. ' + n, fill=(160, 160, 160), font=f)
    hoja.save(os.path.join(OUT, '_hoja_v2.jpg'), quality=92); print('hoja ->', os.path.join(OUT, '_hoja_v2.jpg'))
