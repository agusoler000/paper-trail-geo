# -*- coding: utf-8 -*-
"""ritmo_previo.py - el veredicto de `ritmo.py` ANTES de renderizar: 4 cuadros por segundo a 270x480.

    python produccion/ritmo_previo.py videos/S13_cuatro_frentes --pieza 1

`ritmo.py` decodifica el video a 4 fps y 96x54 y mide tres cosas; la que falla con un mapa de tierra
uniforme es «ningun plano > 6 s sin cambio» (un corte entre dos zonas de papel caqui casi iguales no
se detecta, y tampoco lo ve el ojo). Averiguarlo con el render real cuesta 5 min por intento. Esto
renderiza EXACTAMENTE los instantes que `ritmo.py` va a muestrear (k/4 s), achicados, con 20 procesos,
y le pasa `ritmo.py` al resultado: mismo veredicto en ~1 min.

No sirve para mirar la imagen (para eso `compo.py --hoja` y `muestras.py`): sirve para el numero.

Por que no usa `motor.render`: la cadencia es la global `motor.FPS` y en Windows cada proceso hijo
reimporta el modulo con FPS=24, asi que pedirle 4 fps desde el padre daba cuadros en los instantes
equivocados.
"""
import json, os, shutil, subprocess, sys
import multiprocessing as mp

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

FPS_P = 4
W_P, H_P = 270, 480


def _w(args):
    i0, i1, outdir = args
    sys.path.insert(0, AQUI)
    import compo
    from PIL import Image
    sc = compo._build_env()
    for i in range(i0, i1):
        sc.render(i / FPS_P).convert('RGB').resize((W_P, H_P), Image.BILINEAR).save(
            os.path.join(outdir, 'p_%05d.jpg' % i), quality=85)
    return i1 - i0


def main():
    import compo
    a = sys.argv[1:]
    if '--pieza' not in a:
        print(__doc__); return
    d = compo._resolver(a[0], int(a[a.index('--pieza') + 1]))
    kw = dict(guion=os.path.join(d, 'guion_v.md'), tiempos=os.path.join(d, 'audio', 'tiempos.json'),
              formato='vertical', beat=None, serie=None, base=d, out=os.path.join(d, '_qc'), mundos=None)
    sc, info = compo.build(**kw)
    os.environ['COMPO_ARGS'] = json.dumps(kw)
    n = int(info['dur'] * FPS_P)
    outdir = os.path.join(d, '_qc', '_previo')
    shutil.rmtree(outdir, ignore_errors=True); os.makedirs(outdir, exist_ok=True)
    workers = max(1, (os.cpu_count() or 4) - 2)
    step = max(4, n // (workers * 3))
    chunks = [(i, min(n, i + step), outdir) for i in range(0, n, step)]
    with mp.Pool(workers) as pool:
        hechos = sum(pool.imap_unordered(_w, chunks))
    mp4 = os.path.join(d, '_qc', 'previo_4fps.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS_P), '-i',
                    os.path.join(outdir, 'p_%05d.jpg'), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', mp4],
                   check=True)
    r = subprocess.run([sys.executable, os.path.join(AQUI, 'ritmo.py'), mp4],
                       capture_output=True, text=True)
    print('previo: %d cuadros a %d fps -> %s' % (hechos, FPS_P, mp4))
    print((r.stdout or r.stderr)[-1400:])


if __name__ == '__main__':
    main()
