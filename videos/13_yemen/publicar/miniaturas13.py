# -*- coding: utf-8 -*-
"""Ep. 13 · las TRES miniaturas de la prueba A/B de YouTube. 0 creditos: todo render local.

    python videos/13_yemen/publicar/miniaturas13.py

**Van las tres, no se elige una.** YouTube admite exactamente 3 variantes y las rota hasta quedarse
con la ganadora; cada una lleva **el mismo titular en mayusculas que su titulo** (formato que pidio
Agustin el 16-sep: `SUJETO EN MAYUSCULAS: oracion gancho #tags`). Titulo y miniatura se leen como una
sola cosa, asi que la miniatura repite el prefijo, no una frase distinta.

Reglas que cumplen las tres:
  - **Bandera de Yemen** arriba a la izquierda, con halo (Agustin, 14-sep: *cada vez que hablamos de
    un pais tiene que estar su bandera*). No esta en el catalogo: se dibuja aqui, 0 creditos.
  - Dos o tres palabras enormes, la ultima en rojo. Nada de bandas de texto chico ni sello de marca.
  - **Sin cifras**: las tres del titulo ya cargan bastante y la pregunta tiene que leerse a 216 px,
    que es como se ve en la grilla.
  - Fondo: la hoja del episodio recortada sobre el estrecho, con Perim marcado.
"""
import os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
EPI = os.path.abspath(os.path.join(AQUI, '..'))
RAIZ = os.path.abspath(os.path.join(EPI, '..', '..'))
sys.path.insert(0, os.path.join(RAIZ, 'produccion'))
sys.path.insert(0, os.path.join(RAIZ, 'canal'))
from PIL import Image, ImageDraw
import marca as MK
import miniaturas_v2 as MV2
import props as PR

ARTE = os.path.join(EPI, 'arte', 'assets')
OUT = AQUI
W, H = 1280, 720


def bandera_yemen(w=150):
    """Rojo, blanco y negro en tres franjas. No esta en el catalogo (solo hay ar/es/fr/uk/us/rusa)."""
    h = int(w * 0.66)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, c in enumerate(((206, 17, 38), (245, 242, 235), (30, 28, 26))):
        d.rectangle([0, h * i / 3.0, w, h * (i + 1) / 3.0], fill=c + (255,))
    d.rectangle([0, 0, w - 1, h - 1], outline=(30, 28, 26, 255), width=3)
    return im


def _base(zx=0.435, zy=0.905, pad=1.0, min_frac=0.155):
    """La hoja del episodio recortada sobre el Bab el-Mandeb.

    El mundo es regional (31,5-58,5 E · 9,5-31 N) y el estrecho cae abajo a la izquierda: de ahi
    `zx`/`zy`. `min_frac` chico = plano cerrado, que es lo que pide una miniatura."""
    base = Image.open(os.path.join(ARTE, 'mundo_yemen.png'))
    im, _ = MV2.fondo(base, None, foco=(zx, zy, min_frac), min_frac=min_frac, zx=zx, zy=zy, pad=pad)
    return im


def _chip_bandera(im):
    b = bandera_yemen(168)
    MK.pegar(im, b, (44, 44), blur=18, alpha=170, off=(10, 12))
    return im


def m13_a():
    """Variante 1 · el hecho. Titulo: "YEMEN IN CRISIS: The Houthis just took the Red Sea gate..." """
    im = _base()
    MV2.texto(im, ['YEMEN', 'IN CRISIS'], x=48, y=250, alto=186, maxw=0.62)
    return MK.acabado(_chip_bandera(im))


def m13_b():
    """Variante 2 · el precio. Titulo: "RED SEA SHUT DOWN: Yemen's coast fell and oil jumped..." """
    im = _base(zx=0.47, zy=0.86, min_frac=0.20)
    bar = Image.open(os.path.join(ARTE, 'p13_tanquero.png')).convert('RGBA')
    alto = 300
    bar = bar.resize((int(bar.width * alto / bar.height), alto), Image.LANCZOS)
    MK.pegar(im, bar, (W - bar.width - 30, H - alto - 40), blur=16, alpha=150, off=(16, 20))
    MV2.texto(im, ['RED SEA', 'SHUT DOWN'], x=48, y=250, alto=186, maxw=0.62)
    return MK.acabado(_chip_bandera(im))


def m13_c():
    """Variante 3 · el fracaso. Titulo: "YEMEN COLLAPSES: Eleven years of bombing ended..." """
    im = _base(zx=0.428, zy=0.918, min_frac=0.115)
    faro = Image.open(os.path.join(ARTE, 'p13_faro.png')).convert('RGBA')
    alto = 360
    faro = faro.resize((int(faro.width * alto / faro.height), alto), Image.LANCZOS)
    MK.pegar(im, faro, (W - faro.width - 90, H - alto - 60), blur=16, alpha=150, off=(16, 20))
    MV2.texto(im, ['YEMEN', 'COLLAPSES'], x=48, y=250, alto=186, maxw=0.62)
    return MK.acabado(_chip_bandera(im))


if __name__ == '__main__':
    hechas = []
    for n, fn in (('1_crisis', m13_a), ('2_redsea', m13_b), ('3_collapse', m13_c)):
        im = fn()
        p = os.path.join(OUT, 'miniatura_%s.png' % n)
        im.convert('RGB').save(p)
        hechas.append((n, p))
        print('  ok', os.path.basename(p))
    # hoja de las tres al ancho real del feed (320 px): asi se ve si la pregunta se lee
    ancho = 320
    alto = int(ancho * H / W)
    hoja = Image.new('RGB', (ancho * 3 + 40, alto + 20), (24, 24, 24))
    for i, (n, p) in enumerate(hechas):
        hoja.paste(Image.open(p).resize((ancho, alto), Image.LANCZOS), (10 + i * (ancho + 10), 10))
    hoja.save(os.path.join(EPI, '_miniaturas.jpg'), quality=92)
    print('  hoja -> _miniaturas.jpg  (a 320 px, como se ven en la grilla)')
