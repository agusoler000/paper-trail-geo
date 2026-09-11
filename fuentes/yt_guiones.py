# -*- coding: utf-8 -*-
"""Extrae guiones (transcripciones) de videos de YouTube para investigar temas y estructura.

Mismo motor que el scraper de Skool (`../scrape-skool/scraper/fetch_lesson.py`):
yt-dlp para descubrir videos + youtube-transcript-api para bajar la transcripcion sin descargar video.

Uso:
    python yt_guiones.py buscar "Essequibo Guyana Venezuela explained" [--n 6]
    python yt_guiones.py canal https://www.youtube.com/@CaspianReport [--n 10]
    python yt_guiones.py ids zaqTvSlgexk Q-C4tosjBk8 ...

Salida: fuentes/yt/<id>_<slug>.md  (metadata + texto corrido + version con timestamps)
        fuentes/yt/indice.md       (una linea por video: canal, titulo, duracion, palabras, ruta)
Solo transcripciones en ingles (o auto-generadas en ingles); si no hay, lo anota y sigue.
"""
import json, os, re, subprocess, sys, unicodedata
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi

BASE=Path(__file__).resolve().parent; OUT=BASE/'yt'; OUT.mkdir(exist_ok=True)

def slug(s, n=60):
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode()
    s=re.sub(r'[^A-Za-z0-9]+','-',s).strip('-').lower()
    return s[:n]

def descubrir(target, n):
    """Devuelve lista de dicts {id,title,channel,duration,url} via yt-dlp (sin bajar nada)."""
    cmd=[sys.executable,'-m','yt_dlp','--flat-playlist','--dump-json','--no-warnings','--playlist-end',str(n)]
    if target.startswith('http'):
        # canal: usar la pestana /videos para que salgan los ultimos subidos
        if '/@' in target and not target.rstrip('/').endswith('/videos'): target=target.rstrip('/')+'/videos'
        cmd.append(target)
    else:
        cmd.append(f'ytsearch{n}:{target}')
    out=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
    vids=[]
    for l in out.stdout.splitlines():
        if not l.strip(): continue
        v=json.loads(l)
        vids.append({'id':v.get('id'),'title':v.get('title') or '','channel':v.get('channel') or v.get('uploader') or '',
                     'duration':v.get('duration') or 0,'url':f"https://www.youtube.com/watch?v={v.get('id')}",'views':v.get('view_count')})
    return vids

def transcript(video_id):
    api=YouTubeTranscriptApi()
    try:
        f=api.fetch(video_id,languages=['en','en-US','en-GB'])
    except Exception:
        lst=api.list(video_id)
        f=None
        for t in lst:
            if t.language_code.startswith('en'): f=t.fetch(); break
        if f is None:
            # cualquier idioma traducible al ingles
            for t in lst:
                if t.is_translatable: f=t.translate('en').fetch(); break
        if f is None: raise RuntimeError('sin transcripcion en ingles')
    return f

def hms(s):
    m,s=divmod(int(s),60); h,m=divmod(m,60)
    return f'{h:d}:{m:02d}:{s:02d}' if h else f'{m:d}:{s:02d}'

def guardar(v, f):
    snips=list(f.snippets)
    texto=' '.join(s.text.replace('\n',' ').strip() for s in snips)
    texto=re.sub(r'\s+',' ',texto)
    palabras=len(texto.split())
    # parrafos cada ~60 s para que se pueda leer como guion
    parr=[]; cur=[]; t0=0
    for s in snips:
        if s.start-t0>=60 and cur: parr.append(f'**[{hms(t0)}]** '+' '.join(cur)); cur=[]; t0=s.start
        cur.append(s.text.replace('\n',' ').strip())
    if cur: parr.append(f'**[{hms(t0)}]** '+' '.join(cur))
    path=OUT/f"{v['id']}_{slug(v['title'])}.md"
    md=[f"# {v['title']}",'',f"- Canal: {v['channel']}",f"- URL: {v['url']}",f"- Duración: {hms(v['duration'])}  ·  Palabras: {palabras}  ·  Idioma transcripción: {f.language_code}",
        f"- Vistas: {v.get('views')}",'','---','','## Guion por minuto','','\n\n'.join(parr),'','---','','## Texto corrido','',texto,'']
    path.write_text('\n'.join(md),encoding='utf-8')
    return path, palabras

def main():
    if len(sys.argv)<3: print(__doc__); sys.exit(1)
    modo=sys.argv[1]; n=6
    if '--n' in sys.argv: n=int(sys.argv[sys.argv.index('--n')+1])
    if modo=='ids':
        vids=[{'id':i,'title':i,'channel':'','duration':0,'url':f'https://www.youtube.com/watch?v={i}'} for i in sys.argv[2:] if not i.startswith('--')]
        # completar metadata con yt-dlp uno por uno
        for v in vids:
            try:
                out=subprocess.run([sys.executable,'-m','yt_dlp','--dump-json','--no-warnings','--skip-download',v['url']],capture_output=True,text=True,timeout=120)
                d=json.loads(out.stdout.splitlines()[0]); v.update({'title':d.get('title'),'channel':d.get('channel') or d.get('uploader'),'duration':d.get('duration') or 0,'views':d.get('view_count')})
            except Exception as e: print('  meta?',v['id'],e)
    else:
        vids=descubrir(sys.argv[2],n)
    indice=OUT/'indice.md'
    lines=indice.read_text(encoding='utf-8').splitlines() if indice.exists() else ['# Índice de guiones extraídos','','| id | canal | título | dur | palabras | archivo |','|---|---|---|---|---|---|']
    for v in vids:
        if any(f'| {v["id"]} |' in l for l in lines): print('ya estaba',v['id']); continue
        try:
            f=transcript(v['id']); path,pal=guardar(v,f)
            lines.append(f"| {v['id']} | {v['channel']} | {v['title']} | {hms(v['duration'])} | {pal} | {path.name} |")
            print('ok',v['id'],v['channel'],'|',v['title'],'|',pal,'palabras')
        except Exception as e:
            lines.append(f"| {v['id']} | {v['channel']} | {v['title']} | {hms(v['duration'])} | - | SIN TRANSCRIPCIÓN: {type(e).__name__} |")
            print('sin transcripcion',v['id'],type(e).__name__,str(e)[:80])
    indice.write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__': main()
