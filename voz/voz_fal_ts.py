"""Un clip con timestamps por palabra via fal.ai (George). Uso: python voz/voz_fal_ts.py texto.txt salida.mp3"""
import sys, os, json, pathlib, requests, fal_client
txt=pathlib.Path(sys.argv[1]).read_text(encoding='utf-8').strip(); out=pathlib.Path(sys.argv[2])
r=fal_client.subscribe('fal-ai/elevenlabs/tts/eleven-v3',arguments={'text':txt,'voice':'JBFqnCBsd6RMkjVDRZzb','stability':0.5,'language_code':'en','timestamps':True})
out.write_bytes(requests.get(r['audio']['url']).content)
json.dump({k:v for k,v in r.items() if k!='audio'},open(out.with_suffix('.json'),'w'),indent=1)
print(out, out.stat().st_size, list(r.keys()))
