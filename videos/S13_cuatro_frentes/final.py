# -*- coding: utf-8 -*-
"""De `salida/cuerpo.mp4` (el render de `compo.py`) al archivo que se sube. 0 creditos.

    python final.py 1          # una pieza
    python final.py todas      # las cuatro, en orden

El cuerpo ya trae lo que en la S12 ponia `armar.py` (gancho, chip PART n OF 4, barra de progreso,
subtitulos): `compo.py` compone en vertical nativo. Aca solo queda lo de audio y el cierre:

  1. cortina `cue_04_dron` por debajo de la voz (Lyria, propia; la misma en las cuatro piezas: es la
     identidad sonora de la serie) -> `NN_slug.mp4`
  2. cierre pegado (`cierre.py pegar`): tarjeta LIKE + SUBSCRIBE con la voz de George
  3. **loudnorm a -14 LUFS sobre el archivo ENTERO**, despues del cierre. En la S12 se normalizaba
     antes de pegar el cierre y el cierre quedaba a otro volumen que el cuerpo.
  4. copia `_movil.mp4` (720x1280, < 10 MB) solo para mirarla en el telefono o mandarla por chat
  5. `produccion/ritmo.py --json` sobre el final: tiene que dar PASS (regla 30)
"""
import json, os, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
PROD = os.path.join(RAIZ, 'produccion')
S = os.path.join(AQUI, 'shorts')
FICHA = json.load(open(os.path.join(S, 'serie.json'), encoding='utf-8'))
CUE = os.path.join(PROD, 'musica', 'cue_04_dron.mp3')


def pieza(n):
    for s in FICHA['shorts']:
        if s['n'] == n: return s
    raise SystemExit('pieza %s no existe' % n)


def dur(f):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                 '-of', 'csv=p=0', f], capture_output=True, text=True).stdout.strip())


def ff(*args):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y'] + list(args),
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit('ffmpeg fallo: ' + r.stderr[-600:])


def final(n):
    P = pieza(n)
    d = os.path.join(S, P['dir'], 'salida')
    cuerpo = os.path.join(d, 'cuerpo.mp4')
    if not os.path.exists(cuerpo):
        raise SystemExit('pieza %d: falta %s (render de compo.py)' % (n, cuerpo))
    pz = os.path.join(d, '%02d_%s.mp4' % (P['n'], P['dir'].split('_', 1)[1]))

    # 1 · cortina
    D = dur(cuerpo)
    fil = ("[1:a]atrim=0:%.3f,asetpts=N/SR/TB,volume=0.115,afade=t=in:st=0:d=1.6,"
           "afade=t=out:st=%.3f:d=1.9[m];"
           "[0:a][m]amix=inputs=2:duration=first:dropout_transition=0[a]") % (D, max(0.1, D - 1.9))
    ff('-i', cuerpo, '-i', CUE, '-filter_complex', fil, '-map', '0:v', '-c:v', 'copy',
       '-map', '[a]', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', pz)
    print('pieza %d: cortina -> %s (%.1f s)' % (n, os.path.basename(pz), dur(pz)))

    # 2 · cierre
    sys.path.insert(0, AQUI)
    import cierre
    cierre.pegar(n)

    # 3 · loudnorm sobre el entero
    tmp = pz.replace('.mp4', '_ln.mp4')
    ff('-i', pz, '-map', '0:v', '-c:v', 'copy', '-map', '0:a',
       '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
       '-movflags', '+faststart', tmp)
    os.replace(tmp, pz)

    # 4 · copia movil
    movil = pz.replace('.mp4', '_movil.mp4')
    ff('-i', pz, '-vf', 'scale=720:1280', '-c:v', 'libx264', '-preset', 'medium', '-crf', '30',
       '-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', movil)

    # 5 · ritmo
    r = subprocess.run([sys.executable, os.path.join(PROD, 'ritmo.py'), pz, '--json'],
                       capture_output=True, text=True)
    print('pieza %d: FINAL %s  %.1f s  %.1f MB  |  movil %.1f MB' %
          (n, pz, dur(pz), os.path.getsize(pz) / 1e6, os.path.getsize(movil) / 1e6))
    print('pieza %d: ritmo -> %s' % (n, (r.stdout or r.stderr).strip()[-400:]))
    return pz


if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else '1'
    for n in ([1, 2, 3, 4] if arg == 'todas' else [int(arg)]):
        final(n)
