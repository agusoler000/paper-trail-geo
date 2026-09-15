# -*- coding: utf-8 -*-
"""Mezcla v2 (enfoque dramatico): voz + cortina por ACTO (cues generadas a medida, sin derechos de terceros)
+ pulso grave sintetizado que acelera en los actos III-V + efectos de papel + silencio-golpe en revelaciones.

    python mezcla2.py <voz.wav> <eventos.json> <tiempos.json> <salida.wav>

eventos.json puede traer "cues": [{"beats":[0,1,2,3],"file":"musica/cue_01_intro.mp3","db":-13}, ...]
Cada cue cubre los beats indicados (segun tiempos.json); si es mas corta se repite con crossfade; entre cues
hay crossfade de 3 s. El pulso se configura con "pulso": [{"beats":[6],"bpm":[60,80],"db":-16}, ...].
"""
import json, sys, os, math, subprocess
import numpy as np, soundfile as sf
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from mezcla import cargar, db, pista_sfx, ducking, SR

# COMPRESOR SUAVE SOBRE LA VOZ (2026-09-15, auditoria §6.5). El ep. 06 se entrego con la voz a
# -29 dBFS de media y 3,5 dB de rango; la referencia del canal integra -14,5 LUFS con LRA 2,1. El
# problema no es solo el nivel: con este rango, las lineas flojas se pierden bajo la cortina y la
# de al lado suena bien, asi que subir el master entero no alcanza. 3:1 sobre -18 dB empareja la
# voz ANTES de la mezcla, que es donde hay que hacerlo (despues ya esta mezclada con la musica).
# Se hace con ffmpeg (`acompressor`) y no con numpy a proposito: es exactamente el filtro que
# nombra la especificacion, esta probado, y reimplementar una envolvente de ataque/relajacion a
# mano es codigo nuevo que habria que verificar sin necesidad.
COMP='acompressor=threshold=-18dB:ratio=3:attack=10:release=150:makeup=2:knee=4'

def comprimir(voz_p, activo=True):
    """Devuelve la ruta del wav de voz comprimido (o el original si `activo` es False)."""
    if not activo: return voz_p
    out=os.path.splitext(voz_p)[0]+'_comp.wav'
    subprocess.run(['ffmpeg','-v','error','-y','-i',voz_p,'-af',COMP,'-ac','1','-ar',str(SR),out],check=True)
    return out

def cue_track(n, cues, beats, fade=3.0):
    out=np.zeros(n,np.float32); F=int(fade*SR)
    for c in cues:
        t0=beats[min(c['beats'])]['inicio']-c.get('pre',1.5); t1=beats[max(c['beats'])]['fin']+c.get('post',1.5)
        i0=max(0,int(t0*SR)); i1=min(n,int(t1*SR)); L=i1-i0
        if L<=0: continue
        x=cargar(c['file']); x=x/(np.sqrt(np.mean(x**2))+1e-9)
        # cubrir L muestras repitiendo con crossfade si hace falta
        seg=np.zeros(L,np.float32); pos=0
        while pos<L:
            m=min(len(x),L-pos); chunk=x[:m].copy()
            if pos>0: chunk[:F]*=np.linspace(0,1,min(F,m))[:m]  # entrada suave en la repeticion
            seg[pos:pos+m]+=chunk; pos+=len(x)-F
        # fundidos de entrada/salida de la cue
        fi=min(F,L//2); seg[:fi]*=np.linspace(0,1,fi); seg[-fi:]*=np.linspace(1,0,fi)
        out[i0:i1]+=seg*db(c.get('db',-13.0))
    return out

def pulso_track(n, pulsos, beats, rv):
    out=np.zeros(n,np.float32)
    for p in pulsos:
        t0=beats[min(p['beats'])]['inicio']; t1=beats[max(p['beats'])]['fin']; i0=int(t0*SR); i1=min(n,int(t1*SR)); L=i1-i0
        bpm=np.linspace(p['bpm'][0],p['bpm'][1],L); ph=np.cumsum(bpm/60/SR); seg=np.zeros(L,np.float32)
        for k in np.where(np.diff(np.floor(ph))>0)[0]:
            M=int(0.2*SR); tt=np.arange(M)/SR; beat=np.sin(2*np.pi*np.linspace(58,36,M)*tt)*np.exp(-tt/0.06)
            m=min(M,L-k); seg[k:k+m]+=beat[:m]
        seg=seg/(np.abs(seg).max()+1e-9)*np.linspace(0.3,1.0,L)   # crece a lo largo del acto
        fi=int(2*SR); seg[:fi]*=np.linspace(0,1,fi); seg[-fi:]*=np.linspace(1,0,fi)
        out[i0:i1]+=seg*rv*db(p.get('db',-10.0))
    return out

def main():
    voz_p,ev_p,ti_p,out=sys.argv[1:5]
    crudo=cargar(voz_p)
    voz=cargar(comprimir(voz_p,'--sin-comp' not in sys.argv)); n=min(len(voz),len(crudo)) or len(voz)
    voz=voz[:n] if len(voz)>=n else np.pad(voz,(0,n-len(voz)))
    rv=np.sqrt(np.mean(voz**2))
    f0=lambda x:20*np.log10(np.sqrt(np.mean(x**2))+1e-9)
    print('voz: %.1f dB -> %.1f dB tras el compresor (%s)'%(f0(crudo),f0(voz),COMP.split('=')[0]))
    ev=json.load(open(ev_p,encoding='utf-8')); beats=json.load(open(ti_p,encoding='utf-8'))['beats']
    base=os.path.dirname(os.path.abspath(__file__))
    cues=[dict(c,file=os.path.join(base,c['file'])) for c in ev['cues']]
    mus=cue_track(n,cues,beats); mus=mus/(np.sqrt(np.mean(mus**2))+1e-9)*rv*db(ev.get('musica_db',-13.0))
    mus=ducking(mus,voz,depth_db=ev.get('duck_db',-5.0))
    pul=pulso_track(n,ev.get('pulso',[]),beats,rv); pul=ducking(pul,voz,depth_db=-3.0)
    sfx=pista_sfx([(e['t'],e['kind'],e.get('vol',1.0)) for e in ev['eventos']],n); sfx=sfx/(np.abs(sfx).max()+1e-9)*rv*db(ev.get('sfx_db',6.0))
    # "silencio antes de la revelacion": 0.6 s de musica casi muda antes de cada stinger
    for e in ev['eventos']:
        if e['kind']=='stinger':
            i=int(e['t']*SR); a=max(0,i-int(0.7*SR)); mus[a:i]*=np.linspace(1,0.05,i-a); pul[a:i]*=np.linspace(1,0.05,i-a)
    mix=voz+mus+pul+sfx; mix=mix/max(1.0,np.abs(mix).max()/0.95)
    sf.write(out,mix,SR)
    f=lambda x:20*np.log10(np.sqrt(np.mean(x**2))+1e-9)
    print(f'mezcla2 -> {out}  voz {f(voz):.1f} dB  musica {f(mus):.1f}  pulso {f(pul):.1f}  sfx {f(sfx):.1f}')
if __name__=='__main__': main()
