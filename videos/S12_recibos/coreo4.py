# -*- coding: utf-8 -*-
"""S12 · coreografia sobre el MOTOR v4. El motor de las cuatro piezas; la partitura de cada una
esta en `escenas4.py`.

    python coreo4.py cuadro 4      # cuadros fijos (primero el cuadro, despues el render)
    python coreo4.py check 4       # check_framing + sync.py   (los dos tienen que dar 0)
    python coreo4.py hoja 4        # hoja de contacto de 12 cuadros REALES + la vista a 405 px
    python coreo4.py render 4      # el cuerpo -> shorts/<n>/salida/cuerpo.mp4

NO TOCAR `coreo.py` NI `escenas.py` (la v1): quedan como referencia de lo que se hacia antes.

LAS TRES CORRECCIONES DE LA AUDITORIA SOBRE `prueba_v4.py`, QUE ES LO QUE CAMBIA AQUI

  1. **Nada de hoja rayada a pantalla completa en los planos de MESA.** En la prueba, 5 de 12
     cuadros reales eran una hoja de papel con renglones tapando el mapa — el look que Agustin
     rechazo en el ep. 09 («una cosa blanca con lineas»). Aca MESA es: el mundo oscurecido
     (`dark` 0,55-0,62) + **el DOCUMENTO grande como objeto** (40-55 % del alto) + dos o tres
     props de escritorio chicos en las esquinas, de fondo + las tarjetas. El documento ES el
     papel: no hace falta una hoja debajo, y asi el mapa oscurecido sigue viendose alrededor.
  2. **Ceuta se pinta de espanol POR ENCIMA de Marruecos** (`mundos4.py::ESTRECHO`). Si el
     geojson de los enclaves faltara, `_capas_pieza4` **no pinta Marruecos**: antes un mapa sin
     color que un mapa que diga que Ceuta es Marruecos.
  3. **El gancho va sobre el MAPA en movimiento.** Los primeros `HOOK` segundos de cada pieza son
     un plano de mapa con la camara viajando; el documento de MESA entra despues. `escenas4` lo
     comprueba y `build()` aborta si una partitura pone MESA antes de `HOOK`.

COMO SE ATA A LA VOZ. Nada se ancla «al principio de la linea»: todo se ancla a la palabra real
(`audio/_palabras.json`, timestamps de fal). `p.t('fortynine')` devuelve el instante en que George
dice «forty-nine», y la cifra entra ahi. Es la diferencia entre que la cifra acompane a la voz y
que la persiga.
"""
import json, math, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
PROD = os.path.join(RAIZ, 'produccion')
sys.path.insert(0, PROD); sys.path.insert(0, AQUI)
import motor as M
import props as PR
import mapa_v2 as MV
import mundos4
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
HOOK = 3.5                      # lo que dura la tarjeta de gancho que pega `armar_vertical`
ARTE = os.path.join(AQUI, 'arte', 'assets')
DIRS = {1: '01_tanque', 2: '02_hormuz', 3: '03_hoteles', 4: '04_ceuta'}
NL = chr(10)

# Props de escritorio para los planos de MESA. Del catalogo que ya existe: `clip` y `lapiz` no
# estan, asi que se usan los que si (`lupa`, `moneda`, `regla`, `clavo`, `tijera`). Van de fondo,
# chicos y en las esquinas: dicen «esto es una mesa» sin tapar el documento.
# El `alto_rel` es del ALTO del cuadro y el ancho sale solo: `regla` mide 234x52, asi que un
# alto_rel de 0,070 daba una barra de 603 px cruzando la pantalla (se vio en la hoja de contacto
# de la pieza 4, t=70 s). Estos numeros estan mirados en un cuadro real, no puestos a ojo.
ESCRITORIO = [('lupa', 0.130, 0.820, 0.078), ('moneda', 0.888, 0.848, 0.042),
              ('regla', 0.858, 0.150, 0.022)]


def imagen(name):
    for base in (ARTE, os.path.join(PROD, 'assets')):
        p = os.path.join(base, 'prop_%s.png' % name)
        if os.path.exists(p): return Image.open(p).convert('RGBA')
    raise SystemExit('falta el prop: %s  (dibujalo en arte/props_s12.py)' % name)


def _norm(w):
    import re
    return re.sub(r'[^a-z0-9]', '', w.lower())


class Pieza:
    """El contexto que recibe cada partitura de `escenas4`."""

    def __init__(self, n):
        self.n = n
        self.dir = DIRS[n]
        self.aud = os.path.join(AQUI, 'shorts', self.dir, 'audio')
        self.T = json.load(open(os.path.join(self.aud, 'tiempos.json'), encoding='utf-8'))
        self.pal = [tuple(x) for x in
                    json.load(open(os.path.join(self.aud, '_palabras.json'), encoding='utf-8'))]
        self.dur = float(self.T['dur'])
        self.mu = mundos4.mundo(n)
        self.sc = M.Scene(self.mu, size=(W, H), v4=True)
        self.P = self.mu.P
        self.zmin = max(W / self.mu.w, H / self.mu.h)
        self.planos = []
        self._nombres = set()

    # ------------------------------------------------------------------ tiempos
    def L(self, i):
        """(inicio, fin) de la linea `i` del guion."""
        l = self.T['lineas'][i]; return float(l['inicio']), float(l['fin'])

    def t(self, patron, desde=0.0, si_falta=None):
        """Cuando empieza la palabra `patron` (normalizada) a partir de `desde`.

        Es LA funcion de este modulo: anclar a la palabra y no al principio de la linea es lo que
        hace que la cifra entre cuando la voz la dice. Si la palabra no esta, se avisa fuerte en
        vez de colocar el cartel en un sitio cualquiera."""
        q = _norm(patron)
        for w, t0, t1 in self.pal:
            wn = _norm(w)          # `_palabras.json` guarda la palabra con su puntuacion
            if t0 >= desde - 1e-9 and (wn == q or wn.startswith(q)):
                return float(t0)
        if si_falta is not None:
            print('   AVISO pieza %d: no encuentro %r despues de %.2f -> %.2f'
                  % (self.n, patron, desde, si_falta))
            return float(si_falta)
        raise SystemExit('pieza %d: la palabra %r no esta en _palabras.json despues de %.2f s'
                         % (self.n, patron, desde))

    # ------------------------------------------------------------------ camara
    def plano(self, t0, t1, c0, z0, c1, z1, tipo='mapa'):
        """Un plano = un corte + UN viaje motivado (la gramatica v4).

        `c0`/`c1` son px de mundo o nombres de sitio. El viaje va SIEMPRE hacia lo que dice la voz;
        el recorrido es del 25-35 % para que se lea como un viaje y no como una foto que respira
        (medido en la prueba v4: con un 10 % `ritmo.py` da 2,6 y con un 30 % da 4,6)."""
        c0 = self.P(c0) if isinstance(c0, str) else c0
        c1 = self.P(c1) if isinstance(c1, str) else c1
        z0 = max(z0, self.zmin); z1 = max(z1, self.zmin)
        self.sc.corte(t0, c0, z0)
        self.sc.viaje(t0, t1, c1, z1, 'io')
        self.planos.append((t0, t1, tipo, c0, z0, c1, z1))
        if t1 - t0 > 2.0: M.ev(t0 + 0.05, 'whoosh', 0.35)
        return self

    def _cortes_flojos(self):
        """Cortes que NO se van a leer como cortes, y por que importa.

        `ritmo.py` da por detectado un corte cuando dos cuadros seguidos difieren mas de 12/255.
        Dos planos de MAPA seguidos con zoom parecido y centro parecido ensenan casi lo mismo: la
        camara salta, pero la PANTALLA no cambia, y entonces el corte no existe ni para el que mira
        ni para la medicion. Medido en la pieza 4: el primer montaje tenia un tramo de **20 s sin un
        solo corte detectado** (38-58 s) hecho de cinco planos seguidos, todos de mapa y todos con
        saltos de zoom por debajo del 40 %. `ritmo.py` lo marcaba como «un plano de 20 s» y tenia
        razon.

        Un corte entre dos planos de MESA con el mismo documento tampoco se lee: el documento es HUD
        y no se mueve con la camara, asi que a los dos lados del corte hay el mismo papel.
        """
        flojos = []
        for a, b in zip(self.planos, self.planos[1:]):
            a0, a1, ta, ca0, za0, ca1, za1 = a
            b0, b1, tb, cb0, zb0, cb1, zb1 = b
            if abs(b0 - a1) > 0.05: continue
            r = zb0 / max(1e-6, za1)
            ancho = W / max(1e-6, za1)               # ancho de la ventana en px de mundo
            dxy = math.hypot(cb0[0] - ca1[0], cb0[1] - ca1[1]) / max(1e-6, ancho)
            if ta != tb:
                continue          # mapa<->mesa: el mundo se oscurece y entra un documento; se lee
            if ta == 'mesa':
                flojos.append((b0, 'mesa->mesa', r, dxy))
            elif 0.72 < r < 1.39 and dxy < 0.40:
                flojos.append((b0, '%s->%s' % (ta, tb), r, dxy))
        return flojos

    # ------------------------------------------------------------------ MESA (correccion 1)
    def mesa(self, t0, t1, doc, fy=0.44, alto=0.50, oscuro=0.30, escritorio=ESCRITORIO,
             rot=2.6, deriva=0.130, sfx='paper'):
        """Plano de MESA: mundo oscurecido + DOCUMENTO grande + props de escritorio de fondo.

        Sin hoja rayada: el documento es el papel. El documento **se mueve** (crece un `deriva` y
        gira `rot` grados a lo largo del plano) porque `mu.dark` congela el mapa y, si el documento
        tambien esta quieto, el plano entero es una foto — que es de donde salia el 27 % de quietos
        de `prueba_vida.py`."""
        mu = self.mu
        if t0 > 0.05:
            mu.dark.set(max(0.0, t0 - 0.14), mu.dark(max(0.0, t0 - 0.14)), 'hold')
            mu.dark.set(t0, oscuro, 'io')
        else:
            mu.dark.set(0.0, oscuro, 'hold')
        mu.dark.set(max(t0 + 0.2, t1 - 0.12), oscuro, 'hold'); mu.dark.set(t1, 0.0, 'io')
        for nom, fx, fy2, al in (escritorio or []):
            o = self.hud(imagen(nom), t0, t1, fx, fy2, al, z=12, nombre='mesa:' + nom,
                         bg=True, entra=0.30, sale=0.22, sfx=None)
            o.rot.set(t0, -0.8, 'hold'); o.rot.set(t1, 0.8, 'io')      # nada del todo quieto
        if doc is None:
            # MESA SIN DOCUMENTO: solo el mundo oscurecido como fondo neutro. Sirve cuando lo que
            # tiene que leerse son las BARRAS o las tarjetas y un documento competiria con ellas;
            # y da un corte de verdad (la pantalla entera cambia de tono) alli donde dos planos de
            # mapa seguidos no lo darian.
            return None
        o = self.hud(imagen(doc), t0 + 0.05, t1 - 0.05, 0.5, fy, alto, z=40,
                     nombre='doc:' + doc, entra=0.36, sale=0.26, sfx=sfx)
        # El documento CRECE HACIA el tamano que `hud()` calculo, no a partir de el: `hud()` ya
        # eligio la escala mayor que entra en el cuadro, asi que multiplicarla por (1+deriva) al
        # final lo sacaba por los bordes — 21 violaciones de la regla 1 en la pieza 1, 19 en la 3.
        # Creciendo hacia `k` el movimiento es el mismo y el maximo sigue entrando.
        k = o.sc(t0 + 0.05)
        o.sc.set(t0 + 0.05, k / (1 + deriva), 'hold'); o.sc.set(t1 - 0.05, k, 'io')
        o.rot.set(t0 + 0.05, -rot / 2, 'hold'); o.rot.set(t1 - 0.05, rot / 2, 'io')
        # NO se le pone wobble/bob. Se probó (0,9° y 3 px, buscando movimiento en los planos de
        # mesa) y **rompe la regla 1**: el documento ocupa media pantalla, así que cualquier giro lo
        # saca del cuadro — 24 violaciones de encuadre en la pieza 1, 15 en la 3, 8 en la 2. Y no
        # servía: la mediana de movimiento no se movió (2,77). Lo que sí da movimiento en un plano
        # de mesa es el VIAJE de cámara (el mapa velado se mueve debajo) y el `deriva` del papel.
        self.planos and self.planos[-1]
        return o

    # ------------------------------------------------------------------ HUD
    def hud(self, im, t0, t1, fx, fy, alto_rel, z=60, entra=0.30, sale=0.26, sfx='pop',
            nombre=None, bg=False, margen=18, ancho_max=0.92):
        """Un objeto de PANTALLA, escalado a `alto_rel` del alto del cuadro y sujeto DENTRO
        (regla 1: nada cortado). Cruza los cortes de camara sin partirse, que es lo que el motor
        v3 no dejaba hacer."""
        k = (H * alto_rel) / im.height
        if im.width * k > W * ancho_max - 2 * margen: k = (W * ancho_max - 2 * margen) / im.width
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

    def card(self, txt, t0, t1, fx=0.5, fy=0.20, alto=0.055, size=64, color=None, tcolor=None, **kw):
        im = PR.card(txt, size=size, color=color or PR.PAPEL, tcolor=tcolor or PR.TINTA)
        kw.setdefault('nombre', 'card:' + txt.replace(NL, ' '))
        return self.hud(im, t0, t1, fx, fy, alto, **kw)

    def rotulo(self, txt, t0, t1, fy=0.09, size=46, alto=0.040):
        """El rotulo corto del beat, arriba. `sync.visible()` lo ignora a proposito: un rotulo de
        plano NO es contenido, y contarlo es lo que dejaba pasar los 24 s vacios del ep. 09."""
        im = PR.card(txt, size=size, color=PR.PAPEL, tcolor=PR.TINTA)
        return self.hud(im, t0, t1, 0.5, fy, alto, z=58, nombre='rotulo:' + txt.replace(NL, ' '),
                        entra=0.26, sale=0.22, sfx=None)

    def cifra(self, txt, t0, t1, fy=0.335, alto=0.115, size=180, tcolor=None, **kw):
        """La CIFRA del beat: tarjeta de papel, cuerpo grande, legible a 405 px.

        El nombre lleva el prefijo `cifra:` para que la bandera CIFRA_SIN_PANTALLA de `sync.py` la
        vea aunque este dibujada dentro de un prop (es la limitacion §8.3 del informe del motor)."""
        im = PR.card(txt, size=size, color=PR.PAPEL, tcolor=tcolor or PR.ROJO)
        kw.setdefault('sfx', 'stamp')
        kw.setdefault('entra', 0.12)          # un sello golpea, no se desvanece
        kw.setdefault('sale', 0.18)
        return self.hud(im, t0, t1, kw.pop('fx', 0.5), fy, alto, z=62,
                        nombre='cifra:' + txt.replace(NL, ' '), **kw)

    def prop(self, cual, t0, t1, fx, fy, alto, **kw):
        """Un prop del catalogo como objeto de pantalla.

        El primer parametro se llama `cual` y no `nombre` a proposito: `nombre` es el que viaja en
        `kw` hasta `hud()` cuando hay varias copias del mismo prop (doce petroleros, tres hoteles) y
        cada una necesita un nombre distinto. Con los dos llamandose igual, Python se queja de
        «multiple values for argument 'nombre'»."""
        kw.setdefault('nombre', 'prop:' + cual)
        return self.hud(imagen(cual), t0, t1, fx, fy, alto, **kw)

    # ------------------------------------------------------------------ secuencias animadas
    def secuencia(self, base, t0, t1, n0, n1, fx, fy, alto, z=50, pasos=13, nombre=None,
                  hold_final=0.0):
        """Una secuencia de PNGs (`tanque_n00..12`, `barra_d00..12`, `torre_n00..12`) reproducida
        entre `t0` y `t1`. Cada cuadro es un objeto que se enciende y se apaga: es la unica forma
        de animar un prop con este motor y es lo que ya usaba `coreo.py` v1.

        TRAMPA CONOCIDA (`reference-coreo-crecer-y-props`): `crecer` hace desaparecer props sin que
        el check lo note. Aca no se escala la secuencia: se cambia de cuadro y ya, y todos los
        cuadros se colocan con la MISMA `k` (la del cuadro mas alto), para que la pieza no palpite
        de tamano al cambiar de imagen."""
        ims = [imagen('%s%02d' % (base, i)) for i in range(pasos)]
        hmax = max(i.height for i in ims)
        k = (H * alto) / hmax
        if max(i.width for i in ims) * k > W * 0.92: k = (W * 0.92) / max(i.width for i in ims)
        orden = list(range(n0, n1 + 1)) if n1 >= n0 else list(range(n0, n1 - 1, -1))
        paso = (t1 - t0) / max(1, len(orden))
        objs = []
        for j, idx in enumerate(orden):
            a = t0 + j * paso
            b = t1 + hold_final if j == len(orden) - 1 else a + paso + 0.012   # solape minimo
            im = ims[idx]
            o = M.Obj(im, z=z)
            o.name = (nombre or 'prop:' + base) if j == len(orden) - 1 else 'seq:%s%02d' % (base, idx)
            o.bg = False; o.wobble = 0.0; o.bob = 0.0; o.vida = 0.0; o.shadow = False
            o.sc = M.Track(k)
            o.x = M.Track(min(max(W * fx, im.width * k / 2 + 16), W - im.width * k / 2 - 16))
            o.y = M.Track(min(max(H * fy, im.height * k / 2 + 16), H - im.height * k / 2 - 16))
            o.on, o.off = a, b
            o.a = M.Track(1.0)
            if j == 0: o.a.set(a, 0, 'hold'); o.a.set(a + 0.22, 1, 'io')
            if j == len(orden) - 1:
                o.a.set(max(a + 0.22, b - 0.30), 1, 'hold'); o.a.set(b, 0, 'io')
            self.sc.add_hud(o)
            objs.append(o)
            M.ev(a, 'tick', 0.16)
        return objs

    # ------------------------------------------------------------------ rutas
    def ruta(self, puntos, t0, t1, color=None, width=11, dotted=False, t_off=None,
             verificar=None, tol=0.90, saltar_extremos=1):
        """Una ruta sobre el mapa a partir de puntos (lon, lat).

        Los puntos se proyectan con la MISMA proyeccion del mundo y se registran en `mu.pts`
        (regla 24: de lon/lat, nunca a ojo). No llevan pin: la capa de marcas ya esta horneada.

        `verificar='agua'` comprueba, **sobre el PNG del mundo**, que el recorrido va por agua
        salvo los extremos. Es la unica comprobacion honesta: Natural Earth 50m no resuelve la
        bahia de Ceuta —a esa escala la costa es un bloque y `shapely` dice «tierra» en todo el
        istmo—, asi que lo que hay que verificar no es el poligono sino **lo que se dibuja**, que
        es lo que el espectador ve. Si el recorrido pasara por encima de la tierra dibujada, la
        linea diria que cruzaron por donde esta la valla, justo lo contrario del guion."""
        import numpy as np
        from PIL import Image as _I
        mu = self.mu
        pj, _, _ = MV.proyeccion(*mundos4.SPEC[self.n]['bbox'], mu.w)
        nombres = []
        for i, (lo, la) in enumerate(puntos):
            nm = '_ruta%d_%d' % (self.n, i)
            mu.pts[nm] = [round(v, 2) for v in pj(lo, la)]
            nombres.append(nm)
        if verificar == 'agua':
            base = np.asarray(_I.open(mu.base.filename if hasattr(mu.base, 'filename')
                                      else os.path.join(ARTE, 'mundo_%s.png'
                                                        % mundos4.SPEC[self.n]['nombre'])
                                      ).convert('RGB')).astype(int)
            es_agua = (base[:, :, 2] - base[:, :, 0]) > 25
            # Los segmentos de los EXTREMOS no se cuentan: el origen y el destino son ciudades y
            # estan en tierra por definicion (Fnideq y Ceuta). Lo que hay que demostrar es que el
            # TRAMO DE EN MEDIO va por agua, que es lo que dice el guion: «around the end of the
            # fence, through the water».
            segs = list(zip(puntos, puntos[1:]))
            k0 = saltar_extremos; k1 = len(segs) - saltar_extremos
            tot = moj = 0
            for si, ((l0, a0), (l1, a1)) in enumerate(segs):
                if not (k0 <= si < k1): continue
                x0, y0 = pj(l0, a0); x1, y1 = pj(l1, a1)
                pasos = max(2, int(math.hypot(x1 - x0, y1 - y0) / 4))
                for k in range(pasos + 1):
                    u = k / pasos
                    x, y = int(round(x0 + (x1 - x0) * u)), int(round(y0 + (y1 - y0) * u))
                    if not (0 <= x < base.shape[1] and 0 <= y < base.shape[0]): continue
                    tot += 1; moj += bool(es_agua[y, x])
            frac = moj / max(1, tot)
            print('   ruta pieza %d: %.0f %% del tramo de en medio va por agua DIBUJADA '
                  '(%d muestras, %d de %d segmentos)'
                  % (self.n, 100 * frac, tot, max(0, k1 - k0), len(segs)))
            if frac < tol:
                raise SystemExit('pieza %d: la ruta pasa por tierra dibujada (%.0f %% de agua, '
                                 'minimo %.0f %%). Mover los puntos.' % (self.n, 100 * frac, 100 * tol))
        mu.route(nombres, t0, t1, color=color or PR.ROJO, width=width, dotted=dotted, t_off=t_off)
        M.ev(t0, 'whoosh', 0.45)
        return nombres

    # ------------------------------------------------------------------ rig sobre el mapa
    def figura(self, nombre, t0, t1, sobre, mira=None, alto_rel=0.26, gestos=(), z=44):
        """Un rig DE PIE SOBRE EL MAPA, con peana y sombra de contacto.

        `sobre` es (lon, lat): donde apoya los pies. Generalizado de `_jurista` de `prueba_v4.py`.
        Sin la peana y la sombra el recorte flota y se lee como una calcomania pegada; y el rig se
        ancla por la ESQUINA SUPERIOR IZQUIERDA, no por los pies, asi que colocarlo a ojo da
        violaciones de la regla 1 (paso en `prueba_vida.py`, 14 seguidas)."""
        sc, mu = self.sc, self.mu
        pj, _, _ = MV.proyeccion(*mundos4.SPEC[self.n]['bbox'], mu.w)
        px, py = pj(*sobre) if not isinstance(sobre, (tuple, list)) or len(sobre) != 2 else pj(*sobre)
        rj = json.load(open(os.path.join(M.ELENCO, 'rig', nombre, 'rig.json'), encoding='utf-8'))
        tor = rj['piezas']['torso']
        z_medio = (sc.zoom(t0) + sc.zoom(t1)) / 2
        alto_pieza = (max(b[3] for b in rj['piezas'].values())
                      - min(b[1] for b in rj['piezas'].values()))
        esc = (H * alto_rel / z_medio) / alto_pieza      # px de MUNDO (en pantalla se multiplica z)

        ancho = int((tor[2] - tor[0]) * esc * 1.20)
        sh = Image.new('RGBA', (ancho + 90, 96), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse([45, 30, ancho + 45, 72], fill=(20, 16, 12, 104))
        sh = sh.filter(ImageFilter.GaussianBlur(9))
        so = M.Obj(sh, z=z - 4); so.name = 'sombra:' + nombre; so.bg = True; so.shadow = False
        so.x = M.Track(px); so.y = M.Track(py - 6); so.on, so.off = t0, t1
        so.a.set(t0, 0, 'hold'); so.a.set(t0 + 0.40, 1, 'io')
        so.a.set(t1 - 0.35, 1, 'hold'); so.a.set(t1, 0, 'io')
        sc.add(so)
        pe = PR.rect(max(24, int(ancho * 0.60)), 16, MV.PAPEL, r=4)
        po = M.Obj(pe, z=z - 3); po.name = 'peana:' + nombre; po.bg = True; po.shadow = False
        po.x = M.Track(px); po.y = M.Track(py - 2); po.on, po.off = t0, t1
        po.a = so.a
        sc.add(po)

        r = M.Rig(nombre, 0, 0, sc=esc, z=z, on=t0, off=t1)
        r.x = M.Track(px - (tor[0] + tor[2]) / 2 * esc)
        r.y = M.Track(py - tor[3] * esc)
        r.name = nombre
        if mira is not None:
            r.point_at(t0 + 1.0, self.P(mira) if isinstance(mira, str) else mira,
                       side='R', hold=min(2.6, max(1.0, t1 - t0 - 1.6)))
        r.nod(t0 + 0.5)
        for g in gestos:
            if t0 + 0.3 < g < t1 - 0.4: r.gesture(g)
        r.a.set(t0, 0, 'hold'); r.a.set(t0 + 0.45, 1, 'io')
        r.a.set(t1 - 0.40, 1, 'hold'); r.a.set(t1, 0, 'io')
        sc.add(r)

        # y ahora se COMPRUEBA que entra entero durante todo el plano, y se corre lo justo si no
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
            print('   %s corrido %.0f,%.0f px de mundo para que entre entero' % (nombre, peor[0], peor[1]))
        return r

    # ------------------------------------------------------------------ cierre
    def subtitulos(self, resaltar):
        self.sc.subtitulos(self.pal, estilo='banda', fy=0.885, resaltar=resaltar, ancho=0.88,
                           size=int(W * 0.060))

    def cerrar(self):
        for pl in self.planos: M.ev(pl[0], 'tick', 0.3)
        self.sc.dur = self.dur
        # regla 1 + el gancho va sobre MAPA (correccion 3): se comprueba, no se confia
        for t0, t1, tipo, _c0, _z0, _c1, _z1 in self.planos:
            if tipo == 'mesa' and t0 < HOOK - 0.01:
                raise SystemExit('pieza %d: hay MESA en %.2f s, dentro del gancho (< %.1f s). '
                                 'El gancho va sobre el MAPA en movimiento.' % (self.n, t0, HOOK))
        largo = [(pl[0], pl[1]) for pl in self.planos if pl[1] - pl[0] > 6.0]
        if largo: print('   AVISO: planos de mas de 6 s (ritmo.py los va a marcar): %s' % largo)
        fl = self._cortes_flojos()
        if fl:
            print('   AVISO pieza %d: %d cortes que no se leen como cortes (zoom y centro casi '
                  'iguales a los dos lados):' % (self.n, len(fl)))
            for t, k, r, d in fl:
                print('      t=%6.2f  %-12s  zoom x%.2f  centro %.2f anchos de ventana'
                      % (t, k, r, d))
        return self.sc


# ====================================================================== entradas
def build(n=None):
    n = int(n or os.environ.get('S12_PIEZA', 4))
    M.EVENTS.clear()
    import escenas4
    p = Pieza(n)
    escenas4.PARTITURA[n](p)
    return p.cerrar()


def _build_env():
    return build(int(os.environ.get('S12_PIEZA', 4)))


def salida(n):
    d = os.path.join(AQUI, 'shorts', DIRS[n], 'salida'); os.makedirs(d, exist_ok=True); return d


def cuadro(n, ts=None):
    sc = build(n)
    d = salida(n)
    ts = ts or [sc.dur * f for f in (0.03, 0.14, 0.30, 0.46, 0.62, 0.78, 0.93)]
    for i, tt in enumerate(ts):
        f = os.path.join(d, '_v4_cuadro_%02d.png' % i)
        sc.render(tt).convert('RGB').save(f)
        print('  t=%5.1f -> %s' % (tt, f))


def hoja(n):
    sc = build(n); d = salida(n)
    cols, rows = 4, 3
    cw = 300; ch = int(cw * H / W)
    q = Image.new('RGB', (cols * cw, rows * ch), (20, 20, 20))
    dr = ImageDraw.Draw(q)
    for i in range(cols * rows):
        tt = sc.dur * (i + 0.5) / (cols * rows)
        fr = sc.render(tt).convert('RGB').resize((cw, ch), Image.LANCZOS)
        q.paste(fr, ((i % cols) * cw, (i // cols) * ch))
        dr.text(((i % cols) * cw + 8, (i // cols) * ch + 6), '%.1fs' % tt, fill=(255, 220, 120),
                font=PR.FONTC(20))
    f = os.path.join(d, '_qc_coreo.jpg'); q.save(f, quality=90); print('hoja ->', f)
    tw = 405; th = int(tw * H / W)
    sc.render(sc.dur * 0.45).convert('RGB').resize((tw, th), Image.LANCZOS).save(
        os.path.join(d, '_qc_405.png'))
    print('405 px ->', os.path.join(d, '_qc_405.png'))


def check(n):
    import sync
    sc = build(n); d = salida(n)
    bad = sc.check_framing(0, sc.dur, step=0.20)
    seen = {}
    for t, nm, bb, wn in bad: seen.setdefault(nm, []).append(t)
    for nm, ts in sorted(seen.items(), key=lambda x: -len(x[1])):
        print('  CORTADO %-30s %3d muestras  t=%.1f..%.1f' % (nm, len(ts), min(ts), max(ts)))
    print('violaciones de encuadre: %d' % len(bad))
    rep = sc.report(0, sc.dur)
    print('ritmo (eventos): %d cortes (%.1f/min), huecos > 6 s: %s'
          % (rep['cortes'], rep['cortes_por_min'], rep['huecos'] or 'ninguno'))
    r = sync.auditar(sc, os.path.join(AQUI, 'shorts', DIRS[n], 'audio', 'tiempos.json'),
                     out=os.path.join(AQUI, 'shorts', DIRS[n], '_qc_sync'), dur=sc.dur, paso=1)
    print('sync:', {k: v for k, v in r.items() if not k.startswith('_')})
    return len(bad), r


def render(n):
    os.environ['S12_PIEZA'] = str(n)
    d = salida(n)
    f = os.path.join(d, 'cuerpo.mp4')
    wav = os.path.join(AQUI, 'shorts', DIRS[n], 'audio', 'voz.wav')
    sc = build(n)
    M.render('coreo4', '_build_env', sc.dur, f, audio=wav,
             frames=os.path.join(AQUI, 'shorts', DIRS[n], '_frames_v4'))
    print('OK', f)


if __name__ == '__main__':
    modo = sys.argv[1] if len(sys.argv) > 1 else 'check'
    nn = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    os.environ['S12_PIEZA'] = str(nn)
    {'cuadro': cuadro, 'hoja': hoja, 'check': check, 'render': render}[modo](nn)
