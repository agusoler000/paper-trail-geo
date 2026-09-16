# -*- coding: utf-8 -*-
"""Alineacion del ep. 13. Misma logica que `voz/alinear.py`, con las rutas de la produccion.

Por que no se usa `voz/alinear.py` directamente: espera cabeceras `## BEAT` en el guion y deduce el
directorio de salida con `parents[2]`, que es el reparto viejo (`guiones/` + `produccion/` planos).
Aqui los beats ya estan partidos en `texto/beat_NN_*.txt`, en el mismo orden que los mp3.

    python videos/13_yemen/audio/alinear13.py

Salida en este mismo directorio:
  13_yemen_eleven_brian.wav            voz entera (pre-roll 1 s, 1,5 s entre beats, post-roll 8 s)
  13_yemen_eleven_brian.tiempos.json   beats y lineas con inicio/fin
  _palabras.json                       palabra a palabra, para `Scene.subtitulos()` del motor v4
"""
import json, re, subprocess, sys
from pathlib import Path
import numpy as np, soundfile as sf

AQUI = Path(__file__).resolve().parent
VOZ = 'eleven_brian'
PAUSA_BEAT, PRE, POST = 1.5, 1.0, 8.0
SR = 24000


def norm(w):
    return re.sub(r'[^a-z0-9]', '', w.lower())


def leer_beats():
    """Los beats, en orden, desde texto/beat_NN_*.txt. Cada parrafo es una linea A: del guion."""
    out = []
    for f in sorted((AQUI / 'texto').glob('beat_*.txt')):
        lineas = [l.strip() for l in f.read_text(encoding='utf-8').split('\n\n') if l.strip()]
        out.append({'titulo': f.stem, 'lineas': lineas})
    return out


def main():
    beats = leer_beats()
    print(f'{len(beats)} beats, {sum(len(b["lineas"]) for b in beats)} lineas')

    # 1) concatenar los mp3 con la pausa de beat, recortando silencios de punta
    audio = [np.zeros(int(PRE * SR), np.float32)]
    t = PRE
    for bi, b in enumerate(beats):
        mp3 = AQUI / 'dirigido' / f'beat_{bi:02d}.mp3'
        wav = AQUI / 'dirigido' / f'beat_{bi:02d}.wav'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(mp3),
                        '-ac', '1', '-ar', str(SR), str(wav)], check=True)
        x, _ = sf.read(str(wav))
        x = x.astype(np.float32)
        env = np.abs(x)
        idx = np.where(env > 10 ** (-45 / 20))[0]
        if len(idx):
            x = x[max(0, idx[0] - int(0.05 * SR)):min(len(x), idx[-1] + int(0.15 * SR))]
        if bi:
            audio.append(np.zeros(int(PAUSA_BEAT * SR), np.float32)); t += PAUSA_BEAT
        b['inicio'] = round(t, 3)
        audio.append(x); t += len(x) / SR
        b['fin'] = round(t, 3)
    audio.append(np.zeros(int(POST * SR), np.float32))
    full = np.concatenate(audio)
    full = full / max(1e-6, np.abs(full).max()) * 0.89
    stem = AQUI / f'13_yemen_{VOZ}'
    sf.write(str(stem) + '.wav', full, SR)
    dur = len(full) / SR
    print(f'wav: {dur/60:.2f} min')

    # 2) whisper con timestamps por palabra
    from faster_whisper import WhisperModel
    m = WhisperModel('small.en', device='cpu', compute_type='int8')
    segs, _ = m.transcribe(str(stem) + '.wav', word_timestamps=True, beam_size=3, vad_filter=False)
    words = [(norm(w.word), w.start, w.end, w.word.strip()) for s in segs for w in s.words if norm(w.word)]
    print('palabras reconocidas', len(words))

    # 3) asignar palabras a lineas, beat por beat
    tiempos = []
    for bi, b in enumerate(beats):
        bw = [w for w in words if b['inicio'] - 0.3 <= w[1] <= b['fin'] + 0.3]
        n_total = sum(len(l.split()) for l in b['lineas'])
        k = 0
        for li, l in enumerate(b['lineas']):
            frac = len(l.split()) / n_total
            j0 = min(len(bw) - 1, round(k))
            j1 = max(j0, min(len(bw) - 1, round(k + frac * len(bw)) - 1))
            last = norm(l.split()[-1])
            for jj in range(max(j0, j1 - 3), min(len(bw), j1 + 4)):
                if bw[jj][0] == last:
                    j1 = jj; break
            ini = bw[j0][1] if bw else b['inicio']
            fin = bw[j1][2] if bw else b['fin']
            tiempos.append({'beat': bi, 'linea': li, 'texto': l,
                            'inicio': round(ini, 3), 'fin': round(fin, 3)})
            k = j1 + 1

    json.dump({'voz': VOZ, 'duracion': round(dur, 2),
               'beats': [{'titulo': b['titulo'], 'inicio': b['inicio'], 'fin': b['fin']} for b in beats],
               'lineas': tiempos},
              open(str(stem) + '.tiempos.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    # 4) palabra a palabra, para los subtitulos del motor v4
    json.dump([{'w': w[3], 't0': round(w[1], 3), 't1': round(w[2], 3)} for w in words],
              open(AQUI / '_palabras.json', 'w', encoding='utf-8'), indent=0, ensure_ascii=False)

    # 5) control: ninguna linea por debajo de 0,3 s (§2.3)
    cortas = [x for x in tiempos if x['fin'] - x['inicio'] < 0.3]
    print(f'lineas < 0,3 s: {len(cortas)}')
    for c in cortas[:10]:
        print(f"   beat {c['beat']} linea {c['linea']}: {c['fin']-c['inicio']:.2f}s  {c['texto'][:60]}")
    print(f'OK -> {stem}.wav / .tiempos.json / _palabras.json')


if __name__ == '__main__':
    main()
