# -*- coding: utf-8 -*-
"""Arma la pieza vertical: mete el cuerpo 16:9 en la hoja de papel de 1080x1920 con gancho fijo,
subtitulos quemados, barra de progreso ocre, cortina propia y tarjeta final de suscripcion.

    python armar.py            # -> shorts/01_aviso/salida/01_aviso.mp4
    python armar.py --frame    # solo un cuadro de control, antes de gastar el render

Copia del armador de la S02 con los dos cambios que pide el **modo C** (short suelto, `canal/SHORTS.md`):

  - **Sin sello `PART n OF N`**: no es una serie, asi que `SH.frente` queda como esta.
  - **La tarjeta que cierra el cuerpo es solo la marca** (`PAPER TRAIL · FOLLOW THE PAPER.`): el
    pedido de like y suscripcion va en la tarjeta de `cierre.py`, que viene justo despues y lleva la
    voz encima. Dos carteles casi iguales seguidos se anulaban.

Reusa el compositor de `produccion/shorts.py` (mismo lienzo, misma tipografia, mismas trampas ya
resueltas). La cortina es una cue propia de Lyria ya pagada: 0 creditos (regla 9 y regla 19).
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
P = FICHA['shorts'][0]
CUE = 'cue_04_dron'          # cue propia (Lyria), ya paga; tensa y sin melodia que compita con la voz


def cta_suelto():
    """Tarjeta que cierra el cuerpo: **solo la marca**.

    La version obvia era repetir SUBSCRIBE aca, pero inmediatamente despues va la tarjeta de
    `cierre.py`, que dice LIKE + SUBSCRIBE **con la voz encima** — se veian dos carteles casi iguales
    seguidos y el segundo, que es el que tiene voz, perdia fuerza. Asi el orden queda como lo pidio
    Agustin: la pregunta a los comentarios (en el cuerpo), el sello del canal, y recien despues el
    pedido de like y suscripcion."""
    def build():
        f1 = FONTC(104); f2 = FONTC(52)
        w = max(SH.medir('PAPER TRAIL', f1)[0], SH.medir('FOLLOW THE PAPER.', f2)[0]) + 130
        p = SH.hoja_papel(w, 320, PAPEL, radio=16); d = ImageDraw.Draw(p)
        d.text((w/2, 112), 'PAPER TRAIL', fill=TINTA+(255,), font=f1, anchor='mm')
        d.line([(70, 176), (w-70, 176)], fill=TINTA+(110,), width=3)
        d.text((w/2, 226), 'FOLLOW THE PAPER.', fill=OCRE+(255,), font=f2, anchor='mm')
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


def armar(solo_frame=False):
    d = os.path.join(S, P['dir'])
    cuerpo = os.path.join(d, 'salida', 'cuerpo.mp4')
    if not os.path.exists(cuerpo): raise SystemExit('falta cuerpo.mp4: corre `python coreo.py render 1`')
    T = json.load(open(os.path.join(d, 'audio', 'tiempos.json'), encoding='utf-8'))
    cfg = {'master': cuerpo, 'tiempos': os.path.join(d, 'audio', 'tiempos.json')}
    Sd = {'id': '%02d' % P['n'], 'slug': P['dir'].split('_', 1)[1], 'l0': 0, 'l1': len(T['lineas'])-1,
          'hook': P['hook'], 'rojo': P.get('rojo'), 'resaltar': P.get('resaltar', []),
          'pre': 0.0, 'post': 0.35}
    SH.tarjeta_cta = cta_suelto()
    tmp = os.path.join(d, '_tmp'); os.makedirs(tmp, exist_ok=True)
    out = os.path.join(d, 'salida')
    r = SH.construir('S11_islamizacion_europa', cfg, Sd, tmp, out, solo_frame=solo_frame)
    shutil.rmtree(tmp, ignore_errors=True)
    if not solo_frame: musica(r)
    print('%s  (%.1f MB)' % (os.path.basename(r), os.path.getsize(r)/1e6))
    return r


if __name__ == '__main__':
    armar('--frame' in sys.argv)
