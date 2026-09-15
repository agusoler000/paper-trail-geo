# -*- coding: utf-8 -*-
"""Arma la INTRO v3 del canal: tres planos generados con Luma Flash 2 + voz George + cortina del canal.

    python produccion/intro_v3/armar.py

Los planos NO se dibujan por codigo (decision de Agustin, 2026-09-15): son video generado. Lo unico que
hace este script es cortar, pegar, mezclar y normalizar, que es trabajo de montaje, no de dibujo.

Los cortes estan anclados a los tiempos de la voz (`audio/voz_v3.json`, timestamps por caracter):

    0.35  Every border. Every war. Every deal.   -> PLANO 1  el mundo
    4.55  Someone paid for it.                   -> PLANO 2  elecciones y economia
    6.28  This is Paper Trail.                   -> PLANO 3  el memo, cae el sello
    7.77  We show you the receipt.                  la cifra bajo la tachadura
   10.21  Like, subscribe, follow the paper.        los sellos LIKE y SUBSCRIBE

Por que cada plano sale de donde sale:
  P1  se uso la SEGUNDA toma: la primera metia una mancha oscura sobre Europa a mitad del clip.
  P2  se uso la PRIMERA toma y solo sus primeros 1,8 s: despues empiezan a volar papeles solos.
      La segunda toma fue peor (una masa negra cruza el cuadro), asi que se descarto entera.
  P3  primera toma, entera menos los 0,8 s iniciales de hoja quieta, para que el sello caiga sobre
      la frase "This is Paper Trail" y no despues.
"""
import os, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
PROD = os.path.dirname(AQUI)
CLIPS = os.path.join(AQUI, 'clips')
AUDIO = os.path.join(AQUI, 'audio')
SALIDA = os.path.join(AQUI, 'intro_canal_v3.mp4')

VOZ = os.path.join(AUDIO, 'voz_v3.mp3')
MUSICA = os.path.join(PROD, 'musica', 'tema_canal.mp3')
# La ficha del canal recortada en redondo con alfa. OJO: `canal/out/marca_agua_150.png` NO sirve,
# esta vacia (el circulo ocre sin el nombre). Esta sale del avatar_A, que si lleva PAPER TRAIL.
LOGO = os.path.join(os.path.dirname(PROD), 'canal', 'out', 'logo_marca.png')

DUR = 12.50            # la voz mide 12,43; se deja una cola corta
CONGELADO_DESDE = 10.66

PLANOS = [
    # archivo,              desde, hasta   -> donde cae en la linea de tiempo
    ('P1_mundo_v2.mp4',      0.00, 4.45),  # 0,00 - 4,45
    ('P2_urna.mp4',          0.00, 1.80),  # 4,45 - 6,25
    ('P3_memo.mp4',          0.80, 5.21),  # 6,25 - 10,66  (+ congelado hasta 12,50)
]

LUFS = -19             # el nivel de los episodios (INTRO_OUTRO.md)
MUS_DB = -13           # cortina por debajo de la voz
PAD = DUR - CONGELADO_DESDE

LOGO_PX = 124          # diametro del logo sobre 1920x1080
LOGO_MARGEN = 56       # separacion del borde, arriba a la derecha
LOGO_OP = 0.88         # algo por debajo de opaco para que no compita con el sello del final


def corre(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-2500:], file=sys.stderr)
        raise SystemExit(f'ffmpeg fallo: {cmd[:6]}')
    return r


def main():
    for f in [VOZ, MUSICA] + [os.path.join(CLIPS, p[0]) for p in PLANOS]:
        if not os.path.exists(f):
            raise SystemExit(f'falta {f}')

    tmp = os.path.join(AQUI, '_tmp')
    os.makedirs(tmp, exist_ok=True)
    partes = []

    # 1. cada plano recortado y re-encodeado igual, para que concat no se queje
    for i, (arch, a, b) in enumerate(PLANOS):
        out = os.path.join(tmp, f'p{i}.mp4')
        corre(['ffmpeg', '-v', 'error', '-y', '-ss', str(a), '-to', str(b),
               '-i', os.path.join(CLIPS, arch),
               '-vf', 'scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=24',
               '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-an', out])
        partes.append(out)

    # 2. el congelado final: el ultimo cuadro del plano 3, que ya tiene el sello y LIKE/SUBSCRIBE puestos
    ultimo = os.path.join(tmp, 'ultimo.png')
    corre(['ffmpeg', '-v', 'error', '-y', '-sseof', '-0.1', '-i', partes[-1],
           '-frames:v', '1', '-update', '1', ultimo])
    cola = os.path.join(tmp, 'cola.mp4')
    corre(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-t', f'{PAD:.3f}', '-i', ultimo,
           '-vf', 'fps=24,scale=1920:1080', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17',
           '-pix_fmt', 'yuv420p', '-an', cola])
    partes.append(cola)

    # 3. pegado
    lista = os.path.join(tmp, 'lista.txt')
    with open(lista, 'w', encoding='utf-8') as fh:
        for p in partes:
            fh.write(f"file '{p.replace(os.sep, '/')}'\n")
    mudo = os.path.join(tmp, 'mudo.mp4')
    corre(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lista,
           '-c', 'copy', mudo])

    # 4. mezcla: voz + cortina con ducking, normalizada al nivel de los episodios
    # ojo: las etiquetas NO pueden llamarse [v] ni [a] sueltas dentro del grafo — ffmpeg las lee como
    # especificadores de stream ("Stream specifier 'v' matches no streams") y el grafo no compila.
    # La voz se usa dos veces (como cadena lateral del ducking y como mezcla), asi que va con asplit.
    # El logo va en el mismo filter_complex que el audio: no se puede usar -vf a la vez que un
    # -filter_complex que toca el video.
    filtro = (
        f'[3:v]scale={LOGO_PX}:{LOGO_PX},format=rgba,colorchannelmixer=aa={LOGO_OP}[logo];'
        f'[0:v][logo]overlay=W-w-{LOGO_MARGEN}:{LOGO_MARGEN}:format=auto[conlogo];'
        f'[conlogo]fade=t=in:st=0:d=0.35,fade=t=out:st={DUR-0.25:.2f}:d=0.25[vid];'
        f'[1:a]atrim=0:{DUR},asetpts=N/SR/TB,asplit=2[voz1][voz2];'
        f'[2:a]atrim=0:{DUR},asetpts=N/SR/TB,volume={MUS_DB}dB,'
        f'afade=t=in:st=0:d=0.8,afade=t=out:st={DUR-2.2:.2f}:d=2.2[mus];'
        f'[mus][voz1]sidechaincompress=threshold=0.05:ratio=6:attack=15:release=320[ducked];'
        f'[ducked][voz2]amix=inputs=2:duration=first:dropout_transition=0,'
        f'loudnorm=I={LUFS}:TP=-1.5:LRA=11[mezcla]'
    )
    corre(['ffmpeg', '-v', 'error', '-y', '-i', mudo, '-i', VOZ, '-i', MUSICA, '-i', LOGO,
           '-filter_complex', filtro, '-map', '[vid]', '-map', '[mezcla]',
           '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-shortest', SALIDA])
    # -ar 48000 es obligatorio: loudnorm devuelve 96 kHz por su cuenta y despues el concat con el
    # episodio se pelea con el cambio de frecuencia.

    d = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                        '-of', 'csv=p=0', SALIDA], capture_output=True, text=True).stdout.strip()
    print(f'{SALIDA}  {float(d):.2f} s  {os.path.getsize(SALIDA)/1048576:.1f} MB')


if __name__ == '__main__':
    main()
