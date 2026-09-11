# -*- coding: utf-8 -*-
"""Une los MP3 por beat de ElevenLabs en un WAV y recupera los tiempos de cada linea A: con faster-whisper.

    python voz/alinear.py guiones/01_aviacion_rusa/guion.md produccion/audio/dirigido  --voz eleven_george

Salida: produccion/audio/01_aviacion_rusa_eleven_george.wav + .tiempos.json (mismo formato que voz.py)
Metodo: whisper (small.en, CPU) da palabras con tiempo; se recorren en orden y se asignan a las lineas del
guion por conteo de palabras con tolerancia (el TTS puede pronunciar numeros distinto).
"""
import json, re, sys, subprocess
from pathlib import Path
import numpy as np, soundfile as sf
PAUSA_BEAT=1.5; PRE=1.0; POST=8.0   # v2 2026-09-08: pre-roll 1 s (antes 8 s: 16 s sin voz con la intro delante)
def norm(w): return re.sub(r'[^a-z0-9]','',w.lower())
def leer(p):
    beats=[];cur=None
    for l in Path(p).read_text(encoding='utf-8').splitlines():
        if l.startswith('## BEAT'): cur={'titulo':l[3:].strip(),'lineas':[]}; beats.append(cur)
        elif l.startswith('A:') and cur is not None: cur['lineas'].append(l[2:].strip())
    return [b for b in beats if b['lineas']]
def main():
    g=sys.argv[1]; d=Path(sys.argv[2]); voz=sys.argv[sys.argv.index('--voz')+1] if '--voz' in sys.argv else 'eleven'
    beats=leer(g); nombre=Path(g).parent.name; out=Path(g).resolve().parents[2]/'produccion'/'audio'
    # 1) concatenar beats con pausa
    sr=24000; audio=[np.zeros(int(PRE*sr),np.float32)]; t=PRE
    for bi,b in enumerate(beats):
        mp3=d/f'beat_{bi:02d}.mp3'; wav=d/f'beat_{bi:02d}.wav'
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(mp3),'-ac','1','-ar',str(sr),str(wav)],check=True)
        x,_=sf.read(str(wav)); x=x.astype(np.float32)
        # recortar silencio inicial/final (>-45 dB)
        env=np.abs(x); thr=10**(-45/20); idx=np.where(env>thr)[0]
        if len(idx): x=x[max(0,idx[0]-int(0.05*sr)):min(len(x),idx[-1]+int(0.15*sr))]
        if bi: audio.append(np.zeros(int(PAUSA_BEAT*sr),np.float32)); t+=PAUSA_BEAT
        b['inicio']=round(t,3); audio.append(x); t+=len(x)/sr; b['fin']=round(t,3)
    audio.append(np.zeros(int(POST*sr),np.float32)); full=np.concatenate(audio); full=full/max(1e-6,np.abs(full).max())*0.89
    stem=out/f'{nombre}_{voz}'; sf.write(str(stem)+'.wav',full,sr)
    # 2) whisper con timestamps por palabra
    from faster_whisper import WhisperModel
    m=WhisperModel('small.en',device='cpu',compute_type='int8')
    segs,_=m.transcribe(str(stem)+'.wav',word_timestamps=True,beam_size=3,vad_filter=False)
    words=[(norm(w.word),w.start,w.end) for s in segs for w in s.words if norm(w.word)]
    print('palabras reconocidas',len(words))
    # 3) asignar palabras a lineas, beat por beat (las palabras del beat estan entre inicio y fin del beat)
    tiempos=[]; wi=0
    for bi,b in enumerate(beats):
        bw=[w for w in words if b['inicio']-0.3<=w[1]<=b['fin']+0.3]
        n_total=sum(len(l.split()) for l in b['lineas']); k=0
        for li,l in enumerate(b['lineas']):
            n=len(l.split()); frac=n/n_total
            # ventana proporcional, ajustada por coincidencia de la primera palabra del siguiente tramo
            j0=min(len(bw)-1,round(k)); j1=min(len(bw)-1,round(k+frac*len(bw))-1); j1=max(j0,j1)
            # afinar j1 buscando la ultima palabra de la linea en +-3 posiciones
            last=norm(l.split()[-1])
            for jj in range(max(j0,j1-3),min(len(bw),j1+4)):
                if bw[jj][0]==last: j1=jj; break
            ini=bw[j0][1] if bw else b['inicio']; fin=bw[j1][2] if bw else b['fin']
            tiempos.append({'beat':bi,'linea':li,'texto':l,'inicio':round(ini,3),'fin':round(fin,3)}); k=j1+1
    dur=len(full)/sr
    json.dump({'voz':voz,'duracion':round(dur,2),'beats':[{'titulo':b['titulo'],'inicio':b['inicio'],'fin':b['fin']} for b in beats],'lineas':tiempos},
              open(str(stem)+'.tiempos.json','w',encoding='utf-8'),indent=1,ensure_ascii=False)
    print(f'{voz}: {dur/60:.1f} min -> {stem}.wav / .tiempos.json')
if __name__=='__main__': main()
