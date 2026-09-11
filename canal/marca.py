# -*- coding: utf-8 -*-
# Identidad del canal: avatar, banner, marca de agua y plantilla de miniatura.
# 0 creditos: todo con PIL sobre las texturas y objetos de papel del piloto.
# Uso: python marca.py ["NOMBRE DEL CANAL"] ["tagline"]
import sys, os, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
AQUI=os.path.dirname(os.path.abspath(__file__)); RAIZ=os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ,'produccion'))
import props as PR
from props import TINTA, PAPEL, OCRE, ROJO, FONT, FONTC

NOMBRE = sys.argv[1] if len(sys.argv)>1 else 'PAPER TRAIL'
TAGLINE = sys.argv[2] if len(sys.argv)>2 else 'Follow the paper.'
OUT=os.path.join(AQUI,'out'); os.makedirs(OUT,exist_ok=True)
A=os.path.join(RAIZ,'produccion','assets'); L=os.path.join(RAIZ,'pruebas','look'); E=os.path.join(RAIZ,'pruebas','elenco','cut')
papel_tx=Image.open(os.path.join(A,'papel_1920.png')).convert('RGBA')
madera_tx=Image.open(os.path.join(A,'madera_1920.png')).convert('RGBA')
mapa_hoja=Image.open(os.path.join(L,'mapa_hoja.png')).convert('RGBA')

def tile(tx, size):
    out=Image.new('RGBA',size)
    for y in range(0,size[1],tx.height):
        for x in range(0,size[0],tx.width): out.paste(tx,(x,y))
    return out
def pegar(base, p, xy, blur=8, alpha=120, off=(8,10)):
    s=Image.new('RGBA',p.size,(0,0,0,0)); s.putalpha(p.split()[3].point(lambda v:min(v,alpha)).filter(ImageFilter.GaussianBlur(blur)))
    base.alpha_composite(s,(xy[0]+off[0],xy[1]+off[1])); base.alpha_composite(p,xy)
def acabado(im):
    # grano global + registro offset desalineado (identidad de marca, ESTILO 2.2)
    g=np.asarray(tile(papel_tx,im.size).convert('L')).astype(np.float32)-215
    arr=np.clip(np.asarray(im.convert('RGB')).astype(np.float32)+g[...,None]*0.3,0,255).astype(np.uint8)
    r,gc,b=Image.fromarray(arr).split(); r=ImageChops.offset(r,2,0)
    return Image.merge('RGB',(r,gc,b))
def persp(im, top_in, h):
    src=[(0,0),(im.width,0),(im.width,im.height),(0,im.height)]
    dst=[(top_in,0),(im.width-top_in,0),(im.width,h),(0,h)]
    Aa=[];B=[]
    for (x1,y1),(x2,y2) in zip(dst,src):
        Aa+=[[x1,y1,1,0,0,0,-x2*x1,-x2*y1],[0,0,0,x1,y1,1,-y2*x1,-y2*y1]]; B+=[x2,y2]
    c=np.linalg.solve(np.array(Aa,float),np.array(B,float))
    t=im.transform((im.width,h),Image.PERSPECTIVE,c,Image.BICUBIC)
    # las esquinas que quedan fuera del trapecio se rellenan con madera lisa (si no, quedan transparentes)
    base=Image.new('RGBA',t.size,(82,54,36,255)); base.alpha_composite(t); return base
def tablero(W,H,MESA_Y):
    t=persp(tile(madera_tx,(W+400,H)),160,H-MESA_Y).resize((W,H-MESA_Y))
    grad=Image.linear_gradient('L').resize((W,H-MESA_Y)).point(lambda v:int((255-v)*0.45))
    sh=Image.new('RGBA',(W,H-MESA_Y),(20,12,6,255)); sh.putalpha(grad); t.alpha_composite(sh); return t
def vineta(im, color=(20,12,6), fuerza=0.7, blur=120, margen=100):
    W,H=im.size; vig=Image.new('L',(W,H),0); ImageDraw.Draw(vig).ellipse([-margen,-margen,W+margen,H+margen],fill=255)
    vig=vig.filter(ImageFilter.GaussianBlur(blur)); osc=Image.new('RGBA',(W,H),color+(255,)); osc.putalpha(vig.point(lambda v:int((255-v)*fuerza))); im.alpha_composite(osc)
def ficha(r, txt=None, size=None, color=OCRE, lines=None):
    # ficha ocre grande con anillo de tinta; texto opcional apilado
    def f(d): d.ellipse([2,2,2*r-2,2*r-2],fill=255)
    p=PR.papel((2*r+2,2*r+2),f,color,sombra=False); d=ImageDraw.Draw(p)
    d.ellipse([int(r*0.16),int(r*0.16),int(2*r-r*0.16),int(2*r-r*0.16)],outline=TINTA+(255,),width=max(3,r//40))
    d.ellipse([int(r*0.22),int(r*0.22),int(2*r-r*0.22),int(2*r-r*0.22)],outline=TINTA+(255,),width=max(2,r//80))
    if lines:
        fnt=FONTC(size); n=len(lines); lh=size*1.02; y0=r+1-(n-1)*lh/2
        for i,t in enumerate(lines): d.text((r+1,y0+i*lh),t,fill=TINTA+(255,),font=fnt,anchor='mm')
    elif txt: d.text((r+1,r+1),txt,fill=TINTA+(255,),font=FONT(size),anchor='mm')
    return p
def hoja_mapa(w, rot=0):
    m=mapa_hoja.resize((w,int(w*mapa_hoja.height/mapa_hoja.width)),Image.LANCZOS)
    return m.rotate(rot,resample=Image.BICUBIC,expand=True) if rot else m
def personaje(nombre, h):
    p=Image.open(os.path.join(E,nombre)).convert('RGBA'); return p.resize((int(p.width*h/p.height),h),Image.LANCZOS)
def lineas_nombre():
    w=NOMBRE.split()
    return w if len(w)<=3 else [NOMBRE]

# ---------------------------------------------------------------- AVATAR 800x800 (se ve en circulo)
def avatar_A():
    # madera + ficha ocre con el nombre apilado (la ficha ES el simbolo: lo que esta en juego)
    S=800; im=tile(madera_tx,(S,S)); vineta(im)
    ln=lineas_nombre(); fi=ficha(300,lines=ln,size=96 if len(ln)<=3 else 70)
    pegar(im,fi,(S//2-fi.width//2,S//2-fi.height//2),blur=14,alpha=150,off=(10,16))
    return acabado(im)
def avatar_B():
    # hoja de mapa sobre madera + ficha ocre con monograma
    S=800; im=tile(madera_tx,(S,S))
    m=hoja_mapa(1400,rot=-6); pegar(im,m,(-330,-120),blur=12,alpha=140)
    ini=''.join(w[0] for w in NOMBRE.split() if w.lower()!='the')[:2]
    fi=ficha(150,txt=ini,size=120); pegar(im,fi,(S//2-fi.width//2+30,S//2-fi.height//2+20),blur=10,alpha=150,off=(8,12))
    return acabado(im)
def avatar_C():
    # tarjeta de papel con el nombre, sobre madera (como las tarjetas del video)
    S=800; im=tile(madera_tx,(S,S)); vineta(im)
    c=PR.card('\n'.join(lineas_nombre()),w=540,h=540,size=118,color=PAPEL); c=c.rotate(-3,resample=Image.BICUBIC,expand=True)
    pegar(im,c,(S//2-c.width//2,S//2-c.height//2),blur=14,alpha=150,off=(10,16))
    fi=ficha(70); pegar(im,fi,(S//2+150,S//2+150),blur=8,alpha=140,off=(6,10))
    return acabado(im)

# ---------------------------------------------------------------- BANNER 2560x1440 (zona segura 1546x423 centrada)
def banner():
    W,H=2560,1440; SX0,SY0,SX1,SY1=507,508,2053,931
    im=tile(papel_tx,(W,H)); vineta(im,color=(70,58,45),fuerza=0.4,blur=260,margen=300)
    MESA_Y=470   # borde de la mesa por encima de la zona segura: el nombre queda entero sobre el mapa
    # personajes detras de la mesa, fuera de la zona segura (se ven en escritorio y TV)
    for nombre,x,h in (('01_burocrata.png',110,720),('02_militar.png',2000,720)):
        p=personaje(nombre,h); pegar(im,p,(x,MESA_Y-h+300),blur=16,alpha=130,off=(22,30))
    im.alpha_composite(tablero(W,H,MESA_Y),(0,MESA_Y)); ImageDraw.Draw(im).rectangle([0,MESA_Y-6,W,MESA_Y+8],fill=(58,38,26,255))
    # hoja de mapa apoyada, cubriendo la zona segura
    m=hoja_mapa(2000); m=persp(m,130,int(m.height*0.66)); m=m.rotate(1.2,resample=Image.BICUBIC,expand=True)
    pegar(im,m,(W//2-m.width//2,MESA_Y+50),blur=10,alpha=130,off=(8,14))
    # tarjeta con el nombre + tagline, centradas en la zona segura
    c=PR.card(NOMBRE,size=150,color=PAPEL); c=c.rotate(-1.2,resample=Image.BICUBIC,expand=True)
    cx=W//2-c.width//2; cy=(SY0+SY1)//2-c.height//2-60; pegar(im,c,(cx,cy),blur=12,alpha=140,off=(10,14))
    t=PR.card(TAGLINE,size=58,color=OCRE); t=t.rotate(0.8,resample=Image.BICUBIC,expand=True)
    pegar(im,t,(W//2-t.width//2,cy+c.height+18),blur=10,alpha=130,off=(8,10))
    fi=ficha(48); pegar(im,fi,(1600,SY1+60),blur=6,alpha=130,off=(6,8))
    out=acabado(im)
    g=out.copy(); ImageDraw.Draw(g).rectangle([SX0,SY0,SX1,SY1],outline=(184,64,47),width=6); g.save(os.path.join(OUT,'_banner_guia.jpg'),quality=88)
    return out

# ---------------------------------------------------------------- MARCA DE AGUA 150x150 (PNG alpha)
def marca_agua():
    return ficha(300).resize((150,150),Image.LANCZOS)

# ---------------------------------------------------------------- PLANTILLA DE MINIATURA 1280x720
def miniatura(titulo, sub=None, pers='01_burocrata.png', mapa=None):
    W,H=1280,720; im=tile(papel_tx,(W,H)); vineta(im,color=(70,58,45),fuerza=0.45,blur=150,margen=200); MESA_Y=440
    p=personaje(pers,600); pegar(im,p,(W-p.width-10,MESA_Y-600+230),blur=12,alpha=130,off=(14,20))
    im.alpha_composite(tablero(W,H,MESA_Y),(0,MESA_Y)); ImageDraw.Draw(im).rectangle([0,MESA_Y-4,W,MESA_Y+6],fill=(58,38,26,255))
    if mapa:
        hm=Image.open(mapa).convert('RGBA'); m=hm.resize((1000,int(1000*hm.height/hm.width)),Image.LANCZOS)
    else: m=hoja_mapa(1000)
    m=persp(m,70,int(m.height*0.5)); pegar(im,m,(40,MESA_Y+20),blur=8,alpha=120)
    # titulo: tarjetas apiladas a la izquierda, ancho maximo 3/5 del cuadro; la ultima linea en rojo (unico rojo)
    lines=titulo.split('\n'); y=50; maxw=int(W*0.6)
    for i,t in enumerate(lines):
        col=ROJO if i==len(lines)-1 and len(lines)>1 else TINTA; size=96
        c=PR.card(t,size=size,color=PAPEL,tcolor=col)
        while c.width>maxw and size>48: size-=6; c=PR.card(t,size=size,color=PAPEL,tcolor=col)
        c=c.rotate(-1.5 if i%2==0 else 1,resample=Image.BICUBIC,expand=True)
        pegar(im,c,(40,y),blur=10,alpha=130); y+=c.height+2
    if sub:
        s=PR.card(sub,size=40,color=OCRE); pegar(im,s,(40,MESA_Y+H-MESA_Y-s.height-30),blur=8,alpha=120)
    return acabado(im)

if __name__=='__main__':
    avatar_A().save(os.path.join(OUT,'avatar_A.png')); avatar_B().save(os.path.join(OUT,'avatar_B.png')); avatar_C().save(os.path.join(OUT,'avatar_C.png'))
    banner().save(os.path.join(OUT,'banner_2560x1440.png'))
    marca_agua().save(os.path.join(OUT,'marca_agua_150.png'))
    miniatura('673 AIRLINERS.\nONE IN FIVE\nCANNOT FLY.', sub='HOW UKRAINE GROUNDED RUSSIA', pers='11_zelensky.png',
              mapa=os.path.join(A,'mapa_rusia.png')).save(os.path.join(OUT,'miniatura_01.png'))
    # hoja de contacto: los tres avatares recortados en circulo como los muestra YouTube
    hoja=Image.new('RGB',(1280,420),(30,30,30))
    for i,f in enumerate(('avatar_A.png','avatar_B.png','avatar_C.png')):
        a=Image.open(os.path.join(OUT,f)).convert('RGB').resize((400,400)); mk=Image.new('L',(400,400),0); ImageDraw.Draw(mk).ellipse([0,0,399,399],fill=255)
        hoja.paste(a,(20+i*420,10),mk)
    hoja.save(os.path.join(OUT,'_avatares_circulo.jpg'),quality=90)
    print('ok ->',OUT)
