# -*- coding: utf-8 -*-
"""Regla 25: mete los cinco bloques de transicion de acto DENTRO del audio y desplaza los tiempos.

El bloque dura 4,4 s, la voz principal se calla, y el titulo lo lee una SEGUNDA voz
(`21m00Tcm4TlvDq8ikWAM`). Va antes de los beats 5, 6, 7, 8 y 9 (ACT I a ACT V).

**No se vuelve a correr whisper.** La skill lo dice explicitamente: cambiar la duracion no obliga a
repetir la transcripcion, las palabras cacheadas se desplazan por calculo exacto. Cada linea y cada
palabra posterior a una insercion se corre 4,4 s, que es lo que dura el bloque.

    python videos/13_yemen/audio/actos13.py

Entrada : 13_yemen_eleven_brian.wav + .tiempos.json + _palabras.json  (los de alinear13.py)
Salida  : 13_yemen_cuerpo.wav + 13_yemen_cuerpo.tiempos.json + _palabras_cuerpo.json
          y actos.json, con el t0 de cada bloque para que la coreografia llame a `sc.acto()`.
"""
import json, subprocess
from pathlib import Path
import numpy as np, soundfile as sf

AQUI = Path(__file__).resolve().parent
SR = 24000
BLOQUE = 4.4                 # regla 25: identico en los cinco actos
VOZ_EN = 1.5                 # la segunda voz entra a 1,5 s del bloque (tras el golpe y la regla)

# beat delante del cual va cada bloque -> (numero de acto, titulo, mp3 de la segunda voz)
ACTOS = [
    (5, 'ACT I',   'The Gate',      'acto_1.mp3'),
    (6, 'ACT II',  'Who They Are',  'acto_2.mp3'),
    (7, 'ACT III', 'Eleven Years',  'acto_3.mp3'),
    (8, 'ACT IV',  'The Pincer',    'acto_4.mp3'),
    (9, 'ACT V',   'The Receipt',   'acto_5.mp3'),
]

URLS = {
    'acto_1.mp3': 'https://gcdn.picsart.com/editing-temp/34e9ae3b-a503-439c-a2a9-ac9a6f26d3ea.mp3',
    'acto_2.mp3': 'https://gcdn.picsart.com/editing-temp/f26bf557-baee-488d-98e3-dd29052b0dc6.mp3',
    'acto_3.mp3': 'https://gcdn.picsart.com/editing-temp/5165d378-006f-4629-8728-0a71fe51b3a9.mp3',
    'acto_4.mp3': 'https://gcdn.picsart.com/editing-temp/ff343836-e98a-4325-ae53-cfb797cf6719.mp3',
    'acto_5.mp3': 'https://gcdn.picsart.com/editing-temp/6948b75c-3019-4508-81ca-aaf63dc4304f.mp3',
}


def bajar():
    import urllib.request
    d = AQUI / 'actos'
    d.mkdir(exist_ok=True)
    for n, u in URLS.items():
        if not (d / n).exists():
            urllib.request.urlretrieve(u, d / n)
    return d


def leer_mp3(p):
    w = p.with_suffix('.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(p), '-ac', '1', '-ar', str(SR), str(w)],
                   check=True)
    x, _ = sf.read(str(w))
    x = x.astype(np.float32)
    env = np.abs(x)
    idx = np.where(env > 10 ** (-45 / 20))[0]
    if len(idx):
        x = x[max(0, idx[0] - int(0.03 * SR)):min(len(x), idx[-1] + int(0.10 * SR))]
    return x


def main():
    d = bajar()
    t = json.load(open(AQUI / '13_yemen_eleven_brian.tiempos.json', encoding='utf-8'))
    pal = json.load(open(AQUI / '_palabras.json', encoding='utf-8'))
    x, sr = sf.read(str(AQUI / '13_yemen_eleven_brian.wav'))
    assert sr == SR, sr
    x = x.astype(np.float32)

    # dónde cae cada insercion, en segundos del audio VIEJO: justo al empezar el beat
    cortes = []
    for bi, num, tit, mp3 in [(a[0], a[1], a[2], a[3]) for a in ACTOS]:
        # El bloque va PEGADO al arranque del beat: la regla 25 dice que al cerrarlo "se levanta el
        # velo y corta al acto". La pausa de 1,5 s del beat anterior queda DELANTE del bloque, que es
        # el respiro natural: cierre del acto -> respiro -> golpe -> titulo -> acto.
        t0 = t['beats'][bi]['inicio']
        cortes.append({'t_viejo': t0, 'num': num, 'titulo': tit, 'mp3': mp3})
    cortes.sort(key=lambda c: c['t_viejo'])

    # 1) montar el wav nuevo
    trozos, prev, actos_out = [], 0.0, []
    desplazado = 0.0
    for c in cortes:
        i0, i1 = int(prev * SR), int(c['t_viejo'] * SR)
        trozos.append(x[i0:i1])
        blk = np.zeros(int(BLOQUE * SR), np.float32)
        v = leer_mp3(d / c['mp3'])
        v = v / max(1e-6, np.abs(v).max()) * 0.80
        j = int(VOZ_EN * SR)
        n = min(len(v), len(blk) - j)
        blk[j:j + n] = v[:n]
        trozos.append(blk)
        actos_out.append({'acto': c['num'], 'titulo': c['titulo'],
                          't0': round(c['t_viejo'] + desplazado, 3),
                          'dur': BLOQUE, 'voz_en': VOZ_EN})
        desplazado += BLOQUE
        prev = c['t_viejo']
    trozos.append(x[int(prev * SR):])
    y = np.concatenate(trozos)
    sf.write(str(AQUI / '13_yemen_cuerpo.wav'), y, SR)

    # 2) desplazar tiempos por calculo exacto (nada de volver a transcribir)
    def mover(v):
        s = 0.0
        for c in cortes:
            if v >= c['t_viejo'] - 1e-9:
                s += BLOQUE
        return round(v + s, 3)

    for b in t['beats']:
        b['inicio'], b['fin'] = mover(b['inicio']), mover(b['fin'])
    for l in t['lineas']:
        l['inicio'], l['fin'] = mover(l['inicio']), mover(l['fin'])
    t['duracion'] = round(len(y) / SR, 2)
    t['actos'] = actos_out
    json.dump(t, open(AQUI / '13_yemen_cuerpo.tiempos.json', 'w', encoding='utf-8'),
              indent=1, ensure_ascii=False)

    for p in pal:
        p['t0'], p['t1'] = mover(p['t0']), mover(p['t1'])
    json.dump(pal, open(AQUI / '_palabras_cuerpo.json', 'w', encoding='utf-8'),
              indent=0, ensure_ascii=False)

    print(f'cuerpo: {t["duracion"]:.1f} s = {int(t["duracion"]//60)}:{int(t["duracion"]%60):02d}')
    print(f'{len(actos_out)} bloques de acto de {BLOQUE} s:')
    for a in actos_out:
        print(f'   {a["acto"]:7s} {a["titulo"]:14s} t0={a["t0"]:7.1f}')
    # control: los beats de acto tienen que empezar justo despues de su bloque
    for a, (bi, *_ ) in zip(actos_out, ACTOS):
        ini = t['beats'][bi]['inicio']
        gap = ini - (a['t0'] + BLOQUE)
        assert abs(gap) < 0.05, f'{a["acto"]}: hueco {gap:.3f}s'
    print('control: cada acto arranca justo al cerrar su bloque  -> OK')


if __name__ == '__main__':
    main()
