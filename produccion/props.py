# -*- coding: utf-8 -*-
# Objetos de papel para el piloto. Cada uno = PNG con alpha, textura de papel, borde de corte y sombra propia.
import numpy as np, math, os
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont
rng=np.random.default_rng(9)
TINTA=(34,32,28); PAPEL=(233,223,203); OCRE=(217,164,65); AZUL=(43,76,111); ROJO=(184,64,47); MAPA=(220,207,180)
MADERA=(107,74,51); GRIS=(120,118,110); VERDE=(143,169,140); BLANCO=(245,240,228); HIELO=(200,215,225)
def FONT(s): return ImageFont.truetype('C:/Windows/Fonts/GeorgiaPro-Bold.ttf',s)
def FONTC(s): return ImageFont.truetype('C:/Windows/Fonts/GeorgiaPro-CondBold.ttf',s)
def grano(size):
    g=rng.random((size[1]//5+2,size[0]//5+2)).astype(np.float32)
    return np.asarray(Image.fromarray((g*255).astype(np.uint8)).resize(size,Image.BICUBIC)).astype(np.float32)/255-0.5
def papel(size, draw_fn, color, sombra=True):
    """draw_fn(d) dibuja la mascara con fill=255. Devuelve RGBA con textura+bisel+sombra."""
    size=(int(size[0]),int(size[1]))
    m=Image.new('L',size,0); draw_fn(ImageDraw.Draw(m))
    rgb=np.zeros((size[1],size[0],3),np.float32)+np.array(color,np.float32)+grano(size)[...,None]*16
    edge=np.asarray(ImageChops.subtract(m,m.filter(ImageFilter.MinFilter(5)))).astype(np.float32)/255
    rgb+=edge[...,None]*22
    p=Image.fromarray(np.clip(rgb,0,255).astype(np.uint8)).convert('RGBA'); p.putalpha(m)
    if not sombra: return p
    out=Image.new('RGBA',(size[0]+14,size[1]+16),(0,0,0,0))
    s=Image.new('RGBA',size,(0,0,0,0)); s.putalpha(m.point(lambda v:min(v,110)).filter(ImageFilter.GaussianBlur(5)))
    out.alpha_composite(s,(8,10)); out.alpha_composite(p,(0,0)); return out
def texto(p, txt, size, xy, color=TINTA, font=None, anchor='mm'):
    d=ImageDraw.Draw(p); d.text(xy,txt,fill=color+(255,),font=(font or FONT)(size),anchor=anchor)
def avion(color=BLANCO, w=220):
    h=int(w*0.5)
    def f(d): d.polygon([(0,h*0.55),(w,h*0.2),(w*0.62,h*0.6),(w*0.55,h),(w*0.45,h*0.62)],fill=255)
    p=papel((w+2,h+2),f,color); d=ImageDraw.Draw(p); d.line([(0,h*0.55),(w*0.62,h*0.6)],fill=TINTA+(255,),width=3); return p
def chip(color=OCRE, r=44, txt=None):
    def f(d): d.ellipse([2,2,2*r-2,2*r-2],fill=255)
    p=papel((2*r+2,2*r+2),f,color); d=ImageDraw.Draw(p); d.ellipse([12,12,2*r-10,2*r-10],outline=TINTA+(255,),width=3)
    if txt: texto(p,txt,int(r*0.7),(r+1,r+1))
    return p
def card(txt, w=None, h=None, size=64, color=PAPEL, tcolor=TINTA):
    f=FONT(size); tmp=ImageDraw.Draw(Image.new('L',(10,10))); bb=tmp.multiline_textbbox((0,0),txt,font=f,align='center')
    tw,th=bb[2]-bb[0],bb[3]-bb[1]; w=w or tw+70; h=h or th+50
    def g(d): d.rounded_rectangle([1,1,w-2,h-2],radius=10,fill=255)
    p=papel((w,h),g,color); d=ImageDraw.Draw(p); d.rounded_rectangle([8,8,w-9,h-9],radius=8,outline=TINTA+(255,),width=3)
    d.multiline_text((w/2,h/2),txt,fill=tcolor+(255,),font=f,anchor='mm',align='center'); return p
def rect(w,h,color,r=8):
    def f(d): d.rounded_rectangle([1,1,w-2,h-2],radius=r,fill=255)
    return papel((w,h),f,color)
def sello(txt, color=ROJO, size=54):
    p=card(txt,size=size,color=PAPEL,tcolor=color); d=ImageDraw.Draw(p); d.rounded_rectangle([8,8,p.width-22,p.height-24],radius=8,outline=color+(255,),width=5); return p
def dron(w=90):
    def f(d):
        d.rectangle([w*0.35,w*0.4,w*0.65,w*0.6],fill=255); d.line([(0,w*0.5),(w,w*0.5)],fill=255,width=6)
        for x in (0,w): d.ellipse([x-w*0.18,w*0.32,x+w*0.18,w*0.68],fill=255)
    return papel((w+2,w+2),f,GRIS)
def tren(w=200):
    h=int(w*0.35)
    def f(d):
        d.rounded_rectangle([0,h*0.2,w*0.35,h*0.85],radius=6,fill=255); d.rounded_rectangle([w*0.38,h*0.3,w*0.68,h*0.85],radius=6,fill=255); d.rounded_rectangle([w*0.71,h*0.3,w,h*0.85],radius=6,fill=255)
        for x in (w*0.08,w*0.28,w*0.45,w*0.62,w*0.78,w*0.95): d.ellipse([x-h*0.12,h*0.72,x+h*0.12,h*0.98],fill=255)
        d.rectangle([w*0.04,0,w*0.1,h*0.25],fill=255)
    return papel((w+2,h+2),f,AZUL)
def calendario(n, w=150):
    p=rect(w,int(w*1.1),PAPEL); d=ImageDraw.Draw(p); d.rectangle([4,4,w-4,int(w*0.28)],fill=ROJO+(255,)); texto(p,str(n),int(w*0.5),(w/2,w*0.68)); return p
def poliza(w=320,h=220,titulo='POLICY'):
    p=rect(w,h,BLANCO,r=4); d=ImageDraw.Draw(p)
    for i,y in enumerate(range(50,h-30,26)): d.line([(28,y),(w-28-(i%3)*40,y)],fill=(150,145,130,255),width=4)
    texto(p,titulo,30,(w/2,26)); return p
def alfombra(w=260,h=170):
    def f(d): d.rounded_rectangle([1,1,w-2,h-2],radius=6,fill=255)
    p=papel((w,h),f,ROJO); d=ImageDraw.Draw(p)
    for i in range(3): d.rectangle([12+i*8,12+i*8,w-13-i*8,h-13-i*8],outline=OCRE+(255,),width=3)
    return p
def cerca(w=1300,h=90):
    def f(d):
        for x in range(0,w,60): d.rectangle([x,10,x+16,h],fill=255)
        d.rectangle([0,30,w,42],fill=255); d.rectangle([0,64,w,76],fill=255)
    return papel((w+2,h+2),f,MADERA)
def bateria(w=140):
    h=int(w*0.7)
    def f(d):
        d.rounded_rectangle([0,h*0.45,w,h],radius=8,fill=255)
        for i in range(3): d.line([(w*0.3+i*w*0.2,h*0.5),(w*0.55+i*w*0.2,0)],fill=255,width=10)
    return papel((w+2,h+2),f,GRIS)
def tv(w=260):
    h=int(w*0.7); p=rect(w,h,TINTA,r=10); d=ImageDraw.Draw(p); d.rounded_rectangle([14,14,w-14,h-14],radius=6,fill=(90,110,120,255)); return p
def caja(w=90):
    p=rect(w,int(w*0.8),OCRE,r=4); d=ImageDraw.Draw(p); d.line([(0,int(w*0.4)),(w,int(w*0.4))],fill=TINTA+(255,),width=3); d.line([(w//2,0),(w//2,int(w*0.8))],fill=TINTA+(255,),width=3); return p
def sobre(w=160):
    h=int(w*0.65); p=rect(w,h,BLANCO,r=4); d=ImageDraw.Draw(p); d.line([(0,0),(w/2,h*0.55),(w,0)],fill=TINTA+(255,),width=3); return p
def gota(r=40):
    def f(d): d.ellipse([r*0.2,r*0.8,r*1.8,r*2.4],fill=255); d.polygon([(r,0),(r*0.25,r*1.4),(r*1.75,r*1.4)],fill=255)
    return papel((2*r+2,int(2.5*r)),f,TINTA)
def lingote(w=110):
    h=int(w*0.45)
    def f(d): d.polygon([(w*0.12,0),(w*0.88,0),(w,h),(0,h)],fill=255)
    return papel((w+2,h+2),f,OCRE)
def diamante(w=100):
    h=int(w*0.9)
    def f(d): d.polygon([(w*0.2,0),(w*0.8,0),(w,h*0.3),(w/2,h),(0,h*0.3)],fill=255)
    p=papel((w+2,h+2),f,HIELO); d=ImageDraw.Draw(p); d.line([(0,h*0.3),(w,h*0.3)],fill=TINTA+(255,),width=3); return p
def megafono(w=140):
    h=int(w*0.6)
    def f(d): d.polygon([(0,h*0.35),(w*0.35,h*0.35),(w,0),(w,h),(w*0.35,h*0.65),(0,h*0.65)],fill=255); d.rectangle([0,h*0.35,w*0.2,h*0.85],fill=255)
    return papel((w+2,h+2),f,ROJO)
def escudo(w=120):
    h=int(w*1.2)
    def f(d): d.polygon([(0,0),(w,0),(w,h*0.55),(w/2,h),(0,h*0.55)],fill=255)
    return papel((w+2,h+2),f,GRIS)
def tanque(w=90):
    h=int(w*0.55)
    def f(d): d.rounded_rectangle([0,h*0.45,w,h],radius=8,fill=255); d.rectangle([w*0.3,h*0.15,w*0.7,h*0.5],fill=255); d.rectangle([w*0.65,h*0.25,w,h*0.35],fill=255)
    return papel((w+2,h+2),f,VERDE)
def paraguas(w=260):
    h=int(w*0.6)
    def f(d): d.pieslice([0,0,w,w],180,360,fill=255); d.rectangle([w/2-4,w*0.45,w/2+4,h],fill=255)
    return papel((w+2,h+2),f,ROJO)
def telefono(w=70):
    h=int(w*1.3)
    def f(d): d.rounded_rectangle([0,0,w,h],radius=12,fill=255)
    p=papel((w+2,h+2),f,TINTA); d=ImageDraw.Draw(p); d.rounded_rectangle([8,14,w-8,h-18],radius=6,fill=(90,110,120,255)); return p
def tablero(rows, w=440):
    h=48*len(rows)+40; p=rect(w,h,TINTA,r=6); d=ImageDraw.Draw(p)
    for i,r in enumerate(rows): d.text((24,26+i*48),r,fill=OCRE+(255,),font=FONTC(34))
    return p
def sol(r=40):
    def f(d): d.ellipse([r*0.3,r*0.3,r*1.7,r*1.7],fill=255)
    return papel((2*r+2,2*r+2),f,OCRE)
def luna(r=40):
    def f(d): d.ellipse([r*0.3,r*0.3,r*1.7,r*1.7],fill=255)
    p=papel((2*r+2,2*r+2),f,BLANCO); m=Image.new('L',p.size,255); ImageDraw.Draw(m).ellipse([r*0.7,r*0.15,r*2.1,r*1.55],fill=0)
    p.putalpha(ImageChops.multiply(p.split()[3],m)); return p
def tab(txt,w=200,h=54):
    p=rect(w,h,OCRE,r=10); texto(p,txt,30,(w/2,h/2)); return p
def llave(w=120):
    h=int(w*0.35)
    def f(d): d.rectangle([w*0.2,h*0.35,w*0.85,h*0.65],fill=255); d.ellipse([0,0,h,h],fill=255); d.ellipse([w-h,0,w,h],fill=255)
    return papel((w+2,h+2),f,GRIS)
def humo(r=40):
    def f(d):
        for x,y,rr in [(r,r*1.2,r*0.7),(r*1.5,r*0.9,r*0.55),(r*0.6,r*0.8,r*0.5)]: d.ellipse([x-rr,y-rr,x+rr,y+rr],fill=255)
    return papel((int(2.2*r),2*r),f,(200,196,186))
def balanza(w=220):
    h=int(w*0.6)
    def f(d): d.rectangle([w/2-6,h*0.2,w/2+6,h],fill=255); d.rectangle([0,h*0.2,w,h*0.28],fill=255); d.rectangle([w*0.15,h*0.9,w*0.85,h],fill=255)
    return papel((w+2,h+2),f,TINTA)
def plano(w=200):
    h=int(w*0.7); p=rect(w,h,AZUL,r=4); d=ImageDraw.Draw(p)
    d.polygon([(w*0.1,h*0.55),(w*0.9,h*0.3),(w*0.6,h*0.6),(w*0.55,h*0.85),(w*0.48,h*0.62)],outline=BLANCO+(255,),width=3); return p
def barrera(w=260):
    h=40
    def f(d): d.rectangle([0,0,w,h],fill=255)
    p=papel((w+2,h+2),f,BLANCO); d=ImageDraw.Draw(p)
    for x in range(0,w,52): d.polygon([(x,0),(x+26,0),(x+52,h),(x+26,h)],fill=ROJO+(255,))
    return p
def periodico(txt, w=300, h=170, stamp=None):
    p=rect(w,h,BLANCO,r=3); d=ImageDraw.Draw(p); d.rectangle([12,12,w-12,44],fill=TINTA+(255,))
    d.multiline_text((w/2,100),txt,fill=TINTA+(255,),font=FONTC(30),anchor='mm',align='center')
    for y in range(140,h-10,10): d.line([(20,y),(w-20,y)],fill=(170,165,150,255),width=3)
    if stamp: d.ellipse([w-60,h-60,w-16,h-16],outline=ROJO+(255,),width=4); texto(p,stamp,22,(w-38,h-38),color=ROJO)
    return p
if __name__=='__main__':
    os.makedirs('assets',exist_ok=True)
    A={}
    A['avion']=avion(); A['avion_gris']=avion(GRIS); A['avion_chico']=avion(BLANCO,120); A['chip_aeroflot']=chip(OCRE,50,'A'); A['chip_ocre']=chip(OCRE,36); A['chip_aero']=chip(GRIS,34); A['chip_moscu']=chip(ROJO,30)
    A['dron']=dron(); A['tren']=tren(); A['poliza']=poliza(); A['alfombra']=alfombra(); A['cerca']=cerca(); A['bateria']=bateria(); A['tv']=tv(); A['caja']=caja()
    A['sobre']=sobre(); A['gota']=gota(); A['lingote']=lingote(); A['diamante']=diamante(); A['megafono']=megafono(); A['escudo']=escudo(); A['tanque']=tanque(); A['paraguas']=paraguas()
    A['telefono']=telefono(); A['sol']=sol(); A['luna']=luna(); A['llave']=llave(); A['humo']=humo(); A['balanza']=balanza(); A['plano']=plano(); A['barrera']=barrera()
    A['tab_fleet']=tab('FLEET'); A['tab_drone']=tab('DRONE'); A['tab_country']=tab('COUNTRY'); A['formulario']=poliza(220,150,'FORM'); A['tornillo']=chip(GRIS,16)
    A['sello_loss']=sello('LOSS'); A['sello_settled']=sello('SETTLED'); A['sello_noprice']=sello('NO PRICE'); A['sello_x']=sello('X',ROJO,90)
    A['cartel_sky']=card('SKY\nCLOSED',size=40,color=BLANCO,tcolor=ROJO)
    A['diario_1']=periodico('Russia offers\nairlines reassurances'); A['diario_2']=periodico('Foreign airlines\ncancel flights'); A['diario_3']=periodico('Turkish airlines\nstop flying',stamp='TR')
    A['tablero']=tablero(['SVO 1210  CANCELLED','LED 1225  CANCELLED','KZN 1240  CANCELLED','VVO 1305  CANCELLED','      WHY'])
    A['tablero_c']=tablero(['SVO 1210  CANCELLED','LED 1225  CANCELLED','KZN 1240  CANCELLED','VVO 1305  CANCELLED','OVB 1320  CANCELLED'])
    A['manual']=card('MANUAL',size=28,color=AZUL,tcolor=BLANCO); A['cal20']=calendario(20); A['cal3']=calendario(3)
    for k,v in A.items(): v.save(f'assets/prop_{k}.png')
    print(len(A),'props')
