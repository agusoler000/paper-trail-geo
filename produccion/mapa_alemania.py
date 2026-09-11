# -*- coding: utf-8 -*-
# Hoja de mapa del ep. 2 (AfD): Europa central centrada en Alemania (Natural Earth 50m, Mercator).
# Mismo metodo que mapa_rusia.py v2: sitios REALES con etiqueta, nombres de paises, capas separadas para animar.
#  mapa02_base.png      mar + tierra + contornos + nombres de paises
#  mapa02_alemania.png  relleno de Alemania
#  mapa02_rda.png       relleno de la ex RDA (poligono organico lon/lat, recortado a Alemania) + etiqueta
#  mapa02_sa.png        relleno de Sajonia-Anhalt (poligono organico) + etiqueta
#  mapa02_este_azul.png la ex RDA tenida de azul (para "the East fills blue")
#  mapa02_ciudades.png  puntos + etiquetas
#  mapa02_pts.json      pixeles de cada sitio (para anclar props con G('Ciudad'))
# Lo que no entra en la hoja (Moscu, Roma, Madrid, Lisboa, Atenas, los nordicos, Sri Lanka) va a la PARED (WALL).
import json, math
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
from shapely.geometry import shape, box
LON0,LON1,LAT0,LAT1=-6,32,45.2,56
def m(l): return math.log(math.tan(math.pi/4+math.radians(l)/2))
W=1500; SS=2
H=int(round(W*(m(LAT1)-m(LAT0))/math.radians(LON1-LON0)))   # sin distorsion: 880
def proj(lon,lat):
    x=(lon-LON0)/(LON1-LON0)*W*SS; y=(m(LAT1)-m(lat))/(m(LAT1)-m(LAT0))*H*SS; return (x,y)
def pj(lon,lat): x,y=proj(lon,lat); return (x/SS,y/SS)
TINTA=(34,32,28); MAR=(206,196,172); TIERRA=(228,216,190); ALEMANIA=(190,196,170); ROJO=(184,64,47); AZUL=(43,76,111); GRIS=(150,146,136)
FONTC=lambda s: ImageFont.truetype('C:/Windows/Fonts/GeorgiaPro-CondBold.ttf',s)
d=json.load(open('../fuentes/mapas/ne_50m_countries.geojson',encoding='utf-8'))
base=Image.new('RGB',(W*SS,H*SS),MAR); db=ImageDraw.Draw(base)
ger=Image.new('L',(W*SS,H*SS),0); dg=ImageDraw.Draw(ger)
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
        if name=='Germany': dg.polygon(pts,fill=255)
for pts in outl: db.line(pts+[pts[0]],fill=TINTA,width=3)
base=base.resize((W,H),Image.LANCZOS); ger=ger.resize((W,H),Image.LANCZOS); db=ImageDraw.Draw(base)
PAISES={'GERMANY':(8.0,51.55,26),'FRANCE':(2.6,47.3,22),'POLAND':(19.6,52.3,22),'CZECHIA':(15.4,49.75,16),'AUSTRIA':(15.2,47.3,16),
        'SWITZERLAND':(8.1,46.65,13),'NETHERLANDS':(5.4,52.75,13),'BELGIUM':(4.55,50.45,13),'DENMARK':(9.3,55.35,14),'BRITAIN':(-1.8,52.6,18),
        'UKRAINE':(28.0,49.0,20),'BELARUS':(27.6,53.4,16),'HUNGARY':(19.4,46.9,15),'SLOVAKIA':(19.6,48.75,13),'ITALY':(10.6,45.55,15),
        'LITHUANIA':(24.2,55.55,13),'BALTIC SEA':(17.3,55.2,15),'NORTH SEA':(3.3,54.9,15),'ROMANIA':(24.5,46.6,15),'SLOVENIA':(14.8,46.1,11),'CROATIA':(16.5,45.55,11)}
for nm,(lo,la,sz) in PAISES.items():
    x,y=pj(lo,la); db.text((x,y),nm,fill=(90,84,72),font=FONTC(sz),anchor='mm')
db.rectangle([0,0,W-1,H-1],outline=TINTA,width=4); base.save('assets/mapa02_base.png')
al=Image.new('RGBA',(W,H),ALEMANIA+(0,)); al.putalpha(ger.point(lambda v:int(v*0.85))); al.save('assets/mapa02_alemania.png')
# ex RDA (frontera interalemana + costa, aproximada a mano y recortada a Alemania real)
RDA=[(10.9,53.95),(10.75,53.75),(10.8,53.5),(10.6,53.37),(10.85,53.25),(11.2,53.1),(11.55,53.03),(11.4,52.95),(11.0,52.85),(10.95,52.6),(10.95,52.45),(11.05,52.2),(10.9,52.05),(10.7,51.9),(10.6,51.65),(10.4,51.55),(10.2,51.48),(10.1,51.3),(9.95,51.2),(10.15,51.1),(10.05,50.95),(10.1,50.8),(9.95,50.65),(10.05,50.5),(10.3,50.42),(10.6,50.4),(10.95,50.4),(11.2,50.3),(11.45,50.4),(11.7,50.42),(11.95,50.42),(12.1,50.32),(12.3,50.2),(12.5,50.4),(12.8,50.45),(13.0,50.5),(13.4,50.62),(13.8,50.73),(14.3,50.9),(14.6,50.85),(14.85,50.87),(14.95,51.2),(14.75,51.6),(14.65,52.0),(14.55,52.3),(14.65,52.5),(14.35,52.8),(14.15,52.85),(14.2,53.1),(14.4,53.3),(14.35,53.6),(14.25,53.85),(14.2,54.0),(13.8,54.15),(13.5,54.2),(13.4,54.6),(13.1,54.65),(12.7,54.45),(12.3,54.35),(11.9,54.15),(11.5,54.1),(11.2,54.0)]
rd=Image.new('L',(W,H),0); ImageDraw.Draw(rd).polygon([pj(*p) for p in RDA],fill=255); rdm=ImageChops.multiply(rd,ger).filter(ImageFilter.GaussianBlur(1.0))
def capa(mask,color,alpha,label=None,at=None,size=18,fn=None):
    im=Image.new('RGBA',(W,H),color+(0,)); im.putalpha(mask.point(lambda v:int(v*alpha)))
    if label:
        dd=ImageDraw.Draw(im); x,y=pj(*at)
        for dx in (-1,0,1):
            for dy in (-1,0,1): dd.text((x+dx,y+dy),label,fill=(245,240,228,255),font=FONTC(size),anchor='mm')
        dd.text((x,y),label,fill=TINTA+(255,),font=FONTC(size),anchor='mm')
    im.save('assets/'+fn)
capa(rdm,GRIS,0.55,'FORMER EAST GERMANY',(13.1,53.75),16,'mapa02_rda.png')
capa(rdm,AZUL,0.6,None,None,0,'mapa02_este_azul.png')
# Sajonia-Anhalt (poligono organico)
SA=[(10.95,52.85),(11.3,53.0),(11.6,53.03),(12.0,52.9),(12.25,52.55),(12.35,52.35),(12.55,52.15),(12.9,52.05),(13.15,51.9),(13.0,51.7),(12.85,51.55),(12.4,51.4),(12.3,51.2),(12.2,50.95),(11.9,51.0),(11.75,51.05),(11.5,51.15),(11.3,51.25),(11.05,51.3),(10.6,51.55),(10.6,51.7),(10.7,51.9),(10.85,52.05),(10.9,52.25),(10.95,52.5),(10.85,52.7)]
sa=Image.new('L',(W,H),0); ImageDraw.Draw(sa).polygon([pj(*p) for p in SA],fill=255); sam=ImageChops.multiply(sa,ger)
capa(sam,ROJO,0.45,None,None,0,'mapa02_sa.png')
# contorno de Sajonia-Anhalt (linea de tinta) para que se "dibuje"
so=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(so).line([pj(*p) for p in SA]+[pj(*SA[0])],fill=TINTA+(255,),width=4); so.save('assets/mapa02_sa_borde.png')
# sitios REALES (lon,lat)
P={'Magdeburg':(11.63,52.13),'Halle':(11.97,51.48),'Berlin':(13.4,52.52),'Potsdam':(13.06,52.4),'Leipzig':(12.37,51.34),'Dresden':(13.74,51.05),
   'Erfurt':(11.03,50.98),'Hamburg':(10.0,53.55),'Munich':(11.58,48.14),'Cologne':(6.96,50.94),'Frankfurt':(8.68,50.11),'Hanover':(9.73,52.37),
   'Stuttgart':(9.18,48.78),'Wolfsburg':(10.79,52.42),'Rostock':(12.1,54.09),'Paris':(2.35,48.86),'London':(-0.13,51.51),'Brussels':(4.35,50.85),
   'Amsterdam':(4.9,52.37),'Vienna':(16.37,48.21),'Salzburg':(13.05,47.8),'Prague':(14.42,50.09),'Warsaw':(21.01,52.23),'Copenhagen':(12.57,55.68),
   'Kyiv':(30.52,50.45),'Minsk':(27.56,53.9),'Zurich':(8.54,47.37),'Budapest':(19.04,47.5),'Strasbourg':(7.75,48.58),'Luxembourg':(6.13,49.61),
   'East edge':(31.7,54.6),'South edge':(11.5,45.5),'West edge':(-5.6,48.0)}
pts={k:list(pj(*v)) for k,v in P.items()}; json.dump(pts,open('assets/mapa02_pts.json','w'),indent=1)
ci=Image.new('RGBA',(W,H),(0,0,0,0)); dc=ImageDraw.Draw(ci)
LAB={'Magdeburg':('r',24),'Halle':('r',18),'Berlin':('r',22),'Potsdam':('l',16),'Leipzig':('b',18),'Dresden':('r',18),'Erfurt':('b',18),'Hamburg':('r',18),
     'Munich':('b',18),'Cologne':('l',18),'Frankfurt':('l',18),'Hanover':('t',18),'Rostock':('t',16),'Paris':('b',20),'London':('t',20),'Brussels':('l',18),
     'Amsterdam':('t',16),'Vienna':('r',18),'Salzburg':('b',16),'Prague':('r',18),'Warsaw':('r',20),'Copenhagen':('r',16),'Kyiv':('b',20),'Minsk':('b',18),
     'Zurich':('b',16),'Budapest':('r',16),'Strasbourg':('b',14),'Stuttgart':('b',16)}
for nm,(side,sz) in LAB.items():
    x,y=pts[nm]; r=7 if nm=='Magdeburg' else (6 if nm in ('Berlin','Paris','London','Warsaw','Kyiv') else 5)
    dc.ellipse([x-r-2,y-r-2,x+r+2,y+r+2],fill=(245,240,228,255)); dc.ellipse([x-r,y-r,x+r,y+r],fill=(ROJO if nm=='Magdeburg' else TINTA)+(255,))
    f=FONTC(sz); txt=nm.upper() if nm=='Magdeburg' else nm
    anchor={'r':'lm','l':'rm','t':'mb','b':'mt'}[side]; off={'r':(r+6,0),'l':(-r-6,0),'t':(0,-r-4),'b':(0,r+4)}[side]
    for dx in (-2,-1,0,1,2):
        for dy in (-2,-1,0,1,2): dc.text((x+off[0]+dx,y+off[1]+dy),txt,fill=(245,240,228,255),font=f,anchor=anchor)
    dc.text((x+off[0],y+off[1]),txt,fill=TINTA+(255,),font=f,anchor=anchor)
ci.save('assets/mapa02_ciudades.png')
print('mapa02 ok',W,H,pts['Magdeburg'],pts['Berlin'],pts['Kyiv'])
