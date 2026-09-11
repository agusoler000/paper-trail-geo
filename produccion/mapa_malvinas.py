# -*- coding: utf-8 -*-
# Hoja de mapa del ep. 4 (Malvinas / Falkland Islands): Natural Earth 50m, Mercator sin distorsion.
# Hoja VERTICAL (es una hoja de papel apaisada en vertical sobre la mesa): del Rio de la Plata al Cabo de Hornos.
#  mapa04_base.png        mar + tierra + contornos + nombres de paises y oceano
#  mapa04_ciudades.png    puntos + etiquetas (todos los sitios del guion, REALES)
#  mapa04_islas.png       relleno ocre de las islas (nunca color de agua)
#  mapa04_plataforma.png  plataforma continental sudamericana (isobata ~200 m, aproximada): las islas estan encima
#  mapa04_zonaexcl.png    circulo de la zona de exclusion de 1982 (200 millas nauticas alrededor de las islas)
#  mapa04_pts.json        pixeles de cada sitio (para anclar props con G('Sitio'))
# Lo que NO entra en la hoja (Londres, Washington, Jerusalen, Chagos, Hong Kong) va a la PARED.
# Georgias del Sur y la Antartida entran como puntos de borde ('East edge', 'South edge').
import json, math
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
from shapely.geometry import shape, box

LON0, LON1, LAT0, LAT1 = -76, -52, -57, -33
def m(l): return math.log(math.tan(math.pi/4 + math.radians(l)/2))
W = 1500; SS = 2
H = int(round(W*(m(LAT1)-m(LAT0))/math.radians(LON1-LON0)))   # sin distorsion
def proj(lon, lat):
    x = (lon-LON0)/(LON1-LON0)*W*SS; y = (m(LAT1)-m(lat))/(m(LAT1)-m(LAT0))*H*SS; return (x, y)
def pj(lon, lat):
    x, y = proj(lon, lat); return (x/SS, y/SS)

TINTA=(34,32,28); MAR=(206,196,172); TIERRA=(228,216,190); OCRE=(205,186,140)
ROJO=(184,64,47); GRIS=(150,146,136); AZUL=(120,132,140)
FONTC = lambda s: ImageFont.truetype('C:/Windows/Fonts/GeorgiaPro-CondBold.ttf', s)
FONTR = lambda s: ImageFont.truetype('C:/Windows/Fonts/Georgia.ttf', s)

d = json.load(open('../fuentes/mapas/ne_50m_countries.geojson', encoding='utf-8'))
base = Image.new('RGB', (W*SS, H*SS), MAR); db = ImageDraw.Draw(base)
masks = {n: Image.new('L', (W*SS, H*SS), 0) for n in ('Argentina', 'Chile', 'Falkland Islands')}
bb = box(LON0-3, LAT0-3, LON1+3, LAT1+3); outl = []
for f in d['features']:
    g = shape(f['geometry']); name = f['properties']['ADMIN']
    if not g.intersects(bb): continue
    gg = g.intersection(bb); geoms = list(gg.geoms) if hasattr(gg, 'geoms') else [gg]
    for p in geoms:
        if p.is_empty or p.geom_type != 'Polygon': continue
        pts = [proj(*c) for c in p.exterior.coords]
        if len(pts) < 3: continue
        db.polygon(pts, fill=TIERRA)
        for ring in p.interiors: db.polygon([proj(*c) for c in ring.coords], fill=MAR)
        outl.append(pts)
        if name in masks: ImageDraw.Draw(masks[name]).polygon(pts, fill=255)
for pts in outl: db.line(pts+[pts[0]], fill=TINTA, width=3)
base = base.resize((W, H), Image.LANCZOS); db = ImageDraw.Draw(base)
masks = {k: v.resize((W, H), Image.LANCZOS) for k, v in masks.items()}
arg, chi, isl = masks['Argentina'], masks['Chile'], masks['Falkland Islands']

PAISES = {'ARGENTINA': (-65.5, -40.0, 34), 'CHILE': (-72.0, -46.5, 22), 'URUGUAY': (-56.0, -33.4, 14),
          'SOUTH ATLANTIC OCEAN': (-56.0, -44.0, 26), 'PACIFIC': (-74.8, -47.2, 16),
          'PATAGONIA': (-68.5, -46.5, 18), 'TIERRA DEL FUEGO': (-69.3, -54.15, 11),
          'DRAKE PASSAGE': (-64.0, -56.55, 12)}
for nm, (lo, la, sz) in PAISES.items():
    x, y = pj(lo, la); db.text((x, y), nm, fill=(90, 84, 72), font=FONTC(sz), anchor='mm')
db.rectangle([0, 0, W-1, H-1], outline=TINTA, width=4)
base.save('assets/mapa04_base.png')

def capa(mask, color, alpha, fn):
    im = Image.new('RGBA', (W, H), color+(0,)); im.putalpha(mask.point(lambda v: int(v*alpha))); im.save('assets/'+fn)

# las islas en ocre de papel, nunca en el color del mar (error del ep. 1 con Yakutia)
capa(isl.filter(ImageFilter.MaxFilter(3)), OCRE, 0.85, 'mapa04_islas.png')

# plataforma continental sudamericana, isobata de 200 m aproximada a mano: las islas caen ADENTRO
PLAT = [(-62.4, -38.9), (-59.0, -39.6), (-56.4, -41.6), (-55.2, -44.0), (-54.6, -46.6), (-54.9, -49.0),
        (-54.8, -50.6), (-55.6, -52.6), (-57.4, -53.7), (-60.6, -54.4), (-63.0, -55.2), (-65.4, -55.8),
        (-67.4, -56.2), (-69.4, -56.3), (-69.4, -55.4), (-67.0, -54.6), (-65.0, -53.6), (-64.0, -52.0),
        (-63.4, -50.0), (-63.4, -47.6), (-63.6, -45.2), (-63.0, -42.4), (-62.4, -40.4)]
pm = Image.new('L', (W, H), 0); ImageDraw.Draw(pm).polygon([pj(*p) for p in PLAT], fill=255)
pm = ImageChops.subtract(pm, arg.point(lambda v: 255 if v > 40 else 0))
pm = ImageChops.subtract(pm, chi.point(lambda v: 255 if v > 40 else 0))
capa(pm.filter(ImageFilter.GaussianBlur(1.2)), AZUL, 0.17, 'mapa04_plataforma.png')
# contorno punteado de la plataforma, en capa aparte (se enciende cuando la voz la nombra)
pl = Image.open('assets/mapa04_plataforma.png'); dpl = ImageDraw.Draw(pl)
rr = [pj(*q) for q in PLAT]+[pj(*PLAT[0])]
for i in range(len(rr)-1):
    a, b2 = rr[i], rr[i+1]; L = math.hypot(b2[0]-a[0], b2[1]-a[1]); t = 0
    while t < L:
        u = ((b2[0]-a[0])/L, (b2[1]-a[1])/L); e = min(t+9, L)
        dpl.line([(a[0]+u[0]*t, a[1]+u[1]*t), (a[0]+u[0]*e, a[1]+u[1]*e)], fill=AZUL+(190,), width=3); t += 16
pl.save('assets/mapa04_plataforma.png')

# zona de exclusion de 1982: 200 millas nauticas (370 km) alrededor de (-59.5,-51.7)
CX, CY = -59.5, -51.7
ze = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dz = ImageDraw.Draw(ze)
ring = []
for i in range(361):
    a = math.radians(i); dlat = 370.0/111.0*math.cos(a)
    dlon = 370.0/(111.0*math.cos(math.radians(CY)))*math.sin(a)
    ring.append(pj(CX+dlon, CY+dlat))
for i in range(0, 360, 14):
    dz.line([ring[i], ring[i+7]], fill=ROJO+(215,), width=4)
ze.save('assets/mapa04_zonaexcl.png')

# sitios REALES (lon, lat). Todo prop se coloca con G('Sitio'); nada a ojo.
P = {
    'Buenos Aires': (-58.38, -34.60), 'Montevideo': (-56.16, -34.90), 'Mar del Plata': (-57.54, -38.00),
    'Bahia Blanca': (-62.27, -38.72), 'Puerto Madryn': (-65.03, -42.77), 'Comodoro Rivadavia': (-67.48, -45.86),
    'Rio Gallegos': (-69.22, -51.62), 'Cabo Virgenes': (-68.35, -52.34), 'Rio Grande': (-67.70, -53.79),
    'Ushuaia': (-68.30, -54.80), 'Punta Arenas': (-70.92, -53.16), 'Isla de los Estados': (-64.30, -54.78),
    'Cape Horn': (-67.28, -55.98),
    # las islas
    'Stanley': (-57.85, -51.69), 'Port Louis': (-58.13, -51.55), 'Puerto Soledad': (-58.13, -51.55), 'Port Egmont': (-60.05, -51.35),
    'Mount Pleasant': (-58.45, -51.82), 'Falkland Sound': (-59.40, -51.60), 'San Carlos': (-59.55, -51.50),
    'Goose Green': (-58.97, -51.82), 'West Falkland': (-60.20, -51.75), 'East Falkland': (-58.60, -51.90),
    'Islands': (-59.10, -51.65),
    # el petroleo: Sea Lion, ~220 km al norte de las islas
    'Sea Lion': (-59.10, -49.65), 'North Basin': (-59.60, -50.30),
    # bordes: lo que no entra en la hoja pero tiene direccion real
    'East edge': (LON1-0.2, -54.30),    # Georgias del Sur (-36.5,-54.3)
    'South edge': (-59.00, LAT0+0.25),  # Peninsula Antartica
    'North edge': (-58.38, LAT1-0.25),  # hacia el norte / Londres a doce mil setecientos km
    # anclas de texto
    'Mid Atlantic': (-56.5, -47.5), 'Shelf': (-61.0, -47.0),
}
pts = {k: list(pj(*v)) for k, v in P.items()}
json.dump(pts, open('assets/mapa04_pts.json', 'w'), indent=1)

# capa de puntos + etiquetas
ci = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dc = ImageDraw.Draw(ci)
ETQ = {  # sitio: (texto, dx, dy, anchor, size)
    'Buenos Aires': ('BUENOS AIRES', 8, -2, 'lm', 17), 'Montevideo': ('Montevideo', 8, 6, 'lm', 12),
    'Mar del Plata': ('Mar del Plata', 8, 0, 'lm', 12), 'Bahia Blanca': ('Bahia Blanca', -8, 0, 'rm', 12),
    'Puerto Madryn': ('Puerto Madryn', -8, 0, 'rm', 12), 'Comodoro Rivadavia': ('Comodoro Rivadavia', -8, 0, 'rm', 12),
    'Rio Gallegos': ('Rio Gallegos', -8, 0, 'rm', 13), 'Rio Grande': ('Rio Grande', -8, -6, 'rm', 12),
    'Ushuaia': ('USHUAIA', -8, 6, 'rm', 16), 'Punta Arenas': ('Punta Arenas', -8, 0, 'rm', 12),
    'Isla de los Estados': ('Isla de los Estados', 6, 10, 'lm', 11), 'Cape Horn': ('Cape Horn', 6, 4, 'lm', 11),
    'Stanley': ('STANLEY / PUERTO ARGENTINO', 8, -4, 'lm', 14), 'Port Louis': ('Port Louis', 6, -12, 'lm', 12),
    'Port Egmont': ('Port Egmont', -6, -10, 'rm', 12), 'Mount Pleasant': ('Mount Pleasant', 10, 16, 'lm', 12),
    'San Carlos': ('San Carlos', -7, -9, 'rm', 11), 'Goose Green': ('Goose Green', -7, 9, 'rm', 11),
    'Sea Lion': ('SEA LION', 9, 0, 'lm', 15),
}
for k, (txt, dx, dy, anc, sz) in ETQ.items():
    x, y = pts[k]
    r = 5 if txt.isupper() else 3.5
    dc.ellipse([x-r, y-r, x+r, y+r], fill=TINTA+(255,))
    if k == 'Sea Lion':  # el pozo no es una ciudad: rombo
        dc.polygon([(x, y-8), (x+7, y), (x, y+8), (x-7, y)], fill=ROJO+(255,), outline=TINTA+(255,))
    dc.text((x+dx, y+dy), txt, fill=TINTA+(255,), font=FONTC(sz) if txt.isupper() else FONTR(sz), anchor=anc)
# nombre de las islas sobre el archipielago
x, y = pj(-59.10, -52.35)
dc.text((x, y), 'FALKLAND ISLANDS / ISLAS MALVINAS', fill=(70, 64, 54), font=FONTC(15), anchor='mm')
# flechas de borde: lo que existe y no entra en la hoja. La tipografia no tiene los caracteres de flecha: se dibujan.
BORDE = (110, 100, 84)
def flecha(x, y, ang, s_=8):
    a = math.radians(ang)
    dc.polygon([(x+math.cos(a)*s_, y+math.sin(a)*s_), (x+math.cos(a+2.5)*s_, y+math.sin(a+2.5)*s_),
                (x+math.cos(a-2.5)*s_, y+math.sin(a-2.5)*s_)], fill=BORDE+(255,))
for k, txt, anc, ang, dx, dy in (('East edge', 'SOUTH GEORGIA', 'rm', 0, -26, 0),
                                 ('South edge', 'ANTARCTICA', 'lm', 90, 16, 18),
                                 ('North edge', 'LONDON: 12,700 km', 'lm', -90, 16, 20)):
    x, y = pts[k]
    dc.text((x+dx, y+dy), txt, fill=BORDE+(255,), font=FONTC(13), anchor=anc)
    flecha(x+(dx+12 if anc == 'rm' else dx-8), y+dy, ang)
ci.save('assets/mapa04_ciudades.png')

print('mapa04  W=%d H=%d  sitios=%d' % (W, H, len(P)))
print('  base/islas/plataforma/zonaexcl/ciudades + mapa04_pts.json en assets/')
