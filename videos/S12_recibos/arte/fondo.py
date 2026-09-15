# -*- coding: utf-8 -*-
"""Fondo del short S03: pared de papel arriba, mesa de madera abajo, vineta. 1920x1080, 0 creditos.

    cd videos/S03_aviso_oct7/arte && python fondo.py   ->  assets/fondo.png

Copia literal del de la serie S02 (`videos/S02_ia_riesgo/arte/fondo.py`): la mesa, la hoja de trabajo
y el vestido funcionan igual y no hay motivo para rehacerlos. Lo unico propio del short es lo que cae
ENCIMA (`props_s03.py`).

**Dos medidas cambiadas respecto de la S02, y las dos salieron de mirar cuadros reales:**

1. `MESA_Y` **420** (era 300). El plano WALL mide 738x415 y con la mesa a 300 su tercio inferior caia
   sobre la madera: las tarjetas grandes quedaban con una franja de mesa debajo, como flotando.
2. La hoja de trabajo mide **1150x648 y empieza en x=-14** (era 1010x820 en x=34). El plano CTR llega
   hasta x=1116 y la hoja terminaba en 1044: en el borde derecho de todos los planos de mesa se veia
   una tira de madera. Ahora la hoja CONTIENE al plano entero.

El vestido de la mesa va horneado aca —regla y lapiz— y no como objetos de la escena: son cosas que
nunca se mueven y que si fueran objetos apareceran en el chequeo de encuadre sin aportar nada.
"""
import os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..', '..'))
sys.path.insert(0, os.path.join(RAIZ, 'produccion')); sys.path.insert(0, os.path.join(RAIZ, 'canal'))
from PIL import Image, ImageDraw
import marca as MK
from props import papel, TINTA, PAPEL, OCRE, GRIS, MADERA, BLANCO

W, H, MESA_Y = 1920, 1080, 420
OUT = os.path.join(AQUI, 'assets'); os.makedirs(OUT, exist_ok=True)


def hoja_trabajo(w=1150, h=648):
    """La hoja de trabajo del plano CTR: renglones y margen rojo. Sobre ella caen los props, que asi
    se leen sobre papel y no sobre madera oscura. Es el mismo recurso de la serie S01."""
    def f(d): d.rounded_rectangle([1, 1, w-2, h-2], radius=14, fill=255)
    p = papel((w, h), f, (214, 199, 166)); d = ImageDraw.Draw(p)
    d.rounded_rectangle([16, 16, w-17, h-17], radius=10, outline=TINTA+(210,), width=4)
    for y in range(96, h-40, 92): d.line([(44, y), (w-44, y)], fill=(158, 150, 130, 120), width=3)
    d.line([(128, 30), (128, h-30)], fill=(176, 86, 66, 150), width=3)
    return p


def regla(w=520, h=54):
    def f(d): d.rounded_rectangle([1, 1, w-2, h-2], radius=6, fill=255)
    p = papel((w, h), f, OCRE); d = ImageDraw.Draw(p)
    for x in range(20, w-16, 26):
        d.line([(x, 10), (x, 10+(20 if (x//26) % 5 == 0 else 12))], fill=TINTA+(200,), width=3)
    return p


def lapiz(w=300, h=26):
    def f(d):
        d.rounded_rectangle([1, 1, w-46, h-2], radius=5, fill=255)
        d.polygon([(w-46, 1), (w-2, h/2), (w-46, h-2)], fill=255)
    p = papel((w, h), f, (196, 150, 66)); d = ImageDraw.Draw(p)
    d.polygon([(w-22, h*0.28), (w-2, h/2), (w-22, h*0.72)], fill=TINTA+(255,))
    return p


if __name__ == '__main__':
    im = MK.tile(MK.papel_tx, (W, H))
    im.alpha_composite(MK.tablero(W, H, MESA_Y), (0, MESA_Y))
    ImageDraw.Draw(im).rectangle([0, MESA_Y-5, W, MESA_Y+7], fill=(58, 38, 26, 255))
    MK.pegar(im, hoja_trabajo().rotate(-0.4, resample=Image.BICUBIC, expand=True), (-14, MESA_Y+12),
             blur=18, alpha=115)
    MK.pegar(im, regla().rotate(1.1, resample=Image.BICUBIC, expand=True), (W-620, H-92), blur=14, alpha=100)
    MK.pegar(im, lapiz().rotate(-5.0, resample=Image.BICUBIC, expand=True), (W-330, H-150), blur=12, alpha=110)
    MK.vineta(im, color=(52, 40, 28), fuerza=0.52, blur=170, margen=180)
    im.convert('RGB').save(os.path.join(OUT, 'fondo.png'))
    print('fondo ->', os.path.join(OUT, 'fondo.png'), im.size)
