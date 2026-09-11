# -*- coding: utf-8 -*-
# Hoja de mapa del MUNDO (Natural Earth 50m) para la intro/outro genericas del canal.
# Mismo look que pruebas/look/mapa.py (papel, tinta, mar apenas mas oscuro). Salida: assets/mapa_mundo.png
import json, os, math
from PIL import Image, ImageDraw, ImageFilter
from shapely.geometry import shape, box
from shapely.ops import unary_union

AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.dirname(AQUI)
GEO = os.path.join(RAIZ, 'fuentes', 'mapas', 'ne_50m_countries.geojson')
OUT = os.path.join(AQUI, 'assets', 'mapa_mundo.png')
TINTA, MAR, TIERRA = (34, 32, 28), (206, 196, 172), (228, 216, 190)
W, H, SS = 1500, 900, 2
LON0, LON1, LAT0, LAT1 = -170, 180, -56, 78

def m(l): return math.log(math.tan(math.pi / 4 + math.radians(l) / 2))
def proj(lon, lat):
    return ((lon - LON0) / (LON1 - LON0) * W * SS, (m(LAT1) - m(lat)) / (m(LAT1) - m(LAT0)) * H * SS)

d = json.load(open(GEO, encoding='utf-8'))
bb = box(LON0, LAT0, LON1, LAT1)
img = Image.new('RGB', (W * SS, H * SS), MAR); dr = ImageDraw.Draw(img)
def rings(g):
    if g.geom_type == 'Polygon': yield g.exterior.coords
    elif g.geom_type == 'MultiPolygon':
        for p in g.geoms: yield p.exterior.coords
for f in d['features']:
    g = shape(f['geometry']).intersection(bb)
    if g.is_empty: continue
    for r in rings(g):
        pts = [proj(x, y) for x, y in r]
        if len(pts) > 2: dr.polygon(pts, fill=TIERRA, outline=TINTA, width=2)
# graticula suave
for lon in range(-150, 181, 30):
    x = proj(lon, 0)[0]; dr.line([(x, 0), (x, H * SS)], fill=(190, 180, 158), width=2)
for lat in range(-45, 76, 15):
    y = proj(0, lat)[1]; dr.line([(0, y), (W * SS, y)], fill=(190, 180, 158), width=2)
img = img.resize((W, H), Image.LANCZOS)
# grano de papel
import numpy as np
a = np.asarray(img).astype(np.float32); rng = np.random.default_rng(3)
a = np.clip(a + rng.normal(0, 4, a.shape), 0, 255).astype('uint8'); img = Image.fromarray(a)
os.makedirs(os.path.dirname(OUT), exist_ok=True); img.save(OUT); print('ok', OUT, img.size)
