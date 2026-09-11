# -*- coding: utf-8 -*-
"""Pega la intro y la outro del canal a un episodio terminado.

    python pegar_intro_outro.py 01_aviacion_rusa_v5.mp4            -> 01_aviacion_rusa_v5_canal.mp4
    python pegar_intro_outro.py episodio.mp4 salida.mp4

Re-codifica todo (concat por filtro): es lo unico que garantiza que no haya saltos de audio ni de fps entre
clips. Un episodio de 16 min tarda unos minutos. No toca ningun archivo de entrada.
"""
import os, sys, subprocess
BASE = os.path.dirname(os.path.abspath(__file__))
INTRO = os.path.join(BASE, 'intro_canal.mp4'); OUTRO = os.path.join(BASE, 'outro_canal.mp4')

def pegar(ep, out=None):
    out = out or os.path.splitext(ep)[0] + '_canal.mp4'
    for p in (INTRO, ep, OUTRO):
        if not os.path.exists(p): raise SystemExit('falta ' + p)
    fc = ''.join(f'[{i}:v]scale=1920:1080,fps=24,format=yuv420p[v{i}];[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo[a{i}];' for i in range(3))
    fc += '[v0][a0][v1][a1][v2][a2]concat=n=3:v=1:a=1[v][a]'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', INTRO, '-i', ep, '-i', OUTRO, '-filter_complex', fc, '-map', '[v]', '-map', '[a]',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '19', '-preset', 'medium', '-c:a', 'aac', '-b:a', '192k', out], check=True)
    return out

if __name__ == '__main__':
    ep = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, '01_aviacion_rusa_v5.mp4')
    print('->', pegar(ep, sys.argv[2] if len(sys.argv) > 2 else None))
