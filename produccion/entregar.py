# -*- coding: utf-8 -*-
"""Entrega final de un episodio = cuerpo + INTRO del canal + OUTRO del canal (regla de Agustin 2026-09-07: TODOS los videos).

v2 (2026-09-08, analisis del dia 1: 16 s sin voz mataban la retencion): la intro va DESPUES del cold open.
    --intro_at S   : la intro del canal se inserta en el segundo S del cuerpo (fin del cold open). Sin esta opcion
                     se mantiene el orden viejo (intro al principio), solo para reproducir entregas anteriores.
    --audio  mezcla.wav : reemplaza el audio del cuerpo.
    --head tramo.mp4 --head_dur N : reemplaza los primeros N s del cuerpo por un tramo re-renderizado.

    python entregar.py cuerpo.mp4 salida.mp4 --intro_at 26.5 [--audio mezcla.wav] [--head tramo.mp4 --head_dur 8]

Produce salida.mp4 (1080p, crf 19) y salida_720p.mp4 (<30 MB para enviar).
"""
import os, sys, subprocess
BASE=os.path.dirname(os.path.abspath(__file__))
# Intro del canal. La v3 (15-sep) es la vigente: mapa de papel + archivo + el sello sobre el
# memorandum censurado pidiendo LIKE y suscripcion. Dura 12,5 s contra los 13,96 de la v2.
# Se puede forzar otra con --intro <ruta> para reproducir entregas viejas.
INTRO_V3=os.path.join(BASE,'intro_v3','intro_canal_v3.mp4')
INTRO=INTRO_V3 if os.path.exists(INTRO_V3) else os.path.join(BASE,'intro_canal.mp4')
OUTRO=os.path.join(BASE,'outro_canal.mp4')
def arg(a,k,default=None,cast=str):
    return cast(a[a.index(k)+1]) if k in a else default
def main():
    a=sys.argv[1:]; body=a[0]; out=a[1]
    audio=arg(a,'--audio'); head=arg(a,'--head'); hd=arg(a,'--head_dur',0.0,float); intro_at=arg(a,'--intro_at',None,float)
    intro=arg(a,'--intro',INTRO)
    print('intro:', os.path.basename(intro), '|', os.path.basename(OUTRO))
    ins=['-i',intro,'-i',body,'-i',OUTRO]; n=3; fc=''
    if head:
        ins+=['-i',head]; fc+=f'[3:v]scale=1920:1080,fps=24,format=yuv420p[hv];[1:v]trim=start={hd},setpts=PTS-STARTPTS,scale=1920:1080,fps=24,format=yuv420p[bv];[hv][bv]concat=n=2:v=1:a=0[body_v];'; n+=1
    else: fc+='[1:v]scale=1920:1080,fps=24,format=yuv420p[body_v];'
    if audio: ins+=['-i',audio]; fc+=f'[{n}:a]aformat=sample_rates=48000:channel_layouts=stereo[body_a];'; n+=1
    else: fc+='[1:a]aformat=sample_rates=48000:channel_layouts=stereo[body_a];'
    fc+='[0:v]scale=1920:1080,fps=24,format=yuv420p[iv];[0:a]aformat=sample_rates=48000:channel_layouts=stereo[ia];[2:v]scale=1920:1080,fps=24,format=yuv420p[ov];[2:a]aformat=sample_rates=48000:channel_layouts=stereo[oa];'
    if intro_at:
        S=intro_at
        fc+=(f'[body_v]split[bv1][bv2];[body_a]asplit[ba1][ba2];'
             f'[bv1]trim=end={S},setpts=PTS-STARTPTS[v1];[ba1]atrim=end={S},asetpts=PTS-STARTPTS[a1];'
             f'[bv2]trim=start={S},setpts=PTS-STARTPTS[v2];[ba2]atrim=start={S},asetpts=PTS-STARTPTS[a2];'
             f'[v1][a1][iv][ia][v2][a2][ov][oa]concat=n=4:v=1:a=1[v][am]')
    else:
        fc+='[iv][ia][body_v][body_a][ov][oa]concat=n=3:v=1:a=1[v][am]'
    # NORMALIZACION DEL MASTER (2026-09-15, auditoria §2.4 V4). El ep. 06 se entrego a -29 dBFS de
    # media; la referencia que mide el canal integra -14,5 LUFS. **YouTube baja lo fuerte pero no
    # sube lo flojo**: un master a -29 suena mas bajo que sus vecinos del feed y el espectador lo
    # lee como "peor producido" antes de entender nada. LRA 9 deja respirar las revelaciones (la
    # regla del canal es bajar la voz para la tension); comprimir mas las mataria.
    fc+=';[am]loudnorm=I=-14:TP=-1.5:LRA=9[a]'
    subprocess.run(['ffmpeg','-v','error','-y']+ins+['-filter_complex',fc,'-map','[v]','-map','[a]','-c:v','libx264','-pix_fmt','yuv420p','-crf','19','-preset','medium','-c:a','aac','-b:a','192k','-shortest',out],check=True)
    o720=os.path.splitext(out)[0]+'_720p.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-i',out,'-vf','scale=1280:720','-c:v','libx264','-crf','31','-preset','medium','-c:a','aac','-b:a','128k',o720],check=True)
    for p in (out,o720): print(p, round(os.path.getsize(p)/1e6,1),'MB')
    if intro_at: print('intro insertada en %.1f s del cuerpo (cold open primero)'%intro_at)
if __name__=='__main__': main()
