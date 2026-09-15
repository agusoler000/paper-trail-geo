# -*- coding: utf-8 -*-
"""Arma la pieza vertical: mete el cuerpo 16:9 en la hoja de 1080x1920 con gancho fijo, subtitulos
quemados, barra de progreso ocre, sello PART n OF 3, cortina y tarjeta final.

    python armar.py 1            # -> shorts/01_momika/salida/01_momika.mp4
    python armar.py 1 --frame    # solo un cuadro de control, antes de gastar el render

Copia del armador del S05 con los dos cambios que pide el **modo B** (serie, `canal/SHORTS.md` §3):

  - **Con sello `PART n OF 3`**, misma esquina y misma tipografia en las tres: es lo que hace que
    se lea como serie en el feed y lo que hace que alguien busque las otras (§3.4).
  - **La tarjeta final cambia por pieza**: las dos primeras mandan a la siguiente (`PART 2 NOW`),
    y la ultima **manda al canal** — `FOLLOW THE PAPER` + SUBSCRIBE. Eso ultimo es el
    cambio del 2026-09-14 (`canal/ENFOQUE_VISTAS_SUBS_2026-09-14.md` §3.1): el outro tiene que
    entregar algo, no pedirlo. El pais sale de `serie.json` -> `siguiente.pais`.

Reusa el compositor de `produccion/shorts.py`. La cortina es una cue de Lyria ya paga: 0 creditos.
"""
import json, os, sys, shutil, subprocess
AQUI = os.path.dirname(os.path.abspath(__file__))
PROD = os.path.abspath(os.path.join(AQUI, '..', '..', 'produccion'))
sys.path.insert(0, PROD)
from PIL import Image, ImageDraw
import shorts as SH
from props import TINTA, PAPEL, OCRE, ROJO, FONTC

S = os.path.join(AQUI, 'shorts')
FICHA = json.load(open(os.path.join(S, 'serie.json'), encoding='utf-8'))
CUE = 'cue_04_dron'          # cue propia (Lyria), ya paga; tensa y sin melodia que compita con la voz
N_PIEZAS = FICHA['piezas']


def pieza(n):
    for s in FICHA['shorts']:
        if s['n'] == n: return s
    raise SystemExit('pieza %s no existe' % n)


_FRENTE_ORIG = SH.frente          # se guarda ANTES de pisarlo: `frente_con_sello` lo necesita,
                                  # y si llamara a SH.frente ya pisado se llamaria a si mismo.


def frente_con_sello(n):
    """Linea de tinta del bloque + sello `PART n OF 3` pegado ARRIBA del bloque, a la izquierda.

    Va sobre la hoja y no dentro del video: el cuerpo 16:9 entra completo (regla 1, nada cortado)
    y cualquier cosa encima lo taparia. Arriba del bloque hay hoja libre entre el gancho y el
    video, que es donde vive."""
    im = _FRENTE_ORIG()
    d = ImageDraw.Draw(im)
    txt = 'PART %d OF %d' % (n, N_PIEZAS)
    f = FONTC(40)
    tw, th = SH.medir(txt, f)
    pad_x, pad_y = 26, 14
    x0, y0 = SH.VX + 4, SH.VY - th - pad_y*2 - 16
    chip = SH.hoja_papel(tw + pad_x*2, th + pad_y*2, PAPEL, radio=9)
    ImageDraw.Draw(chip).text(((tw + pad_x*2)/2, (th + pad_y*2)/2), txt,
                              fill=ROJO + (255,), font=f, anchor='mm')
    im.alpha_composite(chip, (int(x0), int(max(0, y0))))
    return im


def cta_serie(n):
    """Tarjeta final. Las dos primeras encadenan; la tercera entrega el pais siguiente."""
    if n < N_PIEZAS:
        lineas = ['PART %d' % (n+1), 'IS UP NOW']
        color_2 = TINTA
    else:
        sig = (FICHA.get('siguiente') or {}).get('pais') or 'MORE'
        lineas = ['%s IS NEXT.' % sig, 'SUBSCRIBE']
        color_2 = ROJO

    def build():
        f1 = FONTC(84); f2 = FONTC(84)
        w = max(SH.medir(lineas[0], f1)[0], SH.medir(lineas[1], f2)[0]) + 110
        h = 84*2 + 190
        p = SH.hoja_papel(w, h, PAPEL, radio=16); d = ImageDraw.Draw(p)
        d.text((w/2, 88), lineas[0], fill=TINTA + (255,), font=f1, anchor='mm')
        d.text((w/2, 88+96), lineas[1], fill=color_2 + (255,), font=f2, anchor='mm')
        d.text((w/2, h-74), 'PAPER TRAIL', fill=OCRE + (255,), font=FONTC(58), anchor='mm')
        return p
    return build


def musica(mp4):
    """Cortina por debajo de la voz y renormalizado a -14 LUFS. 0 creditos: la cue ya estaba paga."""
    cue = os.path.join(PROD, 'musica', CUE+'.mp3')
    if not os.path.exists(cue):
        print('    sin cue, queda sin cortina'); return mp4
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                '-of', 'csv=p=0', mp4], capture_output=True, text=True).stdout.strip())
    tmp = mp4.replace('.mp4', '_m.mp4')
    fil = ("[1:a]atrim=0:%.3f,asetpts=N/SR/TB,volume=0.115,afade=t=in:st=0:d=1.6,"
           "afade=t=out:st=%.3f:d=1.9[m];"
           "[0:a][m]amix=inputs=2:duration=first:dropout_transition=0,"
           "loudnorm=I=-14:TP=-1.5:LRA=11[a]") % (dur, max(0.1, dur-1.9))
    r = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', mp4, '-i', cue,
                        '-filter_complex', fil, '-map', '0:v', '-c:v', 'copy', '-map', '[a]',
                        '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', tmp],
                       capture_output=True, text=True)
    if r.returncode: print('    cortina fallo:', r.stderr[-300:]); return mp4
    os.replace(tmp, mp4); return mp4


def armar(n, solo_frame=False):
    P = pieza(n)
    d = os.path.join(S, P['dir'])
    cuerpo = os.path.join(d, 'salida', 'cuerpo.mp4')
    if not os.path.exists(cuerpo):
        raise SystemExit('falta cuerpo.mp4: corre `python coreo.py render %d`' % n)
    T = json.load(open(os.path.join(d, 'audio', 'tiempos.json'), encoding='utf-8'))
    cfg = {'master': cuerpo, 'tiempos': os.path.join(d, 'audio', 'tiempos.json')}
    Sd = {'id': '%02d' % P['n'], 'slug': P['dir'].split('_', 1)[1], 'l0': 0, 'l1': len(T['lineas'])-1,
          'hook': P['hook'], 'rojo': P.get('rojo'), 'resaltar': P.get('resaltar', []),
          'pre': 0.0, 'post': 0.35}
    SH.tarjeta_cta = cta_serie(n)
    SH.frente = lambda: frente_con_sello(n)
    tmp = os.path.join(d, '_tmp'); os.makedirs(tmp, exist_ok=True)
    out = os.path.join(d, 'salida')
    try:
        r = SH.construir('S12_recibos', cfg, Sd, tmp, out, solo_frame=solo_frame)
    finally:
        SH.frente = _FRENTE_ORIG
    shutil.rmtree(tmp, ignore_errors=True)
    if not solo_frame: musica(r)
    print('%s  (%.1f MB)' % (os.path.basename(r), os.path.getsize(r)/1e6))
    return r


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    n = int(args[0]) if args else 1
    armar(n, '--frame' in sys.argv)
