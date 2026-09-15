# -*- coding: utf-8 -*-
"""Cierra una pieza ya renderizada: armado vertical + cierre + ritmo + hoja de contacto.

    python terminar.py 1

Es la cadena de `ESTADO.md` §2 pasos 5-7 en un solo comando, para no repetirla a mano cuatro veces
y, sobre todo, para que las cuatro piezas salgan exactamente iguales.
"""
import json, os, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
PROD = os.path.join(RAIZ, 'produccion')
sys.path.insert(0, PROD); sys.path.insert(0, AQUI)
import shorts as SH
import props as PR
from PIL import Image, ImageDraw

S = os.path.join(AQUI, 'shorts')
FICHA = json.load(open(os.path.join(S, 'serie.json'), encoding='utf-8'))
CUE = os.path.join(PROD, 'musica', 'cue_04_dron.mp3')


def pieza(n):
    for P in FICHA['shorts']:
        if P['n'] == n: return P
    raise SystemExit('pieza %s no existe' % n)


def _dur(f):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                 '-of', 'csv=p=0', f], capture_output=True, text=True).stdout)


def hoja_contacto(v, out, cols=4, rows=3):
    """12 cuadros REALES del mp4 final. La regla del canal: se mira el archivo, no la previsual."""
    dur = _dur(v)
    cw = 300; ch = int(cw * 1920 / 1080)
    q = Image.new('RGB', (cols * cw, rows * ch), (20, 20, 20)); d = ImageDraw.Draw(q)
    tmp = os.path.join(os.path.dirname(out), '_hoja_tmp'); os.makedirs(tmp, exist_ok=True)
    for i in range(cols * rows):
        t = dur * (i + 0.5) / (cols * rows)
        f = os.path.join(tmp, 'f%02d.png' % i)
        subprocess.run(['ffmpeg', '-v', 'error', '-ss', '%.3f' % t, '-i', v, '-frames:v', '1',
                        '-y', f], check=True)
        q.paste(Image.open(f).convert('RGB').resize((cw, ch), Image.LANCZOS),
                ((i % cols) * cw, (i // cols) * ch))
        d.text(((i % cols) * cw + 8, (i // cols) * ch + 6), '%.1fs' % t, fill=(255, 220, 120),
               font=PR.FONTC(20))
    q.save(out, quality=90)
    for f in os.listdir(tmp): os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    return out


def main(n):
    import cierre as CI
    import ritmo
    P = pieza(n)
    slug = P['dir'].split('_', 1)[1]
    d = os.path.join(S, P['dir'])
    cuerpo = os.path.join(d, 'salida', 'cuerpo.mp4')
    out = os.path.join(d, 'salida', '%02d_%s.mp4' % (n, slug))
    if not os.path.exists(cuerpo): raise SystemExit('falta %s (corre `coreo4.py render %d`)' % (cuerpo, n))

    SH.armar_vertical(cuerpo, os.path.join(d, 'audio', 'tiempos.json'), out,
                      hook=P['hook'], rojo=P['rojo'], resaltar=[], n=n, N=4,
                      cue=CUE if os.path.exists(CUE) else None, subs=False)
    CI.pegar(n)

    # el concat no puede romper ni la resolucion ni el audio
    pr = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                         'stream=codec_type,width,height,sample_rate,channels',
                         '-of', 'default=nw=1', out], capture_output=True, text=True).stdout
    print('   ' + ' · '.join(x for x in pr.split() if x))

    hoja = os.path.join(d, 'salida', '_qc_final.jpg')
    hoja_contacto(out, hoja)
    dur = _dur(out)
    t405 = os.path.join(d, 'salida', '_qc_405.png')
    subprocess.run(['ffmpeg', '-v', 'error', '-ss', '%.3f' % (dur * 0.30), '-i', out,
                    '-frames:v', '1', '-y', '_t.png'], check=True)
    Image.open('_t.png').convert('RGB').resize((405, 720), Image.LANCZOS).save(t405)
    os.remove('_t.png')

    m, ok = ritmo.veredicto(out)
    print(json.dumps({k: v for k, v in m.items() if not k.startswith('_')}, indent=1))
    print('  hoja  ->', hoja)
    print('  405px ->', t405)
    print('  RITMO:', 'PASS' if ok else 'FAIL')
    return m, ok


if __name__ == '__main__':
    main(int(sys.argv[1]))
