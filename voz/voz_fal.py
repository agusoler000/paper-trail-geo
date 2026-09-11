"""Genera beats con ElevenLabs v3 (George) via fal.ai. Uso: python voz/voz_fal.py <dir_dirigido> <beat> [<beat>...]
Necesita FAL_KEY en el entorno (nunca se imprime). Escribe beat_XX.mp3 en el mismo directorio."""
import sys, os, pathlib, requests, fal_client
d = pathlib.Path(sys.argv[1]); assert os.environ.get('FAL_KEY'), 'sin FAL_KEY'
for b in sys.argv[2:]:
    b = int(b); txt = (d / f'beat_{b:02d}.txt').read_text(encoding='utf-8')
    r = fal_client.subscribe('fal-ai/elevenlabs/tts/eleven-v3',
        arguments={'text': txt, 'voice': 'JBFqnCBsd6RMkjVDRZzb', 'stability': 0.5, 'language_code': 'en'})
    url = r['audio']['url']; out = d / f'beat_{b:02d}.mp3'
    out.write_bytes(requests.get(url).content)
    print(f'beat {b:02d}: {len(txt)} chars -> {out.name} {out.stat().st_size} bytes')
