# -*- coding: utf-8 -*-
"""Miniatura 9:16 del short S11. 0 creditos, render local.

    python miniatura.py -> publicar/miniaturas/01_europa.jpg + _qc_miniatura.jpg

v3 (con feedback de vision): luna sin disco ni aro, mapa con mas contraste, flecha de % UNICA,
jerarquia clara (luna > cifra > pregunta > mapa de fondo).
"""
import json, os, sys, math
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
PROD = os.path.join(RAIZ, 'produccion')
sys.path.insert(0, PROD); sys.path.insert(0, os.path.join(RAIZ, 'canal'))
from PIL import Image, ImageDraw, ImageFilter
import marca as MK
from props import papel, TINTA, PAPEL, OCRE, ROJO, FONTC

W, H = 1080, 1920
ARTE = os.path.join(AQUI, 'arte', 'assets')
FICHA = json.load(open(os.path.join(AQUI, 'shorts', 'serie.json'), encoding='utf-8'))
P = FICHA['shorts'][0]
D = P['miniatura']
OUT = os.path.join(AQUI, 'publicar', 'miniaturas'); os.makedirs(OUT, exist_ok=True)

NEGRO = (24, 21, 18)
CREMA = (247, 241, 226)
ROJO_TX = (198, 54, 40)


def medir(d, txt, f):
    b = d.textbbox((0, 0), txt, font=f); return b[2]-b[0], b[3]-b[1]


def texto_duro(d, xy, txt, font, fill, borde=NEGRO, gr=9, anchor='mm'):
    x, y = xy
    paso = max(2, gr//3)
    for dx in range(-gr, gr+1, paso):
        for dy in range(-gr, gr+1, paso):
            if dx or dy: d.text((x+dx, y+dy), txt, fill=borde+(255,), font=font, anchor=anchor)
    d.text((x, y), txt, fill=fill+(255,), font=font, anchor=anchor)


def estrella(d, cx, cy, r, fill):
    pts = []
    for k in range(10):
        a = -math.pi/2 + k*math.pi/5
        rr = r if k % 2 == 0 else r*0.42
        pts.append((cx + rr*math.cos(a), cy + rr*math.sin(a)))
    d.polygon(pts, fill=fill+(255,))


def bandera_ue(w=220):
    h = int(w*0.66)
    def f(d): d.rounded_rectangle([1, 1, w-2, h-2], radius=8, fill=255)
    p = papel((w, h), f, (0, 51, 153)); d = ImageDraw.Draw(p)
    cx, cy, r = w/2, h/2, h*0.34
    for k in range(12):
        a = -math.pi/2 + k*math.pi/6
        estrella(d, cx + r*math.cos(a), cy + r*math.sin(a), h*0.052, (255, 204, 0))
    return p


def pct_flecha(txt, w=260):
    """Flecha roja limpia que sube + cartel blanco con la cifra, alineados."""
    h = int(w*1.15)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(0.38*w, h-12), (0.38*w, 0.36*h), (0.08*w, 0.36*h), (0.50*w, 0),
               (0.92*w, 0.36*h), (0.62*w, 0.36*h), (0.62*w, h-12)],
              fill=ROJO+(255,), outline=CREMA+(255,), width=5)
    bw, bh = int(0.72*w), int(0.22*h)
    d.rounded_rectangle([int((w-bw)/2), int(0.44*h), int((w-bw)/2)+bw, int(0.44*h)+bh],
                        radius=8, fill=(255, 255, 255, 255), outline=NEGRO+(255,), width=3)
    d.text((w/2, int(0.44*h)+bh/2), txt, fill=ROJO+(255,), font=FONTC(int(0.30*w)), anchor='mm')
    return im


def sombra(im, r=18, blur=18):
    a = im.split()[3]
    g = a.filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.GaussianBlur(blur))
    cap = Image.new('RGBA', im.size, (0, 0, 0, 200)); cap.putalpha(g)
    out = Image.new('RGBA', im.size, (0, 0, 0, 0))
    out.alpha_composite(cap); out.alpha_composite(im)
    return out


def una():
    # ---- fondo madera + vineta suave
    mad = os.path.join(PROD, 'assets', 'madera_1920.png')
    if os.path.exists(mad):
        t = Image.open(mad).convert('RGBA')
        base = Image.new('RGBA', (W, H))
        for y in range(0, H, t.height):
            for x in range(0, W, t.width): base.alpha_composite(t, (x, y))
    else:
        base = Image.new('RGBA', (W, H), (96, 70, 48, 255))
    v = Image.new('L', (W, H), 0)
    ImageDraw.Draw(v).ellipse([-320, -60, W+320, H+60], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(260))
    im = Image.composite(base, Image.new('RGBA', (W, H), (36, 28, 22, 255)), v)
    d = ImageDraw.Draw(im)

    # ---- mapa de Europa REAL, centrado, con marco de papel
    mapa = Image.open(os.path.join(ARTE, 'mapa_europa_real.png')).convert('RGBA')
    ANCHO = 1000
    mapa = mapa.resize((ANCHO, int(mapa.height*ANCHO/mapa.width)), Image.LANCZOS)
    b = 24
    hoja = Image.new('RGBA', (mapa.width+2*b, mapa.height+2*b), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hoja)
    hd.rounded_rectangle([0, 0, hoja.width-1, hoja.height-1], radius=18, fill=PAPEL+(255,))
    hd.rounded_rectangle([10, 10, hoja.width-11, hoja.height-11], radius=14, outline=TINTA+(70,), width=3)
    hoja.alpha_composite(mapa, (b, b))
    hoja = hoja.rotate(-2.0, resample=Image.BICUBIC, expand=True)
    sh = Image.new('RGBA', hoja.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([0, 0, hoja.width-1, hoja.height-1], radius=18, fill=(0, 0, 0, 190))
    sh = sh.filter(ImageFilter.GaussianBlur(20))
    mx, my = int((W-hoja.width)/2), 600
    im.alpha_composite(sh, (mx+10, my+14))
    im.alpha_composite(hoja, (mx, my))

    # ---- la media luna + estrella, AL CENTRO (sin sombra: la sombra la engordaba)
    luna = Image.open(os.path.join(ARTE, 'prop_media_luna.png')).convert('RGBA')
    ALTO = 270
    luna = luna.resize((max(1, int(luna.width*ALTO/luna.height)), ALTO), Image.LANCZOS)
    lx, ly = int(W/2 - luna.width/2), 1080
    sh = luna.split()[3].point(lambda v: min(v, 80)).filter(ImageFilter.GaussianBlur(6))
    sh_img = Image.new('RGBA', luna.size, (46, 32, 20, 255)); sh_img.putalpha(sh)
    im.alpha_composite(sh_img, (lx+9, ly+11))
    im.alpha_composite(luna, (lx, ly))

    # ---- bandera de la UE, arriba a la izquierda
    ue = bandera_ue(210).rotate(-6, resample=Image.BICUBIC, expand=True)
    MK.pegar(im, ue, (50, 600), blur=20, alpha=205)

    # ---- UN grafico de % exagerado, arriba a la derecha
    pf = pct_flecha('14%', 260).rotate(6, resample=Image.BICUBIC, expand=True)
    im.alpha_composite(pf, (790, 610))

    # ---- la cifra grande arriba
    cif = D['cifra']
    f = FONTC(230)
    while medir(d, cif, f)[0] > W-110: f = FONTC(f.size-6)
    tw, th = medir(d, cif, f)
    tira = papel((tw+110, th+100),
                 lambda dd: dd.rounded_rectangle([1, 1, tw+108, th+98], radius=16, fill=255), PAPEL)
    tira = tira.rotate(-1.4, resample=Image.BICUBIC, expand=True)
    tx, ty = (W-tira.width)//2, 76
    MK.pegar(im, tira, (tx, ty), blur=24, alpha=215)
    texto_duro(d, (W/2, ty+tira.height/2-4), cif, f, ROJO_TX, borde=(112, 30, 22), gr=6)

    # ---- la pregunta, crema con reborde, TODO del mismo color
    y = ty + tira.height + 56
    fp = FONTC(116)
    while max(medir(d, t, fp)[0] for t in D['palabras']) > W-40: fp = FONTC(fp.size-3)
    for i, t in enumerate(D['palabras']):
        texto_duro(d, (W/2, y+i*int(fp.size*1.02)), t, fp, CREMA, gr=10)

    # ---- marca PT abajo a la izquierda
    fn = FONTC(54); nw, nh = medir(d, 'PT', fn)
    bw, bh = nw+54, nh+38
    ficha = papel((bw, bh), lambda dd: dd.rounded_rectangle([1, 1, bw-2, bh-2], radius=10, fill=255), OCRE)
    bx, by = 48, H-bh-42
    im.alpha_composite(ficha, (bx, by))
    d.rounded_rectangle([bx+8, by+8, bx+bw-9, by+bh-9], radius=8, outline=TINTA+(255,), width=4)
    d.text((bx+bw/2, by+bh/2), 'PT', fill=TINTA+(255,), font=fn, anchor='mm')
    texto_duro(d, (bx+bw+22, by+bh/2), 'PAPER TRAIL', FONTC(46), OCRE, gr=6, anchor='lm')

    dst = os.path.join(OUT, '01_%s.jpg' % P['dir'].split('_', 1)[1])
    im.convert('RGB').save(dst, quality=92)
    return dst


if __name__ == '__main__':
    dst = una()
    print('%s  %.2f MB' % (os.path.basename(dst), os.path.getsize(dst)/1e6))
    g = Image.open(dst).convert('RGB')
    qc = Image.new('RGB', (216+40+540, 960), (24, 22, 20))
    qc.paste(g.resize((216, 384), Image.LANCZOS), (0, 0))
    qc.paste(g.resize((540, 960), Image.LANCZOS), (256, 0))
    f = os.path.join(AQUI, '_qc_miniatura.jpg'); qc.save(f, quality=92)
    print('control (216 px = grilla del canal) ->', f)
