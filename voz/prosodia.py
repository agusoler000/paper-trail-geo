# -*- coding: utf-8 -*-
"""Mide la PROSODIA de una narracion ya generada: cuanto sube y baja, cuanto corre y cuanto frena.
0 creditos, numpy + soundfile (y ffmpeg solo si el archivo no es wav).

    python voz/prosodia.py <voz.wav> <tiempos.json> [--json] [--beats]

Nace del hallazgo de `canal/AUDITORIA_MOTOR_2026-09-15.md` §2.4: la voz del canal no esta mal, esta
DIRIGIDA a ser plana. De las 62 etiquetas de actor del ep. 09, 54 son `flat/measured/quiet/low/dry`.
La referencia (GeoGlobeTales) narra a 189 wpm con frases de 18,7 palabras que corren y frenan;
nosotros a 158 wpm con frases de 10,5 y todo en el mismo tono. Esto es la vara para comparar la voz
vieja con la nueva sin discutir de oido.

Que mide:
  f0 mediana        altura de la voz, en Hz, por autocorrelacion (ventanas de 40 ms, 60-300 Hz).
  rango p10-p90     la distancia entre el grave y el agudo habituales, EN SEMITONOS. Es lo que el
                    oido llama "tiene rango". Una voz plana vive por debajo de 4-5 semitonos.
  wpm por linea     velocidad; su desvio dice si la narracion corre y frena o va siempre igual.
  pausas >= 0,25 s  cuantas, cuanto duran y cuanto varian: el silencio antes de una revelacion.
  RMS por linea     energia; el rango dice si hay dinamica o esta todo al mismo volumen.
  contraste 0-100   combinacion normalizada de rango tonal + sd de wpm + sd de pausas + rango de
                    RMS. NO es una nota: es un numero para comparar dos tomas de la misma voz.
"""
import json, math, os, subprocess, sys, tempfile
import numpy as np

SR = 16000
VENT, SALTO = 0.040, 0.020          # ventana de 40 ms, salto de 20 ms
F0_MIN, F0_MAX = 60.0, 300.0        # George es una voz masculina grave
PAUSA_MIN = 0.25


def cargar(path, sr=SR):
    """Mono a `sr` Hz. Acepta wav, mp3 o lo que sepa leer ffmpeg."""
    try:
        import soundfile as sf
        x, s = sf.read(path, dtype='float32', always_2d=False)
        if getattr(x, 'ndim', 1) > 1: x = x.mean(axis=1)
        if s != sr:
            n = int(round(len(x) * sr / s))
            x = np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)
        return x.astype(np.float32)
    except Exception:
        tmp = os.path.join(tempfile.gettempdir(), '_prosodia.wav')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', path, '-ac', '1', '-ar', str(sr), tmp],
                       check=True)
        import soundfile as sf
        x, _ = sf.read(tmp, dtype='float32')
        return x.astype(np.float32)


def f0_autocorr(x, sr=SR, vent=VENT, salto=SALTO, fmin=F0_MIN, fmax=F0_MAX, umbral=0.30):
    """f0 por autocorrelacion, ventana a ventana. Devuelve (t, f0) solo de las ventanas sonoras.

    Es el metodo de `canal/VOZ.md`: nada de dependencias nuevas. Se quita la media, se normaliza y
    se busca el maximo de la autocorrelacion dentro del rango de periodos posibles; una ventana
    cuenta como sonora si ese maximo pasa `umbral` y la ventana tiene energia suficiente."""
    N = int(vent * sr); S = int(salto * sr)
    lag_min, lag_max = int(sr / fmax), int(sr / fmin)
    if len(x) < N + lag_max: return np.zeros(0), np.zeros(0)
    rms_tot = float(np.sqrt(np.mean(x ** 2)) + 1e-9)
    ts, fs = [], []
    vent_hann = np.hanning(N).astype(np.float32)
    for i in range(0, len(x) - N, S):
        w = x[i:i + N]
        r = float(np.sqrt(np.mean(w ** 2)))
        if r < rms_tot * 0.25: continue                  # silencio o respiracion
        w = (w - w.mean()) * vent_hann
        ac = np.correlate(w, w, mode='full')[N - 1:]
        if ac[0] <= 0: continue
        ac = ac / ac[0]
        seg = ac[lag_min:lag_max]
        if not len(seg): continue
        k = int(np.argmax(seg))
        if seg[k] < umbral: continue
        lag = lag_min + k
        # refinado parabolico sobre los tres puntos del pico: la f0 no salta de muestra en muestra
        if 0 < k < len(seg) - 1:
            a, b, c = seg[k - 1], seg[k], seg[k + 1]
            den = (a - 2 * b + c)
            if abs(den) > 1e-9: lag = lag + 0.5 * (a - c) / den
        ts.append((i + N / 2) / sr); fs.append(sr / lag)
    return np.array(ts), np.array(fs)


def semitonos(a, b):
    if a <= 0 or b <= 0: return 0.0
    return 12.0 * math.log2(b / a)


def medir(wav, tiempos):
    x = cargar(wav)
    dur = len(x) / SR
    T = json.load(open(tiempos, encoding='utf-8')) if isinstance(tiempos, str) else tiempos
    L = T['lineas']

    # ---- tono
    tf, f0 = f0_autocorr(x)
    if len(f0):
        med = float(np.median(f0)); p10 = float(np.percentile(f0, 10)); p90 = float(np.percentile(f0, 90))
        rango_st = semitonos(p10, p90)
    else:
        med = p10 = p90 = rango_st = 0.0

    # ---- velocidad por linea
    wpm, pal_linea = [], []
    for ln in L:
        d = float(ln['fin']) - float(ln['inicio'])
        n = len([w for w in ln['texto'].split() if w.strip('.,;:!?"')])
        if d > 0.2 and n >= 2:
            wpm.append(n / d * 60.0); pal_linea.append(n)
    wpm = np.array(wpm) if wpm else np.zeros(1)

    # ---- pausas entre lineas
    hue = []
    for a, b in zip(L, L[1:]):
        g = float(b['inicio']) - float(a['fin'])
        if g >= PAUSA_MIN: hue.append(g)
    hue = np.array(hue) if hue else np.zeros(1)

    # ---- energia por linea
    rms = []
    for ln in L:
        i0, i1 = int(float(ln['inicio']) * SR), int(float(ln['fin']) * SR)
        seg = x[max(0, i0):min(len(x), i1)]
        if len(seg) > SR * 0.1:
            rms.append(20 * math.log10(float(np.sqrt(np.mean(seg ** 2))) + 1e-9))
    rms = np.array(rms) if rms else np.zeros(1)
    rms_p10, rms_p90 = float(np.percentile(rms, 10)), float(np.percentile(rms, 90))

    # ---- tono DENTRO de cada linea, y de linea a linea.
    # El rango global no sirve para juzgar si la lectura es plana: George tiene rango (VOZ.md lo
    # midio) y a lo largo de 15 min lo usa igual. Lo que el oido llama "plano" es (a) que cada
    # frase suba y baje poco por dentro, y (b) que todas las frases arranquen a la misma altura.
    # Esos son los dos numeros que hay que mirar para comparar una direccion de actor con otra.
    intra, medl = [], []
    for ln in L:
        m_ = (tf >= float(ln['inicio'])) & (tf <= float(ln['fin']))
        v = f0[m_]
        if len(v) < 8: continue
        intra.append(semitonos(float(np.percentile(v, 10)), float(np.percentile(v, 90))))
        medl.append(float(np.median(v)))
    rango_intra = float(np.median(intra)) if intra else 0.0
    deriva_st = float(np.std([semitonos(med, v) for v in medl])) if len(medl) > 2 else 0.0

    # ---- indice de contraste. Los topes salen de lo medido, no de la nada: 6 semitonos de rango
    # dentro de la frase, 3 semitonos de desvio entre frases, 45 wpm de desvio y 9 dB de rango de
    # energia dan 100. NO es una nota: es una vara para comparar dos tomas de la MISMA voz.
    ejes = {'tono_en_la_frase': min(1.0, rango_intra / 6.0),
            'tono_entre_frases': min(1.0, deriva_st / 3.0),
            'velocidad': min(1.0, float(np.std(wpm)) / 45.0),
            'energia': min(1.0, (rms_p90 - rms_p10) / 9.0)}
    contraste = round(100.0 * sum(ejes.values()) / len(ejes), 1)

    return {'archivo': os.path.basename(wav), 'dur_s': round(dur, 2),
            'lineas': len(L), 'palabras': int(sum(pal_linea)),
            'f0_mediana_hz': round(med, 1), 'f0_p10_hz': round(p10, 1), 'f0_p90_hz': round(p90, 1),
            'rango_semitonos': round(rango_st, 2),
            'rango_en_la_frase_st': round(rango_intra, 2),
            'deriva_entre_frases_st': round(deriva_st, 2),
            'ventanas_sonoras': int(len(f0)),
            'wpm_medio': round(float(np.mean(wpm)), 1), 'wpm_sd': round(float(np.std(wpm)), 1),
            'wpm_p10': round(float(np.percentile(wpm, 10)), 1),
            'wpm_p90': round(float(np.percentile(wpm, 90)), 1),
            'palabras_por_linea': round(float(np.mean(pal_linea)) if pal_linea else 0, 1),
            'pausas_n': int(len(hue)) if hue.any() else 0,
            'pausas_media_s': round(float(np.mean(hue)), 2), 'pausas_sd_s': round(float(np.std(hue)), 2),
            'rms_medio_db': round(float(np.mean(rms)), 1),
            'rms_p10_db': round(rms_p10, 1), 'rms_p90_db': round(rms_p90, 1),
            'rms_rango_db': round(rms_p90 - rms_p10, 1),
            'ejes': {k: round(v, 3) for k, v in ejes.items()},
            'contraste': contraste}


def por_beat(wav, tiempos):
    """Lo mismo, beat por beat: sirve para ver que beat se aplano."""
    T = json.load(open(tiempos, encoding='utf-8')) if isinstance(tiempos, str) else tiempos
    if 'beats' not in T: return []
    x = cargar(wav); out = []
    for b in T['beats']:
        L = [l for l in T['lineas'] if l.get('b') == b['i']]
        if not L: continue
        i0, i1 = int(float(b['inicio']) * SR), int(float(b['fin']) * SR)
        seg = x[max(0, i0):min(len(x), i1)]
        _, f0 = f0_autocorr(seg)
        st = semitonos(float(np.percentile(f0, 10)), float(np.percentile(f0, 90))) if len(f0) > 8 else 0.0
        w = [len(l['texto'].split()) / max(0.2, float(l['fin']) - float(l['inicio'])) * 60 for l in L]
        out.append({'beat': b['i'], 'titulo': b.get('titulo', '')[:34], 'lineas': len(L),
                    'rango_st': round(st, 2), 'wpm': round(float(np.mean(w)), 1),
                    'wpm_sd': round(float(np.std(w)), 1)})
    return out


def imprimir(m, beats=None):
    print('\n%s  ·  %d:%02d  ·  %d lineas, %d palabras\n'
          % (m['archivo'], int(m['dur_s'] // 60), int(m['dur_s'] % 60), m['lineas'], m['palabras']))
    print('  TONO       mediana %6.1f Hz   p10 %5.1f   p90 %5.1f   rango global %5.2f semitonos'
          % (m['f0_mediana_hz'], m['f0_p10_hz'], m['f0_p90_hz'], m['rango_semitonos']))
    print('             dentro de la frase %5.2f st  (plana < 4,0)   entre frases %5.2f st  (plana < 1,2)'
          % (m['rango_en_la_frase_st'], m['deriva_entre_frases_st']))
    print('  VELOCIDAD  %6.1f wpm        sd %5.1f      p10 %5.1f   p90 %5.1f   (referencia 189 wpm)'
          % (m['wpm_medio'], m['wpm_sd'], m['wpm_p10'], m['wpm_p90']))
    print('             %.1f palabras por linea   (referencia 18,7)' % m['palabras_por_linea'])
    print('  PAUSAS     %4d de >= %.2f s   media %.2f s   sd %.2f s'
          % (m['pausas_n'], PAUSA_MIN, m['pausas_media_s'], m['pausas_sd_s']))
    print('  ENERGIA    media %.1f dBFS   p10 %.1f   p90 %.1f   rango %.1f dB'
          % (m['rms_medio_db'], m['rms_p10_db'], m['rms_p90_db'], m['rms_rango_db']))
    print('\n  CONTRASTE  %.1f / 100   (%s)' % (m['contraste'], ' · '.join(
        '%s %.2f' % (k, v) for k, v in m['ejes'].items())))
    if beats:
        print('\n  beat  rango_st   wpm   sd   lineas  titulo')
        for b in beats:
            print('  %4d  %8.2f  %5.1f %4.1f   %4d   %s'
                  % (b['beat'], b['rango_st'], b['wpm'], b['wpm_sd'], b['lineas'], b['titulo']))


def main():
    a = sys.argv[1:]
    if len(a) < 2: print(__doc__); return
    wav, ti = a[0], a[1]
    m = medir(wav, ti)
    b = por_beat(wav, ti) if '--beats' in a else None
    if '--json' in a:
        print(json.dumps({'global': m, 'beats': b}, indent=1, ensure_ascii=False))
    else:
        imprimir(m, b)


if __name__ == '__main__':
    main()
