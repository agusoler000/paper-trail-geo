# -*- coding: utf-8 -*-
"""PRUEBA DE ACEPTACION DEL MOTOR v4 — los mismos 25 s de Ceuta de `prueba_vida.py`, pero escritos
NATIVAMENTE sobre el motor nuevo. Es la comparacion honesta: mismo guion, mismos tiempos
sinteticos, misma alternancia MAPA/MESA, mismo jurista.

    python prueba_v4.py cuadro     # cuatro cuadros fijos (regla de Agustin: primero el cuadro)
    python prueba_v4.py hoja       # hoja de contacto de 12 + la vista a 405 px (telefono)
    python prueba_v4.py check      # check_framing + sync.py (VACIO tiene que ser 0)
    python prueba_v4.py render     # los 25 s -> salida/_prueba_v4.mp4   (0 creditos)
    python prueba_v4.py medir      # ritmo.py --json sobre el resultado

QUE CAMBIA RESPECTO DE LA v3, y por que se ve distinto:

  1. **Vertical NATIVO 1080x1920.** El cuerpo ya es la pantalla del telefono. La pieza vieja
     renderizaba 1920x1080 y despues `armar.py` lo metia en un bloque de 1000x563 dentro de una
     hoja de papel: el video ocupaba el 27 % del area de la pantalla.
  2. **El mapa es el MUNDO, no una hoja.** 4000x2251 px de Estrecho generados por
     `mapa_v2.mundo()`. La camara vive dentro y a zoom 1,8 se ve a 1:1. La v3 tenia que meter la
     hoja de 3000 px en un lienzo de 1920 (perdia la mitad de la resolucion) porque `Scene.window`
     no dejaba salir del cuadro.
  3. **Subtitulos y cifras en el HUD.** La v3 los emulaba con un keyframe cada 0,1 s contra la
     ventana de camara y **los partia en cada corte** para que `check_framing` no los marcara. Aca
     viven en px de cuadro: cruzan los cortes enteros y no se achican con el zoom.
  4. **El color narra.** Espana se pinta cuando la voz dice «a Spanish court», Marruecos en «on
     the African mainland». Son capas del mundo (`add_layer`), compuestas SOLO en el recorte.
  5. **El jurista esta de pie SOBRE EL MAPA**, en tierra espanola, con peana y sombra de contacto
     (`mapa_v2.componer`), y senala Ceuta. En la v3 estaba sobre la mesa porque un rig sobre el mar
     no se sostenia: con el mundo grande hay tierra donde pararlo.
  6. **La camara tiene vida propia** (`Scene.vida`): dentro de cada plano hay un push lento y una
     deriva que alterna de sentido. La v3 lo escribia a mano plano por plano.

LOS PLANOS DE MESA. El documento va como **hoja del HUD** sobre el mundo oscurecido (`Mundo.dark`),
no como objeto del mundo ni como segundo fondo. Se probaron las tres:
  · objeto del mundo: la camara sigue viva durante el plano de mesa, asi que la hoja se desplazaba
    bajo los carteles y se veia el borde entrando y saliendo;
  · segundo fondo: obliga a dos escenas y a cortar el video en dos, y pierde la continuidad;
  · HOJA DE HUD (la elegida): queda clavada al cuadro, deja 4 % de margen por el que se ve el mapa
    oscurecido —que da profundidad y recuerda donde estamos— y los carteles, que ya son HUD, caen
    encima sin cuentas de camara.

**Los tiempos son sinteticos**, como en la v3: las 45 palabras del guion real repartidas a 1,88
palabras por segundo, la cadencia medida de George. Se escriben ademas como un `tiempos.json` de
verdad en `salida/_tiempos_prueba.json` para que `sync.py` audite contra el.
"""
import json, math, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
PROD = os.path.join(RAIZ, 'produccion')
sys.path.insert(0, PROD); sys.path.insert(0, AQUI)
import motor as M
import props as PR
import mapa_v2 as MV
from PIL import Image, ImageDraw, ImageFilter

ARTE = os.path.join(AQUI, 'arte', 'assets')
OUT = os.path.join(AQUI, 'shorts', '04_ceuta', 'salida'); os.makedirs(OUT, exist_ok=True)
QC = OUT
W, H = 1080, 1920                       # vertical NATIVO
DUR = 25.0
NL = chr(10)

# ---------------------------------------------------------------- el mundo
# bbox 16:9, el mismo de `arte/mapa.py` (ahi esta explicado por que no es el de la valla: a la
# escala de los 8 km de valla, Natural Earth 50m no llega y marcarla seria inventar costa).
BBOX = (-6.447, -4.253, 35.40, 36.40)
MUNDO_W = 4000
SITIOS = {'Ceuta': (-5.3213, 35.8894), 'Fnideq': (-5.3567, 35.8500),
          'Tarifa': (-5.6045, 36.0128), 'Algeciras': (-5.4500, 36.1275),
          'Gibraltar': (-5.3536, 36.1408), 'Tangier': (-5.8340, 35.7595),
          'Tetouan': (-5.3684, 35.5785)}
# El rojo es de Ceuta y de nadie mas (regla del canal: un rojo por plano).
#
# EL TAMANO DE LOS ROTULOS SE MIDE CONTRA LA VENTANA, NO CONTRA EL MUNDO. El mundo tiene 4000 px
# de ancho, pero un cuadro vertical a zoom minimo ve 1080/0,853 = 1266 px: un rotulo de 66 px de
# mundo ocupa la mitad del ancho de pantalla y se sale por el borde. La primera pasada tenia
# «CEUTA · SPAIN» a 66 y en los planos cerrados salia cortado. A 36 ocupa ~20 % del ancho y se lee
# a 405 px. Y el rotulo dice solo CEUTA: que Ceuta es Espana lo dice el color, el cartel y la voz.
PIN = {'Ceuta': {'color': PR.ROJO, 'r': 13, 'size': 38, 'texto': 'CEUTA', 'off': (1.8, -0.25)},
       'Fnideq': {'color': MV.OCRE, 'r': 8, 'size': 25, 'anc': 'rm', 'off': (-2.4, 1.5)},
       'Algeciras': {'color': (108, 102, 92), 'r': 7, 'size': 24, 'anc': 'rm', 'off': (-2.6, -0.6)},
       'Gibraltar': {'color': (108, 102, 92), 'r': 7, 'size': 24, 'off': (2.6, 0.9)},
       'Tangier': {'color': (108, 102, 92), 'r': 7, 'size': 24, 'anc': 'rm', 'off': (-2.6, 0)},
       'Tarifa': {'color': (108, 102, 92), 'r': 7, 'size': 24, 'anc': 'rm', 'off': (-2.6, 0)},
       'Tetouan': {'color': (108, 102, 92), 'r': 7, 'size': 24, 'off': (2.6, 0)}}


def mundo():
    """El suelo del video. Se genera una vez y se reusa: `build()` corre en cada worker del pool.

    La tierra sale NEUTRA (kaki) a proposito: los roles no van horneados en la hoja, van como capas
    que se encienden cuando la voz nombra el pais. El color es lo que narra; si ya esta puesto desde
    el cuadro 0 no cuenta nada."""
    return MV.mundo('estrecho', BBOX, MUNDO_W,
                    roles=None,                       # la tierra, neutra: el color entra por capas
                    sitios=SITIOS,
                    # Los rotulos van donde la CAMARA pasa. El mundo es 16:9 y el cuadro vertical
                    # solo recorre una franja de unos 1.300 px de ancho: un rotulo a lon -4,70
                    # (x = 3184) no se ve nunca. Comprobado sitio por sitio contra Natural Earth:
                    # los de agua caen en agua y los de tierra en su pais.
                    agua=[('STRAIT OF GIBRALTAR', -5.68, 35.985, 30),
                          ('MEDITERRANEAN SEA', -5.16, 35.72, 30),
                          ('ATLANTIC OCEAN', -5.82, 35.90, 28)],
                    rotulos_extra=[('SPAIN', -5.62, 36.19, 46), ('MOROCCO', -5.55, 35.58, 46)],
                    capas={'esp': (['ESP'], MV.ROL['institucion'], 210),
                           'mar': (['MAR'], MV.ROL['tercero'], 205)},
                    pins_opciones=PIN, marcas=True, out_dir=ARTE)


# ---------------------------------------------------------------- guion y tiempos sinteticos
LINEAS = [
    'On the twenty-nine of June, a Spanish court published a ruling. '
    'Thirty-two days later, forty-nine thousand people crossed into Ceuta in twenty-four hours.',
    'Ceuta is Spain, on the African mainland. A European border with a land fence, '
    'and open water at both ends of it.',
]
PAL_POR_S = 1.88                         # cadencia medida de George en el canal
T_INI = 0.45
RESALTAR = ['twenty-nine', 'June,', 'Thirty-two', 'forty-nine', 'thousand', 'twenty-four',
            'Ceuta', 'Ceuta.', 'Spain,', 'fence,', 'water']


def palabras_y_tiempos():
    """[(palabra, t0, t1)] y un tiempos.json de verdad, para que `sync.py` audite contra el."""
    pal, lin, t = [], [], T_INI
    for i, L in enumerate(LINEAS):
        t0 = t
        for w in L.split():
            pal.append((w, round(t, 3), round(t + 1.0 / PAL_POR_S - 0.02, 3)))
            t += 1.0 / PAL_POR_S
        lin.append({'i': i, 'b': 0, 'texto': L, 'inicio': round(t0, 3), 'fin': round(t - 0.08, 3)})
    T = {'lineas': lin, 'dur': DUR, 'pre': T_INI, 'post': 0.4}
    json.dump(T, open(os.path.join(OUT, '_tiempos_prueba.json'), 'w', encoding='utf-8'), indent=1)
    json.dump(pal, open(os.path.join(OUT, '_palabras_prueba.json'), 'w', encoding='utf-8'))
    return pal, T


def T_PAL(n, pal):
    """Cuando empieza la palabra numero `n` (0-based). Sirve para atar las capas a la voz."""
    return pal[min(n, len(pal) - 1)][1]


# ---------------------------------------------------------------- piezas de HUD
def imagen(name):
    for base in (ARTE, os.path.join(PROD, 'assets')):
        p = os.path.join(base, 'prop_%s.png' % name)
        if os.path.exists(p): return Image.open(p).convert('RGBA')
    raise SystemExit('falta el prop: %s' % name)


def hoja_mesa(margen=0.035):
    """La hoja de trabajo que convierte el plano en un plano de MESA. Va en el HUD."""
    w, h = int(W * (1 - 2 * margen)), int(H * (1 - 2 * margen))
    p = PR.papel((w, h), lambda d: d.rounded_rectangle([1, 1, w - 2, h - 2], radius=18, fill=255),
                 PR.PAPEL, sombra=False)
    d = ImageDraw.Draw(p)
    d.rounded_rectangle([14, 14, w - 15, h - 15], radius=12, outline=PR.TINTA + (90,), width=3)
    for y in range(int(h * 0.12), int(h * 0.88), 78):       # renglones: es una hoja, no un rectangulo
        d.line([(int(w * 0.10), y), (int(w * 0.90 - (y % 3) * 40), y)], fill=(176, 168, 148, 120), width=4)
    sh = Image.new('RGBA', (w + 60, h + 60), (0, 0, 0, 0))
    s = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    s.putalpha(p.split()[3].point(lambda v: min(v, 150)).filter(ImageFilter.GaussianBlur(14)))
    sh.alpha_composite(s, (30, 38)); sh.alpha_composite(p, (24, 24))
    return sh


class Prueba:
    """Envuelve la escena para no repetir las cuentas de HUD en cada cartel."""

    def __init__(self, sc):
        self.sc = sc

    def hud(self, im, t0, t1, fx, fy, alto_rel, z=60, entra=0.30, sale=0.26, sfx='pop',
            nombre=None, bg=False, margen=18):
        """Un objeto de PANTALLA: se escala a `alto_rel` del alto del cuadro y se coloca por
        fraccion, sujetandolo dentro del cuadro (regla 1: nada cortado)."""
        k = (H * alto_rel) / im.height
        if im.width * k > W - 2 * margen: k = (W - 2 * margen) / im.width
        w2, h2 = im.width * k / 2, im.height * k / 2
        o = M.Obj(im, z=z)
        o.name = nombre or 'card:hud'
        o.bg = bg; o.wobble = 0.0; o.bob = 0.0; o.vida = 0.0; o.shadow = False
        o.sc = M.Track(k)
        o.x = M.Track(min(max(W * fx, w2 + margen), W - w2 - margen))
        o.y = M.Track(min(max(H * fy, h2 + margen), H - h2 - margen))
        o.on, o.off = t0, t1
        o.a.set(t0, 0, 'hold'); o.a.set(t0 + entra, 1, 'io')
        o.a.set(max(t0 + entra, t1 - sale), 1, 'hold'); o.a.set(t1, 0, 'io')
        if sfx: M.ev(t0, sfx, 0.5)
        self.sc.add_hud(o)
        return o

    def card(self, txt, t0, t1, fx, fy, alto_rel, size=64, color=None, tcolor=None, **kw):
        im = PR.card(txt, size=size, color=color or PR.PAPEL, tcolor=tcolor or PR.TINTA)
        return self.hud(im, t0, t1, fx, fy, alto_rel, nombre='card:' + txt.replace(NL, ' '), **kw)


# ---------------------------------------------------------------- la coreografia
def build():
    M.EVENTS.clear()
    mu = mundo()
    sc = M.Scene(mu, size=(W, H), v4=True)
    P = mu.P
    pal, T = palabras_y_tiempos()
    p = Prueba(sc)

    CE = P('Ceuta'); TA = P('Tarifa'); AL = P('Algeciras'); TG = P('Tangier'); FN = P('Fnideq')
    ZMIN = max(W / mu.w, H / mu.h)

    # ---- el color narra: cada pais se pinta cuando la voz lo nombra
    T_SPANISH = T_PAL(6, pal)            # «a Spanish court»
    T_AFRICAN = T_PAL(28, pal)           # «on the African mainland»
    mu.add_layer(mu.meta['capas']['esp'], T_SPANISH, 1.5, mode='fade')
    mu.add_layer(mu.meta['capas']['mar'], T_AFRICAN, 1.7, mode='fade')
    # las marcas vuelven POR ENCIMA del color: Natural Earth 50m no separa el enclave y al pintar
    # Marruecos la peninsula de Ceuta quedaria de su color — el mapa diria lo contrario del guion.
    mu.add_layer(mu.meta['capas']['marcas'], T_SPANISH, 0.3, mode='fade')

    # ---- planos. Un plano = corte + UN viaje motivado; la vida del motor hace el resto.
    MESA = [(0.00, 2.55), (8.55, 9.60), (17.70, 21.45)]
    # CUANTO TIENE QUE VIAJAR LA CAMARA. La primera pasada movia el zoom un 9-15 % por plano y
    # `ritmo.py` dio movimiento mediano 2,65: pasa el umbral de §6.6 (2,5) pero se queda lejos de la
    # referencia (9,2 de media). No es que haga falta «mas numero»: es que un recorrido de 10 % en
    # cuatro segundos no se lee como un viaje, se lee como una foto que respira. Duplicado a un
    # 25-35 % por plano —y con paneo lateral, no solo zoom— el recorrido se ve, y el numero sube
    # solo. Cada movimiento sigue yendo HACIA lo que dice la voz; ninguno es relleno.
    PLANOS = [
        # (t0, t1, centro0, z0, centro1, z1)
        (0.00, 2.55, (CE[0] - 60, CE[1] + 20), 1.26, (CE[0] + 20, CE[1] - 40), 1.60),   # MESA · la sentencia
        (2.55, 6.15, ((TG[0] + AL[0]) / 2 - 70, (TG[1] + AL[1]) / 2 + 60), ZMIN + 0.03,
         ((TG[0] + AL[0]) / 2 + 150, (TG[1] + AL[1]) / 2 - 70), ZMIN + 0.36),           # MAPA · el Estrecho
        (6.15, 8.55, ((CE[0] + TA[0]) / 2 - 60, (CE[1] + TA[1]) / 2 + 70), 1.00,
         (CE[0] + 30, CE[1] + 30), 1.46),                                               # MAPA · viaja a Ceuta
        (8.55, 9.60, (CE[0] - 18, CE[1] + 16), 1.50, (CE[0] + 24, CE[1] - 12), 1.82),   # MESA · 49.000
        (9.60, 12.90, (CE[0] + 120, CE[1] + 90), 1.72, (CE[0] - 20, CE[1] - 20), 2.38), # MAPA · Ceuta
        # El encuadre de este plano NO se elige a ojo: tiene que caber la tierra espanola donde se
        # para el jurista (x ~1570, y ~735) Y Ceuta (2052, 1153), que es a donde senala. Con el
        # centro entre Ceuta y Tarifa, la costa espanola caia justo en el borde y el ajuste
        # automatico empujaba al rig 632 px: quedaba de pie sobre el mar.
        (12.90, 17.70, (1770, 1030), 0.97, (1900, 930), 1.30),                          # MAPA · el jurista
        (17.70, 21.45, (CE[0] + 30, CE[1] + 80), 1.34, (CE[0] - 50, CE[1] + 20), 1.68), # MESA · la valla
        (21.45, DUR, (CE[0] + 90, CE[1] + 60), 1.88, (CE[0] - 30, CE[1] - 30), 2.58),   # MAPA · el istmo
    ]
    for t0, t1, xy0, z0, xy1, z1 in PLANOS:
        sc.corte(t0, xy0, z0)
        sc.viaje(t0, t1, xy1, z1, 'io')

    # ---- el mundo se oscurece en los planos de mesa (y vuelve en los de mapa)
    mu.dark.set(0.0, 0.62, 'hold')
    for a, b in MESA:
        if a > 0: mu.dark.set(a - 0.12, 0.0, 'hold'); mu.dark.set(a, 0.62, 'io')
        mu.dark.set(b - 0.10, 0.62, 'hold'); mu.dark.set(b, 0.0, 'io')

    # ---- la hoja de mesa (HUD, bg: no cuenta como contenido ni se verifica encuadre)
    hoja = hoja_mesa()
    for a, b in MESA:
        p.hud(hoja, a, b, 0.5, 0.5, 1.0, z=5, entra=0.14, sale=0.12, sfx=None,
              nombre='mesa', bg=True, margen=0)

    # LOS CARTELES CRUZAN LOS CORTES A PROPOSITO. `sync.py` midio 3,4 s de los 25 sin ningun objeto
    # que contara: medio segundo en cada juntura, porque el cartel saliente se apagaba antes del
    # corte y el entrante empezaba despues. Sobre un mapa vivo eso no se ve «vacio», pero el
    # detector tiene razon en marcarlo: la regla del canal es que cada frase tenga SU imagen, y
    # medio segundo de mapa mudo por corte son 8 segundos en una pieza de 90. Con el HUD se arregla
    # solapando los tiempos, que es justo lo que el motor v3 no dejaba hacer: sus carteles vivian
    # en coordenadas del mundo y el post-pass los APAGABA en cada corte para que no se cortaran.
    # ================================================================ MESA 1 · el documento
    p.hud(imagen('sentencia'), 0.00, 2.52, 0.50, 0.415, 0.42, z=52, entra=0.35)
    p.card('A SPANISH COURT', 1.05, 2.50, 0.50, 0.700, 0.052, size=62, z=54)
    p.card('29 · VI · 2026', 1.55, 2.50, 0.50, 0.790, 0.062, size=76,
           tcolor=PR.ROJO, z=54, sfx='stamp')

    # ================================================================ MAPA 1 · donde pasa
    p.card('THE STRAIT' + NL + 'OF GIBRALTAR', 2.56, 6.12, 0.50, 0.130, 0.075, size=60, z=54)
    p.card('32 DAYS LATER', 6.02, 8.58, 0.50, 0.150, 0.068, size=74, z=54)

    # ================================================================ MESA 2 · la cifra, sola
    p.card('49,000', 8.56, 9.58, 0.50, 0.415, 0.150, size=190, tcolor=PR.ROJO, z=56,
           entra=0.20, sale=0.14, sfx='stamp')
    p.card('IN 24 HOURS', 9.00, 9.58, 0.50, 0.560, 0.048, size=62, z=56, entra=0.16, sale=0.12)

    # ================================================================ MAPA 2 · Ceuta de cerca
    p.card('49,000 CROSSED', 9.62, 12.96, 0.50, 0.135, 0.062, size=68, tcolor=PR.ROJO, z=56,
           entra=0.22)

    # ================================================================ MAPA 3 · el jurista sobre el mapa
    jur = _jurista(sc, mu, 12.95, 17.60, sobre=(-5.585, 36.075), mira=CE, alto_rel=0.24)

    # Estos dos van ABAJO y no arriba: el jurista esta de pie en la mitad superior del cuadro
    # (la costa espanola queda ahi con este encuadre) y un cartel a fy 0,15 le caia en la cabeza.
    p.card('CEUTA IS SPAIN', 12.94, 15.30, 0.50, 0.715, 0.055, size=70, z=56, entra=0.22)
    p.card('ON THE AFRICAN' + NL + 'MAINLAND', 15.45, 17.72, 0.50, 0.720, 0.078, size=62,
           tcolor=PR.ROJO, z=56)

    # ================================================================ MESA 3 · la valla
    p.card('A EUROPEAN BORDER', 17.58, 21.42, 0.50, 0.185, 0.055, size=66, z=54, entra=0.24)
    p.hud(imagen('cerca'), 18.30, 21.35, 0.50, 0.430, 0.075, z=44, entra=0.42)
    p.hud(imagen('gota'), 19.25, 21.35, 0.185, 0.430, 0.052, z=46)
    p.hud(imagen('gota'), 19.50, 21.35, 0.815, 0.430, 0.052, z=46)
    p.card('WATER', 19.90, 21.35, 0.185, 0.540, 0.038, size=52, tcolor=PR.ROJO, z=54)
    p.card('WATER', 20.10, 21.35, 0.815, 0.540, 0.038, size=52, tcolor=PR.ROJO, z=54)

    # ================================================================ MAPA 4 · el cierre
    p.card('8 KM OF FENCE' + NL + 'WATER AT BOTH ENDS', 21.40, DUR, 0.50, 0.145, 0.090,
           size=58, tcolor=PR.ROJO, z=56, sfx='stamp', entra=0.26, sale=0.30)

    # ---- subtitulos: HUD, banda, grupos de 2-4 palabras con los tiempos reales
    sc.subtitulos(pal, estilo='banda', fy=0.885, resaltar=RESALTAR, ancho=0.88,
                  size=int(W * 0.062))

    # ---- el ritmo se marca tambien como eventos (mezcla + Scene.report)
    for t0, _, _, _, _, _ in PLANOS: M.ev(t0, 'tick', 0.3)
    sc.dur = DUR
    return sc


def _jurista(sc, mu, t0, t1, sobre, mira, alto_rel=0.30):
    """El jurista, DE PIE SOBRE EL MAPA, con peana y sombra de contacto.

    `sobre` es (lon, lat): donde apoya los pies, en tierra espanola. La escala sale del alto que
    tiene que ocupar EN PANTALLA en el plano donde aparece; el resto (donde cae el pixel 0,0 del
    recorte) lo resuelve el rig.json, como en `mapa_v2.componer`. Sin la peana y la sombra, el
    recorte flota sobre el mapa y se lee como una calcomania pegada."""
    import json as _json
    pj, _, _ = MV.proyeccion(*BBOX, mu.w)
    px, py = pj(*sobre)
    rj = _json.load(open(os.path.join(M.ELENCO, 'rig', '05_jurista', 'rig.json'), encoding='utf-8'))
    tor = rj['piezas']['torso']
    z_medio = (sc.zoom(t0) + sc.zoom(t1)) / 2
    alto_pieza = max(b[3] for b in rj['piezas'].values()) - min(b[1] for b in rj['piezas'].values())
    esc = (H * alto_rel / z_medio) / alto_pieza          # px de MUNDO: en pantalla se multiplica por z

    ancho = int((tor[2] - tor[0]) * esc * 1.20)
    sh = Image.new('RGBA', (ancho + 90, 96), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([45, 30, ancho + 45, 72], fill=(20, 16, 12, 104))
    sh = sh.filter(ImageFilter.GaussianBlur(9))
    so = M.Obj(sh, z=40); so.name = 'sombra_jur'; so.bg = True; so.shadow = False
    so.x = M.Track(px); so.y = M.Track(py - 6); so.on, so.off = t0, t1
    so.a.set(t0, 0, 'hold'); so.a.set(t0 + 0.40, 1, 'io')
    so.a.set(t1 - 0.35, 1, 'hold'); so.a.set(t1, 0, 'io')
    sc.add(so)
    pe = PR.rect(max(24, int(ancho * 0.60)), 16, MV.PAPEL, r=4)
    po = M.Obj(pe, z=41); po.name = 'peana_jur'; po.bg = True; po.shadow = False
    po.x = M.Track(px); po.y = M.Track(py - 2); po.on, po.off = t0, t1
    po.a = so.a
    sc.add(po)

    r = M.Rig('05_jurista', 0, 0, sc=esc, z=44, on=t0, off=t1)
    r.x = M.Track(px - (tor[0] + tor[2]) / 2 * esc)
    r.y = M.Track(py - tor[3] * esc)
    r.name = '05_jurista'
    r.point_at(t0 + 1.1, mira, side='R', hold=2.4)
    r.nod(t0 + 0.6)
    r.a.set(t0, 0, 'hold'); r.a.set(t0 + 0.45, 1, 'io')
    r.a.set(t1 - 0.40, 1, 'hold'); r.a.set(t1, 0, 'io')
    sc.add(r)
    # y ahora se COMPRUEBA que entra en la ventana durante todo el plano, y se corre lo justo si no
    # (regla 1). A ojo no se puede: el rig se ancla por la esquina superior izquierda y su caja
    # depende de la pose.
    peor = (0.0, 0.0); MG = 24
    t = t0 + 0.5
    while t < t1 - 0.2:
        b = r.bbox(t)
        if b is not None:
            vx0, vy0, vx1, vy1 = sc.window(t)
            dx = max(0.0, vx0 + MG - b[0]) - max(0.0, b[2] - (vx1 - MG))
            dy = max(0.0, vy0 + MG - b[1]) - max(0.0, b[3] - (vy1 - MG))
            if abs(dx) + abs(dy) > abs(peor[0]) + abs(peor[1]): peor = (dx, dy)
        t += 0.15
    if abs(peor[0]) + abs(peor[1]) > 0.5:
        r.x = M.Track(r.x(t0) + peor[0]); r.y = M.Track(r.y(t0) + peor[1])
        so.x = M.Track(px + peor[0]); so.y = M.Track(py - 6 + peor[1])
        po.x = M.Track(px + peor[0]); po.y = M.Track(py - 2 + peor[1])
        print('   jurista corrido %.0f,%.0f px de mundo para que entre entero' % peor)
    return r


# ------------------------------------------------------------------ utilidades
def cuadro(ts=(1.6, 4.6, 11.2, 15.6, 19.8, 23.4)):
    sc = build()
    for i, tt in enumerate(ts):
        f = os.path.join(OUT, '_v4_cuadro_%02d.png' % i)
        sc.render(tt).convert('RGB').save(f)
        print('cuadro t=%.1f ->' % tt, f)


def hoja12():
    sc = build()
    cols, rows = 4, 3
    cw = 300; ch = int(cw * H / W)
    q = Image.new('RGB', (cols * cw, rows * ch), (20, 20, 20))
    d = ImageDraw.Draw(q)
    for i in range(cols * rows):
        tt = DUR * (i + 0.5) / (cols * rows)
        fr = sc.render(tt).convert('RGB').resize((cw, ch), Image.LANCZOS)
        q.paste(fr, ((i % cols) * cw, (i // cols) * ch))
        d.text(((i % cols) * cw + 8, (i // cols) * ch + 6), '%.1fs' % tt, fill=(255, 220, 120),
               font=PR.FONTC(20))
    f = os.path.join(OUT, '_prueba_v4_hoja.jpg'); q.save(f, quality=90)
    print('hoja ->', f)
    # ---- como se ve en un telefono: 405 px de ancho, la medida del PLAN_PASADA_DE_VIDA
    tel_ts = (1.6, 7.2, 11.2, 15.6, 19.8, 23.4)
    tw = 405; th = int(tw * H / W)
    esc = 0.5
    t2 = Image.new('RGB', (int(tw * esc) * len(tel_ts) + 8 * (len(tel_ts) - 1), int(th * esc)), (24, 24, 24))
    for i, tt in enumerate(tel_ts):
        fr = sc.render(tt).convert('RGB').resize((tw, th), Image.LANCZOS)   # primero A 405 px
        t2.paste(fr.resize((int(tw * esc), int(th * esc)), Image.LANCZOS),
                 (i * (int(tw * esc) + 8), 0))
        if i == 2: fr.save(os.path.join(OUT, '_prueba_v4_405.png'))
    f2 = os.path.join(OUT, '_prueba_v4_telefono.jpg'); t2.save(f2, quality=92)
    print('telefono (405 px) ->', f2)


def check():
    import sync
    sc = build()
    bad = sc.check_framing(0, DUR, step=0.20)
    seen = {}
    for t, n, bb, wn in bad: seen.setdefault(n, []).append(t)
    for n, ts in sorted(seen.items(), key=lambda x: -len(x[1])):
        print('CORTADO %-28s %3d muestras  t=%.1f..%.1f' % (n, len(ts), min(ts), max(ts)))
    print('violaciones de encuadre:', len(bad))
    rep = sc.report(0, DUR)
    print('ritmo (eventos): %d cortes (%.1f/min), huecos > 6 s: %s'
          % (rep['cortes'], rep['cortes_por_min'], rep['huecos']))
    r = sync.auditar(sc, os.path.join(OUT, '_tiempos_prueba.json'), out=os.path.join(OUT, '_qc_sync'),
                     dur=DUR, paso=1)
    print('sync:', {k: v for k, v in r.items() if not k.startswith('_')})
    return len(bad), r


def render():
    f = os.path.join(OUT, '_prueba_v4.mp4')
    M.render('prueba_v4', 'build', DUR, f, frames=os.path.join(AQUI, '_frames_v4'))
    print('OK', f)


def medir():
    sys.path.insert(0, PROD)
    import ritmo
    v = os.path.join(OUT, '_prueba_v4.mp4')
    d, ok = ritmo.veredicto(v)
    print(json.dumps(d, indent=1, ensure_ascii=False))
    ritmo.medir(v)
    return ok


if __name__ == '__main__':
    modo = sys.argv[1] if len(sys.argv) > 1 else 'cuadro'
    {'cuadro': cuadro, 'hoja': hoja12, 'check': check, 'render': render, 'medir': medir}[modo]()
