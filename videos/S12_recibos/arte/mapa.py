# -*- coding: utf-8 -*-
"""Hoja de mapa de la serie S12, pieza 4 (Ceuta). Natural Earth 50m, Mercator. 0 creditos.

    cd videos/S12_recibos/arte && python mapa.py
    -> mapa12_base.png  mapa12_ciudades.png  mapa12_pts.json

**Que escala, y por que no la de la valla.** Lo que cuenta la pieza pasa en ocho kilometros: la
valla de Ceuta y sus dos extremos metidos en el agua. A esa escala **Natural Earth 50m no llega** —
Ceuta entera mide menos que el error de la costa— y dibujar la valla sobre una costa inventada seria
exactamente lo que la regla 24 prohibe.

Asi que la hoja hace lo que SI puede afirmar: **el Estrecho de Gibraltar**, con Espana al norte,
Marruecos al sur y Ceuta marcada en su coordenada real, del lado africano. Eso es lo que el
espectador necesita entender en tres segundos —que Ceuta es Espana pegada a Marruecos— y es
verificable punto por punto.

**El esquema de la valla va con props sobre la mesa, no sobre el mapa** (`cerca` + una linea roja),
y se lee como lo que es: un esquema. Un esquema declarado no le debe precision a nadie; una marca
sobre un mapa, si.

  LON -6,447 a -4,253 · LAT 35,40 a 36,40 · W = 3000 (16:9)  ->  **1367 px por grado**.

**Regla 24: los puntos son 100 % precisos.** Todo sale de `pj(lon, lat)` con grados decimales
reales, nunca de un pixel a ojo:

  Ceuta        35,8894 N   -5,3213 E    el enclave espanol (F4.3, F4.4)
  Fnideq       35,8500 N   -5,3567 E    Marruecos, pegado a la frontera; da nombre a las aguas
                                        donde se contaron muertos (F4.6)
  Tarifa       36,0128 N   -5,6045 E    la punta sur de la Espana peninsular
  Algeciras    36,1275 N   -5,4500 E    el puerto del otro lado
  Gibraltar    36,1408 N   -5,3536 E    referencia
  Tanger       35,7595 N   -5,8340 E    referencia
  Tetuan       35,5785 N   -5,3684 E    referencia

Al generarse comprueba dos cosas y avisa: que Ceuta y Fnideq se separen lo suficiente para leerse
como dos sitios (estan a 0,043 grados, que es poco), y a que distancia de tierra cae cada punto.
"""
import json, math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(AQUI, 'assets'); os.makedirs(OUT, exist_ok=True)
GEO = os.path.join(AQUI, '..', '..', '..', 'fuentes', 'mapas', 'ne_50m_countries.geojson')

TINTA = (34, 32, 28); MAR = (142, 154, 156); TIERRA = (234, 223, 197)
ROJO = (184, 64, 47); OCRE = (163, 122, 58)
BAJIO = (176, 186, 184)      # agua somera pegada a la costa: es lo que da relieve al contorno
COSTA = (58, 54, 48)         # la linea de costa, mas suave que TINTA pura


def FONTC(s):
    for f in ('GeorgiaPro-CondBold.ttf', 'georgiab.ttf', 'arialbd.ttf'):
        try: return ImageFont.truetype('C:/Windows/Fonts/' + f, s)
        except OSError: pass
    return ImageFont.load_default()


from shapely.geometry import shape, box, Point
D = json.load(open(GEO, encoding='utf-8'))


def _grano(size, amp=9.0, esc=6):
    """Grano de papel, el mismo recurso que `produccion/props.papel`. Sin esto, el mar y la tierra
    son dos planchas de color liso y el mapa se ve como un PowerPoint, no como una hoja."""
    import numpy as np
    rng = np.random.default_rng(7)
    g = rng.random((size[1]//esc+2, size[0]//esc+2)).astype(np.float32)
    g = np.asarray(Image.fromarray((g*255).astype(np.uint8)).resize(size, Image.BICUBIC))
    return (g.astype(np.float32)/255 - 0.5) * amp


def hoja(lon0, lon1, lat0, lat1, w, ss=2):
    """Devuelve (imagen base, proj, pj, W, H) para un bbox. Mercator.

    **Reescrita el 15-sep por calidad.** La primera version pintaba dos planchas de color liso con
    una linea negra de 3 px encima: en movimiento se veia plana y dura. Ahora la hoja se construye
    en cinco pasadas, que es lo que le da profundidad sin salirse de la paleta del canal:

      1. mar con grano de papel,
      2. **bajio** — una banda de agua clara pegada a la costa, difuminada, que separa tierra y mar
         antes de que haya ninguna linea,
      3. **sombra** de la tierra proyectada sobre el mar (desplazada 7 px y difuminada): es lo que
         hace que la tierra parezca estar POR ENCIMA del agua y no recortada sobre ella,
      4. tierra con su propio grano,
      5. linea de costa fina en dos tonos (oscura por fuera, clara por dentro).
    """
    import numpy as np
    m = lambda l: math.log(math.tan(math.pi / 4 + math.radians(l) / 2))
    h = int(round(w * (m(lat1) - m(lat0)) / math.radians(lon1 - lon0)))
    W2, H2 = w*ss, h*ss

    def proj(lon, lat):
        return ((lon - lon0) / (lon1 - lon0) * W2,
                (m(lat1) - m(lat)) / (m(lat1) - m(lat0)) * H2)
    pj = lambda lon, lat: tuple(c / ss for c in proj(lon, lat))

    # --- mascara de tierra
    mask = Image.new('L', (W2, H2), 0); dm = ImageDraw.Draw(mask)
    bb = box(lon0 - 3, lat0 - 3, lon1 + 3, lat1 + 3); outl = []
    for f in D['features']:
        g = shape(f['geometry'])
        if not g.intersects(bb): continue
        gg = g.intersection(bb); geoms = list(gg.geoms) if hasattr(gg, 'geoms') else [gg]
        for p in geoms:
            if p.is_empty or p.geom_type != 'Polygon': continue
            pts = [proj(*c) for c in p.exterior.coords]
            if len(pts) < 3: continue
            dm.polygon(pts, fill=255)
            for ring in p.interiors: dm.polygon([proj(*c) for c in ring.coords], fill=0)
            outl.append(pts)

    # --- 1 · mar con grano
    gr = _grano((W2, H2))
    base = np.zeros((H2, W2, 3), np.float32) + np.array(MAR, np.float32) + gr[..., None]

    # --- 2 · bajio: la mascara dilatada y difuminada, solo por fuera de la tierra
    ancho = max(6, int(W2*0.006))
    dil = mask.filter(ImageFilter.MaxFilter(2*(ancho//2)+1)).filter(ImageFilter.GaussianBlur(ancho*1.6))
    a = np.asarray(dil).astype(np.float32)/255 * (1 - np.asarray(mask).astype(np.float32)/255)
    base = base*(1-a[..., None]) + np.array(BAJIO, np.float32)*a[..., None]

    # --- 3 · sombra de la tierra sobre el agua
    off = max(4, int(W2*0.0035))
    sh = Image.new('L', (W2, H2), 0); sh.paste(mask, (off, int(off*1.15)))
    sh = sh.filter(ImageFilter.GaussianBlur(off*1.5))
    a = np.asarray(sh).astype(np.float32)/255 * 0.34 * (1 - np.asarray(mask).astype(np.float32)/255)
    base = base*(1-a[..., None]) + np.array((40, 44, 44), np.float32)*a[..., None]

    # --- 4 · tierra con grano propio
    a = np.asarray(mask).astype(np.float32)/255
    tierra = np.zeros((H2, W2, 3), np.float32) + np.array(TIERRA, np.float32) + _grano((W2, H2), 11.0, 5)[..., None]
    base = base*(1-a[..., None]) + tierra*a[..., None]

    im = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))

    # --- 5 · costa en dos tonos
    d = ImageDraw.Draw(im)
    for pts in outl: d.line(pts + [pts[0]], fill=COSTA, width=max(2, int(W2*0.0011)))
    borde = Image.new('RGBA', (W2, H2), (0, 0, 0, 0)); db = ImageDraw.Draw(borde)
    for pts in outl: db.line(pts + [pts[0]], fill=(255, 250, 238, 150), width=max(2, int(W2*0.0022)))
    interior = Image.new('L', (W2, H2), 0)
    interior.paste(mask.filter(ImageFilter.MinFilter(5)), (0, 0))
    borde.putalpha(Image.composite(borde.split()[3], Image.new('L', (W2, H2), 0), mask))
    im = Image.alpha_composite(im.convert('RGBA'), borde).convert('RGB')

    return im.resize((w, h), Image.LANCZOS), proj, pj, w, h


# ================================================================= LA HOJA
# El bbox es 16:9 A PROPOSITO, y esa es una correccion del 15-sep: con el recuadro casi cuadrado
# (-6,10 a -4,90) la hoja salia 3000x3086, y al meterla en un plano de 1920x1080 sobresalia 450 px
# por arriba y por abajo. Como `Scene.window()` limita la camara al lienzo, Espana quedaba PERMANENTE
# fuera de cuadro: en la prueba de vida solo se veia la costa marroqui. Ensanchando la longitud a
# 2,19 grados la hoja sale 16:9 y entra entera en el plano, que es lo que hace falta para volar por
# ella como en la referencia.
LON0, LON1, LAT0, LAT1 = -6.447, -4.253, 35.40, 36.40
base, proj, pj, W, H = hoja(LON0, LON1, LAT0, LAT1, 3000)
db = ImageDraw.Draw(base)

ROT = {'SPAIN': (-5.95, 36.28, 92), 'MOROCCO': (-5.60, 35.49, 92),
       'STRAIT OF GIBRALTAR': (-5.66, 35.98, 40), 'MEDITERRANEAN SEA': (-4.72, 35.80, 46)}
for nm, (lo, la, sz) in ROT.items():
    x, y = pj(lo, la)
    db.text((x, y), nm, fill=(92, 86, 74), font=FONTC(sz), anchor='mm')
db.rectangle([0, 0, W - 1, H - 1], outline=TINTA, width=4)
base.save(os.path.join(OUT, 'mapa12_base.png'))

P = {
    'Ceuta':     (-5.3213, 35.8894),
    'Fnideq':    (-5.3567, 35.8500),
    'Tarifa':    (-5.6045, 36.0128),
    'Algeciras': (-5.4500, 36.1275),
    'Gibraltar': (-5.3536, 36.1408),
    'Tangier':   (-5.8340, 35.7595),
    'Tetouan':   (-5.3684, 35.5785),
    'Center':    (-5.50, 35.90),
    'North edge': (-5.45, LAT1 - 0.06),
}
pts = {k: list(pj(*v)) for k, v in P.items()}
json.dump(pts, open(os.path.join(OUT, 'mapa12_pts.json'), 'w'), indent=1)

# ---------------------------------------------------------------- capa de ciudades
ciu = base.copy(); dc = ImageDraw.Draw(ciu)


def punto(nm, anc='lm', off=(22, 0), sz=46, color=TINTA, r=12, texto=None):
    """Marca + etiqueta. La posicion sale SIEMPRE de la proyeccion, nunca a ojo."""
    x, y = pj(*P[nm])
    dc.ellipse([x-r, y-r, x+r, y+r], fill=color, outline=(250, 246, 236), width=3)
    dc.text((x+off[0], y+off[1]), texto or nm.upper(), fill=color, font=FONTC(sz), anchor=anc)


# La etiqueta dice SPAIN a proposito: en la hoja, Ceuta cae sobre lo que el ojo lee como Marruecos,
# y la primera linea del guion es justo esa («Ceuta is Spain, on the African mainland»). Natural
# Earth 50m no resuelve el enclave, asi que lo dice la etiqueta y no un poligono inventado.
punto('Ceuta', color=ROJO, r=18, sz=60, off=(26, -4), texto='CEUTA · SPAIN')
punto('Fnideq', anc='rm', off=(-24, 16), color=OCRE, sz=40, r=10)
punto('Algeciras', anc='rm', off=(-24, -6), color=(120, 114, 102), sz=38, r=9)
punto('Gibraltar', off=(24, -4), color=(120, 114, 102), sz=38, r=9)
punto('Tangier', anc='rm', off=(-24, 0), color=(120, 114, 102), sz=38, r=9)
ciu.save(os.path.join(OUT, 'mapa12_ciudades.png'))

# ---------------------------------------------------------------- capa de marcas sola
# Se dibuja tambien SOBRE TRANSPARENTE para poder ponerla por ENCIMA de las capas de pais.
# Sin esto, al pintarse Marruecos de ocre la peninsula de Ceuta quedaba del color de Marruecos:
# el mapa afirmaba justo lo contrario de lo que dice el guion. Natural Earth 50m no separa el
# enclave, asi que la marca y la etiqueta tienen que ir por delante del color.
marcas = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dc = ImageDraw.Draw(marcas)
punto('Ceuta', color=ROJO, r=18, sz=60, off=(26, -4), texto='CEUTA · SPAIN')
punto('Fnideq', anc='rm', off=(-24, 16), color=OCRE, sz=40, r=10)
punto('Algeciras', anc='rm', off=(-24, -6), color=(120, 114, 102), sz=38, r=9)
punto('Gibraltar', off=(24, -4), color=(120, 114, 102), sz=38, r=9)
punto('Tangier', anc='rm', off=(-24, 0), color=(120, 114, 102), sz=38, r=9)
marcas.save(os.path.join(OUT, 'mapa12_marcas.png'))

# ---------------------------------------------------------------- comprobaciones (regla 24)
print('hoja %dx%d  ->  %.0f px por grado de longitud' % (W, H, W / (LON1 - LON0)))
cx, cy = pj(*P['Ceuta']); fx, fy = pj(*P['Fnideq'])
print('Ceuta-Fnideq: %.0f px en la hoja (%.3f grados)'
      % (math.hypot(cx - fx, cy - fy), math.hypot(P['Ceuta'][0] - P['Fnideq'][0],
                                                  P['Ceuta'][1] - P['Fnideq'][1])))
tierra = [shape(f['geometry']) for f in D['features']]
for nm, (lo, la) in P.items():
    if nm in ('Center', 'North edge'): continue
    p = Point(lo, la)
    dentro = any(g.contains(p) for g in tierra)
    if dentro:
        print('  %-10s sobre tierra' % nm)
    else:
        dmin = min(g.distance(p) for g in tierra)
        print('  %-10s EN AGUA, a %.3f grados (~%.1f km) de la costa de 50m'
              % (nm, dmin, dmin * 111.0))

# ---------------------------------------------------------------- capas de pais (estilo GeoGlobeTales)
# Referencia que paso Agustin el 15-sep (GeoGlobeTales, 11,9 M vistas): los paises son colores
# planos que se pintan mientras la voz los nombra, y ESE cambio de color es la narracion. El motor
# ya sabe revelarlas (`MapSheet.add_layer(..., mode='wipe')`); lo que faltaba eran las capas.
#
# Se pintan con el MISMO poligono de Natural Earth que dibuja la hoja, asi que encajan al pixel: no
# hay una silueta calcada a mano encima de otra.
# El mar pasó a ser azul-gris (142,154,156) al rehacer la hoja con calidad, asi que el azul de
# Espana tuvo que oscurecerse: con el (52,96,150) de la primera version, pais y mar quedaban a la
# misma luminancia y el pintado no se leia.
AZUL_ES = (36, 74, 126)
OCRE_MA = (178, 130, 56)


def capa_pais(nombres, color, salida, alpha=226):
    """Pinta uno o mas paises sobre una capa transparente del tamano de la hoja."""
    cap = Image.new('RGBA', (W * 2, H * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(cap)
    bb = box(LON0 - 3, LAT0 - 3, LON1 + 3, LAT1 + 3)
    n = 0
    for f in D['features']:
        nm = (f.get('properties', {}).get('NAME') or
              f.get('properties', {}).get('ADMIN') or
              f.get('properties', {}).get('name') or '')
        if nm not in nombres: continue
        g = shape(f['geometry'])
        if not g.intersects(bb): continue
        gg = g.intersection(bb); geoms = list(gg.geoms) if hasattr(gg, 'geoms') else [gg]
        for p in geoms:
            if p.is_empty or p.geom_type != 'Polygon': continue
            pts = [proj(*c) for c in p.exterior.coords]
            if len(pts) < 3: continue
            d.polygon(pts, fill=color + (alpha,)); n += 1
    cap = cap.resize((W, H), Image.LANCZOS)
    cap.save(os.path.join(OUT, salida))
    print('  %-24s %d poligonos' % (salida, n))
    return n


print('capas de pais:')
capa_pais({'Spain'}, AZUL_ES, 'mapa12_es.png')
capa_pais({'Morocco'}, OCRE_MA, 'mapa12_ma.png')
