# -*- coding: utf-8 -*-
"""Cierre de la pieza: la VOZ pide like y suscripcion sobre una tarjeta a pantalla completa.

    python cierre.py tarjeta     # solo el PNG, para mirarlo (0 creditos)
    python cierre.py voz         # genera audio/cierre.mp3 en fal (~USD 0,01)
    python cierre.py pegar       # lo concatena al final de la pieza ya armada (0 creditos)

Pedido de Agustin (2026-09-11): *"en todos los short haz un breve cierre pidiendo like y suscripcion"*,
y para esta pieza en particular: la pregunta a los comentarios primero y **despues** la outro con el
like y la suscripcion. Va aparte del cuerpo a proposito: meterlo dentro del guion obliga a volver a
pedir la voz entera (USD 0,24) para ganar cinco segundos; asi cuesta un centavo y no se toca nada de
lo que ya estaba alineado.
"""
import json, os, subprocess, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
PROD = os.path.join(RAIZ, 'produccion')
sys.path.insert(0, PROD)
from PIL import Image, ImageDraw
import shorts as SH
from props import TINTA, PAPEL, OCRE, ROJO, FONTC

S = os.path.join(AQUI, 'shorts')
FICHA = json.load(open(os.path.join(S, 'serie.json'), encoding='utf-8'))
P = FICHA['shorts'][0]
D = os.path.join(S, P['dir'])
VOZ_ID = 'JBFqnCBsd6RMkjVDRZzb'          # George, la misma voz del cuerpo

TEXTO = ("[warm, quick] If that was worth your time, hit like and subscribe. "
         "And tell me down there: demographic drift, or political project?")
PANTALLA = ('LIKE  +  SUBSCRIBE', 'MORE ON THE CHANNEL')


def pulgar(w=210):
    """Pulgar arriba de papel. Vive aca y no en props_s03.py: solo existe para este cierre."""
    from props import papel
    h = int(w*1.12)

    def f(d):
        d.rounded_rectangle([w*0.16, h*0.44, w-2, h-2], radius=int(w*0.11), fill=255)
        d.rounded_rectangle([w*0.24, h*0.04, w*0.56, h*0.58], radius=int(w*0.15), fill=255)
        d.rounded_rectangle([2, h*0.58, w*0.30, h-2], radius=int(w*0.08), fill=255)
    q = papel((w+2, h+2), f, PAPEL); d = ImageDraw.Draw(q)
    for k in (0.62, 0.76, 0.90):
        d.line([(w*0.62, h*k), (w*0.92, h*k)], fill=TINTA+(160,), width=4)
    d.line([(w*0.30, h*0.58), (w*0.30, h-6)], fill=TINTA+(120,), width=3)
    return q


def campanita(w=200):
    from props import papel
    h = int(w*1.10)

    def f(d):
        d.pieslice([w*0.06, h*0.10, w*0.94, h*1.02], 180, 360, fill=255)
        d.rectangle([w*0.06, h*0.56, w*0.94, h*0.70], fill=255)
        d.rectangle([w*0.46, h*0.02, w*0.54, h*0.14], fill=255)
        d.ellipse([w*0.42, h*0.72, w*0.58, h*0.90], fill=255)
    q = papel((w+2, h+2), f, OCRE); d = ImageDraw.Draw(q)
    d.line([(w*0.06, h*0.70), (w*0.94, h*0.70)], fill=TINTA+(255,), width=4)
    d.ellipse([w*0.42, h*0.72, w*0.58, h*0.90], outline=TINTA+(255,), width=4)
    return q


def tarjeta():
    im = Image.new('RGBA', (SH.W, SH.H), (0, 0, 0, 0))
    im.alpha_composite(SH.tile(SH.papel_tx, (SH.W, SH.H)) if hasattr(SH, 'papel_tx')
                       else Image.new('RGBA', (SH.W, SH.H), (26, 22, 18, 255)), (0, 0))
    im.alpha_composite(SH.hoja_papel(SH.HW, SH.HH, PAPEL, radio=18), (SH.HX, SH.HY))
    d = ImageDraw.Draw(im)
    cx = SH.HX + SH.HW/2
    d.text((cx, SH.HY+170), 'PAPER TRAIL', fill=TINTA+(255,), font=FONTC(76), anchor='mm')
    d.line([(SH.HX+80, SH.HY+250), (SH.HX+SH.HW-80, SH.HY+250)], fill=TINTA+(120,), width=3)
    pu = pulgar().rotate(-7, resample=Image.BICUBIC, expand=True)
    ca = campanita().rotate(6, resample=Image.BICUBIC, expand=True)
    im.alpha_composite(pu, (int(cx-pu.width-150), SH.HY+360))
    im.alpha_composite(ca, (int(cx+150), SH.HY+370))
    l1, l2 = PANTALLA
    f1 = FONTC(112)
    while SH.medir(l1, f1)[0] > SH.HW-120: f1 = FONTC(f1.size-4)
    d.text((cx, SH.HY+760), l1, fill=TINTA+(255,), font=f1, anchor='mm')
    f2 = FONTC(72)
    while SH.medir(l2, f2)[0] > SH.HW-140: f2 = FONTC(f2.size-3)
    d.text((cx, SH.HY+900), l2, fill=ROJO+(255,), font=f2, anchor='mm')
    d.line([(SH.HX+180, SH.HY+1010), (SH.HX+SH.HW-180, SH.HY+1010)], fill=TINTA+(90,), width=3)
    preg = P.get('pregunta_pantalla', 'TELL ME IN THE COMMENTS')
    f3 = FONTC(56)
    while SH.medir(preg, f3)[0] > SH.HW-160: f3 = FONTC(f3.size-2)
    d.text((cx, SH.HY+1100), preg, fill=TINTA+(220,), font=f3, anchor='mm')
    fi = SH.ficha_marca(74)
    im.alpha_composite(fi, (int(cx-fi.width/2), SH.HY+SH.HH-340))
    d.text((cx, SH.HY+SH.HH-140), 'FOLLOW THE PAPER.', fill=OCRE+(255,), font=FONTC(62), anchor='mm')
    return im.convert('RGB')


def voz():
    import fal_client, requests
    assert os.environ.get('FAL_KEY'), 'sin FAL_KEY en el entorno'
    mp3 = os.path.join(D, 'audio', 'cierre.mp3')
    if os.path.exists(mp3) and os.path.getsize(mp3) > 4000:
        print('ya estaba'); return
    r = fal_client.subscribe('fal-ai/elevenlabs/tts/eleven-v3',
                             arguments={'text': TEXTO, 'voice': VOZ_ID, 'stability': 0.5,
                                        'language_code': 'en'})
    open(mp3, 'wb').write(requests.get(r['audio']['url']).content)
    print('cierre.mp3 %d bytes  (%d chars, ~USD %.3f)'
          % (os.path.getsize(mp3), len(TEXTO), len(TEXTO)/1000*0.10))


def _dur(f):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                 '-of', 'csv=p=0', f], capture_output=True, text=True).stdout.strip())


def pegar():
    pieza = os.path.join(D, 'salida', '%02d_%s.mp4' % (P['n'], P['dir'].split('_', 1)[1]))
    mp3 = os.path.join(D, 'audio', 'cierre.mp3')
    if not os.path.exists(pieza): raise SystemExit('sin pieza armada (corre `python armar.py`)')
    if not os.path.exists(mp3): raise SystemExit('sin cierre.mp3 (corre `python cierre.py voz`)')
    tmp = os.path.join(D, '_cierre'); os.makedirs(tmp, exist_ok=True)
    png = os.path.join(tmp, 'tarjeta.png'); tarjeta().save(png)
    dur = _dur(mp3)+0.55                      # un respiro despues de la ultima palabra
    seg = os.path.join(tmp, 'cierre.mp4')
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                    '-loop', '1', '-framerate', '24', '-t', '%.3f' % dur, '-i', png, '-i', mp3,
                    '-filter_complex',
                    '[0:v]scale=1080:1920,format=yuv420p,fade=t=in:st=0:d=0.25[v];'
                    '[1:a]aformat=sample_rates=48000:channel_layouts=stereo,'
                    'apad=whole_dur=%.3f,volume=1.0[a]' % dur,
                    '-map', '[v]', '-map', '[a]', '-t', '%.3f' % dur,
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
                    '-c:a', 'aac', '-b:a', '192k', seg], check=True)
    out = pieza.replace('.mp4', '_cta.mp4')
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', pieza, '-i', seg,
                    '-filter_complex',
                    '[0:v]scale=1080:1920,fps=24,format=yuv420p[a0];'
                    '[0:a]aformat=sample_rates=48000:channel_layouts=stereo[b0];'
                    '[1:v]scale=1080:1920,fps=24,format=yuv420p[a1];'
                    '[1:a]aformat=sample_rates=48000:channel_layouts=stereo[b1];'
                    '[a0][b0][a1][b1]concat=n=2:v=1:a=1[v][a]',
                    '-map', '[v]', '-map', '[a]', '-c:v', 'libx264', '-preset', 'medium',
                    '-crf', '20', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out],
                   check=True)
    os.replace(out, pieza)
    print('+%.1fs de cierre  ->  %.0f s  (%.1f MB)'
          % (dur, _dur(pieza), os.path.getsize(pieza)/1e6))


if __name__ == '__main__':
    modo = sys.argv[1] if len(sys.argv) > 1 else 'tarjeta'
    if modo == 'voz': voz()
    elif modo == 'pegar': pegar()
    else:
        f = os.path.join(AQUI, '_qc_cierre.jpg')
        tarjeta().resize((432, 768), Image.LANCZOS).save(f, quality=92); print('tarjeta ->', f)
