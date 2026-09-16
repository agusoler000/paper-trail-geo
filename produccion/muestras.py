# -*- coding: utf-8 -*-
"""muestras.py - cuadros REALES de una pieza compuesta en los instantes que se piden (tiempo del AUDIO).

    python produccion/muestras.py videos/S13_cuatro_frentes --pieza 1 40.4:completely 44.0:quarter

`compo.py --hoja` muestrea 16 instantes repartidos a ojo, y ahi no caen las cosas que hay que comprobar:
si la refineria se apaga cuando la voz dice «completely», si el 50-50 aparece en «fifty». Esto renderiza
exactamente esos instantes. Los tiempos se pasan en segundos del AUDIO (los de `_palabras.json`) y se
corren a la escena restando `t_ini`, que es lo que `compo.build` recorta al principio.

Salida: `<pieza>/_qc/muestras.jpg`, una fila con cada cuadro rotulado con su tiempo y su etiqueta.
"""
import os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import compo
from PIL import Image, ImageDraw
import props as PR


def main():
    a = sys.argv[1:]
    if len(a) < 3 or '--pieza' not in a:
        print(__doc__); return
    pieza = int(a[a.index('--pieza') + 1])
    d = compo._resolver(a[0], pieza)
    pedidos = [x for x in a[1:] if x not in ('--pieza', str(pieza))]
    guion = os.path.join(d, 'guion_v.md')
    sc, info = compo.build(guion=guion, tiempos=os.path.join(d, 'audio', 'tiempos.json'),
                           formato='vertical', base=d, out=os.path.join(d, '_qc'), verbose=False)
    W, H = info['W'], info['H']
    w = 360; h = int(w * H / W)
    tira = Image.new('RGB', (w * len(pedidos), h + 40), (18, 17, 15))
    dr = ImageDraw.Draw(tira)
    for i, p in enumerate(pedidos):
        t_audio, _, etiqueta = p.partition(':')
        t = max(0.0, min(info['dur'] - 0.02, float(t_audio) - info['t_ini']))
        tira.paste(sc.render(t).convert('RGB').resize((w, h), Image.LANCZOS), (i * w, 40))
        dr.text((i * w + 8, 8), '%s s  %s' % (t_audio, etiqueta), fill=(255, 220, 120), font=PR.FONTC(24))
    out = os.path.join(d, '_qc', 'muestras.jpg')
    tira.save(out, quality=88)
    print('muestras ->', out)


if __name__ == '__main__':
    main()
