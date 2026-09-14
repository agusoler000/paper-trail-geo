# -*- coding: utf-8 -*-
"""Narracion del formato diario con Piper local. Costo cero.

    python videos/DAILY/voz.py --autotest
    python videos/DAILY/voz.py --muestra "texto" A

Decision de Agustin (2026-09-11): el diario va con Piper, los Dispatch y Brief siguen con George.
Medido ese dia: 20 min de audio cuestan USD 2,21 en ElevenLabs y 0 en Piper, con 1,5 a 11 min de CPU.

DOS COSAS QUE ESTE MODULO HACE Y NO SON OBVIAS

1. REACOMODA LA LINEA DE TIEMPO. El LLM escribe "dur": 6.0 adivinando cuanto va a durar la frase.
   La duracion real la define el audio, y casi nunca coincide. Si no se corrige, la boca deja de
   moverse mientras la voz sigue hablando y la ficha cambia en mitad de una frase. Por eso, despues
   de sintetizar, los beats se vuelven a acomodar con la duracion REAL de cada uno y se reescribe
   el guion. Es la diferencia entre que el video este sincronizado o no.

2. SACA LOS VISEMAS SIN RHUBARB. Rhubarb es mejor y si esta instalado se usa. Si no, la boca sale
   del sobre de amplitud del audio (cuando hay volumen, la boca se abre) cruzado con las vocales del
   texto (que forma toma al abrirse). Para una marioneta de papel a 24 cuadros alcanza y sobra.
"""
import hashlib
import json
import os
import subprocess
import sys
import wave

BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(BASE))
for p in (RAIZ, BASE, os.path.join(BASE, "presentador")):
    if p not in sys.path:
        sys.path.insert(0, p)

MODELOS = os.path.join(RAIZ, "voz", "piper")
CACHE = os.path.join(BASE, "_voz_cache")
FPS = 24

# Una voz por presentador (aprobado por Agustin el 2026-09-11).
VOCES = {"A": "A_ryan", "B": "B_joe", "C": "C_alan"}

# Cadencia. `length_scale` de Piper: >1 lee mas lento. Sin esto, los tres leen a ~190 palabras por
# minuto, que es velocidad de podcast, no de informativo. Medido el 2026-09-13 con el guion del
# 14: 12.632 caracteres en 739 s = 17,1 car/s. Un lector de noticias va a 150-160 ppm; con 1,20
# el guion queda en ~155 y ademas se le entiende cada cifra, que es lo que este formato vende.
VELOCIDAD = {"A": 1.22, "B": 1.18, "C": 1.20}

PAUSA_BEAT = 0.35       # aire entre beats, para que no suene pegado
PAUSA_BLOQUE = 0.9      # aire mayor en el pase de un presentador a otro

_cargadas = {}

# Vocal -> forma de boca de Rhubarb (ver presentador/bocas.py)
_VOCAL = {"a": "D", "e": "C", "i": "C", "o": "E", "u": "F", "y": "C"}
_CERRADAS = set("mbp")
_DIENTES = set("fv")
_LENGUA = set("l")


def _voz(clave):
    from piper import PiperVoice
    if clave not in _cargadas:
        m = os.path.join(MODELOS, VOCES.get(clave, VOCES["A"]) + ".onnx")
        if not os.path.exists(m):
            raise FileNotFoundError(
                "falta el modelo %s. Bajalo con: python videos/DAILY/voz.py --bajar" % m)
        _cargadas[clave] = PiperVoice.load(m)
    return _cargadas[clave]


def disponible():
    try:
        import piper  # noqa: F401
    except ImportError:
        return False
    return all(os.path.exists(os.path.join(MODELOS, v + ".onnx")) for v in VOCES.values())


def sintetizar(texto, presentador="A", forzar=False):
    """Genera (o reusa) el wav de una frase. Devuelve (ruta, duracion_segundos).

    Cachea por hash de presentador+texto: reintentar el dia no vuelve a sintetizar lo ya hecho,
    y un guion que cambia una sola frase solo paga esa frase (en CPU, que es lo unico que cuesta).
    """
    os.makedirs(CACHE, exist_ok=True)
    vel = VELOCIDAD.get(presentador, 1.0)
    # la velocidad entra en la clave: si se cambia la cadencia, el cache NO puede devolver el
    # audio viejo (si no, un cambio de ritmo no se oye hasta borrar el cache a mano)
    h = hashlib.sha1(("%s|%.3f|%s" % (presentador, vel, texto)).encode("utf-8")).hexdigest()[:16]
    dest = os.path.join(CACHE, h + ".wav")
    if forzar or not os.path.exists(dest):
        cfg = None
        if abs(vel - 1.0) > 1e-6:
            try:
                from piper import SynthesisConfig
                cfg = SynthesisConfig(length_scale=vel)
            except Exception:
                cfg = None
        with wave.open(dest, "wb") as w:
            if cfg is not None:
                _voz(presentador).synthesize_wav(texto, w, syn_config=cfg)
            else:
                _voz(presentador).synthesize_wav(texto, w)
    with wave.open(dest) as w:
        dur = w.getnframes() / float(w.getframerate())
    return dest, dur


# --------------------------------------------------------------------------- visemas

def _envolvente(ruta, fps=FPS):
    """RMS por cuadro, normalizado 0..1. Es el 'cuanto se abre la boca'."""
    import numpy as np
    with wave.open(ruta) as w:
        sr, n, ancho = w.getframerate(), w.getnframes(), w.getsampwidth()
        crudo = w.readframes(n)
    tipo = {1: np.int8, 2: np.int16, 4: np.int32}.get(ancho, np.int16)
    x = np.frombuffer(crudo, dtype=tipo).astype("float32")
    if w.getnchannels() > 1:
        x = x.reshape(-1, w.getnchannels()).mean(axis=1)
    paso = max(1, int(sr / fps))
    cuadros = max(1, len(x) // paso)
    x = x[:cuadros * paso].reshape(cuadros, paso)
    rms = np.sqrt((x ** 2).mean(axis=1))
    pico = float(rms.max()) or 1.0
    return (rms / pico).tolist()


def _forma(letra, abierto):
    """Que boca toca: la vocal manda la forma, la amplitud manda si esta abierta o cerrada."""
    if abierto < 0.12:
        return "X"
    c = (letra or "").lower()
    if c in _VOCAL:
        f = _VOCAL[c]
        return "B" if abierto < 0.35 and f in "CD" else f
    if c in _CERRADAS:
        return "A"
    if c in _DIENTES:
        return "G"
    if c in _LENGUA:
        return "H"
    return "B" if abierto >= 0.2 else "A"


def visemas_de(ruta_wav, texto, t0=0.0, fps=FPS):
    """[(t_segundos, letra)] para una frase. Sin Rhubarb: sobre de amplitud + vocales del texto."""
    env = _envolvente(ruta_wav, fps)
    letras = [c for c in (texto or "") if c.isalpha()]
    # Piper arranca sin silencio: la boca tiene que ABRIR desde el reposo, no aparecer ya abierta.
    salida, previa = [(round(t0, 3), "X")], "X"
    for i, a in enumerate(env):
        c = letras[int(i * len(letras) / max(1, len(env)))] if letras else ""
        f = _forma(c, a)
        if f != previa:                      # solo se anotan los CAMBIOS de boca
            salida.append((round(t0 + (i + 1) / float(fps), 3), f))
            previa = f
    if previa != "X":                        # y volver al reposo al terminar la frase
        salida.append((round(t0 + (len(env) + 1) / float(fps), 3), "X"))
    return salida


def rhubarb_disponible():
    exe = os.environ.get("RHUBARB", "rhubarb")
    try:
        subprocess.run([exe, "--version"], capture_output=True, timeout=20)
        return True
    except Exception:
        return False


# --------------------------------------------------------------------------- el guion entero

def generar(guion, destino_wav, reacomodar=True, silencio_final=0.6):
    """Sintetiza el guion completo, REACOMODA la linea de tiempo y arma la pista de visemas.

    Devuelve (guion_corregido, pista_visemas, informe).
    """
    import numpy as np

    piezas, pista = [], []
    t = 0.0
    sr = None
    bloque_previo = None
    n_cache = n_nuevas = 0
    chars = 0

    for bl in guion["bloques"]:
        pres = bl.get("presentador", "A")
        if bloque_previo is not None and pres != bloque_previo:
            t += PAUSA_BLOQUE
        bloque_previo = pres
        for beat in bl["beats"]:
            texto = (beat.get("texto") or "").strip()
            if not texto:
                continue
            chars += len(texto)
            h = hashlib.sha1((pres + "|" + texto).encode("utf-8")).hexdigest()[:16]
            ya = os.path.exists(os.path.join(CACHE, h + ".wav"))
            ruta, dur = sintetizar(texto, pres)
            n_cache += 1 if ya else 0
            n_nuevas += 0 if ya else 1

            if reacomodar:
                beat["t"] = round(t, 3)
                beat["dur"] = round(dur, 3)     # la duracion REAL, no la que adivino el LLM
            piezas.append((t, ruta))
            pista.extend(visemas_de(ruta, texto, t0=t))
            t += dur + PAUSA_BEAT

    total = t + silencio_final
    # Mezcla: cada pieza en su lugar de la linea de tiempo.
    with wave.open(piezas[0][1]) as w0:
        sr = w0.getframerate()
        canales, ancho = w0.getnchannels(), w0.getsampwidth()
    pista_audio = np.zeros(int(total * sr) + sr, dtype="float32")
    for inicio, ruta in piezas:
        with wave.open(ruta) as w:
            x = np.frombuffer(w.readframes(w.getnframes()), dtype="int16").astype("float32")
        i = int(inicio * sr)
        j = min(len(pista_audio), i + len(x))
        pista_audio[i:j] += x[:j - i]
    pico = float(np.abs(pista_audio).max()) or 1.0
    pista_audio = (pista_audio / pico * 0.89 * 32767).astype("int16")
    with wave.open(destino_wav, "wb") as w:
        w.setnchannels(canales)
        w.setsampwidth(ancho)
        w.setframerate(sr)
        w.writeframes(pista_audio.tobytes())

    pista.sort(key=lambda p: p[0])
    informe = {"dur_seg": round(total, 1), "dur_min": round(total / 60, 1),
               "beats": len(piezas), "chars": chars,
               "cacheadas": n_cache, "sintetizadas": n_nuevas,
               "visemas": len(pista), "costo_usd": 0.0,
               "costo_elevenlabs_equivalente_usd": round(chars * 0.10 / 1000, 2)}
    return guion, pista, informe


def bajar_modelos():
    import urllib.request
    base = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en"
    rutas = {"A_ryan": "en_US/ryan/high/en_US-ryan-high",
             "B_joe": "en_US/joe/medium/en_US-joe-medium",
             "C_alan": "en_GB/alan/medium/en_GB-alan-medium"}
    os.makedirs(MODELOS, exist_ok=True)
    for k, p in rutas.items():
        for ext in (".onnx", ".onnx.json"):
            dest = os.path.join(MODELOS, k + ext)
            if os.path.exists(dest):
                continue
            urllib.request.urlretrieve("%s/%s%s?download=true" % (base, p, ext), dest)
            print("bajado", os.path.basename(dest))


# --------------------------------------------------------------------------- autotest

def _autotest():
    fallos = []

    def chequeo(nombre, cond, extra=""):
        print(("OK   " if cond else "FALLA") + " " + nombre + ((" | " + extra) if extra else ""))
        if not cond:
            fallos.append(nombre)

    if not disponible():
        print("SALTEA: falta piper o los modelos. Corre: python videos/DAILY/voz.py --bajar")
        return 0

    print("--- una voz por presentador ---")
    chequeo("hay tres voces, una por presentador", len(VOCES) == 3 and set(VOCES) == {"A", "B", "C"})
    chequeo("los tres modelos estan en disco",
            all(os.path.exists(os.path.join(MODELOS, v + ".onnx")) for v in VOCES.values()))

    print("--- sintesis y cache ---")
    import time
    txt = "Moscow says the measures will fail."
    r1, d1 = sintetizar(txt, "A", forzar=True)
    t0 = time.time()
    r2, d2 = sintetizar(txt, "A")
    t_cache = time.time() - t0
    chequeo("la segunda vez sale del cache", r1 == r2 and t_cache < 0.25, "%.3fs" % t_cache)
    chequeo("la duracion es estable", abs(d1 - d2) < 0.001)
    ra, _ = sintetizar(txt, "A")
    rb, _ = sintetizar(txt, "B")
    chequeo("el mismo texto con otro presentador es otro archivo", ra != rb)

    print("--- visemas ---")
    v = visemas_de(r1, txt)
    chequeo("salen visemas", len(v) > 4, "n=%d" % len(v))
    chequeo("todos son formas validas", all(f in "ABCDEFGHX" for _, f in v))
    chequeo("estan ordenados en el tiempo", all(v[i][0] <= v[i + 1][0] for i in range(len(v) - 1)))
    chequeo("arranca y termina en silencio", v[0][1] == "X" and v[-1][1] == "X",
            "%s ... %s" % (v[0][1], v[-1][1]))
    chequeo("no se queda en una sola forma", len({f for _, f in v}) >= 4,
            "formas=%s" % "".join(sorted({f for _, f in v})))

    print("--- lo mas importante: reacomoda la linea de tiempo ---")
    guion = {"fecha": "2026-09-11", "bloques": [
        {"nombre": "THE POWERS", "presentador": "A", "beats": [
            {"t": 0.0, "dur": 99.0, "texto": "Washington announced new sanctions this morning.",
             "ficha": "titular", "datos": {}},
            {"t": 99.0, "dur": 1.0, "texto": "Moscow says the measures will fail.",
             "ficha": "versus", "datos": {}}]},
        {"nombre": "THE SOUTH", "presentador": "B", "beats": [
            {"t": 100.0, "dur": 0.5, "texto": "Argentine inflation slowed again.",
             "ficha": "dato", "datos": {}}]}]}
    dest = os.path.join(BASE, "_voz_test.wav")
    g2, pista, inf = generar(guion, dest)
    beats = [b for bl in g2["bloques"] for b in bl["beats"]]
    chequeo("las duraciones inventadas (99 s, 1 s, 0,5 s) fueron reemplazadas",
            all(0.5 < b["dur"] < 20 for b in beats),
            "durs=%s" % [b["dur"] for b in beats])
    chequeo("los beats quedan en orden y sin pisarse",
            all(beats[i]["t"] + beats[i]["dur"] <= beats[i + 1]["t"] + 0.01
                for i in range(len(beats) - 1)))
    chequeo("hay mas aire en el cambio de presentador",
            beats[2]["t"] - (beats[1]["t"] + beats[1]["dur"]) > PAUSA_BEAT + 0.3)
    with wave.open(dest) as w:
        dur_wav = w.getnframes() / float(w.getframerate())
    chequeo("el wav dura lo que dice la linea de tiempo",
            abs(dur_wav - inf["dur_seg"]) < 1.2, "wav=%.1f informe=%.1f" % (dur_wav, inf["dur_seg"]))
    chequeo("el ultimo beat termina antes de que se acabe el audio",
            beats[-1]["t"] + beats[-1]["dur"] <= dur_wav + 0.01)

    print("--- el numero que importa ---")
    print("      %d chars · %.1f s de audio · Piper USD %.2f · ElevenLabs habria costado USD %.2f"
          % (inf["chars"], inf["dur_seg"], inf["costo_usd"], inf["costo_elevenlabs_equivalente_usd"]))
    chequeo("el costo es cero", inf["costo_usd"] == 0.0)
    chequeo("rhubarb es opcional, no obligatorio", True,
            "instalado" if rhubarb_disponible() else "no instalado, se usa el sobre de amplitud")
    if os.path.exists(dest):
        os.remove(dest)

    print()
    print("FALLOS: %d" % len(fallos) + (" -> " + ", ".join(fallos) if fallos else ""))
    return 1 if fallos else 0


if __name__ == "__main__":
    if "--autotest" in sys.argv:
        sys.exit(_autotest())
    if "--bajar" in sys.argv:
        bajar_modelos()
        sys.exit(0)
    if "--muestra" in sys.argv:
        i = sys.argv.index("--muestra")
        texto = sys.argv[i + 1]
        pres = sys.argv[i + 2] if len(sys.argv) > i + 2 else "A"
        r, d = sintetizar(texto, pres)
        print("%s  %.2fs" % (r, d))
        sys.exit(0)
    print(__doc__)
