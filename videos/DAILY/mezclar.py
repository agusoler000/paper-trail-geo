# -*- coding: utf-8 -*-
"""Etapa 7 del diario: cuadros + voz + CORTINA -> mp4, y despues intro y outro del canal.

    python videos/DAILY/mezclar.py 2026-09-14

Esto es lo que `DIARIO.md` §5 llama `mezcla`: "voz + cortina + intro/outro". La primera version
del 14 salio con voz sola y sin intro, que es justo lo que Agustin marco.

LA CORTINA
Cues propias de `produccion/musica/cue_*.mp3` (Lyria via PicsArt, sin atribucion obligatoria; ver
`produccion/CREDITOS_MUSICA.md`). Cada una dura ~176 s, asi que para 20 minutos se encadenan varias
con fundido cruzado: repetir una sola siete veces se oye como un loop y cansa.

Receta del canal, medida en `CREDITOS_MUSICA.md`: **cortina 12 dB bajo la voz, ducking -5 dB**.
El ducking se hace con `sidechaincompress` de ffmpeg en vez del `mezcla.ducking` de numpy: el mismo
efecto, pero sin cargar 20 minutos de audio en memoria.

EL ORDEN DE LAS PIEZAS (Agustin, 2026-09-14)
    saludo del dia  ->  intro del canal  ->  programa  ->  outro del canal
El saludo NO es un clip: es el bloque INTRO del guion, con la fecha hablada, y se renderiza con
todo lo demas. Por eso el cuerpo se parte en dos y la intro del canal se mete en el medio, en el
aire que hay entre el saludo y el cold open.

Regla 4 de la skill (decision de Agustin, 2026-09-11): la intro y la outro del canal **van en
todos los videos** y las dos piden LIKE y SUSCRIPCION. Por eso el saludo no las pide: entrarian
dos veces en treinta segundos. Estan en `produccion/intro_canal.mp4` (13,96 s) y
`produccion/outro_canal.mp4` (19,79 s). Cuando el formato tenga las suyas (`DIARIO.md` §11.6), se
cambian esas dos rutas y nada mas.
"""
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(BASE))
MUSICA = os.path.join(RAIZ, "produccion", "musica")
FPS = 24

# Orden de las cues en la cama. No es alfabetico: arranca con la mas sobria (reloj y piano lejano),
# mete las tensas en el medio del programa y cierra con la mas abierta.
CUES = ["cue_01_intro", "cue_02_flota", "cue_05_pais", "cue_04_dron", "cue_06_siberia"]
CRUCE = 4.0          # segundos de fundido cruzado entre cues
BAJO_VOZ_DB = -12.0  # la cortina, antes del ducking
DUCK_DB = -5.0       # cuanto mas baja cuando hay voz


def _dur(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def cama(destino, segundos):
    """Encadena cues con fundido cruzado hasta cubrir `segundos`, y cierra con un fade out."""
    cues = [os.path.join(MUSICA, c + ".mp3") for c in CUES]
    cues = [c for c in cues if os.path.exists(c)]
    if not cues:
        raise SystemExit("no hay cues en %s" % MUSICA)

    # cuantas piezas hacen falta, contando que cada cruce se come CRUCE segundos
    durs = [_dur(c) for c in cues]
    orden, total = [], 0.0
    i = 0
    while total < segundos + 5:
        orden.append(i % len(cues))
        total += durs[i % len(cues)] - (CRUCE if len(orden) > 1 else 0)
        i += 1

    entradas = []
    for k in orden:
        entradas += ["-i", cues[k]]
    fc = ""
    prev = "[0:a]"
    for n in range(1, len(orden)):
        sal = "[x%d]" % n
        fc += "%s[%d:a]acrossfade=d=%.1f:c1=tri:c2=tri%s;" % (prev, n, CRUCE, sal)
        prev = sal
    fc += "%satrim=0:%.3f,afade=t=out:st=%.3f:d=3,aformat=sample_rates=48000:channel_layouts=stereo[out]" % (
        prev, segundos, max(0.0, segundos - 3))
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + entradas +
                   ["-filter_complex", fc, "-map", "[out]", destino], check=True)
    return destino


def _corte_saludo(dia):
    """Segundo en el que termina el bloque INTRO (el saludo) y empieza el resto del programa.

    Ahi va la intro del canal. Agustin, 2026-09-14: el saludo con la fecha va ANTES de la intro
    del canal, en este video y en todos los informativos.
    """
    import json
    g = json.load(open(os.path.join(dia, "guion.json"), encoding="utf-8"))
    fin_intro = 0.0
    inicio_resto = None
    for bl in g["bloques"]:
        if bl["nombre"] == "INTRO":
            fin_intro = max(b["t"] + b["dur"] for b in bl["beats"])
        else:
            t0 = min(b["t"] for b in bl["beats"])
            inicio_resto = t0 if inicio_resto is None else min(inicio_resto, t0)
    if inicio_resto is None or fin_intro <= 0:
        return None
    # a mitad del aire entre el saludo y el cold open: no corta ni una palabra de ninguno
    return (fin_intro + inicio_resto) / 2.0


def _tramo(frames, audio, desde_cuadro, cuadros, desde_seg, dur_seg, destino):
    cmd = ["ffmpeg", "-v", "error", "-y",
           "-start_number", str(desde_cuadro), "-framerate", str(FPS),
           "-i", os.path.join(frames, "f_%06d.jpg"),
           "-ss", "%.4f" % desde_seg]
    if dur_seg is not None:
        cmd += ["-t", "%.4f" % dur_seg]
    cmd += ["-i", audio]
    if cuadros is not None:
        cmd += ["-frames:v", str(cuadros)]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium",
            "-c:a", "aac", "-b:a", "192k", "-shortest", destino]
    subprocess.run(cmd, check=True)
    return destino


def _concat(piezas, destino):
    """Concatena por filtro (re-codifica): es lo unico que garantiza que no haya saltos de audio
       ni de fps entre piezas que vienen de origenes distintos."""
    entradas = []
    for p in piezas:
        entradas += ["-i", p]
    fc = "".join("[%d:v]scale=1920:1080,fps=%d,format=yuv420p[v%d];"
                 "[%d:a]aformat=sample_rates=48000:channel_layouts=stereo[a%d];"
                 % (i, FPS, i, i, i) for i in range(len(piezas)))
    fc += "".join("[v%d][a%d]" % (i, i) for i in range(len(piezas)))
    fc += "concat=n=%d:v=1:a=1[v][a]" % len(piezas)
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + entradas +
                   ["-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "192k", destino], check=True)
    return destino


def mezclar(fecha, con_musica=True):
    dia = os.path.join(BASE, "_dias", fecha)
    frames = os.path.join(BASE, "_frames_%s" % fecha)
    voz = os.path.join(dia, "voz.wav")

    dur = _dur(voz)
    print("voz: %.1f s" % dur, flush=True)

    # --- 1. la banda de sonido del cuerpo: voz + cortina
    audio = os.path.join(dia, "_audio.m4a")
    if con_musica:
        bed = cama(os.path.join(dia, "_cortina.wav"), dur)
        print("cortina: %s" % bed, flush=True)
        fc = ("[1:a]volume=%.1fdB[m];"
              "[m][0:a]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=700:"
              "makeup=1:detection=rms[mduck];"
              "[0:a][mduck]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
              "alimiter=limit=0.97[a]" % BAJO_VOZ_DB)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", voz, "-i", bed,
                        "-filter_complex", fc, "-map", "[a]",
                        "-c:a", "aac", "-b:a", "192k", audio], check=True)
    else:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", voz,
                        "-c:a", "aac", "-b:a", "192k", audio], check=True)

    # --- 2. el cuerpo, partido donde termina el saludo
    corte = _corte_saludo(dia)
    intro = os.path.join(RAIZ, "produccion", "intro_canal.mp4")
    outro = os.path.join(RAIZ, "produccion", "outro_canal.mp4")
    for p in (intro, outro):
        if not os.path.exists(p):
            raise SystemExit("falta " + p)

    if corte is None:
        cuerpo = _tramo(frames, audio, 0, None, 0.0, None, os.path.join(dia, "_cuerpo.mp4"))
        piezas = [intro, cuerpo, outro]
    else:
        ncorte = int(round(corte * FPS))
        print("saludo: 0 -> %.2f s (%d cuadros); la intro del canal entra ahi" % (corte, ncorte),
              flush=True)
        p1 = _tramo(frames, audio, 0, ncorte, 0.0, corte, os.path.join(dia, "_p1_saludo.mp4"))
        p2 = _tramo(frames, audio, ncorte, None, corte, None, os.path.join(dia, "_p2_cuerpo.mp4"))
        piezas = [p1, intro, p2, outro]

    # --- 3. saludo -> intro del canal -> programa -> outro del canal
    final = _concat(piezas, os.path.join(dia, "video.mp4"))
    print("FINAL: %s (%.1f s, %.1f MB)"
          % (final, _dur(final), os.path.getsize(final) / 1e6), flush=True)
    return final


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("uso: python videos/DAILY/mezclar.py <fecha> [--sin-musica]")
    mezclar(sys.argv[1], con_musica="--sin-musica" not in sys.argv)
