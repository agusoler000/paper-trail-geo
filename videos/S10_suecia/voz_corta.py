# -*- coding: utf-8 -*-
"""Voz de la serie S10 («What Sweden Paid For»): direccion de actor -> ElevenLabs v3 (George)
via **PicsArt** -> whisper -> tiempos.json.

    python voz_corta.py dirigir            # las tres piezas -> audio/texto.txt
    python voz_corta.py bajar <n> <url>    # guarda el mp3 que devolvio PicsArt
    python voz_corta.py alinear <n>        # whisper -> tiempos.json

**Por que PicsArt y no fal** (decision de Agustin, 2026-09-14): los creditos de PicsArt ya estan
pagados y resetean el 14-oct (500 disponibles). fal se cobra en USD contra el tope de 4 por
produccion. Mismo modelo (`eleven-v3`), misma voz (George). La contra conocida es que PicsArt
**no devuelve timestamps**; los repone whisper local en `alinear`, que es el mismo camino que ya
usa el motor de fal. La llamada a PicsArt la hace el asistente por MCP (no hay clave en el
entorno), y aca solo entra el mp3 resultante.

**La direccion es distinta en cada pieza, a proposito:**

  - **01 · Momika.** Es un homicidio. Arranca como un informe (lo mas plano posible: el contraste
    lo hace el hecho, no la voz) y solo se quiebra en la linea 1 — «It didn't» — que es el giro de
    la pieza y va sola, despues de un silencio. El cierre es la unica linea lenta.
  - **02 · Ibn Rushd.** Es una cronica de plata publica, y el motor es la **repeticion**: «again,
    and again, and again». Se lee con paciencia de contador, no con indignacion; la indignacion la
    pone el espectador cuando oye «sixteen years» por segunda vez.
  - **03 · Escuelas.** Tiene una bisagra explicita en el medio («That is the part the state can
    reach» / «Here is the part it cannot»). Las dos mitades se leen distinto: la primera es
    administrativa, la segunda baja el volumen.

Regla del canal: tension = bajar la voz, no subirla (`VOZ.md`).
"""
import json, os, re, subprocess, sys
from difflib import SequenceMatcher
from pathlib import Path

AQUI = Path(__file__).resolve().parent
S = AQUI / 'shorts'
FICHA = json.loads((S / 'serie.json').read_text(encoding='utf-8'))
VOZ_ID = 'JBFqnCBsd6RMkjVDRZzb'          # George
PRE, POST = 0.55, 0.45

APERTURA = "[low, a newsroom voice, matter-of-fact]"

# Una tabla por pieza. La clave es el indice de linea A:.
TAGS = {
 0: {                                    # Momika
   1: "[pause] [flat, hard]",
   2: "[slower, each detail landing]",
   3: "[dry]",
   4: "[pause] [slow, each word landing]",
   5: "[quiet, final]",
   6: "[pause] [warmer, direct, asking]",
 },
 1: {                                    # Ibn Rushd
   1: "[patient, itemising]",
   2: "[clipped, procedural]",
   3: "[pause] [slow, each word landing]",
   4: "[dry]",
   5: "[quiet, final]",
   6: "[pause] [warmer, direct, asking]",
 },
 2: {                                    # Escuelas
   1: "[flat]",
   2: "[pause] [lower, slower]",
   3: "[level]",
   4: "[pointed]",
   5: "[pause] [quiet, final]",
   6: "[pause] [warmer, direct, asking]",
 },
}


def pieza(n):
    return FICHA['shorts'][n]


def lineas(n):
    """Las lineas A: del guion. Acepta '**A:** x' y 'A: x'.

    Normaliza el guion NO SEPARABLE (U+2011) a guion comun: los .md lo usan para que
    «twenty-ninth» no se parta al final de un renglon, pero al TTS le llega un caracter raro
    y en la prueba del S03 se comio la palabra. El em-dash si se deja: lo lee como pausa.
    """
    txt = (S / pieza(n)['dir'] / 'guion.md').read_text(encoding='utf-8')
    out = []
    for l in txt.split('\n'):
        l = l.strip()
        m = re.match(r'^\*\*A:\*\*\s+(.+)$', l) or re.match(r'^A:\s+(.+)$', l)
        if m:
            s = m.group(1).replace('\u2011', '-').replace('\u00a0', ' ')
            out.append(re.sub(r'\s+', ' ', s).strip())
    return out


def aud(n):
    return S / pieza(n)['dir'] / 'audio'


def dirigir():
    tot_cr = 0
    for n in range(len(FICHA['shorts'])):
        L = lineas(n)
        out = [APERTURA]
        for i, l in enumerate(L):
            if i in TAGS[n]: out.append(TAGS[n][i])
            out.append(l)
        a = aud(n); a.mkdir(parents=True, exist_ok=True)
        t = ' '.join(out)
        (a / 'texto.txt').write_text(t, encoding='utf-8')
        pal = sum(len(l.split()) for l in L)
        cr = pal / 95 * 3                       # medida de VOZ.md: ~3 creditos por ~95 palabras
        tot_cr += cr
        print('  %d %-18s %2d lineas  %3d palabras  %4d chars  ~%.0f cr  ~%.0f s'
              % (n + 1, pieza(n)['dir'], len(L), pal, len(t), cr, pal / 113 * 60))
    print('  TOTAL ~%.0f creditos PicsArt (saldo 500). En fal habrian sido ~USD %.2f'
          % (tot_cr, tot_cr / 3 * 95 / 140 * 0.10 * 1.4))


def bajar():
    """voz_corta.py bajar <n> <url> — guarda el mp3 que devolvio PicsArt."""
    import requests
    n = int(sys.argv[2]) - 1
    url = sys.argv[3]
    a = aud(n); a.mkdir(parents=True, exist_ok=True)
    mp3 = a / 'voz.mp3'
    mp3.write_bytes(requests.get(url, timeout=120).content)
    print('%s  %d bytes' % (mp3, mp3.stat().st_size))


def alinear():
    import numpy as np, soundfile as sf
    n = int(sys.argv[2]) - 1
    A = aud(n)
    norm = lambda w: re.sub(r'[^a-z0-9]', '', w.lower())
    sr = 24000
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(A/'voz.mp3'), '-ac', '1',
                    '-ar', str(sr), str(A/'_raw.wav')], check=True)
    x, _ = sf.read(str(A/'_raw.wav')); x = x.astype(np.float32)
    env = np.abs(x); idx = np.where(env > 10**(-45/20))[0]
    if len(idx): x = x[max(0, idx[0]-int(0.05*sr)):min(len(x), idx[-1]+int(0.15*sr))]
    full = np.concatenate([np.zeros(int(PRE*sr), np.float32), x, np.zeros(int(POST*sr), np.float32)])
    full = full/max(1e-6, np.abs(full).max())*0.89
    sf.write(str(A/'voz.wav'), full, sr)
    dur = round(len(full)/sr, 3)
    (A/'_raw.wav').unlink(missing_ok=True)

    cache = A/'_palabras.json'
    if cache.exists():
        words = [tuple(w) for w in json.loads(cache.read_text(encoding='utf-8'))]
        print('palabras del cache: %d' % len(words))
    else:
        from faster_whisper import WhisperModel
        m = WhisperModel('small.en', device='cpu', compute_type='int8')
        segs, _ = m.transcribe(str(A/'voz.wav'), word_timestamps=True, beam_size=3, vad_filter=False)
        words = [(norm(w.word), w.start, w.end) for sg in segs for w in sg.words if norm(w.word)]
        cache.write_text(json.dumps(words), encoding='utf-8')
        print('whisper: %d palabras' % len(words))

    L = lineas(n)
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
    MINL = lambda k: 0.30+0.050*k
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
              open(A/'tiempos.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    cortas = [o['i'] for o in out if o['fin']-o['inicio'] < 0.55]
    sin_anc = [i for i in range(len(L)) if i not in cen]
    print('pieza %d  dur=%.1fs  lineas=%d  sin anclaje=%s  <0.55s=%s'
          % (n+1, dur, len(out), sin_anc or 'ninguna', cortas or 'ninguna'))


if __name__ == '__main__':
    modo = sys.argv[1] if len(sys.argv) > 1 else 'dirigir'
    {'dirigir': dirigir, 'bajar': bajar, 'alinear': alinear}[modo]()
