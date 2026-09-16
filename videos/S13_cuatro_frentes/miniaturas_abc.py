# -*- coding: utf-8 -*-
"""Miniaturas A/B/C de la S13 («FOUR LINES»), v2. 0 creditos.

    python miniaturas_abc.py  ->  publicar/miniaturas/0N_<slug>_{A,B,C}.jpg + _qc_miniaturas_abc_216.jpg / _540.jpg

**Pedido de Agustin (16-sep), sobre la v1:** *«En la de Rusia y Ucrania esta bien el WHO IS WINNING pero
deberia decir algo en referencia a la guerra: UCRANIA VS RUSIA o GUERRA DE UCRANIA. En la de Venezuela
tambien. En todas tiene que haber una referencia al o los paises implicados. Y tiene que ser una sentencia
chocante que a uno le llame la atencion y quiera ver el video.»*

Y la regla de siempre que la v1 no cumplio (memoria `feedback-titulos-y-miniaturas`, 14-sep): **tres
miniaturas por pieza**, renderizadas, con hoja de comparacion a 216 px.

Cada miniatura, de arriba abajo: banderas · LOS PAISES en texto · la frase chocante (lo mas grande) · un
dato en rojo · el objeto con su circulo · sello de la serie.

**Toda frase sale de `fuentes/referencia.md`** (regla 7). Se descartaron por exagerar: «ONE VOTE FROM
BEING STOPPED» (aunque el voto procesal hubiera salido al reves, la resolucion todavia tenia que aprobarse),
«RUSSIA IS RUNNING OUT OF DIESEL» (sin fuente) y «NO WARSHIPS NEEDED» (la Armada china sigue ahi, F16).
"""
import os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import miniatura as MI
from PIL import Image, ImageDraw
from props import OCRE, ROJO, FONTC

W, H = MI.W, MI.H
CREMA, NEGRO = MI.CREMA, MI.NEGRO

VARIANTES = {
 1: {'dir': '01_refineria', 'banderas': ['bandera_ua', 'bandera_rusia'], 'v': {
   'A': dict(pais='UKRAINE VS RUSSIA', grande=['WHO IS', 'WINNING?'], roja=['A REFINERY HIT', 'EVERY 3 DAYS'],
             objeto='refineria_off', circ=(0.90, 0.13, 0.17)),                       # F4
   'B': dict(pais='UKRAINE VS RUSSIA', grande=["RUSSIA'S FUEL", 'UNDER FIRE'], roja=['3 OF 6 TOP', 'PLANTS HIT'],
             objeto='refinerias_d12', circ=(0.50, 0.26, 0.19)),                      # F3
   'C': dict(pais='THE UKRAINE WAR', grande=['RUSSIA BANNED', 'DIESEL EXPORTS'], roja=['FIRST TIME EVER'],
             objeto='cisterna', circ=(0.37, 0.42, 0.30)),                            # F6
 }},
 2: {'dir': '02_voto', 'banderas': ['bandera_eeuu', 'bandera_ve'], 'v': {
   'A': dict(pais='USA VS VENEZUELA', grande=['A PRESIDENT,', 'CAPTURED'], roja=['CONGRESS NEVER', 'SAID YES'],
             objeto='capitolio_g', circ=(0.50, 0.30, 0.24)),                         # F7, F10
   'B': dict(pais='USA VS VENEZUELA', grande=['WHO', 'AUTHORIZED IT?'], roja=['NOT CONGRESS'],
             objeto='doc_memo', circ=(0.19, 0.885, 0.13)),                           # F10, F11
   'C': dict(pais='VENEZUELA', grande=['CONGRESS NEVER', 'AUTHORIZED IT'], roja=['51-50'],
             objeto='votos_b04', circ=(0.70, 0.24, 0.16)),                           # F10, F12
 }},
 3: {'dir': '03_fecha', 'banderas': ['bandera_china', 'bandera_tw'], 'v': {
   'A': dict(pais='CHINA VS TAIWAN', grande=["CHINA'S NEW", 'WEAPON: A DATE'], roja=['NO SHOT FIRED'],
             objeto='calendario_24', circ=(0.50, 0.63, 0.30)),                       # F13, F14 (tesis)
   'B': dict(pais='CHINA VS TAIWAN', grande=['A SUMMIT', 'OR WEAPONS?'], roja=["BEIJING'S WARNING"],
             objeto='balanza_d06', circ=(0.14, 0.56, 0.16)),                         # F14
   'C': dict(pais='TAIWAN', grande=['CHINA AT THE', 'BACK DOOR'], roja=['COAST GUARD:', 'FIRST TIME EVER'],
             objeto='guardacostas', circ=(0.72, 0.66, 0.32)),                        # F16
 }},
 4: {'dir': '04_subasta', 'banderas': ['bandera_reino'], 'v': {
   'A': dict(pais="BRITAIN'S DEBT", grande=['£11.8 BILLION', 'IN ONE MONTH'], roja=['JUST ON INTEREST'],
             objeto='pilas_d12', circ=(0.73, 0.855, 0.17)),                          # F20
   'B': dict(pais='UK ECONOMY', grande=['WHO REALLY', 'DECIDES?'], roja=['NOT THE CHANCELLOR'],
             objeto='martillo_subasta', circ=(0.36, 0.36, 0.26)),                    # F17 (tesis)
   'C': dict(pais='BRITAIN', grande=['WORST RATE', 'SINCE 1998'], roja=['5.82%'],
             objeto='gilt_30', circ=(0.70, 0.66, 0.22)),                             # F17
 }},
}


def _linea(d, y, txt, tam, color, margen, gr):
    f = FONTC(tam)
    while d.textbbox((0, 0), txt, font=f)[2] > W - margen: f = FONTC(f.size - 4)
    MI.texto_duro(d, (W // 2, y + f.size // 2), txt, f, color, gr=gr)
    return y + int(f.size * 1.06)


def una(n, banderas, V):
    im = MI.fondo(); d = ImageDraw.Draw(im)
    ANCHO = 215 if len(banderas) > 1 else 240
    for i, b in enumerate(banderas):
        fl = MI.prop(b)
        fl = fl.resize((ANCHO, max(1, int(fl.height * ANCHO / fl.width))), Image.LANCZOS)
        fl = MI.halo(fl, 14).rotate(-4 if i == 0 else 4, resample=Image.BICUBIC, expand=True)
        im.alpha_composite(fl, (40 if i == 0 else W - fl.width - 40, 40))
    y = 262
    y = _linea(d, y, V['pais'], 118, OCRE, 90, 10) + 22             # los paises
    for ln in V['grande']:                                          # la frase
        y = _linea(d, y, ln, 150, CREMA, 80, 12)
    y += 16
    for ln in V['roja']:                                            # el dato
        y = _linea(d, y, ln, 118, ROJO, 120, 11)
    y_libre = y + 10
    ob = MI.prop(V['objeto'])
    caja = (H - 190) - (y_libre + 30)
    k = min((W - 140) / ob.width, caja / ob.height)
    ob = ob.resize((max(1, int(ob.width * k)), max(1, int(ob.height * k))), Image.LANCZOS)
    ob = MI.halo(ob, 20).rotate(-3, resample=Image.BICUBIC, expand=True)
    ox = (W - ob.width) // 2
    oy = y_libre + 30 + max(0, (caja - ob.height) // 2)
    im.alpha_composite(ob, (ox, oy))
    cxf, cyf, rf = V['circ']
    r = int(min(ob.width, ob.height) * rf)
    cx = ox + int(ob.width * cxf); cy = oy + int(ob.height * cyf)
    for g in (0, 1, 2):
        d.ellipse([cx - r - g, cy - r - g, cx + r + g, cy + r + g], outline=ROJO + (255,), width=11)
    MI.texto_duro(d, (W // 2, H - 100), 'FOUR LINES · PART %d OF 4' % n, FONTC(52), OCRE, gr=7)
    return im.convert('RGB')


def main():
    out = os.path.join(AQUI, 'publicar', 'miniaturas')
    hechas = {}
    for n, P in VARIANTES.items():
        for letra, V in P['v'].items():
            im = una(n, P['banderas'], V)
            f = os.path.join(out, '%s_%s.jpg' % (P['dir'], letra))
            im.save(f, quality=90, optimize=True)
            assert os.path.getsize(f) < 2e6
            hechas[(n, letra)] = im
            print('  %s  %.2f MB' % (f, os.path.getsize(f) / 1e6))
    for ancho, nombre in ((216, '_qc_miniaturas_abc_216.jpg'), (360, '_qc_miniaturas_abc_360.jpg')):
        alto = int(ancho * H / W); pad = 16
        q = Image.new('RGB', (3 * ancho + 4 * pad, 4 * (alto + 34) + pad), (26, 24, 22))
        dq = ImageDraw.Draw(q)
        for n in range(1, 5):
            for j, letra in enumerate('ABC'):
                x = pad + j * (ancho + pad); y = pad + (n - 1) * (alto + 34)
                dq.text((x, y), 'PIEZA %d · %s' % (n, letra), fill=(255, 220, 120), font=FONTC(20))
                q.paste(hechas[(n, letra)].resize((ancho, alto), Image.LANCZOS), (x, y + 26))
        q.save(os.path.join(AQUI, nombre), quality=90)
        print('hoja ->', os.path.join(AQUI, nombre))


if __name__ == '__main__':
    main()
