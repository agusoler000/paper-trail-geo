# -*- coding: utf-8 -*-
"""Voz de la serie S12 («THE RECEIPT», tanda del 2026-09-15): direccion de actor -> ElevenLabs
v3 (George) -> tiempos.json.

    python voz_corta.py dirigir            # las cuatro piezas -> audio/texto.txt
    python voz_corta.py generar <n>        # llama a FAL (CUESTA) y guarda voz.mp3 + voz.json
    python voz_corta.py bajar <n> <url>    # guarda el mp3 que devolvio PicsArt (0 USD)
    python voz_corta.py alinear <n>        # tiempos.json (de voz.json si esta; si no, whisper)

**Las dos vias, y cuando conviene cada una** (`reference-dos-vias-de-voz`):

  - **PicsArt** (`bajar`): los creditos ya estan pagados y resetean el 14-oct, asi que no toca el
    tope de USD 4 por produccion. La contra es que **no devuelve timestamps** y hay que reponerlos
    con whisper local (minutos de CPU y los numeros transcritos como digitos).
  - **fal** (`generar`): cuesta unos centavos por pieza y devuelve la alineacion caracter a
    caracter (`timestamps: True`). `alinear` la usa tal cual y no corre whisper, y las palabras son
    LAS DEL GUION, no las que oyo una transcripcion.

Mismo modelo (`eleven-v3`) y misma voz (George) en las dos. La clave de fal sale de `FAL_KEY` del
entorno, igual que en `videos/09_deuda_eeuu/voz_ep.py`.

**La direccion es distinta en cada pieza, a proposito:**

  - **01 · El tanque.** Es un inventario. Se lee como un parte de existencias, lo mas plano posible,
    y solo se quiebra en la linea 3 — «The price went up seventeen percent» — que es la unica frase
    corta del guion y el giro entero de la pieza. Va sola, despues de un silencio.
  - **02 · Hormuz.** Es un mecanismo, y se lee como quien explica como funciona una maquina:
    paciente, sin prisa, sin subrayar. El remate («It only had to make them uninsurable») baja el
    volumen en vez de subirlo, que es la regla del canal.
  - **03 · Los hoteles.** Es contabilidad. Paciencia de auditor durante seis lineas; «Same
    contracts. Same ten years.» va cortada y seca; y la linea 6 cambia de registro a propósito
    —directa, a camara— porque es la que separa esta pieza del otro debate.
  - **04 · Ceuta.** Es una cronologia. La linea 2 es la mas importante de las cuatro piezas (lo que
    el tribunal NO hizo) y va lenta y precisa: si esa frase se lee rapido, la pieza afirma algo
    falso. El cierre es el mas bajo de la tanda.

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
sys.path.insert(0, str(AQUI.parent.parent / 'voz'))
import timestamps as TS

# La direccion de actor vive en `direccion_s12.py` (v2, 2026-09-15). La v1 que estaba aca abria
# las cuatro piezas con [flat/low/dry] y pedia "lo mas plano posible": para un short de 90 s en el
# feed eso es letal, y `voz/prosodia.py` lo midio en el ep. 09 (0,99 st entre frases, 3,5 dB de
# rango). La v2 alterna familias de etiqueta y solo enfria la cifra.
from direccion_s12 import APERTURA, TAGS


def _fundir(apertura, tag):
    """Une la etiqueta de apertura con la de la linea 0 en UN solo corchete, sin repetir palabras.

    Cuanto mas corta, menos probable es que el modelo la lea en voz alta; por eso se quita lo que
    ya diga la apertura y se corta en 96 caracteres."""
    dentro = lambda s_: s_.strip()[1:-1].strip() if s_ and s_.strip().startswith('[') else (s_ or '')
    a = dentro(apertura); b = dentro(tag)
    if not b: return '[%s]' % a
    ya = {w.strip('.,;') for w in a.lower().split()}
    b2 = ', '.join(tr for tr in [t.strip() for t in b.split(',')]
                   if tr and tr.split()[0].lower().strip('.,;') not in ya)
    j = a if not b2 else '%s, %s' % (a, b2)
    if len(j) > 96: j = j[:96].rsplit(',', 1)[0]
    return '[%s]' % j


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
        out = []
        for i, l in enumerate(L):
            tag = TAGS[n].get(i)
            if i == 0:
                # UNA SOLA ETIQUETA AL ABRIR. Con dos corchetes seguidos al principio, eleven-v3
                # a veces los LEE EN VOZ ALTA en vez de interpretarlos: medido el 2026-09-15 en la
                # primera tanda: la pieza 1 gasto 6,0 s y la 3 gasto 1,2 s de audio a -16 dBFS
                # (nivel de habla) diciendo las etiquetas antes de la primera palabra del guion.
                # Las piezas 2 y 4, con la misma estructura, salieron limpias: no es determinista,
                # asi que no se puede "probar y ya". Fundidas en un solo corchete, y corto.
                out.append(_fundir(APERTURA[n], tag))
                tag = None
            if tag: out.append(tag)
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


def generar():
    """voz_corta.py generar <n> — pide la pieza a fal con timestamps. **CUESTA** (~USD 0,03).

    Guarda `audio/voz.mp3` y `audio/voz.json` (la respuesta completa, con la alineacion caracter a
    caracter). Con ese json, `alinear` no corre whisper."""
    import fal_client, requests
    assert os.environ.get('FAL_KEY'), 'sin FAL_KEY en el entorno'
    n = int(sys.argv[2]) - 1
    a = aud(n); a.mkdir(parents=True, exist_ok=True)
    txt = (a / 'texto.txt').read_text(encoding='utf-8')
    r = fal_client.subscribe('fal-ai/elevenlabs/tts/eleven-v3',
                             arguments={'text': txt, 'voice': VOZ_ID, 'timestamps': True,
                                        'stability': 0.5, 'language_code': 'en'})
    (a / 'voz.mp3').write_bytes(requests.get(r['audio']['url']).content)
    (a / 'voz.json').write_text(json.dumps(r), encoding='utf-8')
    print('pieza %d: %d chars -> %s (%d bytes)%s'
          % (n + 1, len(txt), a / 'voz.mp3', (a / 'voz.mp3').stat().st_size,
             '  con timestamps' if TS.hay(str(a / 'voz.json')) else '  SIN timestamps: cae a whisper'))


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
    recorte = 0.0
    if len(idx):
        i0 = max(0, idx[0]-int(0.05*sr)); recorte = i0/sr
        x = x[i0:min(len(x), idx[-1]+int(0.15*sr))]

    # ---- ELEVEN-V3 LEE EN VOZ ALTA LAS ETIQUETAS DE APERTURA LARGAS.
    # Medido el 2026-09-15 sobre las cuatro piezas de la S12: la etiqueta que abre la pieza 1 se
    # llevo 4,96 s de audio a -19,7 dBFS (nivel de habla) y la de la 3, 4,60 s a -18,0 -- las dijo.
    # Las de dentro del texto NO: duran 0,6-0,9 s, que es menos de lo que tardaria en pronunciar
    # sus propias palabras, y son solape de la alineacion con la palabra de al lado. Fundir las dos
    # etiquetas de apertura en una sola NO lo arregla (se probo, y la 3 empeoro): lo que lo dispara
    # es la LONGITUD, no el numero de corchetes.
    # El arreglo no cuesta un credito: los timestamps dicen exactamente donde empieza la primera
    # palabra DEL GUION, asi que se corta ahi y se deja 0,18 s de aire. Lo que se tira es
    # justamente lo que sobra.
    if TS.hay(str(A/'voz.json')):
        _pf = TS.palabras(json.loads((A/'voz.json').read_text(encoding='utf-8')))
        if _pf:
            t_voz = max(0.0, _pf[0][1] - 0.18)
            if t_voz > recorte + 0.25:
                corte = int((t_voz - recorte) * sr)
                if 0 < corte < len(x) - sr:
                    x = x[corte:]
                    print('  etiqueta de apertura hablada: recortados %.2f s' % (t_voz - recorte))
                    recorte = t_voz
    full = np.concatenate([np.zeros(int(PRE*sr), np.float32), x, np.zeros(int(POST*sr), np.float32)])
    full = full/max(1e-6, np.abs(full).max())*0.89
    sf.write(str(A/'voz.wav'), full, sr)
    dur = round(len(full)/sr, 3)
    (A/'_raw.wav').unlink(missing_ok=True)

    cache = A/'_palabras.json'
    # Con fal (`generar`) la alineacion viene en `voz.json`: las palabras son las del guion y los
    # tiempos los del proveedor. El `PRE` de silencio y el recorte del arranque se aplican aca, que
    # es donde se sabe cuanto se quito. Con PicsArt (`bajar`) no hay json y sigue mandando whisper.
    if TS.hay(str(A/'voz.json')):
        # `norm=None`: se guarda la palabra TAL CUAL la leyo, con su guion y su puntuacion
        # («twenty-four», «ruling.», «$104.61»), no normalizada. Con fal se puede porque el texto
        # es EL DEL GUION; con whisper no, que es por lo que estaba normalizado.
        # No es cosmetico, arregla tres cosas a la vez:
        #   · el subtitulo decia «TWENTYFOUR» y ahora dice «TWENTY-FOUR»;
        #   · `motor.agrupar` corta los grupos POR PUNTUACION, y sin puntuacion no cortaba nunca
        #     (salian grupos como «NARROWER IT SAID SUMMARY», a caballo de dos frases);
        #   · `resaltar` compara quitando la puntuacion, asi que contra una palabra normalizada no
        #     casaba NUNCA y no habia una sola palabra en rojo en el subtitulo.
        words = TS.palabras(json.loads((A/'voz.json').read_text(encoding='utf-8')),
                            t0=PRE, recorte=recorte, norm=None)
        cache.write_text(json.dumps(words), encoding='utf-8')
        print('timestamps de fal: %d palabras (whisper NO se corre)' % len(words))
    elif cache.exists():
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
        # el emparejamiento SI va normalizado en los dos lados (las palabras ya no lo estan)
        sm = SequenceMatcher(None, [t for _, t in gt], [norm(w[0]) for w in words], autojunk=False)
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
    {'dirigir': dirigir, 'generar': generar, 'bajar': bajar, 'alinear': alinear}[modo]()
