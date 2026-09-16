# -*- coding: utf-8 -*-
"""alternar.py - reparte cortes de LUZ (mesa oscura <-> mapa claro) para que ningun tramo pase de N s.

    python produccion/alternar.py videos/S13_cuatro_frentes --pieza 3 [--max 4.3] [--escribir]

Sin `--escribir` solo muestra lo que haria. Con `--escribir` agrega los verbos a `guion_v.md` (y deja
una copia `guion_v.md.bak`).

Como decide (ver `luz.py` para el por que):
  1. Compone la pieza, saca los tramos de mesa y lista los huecos entre cambios de luz.
  2. En cada hueco de mas de `--max` s mete `n` cambios, repartidos parejo. **La paridad importa**: el
     borde derecho de un hueco interior ya es un cambio (claro->oscuro o al reves); si se mete un numero
     IMPAR de cambios, el estado antes del borde queda igual al de despues y el borde deja de ser corte.
     Por eso en los huecos interiores `n` es par. El primero (desde el fin del gancho) y el ultimo (hasta
     la tarjeta de cierre) no tienen esa restriccion: el gancho que se va y el cierre que entra cambian
     la imagen igual.
  3. Cada cambio se ancla a la PALABRA de la voz mas cercana al instante ideal (un verbo motiva el corte,
     `COMPO.md`), dentro de su linea, y nunca a menos de 1,2 s de otro cambio.
  4. Si el tramo esta claro, el primero es `MESA @ "palabra"`; si esta oscuro, `MAPA(sitio, clase)`, con
     el sitio del ultimo MAPA anterior del guion y la clase alternando medio/abrir.

Despues hay que correr `compo.py --pieza N` (check) y `luz.py`: un corte nuevo puede dejar una linea sin
contenido (regla g) y eso se arregla a mano, anclando el contenido al mismo instante.
"""
import io, json, math, os, re, shutil, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import compo
import luz

SEP = ' · '


def _norm(w):
    return re.sub(r'[^a-z0-9]', '', w.lower())


def plan(d, lim):
    sc, info = compo.build(guion=os.path.join(d, 'guion_v.md'), tiempos=os.path.join(d, 'audio', 'tiempos.json'),
                           formato='vertical', base=d, out=os.path.join(d, '_qc'), verbose=False)
    C = info['compo']; dur = info['dur']; t_ini = info['t_ini']
    lineas = info['lineas']
    pal = json.load(open(os.path.join(d, 'audio', '_palabras.json'), encoding='utf-8'))
    pal = [(w, float(a) - t_ini, float(b) - t_ini) for w, a, b in pal if _norm(w)]
    mesas = sorted(C.mesas)
    oscuro = lambda t: any(a <= t < b for a, b in mesas)
    ts = luz.cambios(info)
    usados = list(ts)
    inserciones = []                                    # (t, linea, palabra, tipo)
    for k, (x, y) in enumerate(zip(ts, ts[1:])):
        g = y - x
        if g <= lim: continue
        primero = (k == 0)
        ultimo = (abs(y - dur) < 0.05)
        n = max(1, math.ceil(g / lim) - 1)
        if not (primero or ultimo) and n % 2: n += 1
        estado = oscuro((x + y) / 2)
        for j in range(1, n + 1):
            ideal = x + g * j / (n + 1)
            cand = []
            for w, a, b in pal:
                if not (x + 1.2 < a < y - 1.2) or any(abs(a - u) < 1.2 for u in usados): continue
                li = next((i for i, l in enumerate(lineas) if l['inicio'] <= a < l['fin']), None)
                if li is None: continue
                # `@ "palabra"` se resuelve a la PRIMERA aparicion en la linea: una palabra repetida
                # («the», «of») ancla el corte en otro sitio. Solo palabras de contenido y unicas.
                nw = _norm(w)
                if len(nw) < 4 and not nw.isdigit(): continue
                if [_norm(x_) for x_ in lineas[li]['texto'].split()].count(nw) != 1: continue
                cand.append((abs(a - ideal), a, w, li))
            if not cand: continue
            _, a, w, li = min(cand)
            estado = not estado
            inserciones.append((a, li, w, 'MESA' if estado else 'MAPA'))
            usados.append(a)
    return inserciones, info


def escribir(d, inserciones):
    p = os.path.join(d, 'guion_v.md')
    shutil.copyfile(p, p + '.bak')
    txt = io.open(p, encoding='utf-8').read().split('\n')
    # indice de cada bloque A: -> su linea V: (la primera V: despues del A:)
    bloques = []
    for i, l in enumerate(txt):
        if l.startswith('**A:**'):
            v = next((j for j in range(i + 1, min(i + 6, len(txt))) if txt[j].startswith('**V:**')), None)
            bloques.append((i, v))
    mundo = json.load(open(os.path.join(d, 'mundo.json'), encoding='utf-8'))
    sitio_def = list(mundo.get('sitios', {}))[0]
    clase_alt = ['medio', 'abrir']
    for k, (t, li, w, tipo) in enumerate(sorted(inserciones)):
        _, vi = bloques[li]
        if vi is None: continue
        # el sitio del ultimo MAPA anterior (en esta linea o las previas)
        previo = ' '.join(txt[bloques[q][1]] for q in range(li + 1) if bloques[q][1] is not None)
        sit = re.findall(r'MAPA\(([^,\)]+)', previo)
        sitio = sit[-1].strip() if sit else sitio_def
        palabra = re.sub(r'[^\w\-\']', '', w)
        verbo = ('MESA @ "%s"' % palabra) if tipo == 'MESA' else \
                ('MAPA(%s, %s) @ "%s"' % (sitio, clase_alt[k % 2], palabra))
        txt[vi] = txt[vi] + SEP + verbo
    io.open(p, 'w', encoding='utf-8').write('\n'.join(txt))


def main():
    a = sys.argv[1:]
    if '--pieza' not in a:
        print(__doc__); return
    n = int(a[a.index('--pieza') + 1])
    lim = float(a[a.index('--max') + 1]) if '--max' in a else 4.3
    d = compo._resolver(a[0], n)
    ins, info = plan(d, lim)
    print('pieza %d: %d cambios de luz a insertar' % (n, len(ins)))
    for t, li, w, tipo in sorted(ins):
        print('   %6.2f s  linea %2d  %-4s @ "%s"' % (t, li, tipo, w))
    if '--escribir' in a and ins:
        escribir(d, ins)
        print('guion_v.md actualizado (copia en guion_v.md.bak)')


if __name__ == '__main__':
    main()
