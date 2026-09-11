"""Convierte un VTT auto-generado de YouTube (yt-dlp) al formato de fuentes/yt/*.md.
Uso: python vtt2md.py _sub/<id>.<lang>.vtt "<canal>" "<titulo>" <duracion_s> <fecha> [vistas]
Dedupe: YouTube repite cada linea en dos cues (rolling); se queda con la ultima linea de cada cue."""
import re, sys, pathlib
vtt, canal, titulo, dur, fecha = sys.argv[1:6]
vistas = sys.argv[6] if len(sys.argv) > 6 else ''
vid = pathlib.Path(vtt).name.split('.')[0]
txt = pathlib.Path(vtt).read_text(encoding='utf-8')
cues = re.split(r'\n\n+', txt)
out = []
for c in cues:
    lines = [l for l in c.strip().split('\n') if l.strip()]
    if not lines or '-->' not in lines[0]:
        continue
    t0 = lines[0].split('-->')[0].strip()
    body = [re.sub(r'<[^>]+>', '', l).strip() for l in lines[1:]]
    body = [b for b in body if b and b != '&nbsp;']
    if not body:
        continue
    last = body[-1]
    if out and out[-1][1] == last:
        continue
    h, m, s = t0.split(':'); sec = int(h)*3600 + int(m)*60 + float(s)
    out.append((sec, last))
slug = re.sub(r'[^a-z0-9]+', '-', titulo.lower()).strip('-')[:60]
dest = pathlib.Path('yt') / f'{vid}_{slug}.md'
plain = ' '.join(t for _, t in out)
words = len(plain.split())
md = [f'# {titulo}', '', f'- id: {vid}', f'- canal: {canal}', f'- duracion: {int(dur)//60}:{int(dur)%60:02d}',
      f'- fecha: {fecha}', f'- vistas: {vistas}', f'- palabras: {words}', f'- origen: subtitulos automaticos (yt-dlp, {pathlib.Path(vtt).name})', '',
      '## Texto corrido', '', plain, '', '## Con tiempos', '']
md += [f'[{int(s)//60:02d}:{int(s)%60:02d}] {t}' for s, t in out]
dest.write_text('\n'.join(md), encoding='utf-8')
with open('yt/indice.md', 'a', encoding='utf-8') as f:
    f.write(f'- {canal} | {titulo} | {int(dur)//60}:{int(dur)%60:02d} | {words} palabras | {dest.as_posix()}\n')
print(dest, words, 'palabras')
