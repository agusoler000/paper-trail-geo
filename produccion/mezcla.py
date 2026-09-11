# -*- coding: utf-8 -*-
"""Mezcla final de audio: voz + cortina musical (ducking bajo la voz) + efectos de sonido de papel.

    python mezcla.py audio/01_aviacion_rusa_eleven_george.wav eventos.json salida.wav

Musica: pistas CC BY 4.0 de Kevin MacLeod (incompetech.com) en produccion/musica/. Credito obligatorio en la
descripcion del video (ver CREDITOS_MUSICA.md). Se encadenan con crossfade hasta cubrir la duracion.
SFX: sintetizados con numpy (papel que se desliza, golpe seco de sello, pop, whoosh, clac de ficha), sin derechos.
"""
import json, sys, os, subprocess, math
import numpy as np, soundfile as sf
SR=48000
def cargar(p, sr=SR):
    tmp=p+'.tmp.wav'; subprocess.run(['ffmpeg','-v','error','-y','-i',p,'-ac','1','-ar',str(sr),tmp],check=True)
    x,_=sf.read(tmp); os.remove(tmp); return x.astype(np.float32)
def db(g): return 10**(g/20)
# ---------------------------------------------------------------- SFX sintetizados
rng=np.random.default_rng(4)
def env(n, a=0.005, d=0.1, s=0.0, r=0.05, hold=0.0):
    t=np.arange(n)/SR; e=np.ones(n,np.float32)
    A=int(a*SR); D=int(d*SR); R=int(r*SR); H=int(hold*SR)
    e[:A]=np.linspace(0,1,max(A,1))[:A]
    if D: e[A:A+D]=np.linspace(1,s,D)[:max(0,min(D,n-A))]
    e[A+D:A+D+H]=s
    tail=n-(A+D+H)
    if tail>0: e[A+D+H:]=np.linspace(s,0,tail)
    return e
def noise(n): return rng.standard_normal(n).astype(np.float32)
def lowpass(x, fc):
    # un polo, suficiente para color
    a=math.exp(-2*math.pi*fc/SR); y=np.zeros_like(x); acc=0.0
    for i in range(len(x)): acc=a*acc+(1-a)*x[i]; y[i]=acc
    return y
def bandpass(x, lo, hi): return lowpass(x,hi)-lowpass(x,lo)
def sfx_slide(dur=0.35):   # papel deslizandose sobre madera
    n=int(dur*SR); x=bandpass(noise(n),800,4000)*env(n,0.02,dur*0.6,0.3,dur*0.35); return x*0.5
def sfx_pop(dur=0.12):     # aparicion de tarjeta/objeto: pop corto con cuerpo
    n=int(dur*SR); t=np.arange(n)/SR; f=np.linspace(520,180,n); x=np.sin(2*np.pi*np.cumsum(f)/SR)*env(n,0.002,0.06,0.2,0.05); return x*0.35
def sfx_unpop(dur=0.14):
    n=int(dur*SR); x=bandpass(noise(n),1500,6000)*env(n,0.003,0.05,0.2,0.08); return x*0.25
def sfx_thump(dur=0.25):   # puno sobre la mesa / sello
    n=int(dur*SR); t=np.arange(n)/SR; f=np.linspace(110,45,n); x=np.sin(2*np.pi*np.cumsum(f)/SR)*env(n,0.002,0.12,0.15,0.1); x+=lowpass(noise(n),300)*env(n,0.001,0.04,0,0.02)*0.8; return x*0.8
def sfx_stamp():
    x=sfx_thump(0.2); c=bandpass(noise(int(0.05*SR)),2000,7000)*env(int(0.05*SR),0.001,0.03,0,0.02); x[:len(c)]+=c*0.5; return x
def sfx_whoosh(dur=0.5):   # entrada/salida de personaje
    n=int(dur*SR); x=bandpass(noise(n),300,2500)*env(n,0.15,0.2,0.4,0.15); return x*0.45
def sfx_clack(dur=0.09):   # ficha sobre la mesa
    n=int(dur*SR); t=np.arange(n)/SR; x=np.sin(2*np.pi*900*t)*env(n,0.001,0.03,0.1,0.05)+bandpass(noise(n),2500,8000)*env(n,0.001,0.02,0,0.03); return x*0.4
def sfx_tick(dur=0.05):
    n=int(dur*SR); x=bandpass(noise(n),3000,9000)*env(n,0.001,0.02,0,0.02); return x*0.3
def sfx_draw(dur=1.5):     # linea que se dibuja: lapiz sobre papel
    n=int(dur*SR); x=bandpass(noise(n),2000,6000)*env(n,0.05,dur*0.5,0.6,dur*0.4)*(0.7+0.3*np.sin(np.arange(n)/SR*37)); return x*0.18
def sfx_flip(dur=0.18):    # pagina de calendario
    n=int(dur*SR); x=bandpass(noise(n),1000,5000)*env(n,0.01,0.08,0.3,0.08); return x*0.35
def sfx_stinger(dur=1.6):  # entrada de acto: nota grave + tick
    n=int(dur*SR); t=np.arange(n)/SR; x=(np.sin(2*np.pi*110*t)+0.5*np.sin(2*np.pi*220*t)+0.25*np.sin(2*np.pi*330*t))*env(n,0.01,0.6,0.35,0.9); return x*0.35
SFX={'slide':sfx_slide,'pop':sfx_pop,'unpop':sfx_unpop,'thump':sfx_thump,'stamp':sfx_stamp,'whoosh':sfx_whoosh,'clack':sfx_clack,'tick':sfx_tick,'draw':sfx_draw,'flip':sfx_flip,'stinger':sfx_stinger}
def pista_sfx(eventos, n):
    out=np.zeros(n,np.float32); count={}
    ult={}  # anti-metralla: no repetir el mismo sfx en <120 ms
    for t,kind,vol in sorted(eventos):
        if kind not in SFX: continue
        if kind in ult and t-ult[kind]<0.12: continue
        ult[kind]=t; count[kind]=count.get(kind,0)+1
        x=SFX[kind]()*vol; i=int(t*SR)
        if i>=n: continue
        m=min(len(x),n-i); out[i:i+m]+=x[:m]
    print('sfx:',count); return out
# ---------------------------------------------------------------- musica
def cama(n, pistas, fade=4.0, gain_db=-23.0):
    """encadena pistas con crossfade hasta cubrir n muestras; normaliza cada pista a -20 LUFS aprox (RMS)."""
    out=np.zeros(n,np.float32); pos=0; k=0; F=int(fade*SR)
    while pos<n:
        x=cargar(pistas[k%len(pistas)]); k+=1
        x=x/(np.sqrt(np.mean(x**2))+1e-6)*0.1           # RMS comun
        # recortar 1.5 s de cabeza (silencios) y fundido de entrada/salida
        x=x[int(1.5*SR):]; x[:F]*=np.linspace(0,1,F); x[-F:]*=np.linspace(1,0,F)
        m=min(len(x),n-pos); out[pos:pos+m]+=x[:m]; pos+=len(x)-F
    out[:int(0.5*SR)]*=np.linspace(0,1,int(0.5*SR))
    return out*db(gain_db)/0.1*0.1   # gain relativo al RMS 0.1
def ducking(music, voice, atk=0.05, rel=0.6, depth_db=-9.0):
    """baja la musica cuando hay voz (envolvente RMS de la voz, suavizada)."""
    hop=int(0.02*SR); n=len(voice); envl=np.zeros(n//hop+1,np.float32)
    for i in range(0,n,hop): envl[i//hop]=np.sqrt(np.mean(voice[i:i+hop]**2))
    thr=np.percentile(envl[envl>0],20) if (envl>0).any() else 0.01
    g=np.ones_like(envl); on=envl>thr*1.5
    ga=math.exp(-hop/SR/atk); gr=math.exp(-hop/SR/rel); cur=1.0
    for i in range(len(g)):
        target=db(depth_db) if on[i] else 1.0
        cur=cur*(ga if target<cur else gr)+target*(1-(ga if target<cur else gr)); g[i]=cur
    gfull=np.repeat(g,hop)[:len(music)]
    if len(gfull)<len(music): gfull=np.pad(gfull,(0,len(music)-len(gfull)),constant_values=gfull[-1])
    return music*gfull
def main():
    voz_p,ev_p,out=sys.argv[1],sys.argv[2],sys.argv[3]
    voz=cargar(voz_p); n=len(voz)
    ev=json.load(open(ev_p,encoding='utf-8'))
    pistas=[os.path.join(os.path.dirname(__file__),'musica',p) for p in ev.get('musica',['Lost_Frontier.mp3','Deliberate_Thought.mp3'])]
    rv=np.sqrt(np.mean(voz**2))
    mus=cama(n,pistas,gain_db=0.0); mus=mus/(np.sqrt(np.mean(mus**2))+1e-9)*rv*db(ev.get('musica_db',-14.0))   # cortina: X dB bajo la voz
    mus=ducking(mus,voz,depth_db=ev.get('duck_db',-6.0))
    sfx=pista_sfx([(e['t'],e['kind'],e.get('vol',1.0)) for e in ev['eventos']],n); sfx=sfx/(np.abs(sfx).max()+1e-9)*rv*db(ev.get('sfx_db',6.0))  # picos de sfx ~ +6 dB sobre el RMS de voz
    mix=voz+mus+sfx
    # limitador suave
    peak=np.abs(mix).max(); mix=mix/max(1.0,peak/0.95)
    sf.write(out,mix,SR); print(f'mezcla -> {out}  voz rms {20*np.log10(np.sqrt(np.mean(voz**2))+1e-9):.1f} dB  musica rms {20*np.log10(np.sqrt(np.mean(mus**2))+1e-9):.1f} dB  sfx rms {20*np.log10(np.sqrt(np.mean(sfx**2))+1e-9):.1f} dB')
if __name__=='__main__': main()
