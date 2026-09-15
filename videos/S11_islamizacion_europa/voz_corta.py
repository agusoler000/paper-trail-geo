# -*- coding: utf-8 -*-
"""Voz del short S11: direccion -> ElevenLabs v3 (George) via fal -> whisper -> tiempos.json.

    python voz_corta.py dirigir     # escribe shorts/01_europa/audio/texto.txt (0 creditos)
    python voz_corta.py generar     # llama a fal (CUESTA ~USD 0,28)
    python voz_corta.py alinear     # whisper -> audio/voz.wav + audio/tiempos.json (0 creditos)

Copia del alineador del ep. 06 (empareja por TEXTO con SequenceMatcher, centro = MEDIANA de los
tokens anclados, red de seguridad de duracion). Esta pieza tiene ocho cifras en 25 lineas: sin esto
el cierre se come la conclusion.
"""
import json, os, re, subprocess, sys
from difflib import SequenceMatcher
from pathlib import Path

AQUI = Path(__file__).resolve().parent
S = AQUI / 'shorts'
FICHA = json.loads((S / 'serie.json').read_text(encoding='utf-8'))
P = FICHA['shorts'][0]
AUD = S / P['dir'] / 'audio'
VOZ_ID = 'JBFqnCBsd6RMkjVDRZzb'          # George
PRE, POST = 0.55, 0.45

APERTURA = "[an editorial voice, steady and clear]"
TAGS = {}


def lineas():
    txt = (S / P['dir'] / 'guion.md').read_text(encoding='utf-8')
    return [l[2:].strip() for l in txt.split('\n') if l.startswith('A: ')]


def dirigir():
    L = lineas()
    out = [APERTURA]
    for i, l in enumerate(L):
        if i in TAGS: out.append(TAGS[i])
        out.append(l)
    AUD.mkdir(parents=True, exist_ok=True)
    t = ' '.join(out)
    (AUD / 'texto.txt').write_text(t, encoding='utf-8')
    pal = sum(len(l.split()) for l in L)
    print('%d lineas  %d palabras  %d chars  ~USD %.2f  ~%.0f s de voz'
          % (len(L), pal, len(t), len(t)/1000*0.10, pal/140*60))


def generar():
    import fal_client, requests
    assert os.environ.get('FAL_KEY'), 'sin FAL_KEY en el entorno'
    mp3 = AUD / 'voz.mp3'
    if mp3.exists() and mp3.stat().st_size > 5000:
        print('ya estaba (%d bytes)' % mp3.stat().st_size); return
    txt = (AUD / 'texto.txt').read_text(encoding='utf-8')
    r = fal_client.subscribe('fal-ai/elevenlabs/tts/eleven-v3',
                             arguments={'text': txt, 'voice': VOZ_ID, 'stability': 0.5,
                                        'language_code': 'en'})
    mp3.write_bytes(requests.get(r['audio']['url']).content)
    print('voz.mp3 %d bytes  (%d chars, ~USD %.2f)' % (mp3.stat().st_size, len(txt), len(txt)/1000*0.10))


def alinear():
    import numpy as np, soundfile as sf
    norm = lambda w: re.sub(r'[^a-z0-9]', '', w.lower())
    sr = 24000
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(AUD/'voz.mp3'), '-ac', '1',
                    '-ar', str(sr), str(AUD/'_raw.wav')], check=True)
    x, _ = sf.read(str(AUD/'_raw.wav')); x = x.astype(np.float32)
    env = np.abs(x); idx = np.where(env > 10**(-45/20))[0]
    if len(idx): x = x[max(0, idx[0]-int(0.05*sr)):min(len(x), idx[-1]+int(0.15*sr))]
    full = np.concatenate([np.zeros(int(PRE*sr), np.float32), x, np.zeros(int(POST*sr), np.float32)])
    full = full/max(1e-6, np.abs(full).max())*0.89
    sf.write(str(AUD/'voz.wav'), full, sr)
    dur = round(len(full)/sr, 3)
    (AUD/'_raw.wav').unlink(missing_ok=True)

    cache = AUD/'_palabras.json'
    if cache.exists():
        words = [tuple(w) for w in json.loads(cache.read_text(encoding='utf-8'))]
        print('palabras del cache: %d' % len(words))
    else:
        from faster_whisper import WhisperModel
        m = WhisperModel('small.en', device='cpu', compute_type='int8')
        segs, _ = m.transcribe(str(AUD/'voz.wav'), word_timestamps=True, beam_size=3, vad_filter=False)
        words = [(norm(w.word), w.start, w.end) for sg in segs for w in sg.words if norm(w.word)]
        cache.write_text(json.dumps(words), encoding='utf-8')
        print('whisper: %d palabras' % len(words))

    L = lineas()
    ini_b, fin_b = PRE*0.5, dur-POST*0.5
    gt = []
    for i, ln in enumerate(L):
        for t in ln.split():
            if norm(t): gt.append((i, norm(t)))
    anc = {}
    if words and gt:
        sm = SequenceMatcher(None, [t for _, t in gt], [w[0] for w in words], autojunk=False)
        for a_, b_, n_ in sm.get_matching_blocks():
            for k in range(n_): anc[a_+k] = (words[b_+k][1], words[b_+k][2])
    cen = {}
    for i in range(len(L)):
        ts = sorted(anc[k][0] for k, (li, _) in enumerate(gt) if li == i and k in anc)
        if ts: cen[i] = ts[len(ts)//2]
    ok = []
    for i in sorted(cen):
        while ok and cen[i] < cen[ok[-1]]-0.05: ok.pop()
        ok.append(i)
    cen = {i: cen[i] for i in ok}
    lim = {}
    for i in sorted(cen):
        prev = max([k for k in cen if k < i], default=None)
        nxt = min([k for k in cen if k > i], default=None)
        a = (cen[prev]+cen[i])/2 if prev is not None else max(ini_b, cen[i]-1.2)
        b = (cen[i]+cen[nxt])/2 if nxt is not None else min(fin_b, cen[i]+1.6)
        lim[i] = (a, b)
    pal = [max(1, len([t for t in ln.split() if norm(t)])) for ln in L]
    for i in range(len(L)):
        if i in lim: continue
        izq = max([k for k in lim if k < i], default=None)
        der = min([k for k in lim if k > i], default=None)
        t0 = lim[izq][1] if izq is not None else ini_b
        t1 = lim[der][0] if der is not None else fin_b
        hueco = [k for k in range(len(L)) if k not in lim
                 and (izq is None or k > izq) and (der is None or k < der)]
        tot = sum(pal[k] for k in hueco) or 1
        t = t0
        for k in hueco:
            d = max(0.30, (t1-t0)*pal[k]/tot); lim[k] = (t, t+d); t += d
    MINL = lambda n: 0.30+0.050*n
    seq = [list(lim[i]) for i in range(len(L))]
    i = 0
    while i < len(seq):
        if seq[i][1]-seq[i][0] >= MINL(pal[i])-1e-3: i += 1; continue
        j = i
        while j+1 < len(seq) and seq[j+1][1]-seq[j+1][0] < MINL(pal[j+1])-1e-3: j += 1
        t0 = seq[i-1][1] if i else ini_b
        t1 = seq[j+1][0] if j+1 < len(seq) else fin_b
        need = sum(MINL(pal[k]) for k in range(i, j+1))
        if t1-t0 < need:
            t0 = max(ini_b, min(t0, t1-need))
            if i: seq[i-1][1] = max(seq[i-1][0]+0.30, t0)
        tot = sum(pal[k] for k in range(i, j+1)) or 1
        t = t0
        for k in range(i, j+1):
            d = max(MINL(pal[k]), (t1-t0)*pal[k]/tot)
            seq[k] = [t, min(t+d, t1)]; t = seq[k][1]
        i = j+1
    out, t_prev = [], ini_b
    for i, ln in enumerate(L):
        ini, fin = seq[i]
        ini = min(max(ini, t_prev, ini_b), fin_b-0.30)
        fin = min(max(fin, ini+0.30), fin_b)
        if i == 0: ini = min(ini, words[0][1] if words else PRE)
        out.append({'i': i, 'texto': ln, 'inicio': round(ini, 3), 'fin': round(fin, 3)})
        t_prev = ini
    json.dump({'lineas': out, 'dur': dur, 'pre': PRE, 'post': POST},
              open(AUD/'tiempos.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    cortas = [o['i'] for o in out if o['fin']-o['inicio'] < 0.55]
    sin_anc = [i for i in range(len(L)) if i not in cen]
    print('dur=%.1fs  lineas=%d  sin anclaje=%s  <0.55s=%s'
          % (dur, len(out), sin_anc or 'ninguna', cortas or 'ninguna'))


if __name__ == '__main__':
    modo = sys.argv[1] if len(sys.argv) > 1 else 'dirigir'
    {'dirigir': dirigir, 'generar': generar, 'alinear': alinear}[modo]()
