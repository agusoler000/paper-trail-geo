# -*- coding: utf-8 -*-
"""Compacta las PAUSAS de una voz ya generada, sin tocar la voz. 0 creditos.

    python voz/compactar.py <voz.wav> <salida.wav> [--palabras in.json out.json] [--tiempos in.json out.json]
                            [--max 0.40] [--max-largo 0.75] [--min 0.28] [--umbral -38] [--proteger a-b,c-d]

Por que existe (auditoria del motor, 2026-09-15). Medido con la misma vara sobre la referencia que
paso Agustin (GeoGlobeTales) y sobre nuestras voces:

    referencia:  3 pausas/min de >= 0,25 s     ·  189 wpm
    nosotros:   18-22 pausas/min, media 0,8 s   ·  150-160 wpm   (la pieza 4 de la S12: 25 % del clip es silencio)

Las etiquetas de direccion ([faster], [leaning in]...) no mueven ese numero: ElevenLabs cierra cada
frase con una pausa larga y el guion tiene una frase por linea. La monotonia que se oye es, en buena
parte, ese metronomo de silencios iguales. Esto los acorta:

  - una pausa "de frase" (0,28-1,0 s) queda en `--max` (0,40 s por defecto);
  - una pausa "dramatica" (>= 1,0 s: las que ponen los [pause] de la direccion y los limites de
    beat) queda en `--max-largo` (0,75 s): se conserva el gesto, no la espera;
  - los tramos `--proteger` (los bloques de acto de 4,4 s del episodio, por ejemplo) no se tocan;
  - el silencio inicial y el final no se tocan (son el pre/post-roll del montaje).

El corte se hace con un fundido de 12 ms en la juntura, nunca a cuchillo. Y como se sabe exactamente
que se quito y donde, se reescriben los tiempos por palabra (`_palabras.json`) y por linea
(`tiempos.json`) con la misma funcion, asi que la coreografia sigue clavada a la voz.
"""
import json, sys
import numpy as np, soundfile as sf

FADE = 0.012


def _energia(x, sr, paso=0.01):
    n = int(paso * sr)
    k = len(x) // n
    e = np.sqrt(np.mean(x[:k * n].reshape(k, n) ** 2, axis=1))
    return 20 * np.log10(e + 1e-9), paso


def pausas(x, sr, umbral=-38.0, minimo=0.28):
    """[(t0, t1)] de los tramos de silencio de al menos `minimo` s."""
    e, paso = _energia(x, sr)
    sil = e < umbral
    out = []; run = 0; ini = 0
    for k, s in enumerate(sil):
        if s:
            if run == 0: ini = k
            run += 1
        else:
            if run * paso >= minimo: out.append((ini * paso, (ini + run) * paso))
            run = 0
    if run * paso >= minimo: out.append((ini * paso, (ini + run) * paso))
    return out


def compactar(x, sr, maximo=0.40, max_largo=0.75, minimo=0.28, umbral=-38.0, proteger=(),
              largo_desde=1.0):
    """Devuelve (y, cortes) con cortes = [(t_desde, t_hasta)] en la linea de tiempo VIEJA de lo
    que se quito. Cada pausa se acorta por su cola (se conserva el arranque del silencio, que es
    donde cae el final de la palabra anterior)."""
    dur = len(x) / sr
    cortes = []
    for a, b in pausas(x, sr, umbral, minimo):
        if a < 0.05 or b > dur - 0.05: continue                  # pre/post-roll
        if any(pa - 0.05 <= a and b <= pb + 0.05 for pa, pb in proteger): continue
        if any(a < pb and b > pa for pa, pb in proteger): continue
        largo = b - a
        tope = max_largo if largo >= largo_desde else maximo
        if largo <= tope + 0.02: continue
        # se quita el tramo [a+tope-FADE, b-FADE]: queda `tope` de silencio
        cortes.append((a + tope - FADE, b - FADE))
    # construir
    y = []; f = int(FADE * sr); pos = 0
    for c0, c1 in cortes:
        i0, i1 = int(c0 * sr), int(c1 * sr)
        seg = x[pos:i0].copy()
        if len(seg) >= f and f > 0: seg[-f:] *= np.linspace(1, 0, f, dtype=np.float32)
        y.append(seg)
        nxt = x[i1:i1 + f].copy() * np.linspace(0, 1, min(f, len(x) - i1), dtype=np.float32)[:len(x[i1:i1 + f])]
        # el fundido de entrada se suma al final del tramo anterior (crossfade real)
        if len(y[-1]) >= len(nxt): y[-1][-len(nxt):] += nxt
        else: y.append(nxt)
        pos = i1 + f
    y.append(x[pos:].copy())
    return np.concatenate(y), cortes


def mapa(cortes):
    """Funcion t_viejo -> t_nuevo."""
    def f(t):
        d = 0.0
        for c0, c1 in cortes:
            if t >= c1: d += (c1 - c0)
            elif t > c0: d += (t - c0)
        return round(t - d, 3)
    return f


def _remap_palabras(pal, f):
    return [[w, f(float(a)), max(f(float(a)) + 0.02, f(float(b)))] for w, a, b in pal]


def _remap_tiempos(T, f):
    T = dict(T)
    if 'lineas' in T:
        for l in T['lineas']:
            l['inicio'] = f(float(l['inicio'])); l['fin'] = max(l['inicio'] + 0.05, f(float(l['fin'])))
    for k in ('beats', 'actos'):
        for b in T.get(k, []) or []:
            for kk in ('inicio', 'fin', 'voz_ini', 'voz_fin'):
                if kk in b: b[kk] = f(float(b[kk]))
    if 'dur' in T: T['dur'] = f(float(T['dur']))
    return T


def main():
    a = sys.argv[1:]
    if len(a) < 2: print(__doc__); return
    src, dst = a[0], a[1]
    def opt(k, d=None): return a[a.index(k) + 1] if k in a else d
    def opt2(k):
        if k not in a: return None
        i = a.index(k); return (a[i + 1], a[i + 2])
    prot = []
    if opt('--proteger'):
        for tr in opt('--proteger').split(','):
            p, q = tr.split('-'); prot.append((float(p), float(q)))
    x, sr = sf.read(src); x = x.astype(np.float32)
    if x.ndim > 1: x = x.mean(axis=1)
    y, cortes = compactar(x, sr, maximo=float(opt('--max', 0.40)), max_largo=float(opt('--max-largo', 0.75)),
                          minimo=float(opt('--min', 0.28)), umbral=float(opt('--umbral', -38)), proteger=prot)
    sf.write(dst, y, sr)
    f = mapa(cortes)
    quitado = sum(c1 - c0 for c0, c1 in cortes)
    print('%s: %.1f s -> %.1f s  (%d pausas acortadas, %.1f s quitados, %d protegidas)'
          % (dst, len(x) / sr, len(y) / sr, len(cortes), quitado, len(prot)))
    if opt2('--palabras'):
        pi, po = opt2('--palabras')
        pal = json.load(open(pi, encoding='utf-8'))
        json.dump(_remap_palabras(pal, f), open(po, 'w', encoding='utf-8'))
        print('palabras ->', po)
    if opt2('--tiempos'):
        ti, to = opt2('--tiempos')
        T = json.load(open(ti, encoding='utf-8'))
        json.dump(_remap_tiempos(T, f), open(to, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('tiempos ->', to)


if __name__ == '__main__':
    main()
