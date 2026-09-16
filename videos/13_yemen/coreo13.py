# -*- coding: utf-8 -*-
"""Ep. 13 · Yemen / Bab el-Mandeb — coreografia sobre el MOTOR v4 (regla 30).

    python videos/13_yemen/coreo13.py cuadro 240     # un cuadro fijo (mirar ANTES de renderizar)
    python videos/13_yemen/coreo13.py check          # check_framing + cortes flojos  (0 y 0)
    python videos/13_yemen/coreo13.py hoja           # hoja de contacto de 12 cuadros REALES
    python videos/13_yemen/coreo13.py sync           # auditoria guion->imagen (VACIO tiene que ser 0)
    python videos/13_yemen/coreo13.py eventos        # _eventos.json para mezcla2.py
    python videos/13_yemen/coreo13.py render         # el cuerpo -> salida/cuerpo.mp4

Formato: **16:9, 1920x1080** (Dispatch). La plantilla de la que sale esto (`S12_recibos/coreo4.py`)
es vertical; aqui cambian el cuadro y las fracciones, no la gramatica.

COMO SE ATA A LA VOZ. Nada se ancla "al principio de la linea": los carteles y las cifras se anclan
a la PALABRA real, con `d.t('nine')`, que sale de `audio/_palabras_cuerpo.json`. Es la diferencia
entre que la cifra acompane a la voz y que la persiga.

LAS TRES COSAS QUE ESTE EPISODIO TIENE QUE RESPETAR SI O SI
  1. Regla 1: nada cortado por el borde. `check_framing` = 0 o el render aborta.
  2. Regla 24: todo lo que se apoya en el mapa va por `d.P('<sitio>')`, que sale de lon/lat. Nada a ojo.
  3. §7 del motor v4: el mapa es `bg` y NO cuenta como contenido. Cada frase necesita su imagen
     ENCIMA del mapa, o `sync.py` marca VACIO y el render no sale.
"""
import json, math, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
PROD = os.path.join(RAIZ, 'produccion')
sys.path.insert(0, PROD)
sys.path.insert(0, AQUI)
import motor as M
import props as PR
import mapa_v2 as MV
from PIL import Image

sys.path.insert(0, os.path.join(AQUI, 'arte'))
import mapa as MAPA

W, H = 1920, 1080
ARTE = os.path.join(AQUI, 'arte', 'assets')
AUDIO = os.path.join(AQUI, 'audio')
NL = chr(10)

# Props de escritorio para los planos de MESA: dicen "esto es una mesa" sin tapar el documento.
# Van de fondo, chicos y en las esquinas. Todos existen ya en produccion/assets (regla 19).
ESCRITORIO = [('lupa', 0.085, 0.845, 0.085), ('moneda', 0.930, 0.870, 0.045),
              ('regla', 0.905, 0.140, 0.026)]

_CACHE = {}


def imagen(nombre):
    """Un prop, cacheado por proceso (build() corre en cada worker del pool).

    Busca primero en los props PROPIOS del episodio (`arte/assets/p13_*.png`, hechos por
    `arte/props13.py`) y despues en el catalogo compartido. Los propios existen porque varios del
    catalogo llevan texto horneado de otros episodios (Malvinas, Rusia, el simbolo euro): el detalle
    esta en la cabecera de `props13.py`."""
    if nombre not in _CACHE:
        cand = [os.path.join(ARTE, 'p13_%s.png' % nombre),
                os.path.join(PROD, 'assets', 'prop_%s.png' % nombre)]
        for c in cand:
            if os.path.exists(c):
                _CACHE[nombre] = Image.open(c).convert('RGBA')
                break
        else:
            raise SystemExit('falta el prop %r (ni %s ni el catalogo)' % (nombre, cand[0]))
    return _CACHE[nombre]


def _norm(w):
    import re
    return re.sub(r'[^a-z0-9]', '', str(w).lower())


class Dir(object):
    """La batuta: mundo + tiempos + helpers de camara y de pantalla."""

    def __init__(self):
        self.mu = MAPA.build()                       # cacheado en disco, no se regenera por worker
        self.sc = M.Scene(self.mu, size=(W, H), v4=True)
        self.zmin = max(W / self.sc.WM, H / self.sc.HM)
        self.t_ = json.load(open(os.path.join(AUDIO, '13_yemen_cuerpo.tiempos.json'), encoding='utf-8'))
        self.pal = [(p['w'], p['t0'], p['t1'])
                    for p in json.load(open(os.path.join(AUDIO, '_palabras_cuerpo.json'), encoding='utf-8'))]
        self.planos = []
        self.avisos = []          # anclas que whisper oyo distinto
        self.dur = self.t_['duracion']

    # ------------------------------------------------------------------ anclas
    def L(self, beat, linea):
        """(inicio, fin) de la linea `linea` del beat `beat`, en segundos del cuerpo."""
        for x in self.t_['lineas']:
            if x['beat'] == beat and x['linea'] == linea:
                return x['inicio'], x['fin']
        raise SystemExit('no existe la linea %d del beat %d' % (linea, beat))

    def B(self, beat):
        b = self.t_['beats'][beat]
        return b['inicio'], b['fin']

    def t(self, patron, desde=0.0):
        """El instante EXACTO en que la voz dice esa palabra, a partir de `desde`.

        `patron` puede ser una palabra o **varias alternativas**: `d.t(('thirty', '30'), t0)`.
        Hace falta porque el guion escribe los numeros con letra —para que el TTS los lea bien— y
        whisper los transcribe como cifra: "thirty kilometres" vuelve como `30 kilometers`, y
        "nine point three" como `9 .3`. Tambien cambia nombres propios raros (Perim -> "Parham").

        Si no encuentra ninguna variante **no aborta**: avisa y devuelve `desde`, con lo que el
        cartel entra al principio de la linea. Peor anclado, pero el video sale; abortar el render
        entero por una palabra que whisper oyo distinto no compensa.
        """
        alts = [patron] if isinstance(patron, str) else list(patron)
        qs = [_norm(a) for a in alts]
        for w, t0, t1 in self.pal:
            wn = _norm(w)
            if t0 >= desde - 1e-9 and any(wn == q or wn.startswith(q) for q in qs):
                return float(t0)
        self.avisos.append((alts, round(desde, 2)))
        return float(desde)

    def P(self, sitio):
        return self.mu.P(sitio)

    # ------------------------------------------------------------------ camara
    # Un plano de mas de ~5 s sin cambio lo cuenta `ritmo.py` como plano muerto. La primera pasada
    # (16-sep) escribia UN plano por grupo de lineas: 51 planos en 934 s = 3,3 cortes/min contra los
    # 10 de la meta, 41 de 51 por encima de 6 s, el mas largo de 33 s, y un recorrido mediano de
    # 0,032 anchos de ventana cuando la doc pide 0,25-0,35. Veredicto: FAIL en las tres pruebas.
    #
    # Se arregla aqui y no en la partitura: `plano()` TROCEA solo. Cada tramo recibe su corte y su
    # viaje, el centro y el zoom se interpolan a lo largo del plano original —asi el movimiento
    # sigue siendo el que pidio la partitura— y ademas:
    #   · el corte alterna escala (abierto / cerrado) para que la PANTALLA cambie y el corte se lea;
    #     dos planos de mapa con zoom parecido no los detecta `ritmo.py` ni los ve el espectador.
    #   · cada tramo entra desplazado, para que su viaje recorra de verdad ~0,3 anchos de ventana.
    TROZO = 4.4          # segundos por tramo
    # SALTO tiene que quedar FUERA de la banda que `cortes_flojos()` considera imperceptible
    # (0,72-1,39): con 1,30 los 148 cortes nuevos entraban justos dentro y no se leian. A 1,50 el
    # corte hacia arriba da 1,50 y el de vuelta 0,67, los dos fuera.
    SALTO = 1.50         # cuanto abre/cierra el corte respecto al zoom interpolado
    DESVIO = 0.40        # desplazamiento de entrada, en anchos de ventana

    def plano(self, t0, t1, c0, z0, c1, z1, tipo='mapa', trocear=True):
        """Un plano = un corte + UN viaje motivado. El viaje va HACIA lo que dice la voz.

        Si dura mas de `TROZO * 1.25` se parte en tramos; `trocear=False` lo deja entero (lo usan
        los bloques de acto, que tienen su propia coreografia de 4,4 s)."""
        c0 = self.P(c0) if isinstance(c0, str) else c0
        c1 = self.P(c1) if isinstance(c1, str) else c1
        z0, z1 = max(z0, self.zmin), max(z1, self.zmin)
        dur = t1 - t0
        n = 1 if (not trocear or dur <= self.TROZO * 1.25) else int(math.ceil(dur / self.TROZO))
        for k in range(n):
            a = t0 + dur * k / n
            b = t0 + dur * (k + 1) / n
            u0, u1 = k / float(n), (k + 1) / float(n)
            ca = (c0[0] + (c1[0] - c0[0]) * u0, c0[1] + (c1[1] - c0[1]) * u0)
            cb = (c0[0] + (c1[0] - c0[0]) * u1, c0[1] + (c1[1] - c0[1]) * u1)
            za = max(self.zmin, z0 + (z1 - z0) * u0)
            zb = max(self.zmin, z0 + (z1 - z0) * u1)
            if n > 1:
                # En un plano ABIERTO el mundo ya llena el cuadro: el motor sujeta el centro contra
                # el borde, el desvio se anula y el corte no cambia nada. Es lo que dejaba dos huecos
                # de 8 s (t=251 con z=0,26 y t=656 con z=0,43) pese a haber un corte cada 4,4 s.
                # Donde no se puede mover la camara, se mueve la ESCALA: el salto crece con la
                # apertura, y ahi solo se cierra —abrir mas chocaria contra `zmin` y se quedaria igual.
                ap = min(1.0, self.zmin / max(1e-6, za))      # 1 = mundo entero en pantalla
                salto = self.SALTO * (1.0 + 0.85 * ap)
                sube = bool(k % 2) or (za / salto) < self.zmin * 1.10
                za = max(self.zmin, za * (salto if sube else 1.0 / salto))
                ancho = W / za
                s = 1 if k % 2 else -1
                ca = (ca[0] - s * self.DESVIO * ancho * 0.88,
                      ca[1] - s * self.DESVIO * ancho * 0.30)
            self.sc.corte(a, ca, za)
            self.sc.viaje(a, b, cb, zb, 'io')
            self.planos.append((a, b, tipo, ca, za, cb, zb))
            if b - a > 2.0:
                M.ev(a + 0.05, 'whoosh', 0.35)
        return self

    def cortes_flojos(self):
        """Cortes que la pantalla no va a leer como cortes (dos planos de mapa casi iguales).

        `ritmo.py` da por detectado un corte cuando dos cuadros seguidos difieren mas de 12/255:
        dos planos de mapa con zoom y centro parecidos ensenan lo mismo y el corte no existe."""
        flojos = []
        for a, b in zip(self.planos, self.planos[1:]):
            a0, a1, ta, ca0, za0, ca1, za1 = a
            b0, b1, tb, cb0, zb0, cb1, zb1 = b
            if abs(b0 - a1) > 0.05 or ta != tb:
                continue
            r = zb0 / max(1e-6, za1)
            ancho = W / max(1e-6, za1)
            dxy = math.hypot(cb0[0] - ca1[0], cb0[1] - ca1[1]) / max(1e-6, ancho)
            # mesa->mesa se marcaba SIEMPRE, heredado de la plantilla S12: alli el documento es HUD
            # y la camara no se movia, asi que a los dos lados del corte habia el mismo papel. Aqui
            # la mesa **si** lleva plano de camara (el mapa velado viaja debajo), asi que se juzga
            # con el mismo criterio que el mapa: floja solo si ni la escala ni el encuadre cambian.
            if 0.72 < r < 1.39 and dxy < 0.40:
                flojos.append((round(b0, 1), '%s->%s' % (ta, tb), round(r, 2), round(dxy, 2)))
        return flojos

    # ------------------------------------------------------------------ pantalla (HUD)
    def hud(self, im, t0, t1, fx, fy, alto_rel, z=60, entra=0.30, sale=0.26, sfx='pop',
            nombre=None, bg=False, margen=20, ancho_max=0.92):
        """Objeto de PANTALLA, escalado a `alto_rel` del alto y SUJETO DENTRO (regla 1)."""
        k = (H * alto_rel) / im.height
        if im.width * k > W * ancho_max - 2 * margen:
            k = (W * ancho_max - 2 * margen) / im.width
        w2, h2 = im.width * k / 2, im.height * k / 2
        o = M.Obj(im, z=z)
        o.name = nombre or 'card:hud'
        o.bg = bg
        o.wobble = 0.0; o.bob = 0.0; o.vida = 0.0; o.shadow = False
        o.sc = M.Track(k)
        o.x = M.Track(min(max(W * fx, w2 + margen), W - w2 - margen))
        o.y = M.Track(min(max(H * fy, h2 + margen), H - h2 - margen))
        o.on, o.off = t0, t1
        o.a.set(t0, 0, 'hold'); o.a.set(t0 + entra, 1, 'io')
        o.a.set(max(t0 + entra, t1 - sale), 1, 'hold'); o.a.set(t1, 0, 'io')
        if sfx:
            M.ev(t0, sfx, 0.5)
        self.sc.add_hud(o)
        return o

    def prop(self, nombre, t0, t1, fx, fy, alto=0.16, **kw):
        kw.setdefault('nombre', 'prop:' + nombre)
        return self.hud(imagen(nombre), t0, t1, fx, fy, alto, **kw)

    def card(self, txt, t0, t1, fx=0.5, fy=0.22, alto=0.070, size=66, color=None, tcolor=None, **kw):
        im = PR.card(txt, size=size, color=color or PR.PAPEL, tcolor=tcolor or PR.TINTA)
        kw.setdefault('nombre', 'card:' + txt.replace(NL, ' '))
        return self.hud(im, t0, t1, fx, fy, alto, **kw)

    def cifra(self, txt, t0, t1, fx=0.5, fy=0.30, alto=0.150, size=190, tcolor=None, **kw):
        """La CIFRA del beat. El prefijo `cifra:` es lo que hace que `sync.py` la vea y no
        marque CIFRA_SIN_PANTALLA."""
        im = PR.card(txt, size=size, color=PR.PAPEL, tcolor=tcolor or PR.ROJO)
        kw.setdefault('nombre', 'cifra:' + txt.replace(NL, ' '))
        kw.setdefault('sfx', 'flip')
        return self.hud(im, t0, t1, fx, fy, alto, **kw)

    def sello(self, txt, t0, t1, fx=0.5, fy=0.5, alto=0.10, size=60, **kw):
        im = PR.sello(txt, color=PR.ROJO, size=size)
        kw.setdefault('nombre', 'sello:' + txt)
        kw.setdefault('sfx', 'stamp')
        kw.setdefault('entra', 0.16)
        o = self.hud(im, t0, t1, fx, fy, alto, **kw)
        self.sc.shake(t0)
        return o

    def rotulo(self, txt, t0, t1, fy=0.075, size=44, alto=0.046):
        """Rotulo del beat. `sync.visible()` lo IGNORA a proposito: un rotulo no es contenido."""
        im = PR.card(txt, size=size, color=PR.PAPEL, tcolor=PR.TINTA)
        return self.hud(im, t0, t1, 0.5, fy, alto, z=58, nombre='rotulo:' + txt.replace(NL, ' '),
                        entra=0.26, sale=0.22, sfx=None)

    # ------------------------------------------------------------------ mesa
    def mesa(self, t0, t1, doc, fy=0.46, alto=0.56, oscuro=0.32, rot=2.4, deriva=0.12,
             centro='Bab el-Mandeb', z=None):
        """Plano de MESA: mundo oscurecido + documento grande + props de escritorio de fondo.

        **Sin hoja rayada a pantalla completa**: el documento ES el papel (Agustin rechazo "una cosa
        blanca con lineas" en el ep. 09). Asi el mapa oscurecido se sigue viendo alrededor."""
        mu = self.mu
        # La MESA tambien necesita su plano de camara. Sin el, la coreografia no toca la camara en
        # todo el tramo: el mapa se queda congelado debajo del velo y el documento es HUD, que no se
        # mueve con el zoom -> la pantalla entera se para. En el tramo 100-200 s eso daba un hueco de
        # 29,5 s sin un solo cambio para `ritmo.py`, con 63 cortes detectados alrededor. El manual del
        # motor v4 lo dice: "lo que si da movimiento en un plano de mesa es el VIAJE de camara (el
        # mapa velado se mueve debajo)". Va troceado como cualquier otro plano.
        zz = z if z is not None else 0.62
        self.plano(t0, t1, centro, zz, centro, zz * 1.22, tipo='mesa')
        if t0 > 0.05:
            mu.dark.set(max(0.0, t0 - 0.14), mu.dark(max(0.0, t0 - 0.14)), 'hold')
            mu.dark.set(t0, oscuro, 'io')
        else:
            mu.dark.set(0.0, oscuro, 'hold')
        mu.dark.set(max(t0 + 0.2, t1 - 0.12), oscuro, 'hold')
        mu.dark.set(t1, 0.0, 'io')
        for nom, fx, fy2, al in ESCRITORIO:
            o = self.hud(imagen(nom), t0, t1, fx, fy2, al, z=12, nombre='mesa:' + nom,
                         bg=True, entra=0.30, sale=0.22, sfx=None)
            o.rot.set(t0, -0.8, 'hold'); o.rot.set(t1, 0.8, 'io')
        if doc is None:
            return None
        o = self.hud(imagen(doc), t0 + 0.05, t1 - 0.05, 0.5, fy, alto, z=40,
                     nombre='doc:' + doc, entra=0.36, sale=0.26, sfx='paper')
        # El documento CRECE HACIA la escala que `hud()` calculo, no a partir de ella: multiplicarla
        # al final lo sacaba por los bordes (21 violaciones de la regla 1 en la pieza 1 de la S12).
        k = o.sc(t0 + 0.05)
        o.sc.set(t0 + 0.05, k / (1 + deriva), 'hold'); o.sc.set(t1 - 0.05, k, 'io')
        o.rot.set(t0 + 0.05, -rot / 2, 'hold'); o.rot.set(t1 - 0.05, rot / 2, 'io')
        return o

    # ------------------------------------------------------------------ acto (regla 25)
    def acto(self, num, titulo, t0, dur=4.4):
        """El bloque de transicion, que YA ESTA EN EL AUDIO (`audio/actos13.py`). Aqui va la imagen:
        golpe y sacudon -> regla de papel que cruza -> velo -> cae ACT N -> ficha PAPER TRAIL."""
        mu = self.mu
        M.ev(t0, 'stinger', 0.9)
        M.ev(t0 + 0.02, 'thump', 0.8)
        self.sc.shake(t0)
        # velo: el mapa se apaga y vuelve al cortar al acto
        mu.dark.set(max(0.0, t0 - 0.05), mu.dark(max(0.0, t0 - 0.05)), 'hold')
        mu.dark.set(t0 + 0.45, 0.82, 'io')
        mu.dark.set(t0 + dur - 0.55, 0.82, 'hold')
        mu.dark.set(t0 + dur, 0.0, 'io')
        # la regla de papel cruza el cuadro
        r = self.hud(imagen('regla'), t0 + 0.05, t0 + 0.95, -0.15, 0.5, 0.030, z=70,
                     nombre='acto:regla', entra=0.05, sale=0.05, sfx='whoosh', margen=-400)
        r.x.set(t0 + 0.05, -260, 'hold'); r.x.set(t0 + 0.95, W + 260, 'io')
        # La regla CRUZA el cuadro a proposito: entra por un borde y sale por el otro. Sin esto,
        # `check_framing` la cuenta como violacion de la regla 1 y aborta el render. `transit` es
        # justo el mecanismo que el motor tiene para lo que sale de cuadro queriendo.
        r.transit.append((t0, t0 + 1.05))
        # la tarjeta del acto entra girando, y la segunda voz la lee a 1,5 s (regla 25)
        c = self.card(num, t0 + 0.55, t0 + dur - 0.30, fy=0.44, alto=0.120, size=150,
                      tcolor=PR.ROJO, entra=0.28, sale=0.24, sfx='clack')
        c.rot.set(t0 + 0.55, -7.0, 'hold'); c.rot.set(t0 + 1.30, 0.0, 'back')
        self.card(titulo, t0 + 1.35, t0 + dur - 0.30, fy=0.605, alto=0.052, size=56,
                  entra=0.26, sale=0.22, sfx=None, nombre='acto:sub:' + titulo)
        self.card('PAPER TRAIL', t0 + 2.35, t0 + dur - 0.25, fy=0.735, alto=0.034, size=38,
                  entra=0.24, sale=0.20, sfx='stamp', nombre='acto:ficha')
        self.planos.append((t0, t0 + dur, 'acto', (0, 0), 1.0, (0, 0), 1.0))  # no se trocea


# ====================================================================== partitura
def build():
    M.EVENTS.clear()
    d = Dir()
    import partitura13
    partitura13.escribir(d)
    # `size` a mano: el motor calcula `W*0.062`, que sobre 1920 de ancho da 119 px de fuente. Eso
    # esta pensado para VERTICAL (W=1080 -> 67 px sobre 1920 de alto); en 16:9 la caja salia de
    # 361 px de alto y se iba por debajo del cuadro -> 1.353 violaciones de la regla 1.
    d.sc.subtitulos(d.pal, estilo='banda', fy=0.868, size=52, ancho=0.80,
                    resaltar=['9.3', '4.1', '30', '15', '332', '$99.85', '$109.21',
                              'Perim', 'Mocha', 'Sanaa', 'Hormuz'])
    d.sc.dur = d.dur
    return d.sc, d


# ====================================================================== comandos
def _sc():
    sc, d = build()
    return sc, d


def escena():
    """Solo la Scene. `M.render` importa este modulo en cada worker y llama a esta funcion, y
    espera **una Scene**, no la tupla que devuelve `build()`."""
    return build()[0]


def cuadro(ts):
    sc, d = _sc()
    for t in ts:
        im = sc.render(float(t))
        p = os.path.join(AQUI, '_cuadro_%s.jpg' % str(t).replace('.', '_'))
        im.convert('RGB').save(p, quality=90)
        print('  ->', p)


def check():
    sc, d = _sc()
    v = sc.check_framing(0, sc.dur)
    print('violaciones de encuadre:', len(v))
    for x in v[:12]:
        print('   CORTADO', x)
    f = d.cortes_flojos()
    print('cortes flojos:', len(f))
    for x in f[:12]:
        print('   FLOJO', x)
    print('anclas no encontradas:', len(d.avisos))
    for a in d.avisos[:12]:
        print('   ANCLA', a)
    print('planos:', len(d.planos), ' duracion:', round(sc.dur, 1), 's')
    return 0 if (not v and not f) else 1


def sync_():
    sc, d = _sc()
    import sync
    r = sync.auditar(sc, os.path.join(AUDIO, '13_yemen_cuerpo.tiempos.json'),
                     out=os.path.join(AQUI, '_qc'))
    print(r)
    return 0 if not r.get('VACIO') else 1


# Musica por acto (regla 9: cues propias de Lyria, sin derechos de terceros). Las 7 que hay ya
# estan pagadas (regla 19); se reparten por peso dramatico, no por orden de archivo.
CUES = [
    {'beats': [0, 1, 2], 'file': 'musica/cue_01_intro.mp3'},     # preguntas, cold open y gancho
    {'beats': [3, 4], 'file': 'musica/cue_03_partes.mp3'},       # la geografia y las dos versiones
    {'beats': [5, 6], 'file': 'musica/cue_02_flota.mp3'},        # ACT I-II: el estrecho y quienes son
    {'beats': [7, 8], 'file': 'musica/cue_04_dron.mp3'},         # ACT III-IV: los once anos y la tenaza
    {'beats': [9, 10, 11], 'file': 'musica/cue_05_pais.mp3'},    # ACT V, cierre y proximo
]
# El pulso grave acelera en los actos III-V, que es donde el relato aprieta.
PULSO = [{'beats': [7], 'bpm': [58, 70], 'db': -17},
         {'beats': [8], 'bpm': [66, 80], 'db': -16},
         {'beats': [9, 10], 'bpm': [72, 88], 'db': -16}]


def eventos():
    """Exporta `_eventos.json` para `mezcla2.py`: los efectos que emitio la coreografia + las cues."""
    sc, d = _sc()
    ev = [{'t': t, 'kind': k, 'vol': v} for (t, k, v) in sorted(M.EVENTS)]
    out = os.path.join(AQUI, '_eventos.json')
    json.dump({'eventos': ev, 'cues': CUES, 'pulso': PULSO,
               'musica_db': -13.0, 'duck_db': -5.0, 'sfx_db': 6.0},
              open(out, 'w', encoding='utf-8'), indent=1)
    from collections import Counter
    c = Counter(k for _, k, _ in M.EVENTS)
    print('%d eventos -> %s' % (len(ev), out))
    print('  ' + '  '.join('%s=%d' % kv for kv in sorted(c.items())))
    return out


def hoja():
    sc, d = _sc()
    n = 12
    ims = [sc.render(sc.dur * (i + 0.5) / n) for i in range(n)]
    w, h = W // 4, H // 4
    hoja = Image.new('RGB', (w * 4, h * 3), (20, 20, 20))
    for i, im in enumerate(ims):
        hoja.paste(im.convert('RGB').resize((w, h), Image.LANCZOS), ((i % 4) * w, (i // 4) * h))
    p = os.path.join(AQUI, '_hoja.jpg')
    hoja.save(p, quality=88)
    print('  ->', p)


# Cuantos procesos del pool. El automatico del motor es (nucleos - 2) = 14 aqui, y **no cabe en
# memoria**: cada worker construye la escena entera, y este mundo son 9000x7697 en RGBA = 277 MB,
# mas las cuatro capas de pais del mismo tamano = ~1,4 GB por worker. Con 14 pedia ~19 GB sobre 15,7
# de la maquina y el render moria con MemoryError a mitad. Con 5 son ~7 GB, que entran en los 8,8
# libres. Si se cambia el tamano del mundo, hay que revisar este numero.
WORKERS = 5


def render(t0=0.0, dur=None, workers=WORKERS):
    """El cuerpo -> salida/cuerpo.mp4.

    `frames` propio del episodio: `produccion/_frames` es compartido y dos renders a la vez se
    pisan (canal/ESTRUCTURA.md §4.1). El audio que se pega aqui es la VOZ; la mezcla con las cues
    se hace despues y solo hay que rehacer el muxing, no los cuadros."""
    sc, d = _sc()
    out = os.path.join(AQUI, 'salida')
    os.makedirs(out, exist_ok=True)
    return M.render('coreo13', 'escena', dur or sc.dur, os.path.join(out, 'cuerpo.mp4'),
                    audio=os.path.join(AUDIO, '13_yemen_cuerpo.wav'), workers=workers,
                    t0=t0, frames=os.path.join(AQUI, '_frames'))


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if cmd == 'cuadro':
        cuadro(sys.argv[2:] or [30])
    elif cmd == 'check':
        sys.exit(check())
    elif cmd == 'sync':
        sys.exit(sync_())
    elif cmd == 'hoja':
        hoja()
    elif cmd == 'eventos':
        eventos()
    elif cmd == 'render':
        a = [float(x) for x in sys.argv[2:4]]
        print(render(a[0] if a else 0.0, a[1] if len(a) > 1 else None))
    else:
        raise SystemExit('cmd: cuadro | check | sync | hoja | render')
