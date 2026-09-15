# -*- coding: utf-8 -*-
"""Los cuatro MUNDOS de la S12, uno por pieza (motor v4). 0 creditos: todo sale de Natural Earth.

    python mundos4.py            # genera los cuatro y guarda un cuadro de QC de cada uno
    python mundos4.py 4          # solo el de la pieza 4
    python mundos4.py 4 --force  # lo regenera aunque este en disco

REGLAS QUE MANDAN ACA

  · **Regla 24**: cada sitio sale de lon/lat y `mapa_v2.mundo()` aborta si cae a mas de 3 px de una
    proyeccion Mercator calculada aparte. Ninguna coordenada se pone a ojo.
  · **El bbox es MAS ALTO QUE ANCHO** en las cuatro. Con un bbox 16:9 (lo que tenia la prueba v4) el
    cuadro vertical solo puede recorrer una franja estrecha y a `zmin` sobran mundo a los lados y
    falta arriba y abajo. Con h/w > 1, a `zmin` se ve el alto entero del mundo.
  · **Los rotulos se miden contra la VENTANA, no contra el mundo** (`MOTOR_V4.md` §9). Un mundo de
    2600 px visto a `zmin` por un cuadro vertical muestra ~1900 px de ancho: un rotulo de 150 px
    ocuparia el 8 % del ancho de pantalla y a 405 px no se leeria. Los de pais van a 72-84 px y los
    de agua a 52-64; comprobado en los cuadros de `_qc/`.
  · **Los roles NO van horneados**: la tierra sale kaki neutra y el color entra por `capas`, que la
    coreografia enciende cuando la voz nombra el pais. Un color puesto desde el cuadro 0 no narra.

DOS DECISIONES QUE NO SON TECNICAS Y QUEDAN ANOTADAS

  1. **El agua de la pieza 1 no lleva rotulo.** El nombre de ese golfo esta en disputa politica
     desde 2025 y el guion **no lo nombra ni una vez**: la pieza habla de cuatro domos de sal en
     Texas y Luisiana. Poner un nombre —cualquiera de los dos— seria que el mapa tome una postura
     que Agustin no tomo y que el guion no necesita. Se rotulan TEXAS y LOUISIANA, que es de lo que
     habla la voz. Si Agustin quiere el rotulo, es una linea.
  2. **Ceuta se pinta con el color de Espana POR ENCIMA de Marruecos** (ver `capa_ceuta`).
"""
import json, math, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
PROD = os.path.join(RAIZ, 'produccion')
sys.path.insert(0, PROD); sys.path.insert(0, AQUI)
import mapa_v2 as MV
import props as PR

ARTE = os.path.join(AQUI, 'arte', 'assets')
QC = os.path.join(AQUI, '_qc')
GEO_ENCLAVES = os.path.join(RAIZ, 'fuentes', 'mapas', 'ne_10m_ceuta_melilla.geojson')
GRIS = (108, 102, 92)


# ================================================================= 1 · EL TANQUE (Golfo, EE. UU.)
# Las cuatro localidades donde el DOE ubica los domos de sal de la reserva (F1.10). En el mapa se
# marca la LOCALIDAD, no el domo: no hay coordenada citable del sitio y marcarla seria inventarla.
# Cada una verificada contra su pagina de Wikipedia el 2026-09-15 (ver `fuentes/coords_f110.md`).
GULF = dict(
    nombre='gulf',
    bbox=(-97.5, -89.5, 24.5, 33.5),          # h/w = 1,30: mas alto que ancho
    w=2600,
    # Verificadas una a una contra su pagina de Wikipedia el 2026-09-15 (infobox). Las que traia
    # PLAN_VISUAL_V4.md estaban cerca pero no eran las del infobox: Lake Charles se iba 0,029 deg
    # de latitud = 3,2 km = 9 px a la escala de este mundo. Se usan las verificadas.
    sitios={'Freeport': (-95.35694, 28.95944),      # Bryan Mound    · 184 M bbl
            'Winnie': (-94.38333, 29.81889),        # Big Hill       ·  90 M
            'Lake Charles': (-93.23667, 30.19722),  # West Hackberry ·  88 M
            'Baton Rouge': (-91.17861, 30.44750),   # Bayou Choctaw  ·  51 M
            'Houston': (-95.36980, 29.76040),
            'New Orleans': (-90.07150, 29.95110)},
    agua=[],                                   # ver la decision 1 de la cabecera
    # Posiciones calculadas contra la VENTANA a zmin (x = 358..2242 px de mundo), no a ojo.
    # MEXICO se cae: su unico hueco de tierra queda en x=293, fuera de la franja que recorre la
    # camara, y la voz no lo nombra ni una vez.
    rotulos_extra=[('TEXAS', -95.95, 31.30, 84), ('LOUISIANA', -92.30, 31.40, 78)],
    # `sujeto` es CELESTE (72,178,190) y el oceano es TEAL (70,142,152): pintar EE. UU. de
    # `sujeto` sobre este mapa hacia que la tierra y el mar fueran el mismo color — se ve en la
    # primera hoja de contacto de la pieza 1, donde el cuadro entero es teal y los cuatro domos
    # flotan sin costa. Ademas mataba el movimiento medido (sin contraste no hay diferencia de
    # pixeles que medir). Va `institucion` (azul), que ademas es lo correcto: el sujeto de la pieza
    # es LA RESERVA, un organismo del Estado (ESTADO.md §3), no «el pais del que habla el video».
    capas={'usa': (['USA'], MV.ROL['institucion'], 205)},
    pins={'Freeport': {'color': MV.ROJO, 'r': 11, 'size': 40, 'anc': 'rm', 'off': (-2.4, 0.2)},
          'Winnie': {'color': MV.ROJO, 'r': 11, 'size': 40, 'anc': 'rm', 'off': (-2.4, 1.5)},
          'Lake Charles': {'color': MV.ROJO, 'r': 11, 'size': 40, 'off': (2.4, 1.6)},
          # 'rm' = la etiqueta va a la IZQUIERDA del punto: a la derecha se salia del cuadro
          'Baton Rouge': {'color': MV.ROJO, 'r': 11, 'size': 40, 'anc': 'rm', 'off': (-2.4, 0.2)},
          'Houston': {'color': GRIS, 'r': 8, 'size': 32, 'anc': 'rm', 'off': (-2.6, -1.2)},
          'New Orleans': {'color': GRIS, 'r': 8, 'size': 32, 'off': (2.6, -1.0)}},
)

# ================================================================= 2 · HORMUZ (Golfo Persico)
HORMUZ = dict(
    nombre='hormuz',
    bbox=(47.0, 60.0, 19.5, 33.5),            # h/w = 1,19. Kuwait City obliga a llegar a lon 47
    w=2600,
    # Hormuz, verificado contra el infobox de Wikipedia el 2026-09-15: 26,6 N 56,5 E (el plan
    # traia 26,57/56,25, que cae 25 km al oeste). El estrecho es ancho y las dos caen dentro,
    # pero se usa la citable.
    sitios={'Hormuz': (56.5000, 26.6000), 'Bandar Abbas': (56.2667, 27.1833),
            'Fujairah': (56.3265, 25.1288), 'Ras Tanura': (50.1580, 26.6927),
            'Kuwait City': (47.9774, 29.3759), 'Doha': (51.5310, 25.2854),
            'Muscat': (58.3829, 23.5880)},
    # Ventana a zmin: x = 417..2183. ARABIAN SEA caia en x=2320 y no lo nombra el guion: fuera.
    agua=[('THE GULF', 50.30, 28.60, 64), ('GULF OF OMAN', 57.00, 24.60, 50)],
    rotulos_extra=[('IRAN', 53.60, 30.60, 84), ('SAUDI ARABIA', 50.60, 23.60, 72),
                   ('OMAN', 56.90, 21.80, 76), ('U.A.E.', 54.40, 24.00, 60)],
    capas={'iran': (['IRN'], MV.ROL['deudor'], 205),
           'golfo': (['OMN', 'ARE'], MV.ROL['tercero'], 190)},
    pins={'Hormuz': {'color': MV.ROJO, 'r': 13, 'size': 44, 'texto': 'STRAIT OF HORMUZ',
                     'anc': 'rm', 'off': (-2.4, -1.4)},
          'Bandar Abbas': {'color': MV.OCRE, 'r': 9, 'size': 34, 'off': (2.5, -0.9)},
          'Fujairah': {'color': GRIS, 'r': 8, 'size': 32, 'off': (2.5, 1.2)},
          'Ras Tanura': {'color': MV.OCRE, 'r': 9, 'size': 34, 'off': (2.5, 0.2)},
          'Kuwait City': {'color': GRIS, 'r': 8, 'size': 32, 'anc': 'rm', 'off': (-2.5, 0)},
          'Doha': {'color': GRIS, 'r': 8, 'size': 32, 'anc': 'rm', 'off': (-2.5, 1.0)},
          'Muscat': {'color': GRIS, 'r': 8, 'size': 32, 'off': (2.5, 0.6)}},
)

# ================================================================= 3 · LOS HOTELES (Islas Britanicas)
UK = dict(
    nombre='uk',
    bbox=(-10.0, 2.5, 49.5, 59.0),            # h/w = 1,30
    w=2600,
    sitios={'London': (-0.1278, 51.5074), 'Manchester': (-2.2426, 53.4808),
            'Birmingham': (-1.8904, 52.4862), 'Glasgow': (-4.2518, 55.8642)},
    # Ventana a zmin: x = 344..2256.
    agua=[('NORTH SEA', 0.20, 56.50, 52), ('IRISH SEA', -5.10, 53.60, 52),
          ('THE CHANNEL', -2.40, 50.00, 52)],
    rotulos_extra=[('BRITAIN', -2.60, 54.60, 84), ('IRELAND', -7.40, 53.30, 68)],
    capas={'gbr': (['GBR'], MV.ROL['institucion'], 205),
           'irl': (['IRL'], MV.ROL['tercero'], 175)},
    pins={'London': {'color': MV.ROJO, 'r': 13, 'size': 44, 'anc': 'rm', 'off': (-2.4, 1.0)},
          'Manchester': {'color': MV.OCRE, 'r': 9, 'size': 34, 'anc': 'rm', 'off': (-2.5, -0.4)},
          'Birmingham': {'color': MV.OCRE, 'r': 9, 'size': 34, 'anc': 'rm', 'off': (-2.5, 0.8)},
          'Glasgow': {'color': MV.OCRE, 'r': 9, 'size': 34, 'anc': 'rm', 'off': (-2.5, 0)}},
)

# ================================================================= 4 · CEUTA (Estrecho, VERTICAL)
# El mundo de `prueba_v4.py` era 16:9 (bbox -6,447..-4,253). Este es el mismo sitio rehecho
# VERTICAL, que es lo que pide `PLAN_VISUAL_V4.md` §4.
ESTRECHO = dict(
    nombre='estrecho_v',
    bbox=(-5.95, -4.85, 35.40, 36.45),        # h/w = 1,21
    w=2600,
    sitios={'Ceuta': (-5.3213, 35.8894), 'Fnideq': (-5.3567, 35.8500),
            'Tarifa': (-5.6045, 36.0128), 'Algeciras': (-5.4500, 36.1275),
            'Gibraltar': (-5.3536, 36.1408), 'Tangier': (-5.8340, 35.7595),
            'Tetouan': (-5.3684, 35.5785)},
    # Ventana a zmin: x = 438..2162. ATLANTIC OCEAN caia en x=213 y la voz dice «open water at
    # both ends», nunca «Atlantic»: fuera.
    agua=[('STRAIT OF GIBRALTAR', -5.63, 36.02, 54),
          ('MEDITERRANEAN SEA', -5.16, 35.86, 58)],
    rotulos_extra=[('SPAIN', -5.55, 36.30, 84), ('MOROCCO', -5.52, 35.52, 84)],
    capas={'esp': (['ESP'], MV.ROL['institucion'], 210),
           'mar': (['MAR'], MV.ROL['acreedor'], 205)},
    # LA CORRECCION DE LA AUDITORIA. Natural Earth 50m mete la peninsula de Ceuta dentro del
    # poligono de Marruecos: al encender la capa `mar`, Ceuta quedaba OCRE y el mapa afirmaba justo
    # lo contrario que la voz («Ceuta is Spain»). En la prueba v4 se tapaba volviendo a poner las
    # marcas encima, pero eso solo devuelve el PUNTO rojo: la tierra seguia siendo de Marruecos.
    # Aca la peninsula se pinta del color de Espana, desde NE **10m** `admin_0_map_subunits`, y la
    # coreografia la enciende DESPUES de `mar` para que gane. Si el geojson no estuviera, la
    # coreografia no pinta Marruecos (ver `coreo4.py::_pintar_pieza4`).
    capas_geojson={'ceuta': (GEO_ENCLAVES, ['Ceuta', 'Melilla'], MV.ROL['institucion'], 210)},
    pins={'Ceuta': {'color': MV.ROJO, 'r': 14, 'size': 46, 'texto': 'CEUTA', 'off': (2.0, -0.3)},
          'Fnideq': {'color': MV.OCRE, 'r': 9, 'size': 34, 'anc': 'rm', 'off': (-2.5, 1.4)},
          'Algeciras': {'color': GRIS, 'r': 8, 'size': 32, 'anc': 'rm', 'off': (-2.6, -0.6)},
          'Gibraltar': {'color': GRIS, 'r': 8, 'size': 32, 'off': (2.6, 0.9)},
          'Tangier': {'color': GRIS, 'r': 8, 'size': 32, 'anc': 'rm', 'off': (-2.6, 0)},
          'Tarifa': {'color': GRIS, 'r': 8, 'size': 32, 'anc': 'rm', 'off': (-2.6, 0)},
          'Tetouan': {'color': GRIS, 'r': 8, 'size': 32, 'off': (2.6, 0)}},
)

SPEC = {1: GULF, 2: HORMUZ, 3: UK, 4: ESTRECHO}


def mundo(n, force=False):
    """El mundo de la pieza `n`. Se cachea en disco: `build()` corre en CADA worker del pool."""
    s = SPEC[n]
    return MV.mundo(s['nombre'], s['bbox'], s['w'],
                    roles=None,                      # la tierra, neutra: el color entra por capas
                    # etiquetas=False: `hoja_v2` rotula cada pais con el LABEL_X/Y de Natural Earth
                    # ADEMAS de lo que pida `rotulos_extra`, y salian los dos — «Iran» en cursiva
                    # encima de «IRAN», «Britain» encima de «BRITAIN». Se ve en los primeros
                    # `_qc/v4_mundo_*.png`. Los rotulos los pone esta tabla, que es la que esta
                    # medida contra la ventana.
                    etiquetas=False,
                    sitios=s['sitios'], agua=s['agua'], rotulos_extra=s['rotulos_extra'],
                    capas=s['capas'], capas_geojson=s.get('capas_geojson'),
                    pins_opciones=s['pins'], marcas=True, out_dir=ARTE, force=force)


def relacion(n):
    """h/w del mundo, para comprobar de un vistazo que el bbox es mas alto que ancho."""
    s = SPEC[n]; lon0, lon1, lat0, lat1 = s['bbox']
    m = lambda l: math.log(math.tan(math.pi / 4 + math.radians(l) / 2))
    return (m(lat1) - m(lat0)) / math.radians(lon1 - lon0)


if __name__ == '__main__':
    import motor as M
    from PIL import Image
    os.makedirs(QC, exist_ok=True)
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    force = '--force' in sys.argv
    for n in ([int(args[0])] if args else [1, 2, 3, 4]):
        print('\n=========== pieza %d · %s  (h/w = %.2f)' % (n, SPEC[n]['nombre'], relacion(n)))
        mu = mundo(n, force=force)
        zmin = max(1080 / mu.w, 1920 / mu.h)
        print('  mundo %dx%d   zmin=%.3f  ->  a zmin se ven %d x %d px de mundo'
              % (mu.w, mu.h, zmin, 1080 / zmin, 1920 / zmin))
        # cuadro fijo de QC a 1080x1920: primero se MIRA, despues se coreografia
        sc = M.Scene(mu, size=(1080, 1920), v4=True)
        sc.vida = None
        sc.corte(0.0, (mu.w / 2, mu.h / 2), zmin, tick=False)
        f = os.path.join(QC, 'v4_mundo_%d.png' % n)
        sc.render(0.0).convert('RGB').save(f)
        print('  QC ->', f)
