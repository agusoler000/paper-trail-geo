# -*- coding: utf-8 -*-
# Hoja de mapa del ep. 3 (frente norte sobre Kiev desde Bielorrusia): Natural Earth 50m, Mercator sin distorsion.
# Mismo metodo que mapa_alemania.py: sitios REALES con etiqueta, nombres de paises, capas separadas para animar.
#  mapa03_base.png      mar + tierra + contornos + nombres de paises
#  mapa03_ciudades.png  puntos + etiquetas
#  mapa03_belarus.png   relleno de Bielorrusia (ocre, recortado al pais real)
#  mapa03_donbas.png    poligono a mano del Donbas (Donetsk + Luhansk) recortado a Ucrania, rojo apagado
#  mapa03_ejes.png      ejes de ataque en tinta punteada (Gomel->Chernihiv->Kyiv, Bryansk->Sumy, Kursk->Sumy, Belgorod->Kharkiv)
#  mapa03_muerte.png    franja de la muerte: hatch gris +-40 km sobre la linea de frente del este
#  mapa03_pts.json      pixeles de cada sitio (para anclar props con G('Sitio'))
# Kaliningrado no entra: punto de borde 'West edge' en el margen izquierdo a su latitud.
import json, math
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
from shapely.geometry import shape, box
LON0,LON1,LAT0,LAT1=22,41,46.5,56.5
def m(l): return math.log(math.tan(math.pi/4+math.radians(l)/2))
W=1500; SS=2
H=int(round(W*(m(LAT1)-m(LAT0))/math.radians(LON1-LON0)))   # sin distorsion
def proj(lon,lat):
    x=(lon-LON0)/(LON1-LON0)*W*SS; y=(m(LAT1)-m(lat))/(m(LAT1)-m(LAT0))*H*SS; return (x,y)
def pj(lon,lat): x,y=proj(lon,lat); return (x/SS,y/SS)
TINTA=(34,32,28); MAR=(206,196,172); TIERRA=(228,216,190); OCRE=(205,186,140); ROJO=(184,64,47); GRIS=(150,146,136)
FONTC=lambda s: ImageFont.truetype('C:/Windows/Fonts/GeorgiaPro-CondBold.ttf',s)
d=json.load(open('../fuentes/mapas/ne_50m_countries.geojson',encoding='utf-8'))
base=Image.new('RGB',(W*SS,H*SS),MAR); db=ImageDraw.Draw(base)
masks={n:Image.new('L',(W*SS,H*SS),0) for n in ('Belarus','Ukraine')}
bb=box(LON0-3,LAT0-3,LON1+3,LAT1+3); outl=[]
for f in d['features']:
    g=shape(f['geometry']); name=f['properties']['ADMIN']
    if not g.intersects(bb): continue
    gg=g.intersection(bb); geoms=list(gg.geoms) if hasattr(gg,'geoms') else [gg]
    for p in geoms:
        if p.is_empty or p.geom_type!='Polygon': continue
        pts=[proj(*c) for c in p.exterior.coords]; db.polygon(pts,fill=TIERRA)
        for ring in p.interiors: db.polygon([proj(*c) for c in ring.coords],fill=MAR)
        outl.append(pts)
        if name in masks: ImageDraw.Draw(masks[name]).polygon(pts,fill=255)
for pts in outl: db.line(pts+[pts[0]],fill=TINTA,width=3)
base=base.resize((W,H),Image.LANCZOS); db=ImageDraw.Draw(base)
masks={k:v.resize((W,H),Image.LANCZOS) for k,v in masks.items()}
bel,ukr=masks['Belarus'],masks['Ukraine']
PAISES={'UKRAINE':(32.3,49.3,30),'BELARUS':(26.3,53.0,26),'RUSSIA':(39.3,54.3,30),'POLAND':(22.9,51.3,16),'LITHUANIA':(24.2,55.3,14),
        'LATVIA':(26.6,56.25,12),'MOLDOVA':(28.3,47.35,13),'ROMANIA':(25.0,46.95,14),'SEA OF AZOV':(37.7,46.62,12)}
for nm,(lo,la,sz) in PAISES.items():
    x,y=pj(lo,la); db.text((x,y),nm,fill=(90,84,72),font=FONTC(sz),anchor='mm')
db.rectangle([0,0,W-1,H-1],outline=TINTA,width=4); base.save('assets/mapa03_base.png')
def capa(mask,color,alpha,fn):
    im=Image.new('RGBA',(W,H),color+(0,)); im.putalpha(mask.point(lambda v:int(v*alpha))); im.save('assets/'+fn)
# Bielorrusia: ocre de papel (nunca celeste), recortada al pais real
capa(bel,OCRE,0.55,'mapa03_belarus.png')
# Donbas (oblasts de Donetsk + Luhansk, aproximado a mano y recortado a Ucrania real)
DONBAS=[(36.7,49.05),(37.0,49.2),(37.4,49.2),(37.8,49.5),(38.1,49.95),(38.6,50.1),(39.0,50.05),(39.4,49.75),(40.0,49.6),(40.2,49.25),
        (39.95,48.85),(40.1,48.5),(39.8,48.1),(39.4,47.85),(38.9,47.7),(38.5,47.5),(38.3,47.25),(38.0,47.0),(37.5,46.95),(37.0,46.8),
        (36.6,46.8),(36.55,47.3),(36.6,47.7),(36.5,48.0),(36.55,48.35),(36.4,48.6),(36.6,48.85)]
dm=Image.new('L',(W,H),0); ImageDraw.Draw(dm).polygon([pj(*p) for p in DONBAS],fill=255)
capa(ImageChops.multiply(dm,ukr).filter(ImageFilter.GaussianBlur(1.0)),ROJO,0.45,'mapa03_donbas.png')
# sitios REALES (lon,lat)
P={'Kyiv':(30.52,50.45),'Chernihiv':(31.29,51.49),'Sumy':(34.80,50.91),'Kharkiv':(36.23,49.99),'Gomel':(30.98,52.43),'Minsk':(27.56,53.90),
   'Bryansk':(34.37,53.24),'Oryol':(36.08,52.97),'Tsimbulova':(36.0,52.9),'Dobropillia':(37.08,48.47),'Donetsk':(37.80,48.00),
   'Kramatorsk':(37.55,48.72),'Moscow':(37.62,55.76),'Kursk':(36.19,51.73),'Belgorod':(36.58,50.60),'Mozyr':(29.27,52.05),
   'Chernobyl':(30.22,51.39),'Zhytomyr':(28.66,50.25),'Poltava':(34.55,49.59),'Luhansk':(39.31,48.57),'Pokrovsk':(37.18,48.28),
   'Gomel axis':(30.95,51.85),'Bakhmut':(38.00,48.59),
   'West edge':(LON0+0.15,54.71),      # Kaliningrado (20.51,54.71) queda fuera: borde izquierdo a su latitud
   'Donbas':(38.0,48.4),'North front':(33.0,51.9)}
KALININGRAD=(20.51,54.71)
pts={k:list(pj(*v)) for k,v in P.items()}; json.dump(pts,open('assets/mapa03_pts.json','w'),indent=1)
# ejes de ataque: tinta punteada + punta de flecha
ej=Image.new('RGBA',(W,H),(0,0,0,0)); de=ImageDraw.Draw(ej)
def dashed(a,b,dash=12,gap=9,w=4,col=TINTA+(255,)):
    L=math.hypot(b[0]-a[0],b[1]-a[1]); ux,uy=(b[0]-a[0])/L,(b[1]-a[1])/L; s=0
    while s<L:
        e=min(s+dash,L); de.line([(a[0]+ux*s,a[1]+uy*s),(a[0]+ux*e,a[1]+uy*e)],fill=col,width=w); s+=dash+gap
def arrow(a,b,size=16,w=4,col=TINTA+(255,)):
    ang=math.atan2(b[1]-a[1],b[0]-a[0])
    for k in (-1,1):
        t=ang+math.pi+k*0.45; de.line([b,(b[0]+math.cos(t)*size,b[1]+math.sin(t)*size)],fill=col,width=w)
def eje(names,short=False):
    q=[tuple(pts[n]) for n in names]
    for a,b in zip(q,q[1:]): dashed(a,b,dash=(9 if short else 12),gap=(7 if short else 9))
    arrow(q[-2],q[-1])
eje(['Gomel','Chernihiv','Kyiv']); eje(['Bryansk','Sumy']); eje(['Kursk','Sumy'],True); eje(['Belgorod','Kharkiv'],True)
ej.save('assets/mapa03_ejes.png')
# franja de la muerte: +-40 km a cada lado de la linea de frente del este, hatch gris, recortada a Ucrania
FRENTE=[(37.6,49.95),(37.6,49.7),(38.1,48.9),(38.00,48.59),(37.18,48.28),(37.25,47.78),(36.26,47.66),(35.8,47.57),(34.5,47.2),(33.5,46.9),(32.6,46.65)]
fl=[pj(*p) for p in FRENTE]
km_px=(pj(37.5,48.0)[0]-pj(36.5,48.0)[0])/(111.32*math.cos(math.radians(48.0)))   # px por km a lat 48
half=int(round(40*km_px))
fm=Image.new('L',(W,H),0); df=ImageDraw.Draw(fm)
df.line(fl,fill=255,width=2*half,joint='curve')
for p in fl: df.ellipse([p[0]-half,p[1]-half,p[0]+half,p[1]+half],fill=255)
fm=fm.filter(ImageFilter.GaussianBlur(1.5))
hatch=Image.new('L',(W,H),70); dh=ImageDraw.Draw(hatch)
for i in range(-H,W+H,9): dh.line([(i,0),(i+H,H)],fill=255,width=2)
capa(ImageChops.multiply(ImageChops.multiply(fm,ukr),hatch),GRIS,0.85,'mapa03_muerte.png')
# capa de ciudades: punto + etiqueta con halo
ci=Image.new('RGBA',(W,H),(0,0,0,0)); dc=ImageDraw.Draw(ci)
LAB={'Kyiv':('b',24),'Chernihiv':('r',18),'Sumy':('r',18),'Kharkiv':('r',20),'Gomel':('r',18),'Minsk':('t',22),'Bryansk':('t',18),'Oryol':('r',18),
     'Tsimbulova':('b',12),'Dobropillia':('l',14),'Donetsk':('r',18),'Kramatorsk':('t',14),'Moscow':('r',22),'Kursk':('r',18),'Belgorod':('r',18),
     'Mozyr':('l',16),'Chernobyl':('l',16),'Zhytomyr':('b',16),'Poltava':('b',16),'Luhansk':('r',18),'Pokrovsk':('b',14),'Gomel axis':('l',13),'Bakhmut':('r',14)}
for nm,(side,sz) in LAB.items():
    x,y=pts[nm]; r=8 if nm=='Kyiv' else (6 if nm in ('Moscow','Minsk','Kharkiv') else (3 if nm in ('Tsimbulova','Gomel axis') else 5))
    dc.ellipse([x-r-2,y-r-2,x+r+2,y+r+2],fill=(245,240,228,255)); dc.ellipse([x-r,y-r,x+r,y+r],fill=(ROJO if nm in ('Kyiv','Moscow') else TINTA)+(255,))
    f=FONTC(sz); txt=nm.upper() if nm in ('Kyiv','Moscow') else nm
    anchor={'r':'lm','l':'rm','t':'mb','b':'mt'}[side]; off={'r':(r+6,0),'l':(-r-6,0),'t':(0,-r-4),'b':(0,r+4)}[side]
    for dx in (-2,-1,0,1,2):
        for dy in (-2,-1,0,1,2): dc.text((x+off[0]+dx,y+off[1]+dy),txt,fill=(245,240,228,255),font=f,anchor=anchor)
    dc.text((x+off[0],y+off[1]),txt,fill=TINTA+(255,),font=f,anchor=anchor)
# marca de borde para Kaliningrado (fuera de la hoja, a la izquierda)
x,y=pts['West edge']; dc.polygon([(x-2,y),(x+14,y-9),(x+14,y+9)],fill=TINTA+(255,))
for dx in (-2,-1,0,1,2):
    for dy in (-2,-1,0,1,2): dc.text((x+20+dx,y+dy),'Kaliningrad',fill=(245,240,228,255),font=FONTC(14),anchor='lm')
dc.text((x+20,y),'Kaliningrad',fill=TINTA+(255,),font=FONTC(14),anchor='lm')
ci.save('assets/mapa03_ciudades.png')
fuera=[k for k,v in P.items() if not (LON0<=v[0]<=LON1 and LAT0<=v[1]<=LAT1)]
print('mapa03 ok',W,H,'sitios',len(P),'fuera',fuera,'Kaliningrad real',KALININGRAD,'franja px/lado',half)
