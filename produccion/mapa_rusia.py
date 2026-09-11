# -*- coding: utf-8 -*-
# Hoja de mapa de Rusia (Natural Earth 50m) en capas separadas para animar. v2 (2026-09-07, feedback de Agustin:
# "ubica los sitios reales"): ciudades/aeropuertos con coordenadas reales y ETIQUETA, nombres de paises, Yakutia con
# forma organica, capas de escarcha suaves enmascaradas a Rusia, husos mas finos, y Alaska occidental en la hoja.
#  mapa_base.png (mar+tierra+contornos+nombres de paises), mapa_rusia.png (relleno Rusia), mapa_husos.png (11 meridianos),
#  mapa_ciudades.png (puntos+etiquetas), mapa_yakutia.png, mapa_frost_norte.png, mapa_frost_este.png, mapa_pts.json
import json, math
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
from shapely.geometry import shape, box
W,H=1500,900; SS=2
LON0,LON1,LAT0,LAT1=18,200,38,78          # Eurasia norte + Alaska occidental; lon>180 = Chukotka/Alaska
def proj(lon,lat):
    if lon<0: lon+=360
    x=(lon-LON0)/(LON1-LON0)*W*SS
    def m(l): return math.log(math.tan(math.pi/4+math.radians(l)/2))
    y=(m(LAT1)-m(lat))/(m(LAT1)-m(LAT0))*H*SS
    return (x,y)
def pj(lon,lat): x,y=proj(lon,lat); return (x/SS,y/SS)
TINTA=(34,32,28); MAR=(206,196,172); TIERRA=(228,216,190); RUSIA=(190,196,170); ROJO=(184,64,47); HIELO=(200,215,225)
FONTC=lambda s: ImageFont.truetype('C:/Windows/Fonts/GeorgiaPro-CondBold.ttf',s)
FONT=lambda s: ImageFont.truetype('C:/Windows/Fonts/GeorgiaPro-Bold.ttf',s)
d=json.load(open('../fuentes/mapas/ne_50m_countries.geojson',encoding='utf-8'))
base=Image.new('RGB',(W*SS,H*SS),MAR); db=ImageDraw.Draw(base)
rus=Image.new('L',(W*SS,H*SS),0); dr=ImageDraw.Draw(rus)
bb=box(LON0-5,LAT0-5,LON1+5,LAT1+5); bb2=box(-180,LAT0-5,-160,LAT1+5)
outl=[]
for f in d['features']:
    g=shape(f['geometry']); name=f['properties']['ADMIN']
    parts=[]
    if g.intersects(bb): parts.append(g.intersection(bb))
    if g.intersects(bb2): parts.append(g.intersection(bb2))
    for gg in parts:
        geoms=list(gg.geoms) if hasattr(gg,'geoms') else [gg]
        for p in geoms:
            if p.is_empty or p.geom_type!='Polygon': continue
            pts=[proj(*c) for c in p.exterior.coords]
            db.polygon(pts,fill=TIERRA)
            for ring in p.interiors: db.polygon([proj(*c) for c in ring.coords],fill=MAR)
            outl.append(pts)
            if name=='Russia': dr.polygon(pts,fill=255)
for pts in outl: db.line(pts+[pts[0]],fill=TINTA,width=3)
base=base.resize((W,H),Image.LANCZOS); rus=rus.resize((W,H),Image.LANCZOS)
db=ImageDraw.Draw(base)
# nombres de paises/regiones (tinta suave, condensada)
PAISES={'RUSSIA':(96,66,44),'KAZAKHSTAN':(66,47.5,22),'MONGOLIA':(103,46.2,20),'CHINA':(112,41,22),'UKRAINE':(31.5,48.6,17),
        'FINLAND':(26.5,63.5,16),'TURKEY':(33.5,39.3,16),'ALASKA':(196.5,66.5,17),'BELARUS':(27.8,52.6,13),'IRAN':(53,38.9,15),
        'JAPAN':(141.5,39.4,15),'SIBERIA':(90,58.5,22),'YAKUTIA':(127,65.5,17),'CHUKOTKA':(172,67.5,13),'KAMCHATKA':(159,57,13),'ARCTIC OCEAN':(110,76.5,18)}
for nm,(lo,la,sz) in PAISES.items():
    x,y=pj(lo,la); f=FONTC(sz); col=(90,84,72)
    db.text((x,y),nm,fill=col,font=f,anchor='mm')
db.rectangle([0,0,W-1,H-1],outline=TINTA,width=4)
base.save('assets/mapa_base.png')
rl=Image.new('RGBA',(W,H),RUSIA+(0,)); rl.putalpha(rus.point(lambda v:int(v*0.85))); rl.save('assets/mapa_rusia.png')
# husos: meridianos cada 15 grados desde 30E a 180 (11 lineas), finos y punteados
hz=Image.new('RGBA',(W,H),(0,0,0,0)); dh=ImageDraw.Draw(hz)
for lon in range(30,181,15):
    a=pj(lon,LAT0); b=pj(lon,LAT1)
    n=int(abs(b[1]-a[1])/14)
    for j in range(0,n,2):
        u0,u1=j/n,(j+1)/n; dh.line([(a[0],a[1]+(b[1]-a[1])*u0),(a[0],a[1]+(b[1]-a[1])*u1)],fill=TINTA+(95,),width=2)
hz.save('assets/mapa_husos.png')
# puntos de interes REALES (lon,lat). 'Urals' se mantiene como alias de Yekaterinburg.
P={'Moscow':(37.6,55.75),'St Petersburg':(30.3,59.9),'Kazan':(49.1,55.8),'Yekaterinburg':(60.6,56.8),'Samara':(50.2,53.2),
   'Sochi':(39.7,43.6),'Rostov':(39.7,47.2),'Murmansk':(33.1,69.0),'Smolensk':(32.0,54.8),'Omsk':(73.4,55.0),
   'Novosibirsk':(82.9,55.0),'Krasnoyarsk':(92.9,56.0),'Norilsk':(88.2,69.3),'Irkutsk':(104.3,52.3),'Yakutsk':(129.7,62.0),
   'Mirny':(113.9,62.5),'Tiksi':(128.9,71.6),'Khabarovsk':(135.1,48.5),'Vladivostok':(131.9,43.1),'Sakhalin':(142.7,46.95),
   'Magadan':(150.8,59.6),'Petropavlovsk':(158.6,53.0),'Anadyr':(177.5,64.7),'Nome':(194.6,64.5),
   'Minsk':(27.6,53.9),'Kyiv':(30.5,50.45),'Krakow':(19.9,50.06),'Ankara':(32.9,39.9),'Istanbul':(28.98,41.0),
   'Astana':(71.4,51.2),'Yerevan':(44.5,40.2),'Beijing':(116.4,39.9),'Ulaanbaatar':(106.9,47.9),'Helsinki':(24.9,60.2),'Tbilisi':(44.8,41.7),'Surgut':(73.4,61.25)}
P['Urals']=P['Yekaterinburg']
pts={k:list(pj(*v)) for k,v in P.items()}
json.dump(pts,open('assets/mapa_pts.json','w'),indent=1)
# capa de ciudades: punto + etiqueta con halo
ci=Image.new('RGBA',(W,H),(0,0,0,0)); dc=ImageDraw.Draw(ci)
LAB={'Moscow':('b',0),'St Petersburg':('r',-1),'Kazan':('b',0),'Yekaterinburg':('b',0),'Novosibirsk':('b',0),'Krasnoyarsk':('t',0),'Irkutsk':('b',0),
     'Yakutsk':('r',0),'Khabarovsk':('r',0),'Vladivostok':('b',0),'Magadan':('t',0),'Norilsk':('r',0),'Murmansk':('r',0),'Sochi':('b',0),'Omsk':('b',0),
     'Mirny':('l',0),'Anadyr':('t',0),'Petropavlovsk':('r',0),'Minsk':('l',0),'Kyiv':('l',0),'Astana':('b',0),'Ankara':('t',0),'Beijing':('t',0),
     'Ulaanbaatar':('b',0),'Helsinki':('r',0),'Nome':('t',0),'Smolensk':('l',0),'Samara':('b',0),'Krakow':('l',0),'Yerevan':('t',0),'Tiksi':('t',0),'Sakhalin':('r',0),'Surgut':('r',0)}
for nm,(side,_) in LAB.items():
    x,y=pts[nm]; r=5 if nm!='Moscow' else 7
    dc.ellipse([x-r-2,y-r-2,x+r+2,y+r+2],fill=(245,240,228,255)); dc.ellipse([x-r,y-r,x+r,y+r],fill=(ROJO if nm=='Moscow' else TINTA)+(255,))
    f=FONTC(22 if nm=='Moscow' else 18); txt=nm.upper() if nm=='Moscow' else nm
    anchor={'r':'lm','l':'rm','t':'mb','b':'mt'}[side]; off={'r':(r+6,0),'l':(-r-6,0),'t':(0,-r-4),'b':(0,r+4)}[side]
    for dx in (-2,-1,0,1,2):
        for dy in (-2,-1,0,1,2): dc.text((x+off[0]+dx,y+off[1]+dy),txt,fill=(245,240,228,255),font=f,anchor=anchor)
    dc.text((x+off[0],y+off[1]),txt,fill=TINTA+(255,),font=f,anchor=anchor)
ci.save('assets/mapa_ciudades.png')
# Yakutia (Sakha) aproximada con poligono organico lon/lat, recortada a Rusia
yk=Image.new('L',(W,H),0); dy=ImageDraw.Draw(yk)
poly=[(105,72.5),(112,73.6),(120,73.3),(128,73.2),(136,72.4),(143,72.0),(150,71.4),(157,70.5),(162,68.5),(163,65.5),(160,63),(154,61.5),(150,60.5),(145,59.5),(140,57.5),(135,56.2),(129,55.8),(122,56.3),(115,57.2),(110,58.5),(107,61),(105,65),(104,69)]
dy.polygon([pj(lo,la) for lo,la in poly],fill=255)
ykm=ImageChops.multiply(yk,rus).filter(ImageFilter.GaussianBlur(1.2))
yl=Image.new('RGBA',(W,H),HIELO+(0,)); yl.putalpha(ykm.point(lambda v:int(v*0.5))); yl.save('assets/mapa_yakutia.png')
# escarcha norte (alpha decrece de norte a ~lat 58) y este (crece de lon 95 a 180), ambas solo sobre Rusia
import numpy as np
ys=np.arange(H); y58=pj(100,58)[1]; y75=pj(100,75)[1]
gn=np.clip((y58-ys)/(y58-y75),0,1)[:,None]*np.ones((1,W))
xs=np.arange(W); x95=pj(95,60)[0]; x180=pj(180,60)[0]
ge=np.clip((xs-x95)/(x180-x95),0,1)[None,:]*np.ones((H,1))
rm=np.asarray(rus).astype(np.float32)/255
for nm,g in (('norte',gn),('este',ge)):
    a=(g*rm*150).astype(np.uint8); im=Image.new('RGBA',(W,H),HIELO+(0,)); im.putalpha(Image.fromarray(a).filter(ImageFilter.GaussianBlur(3))); im.save(f'assets/mapa_frost_{nm}.png')
print('mapa v2 ok',pts['Moscow'],pts['Vladivostok'],pts['Nome'])
