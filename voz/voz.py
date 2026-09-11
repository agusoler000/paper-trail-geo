# -*- coding: utf-8 -*-
"""Narra un guion (formato A:/V: de guiones/) con Kokoro y deja WAV + tiempos por linea.

    python voz/voz.py guiones/01_aviacion_rusa/guion.md --voz am_onyx [--voz bm_george] [--hasta 60]

Salida en produccion/audio/:
  <guion>_<voz>.wav          narracion completa (24 kHz mono)
  <guion>_<voz>.tiempos.json inicio/fin de cada linea A: y de cada beat -> lo usa el traductor de escenas
  <guion>_<voz>.txt          texto normalizado que se le dio al TTS (para revisar pronunciaciones)

Reglas heredadas de canal_youtube/scripts/voz_pruebas_kokoro.py:
  - frase por frase (cada linea A:), pegadas con silencio; el salto de linea ES la respiracion
  - ritmo calibrado a 145 wpm efectivos (ESTILO.md 3): Kokoro sale de fabrica a 180-225
  - pausa 0.45 s entre lineas, 1.1 s entre beats
Modelo: C:\\ia\\kokoro (kokoro-v1.0.onnx, voices-v1.0.bin), corre en CPU.
"""
import json, re, sys, time
from pathlib import Path
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

BASE=Path(__file__).resolve().parents[1]
MODEL=Path(r'C:\ia\kokoro'); OUT=BASE/'produccion'/'audio'; OUT.mkdir(parents=True,exist_ok=True)
WPM=137.0; PAUSA=0.5; PAUSA_BEAT=1.2

# Capa de normalizacion para TTS (ESTILO.md 3.3). Crece video a video.
PRON={
 'Aeroflot':'Airo-flot','Vladivostok':'Vladi-vostok','Yakutia':'Ya-kootia','Sakhalin':'Sakha-leen',
 'Krakow':'Krakov','Kyiv':'Keev','Hormuz':'Hor-mooz','Zelensky':'Zelen-skee','Pegasus':'Pegasus',
 'Kazakhstan':'Kazak-stan','Belarus':'Bela-roos','Emirates':'Emirates','Minsk':'Minsk','Sakhalin':'Sakha-leen',
}
def normalizar(t):
    for k,v in PRON.items(): t=re.sub(r'\b%s\b'%re.escape(k),v,t)
    t=t.replace('$',' dollars ').replace('%',' percent').replace('→',' to ')
    t=re.sub(r'\b(\d{4})\b',lambda m: m.group(1) if int(m.group(1))>2100 else m.group(1),t)
    return t

def leer_guion(p):
    beats=[]; cur=None
    for l in Path(p).read_text(encoding='utf-8').splitlines():
        if l.startswith('## BEAT'):
            cur={'titulo':l[3:].strip(),'lineas':[]}; beats.append(cur)
        elif l.startswith('A:') and cur is not None:
            cur['lineas'].append(l[2:].strip())
    return [b for b in beats if b['lineas']]

def sintetizar(k,beats,voz,speed):
    sr=24000; audio=[]; tiempos=[]; t=0.0
    for bi,b in enumerate(beats):
        if bi: audio.append(np.zeros(int(PAUSA_BEAT*sr),np.float32)); t+=PAUSA_BEAT
        b_ini=t
        for li,linea in enumerate(b['lineas']):
            if li: audio.append(np.zeros(int(PAUSA*sr),np.float32)); t+=PAUSA
            s,sr=k.create(normalizar(linea),voice=voz,speed=speed,lang='en-us')
            s=s.astype(np.float32); audio.append(s); d=len(s)/sr
            tiempos.append({'beat':bi,'linea':li,'texto':linea,'inicio':round(t,3),'fin':round(t+d,3)}); t+=d
        b['inicio']=round(b_ini,3); b['fin']=round(t,3)
    return np.concatenate(audio),sr,tiempos

def main():
    args=sys.argv[1:]; guion=args[0]
    voces=[args[i+1] for i,a in enumerate(args) if a=='--voz'] or ['am_onyx']
    hasta=float(args[args.index('--hasta')+1]) if '--hasta' in args else None
    beats=leer_guion(guion); nombre=Path(guion).parent.name
    palabras=sum(len(l.split()) for b in beats for l in b['lineas'])
    k=Kokoro(str(MODEL/'kokoro-v1.0.onnx'),str(MODEL/'voices-v1.0.bin'))
    for voz in voces:
        t0=time.time()
        # calibracion de ritmo sobre el primer beat largo (2 pasadas), como en Marlowe
        cal=next(b for b in beats if len(b['lineas'])>=8); speed=0.9
        for _ in range(2):
            a,sr,_=sintetizar(k,[cal],voz,speed); real=len(' '.join(cal['lineas']).split())/(len(a)/sr/60)
            if abs(real-WPM)<3: break
            speed=max(0.5,min(1.5,speed*WPM/real))
        sel=beats
        if hasta:
            sel=[]; acc=0
            for b in beats:
                sel.append(b); acc+=len(' '.join(b['lineas']).split())/WPM*60
                if acc>=hasta: break
        audio,sr,tiempos=sintetizar(k,sel,voz,speed)
        audio=audio/max(1e-6,np.abs(audio).max())*0.89          # normaliza pico a -1 dBFS
        dur=len(audio)/sr; wpm=sum(len(l.split()) for b in sel for l in b['lineas'])/(dur/60)
        stem=OUT/f'{nombre}_{voz}'
        sf.write(str(stem)+'.wav',audio,sr)
        json.dump({'voz':voz,'speed':round(speed,3),'wpm':round(wpm,1),'duracion':round(dur,2),
                   'beats':[{'titulo':b['titulo'],'inicio':b['inicio'],'fin':b['fin']} for b in sel],'lineas':tiempos},
                  open(str(stem)+'.tiempos.json','w',encoding='utf-8'),indent=1,ensure_ascii=False)
        Path(str(stem)+'.txt').write_text('\n'.join(normalizar(l) for b in sel for l in b['lineas']),encoding='utf-8')
        print(f'{voz}: speed {speed:.2f}  {wpm:.0f} wpm  {dur/60:.1f} min  ({time.time()-t0:.0f} s de proceso)  -> {stem}.wav')

if __name__=='__main__': main()
