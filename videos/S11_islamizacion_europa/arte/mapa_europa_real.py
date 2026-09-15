# -*- coding: utf-8 -*-
# Hoja de mapa de EUROPA (Natural Earth 50m) para la miniatura del S11.
# Mismo look que produccion/mapa_mundo.py: papel, tinta, mar calido. Salida: assets/mapa_europa_real.png
import json, os, math
from PIL import Image, ImageDraw
from shapely.geometry import shape, box

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..', '..'))
GEO = os.path.join(RAIZ, 'fuentes', 'mapas', 'ne_50m_countries.geojson')
OUT = os.path.join(AQUI, 'assets', 'mapa_europa_real.png')
TINTA, MAR, TIERRA = (52, 46, 40), (182, 172, 150), (242, 233, 210)
W, H, SS = 1500, 1100, 2
LON0, LON1, LAT0, LAT1 = -12, 42, 34, 72


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
        if len(pts) > 2: dr.polygon(pts, fill=TIERRA, outline=TINTA, width=3)
img = img.resize((W, H), Image.LANCZOS)
import numpy as np
a = np.asarray(img).astype(np.float32); rng = np.random.default_rng(3)
a = np.clip(a + rng.normal(0, 4, a.shape), 0, 255).astype('uint8'); img = Image.fromarray(a)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT); print('ok', OUT, img.size)
