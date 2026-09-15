# -*- coding: utf-8 -*-
"""Mide el RITMO VISUAL de un video terminado: cuanto se mueve la imagen, cada cuanto hay corte
y cuanto del cuadro esta ocupado. 0 creditos, ffmpeg + numpy.

Nace del hallazgo del 2026-09-15 (canal/POR_QUE_SON_SOSOS_2026-09-15.md): el checklist mide
cortes por minuto y daba verde (10,4/min) mientras el 62 % de los cuadros del episodio eran
identicos al anterior. Un corte cada 4 s entre dos imagenes fijas no es ritmo: es un pase de
diapositivas. Esto mide lo que falta.

    python produccion/ritmo.py <video.mp4>              # informe + veredicto
    python produccion/ritmo.py <video.mp4> --contacto   # ademas, hoja de contacto de 12 cuadros
    python produccion/ritmo.py <video.mp4> --json       # solo el dict + PASS/FAIL (para el checklist)

Que significa cada numero:
  quietos     % de muestras (a 4 fps) cuya diferencia con la anterior es < 0,8/255, o sea, imagen
              congelada. Medido en los eps. 04 y 06: 62,8 % y 62,2 %. META: < 20 %.
  cortes/min  cambios de plano detectados. Los eps. 04 y 06 dan 11,3 y 10,5. META: 10-15 (se cumple).
  ocupacion   % del cuadro con papel/documento (luminancia > 150). Mediana de los eps: 34 %.
              El resto es mesa vacia. META: mediana > 55 %.
              **No aplica a un video de mundo-mapa**: ahi mide teal, no mesa vacia (§6.6).

VEREDICTO (motor v4, §6.6): `veredicto(path) -> (dict, bool)` con las tres condiciones que se
exigen a una produccion nueva: quietos < 20 %, movimiento MEDIANO >= 2,5 y ningun plano de mas de
6 s sin un cambio. La medicion no cambio: son los mismos numeros de siempre, leidos como regla.
"""
import subprocess, sys, os, json
import numpy as np

FPS, W, H = 4, 96, 54
QUIETO, CORTE = 0.8, 12.0
META_QUIETOS, META_CORTES, META_OCUP = 20.0, 10.0, 55.0
META_MOV_MEDIANA, META_PLANO_MAX = 2.5, 6.0


def _frames(path, fps, w, h):
    cmd = ['ffmpeg', '-v', 'error', '-i', path, '-vf', f'fps={fps},scale={w}:{h}',
           '-pix_fmt', 'gray', '-f', 'rawvideo', '-']
    out = subprocess.run(cmd, capture_output=True).stdout
    n = len(out) // (w * h)
    return np.frombuffer(out, dtype=np.uint8)[:n * w * h].reshape(n, h, w)


def metricas(path):
    """Los numeros crudos, sin imprimir. La medicion es la misma de siempre."""
    f = _frames(path, FPS, W, H).astype(np.int16)
    d = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))
    dur = len(f) / FPS
    cortes = np.where(d > CORTE)[0] / FPS
    g = np.diff(cortes) if len(cortes) > 1 else np.array([dur])
    o = _frames(path, 1, 160, 90)
    ocup = (o > 150).mean(axis=(1, 2)) * 100
    return {'archivo': os.path.basename(path), 'dur': round(float(dur), 2),
            'quietos': round(float(100 * (d < QUIETO).mean()), 2),
            'cortes': int(len(cortes)),
            'cortes_por_min': round(float(len(cortes) / max(1e-9, dur / 60)), 2),
            'ocupacion_mediana': round(float(np.median(ocup)), 2),
            'movimiento_medio': round(float(d.mean()), 3),
            'movimiento_mediano': round(float(np.median(d)), 3),
            'hueco_mediano': round(float(np.median(g)), 2),
            'hueco_p90': round(float(np.percentile(g, 90)), 2),
            'plano_mas_largo': round(float(g.max()), 2),
            '_d': d, '_cortes': cortes, '_g': g, '_ocup': ocup}


def veredicto(path, m=None):
    """(dict, ok). Las tres condiciones de §6.6 para una produccion nueva. `ocupacion` NO entra:
    en un video de mundo-mapa mide teal saturado, no mesa vacia."""
    m = m or metricas(path)
    pruebas = {
        'quietos < %.0f %%' % META_QUIETOS: m['quietos'] < META_QUIETOS,
        'movimiento mediano >= %.1f' % META_MOV_MEDIANA: m['movimiento_mediano'] >= META_MOV_MEDIANA,
        'ningun plano > %.0f s sin cambio' % META_PLANO_MAX: m['plano_mas_largo'] <= META_PLANO_MAX,
    }
    out = {k: v for k, v in m.items() if not k.startswith('_')}
    out['pruebas'] = pruebas
    out['veredicto'] = 'PASS' if all(pruebas.values()) else 'FAIL'
    return out, all(pruebas.values())


def medir(path):
    m = metricas(path)
    d, cortes, g, ocup = m['_d'], m['_cortes'], m['_g'], m['_ocup']
    dur = m['dur']
    quietos, cpm, med_oc = m['quietos'], m['cortes_por_min'], m['ocupacion_mediana']

    print(f'\n{os.path.basename(path)}  ·  {int(dur//60)}:{int(dur%60):02d}\n')
    print(f'  quietos     {quietos:5.1f} %   (meta < {META_QUIETOS:.0f} %)   {"OK" if quietos < META_QUIETOS else "<-- LA IMAGEN NO SE MUEVE"}')
    print(f'  cortes/min  {cpm:5.1f}     (meta > {META_CORTES:.0f})     {"OK" if cpm >= META_CORTES else "<-- pocos cortes"}')
    print(f'  ocupacion   {med_oc:5.1f} %   (meta > {META_OCUP:.0f} %)   {"OK" if med_oc > META_OCUP else "<-- demasiada mesa vacia"}')
    print(f'\n  movimiento medio {d.mean():.2f}/255 · mediana {np.median(d):.2f}')
    print(f'  hueco entre cortes: mediana {np.median(g):.1f}s · p90 {np.percentile(g,90):.1f}s · max {g.max():.1f}s')

    if len(cortes) > 1:
        peor = sorted(zip(cortes[:-1], g), key=lambda t: -t[1])[:5]
        print('  planos mas largos: ' + ' · '.join(f'{int(t//60)}:{int(t%60):02d} ({d_:.0f}s)' for t, d_ in peor))

    print('\n  min:seg | mov  | cortes | ocup')
    for b in range(int(np.ceil(dur / 30))):
        s0, s1 = b * 30, (b + 1) * 30
        seg = d[int(s0 * FPS):int(s1 * FPS)]
        if not len(seg): continue
        c = int(((cortes >= s0) & (cortes < s1)).sum())
        oc = ocup[s0:s1].mean() if s0 < len(ocup) else 0
        flo = '  <-- tramo flojo' if (seg.mean() < 1.5 or c < 4) else ''
        print(f'  {s0//60:02d}:{s0%60:02d}   | {seg.mean():4.2f} | {c:2d}     | {oc:4.0f} %{flo}')

    v, ok = veredicto(path, m)
    print('\n  VEREDICTO (motor v4 §6.6): ' + v['veredicto'])
    for k, r in v['pruebas'].items():
        print(f'    {"OK  " if r else "FALLA"}  {k}')
    return quietos, cpm, med_oc


def contacto(path, n=12):
    from PIL import Image, ImageDraw
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                '-of', 'csv=p=0', path], capture_output=True, text=True).stdout)
    ts = [int(dur * (i + 0.5) / n) for i in range(n)]
    ims = []
    for t in ts:
        tmp = os.path.join(os.path.dirname(os.path.abspath(path)), f'_c{t}.png')
        subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t), '-i', path, '-frames:v', '1',
                        '-vf', 'scale=400:-1', tmp, '-y'], check=True)
        ims.append((t, Image.open(tmp).copy())); os.remove(tmp)
    w, h = ims[0][1].size
    out = Image.new('RGB', (w * 4, h * ((n + 3) // 4)), (15, 15, 15)); dr = ImageDraw.Draw(out)
    for i, (t, im) in enumerate(ims):
        x, y = (i % 4) * w, (i // 4) * h
        out.paste(im, (x, y)); dr.text((x + 6, y + 6), f'{t//60}:{t%60:02d}', fill=(255, 220, 120))
    dst = os.path.splitext(path)[0] + '_contacto.png'
    out.save(dst); print('\n  hoja de contacto ->', dst)


if __name__ == '__main__':
    v = sys.argv[1]
    if '--json' in sys.argv:
        d, ok = veredicto(v)
        print(json.dumps(d, indent=1, ensure_ascii=False))
        sys.exit(0 if ok else 1)
    medir(v)
    if '--contacto' in sys.argv: contacto(v)
