# -*- coding: utf-8 -*-
"""ESTANDAR VISUAL V2 como BIBLIOTECA: el mapa deja de ser una hoja que aparece a veces y pasa a ser
el SUELO del video (`motor.Mundo`). 0 creditos: PIL + numpy + shapely + Natural Earth 50m.

Sale de `videos/09_deuda_eeuu/arte/mapa_v2.py` (prueba de concepto del 15-sep) y conserva el mismo
look: oceano teal, orilla clara, tierra kaki con relieve procedural, paises coloreados POR ROL,
rotulos sobre el territorio y grano de papel.

    import mapa_v2 as MV
    mundo = MV.mundo('estrecho', (-6.447, -4.253, 35.40, 36.40), 4000,
                     roles={'ESP': 'institucion', 'MAR': 'tercero'},
                     sitios={'Ceuta': (-5.3213, 35.8894), ...},
                     capas={'esp': (['ESP'], MV.ROL['institucion'])},
                     out_dir='arte/assets')
    sc = motor.Scene(mundo, size=(1080, 1920), v4=True)
    mundo.add_layer(mundo.meta['capas']['esp'], 12.0, 1.4)

Funciones:
  hoja_v2(lon0, lon1, lat0, lat1, w, ...) -> (RGB, meta)   la hoja rica
  capa_pais(meta, paises, color, alpha)   -> RGBA          encaja al pixel con la hoja
  pins(meta, sitios, ...)                 -> RGBA          punto exacto + etiqueta (regla 24)
  mundo(nombre, bbox, w, ...)             -> motor.Mundo   la guarda en disco y la devuelve

REGLA 24 (los sitios del mapa son exactos): `mundo()` comprueba cada sitio contra una proyeccion
Mercator calculada APARTE y aborta si alguno se pasa de 3 px. Se imprime siempre.
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from shapely.geometry import shape, box

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..'))
GEO = os.path.join(RAIZ, 'fuentes', 'mapas', 'ne_50m_countries.geojson')
sys.path.insert(0, AQUI)
import props as PR
import motor as M

# ============================================================ PALETA V2 (ESTANDAR_VISUAL_V2.md §2)
TINTA = (34, 32, 28)
PAPEL = (233, 223, 203)          # los objetos siguen siendo de papel: recibo, bono, carteles, sello
OCEANO = (70, 142, 152)          # teal saturado (la referencia mide (79,151,158) en aguas abiertas)
ORILLA = (132, 194, 196)         # agua baja: halo claro pegado a la costa
TIERRA = (190, 178, 136)         # kaki papel; la referencia mide (157,152,116)
ROL = {                          # color = rol en la historia, no nacionalidad
    'deudor':      (198, 48, 44),    # rojo senal: lo que esta en disputa / la cifra que duele
    'acreedor':    (226, 140, 44),   # ocre: dinero, el que cobra
    'institucion': (52, 88, 170),    # azul: Estados, tratados, bancos centrales
    'sujeto':      (72, 178, 190),   # celeste: el pais del que habla el video
    'tercero':     (92, 150, 72),    # verde: el tercero interesado, el aliado
}
LABEL_TIERRA = (84, 76, 58)
ROJO = (184, 64, 47)
OCRE = (163, 122, 58)

NOMBRE = {'United Kingdom': 'Britain', 'United States of America': 'United States',
          'Dem. Rep. Congo': 'D.R. Congo', 'Central African Rep.': 'Central Africa',
          'Bosnia and Herz.': 'Bosnia', 'S. Sudan': 'South Sudan'}

_D = None


def datos():
    """Natural Earth 50m, cargado una sola vez por proceso (son ~25 MB de JSON)."""
    global _D
    if _D is None:
        _D = json.load(open(GEO, encoding='utf-8'))
    return _D


def fuente(nombre, s):
    try: return ImageFont.truetype('C:/Windows/Fonts/' + nombre, int(s))
    except OSError: return ImageFont.load_default()


def ruido(w, h, celda, seed):
    """Ruido suave 0..1 por celdas (como props.grano pero con celda variable)."""
    rng = np.random.default_rng(seed)
    g = rng.random((h // celda + 2, w // celda + 2)).astype(np.float32)
    im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im).astype(np.float32) / 255.0


# ---------------------------------------------------------------- proyeccion (regla 24)
def _m(l): return math.log(math.tan(math.pi / 4 + math.radians(l) / 2))


def proyeccion(lon0, lon1, lat0, lat1, w):
    """Mercator del bbox a un lienzo de ancho `w`. Devuelve (pj, w, h). UNICA fuente de px."""
    h = int(round(w * (_m(lat1) - _m(lat0)) / math.radians(lon1 - lon0)))
    def pj(lon, lat):
        return ((lon - lon0) / (lon1 - lon0) * w,
                (_m(lat1) - _m(lat)) / (_m(lat1) - _m(lat0)) * h)
    return pj, w, h


def _iso(p):
    return p.get('ADM0_A3') or p.get('ISO_A3')


def _casa(p, quienes):
    """True si el pais `p` esta en `quienes` (acepta ISO_A3 y NAME/ADMIN)."""
    if not quienes: return False
    return (_iso(p) in quienes or p.get('NAME') in quienes or p.get('ADMIN') in quienes
            or NOMBRE.get(p.get('NAME')) in quienes)


# ---------------------------------------------------------------- la hoja
def hoja_v2(lon0, lon1, lat0, lat1, w, roles=None, etiquetas=True, agua=(), ss=2, seed=9,
            rotulos_pos=None, sitios=None, rotulos_extra=()):
    """Hoja de mapa v2. Devuelve (imagen RGB, meta).

    roles        : {ISO_A3 o NAME: 'deudor'|'acreedor'|'institucion'|'sujeto'|'tercero'}
    agua         : [(texto, lon, lat, size)]  rotulos de mares y oceanos
    etiquetas    : rotular cada pais SOBRE su territorio si le cabe (LABEL_X/Y de Natural Earth)
    rotulos_pos  : {ISO_A3: (lon, lat)} corre un rotulo cuando un personaje o una tarjeta lo taparia
    rotulos_extra: [(texto, lon, lat, size[, color])] rotulo de tierra puesto a mano. Hace falta
                   cuando el bbox es un primer plano y el LABEL_X/Y del pais cae FUERA (el Estrecho
                   de Gibraltar: los centroides de Espana y de Marruecos estan a cientos de km).
    sitios       : {nombre: (lon, lat)}; van al meta['pts'] en px de hoja (dibujarlos es `pins`)

    meta = {bbox, w, h, px_por_grado, pts, roles, pj}
    """
    roles = roles or {}; rotulos_pos = rotulos_pos or {}
    pj, w, h = proyeccion(lon0, lon1, lat0, lat1, w)
    W2, H2 = w * ss, h * ss
    def proj(lon, lat, k=ss):
        x, y = pj(lon, lat); return (x * k, y * k)

    D = datos()
    # ---- 1. mascaras y colores a doble resolucion (bordes limpios), despues se bajan
    mask = Image.new('L', (W2, H2), 0); dm = ImageDraw.Draw(mask)
    col = Image.new('RGB', (W2, H2), TIERRA); dc = ImageDraw.Draw(col)
    bord = Image.new('L', (W2, H2), 0); db = ImageDraw.Draw(bord)
    glow = Image.new('L', (W2, H2), 0); dg = ImageDraw.Draw(glow)
    bb = box(lon0 - 3, lat0 - 3, lon1 + 3, lat1 + 3)
    partes = {}      # iso -> ancho en px (a 1x) del trozo mas grande, para el cuerpo de la etiqueta
    for f in D['features']:
        p = f['properties']; iso = _iso(p)
        g = shape(f['geometry'])
        if not g.intersects(bb): continue
        gg = g.intersection(bb); geoms = list(gg.geoms) if hasattr(gg, 'geoms') else [gg]
        rol = roles.get(iso) or roles.get(p.get('NAME')) or roles.get(p.get('ADMIN'))
        for q in geoms:
            if q.is_empty or q.geom_type != 'Polygon': continue
            pts = [proj(*c) for c in q.exterior.coords]
            if len(pts) < 3: continue
            dm.polygon(pts, fill=255)
            dc.polygon(pts, fill=ROL[rol] if rol else TIERRA)
            for ring in q.interiors:
                rp = [proj(*c) for c in ring.coords]
                dm.polygon(rp, fill=0); dc.polygon(rp, fill=OCEANO)
            db.line(pts + [pts[0]], fill=255, width=4)
            if rol: dg.line(pts + [pts[0]], fill=255, width=14)
            xs = [a for a, _ in pts]
            partes[iso] = max(partes.get(iso, 0), (max(xs) - min(xs)) / ss)
    mask = mask.resize((w, h), Image.LANCZOS); col = col.resize((w, h), Image.LANCZOS)
    bord = bord.resize((w, h), Image.LANCZOS)
    glow = glow.resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(3))

    # ---- 2. oceano: color base + manchas de acuarela + halo claro pegado a la costa
    mk = np.asarray(mask).astype(np.float32) / 255.0
    oce = np.zeros((h, w, 3), np.float32) + np.array(OCEANO, np.float32)
    oce += ((ruido(w, h, 110, seed + 1) - 0.5) * 14 + (ruido(w, h, 26, seed + 2) - 0.5) * 6)[..., None]
    halo = np.asarray(mask.filter(ImageFilter.GaussianBlur(26))).astype(np.float32) / 255.0
    halo = np.clip(halo * (1.0 - mk) * 1.35, 0, 1)
    oce = oce * (1 - halo[..., None]) + np.array(ORILLA, np.float32) * halo[..., None]

    # ---- 3. tierra: relieve procedural (sombreado con luz del noroeste), solo sobre la tierra
    N = 0.55 * ruido(w, h, 170, seed + 3) + 0.30 * ruido(w, h, 60, seed + 4) + 0.15 * ruido(w, h, 20, seed + 5)
    gy, gx = np.gradient(N)
    s = -gx - gy                                  # luz desde arriba a la izquierda
    s = (s - s.mean()) / (s.std() + 1e-6)
    sombra = 1.0 + 0.075 * np.clip(s, -2.2, 2.2)
    tierra = np.asarray(col).astype(np.float32) * sombra[..., None]

    # ---- 4. composicion: agua + tierra + brillo de los territorios con rol + tinta de fronteras
    out = oce * (1 - mk[..., None]) + tierra * mk[..., None]
    gl = np.asarray(glow).astype(np.float32) / 255.0 * 0.55
    out = out * (1 - gl[..., None]) + np.array((252, 250, 236), np.float32) * gl[..., None]
    bd = np.asarray(bord).astype(np.float32) / 255.0 * 0.82
    out = out * (1 - bd[..., None]) + np.array(TINTA, np.float32) * bd[..., None]
    out += (PR.grano((w, h)) * 12)[..., None]       # el grano de papel de siempre: identidad
    im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

    # ---- 5. rotulos sobre el propio territorio (LABEL_X/LABEL_Y de Natural Earth)
    d = ImageDraw.Draw(im); puestos = []
    def choca(b):
        return any(not (b[2] < q[0] or b[0] > q[2] or b[3] < q[1] or b[1] > q[3]) for q in puestos)
    if etiquetas:
        feats = sorted(D['features'], key=lambda f: -partes.get(_iso(f['properties']), 0))
        for f in feats:                         # los grandes primero: si dos chocan, gana el grande
            p = f['properties']; iso = _iso(p)
            if iso not in partes: continue
            lx, ly = rotulos_pos.get(iso) or (p.get('LABEL_X'), p.get('LABEL_Y'))
            if lx is None or not (lon0 < lx < lon1 and lat0 < ly < lat1): continue
            nombre = NOMBRE.get(p.get('NAME'), p.get('NAME'))
            ancho = partes[iso]
            rol = roles.get(iso) or roles.get(p.get('NAME')) or roles.get(p.get('ADMIN'))
            # el cuerpo sale del ancho del pais: el nombre tiene que caber DENTRO
            size = int(min(ancho * 0.16, w * 0.026)) if not rol else int(min(ancho * 0.19, w * 0.03))
            if size < w * 0.0085 and not rol: continue
            fnt = fuente('GeorgiaPro-BoldItalic.ttf' if rol else 'GeorgiaPro-Italic.ttf', max(size, 30))
            tw = d.textlength(nombre, font=fnt)
            if tw > ancho * 0.92 and not rol: continue
            x, y = pj(lx, ly)
            b = d.textbbox((x, y), nombre, font=fnt, anchor='mm')
            if choca(b) and not rol: continue
            puestos.append(b)
            if rol:
                base = ROL[rol]
                d.text((x, y), nombre, font=fnt, fill=tuple(int(c * 0.42) for c in base), anchor='mm',
                       stroke_width=max(2, size // 14), stroke_fill=(252, 248, 234))
            else:
                d.text((x, y), nombre, font=fnt, fill=LABEL_TIERRA, anchor='mm',
                       stroke_width=max(1, size // 22), stroke_fill=(224, 214, 178))
    for txt, lo, la, sz in agua:
        x, y = pj(lo, la)
        d.text((x, y), txt, font=fuente('GeorgiaPro-CondItalic.ttf', sz), fill=(214, 236, 234),
               anchor='mm', stroke_width=1, stroke_fill=(52, 110, 122))
    for r in rotulos_extra:
        txt, lo, la, sz = r[0], r[1], r[2], r[3]
        cl = r[4] if len(r) > 4 else LABEL_TIERRA
        x, y = pj(lo, la)
        d.text((x, y), txt, font=fuente('GeorgiaPro-BoldItalic.ttf', sz), fill=cl, anchor='mm',
               stroke_width=max(2, int(sz // 16)), stroke_fill=(246, 240, 216))

    pts = {k: [round(v, 2) for v in pj(*ll)] for k, ll in (sitios or {}).items()}
    meta = {'bbox': [lon0, lon1, lat0, lat1], 'w': w, 'h': h,
            'px_por_grado': round(w / (lon1 - lon0), 3), 'pts': pts,
            'roles': roles, 'sitios': {k: list(v) for k, v in (sitios or {}).items()}, 'pj': pj}
    return im, meta


# ---------------------------------------------------------------- capas y pins
def capa_pais(meta, paises, color, alpha=226, ss=2, borde=0):
    """RGBA del tamano de la hoja con uno o mas paises pintados. Usa el MISMO poligono de Natural
    Earth que dibujo la hoja, asi que encaja al pixel: no hay una silueta calcada a mano encima."""
    lon0, lon1, lat0, lat1 = meta['bbox']; w, h = meta['w'], meta['h']
    pj, _, _ = proyeccion(lon0, lon1, lat0, lat1, w)
    quienes = {paises} if isinstance(paises, str) else set(paises)
    cap = Image.new('RGBA', (w * ss, h * ss), (0, 0, 0, 0)); d = ImageDraw.Draw(cap)
    bb = box(lon0 - 3, lat0 - 3, lon1 + 3, lat1 + 3); n = 0
    for f in datos()['features']:
        p = f['properties']
        if not _casa(p, quienes): continue
        g = shape(f['geometry'])
        if not g.intersects(bb): continue
        gg = g.intersection(bb); geoms = list(gg.geoms) if hasattr(gg, 'geoms') else [gg]
        for q in geoms:
            if q.is_empty or q.geom_type != 'Polygon': continue
            pts = [tuple(c * ss for c in pj(*cc)) for cc in q.exterior.coords]
            if len(pts) < 3: continue
            d.polygon(pts, fill=tuple(color) + (alpha,)); n += 1
            for ring in q.interiors:
                d.polygon([tuple(c * ss for c in pj(*cc)) for cc in ring.coords], fill=(0, 0, 0, 0))
            if borde: d.line(pts + [pts[0]], fill=(252, 248, 234, 235), width=borde * ss)
    cap = cap.resize((w, h), Image.LANCZOS)
    cap.n_poligonos = n          # el atributo va DESPUES del resize: `resize` devuelve otra imagen
    return cap


def capa_geojson(meta, ruta, nombres, color, alpha=226, ss=2, borde=0):
    """Como `capa_pais`, pero el poligono sale de un geojson APARTE en vez de Natural Earth 50m.

    **Para que existe.** La hoja se dibuja con NE 50m, que no separa los enclaves: al pintar
    Marruecos, la peninsula de Ceuta queda del color de Marruecos y el mapa afirma lo contrario que
    el guion (es la trampa que anota `ESTADO.md` y que la prueba v4 tapaba volviendo a poner las
    marcas encima — el punto rojo quedaba sobre tierra marroqui). La solucion de verdad es pintar
    Ceuta con el color de Espana POR ENCIMA de la capa de Marruecos, y para eso hace falta un
    poligono que si distinga el enclave: NE **10m** `admin_0_map_subunits`, dominio publico,
    recortado a Ceuta y Melilla en `fuentes/mapas/ne_10m_ceuta_melilla.geojson` (1,5 KB).

    `nombres` se compara contra la propiedad `name` de cada feature. Usa la MISMA proyeccion
    (`meta`), asi que encaja al pixel con la hoja y con las capas de pais.
    """
    lon0, lon1, lat0, lat1 = meta['bbox']; w, h = meta['w'], meta['h']
    pj, _, _ = proyeccion(lon0, lon1, lat0, lat1, w)
    quienes = {nombres} if isinstance(nombres, str) else set(nombres)
    gj = json.load(open(ruta, encoding='utf-8'))
    cap = Image.new('RGBA', (w * ss, h * ss), (0, 0, 0, 0)); d = ImageDraw.Draw(cap)
    bb = box(lon0 - 3, lat0 - 3, lon1 + 3, lat1 + 3); n = 0
    for f in gj['features']:
        p = f.get('properties', {})
        if not (quienes & {str(p.get(k)) for k in ('name', 'NAME', 'subunit', 'SUBUNIT')}): continue
        g = shape(f['geometry'])
        if not g.intersects(bb): continue
        gg = g.intersection(bb); geoms = list(gg.geoms) if hasattr(gg, 'geoms') else [gg]
        for q in geoms:
            if q.is_empty or q.geom_type != 'Polygon': continue
            pts = [tuple(c * ss for c in pj(*cc)) for cc in q.exterior.coords]
            if len(pts) < 3: continue
            d.polygon(pts, fill=tuple(color) + (alpha,)); n += 1
            for ring in q.interiors:
                d.polygon([tuple(c * ss for c in pj(*cc)) for cc in ring.coords], fill=(0, 0, 0, 0))
            if borde: d.line(pts + [pts[0]], fill=(252, 248, 234, 235), width=borde * ss)
    cap = cap.resize((w, h), Image.LANCZOS)
    cap.n_poligonos = n
    return cap


def pins(meta, sitios=None, color=None, r=None, size=None, off=(1.9, -0.25), anc='lm', mayus=True,
         opciones=None):
    """RGBA con el punto EXACTO de cada sitio y su etiqueta. Va SIEMPRE por encima de las capas de
    pais: Natural Earth 50m no separa los enclaves, y al pintar el pais vecino el sitio quedaria de
    su color (la peninsula de Ceuta, el caso del S12).

    `opciones`: {sitio: {color, r, size, off, anc, texto}} — el sitio que lleva el peso de la pieza
    se pone grande y rojo, los de referencia chicos y grises, y el anclaje se elige para que dos
    etiquetas vecinas no se pisen (Algeciras y Gibraltar estan a 10 km).
    """
    w, h = meta['w'], meta['h']
    pts = meta['pts']
    opciones = opciones or {}
    nombres = sitios if sitios is not None else list(pts)
    if isinstance(nombres, dict): nombres = list(nombres)
    cap = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(cap)
    R0 = r or max(6, int(w * 0.0042))
    S0 = size or max(22, int(w * 0.0145))
    for nm in nombres:
        if nm not in pts: continue
        op = opciones.get(nm, {})
        c = tuple(op.get('color') or ((color or {}).get(nm, ROJO) if isinstance(color, dict) else (color or ROJO)))
        R = int(op.get('r', R0)); S = int(op.get('size', S0))
        o = op.get('off', off); an = op.get('anc', anc)
        txt = op.get('texto') or (nm.upper() if mayus else nm)
        fnt = fuente('GeorgiaPro-CondBold.ttf', S)
        x, y = pts[nm]
        d.ellipse([x - R, y - R, x + R, y + R], fill=c + (255,), outline=(250, 246, 236, 255),
                  width=max(2, R // 4))
        d.text((x + o[0] * R, y + o[1] * R), txt, fill=c + (255,),
               font=fnt, anchor=an, stroke_width=max(2, S // 11), stroke_fill=(250, 246, 236, 225))
    return cap


# ---------------------------------------------------------------- el mundo completo
def _guardar(obj, ruta, es_json=False):
    """Escribe a un temporal y RENOMBRA. El rename es atomico, `save` no.

    Por que hace falta: `build()` corre en los 20 workers del pool y todos llaman a `mundo()`. Si la
    cache esta fria —o se invalida, que es lo que paso al meter los colores en la firma— los veinte
    generan el mismo PNG A LA VEZ y se pisan mientras escriben. Resultado medido en la S12:
    `mundo_hormuz_marcas.png` de **0 bytes** y el render abortando con «broken PNG file». Con el
    rename, un worker que llegue tarde encuentra el archivo entero o no lo encuentra, nunca a medias.
    El temporal lleva el PID para que dos procesos no compartan el mismo.
    """
    tmp = '%s.%d.tmp' % (ruta, os.getpid())
    if es_json:
        with open(tmp, 'w', encoding='utf-8') as f: json.dump(obj, f, indent=1)
    else:
        # el formato va EXPLICITO: PIL lo deduce de la extension y `.tmp` no le dice nada
        obj.save(tmp, format='PNG')
    os.replace(tmp, ruta)


def _chequeo_regla24(meta, tol=3.0):
    """Cada sitio, contra una proyeccion Mercator calculada APARTE. Imprime y devuelve el peor error."""
    lon0, lon1, lat0, lat1 = meta['bbox']; w, h = meta['w'], meta['h']
    peor, quien = 0.0, ''
    for nm, (lon, lat) in meta.get('sitios', {}).items():
        gx = (lon - lon0) / (lon1 - lon0) * w
        gy = (_m(lat1) - _m(lat)) / (_m(lat1) - _m(lat0)) * h
        px, py = meta['pts'][nm]
        e = math.hypot(gx - px, gy - py)
        if e > peor: peor, quien = e, nm
    print('  regla 24: peor error %.3f px (%s) sobre %d sitios  ->  %s'
          % (peor, quien or '-', len(meta.get('sitios', {})), 'OK' if peor < tol else 'FALLA'))
    if peor >= tol:
        raise SystemExit('REGLA 24: un sitio cae a %.2f px de su proyeccion (tope %.1f)' % (peor, tol))
    return peor


def mundo(nombre, bbox, w, roles=None, sitios=None, agua=(), out_dir=None, capas=None,
          marcas=True, etiquetas=True, rotulos_pos=None, force=False, seed=9, pin_color=None,
          rotulos_extra=(), pins_opciones=None, capas_geojson=None):
    """Construye (o reusa) el suelo del video y lo devuelve como `motor.Mundo`.

    Guarda en `out_dir`:  mundo_<nombre>.png · mundo_<nombre>_pts.json · mundo_<nombre>_meta.json
    y una capa por entrada de `capas` = {alias: (paises, color[, alpha])}, en
    mundo_<nombre>_<alias>.png. Las rutas quedan en `meta['capas']`, listas para `add_layer`.

    `force=False` reusa lo que ya esta en disco: `build()` corre en CADA worker del pool y
    regenerar una hoja de 4000 px veinte veces seria absurdo.
    """
    out_dir = out_dir or os.path.join(AQUI, 'assets')
    os.makedirs(out_dir, exist_ok=True)
    png = os.path.join(out_dir, 'mundo_%s.png' % nombre)
    pj_ = os.path.join(out_dir, 'mundo_%s_pts.json' % nombre)
    mj = os.path.join(out_dir, 'mundo_%s_meta.json' % nombre)
    lon0, lon1, lat0, lat1 = bbox
    firma = {'bbox': list(bbox), 'w': int(w), 'roles': roles or {},
             'sitios': {k: list(v) for k, v in (sitios or {}).items()},
             # La firma lleva los COLORES, no solo los alias. Sin esto, cambiar el rol de un pais
             # (S12 pieza 1: EE. UU. de `sujeto` a `institucion`) no invalidaba la cache y el
             # mundo seguia saliendo del PNG viejo sin decir nada.
             'capas': sorted((k, list(v[1]), v[2] if len(v) > 2 else 226)
                             for k, v in (capas or {}).items()),
             'capas_geojson': sorted((k, list(v[2]), v[3] if len(v) > 3 else 226)
                                     for k, v in (capas_geojson or {}).items()),
             'marcas': bool(marcas), 'seed': seed,
             'rotulos_extra': [list(r) for r in rotulos_extra],
             'agua': [list(a) for a in agua],
             'pins': sorted((pins_opciones or {}).keys())}
    if not force and os.path.exists(png) and os.path.exists(mj):
        meta = json.load(open(mj, encoding='utf-8'))
        # La firma se compara SERIALIZADA. Al guardarla en JSON las tuplas vuelven como listas, asi
        # que `meta['firma'] == firma` daba False SIEMPRE en cuanto la firma dejo de ser de tipos
        # planos (§2.4c): la cache no acertaba nunca y los veinte workers del pool se ponian a
        # regenerar el mundo a la vez — que es de donde salieron el PNG de 0 bytes y el
        # «Acceso denegado» al renombrar sobre un archivo que otro worker tenia abierto.
        _f = lambda d: json.dumps(d, sort_keys=True, default=list)
        if _f(meta.get('firma')) == _f(firma):
            mu = M.Mundo(png, pts=pj_, meta=meta, nombre=nombre)
            return mu
    print('mapa_v2.mundo(%s): generando %d px ...' % (nombre, w), flush=True)
    im, meta = hoja_v2(lon0, lon1, lat0, lat1, w, roles=roles, etiquetas=etiquetas, agua=agua,
                       seed=seed, rotulos_pos=rotulos_pos, sitios=sitios,
                       rotulos_extra=rotulos_extra)
    meta.pop('pj', None)
    _chequeo_regla24(meta)
    rutas = {}
    for alias, spec in (capas or {}).items():
        paises, color = spec[0], spec[1]
        alpha = spec[2] if len(spec) > 2 else 226
        cp = capa_pais(meta, paises, color, alpha=alpha)
        p = os.path.join(out_dir, 'mundo_%s_%s.png' % (nombre, alias))
        _guardar(cp, p); rutas[alias] = p
        print('  capa %-10s %d poligonos -> %s' % (alias, getattr(cp, 'n_poligonos', 0), os.path.basename(p)))
    # Capas por geojson aparte (enclaves que NE 50m no separa: Ceuta, Melilla). Van DESPUES de las
    # de pais a proposito: el orden en que se guardan no manda —manda el orden de `add_layer` en la
    # coreografia—, pero dejarlas juntas y nombradas aparte deja claro que son otra fuente.
    for alias, spec in (capas_geojson or {}).items():
        ruta, nombres, color = spec[0], spec[1], spec[2]
        alpha = spec[3] if len(spec) > 3 else 226
        cp = capa_geojson(meta, ruta, nombres, color, alpha=alpha)
        p = os.path.join(out_dir, 'mundo_%s_%s.png' % (nombre, alias))
        _guardar(cp, p); rutas[alias] = p
        print('  capa %-10s %d poligonos (geojson) -> %s'
              % (alias, getattr(cp, 'n_poligonos', 0), os.path.basename(p)))
        if not getattr(cp, 'n_poligonos', 0):
            print('  AVISO: la capa geojson "%s" salio VACIA (nombres=%s)' % (alias, nombres))
    if marcas and meta['pts']:
        mk = pins(meta, color=pin_color, opciones=pins_opciones)
        p = os.path.join(out_dir, 'mundo_%s_marcas.png' % nombre)
        _guardar(mk, p); rutas['marcas'] = p
        # las marcas van HORNEADAS en la hoja tambien: asi el mapa nunca esta sin rotular, y la capa
        # suelta queda para volver a ponerlas POR ENCIMA de un pais pintado.
        im = Image.alpha_composite(im.convert('RGBA'), mk).convert('RGB')
    meta['capas'] = rutas; meta['firma'] = firma; meta['nombre'] = nombre
    _guardar(im, png)
    _guardar(meta['pts'], pj_, es_json=True)
    # el META va EL ULTIMO: es lo que mira la cache, asi que hasta que no esten todos los PNG
    # enteros ningun otro proceso da el mundo por bueno.
    _guardar(meta, mj, es_json=True)
    print('  %dx%d  %.1f px/grado  %d sitios  ->  %s'
          % (meta['w'], meta['h'], meta['px_por_grado'], len(meta['pts']), os.path.basename(png)))
    return M.Mundo(png, pts=pj_, meta=meta, nombre=nombre)


if __name__ == '__main__':
    # demo: el Estrecho de Gibraltar de la S12, que es la prueba de aceptacion del motor v4
    d = os.path.join(RAIZ, 'videos', 'S12_recibos', 'arte', 'assets')
    mu = mundo('estrecho', (-6.447, -4.253, 35.40, 36.40), 4000,
               roles={'ESP': 'institucion', 'MAR': 'tercero'},
               sitios={'Ceuta': (-5.3213, 35.8894), 'Fnideq': (-5.3567, 35.8500),
                       'Tarifa': (-5.6045, 36.0128), 'Algeciras': (-5.4500, 36.1275),
                       'Gibraltar': (-5.3536, 36.1408), 'Tangier': (-5.8340, 35.7595),
                       'Tetouan': (-5.3684, 35.5785)},
               agua=[('STRAIT OF GIBRALTAR', -5.66, 35.98, 52),
                     ('MEDITERRANEAN SEA', -4.70, 35.78, 60),
                     ('ATLANTIC OCEAN', -6.20, 35.70, 54)],
               capas={'esp': (['ESP'], ROL['institucion']), 'mar': (['MAR'], ROL['acreedor'])},
               out_dir=d, force='--force' in sys.argv)
    print(mu.w, mu.h, list(mu.pts)[:4])
