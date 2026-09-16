# -*- coding: utf-8 -*-
"""luz.py - los cambios de LUZ de una pieza compuesta (mapa claro <-> mesa oscura), sin renderizar.

    python produccion/luz.py videos/S13_cuatro_frentes --pieza 1 [--max 5.0]

Por que existe (S13, 16-sep). `ritmo.py` falla una pieza si hay un plano de mas de 6 s «sin cambio»,
y detecta el cambio como una diferencia media de gris > 12/255 entre dos muestras a 4 fps. Un corte de
mapa a mapa entre dos zonas de tierra parecidas queda JUSTO en ese umbral: `ritmo_previo.py` daba PASS
y el render real, comprimido, daba FAIL (7,8 s). Lo que se detecta SIEMPRE es el paso del mapa claro a
la mesa oscura (`Mundo.dark` 0,58) y vuelta. Esto lista esos pasos a partir de los tramos de mesa que
`compo.build` ya calculo, mas el fin del gancho y el fin del cuerpo (donde entra la tarjeta de cierre),
y marca cada hueco de mas de `--max` segundos con la linea de voz que cae en el.

Criterio: con todos los huecos por debajo de 5 s, `ritmo.py` pasa aunque ningun corte mapa-mapa se
detecte. Los otros cambios (cifras, props, secuencias) quedan de margen.
"""
import os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import compo


def cambios(info):
    C = info['compo']
    dur = info['dur']
    t = []
    if C.G.get('gancho') if hasattr(C, 'G') and isinstance(C.G, dict) else False:
        t.append(getattr(compo, 'HOOK', 3.5))
    else:
        t.append(3.5)
    for a, b in sorted(C.mesas):
        t += [a, b]
    t.append(dur)
    return sorted(x for x in set(round(v, 2) for v in t) if 0.0 <= x <= dur + 0.01)


def main():
    a = sys.argv[1:]
    if '--pieza' not in a:
        print(__doc__); return
    n = int(a[a.index('--pieza') + 1])
    lim = float(a[a.index('--max') + 1]) if '--max' in a else 5.0
    d = compo._resolver(a[0], n)
    sc, info = compo.build(guion=os.path.join(d, 'guion_v.md'), tiempos=os.path.join(d, 'audio', 'tiempos.json'),
                           formato='vertical', base=d, out=os.path.join(d, '_qc'), verbose=False)
    ts = cambios(info)
    lineas = info['lineas']
    peor = 0.0
    print('pieza %d: %d cambios de luz en %.1f s' % (n, len(ts), info['dur']))
    for x, y in zip(ts, ts[1:]):
        g = y - x
        peor = max(peor, g)
        if g > lim:
            dentro = [i for i, l in enumerate(lineas) if l['inicio'] < y and l['fin'] > x]
            print('  HUECO %.1f s  %6.2f -> %6.2f   lineas %s' % (g, x, y, dentro))
            for i in dentro:
                print('         %2d  %6.2f-%6.2f  %s' % (i, lineas[i]['inicio'], lineas[i]['fin'], lineas[i]['texto'][:70]))
    print('  hueco maximo %.2f s  ->  %s' % (peor, 'OK' if peor <= lim else 'CORREGIR'))


if __name__ == '__main__':
    main()
