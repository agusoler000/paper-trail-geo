# -*- coding: utf-8 -*-
"""Tiempos de palabra que devuelve ElevenLabs (via fal), para no tener que correr whisper.

`fal-ai/elevenlabs/tts/eleven-v3` con `timestamps: True` devuelve, junto al mp3, la alineacion
CARACTER a caracter del texto que leyo:

    {"characters": ["O","n"," ","t","h","e", ...],
     "character_start_times_seconds": [0.0, 0.046, ...],
     "character_end_times_seconds":   [0.046, 0.093, ...]}

Esto lo convierte en palabras. Sirve para dos cosas (auditoria §6.5):

  1. **Ahorrar 35 minutos de CPU por episodio**: `alinear` corria `faster-whisper small.en` sobre
     los 15 minutos de voz SOLO para reponer unos tiempos que el proveedor ya habia calculado.
  2. **Exactitud**: whisper transcribe lo que oye («2,977») y el guion escribe lo que se lee («two
     thousand nine hundred and seventy-seven»); emparejar las dos cosas es lo que obligo a montar
     el anclaje por mediana. Con estos tiempos las palabras son LAS DEL GUION, sin traduccion.

Las etiquetas de direccion de actor (`[measured]`, `[pause]`) van en el texto pero no se dicen: se
descartan. Los tiempos son relativos al mp3 que devolvio el proveedor, asi que al concatenar los
beats hay que sumarles el desplazamiento del beat y restarles lo que se recorto de silencio al
principio (`recorte`).
"""
import json, os, re

_NORM = lambda w: re.sub(r'[^a-z0-9]', '', w.lower())


def _es_bloque(v):
    return isinstance(v, dict) and 'characters' in v and 'character_start_times_seconds' in v


def _pegar(trozos):
    """Une varios bloques de alineacion en uno solo.

    **La forma real que devuelve fal** (medida el 2026-09-15 con la pieza 4 de la S12, y la razon
    por la que `hay()` daba False la primera vez que se llamo de verdad): `timestamps` no es un
    bloque, es una LISTA de 36 bloques, uno por trozo de sintesis. Los tiempos NO son relativos a
    cada trozo: son continuos y el trozo N termina exactamente donde empieza el N+1 (comprobado
    bloque a bloque), asi que pegarlos es concatenar y ya. Reconstruido, el texto da byte a byte
    el `texto.txt` que se le mando.
    """
    ch, a, b = [], [], []
    for c in trozos:
        n = len(c['characters'])
        e = c.get('character_end_times_seconds') or c['character_start_times_seconds']
        ch += list(c['characters'])
        a += [float(x) for x in c['character_start_times_seconds'][:n]]
        b += [float(x) for x in e[:n]]
    return {'characters': ch, 'character_start_times_seconds': a,
            'character_end_times_seconds': b}


def alineacion(payload):
    """Encuentra el bloque de alineacion dentro de la respuesta, venga donde venga.

    Acepta las cuatro formas vistas: el bloque suelto, dentro de `timestamps`/`alignment`/
    `normalized_alignment`, y **una lista de bloques** (lo que manda fal de verdad, ver `_pegar`).
    """
    if payload is None: return None
    if isinstance(payload, str):
        payload = json.loads(open(payload, encoding='utf-8').read()) if os.path.exists(payload) else json.loads(payload)
    if isinstance(payload, list):
        tr = [c for c in payload if _es_bloque(c)]
        if tr: return _pegar(tr)
        # **La quinta forma** (ep. 09, 2026-09-15): una lista de RESPUESTAS ENTERAS de fal, que es
        # lo que guarda `voz_ep.py` (un elemento por pedido; un beat largo se parte en dos). Cada
        # elemento es `{'audio': ..., 'timestamps': [bloques]}`, no un bloque, asi que el filtro de
        # arriba lo dejaba fuera, `hay()` daba False y `alinear` se caia a whisper sin decir nada:
        # 35 minutos de CPU y las palabras de la transcripcion en vez de las del guion.
        sub = [c for c in (alineacion(x) for x in payload) if c]
        return _pegar(sub) if sub else None
    cand = [payload]
    for k in ('timestamps', 'alignment', 'normalized_alignment', 'audio', 'data', 'output'):
        v = payload.get(k) if isinstance(payload, dict) else None
        if isinstance(v, dict): cand.append(v)
    for c in cand:
        if not isinstance(c, dict): continue
        if _es_bloque(c): return c
        for k in ('timestamps', 'alignment', 'normalized_alignment'):
            v = c.get(k)
            if _es_bloque(v): return v
            if isinstance(v, list):
                tr = [q for q in v if _es_bloque(q)]
                if tr: return _pegar(tr)
    return None


def palabras(payload, t0=0.0, recorte=0.0, norm=_NORM, sin_tags=True):
    """[(palabra, inicio, fin)] a partir de la alineacion por caracteres.

    t0      : donde empieza este beat en la linea de tiempo final.
    recorte : segundos de silencio que se le quitaron al principio del mp3 al concatenar.
    """
    al = alineacion(payload)
    if not al: return []
    ch = al['characters']
    a = al['character_start_times_seconds']
    b = al.get('character_end_times_seconds') or a
    n = min(len(ch), len(a), len(b))
    out = []
    pal, ini, fin = '', None, None
    dentro = False
    for i in range(n):
        c = ch[i]
        if sin_tags:
            if c == '[': dentro = True
            if dentro:
                if c == ']': dentro = False
                continue
        if c.isspace():
            if pal:
                w = norm(pal) if norm else pal
                if w: out.append((w, t0 + ini - recorte, t0 + fin - recorte))
            pal, ini, fin = '', None, None
            continue
        if ini is None: ini = float(a[i])
        fin = float(b[i]); pal += c
    if pal:
        w = norm(pal) if norm else pal
        if w: out.append((w, t0 + ini - recorte, t0 + fin - recorte))
    return out


def hay(ruta):
    """True si el json de timestamps existe y trae alineacion utilizable."""
    if not (ruta and os.path.exists(ruta)): return False
    try: return alineacion(json.load(open(ruta, encoding='utf-8'))) is not None
    except Exception: return False


def duracion(payload):
    al = alineacion(payload)
    if not al: return 0.0
    b = al.get('character_end_times_seconds') or al['character_start_times_seconds']
    return float(b[-1]) if b else 0.0
