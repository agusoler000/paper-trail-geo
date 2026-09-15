# -*- coding: utf-8 -*-
"""Hoja de mapa de la serie S10. Natural Earth 50m, Mercator. 0 creditos (render local).

    cd videos/S10_suecia/arte && python mapa.py
    -> mapa10_base.png  mapa10_ciudades.png  mapa10_pts.json

**Una sola hoja, y por que.** Suecia mide 14 grados de latitud: si la hoja entrara entera
(hasta Kiruna, 67,9 N) Malmo y Estocolmo quedarian en el quinto inferior y Sodertalje seria
indistinguible de Estocolmo. Todo lo que cuenta esta serie pasa **entre Malmo y Uppsala**, asi
que la hoja llega hasta Sundsvall: la silueta sigue leyendose como Suecia —con Dinamarca al sur
y Noruega al oeste— y las ciudades quedan a tamano util.

  LON 8,0 a 22,0 · LAT 54,8 a 63,2 · W = 3200  ->  **229 px por grado** de longitud.

Con eso **Estocolmo y Sodertalje** (0,443 grados de separacion) quedan a ~101 px en la hoja, o
sea ~240 px en el plano MAP (zoom 1,66x sobre un recorte). Se leen como dos sitios distintos,
que es justo lo que necesita la pieza 1: el asesinato no fue en la capital.

**Regla 24 de Agustin: los puntos son 100 % precisos.** Todo sale de `pj(lon, lat)` con
coordenadas reales, nunca de un pixel a ojo. Grados decimales:

  Estocolmo      59,3293 N   18,0686 E    la capital
  Sodertalje     59,1955 N   17,6252 E    donde mataron a Momika, 29-ene-2025 (G3)
  Uppsala        59,8586 N   17,6389 E    una de las dos escuelas cerradas en 2022 (G2)
  Goteborg       57,7089 N   11,9746 E    2a ciudad; una de las tres del estudio del 14 % (G8)
  Malmo          55,6050 N   13,0038 E    3a ciudad; idem (G8)
  Orebro         59,2741 N   15,2066 E
  Copenhague     55,6761 N   12,5683 E    contexto: el Oresund, al otro lado del puente
  Oslo           59,9139 N   10,7522 E    contexto

El archivo deja tambien `mapa10_pts.json` con los puntos ya proyectados a pixeles de la hoja,
para que la coreografia NUNCA coloque una marca a ojo.

**Limitacion medida y asumida: Estocolmo.** Su coordenada exacta cae **7 px (1,7 km) dentro del
agua** en esta hoja, porque Natural Earth 50m no resuelve el archipielago de Estocolmo. El punto
no esta mal — la costa lo esta. Se deja asi a proposito: mover el punto para que caiga sobre
tierra seria falsear la coordenada, que es exactamente lo que la regla 24 prohibe. Visualmente
lee bien, porque Estocolmo ES una ciudad sobre el agua. Si alguna vez hace falta mas precision,
la salida es bajar Natural Earth 10m a `fuentes/mapas/`, no correr el punto.
"""
import json, math, os
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(AQUI, 'assets'); os.makedirs(OUT, exist_ok=True)
GEO = os.path.join(AQUI, '..', '..', '..', 'fuentes', 'mapas', 'ne_50m_countries.geojson')

TINTA = (34, 32, 28); MAR = (168, 170, 164); TIERRA = (234, 223, 197)
ROJO = (184, 64, 47); OCRE = (163, 122, 58)
AZUL_SE = (0, 82, 147)


def FONTC(s):
    for f in ('GeorgiaPro-CondBold.ttf', 'georgiab.ttf', 'arialbd.ttf'):
        try: return ImageFont.truetype('C:/Windows/Fonts/' + f, s)
        except OSError: pass
    return ImageFont.load_default()


from shapely.geometry import shape, box
D = json.load(open(GEO, encoding='utf-8'))


def hoja(lon0, lon1, lat0, lat1, w, ss=2):
    """Devuelve (imagen base, proj, pj, W, H) para un bbox. Mercator."""
    m = lambda l: math.log(math.tan(math.pi / 4 + math.radians(l) / 2))
    h = int(round(w * (m(lat1) - m(lat0)) / math.radians(lon1 - lon0)))

    def proj(lon, lat):
        return ((lon - lon0) / (lon1 - lon0) * w * ss,
                (m(lat1) - m(lat)) / (m(lat1) - m(lat0)) * h * ss)
    pj = lambda lon, lat: tuple(c / ss for c in proj(lon, lat))

    im = Image.new('RGB', (w * ss, h * ss), MAR); d = ImageDraw.Draw(im)
    bb = box(lon0 - 3, lat0 - 3, lon1 + 3, lat1 + 3); outl = []
    for f in D['features']:
        g = shape(f['geometry'])
        if not g.intersects(bb): continue
        gg = g.intersection(bb); geoms = list(gg.geoms) if hasattr(gg, 'geoms') else [gg]
        for p in geoms:
            if p.is_empty or p.geom_type != 'Polygon': continue
            pts = [proj(*c) for c in p.exterior.coords]
            if len(pts) < 3: continue
            d.polygon(pts, fill=TIERRA)
            for ring in p.interiors: d.polygon([proj(*c) for c in ring.coords], fill=MAR)
            outl.append(pts)
    for pts in outl: d.line(pts + [pts[0]], fill=TINTA, width=3)
    return im.resize((w, h), Image.LANCZOS), proj, pj, w, h


# ================================================================= LA HOJA
LON0, LON1, LAT0, LAT1 = 8.0, 22.0, 54.8, 63.2
base, proj, pj, W, H = hoja(LON0, LON1, LAT0, LAT1, 3200)
db = ImageDraw.Draw(base)

ROT = {'SWEDEN': (15.4, 61.4, 62), 'NORWAY': (9.4, 61.2, 44), 'DENMARK': (9.3, 55.9, 30),
       'FINLAND': (21.2, 62.4, 34), 'BALTIC SEA': (19.0, 56.6, 40),
       'NORTH SEA': (8.7, 57.4, 30), 'GULF OF BOTHNIA': (19.6, 61.0, 26)}
for nm, (lo, la, sz) in ROT.items():
    x, y = pj(lo, la)
    db.text((x, y), nm, fill=(92, 86, 74), font=FONTC(sz), anchor='mm')
db.rectangle([0, 0, W - 1, H - 1], outline=TINTA, width=4)
base.save(os.path.join(OUT, 'mapa10_base.png'))

P = {
    'Stockholm':  (18.0686, 59.3293),
    'Sodertalje': (17.6252, 59.1955),
    'Uppsala':    (17.6389, 59.8586),
    'Goteborg':   (11.9746, 57.7089),
    'Malmo':      (13.0038, 55.6050),
    'Orebro':     (15.2066, 59.2741),
    'Copenhagen': (12.5683, 55.6761),
    'Oslo':       (10.7522, 59.9139),
    # bordes, para lineas hacia sitios fuera de la hoja
    'South edge': (14.0, LAT0 + 0.25),
    'East edge':  (LON1 - 0.4, 59.0),
    'Center':     (15.5, 59.0),
}
pts = {k: list(pj(*v)) for k, v in P.items()}
json.dump(pts, open(os.path.join(OUT, 'mapa10_pts.json'), 'w'), indent=1)

# ---------------------------------------------------------------- capa de ciudades
ciu = base.copy(); dc = ImageDraw.Draw(ciu)


def punto(nm, anc='lm', off=(20, 0), sz=44, color=TINTA, r=11, texto=None):
    """Marca + etiqueta. La posicion sale SIEMPRE de la proyeccion, nunca a ojo."""
    x, y = pj(*P[nm])
    dc.ellipse([x-r, y-r, x+r, y+r], fill=color, outline=(250, 246, 236), width=3)
    dc.text((x+off[0], y+off[1]), texto or nm.upper(), fill=color, font=FONTC(sz), anchor=anc)


punto('Stockholm', sz=52)
punto('Sodertalje', anc='rm', off=(-22, 16), color=ROJO, r=14, texto='SODERTALJE')
punto('Uppsala', anc='rm', off=(-22, -6), color=OCRE)
punto('Goteborg', anc='rm', off=(-22, 0), color=OCRE, texto='GOTHENBURG')
punto('Malmo', anc='rm', off=(-22, 0), color=OCRE)
punto('Orebro', anc='rm', off=(-22, -8), sz=38, color=(120, 114, 102), r=8)
ciu.save(os.path.join(OUT, 'mapa10_ciudades.png'))

# ---------------------------------------------------------------- comprobacion (regla 24)
sx, sy = pj(*P['Stockholm']); tx, ty = pj(*P['Sodertalje'])
sep = math.hypot(sx-tx, sy-ty)
gx = W / (LON1 - LON0)
print('hoja %dx%d  %.0f px por grado de longitud' % (W, H, gx))
print('Estocolmo-Sodertalje: %.0f px en la hoja (0,443 grados)' % sep)
assert sep > 60, 'Sodertalje y Estocolmo se confunden: hay que cerrar la hoja'
for nm in P:
    x, y = pj(*P[nm])
    assert -5 <= x <= W+5 and -5 <= y <= H+5, '%s cae fuera de la hoja' % nm
print('%d puntos, todos dentro de la hoja -> mapa10_pts.json' % len(P))
