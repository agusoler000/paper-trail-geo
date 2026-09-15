# -*- coding: utf-8 -*-
"""Miniaturas 9:16 de la serie S10. 0 creditos: todo render local.

    python miniatura.py           ->  publicar/miniaturas/0N_<slug>.jpg (1080x1920) + _qc_miniaturas.jpg
    python miniatura.py 2         ->  solo la pieza 2

Hereda las cuatro decisiones de la version que Agustin aprobo en la S02, que salieron de que
rechazara la primera (*"LAS MINIATURAS SIGUEN SIENDO HORRIBLES... TIENE QUE SER ENFOCADO EN QUE
HAGAN CLICK"*):

  1. **Fondo oscuro** (madera oscurecida + viñeta dura). Una hoja clara no existe en un feed.
  2. **Un objeto grande** con halo claro que lo separa del fondo. Tamano = presencia.
  3. **Una jerarquia**: la pregunta arriba, grande; la cifra en rojo; nada mas.
  4. **Un circulo rojo** sobre lo que importa: el recurso mas viejo y mas efectivo.

**Lo propio de esta serie** (regla del 2026-09-14, `canal/CANAL.md` §7.1): la miniatura lleva **la
MISMA pregunta que el titulo**, en dos o tres palabras enormes. Titulo y miniatura se leen como una
sola cosa; si el titulo pregunta y la miniatura afirma, se anulan.

**La bandera del pais va SIEMPRE** (regla de Agustin, 2026-09-14, `canal/CANAL.md` §7.1): a 216 px
dice de que se trata antes de que nadie lea una palabra, y encadena las piezas del mismo pais. Va
como chip arriba a la izquierda, con halo, sin tocar la pregunta — que va centrada mas abajo. Se
controla con `miniatura.bandera` en `serie.json`.

**Los objetos de papel entran ENTEROS, con margen** (leccion del S05): una cara cortada sigue siendo
una cara, pero un documento sangrado por el borde pierde justo la palabra que lo explicaba.

Se revisa a **216 px de ancho**, que es lo que mide en la grilla del canal.
"""
import json, os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
PROD = os.path.join(RAIZ, 'produccion')
sys.path.insert(0, PROD)
from PIL import Image, ImageDraw, ImageFilter
from props import TINTA, PAPEL, OCRE, ROJO, FONTC

W, H = 1080, 1920
ARTE = os.path.join(AQUI, 'arte', 'assets')
S05A = os.path.join(RAIZ, 'videos', 'S05_mapa_alianzas', 'arte', 'assets')
S01A = os.path.join(RAIZ, 'videos', 'S01_11s', 'arte', 'assets')
FICHA = json.load(open(os.path.join(AQUI, 'shorts', 'serie.json'), encoding='utf-8'))
OUT = os.path.join(AQUI, 'publicar', 'miniaturas'); os.makedirs(OUT, exist_ok=True)

NEGRO = (18, 16, 14)
CREMA = (247, 241, 226)


def prop(nombre):
    for base in (ARTE, S05A, S01A, os.path.join(PROD, 'assets')):
        f = os.path.join(base, 'prop_%s.png' % nombre)
        if os.path.exists(f): return Image.open(f).convert('RGBA')
    raise SystemExit('falta el prop: ' + nombre)


def halo(im, r=20, color=CREMA, fuerza=235):
    """Contorno claro alrededor de una figura: es lo que la separa de un fondo oscuro."""
    g = im.split()[3]
    for _ in range(max(1, r//5)): g = g.filter(ImageFilter.MaxFilter(9))
    g = g.filter(ImageFilter.GaussianBlur(r*0.5)).point(lambda v: min(fuerza, int(v*2.0)))
    cap = Image.new('RGBA', im.size, color+(0,)); cap.putalpha(g)
    out = Image.new('RGBA', im.size, (0, 0, 0, 0))
    out.alpha_composite(cap); out.alpha_composite(im)
    return out


def texto_duro(d, xy, txt, font, fill, borde=NEGRO, gr=10, anchor='mm'):
    """Texto con reborde grueso: sobre una figura o una viñeta sigue legible."""
    x, y = xy
    paso = max(2, gr//3)
    for dx in range(-gr, gr+1, paso):
        for dy in range(-gr, gr+1, paso):
            if dx or dy: d.text((x+dx, y+dy), txt, fill=borde+(255,), font=font, anchor=anchor)
    d.text((x, y), txt, fill=fill+(255,), font=font, anchor=anchor)


def fondo():
    mad = os.path.join(PROD, 'assets', 'madera_1920.png')
    if os.path.exists(mad):
        t = Image.open(mad).convert('RGBA')
        base = Image.new('RGBA', (W, H))
        for y in range(0, H, t.height):
            for x in range(0, W, t.width): base.alpha_composite(t, (x, y))
    else:
        base = Image.new('RGBA', (W, H), (76, 52, 36, 255))
    base.alpha_composite(Image.new('RGBA', (W, H), NEGRO+(185,)))
    v = Image.new('L', (W, H), 0)
    ImageDraw.Draw(v).ellipse([-280, 140, W+280, H-140], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(230))
    return Image.composite(base, Image.new('RGBA', (W, H), NEGRO+(255,)), v)


def una(P):
    D = P['miniatura']
    im = fondo(); d = ImageDraw.Draw(im)

    # ---- ORDEN DEL LAYOUT: bandera -> pregunta -> cifra -> y el objeto en lo que QUEDA.
    # En la primera version el objeto se colocaba con una formula propia
    # (`H - alto - 300 + (900-alto)//3`) que no sabia nada del texto, y con un objeto bajito subia
    # hasta pisar la cifra: en la pieza 3 «£8M A DAY» quedaba escrito ENCIMA del hotel e ilegible.
    # Ahora el texto se dibuja primero, deja una `y_libre`, y el objeto se escala a la caja que
    # sobra. Es imposible que se solapen.

    # ---- la bandera del pais, arriba a la izquierda. Regla de Agustin del 14-sep.
    ban = D.get('bandera')
    if ban:
        fl = prop(ban)
        ANCHO_BAN = 260
        fl = fl.resize((ANCHO_BAN, max(1, int(fl.height*ANCHO_BAN/fl.width))), Image.LANCZOS)
        fl = halo(fl, 16).rotate(-4, resample=Image.BICUBIC, expand=True)
        im.alpha_composite(fl, (46, 52))

    # ---- la pregunta, arriba, en dos lineas. Es la MISMA del titulo.
    lineas = D['pregunta']
    y = 300 + (70 if ban else 0)
    for ln in lineas:
        f = FONTC(168)
        while d.textbbox((0, 0), ln, font=f)[2] > W-110: f = FONTC(f.size-5)
        texto_duro(d, (W//2, y), ln, f, CREMA, gr=12)
        y += int(f.size*1.10)
    y_libre = y + int(FONTC(168).size*0.10)

    # ---- la cifra en rojo, entre la pregunta y el objeto
    cif = str(D.get('cifra', '')).strip()
    if cif:
        f = FONTC(150)
        while d.textbbox((0, 0), cif, font=f)[2] > W-260: f = FONTC(f.size-5)
        texto_duro(d, (W//2, y_libre+f.size*0.62), cif, f, ROJO, gr=12)
        y_libre += int(f.size*1.30)

    # ---- el objeto grande, entero y con margen, en la caja que queda hasta el sello de serie
    ob = prop(D['objeto'])
    CAJA_ALTO = (H-210) - (y_libre+40)
    k = min((W-120)/ob.width, CAJA_ALTO/ob.height)
    ob = ob.resize((max(1, int(ob.width*k)), max(1, int(ob.height*k))), Image.LANCZOS)
    ob = halo(ob, 22).rotate(-3, resample=Image.BICUBIC, expand=True)
    ox = (W-ob.width)//2
    oy = y_libre + 40 + max(0, (CAJA_ALTO-ob.height)//2)
    im.alpha_composite(ob, (ox, oy))

    # ---- circulo rojo sobre el objeto: donde tiene que ir el ojo
    # `circulo_r` por pieza: con el radio fijo al 30 % del lado menor, en la sentencia el circulo
    # quedaba TAPANDO la fecha en vez de senalarla, y la fecha es el dato de la pieza.
    r = int(min(ob.width, ob.height)*D.get('circulo_r', 0.30))
    cx = ox + int(ob.width*D.get('circulo_x', 0.66))
    cy = oy + int(ob.height*D.get('circulo_y', 0.34))
    for gr in (0, 1, 2):
        d.ellipse([cx-r-gr, cy-r-gr, cx+r+gr, cy+r+gr], outline=ROJO+(255,), width=11)

    # ---- sello de serie abajo, igual en las tres
    f = FONTC(58)
    texto_duro(d, (W//2, H-120), 'PART %d OF %d' % (P['n'], FICHA['piezas']), f, OCRE, gr=8)
    return im.convert('RGB')


def main():
    solo = int(sys.argv[1]) if len(sys.argv) > 1 else None
    hechas = []
    for P in FICHA['shorts']:
        if solo and P['n'] != solo: continue
        im = una(P)
        slug = P['dir']
        f = os.path.join(OUT, '%s.jpg' % slug)
        im.save(f, quality=90, optimize=True)
        hechas.append((f, im))
        print('  %-20s %.2f MB' % (os.path.basename(f), os.path.getsize(f)/1e6))
    # hoja de control: a 216 px, que es como se ve en la grilla del canal
    if hechas:
        cw = 216; ch = int(cw*H/W)
        q = Image.new('RGB', (cw*len(hechas)+20*(len(hechas)+1), ch+40), (26, 24, 22))
        for i, (_, im) in enumerate(hechas):
            q.paste(im.resize((cw, ch), Image.LANCZOS), (20+i*(cw+20), 20))
        g = os.path.join(AQUI, '_qc_miniaturas.jpg'); q.save(g, quality=92)
        print('control a 216 px ->', g)


if __name__ == '__main__':
    main()
