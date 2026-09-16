# -*- coding: utf-8 -*-
"""Miniaturas 9:16 de la serie S13 («FOUR LINES»). 0 creditos: todo render local.

    python miniatura.py        ->  publicar/miniaturas/0N_<slug>.jpg (1080x1920, < 2 MB) + _qc_miniaturas.jpg

El diseño es el de la S12, que Agustin aprobo (y que salio de rechazar la primera version de la S02,
*"TIENE QUE SER ENFOCADO EN QUE HAGAN CLICK"*): fondo oscuro, la MISMA pregunta del titulo enorme arriba,
la cifra en rojo, un objeto grande con halo claro y un circulo rojo donde tiene que ir el ojo.

Lo que cambia en la S13:
  - **Dos banderas** cuando la pieza habla de dos paises (Ucrania y Rusia; Venezuela y EE. UU.; Taiwan y
    China). Regla de Agustin del 14-sep: si el video habla de un pais, su bandera va SIEMPRE. Van como
    fichas arriba, una a cada lado, sin tocar la pregunta.
  - Las fichas de bandera son todas del mismo molde (`arte/props_s13.py`): mezclar la bandera de mastil
    del indice con la de ficha en la misma portada se veia como dos series distintas.

Se revisa a **216 px de ancho**, que es lo que mide en la grilla del canal.
"""
import json, os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
PROD = os.path.join(RAIZ, 'produccion')
sys.path.insert(0, PROD)
from PIL import Image, ImageDraw, ImageFilter
from props import OCRE, ROJO, FONTC
import compo

W, H = 1080, 1920
FICHA = json.load(open(os.path.join(AQUI, 'shorts', 'serie.json'), encoding='utf-8'))
OUT = os.path.join(AQUI, 'publicar', 'miniaturas'); os.makedirs(OUT, exist_ok=True)
NEGRO = (18, 16, 14)
CREMA = (247, 241, 226)


class _C:
    base = os.path.join(AQUI, 'shorts', '01_refineria')


def prop(nombre):
    for b in compo._dirs_props(_C):
        f = os.path.join(b, 'prop_%s.png' % nombre)
        if os.path.exists(f): return Image.open(f).convert('RGBA')
    raise SystemExit('falta el prop: ' + nombre)


def halo(im, r=20, color=CREMA, fuerza=235):
    g = im.split()[3]
    for _ in range(max(1, r // 5)): g = g.filter(ImageFilter.MaxFilter(9))
    g = g.filter(ImageFilter.GaussianBlur(r * 0.5)).point(lambda v: min(fuerza, int(v * 2.0)))
    cap = Image.new('RGBA', im.size, color + (0,)); cap.putalpha(g)
    out = Image.new('RGBA', im.size, (0, 0, 0, 0))
    out.alpha_composite(cap); out.alpha_composite(im)
    return out


def texto_duro(d, xy, txt, font, fill, borde=NEGRO, gr=10, anchor='mm'):
    x, y = xy
    paso = max(2, gr // 3)
    for dx in range(-gr, gr + 1, paso):
        for dy in range(-gr, gr + 1, paso):
            if dx or dy: d.text((x + dx, y + dy), txt, fill=borde + (255,), font=font, anchor=anchor)
    d.text((x, y), txt, fill=fill + (255,), font=font, anchor=anchor)


def fondo():
    mad = os.path.join(PROD, 'assets', 'madera_1920.png')
    if os.path.exists(mad):
        t = Image.open(mad).convert('RGBA')
        base = Image.new('RGBA', (W, H))
        for y in range(0, H, t.height):
            for x in range(0, W, t.width): base.alpha_composite(t, (x, y))
    else:
        base = Image.new('RGBA', (W, H), (76, 52, 36, 255))
    base.alpha_composite(Image.new('RGBA', (W, H), NEGRO + (185,)))
    v = Image.new('L', (W, H), 0)
    ImageDraw.Draw(v).ellipse([-280, 140, W + 280, H - 140], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(230))
    return Image.composite(base, Image.new('RGBA', (W, H), NEGRO + (255,)), v)


def una(P):
    D = P['miniatura']
    im = fondo(); d = ImageDraw.Draw(im)

    # ---- banderas arriba: una a la izquierda, la otra (si hay) a la derecha
    bans = D.get('banderas') or []
    ANCHO_BAN = 250 if len(bans) > 1 else 270
    for i, b in enumerate(bans):
        fl = prop(b)
        fl = fl.resize((ANCHO_BAN, max(1, int(fl.height * ANCHO_BAN / fl.width))), Image.LANCZOS)
        fl = halo(fl, 16).rotate(-4 if i == 0 else 4, resample=Image.BICUBIC, expand=True)
        x = 46 if i == 0 else W - fl.width - 46
        im.alpha_composite(fl, (x, 52))

    # ---- la pregunta del titulo
    y = 300 + (70 if bans else 0)
    for ln in D['pregunta']:
        f = FONTC(168)
        while d.textbbox((0, 0), ln, font=f)[2] > W - 110: f = FONTC(f.size - 5)
        texto_duro(d, (W // 2, y), ln, f, CREMA, gr=12)
        y += int(f.size * 1.10)
    y_libre = y + int(FONTC(168).size * 0.10)

    # ---- la cifra en rojo
    cif = str(D.get('cifra', '')).strip()
    if cif:
        f = FONTC(150)
        while d.textbbox((0, 0), cif, font=f)[2] > W - 260: f = FONTC(f.size - 5)
        texto_duro(d, (W // 2, y_libre + f.size * 0.62), cif, f, ROJO, gr=12)
        y_libre += int(f.size * 1.30)

    # ---- el objeto, entero y con margen, en la caja que queda
    ob = prop(D['objeto'])
    CAJA_ALTO = (H - 210) - (y_libre + 40)
    k = min((W - 120) / ob.width, CAJA_ALTO / ob.height)
    ob = ob.resize((max(1, int(ob.width * k)), max(1, int(ob.height * k))), Image.LANCZOS)
    ob = halo(ob, 22).rotate(-3, resample=Image.BICUBIC, expand=True)
    ox = (W - ob.width) // 2
    oy = y_libre + 40 + max(0, (CAJA_ALTO - ob.height) // 2)
    im.alpha_composite(ob, (ox, oy))

    # ---- circulo rojo
    r = int(min(ob.width, ob.height) * D.get('circulo_r', 0.30))
    cx = ox + int(ob.width * D.get('circulo_x', 0.66))
    cy = oy + int(ob.height * D.get('circulo_y', 0.34))
    for gr in (0, 1, 2):
        d.ellipse([cx - r - gr, cy - r - gr, cx + r + gr, cy + r + gr], outline=ROJO + (255,), width=11)

    # ---- sello de serie
    texto_duro(d, (W // 2, H - 120), 'FOUR LINES · PART %d OF %d' % (P['n'], FICHA['piezas']),
               FONTC(58), OCRE, gr=8)
    return im.convert('RGB')


def main():
    hechas = []
    for P in FICHA['shorts']:
        im = una(P)
        f = os.path.join(OUT, '%s.jpg' % P['dir'])
        im.save(f, quality=90, optimize=True)
        assert os.path.getsize(f) < 2e6, '%s pesa mas de 2 MB' % f
        hechas.append((f, im))
        print('  %s  %.2f MB' % (f, os.path.getsize(f) / 1e6))
    cw = 216; ch = int(cw * H / W)
    q = Image.new('RGB', (cw * len(hechas) + 20 * (len(hechas) + 1), ch + 40), (26, 24, 22))
    for i, (_, im) in enumerate(hechas):
        q.paste(im.resize((cw, ch), Image.LANCZOS), (20 + i * (cw + 20), 20))
    g = os.path.join(AQUI, '_qc_miniaturas.jpg'); q.save(g, quality=92)
    big = Image.new('RGB', (540 * len(hechas), 960), (26, 24, 22))
    for i, (_, im) in enumerate(hechas):
        big.paste(im.resize((540, 960), Image.LANCZOS), (i * 540, 0))
    big.save(os.path.join(AQUI, '_qc_miniaturas_540.jpg'), quality=90)
    print('control a 216 px ->', g)


if __name__ == '__main__':
    main()
