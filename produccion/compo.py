# -*- coding: utf-8 -*-
"""COMPOSITOR DECLARATIVO (motor v4). De un guion ANOTADO a una coreografia completa y CORRECTA POR
CONSTRUCCION. Manual: `produccion/COMPO.md`. 0 creditos.

QUE RESUELVE. El motor v4 garantiza lo CORRECTO (nada cortado, nada vacio, cifras en pantalla,
puntos exactos, ritmo). No garantiza la COMPOSICION: que cada cuadro tenga jerarquia, se lea en un
telefono y la imagen diga lo que dice la voz. Eso dependia de mirar la hoja de contacto linea por
linea y de escribir 500-1000 lineas de partitura a mano por pieza. Aca la partitura se DEDUCE de un
vocabulario cerrado de verbos:

    A: On the twenty-ninth of June, a Spanish court published a ruling. Thirty-two days later, ...
    V: MAPA(Ceuta, abrir) · DOC(sentencia, "29 · VI · 2026") @ "published" · CIFRA(49,000, "IN 24 HOURS") @ "forty-nine"

y el compositor elige el hueco, el tamano, el color, la camara, la entrada, la vida y el relevo. Las
reglas de composicion las verifica `compo.check(sc, info)`, que ABORTA si alguna falla.

    import compo
    sc, info = compo.build('guion_v.md', 'audio/tiempos.json', 'audio/_palabras.json',
                           formato='vertical', mundos='mundo.json', serie=(4, 4))
    compo.check(sc, info)

    python produccion/compo.py <dir_produccion> --pieza 4 [--check|--render|--hoja]

NO TOCA `produccion/motor.py`. Todo lo que hace falta y el motor no tiene (rejilla de huecos, HUD con
el cuerpo medido, MESA sin hoja rayada, rig de pie sobre el mapa con peana, secuencias, rutas
verificadas contra el agua dibujada) vive aca. Generaliza lo que la S12 tenia a mano en
`videos/S12_recibos/coreo4.py` + `escenas4.py`.
"""
import json, math, os, re, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
if AQUI not in sys.path: sys.path.insert(0, AQUI)
RAIZ = os.path.abspath(os.path.join(AQUI, '..'))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import motor as M
import props as PR
import mapa_v2 as MV

NL = chr(10)

# ============================================================== 1. FORMATO Y REJILLA
FORMATOS = {'vertical': (1080, 1920), 'horizontal': (1920, 1080)}
# La rejilla no son cajas fijas: son LIMITES y BANDAS PREFERIDAS. El hueco real lo calcula
# `Compo._hueco` contra lo que ya esta vivo en pantalla, que es lo unico que evita que dos carteles
# se pisen cuando el documento ocupa medio cuadro. Dibujo ASCII en COMPO.md §3.
LIMITES = {'vertical': (0.095, 0.830), 'horizontal': (0.105, 0.845)}     # bajo el rotulo / sobre el subtitulo
PREFERIDAS = {'vertical': {'alto': 0.232, 'bajo': 0.672},
              'horizontal': {'alto': 0.330, 'bajo': 0.690}}
COLUMNAS = {'vertical': {'centro': 0.500}, 'horizontal': {'izq': 0.230, 'der': 0.770}}
TERCIOS = {'vertical': {'izq': (0.270, 0.470), 'centro': (0.500, 0.470), 'der': (0.730, 0.470)},
           'horizontal': {'izq': (0.215, 0.545), 'centro': (0.500, 0.500), 'der': (0.785, 0.545)}}
ROTULO_FY = {'vertical': 0.072, 'horizontal': 0.078}
SUB_FY = {'vertical': 0.885, 'horizontal': 0.905}
DOC_FY = {'vertical': 0.440, 'horizontal': 0.425}
DOC_ALTO = {'vertical': 0.500, 'horizontal': 0.520}

# Tamanos minimos, medidos a 405 px de ancho de telefono. El cuerpo va en fraccion del ALTO del
# cuadro; el prop y el rig, en fraccion del ancho y del alto. Por debajo no se lee y `check` aborta.
MIN_CUERPO = {'cifra': 0.080, 'tarjeta': 0.042, 'pie': 0.026, 'rotulo': 0.026}
MIN_PROP_W = 0.14
MIN_RIG_H = {'vertical': 0.26, 'horizontal': 0.42}
MAX_SOLAPE = 0.08          # fraccion del area del menor de los dos elementos
MAX_ELEM = 4               # cifra + tarjeta + objeto/rig + subtitulo
MAX_PALABRAS = 4           # por linea de tarjeta
MAX_PLANO = 5.0            # s sin corte de contenido
VIDA_MIN = 2.2
VIDA_MAX = 9.0             # a los 12 s `sync.py` lo marca TEXTO_VIEJO, con razon
RELEVO = 0.25              # s de fundido cuando otro objeto ocupa el mismo slot
HOOK = 3.5                 # lo que dura la tarjeta de gancho de un short

# Clases de plano. El zoom es "ancho del cuadro / ancho de la ventana" en px de mundo; los valores
# estan medidos sobre mundos de ~2600 px vistos en vertical y se escalan al formato real.
ZOOM = {'abrir': (0.05, 0.36), 'medio': (1.00, 1.30), 'cerrar': (1.85, 2.40)}
ROJO, OCRE, TINTA, PAPEL = PR.ROJO, PR.OCRE, PR.TINTA, PR.PAPEL
OSCURO_MESA = 0.58         # `Mundo.dark` en los planos de MESA: el mapa da un paso atras, no se va
PRIO_ROJO = {'cifra': 0, 'ruta': 1, 'sello': 2, 'tarjeta': 3}
MIN_TIERRA = 0.40          # fraccion de la ventana con tierra (o con contenido) en un plano de mapa
MIN_TIERRA_MUNDO = 0.35    # por debajo de esto, el bbox del mundo esta mal elegido
MIN_RIG_S = 6.0            # segundos seguidos que un rig tiene que estar en pantalla

# TEXTO HORNEADO EN LOS PROPS. Un PNG con letras dice cosas que `sync.py` no puede leer (lee el
# NOMBRE del objeto, no sus pixeles): la pieza 3 de la S12 enseno un contrato «LEASE 99 YEARS»
# mientras la voz decia «same ten years» y no lo vio nadie. Todo prop con texto se declara aca (o en
# un `prop_<nombre>.txt` al lado del PNG) y `check` exige que cada palabra y cada cifra esten
# dichas en la linea, en el beat o en la hoja de fuentes.
TEXTOS_PROPS = {
    'sentencia': 'TRIBUNAL SUPREMO · 29 · VI · 2026 · FIRME',
    'resolucion': 'RESOLUCION',
    'hotel': 'HOTEL',
    'poliza': 'POLICY', 'formulario': 'FORM', 'manual': 'MANUAL',
    'sello_loss': 'LOSS', 'sello_settled': 'SETTLED', 'sello_noprice': 'NO PRICE',
    'sello_paid': 'PAID', 'sello_same': 'SAME', 'sello_x': 'X',
    'cartel_sky': 'SKY CLOSED',
    'tab_fleet': 'FLEET', 'tab_drone': 'DRONE', 'tab_country': 'COUNTRY',
    'cerca': '', 'gota': '', 'lupa': '', 'moneda': '', 'regla': '', 'martillo_juez': '',
    'lingote': '', 'diamante': '', 'balanza': '', 'barrera': '', 'escudo': '', 'sobre': '',
    'recibo': 'U.S. TREASURY DEBT TO THE PENNY TOTAL $40,046,178,322,792.78 SEPT 11, 2026',
    'bono_0': 'U.S. TREASURY BOND $100 2 PER CENT', 'bono_1': 'U.S. TREASURY BOND $100 2 PER CENT',
    'bono_2': 'U.S. TREASURY BOND $100 2 PER CENT', 'bono_3': 'U.S. TREASURY BOND $100 2 PER CENT',
}
# Marca y llamada a la accion: no lo dice la voz y no tiene que decirlo.
TEXTO_LIBRE = {'paper', 'trail', 'follow', 'the', 'subscribe', 'like', 'part', 'of', 'comments',
               'comment', 'next', 'stay', 'and', 'a', 'an', 'to', 'in', 'on', 'at', 'is', 'it',
               'for', 'by', 'was', 'were', 'not', 'no', 'one', 'two', 'per', 'cent', 'percent'}
# Un documento tiene NOMBRE. «REPORT», «DECREE», «DOCUMENT» a secas no dicen nada y son la puerta
# por la que entra un papel que no es el papel del que habla la voz.
PLACEHOLDERS = {'report', 'decree', 'document', 'doc', 'paper', 'file', 'letter', 'form',
                'informe', 'documento', 'decreto', 'papel', 'carta', 'ruling', 'sentencia'}
ESCRITORIO = [('lupa', 0.130, 0.820, 0.078), ('moneda', 0.888, 0.848, 0.042),
              ('regla', 0.858, 0.150, 0.022)]
VERBOS = ('MAPA', 'MESA', 'PINTA', 'RUTA', 'CIFRA', 'TARJETA', 'SELLO', 'DOC', 'PROP',
          'PERSONAJE', 'SECUENCIA', 'ROTULO')


# ============================================================== 2. LECTURA DEL GUION ANOTADO
def _norm(s):
    s = str(s).replace('‑', '-').replace('‐', '-').replace('–', '-')
    s = s.replace('—', ' ').replace('’', "'")
    return re.sub(r'[^a-z0-9]+', '', s.lower())


def _norm_linea(s):
    s = str(s).replace('‑', '-').replace('‐', '-').replace('–', '-')
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()


def _partir(s, sep):
    """Parte `s` por `sep` respetando comillas y parentesis."""
    out, cur, q, depth = [], '', False, 0
    for ch in s:
        if ch == '"': q = not q
        if not q:
            if ch in '([': depth += 1
            elif ch in ')]': depth -= 1
            if depth == 0 and ch == sep:
                out.append(cur); cur = ''; continue
        cur += ch
    out.append(cur)
    return [x.strip() for x in out if x.strip()]


def _args(s):
    """Parte los argumentos de un verbo. Una coma ENTRE DIGITOS no separa: `49,000` y `+2,400%` son
    UN argumento. Es lo que permite escribir `CIFRA(49,000, "IN 24 HOURS")` sin comillas."""
    out, cur, q = [], '', False
    for i, ch in enumerate(s):
        if ch == '"': q = not q; cur += ch; continue
        if ch == ',' and not q:
            if i and s[i - 1].isdigit() and i + 1 < len(s) and s[i + 1].isdigit():
                cur += ch; continue
            out.append(cur); cur = ''; continue
        cur += ch
    out.append(cur)
    return [x.strip() for x in out if x.strip()]


def _desnuda(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == '"' and v[-1] == '"': v = v[1:-1]
    return v.replace('|', NL)


_RE_VERBO = re.compile(r'^([A-Z_]+)\s*(?:\((.*)\))?\s*$', re.S)
_RE_ANCLA = re.compile(r'@\s*(?:"([^"]+)"|([^\s"+-]+))\s*([+-]\s*[0-9.]+)?\s*$')


def _parse_verbo(txt):
    """`CIFRA(49,000, "IN 24 HOURS") @ "forty-nine" +0.2` -> dict."""
    anc, off = None, 0.0
    m = _RE_ANCLA.search(txt)
    if m:
        anc = m.group(1) or m.group(2)
        if m.group(3): off = float(m.group(3).replace(' ', ''))
        txt = txt[:m.start()].strip()
    mm = _RE_VERBO.match(txt.strip())
    if not mm: raise SystemExit('compo: no entiendo el verbo %r' % txt)
    nombre = mm.group(1).upper()
    if nombre not in VERBOS:
        raise SystemExit('compo: verbo desconocido %r (vocabulario: %s)' % (nombre, ', '.join(VERBOS)))
    pos, kw = [], {}
    for a in _args(mm.group(2) or ''):
        if re.match(r'^[A-Za-z_ñÑ]+\s*=', a.strip()) and not a.strip().startswith('"'):
            k, v = a.split('=', 1)
            kw[_norm(k).replace('ñ', 'n')] = _desnuda(v)
        else:
            pos.append(_desnuda(a))
    return {'verbo': nombre, 'args': pos, 'kw': kw, 'ancla': anc, 'off': off, 'fuente': txt.strip()}


def leer_guion(ruta):
    """Lee un guion anotado. Devuelve {titulo, gancho, rojo, serie, resaltar, mundo, lineas}.

      `A: ...` / `**A:** ...`    una linea de voz (el orden manda)
      `V: ...`                   su anotacion (puede haber varias por linea; se concatenan)
      `## BEAT ...`              separador de beat en un episodio
      ```mundo {json} ```        el mundo (o un `mundo.json` al lado)
      `SERIE 4/4` `RESALTAR a,b` cabecera opcional
    """
    txt = open(ruta, encoding='utf-8').read()
    G = {'titulo': '', 'gancho': [], 'rojo': None, 'serie': None, 'resaltar': [], 'mundo': None,
         'lineas': [], 'n_anot': 0, 'texto_ok': []}
    m = re.search(r'```\s*mundo\s*(.*?)```', txt, re.S)
    if m:
        G['mundo'] = json.loads(m.group(1)); txt = txt[:m.start()] + txt[m.end():]
    m = re.search(r'[Gg]ancho[^\n]*\n+```\s*\n(.*?)```', txt, re.S)
    if m:
        G['gancho'] = [l.strip() for l in m.group(1).strip().split('\n') if l.strip()][:3]
        r = re.search(r'la\s+(\d)\s+en\s+rojo', m.group(0))
        if r: G['rojo'] = int(r.group(1)) - 1        # `tarjeta_hook` indexa desde 0
    beat, beat_tit = -1, ''
    for ln in txt.split('\n'):
        s = ln.strip()
        if s.startswith('# ') and not G['titulo']: G['titulo'] = s[2:].strip()
        if s.startswith('## '):
            beat += 1
            beat_tit = re.sub(r'^##\s*(BEAT\s*\d+\s*[·.—-]\s*)?', '', s)
            beat_tit = re.split(r'[·|]', beat_tit)[0].strip()
            continue
        if s.upper().startswith('SERIE '):
            n = re.findall(r'\d+', s)
            if len(n) >= 2: G['serie'] = (int(n[0]), int(n[1]))
            continue
        if s.upper().startswith('RESALTAR '):
            G['resaltar'] += [x.strip() for x in s[9:].split(',') if x.strip()]; continue
        if s.upper().startswith('TEXTO_OK '):
            # la unica salida de la regla TEXTO_NO_DICHO, y a la vista: palabras que estan en
            # pantalla, no las dice la voz y no figuran literales en la hoja de fuentes, pero el
            # autor justifica (el sello FIRME de una sentencia, «DAY» en el gancho por «24 hours»)
            G['texto_ok'] += [x.strip().lower() for x in s[9:].split(',') if x.strip()]; continue
        c = re.sub(r'^\*\*([AV]):\*\*', r'\1:', s)
        if c.startswith('A:'):
            G['lineas'].append({'texto': c[2:].strip(), 'verbos': [], 'beat': max(0, beat),
                                'beat_titulo': beat_tit})
            continue
        if c.startswith('V:') and G['lineas']:
            cuerpo = c[2:].strip()
            if cuerpo.startswith('[') or cuerpo.startswith('`'):
                continue                       # anotacion del plan viejo (`V: [MAP] ...`)
            G['lineas'][-1]['verbos'] += [_parse_verbo(v) for v in _partir(cuerpo, '·')]
            G['n_anot'] += 1
    return G


class Palabras:
    """`audio/_palabras.json` = [[palabra, t0, t1], ...]. Es lo que ata la imagen a la VOZ: nada se
    ancla «al principio de la linea» salvo que la anotacion no diga otra cosa."""

    def __init__(self, lista):
        self.pal = [(str(w), float(a), float(b)) for w, a, b in lista]
        self.norm = [_norm(w) for w, _, _ in self.pal]

    def t(self, patron, desde=0.0, hasta=1e9, avisos=None, linea=-1):
        q = _norm(patron)
        if not q: return None
        # La segunda vuelta se estira 4 s y NO MAS. Sin ese tope, un ancla que la transcripcion no
        # tiene (`_palabras.json` del ep. 09 escribe «1 . 13 trillion», no «one point one three»)
        # encontraba esa palabra treinta segundos despues y mandaba la cifra a otro beat.
        for ventana in ((desde, hasta), (desde, hasta + 4.0)):
            for i, (w, a, b) in enumerate(self.pal):
                if not (ventana[0] - 1e-6 <= a <= ventana[1]): continue
                n = self.norm[i]
                if n == q or n.startswith(q) or (len(n) >= 4 and q.startswith(n)): return a
        if avisos is not None:
            avisos.append('linea %d: la palabra %r no esta en _palabras.json cerca de esa linea; '
                          'el objeto entra al empezar la linea (mira la transcripcion: puede estar '
                          'escrita en cifras)' % (linea, patron))
        return None


# ============================================================== 3. EL MUNDO
def _color(v):
    """Un color puede venir como nombre de ROL (`institucion`, lo correcto: el color narra un rol,
    no una nacionalidad), como nombre de la paleta o como [r, g, b]."""
    if isinstance(v, (list, tuple)) and len(v) == 3: return tuple(int(x) for x in v)
    s = str(v).lower()
    if s in MV.ROL: return MV.ROL[s]
    return {'rojo': ROJO, 'ocre': OCRE, 'tinta': TINTA, 'papel': PAPEL, 'gris': PR.GRIS,
            'azul': PR.AZUL, 'verde': PR.VERDE, 'blanco': PR.BLANCO}.get(s, ROJO)


def mundo_de(spec, out_dir, force=False):
    """`spec` (dict de `mundo.json`) -> `motor.Mundo` cacheado en disco, con los `puntos` extra ya
    proyectados. La regla 24 la comprueba `mapa_v2.mundo` y aborta si un sitio se corre 3 px."""
    capas = {k: (v[0], _color(v[1]), int(v[2]) if len(v) > 2 else 226)
             for k, v in (spec.get('capas') or {}).items()}
    cgj = {}
    for k, v in (spec.get('capas_geojson') or {}).items():
        ruta = v[0] if os.path.isabs(v[0]) else os.path.join(RAIZ, v[0])
        cgj[k] = (ruta, v[1], _color(v[2]), int(v[3]) if len(v) > 3 else 226)
    pins = {}
    for k, v in (spec.get('pins') or {}).items():
        o = dict(v)
        if 'color' in o: o['color'] = _color(o['color'])
        pins[k] = o
    mu = MV.mundo(spec['nombre'], tuple(spec['bbox']), int(spec['w']),
                  roles=spec.get('roles'), sitios=spec.get('sitios'),
                  agua=[tuple(a) for a in spec.get('agua', ())],
                  rotulos_extra=[tuple(r) for r in spec.get('rotulos_extra', ())],
                  capas=capas or None, capas_geojson=cgj or None,
                  etiquetas=bool(spec.get('etiquetas', False)),
                  marcas=bool(spec.get('marcas', True)),
                  pins_opciones=pins or None, out_dir=out_dir, force=force)
    # Puntos auxiliares (el extremo de la valla, los saltos de una ruta, donde se para un rig): no
    # son sitios rotulados, pero son px de mundo EXACTOS, de lon/lat, como manda la regla 24.
    pj, _, _ = MV.proyeccion(*spec['bbox'], mu.w)
    mu.puntos = {k: (round(pj(lo, la)[0], 2), round(pj(lo, la)[1], 2))
                 for k, (lo, la) in (spec.get('puntos') or {}).items()}
    mu.spec = spec
    fr = tierra_mundo(mu)[1]
    if fr < MIN_TIERRA_MUNDO:
        print('  AVISO: el bbox de %s tiene solo %.0f %% de tierra. Un mundo casi todo agua da '
              'planos de mar vacio con un pin; achicar el bbox o correrlo hacia la costa.'
              % (spec['nombre'], 100 * fr), flush=True)
    return mu


def tierra_mundo(mu, red=4):
    """(mascara de tierra reducida, fraccion de tierra del mundo, integral). Se cachea en el Mundo.

    La tierra se lee del PNG por color (el agua es lo unico con azul muy por encima del rojo), no de
    los poligonos: lo que importa es lo que se DIBUJA, que es lo que se ve."""
    if getattr(mu, '_tierra', None) is None:
        a = np.asarray(mu.base.convert('RGB'))[::red, ::red].astype(np.int16)
        m = ~((a[:, :, 2] - a[:, :, 0]) > 25)
        integ = np.zeros((m.shape[0] + 1, m.shape[1] + 1), np.int32)
        integ[1:, 1:] = np.cumsum(np.cumsum(m.astype(np.int32), axis=0), axis=1)
        mu._tierra = (m, float(m.mean()), integ, red)
    return mu._tierra[0], mu._tierra[1], mu._tierra[2]


def frac_tierra(mu, ventana, red=4):
    """Fraccion de TIERRA dentro de una ventana de camara (px de mundo). O(1) con la integral."""
    _m, _f, integ = tierra_mundo(mu, red)
    h, w = integ.shape[0] - 1, integ.shape[1] - 1
    x0 = max(0, min(int(ventana[0] / red), w - 1)); y0 = max(0, min(int(ventana[1] / red), h - 1))
    x1 = max(x0 + 1, min(int(ventana[2] / red), w)); y1 = max(y0 + 1, min(int(ventana[3] / red), h))
    s = integ[y1, x1] - integ[y0, x1] - integ[y1, x0] + integ[y0, x0]
    return float(s) / max(1, (x1 - x0) * (y1 - y0))


# ============================================================== 4. EL COMPOSITOR
class Compo:
    """Convierte la lista de verbos en objetos colocados. Lo usa `build()`."""

    def __init__(self, mu, formato, T, pal, G, serie=None, base=None):
        self.mu, self.formato, self.T, self.pal, self.G = mu, formato, T, pal, G
        self.W, self.H = FORMATOS[formato]
        self.sc = M.Scene(mu, size=(self.W, self.H), v4=True)
        self.dur = float(T['dur'])
        self.sc.dur = self.dur
        self.zmin = max(self.W / mu.w, self.H / mu.h)
        # el zoom de las clases esta medido sobre un mundo de 2600 px visto en vertical
        self.kz = (self.W / mu.w) / (1080.0 / 2600.0)
        self.base = base or os.getcwd()
        self.serie = serie
        self.avisos = []
        self.planos = []       # (t0, t1, tipo, c0, z0, c1, z1, sitio)
        self.objetos = []      # los metadatos que mira `check`
        self.rigs = []
        self.mesas = []
        self.rojo = []         # intervalos con el UNICO rojo concedido
        self.rojo_mapa = []    # intervalos en que el compositor pinta rojo SOBRE el mapa (rutas)
        self.capas_on = {}

    # ---------------------------------------------------------- geometria
    def P(self, nombre):
        if nombre in self.mu.pts: return self.mu.P(nombre)
        if nombre in getattr(self.mu, 'puntos', {}): return self.mu.puntos[nombre]
        raise SystemExit('compo: el sitio %r no esta en el mundo (sitios: %s | puntos: %s)'
                         % (nombre, ', '.join(sorted(self.mu.pts))[:140],
                            ', '.join(sorted(getattr(self.mu, 'puntos', {})))[:100]))

    def pantalla(self, xy, t):
        x0, y0, x1, y1 = self.sc.window(t)
        return ((xy[0] - x0) / max(1e-6, x1 - x0) * self.W,
                (xy[1] - y0) / max(1e-6, y1 - y0) * self.H)

    def caja_mundo(self, obj, t0, t1, paso=0.4):
        """Union de los rectangulos de PANTALLA que ocupa un objeto del mundo mientras vive. Es
        conservador a proposito: la camara se mueve y el objeto con ella."""
        xs, ys = [], []; t = t0 + 0.05
        while t < t1:
            b = obj.bbox(t)
            if b is not None:
                a = self.pantalla((b[0], b[1]), t); c = self.pantalla((b[2], b[3]), t)
                xs += [a[0], c[0]]; ys += [a[1], c[1]]
            t += paso
        if not xs: return (0, 0, 0, 0)
        return (min(xs), min(ys), max(xs), max(ys))

    def caja_pin(self, sitio, t):
        """Rectangulo de pantalla del punto y el rotulo de un sitio. El texto NUNCA va encima:
        tapar el sitio del que habla la voz es lo peor que puede hacer un cartel."""
        try: p = self.P(sitio)
        except SystemExit: return None
        op = (getattr(self.mu, 'spec', {}).get('pins') or {}).get(sitio, {})
        r = float(op.get('r', max(6, self.mu.w * 0.0042)))
        s = float(op.get('size', max(22, self.mu.w * 0.0145)))
        txt = str(op.get('texto') or sitio)
        L = max(4 * r, len(txt) * 0.55 * s)
        anc = op.get('anc', 'lm'); o = op.get('off', (1.9, -0.25))
        cx = p[0] + o[0] * r + (-L / 2 if anc == 'rm' else L / 2)
        caja = (min(p[0] - 2 * r, cx - L / 2), p[1] - 1.5 * s,
                max(p[0] + 2 * r, cx + L / 2), p[1] + 1.5 * s)
        a = self.pantalla((caja[0], caja[1]), t); b = self.pantalla((caja[2], caja[3]), t)
        return (a[0], a[1], b[0], b[1])

    # ---------------------------------------------------------- camara
    def _z(self, clase, i):
        if clase == 'abrir': return (self.zmin + 0.04, self.zmin + 0.30 + 0.14 * (i % 2))
        a, b = ZOOM[clase]
        return (a * self.kz, b * self.kz)

    def ventana_de(self, c, z):
        z = max(z, self.zmin); w, h = self.W / z, self.H / z
        return (c[0] - w / 2, c[1] - h / 2, c[0] + w / 2, c[1] + h / 2)

    def hacia_tierra(self, c, z, sitio=None):
        """Corre el centro del plano hasta que la ventana tenga al menos `MIN_TIERRA` de tierra.

        Es la regla del mar vacio: la pieza 1 de la S12 tenia 9 de 16 cuadros con un 70 % de agua y
        un pin, porque el bbox del Golfo es casi todo mar y la costa corre por el borde. El
        compositor no puede elegir un encuadre asi ni aunque el sitio sea exacto."""
        mejor = (frac_tierra(self.mu, self.ventana_de(c, z)), c)
        if mejor[0] >= MIN_TIERRA: return c, mejor[0]
        an, al = self.W / max(1e-6, z), self.H / max(1e-6, z)
        for r in (0.18, 0.34, 0.5):
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0), (-0.7, -0.7), (0.7, -0.7),
                           (-0.7, 0.7), (0.7, 0.7)):
                cc = self._sujetar((c[0] + dx * an * r, c[1] + dy * al * r), z)
                f = frac_tierra(self.mu, self.ventana_de(cc, z))
                if f > mejor[0]: mejor = (f, cc)
            if mejor[0] >= MIN_TIERRA: break
        return mejor[1], mejor[0]

    def planificar(self, eventos):
        """Un plano = un corte + UN viaje motivado. Cada `MAPA`/`DOC`/`MESA` abre plano; un plano
        largo se parte para que no haya nunca mas de `MAX_PLANO` s sin corte de contenido."""
        cortes = []
        for e in eventos:
            if e['verbo'] not in ('MAPA', 'MESA', 'DOC'): continue
            cortes.append({'t': e['t'], 'tipo': 'mapa' if e['verbo'] == 'MAPA' else 'mesa',
                           'sitio': e['args'][0] if (e['verbo'] == 'MAPA' and e['args']) else None,
                           'clase': e['args'][1] if (e['verbo'] == 'MAPA' and len(e['args']) > 1)
                           else None})
        if not cortes or cortes[0]['t'] > 0.05:
            cortes.insert(0, {'t': 0.0, 'tipo': 'mapa', 'sitio': None, 'clase': 'abrir'})
        # LA CAMARA VA AL PERSONAJE. Si el plano apunta a otro sitio, el rig queda contra el borde,
        # el ajuste de encuadre lo empuja 600 px y termina de pie sobre el mar (pasado real de la
        # primera corrida). El sitio del plano donde entra un rig es el sitio del rig.
        for e in eventos:
            if e['verbo'] != 'PERSONAJE': continue
            sob = e['kw'].get('sobre') or (e['args'][1] if len(e['args']) > 1 else None)
            if not sob: continue
            prev = [c for c in cortes if c['tipo'] == 'mapa' and -1.2 <= e['t'] - c['t'] <= 1.2]
            if prev: prev[-1]['sitio'] = sob
            else: cortes.append({'t': e['t'], 'tipo': 'mapa', 'sitio': sob, 'clase': 'medio'})
        cortes.sort(key=lambda c: c['t'])
        fus = [cortes[0]]                      # dos marcas casi juntas son UN corte
        for c in cortes[1:]:
            if c['t'] - fus[-1]['t'] < 0.55:
                for k, v in c.items():
                    if k != 't' and v is not None: fus[-1][k] = v
            else: fus.append(c)
        anclas = sorted(set(round(e['t'], 3) for e in eventos))
        out = []
        for i, c in enumerate(fus):
            t1 = fus[i + 1]['t'] if i + 1 < len(fus) else self.dur
            if t1 - c['t'] <= MAX_PLANO: out.append(dict(c, t1=t1)); continue
            # El corte se busca en un ANCLA (un verbo motiva el corte), pero acotado a
            # `MAX_PLANO`: buscar el ancla mas cercana al reparto ideal sin ese tope dejaba los
            # cortes amontonados al principio y un ultimo tramo de 8 s sin cortar.
            bordes = [c['t']]
            while t1 - bordes[-1] > MAX_PLANO:
                resto = t1 - bordes[-1]
                ideal = bordes[-1] + resto / max(1, round(resto / (MAX_PLANO - 0.5)))
                ideal = min(ideal, bordes[-1] + MAX_PLANO - 0.2)
                cand = [a for a in anclas
                        if bordes[-1] + 1.2 < a < min(t1 - 1.0, bordes[-1] + MAX_PLANO)]
                nb = min(cand, key=lambda a: abs(a - ideal)) if cand else ideal
                bordes.append(max(nb, bordes[-1] + 1.0))
            bordes.append(t1)
            for k in range(len(bordes) - 1):
                cc = dict(c, t=bordes[k], t1=bordes[k + 1])
                if k: cc['clase'] = None
                out.append(cc)
        # La clase por defecto ALTERNA abierto/cerrado. Dos planos de mapa seguidos con el mismo
        # encuadre no se leen como un corte (la camara salta, la pantalla no cambia) y `ritmo.py`
        # los cuenta —con razon— como un plano solo.
        ult = None
        for i, c in enumerate(out):
            if not c['clase']: c['clase'] = 'abrir' if ult in ('cerrar', 'medio') else 'cerrar'
            ult = c['clase']
            if not c['sitio']:
                c['sitio'] = next((d['sitio'] for d in reversed(out[:i + 1]) if d['sitio']), None) \
                             or (list(self.mu.pts)[0] if self.mu.pts else None)
        # LA RESERVA DEL PERSONAJE. Un rig no puede reescalarse (las piezas se redimensionan al
        # construirlo) ni moverse del sitio donde apoya los pies: si en medio de sus 6 s la camara
        # abre a la mitad de zoom o se va a otro pais, el rig se queda en el 17 % del alto o
        # directamente fuera de la ventana. Asi que los planos de esa ventana comparten CLASE y
        # SITIO. La reserva se corta en el primer `MAPA`/`DOC` que pida otra cosa: ahi el
        # compositor no decide por el guion, avisa y `check` marca el rig corto.
        for e in eventos:
            if e['verbo'] != 'PERSONAJE': continue
            sob = e['kw'].get('sobre') or (e['args'][1] if len(e['args']) > 1 else None)
            fin = min(self.dur, e['t'] + MIN_RIG_S + 1.6)
            for c in out:
                if c['t'] <= e['t'] + 0.3: continue
                if c['tipo'] != 'mapa' or (sob and c['sitio'] and c['sitio'] != sob):
                    fin = min(fin, c['t']); break
            dentro = [c for c in out if c['t'] < fin - 0.05 and c['t1'] > e['t'] and c['tipo'] == 'mapa']
            e['ventana_rig'] = (e['t'], fin)
            if not dentro: continue
            clase = dentro[0]['clase']
            for c in dentro[1:]:
                if c['clase'] != clase or c['sitio'] != dentro[0]['sitio']:
                    self.avisos.append('plano de %.2f s: %s/%s -> %s/%s para que el personaje se '
                                       'quede del mismo tamano y en el cuadro'
                                       % (c['t'], c['clase'], c['sitio'], clase, dentro[0]['sitio']))
                c['clase'] = clase; c['sitio'] = dentro[0]['sitio']; c['fijo'] = True
        self._emitir(out)

    def _emitir(self, planos):
        prev = None
        for i, c in enumerate(planos):
            z0, z1 = self._z(c['clase'], i)
            p = self.P(c['sitio']) if c['sitio'] else (self.mu.w / 2, self.mu.h / 2)
            if c.get('fijo') and self.formato == 'horizontal':
                # con un personaje en pantalla la camara se corre para que el rig caiga en el
                # tercio izquierdo: en 16:9 el texto necesita una columna libre al lado
                p = (p[0] + self.W / max(1e-6, (z0 + z1) / 2) * 0.20, p[1])
            sg = 1 if i % 2 == 0 else -1
            sv = 1 if (i // 2) % 2 == 0 else -1
            anc = self.W / max(1e-6, (z0 + z1) / 2); alt = self.H / max(1e-6, (z0 + z1) / 2)
            # El viaje recorre un 30 % de la ventana. Con un personaje en pantalla se baja al 12 %:
            # el rig no se mueve del sitio, y si la camara lo pasea, su caja barre medio cuadro y no
            # queda columna libre para el texto. El movimiento lo pone el propio rig.
            kv = 0.12 if c.get('fijo') else 0.30
            c0 = self._sujetar((p[0] + sg * anc * kv, p[1] + sv * alt * kv * 0.53), z0)
            c1 = self._sujetar((p[0] - sg * anc * kv * 0.2, p[1] - sv * alt * kv * 0.13), z1)
            if math.hypot(c1[0] - c0[0], c1[1] - c0[1]) < anc * 0.12:
                c0 = self._sujetar((p[0] - sg * anc * 0.32, p[1] - sv * alt * 0.18), z0)
            if prev is not None and self._flojo(prev, (c0, z0, c['tipo'])):
                if c.get('fijo'):
                    # El zoom esta reservado por un rig: no se puede separar el corte moviendo el
                    # zoom ni saltando medio cuadro (el personaje se iria de la ventana). Se corre
                    # el encuadre un tercio y se acepta que el corte lo lea el CONTENIDO: el rig
                    # gesticula y las tarjetas cambian. `ritmo.py` es el juez.
                    d = anc * 0.30 * (1 if c0[0] <= prev[0][0] else -1)
                    c0 = self._sujetar((prev[0][0] + d, c0[1]), z0 * 0.86)
                    self.avisos.append('corte de %.2f s dentro de un plano con personaje: se '
                                       'separa por encuadre, no por zoom' % c['t'])
                else:
                    z0, z1, c0 = self._separar(prev, z0, z1, c0, p)
                    self.avisos.append('corte flojo en %.2f s corregido solo: zoom %.2f -> %.2f'
                                       % (c['t'], prev[1], z0))
            if c['tipo'] == 'mapa':
                c0, f0 = self.hacia_tierra(c0, z0, c['sitio'])
                c1, f1 = self.hacia_tierra(c1, z1, c['sitio'])
                if min(f0, f1) < MIN_TIERRA:
                    self.avisos.append('plano de %.2f s: lo mas de tierra que se consigue es '
                                       '%.0f %% (minimo %.0f %%)' % (c['t'], 100 * min(f0, f1),
                                                                     100 * MIN_TIERRA))
            self.sc.corte(c['t'], c0, z0)
            self.sc.viaje(c['t'], c['t1'], c1, z1, 'io')
            if c['t1'] - c['t'] > 2.0: M.ev(c['t'] + 0.05, 'whoosh', 0.3)
            self.planos.append((c['t'], c['t1'], c['tipo'], c0, z0, c1, z1, c['sitio']))
            prev = (c1, z1, c['tipo'])

    def _sujetar(self, c, z):
        z = max(z, self.zmin); w, h = self.W / z, self.H / z
        return (min(max(c[0], w / 2), self.mu.w - w / 2), min(max(c[1], h / 2), self.mu.h - h / 2))

    def _flojo(self, prev, nuevo):
        (c1, z1, t1), (c0, z0, t0) = prev, nuevo
        if t1 != t0: return False              # mapa<->mesa: la pantalla entera cambia de tono
        r = z0 / max(1e-6, z1)
        d = math.hypot(c0[0] - c1[0], c0[1] - c1[1]) / max(1e-6, self.W / max(1e-6, z1))
        return 0.72 < r < 1.39 and d < 0.40

    def _separar(self, prev, z0, z1, c0, p):
        """Empuja el zoom y el centro del plano nuevo hasta que el corte se LEA como corte."""
        z1p = prev[1]
        nz0 = z1p * (1.75 if z0 >= z1p else 0.56)
        nz0 = max(self.zmin, min(nz0, self.zmin * 6.5))
        k = nz0 / max(1e-6, z0)
        anc = self.W / nz0
        nc0 = self._sujetar((p[0] + (anc * 0.34 if c0[0] <= p[0] else -anc * 0.34), c0[1]), nz0)
        return nz0, max(self.zmin, z1 * k), nc0

    def zoom_max(self, t0, t1):
        z = self.zmin; t = t0
        while t <= t1: z = max(z, self.sc.zoom(t) * 1.16); t += 0.2
        return z

    # ---------------------------------------------------------- huecos (la eleccion de slot)
    def _rect(self, fx, fy, w, h):
        return (fx * self.W - w / 2, fy * self.H - h / 2, fx * self.W + w / 2, fy * self.H + h / 2)

    def _ocupado(self, familia, t0, t1, fx, w):
        """Intervalos verticales (en fraccion del alto) tomados por algo que NO es de esta familia
        y que comparte columna con lo que queremos poner."""
        occ = []
        x0, x1 = fx * self.W - w / 2 - 12, fx * self.W + w / 2 + 12
        for o in self.objetos:
            if o['off'] <= t0 + 0.02 or o['on'] >= t1 - 0.02: continue
            if o['familia'] == familia: continue        # mismo slot: es un relevo, no un choque
            if o['kind'] == 'rotulo': continue
            q = o['rect']
            if o.get('mundo'):
                # un objeto del mundo se mueve con la camara: su rectangulo de toda la vida es
                # enorme y bloquearia el cuadro entero. Lo que estorba es donde esta MIENTRAS los
                # dos coinciden en pantalla.
                q = self.caja_mundo(o['obj'], max(t0, o['on']), min(t1, o['off']))
            if q[2] - q[0] <= 0: continue
            if q[2] < x0 or q[0] > x1: continue
            occ.append((q[1] / self.H, q[3] / self.H))
        return occ

    def _hueco(self, familia, t0, t1, sitio, w, h, fx=0.5):
        """El hueco libre donde cae el objeto. Es LA funcion de composicion: el texto va al lado
        contrario del sitio del que se habla, nunca encima de su pin, nunca encima de un rig ni de
        otro texto vivo, y siempre dentro de la franja legible (bajo el rotulo, sobre el subtitulo).
        Devuelve (fy, banda) o (None, None) si no entra."""
        lim0, lim1 = LIMITES[self.formato]
        alto = h / self.H
        occ = self._ocupado(familia, t0, t1, fx, w)
        # El pin se mira durante TODA la vida del cartel, no solo cuando entra: la camara se mueve y
        # el sitio se le mete debajo cuatro segundos despues (paso en la primera corrida, t=21,6 s).
        if sitio:
            # solo mientras dure ESTE plano: en el corte la composicion se decide de nuevo, y de
            # que el cartel no acabe sobre el pin cuatro segundos despues se ocupa `_hasta_sin_pin`
            # acortandolo. Mirar los 7 s enteros dejaba a la cifra sin ningun hueco libre.
            t = t0 + 0.2
            while t < min(t1, max(t0 + 1.2, self.fin_plano(t0))):
                caja = self.caja_pin(sitio, min(t, self.dur - 0.05))
                if caja and not (caja[2] < fx * self.W - w / 2 or caja[0] > fx * self.W + w / 2):
                    occ.append((caja[1] / self.H, caja[3] / self.H))
                t += 0.6
        # lado contrario al sitio
        prefiere_bajo = True
        if sitio:
            try:
                p = self.pantalla(self.P(sitio), min(t1 - 0.05, t0 + 0.4))
                prefiere_bajo = p[1] < self.H * 0.55
            except SystemExit: pass
        centro = PREFERIDAS[self.formato]['bajo' if prefiere_bajo else 'alto']
        mejor, punt, sol = None, None, 1.0
        fy = lim0 + alto / 2
        while fy <= lim1 - alto / 2 + 1e-9:
            a, b = fy - alto / 2, fy + alto / 2
            # cuanto se pisa con lo que ya esta vivo, en fraccion del alto del cartel
            s = sum(max(0.0, min(b, q1 + 0.008) - max(a, q0 - 0.008)) for q0, q1 in occ) / max(1e-6, alto)
            # el solape pesa MUCHO mas que la banda preferida: un 13 % de pisado cerca del
            # centro le ganaba a un hueco limpio un poco mas arriba, y `check` lo marcaba.
            d = s * 40.0 + abs(fy - centro)
            if punt is None or d < punt: mejor, punt, sol = fy, d, s
            fy += 0.008
        if mejor is None: return None, None, 1.0
        return mejor, ('alto' if mejor < 0.5 else 'bajo'), sol

    def _apagar(self, o, t, minimo=0.6):
        """Apaga un objeto en `t` con `RELEVO` s de fundido, y con el su pie (son un bloque)."""
        nuevo = max(o['on'] + minimo, t)
        if nuevo >= o['off']: return False
        ob = o['obj']; ob.off = nuevo
        ob.a.set(max(o['on'] + 0.3, nuevo - RELEVO), 1, 'hold'); ob.a.set(nuevo, 0, 'io')
        o['off'] = nuevo
        for q in self.objetos:
            if q.get('padre') is ob and q['off'] > nuevo: self._apagar(q, nuevo, minimo=0.3)
        return True

    def fin_plano(self, t):
        return next((p[1] for p in self.planos if p[0] - 0.01 <= t < p[1]), self.dur)

    def _hasta_sin_pin(self, sitio, t0, t1, fx, w, h, fy):
        return self._sin_pin(sitio, t0 + 0.2, t1, self._rect(fx, fy, w, h), t0 + VIDA_MIN)

    def _sin_pin(self, sitio, t0, t1, r, piso=0.0):
        """Hasta cuando este rectangulo NO tapa el pin del sitio nombrado. La camara se mueve: un
        cartel bien colocado a los 6 s puede estar encima de Ceuta a los 10."""
        if not sitio: return t1
        t = t0
        while t < t1:
            caja = self.caja_pin(sitio, min(t, self.dur - 0.05))
            if caja:
                ix = max(0.0, min(r[2], caja[2]) - max(r[0], caja[0]))
                iy = max(0.0, min(r[3], caja[3]) - max(r[1], caja[1]))
                area = max(1.0, (caja[2] - caja[0]) * (caja[3] - caja[1]))
                if ix * iy / area > 0.22:
                    return max(piso, round(t - 0.25, 3))
            t += 0.2
        return t1

    def estirar(self, o, nuevo, sale=0.25):
        """Alarga la vida de un objeto. Hay que RECONSTRUIR la pista de alpha: si se dejan los
        keyframes del apagado viejo, la pista baja a 0 y vuelve a subir, y el objeto parpadea."""
        ob = o['obj']
        if nuevo <= o['off']: return
        corte = o['off'] - 0.001
        ob.a.k = [k for k in ob.a.k if k[0] < corte - 0.25] or [(0.0, 0.0, 'hold')]
        ob.a.set(max(o['on'] + 0.2, corte - 0.25), 1, 'io')
        ob.a.set(max(o['on'] + 0.4, nuevo - sale), 1, 'hold'); ob.a.set(nuevo, 0, 'io')
        ob.off = nuevo; o['off'] = nuevo
        for q in self.objetos:
            if q.get('padre') is ob and q['off'] < nuevo: self.estirar(q, nuevo, sale)

    def _relevo(self, familia, t):
        """El nuevo reemplaza al viejo de la misma familia: el viejo se apaga justo cuando el nuevo
        empieza a entrar, asi que no coinciden ni un cuadro (un fundido cruzado deja los dos textos
        encima y no se lee ninguno)."""
        for o in list(self.objetos):
            if o['familia'] != familia or o['kind'] in ('rotulo', 'gancho'): continue
            if o['off'] <= t + 0.02 or o['on'] >= t: continue
            self._apagar(o, t)

    def _relevo_rect(self, rect, t):
        """Apaga lo que quede DEBAJO de un objeto nuevo grande (el documento de un plano de MESA),
        sea de la familia que sea: un cambio de escenario se lleva la composicion anterior."""
        for o in list(self.objetos):
            # el rotulo tambien cae: vive arriba del todo, pero un rig de pie sobre el mapa le llega
            if o['off'] <= t + 0.02 or o['on'] >= t or o['kind'] == 'gancho': continue
            q = o['rect']
            if q[2] - q[0] <= 0: continue
            ix = max(0.0, min(q[2], rect[2]) - max(q[0], rect[0]))
            iy = max(0.0, min(q[3], rect[3]) - max(q[1], rect[1]))
            menor = min((q[2] - q[0]) * (q[3] - q[1]), (rect[2] - rect[0]) * (rect[3] - rect[1]))
            if menor <= 0 or ix * iy / menor <= MAX_SOLAPE: continue
            self._apagar(o, t, minimo=0.4)

    # ---------------------------------------------------------- HUD
    def hud(self, im, t0, t1, fx, fy, escala=1.0, z=60, entra=0.26, sale=0.22, sfx='pop',
            nombre='card:', bg=False, margen=20, ancho_max=0.94, alto_max=0.62, deriva=True):
        """Objeto de PANTALLA: px de cuadro, cruza los cortes de camara sin partirse y sujeto DENTRO
        del cuadro (regla 1). Devuelve (obj, escala_final)."""
        k = escala
        if im.width * k > self.W * ancho_max - 2 * margen: k = (self.W * ancho_max - 2 * margen) / im.width
        if im.height * k > self.H * alto_max: k = (self.H * alto_max) / im.height
        w2, h2 = im.width * k / 2, im.height * k / 2
        o = M.Obj(im, z=z); o.name = nombre; o.bg = bg; o.shadow = False
        o.wobble = 0.0; o.bob = 0.0; o.vida = 0.0
        o.x = M.Track(min(max(self.W * fx, w2 + margen), self.W - w2 - margen))
        o.y = M.Track(min(max(self.H * fy, h2 + margen), self.H - h2 - margen))
        o.sc = M.Track(k)
        o.on, o.off = t0, t1
        o.a.set(t0, 0, 'hold'); o.a.set(t0 + entra, 1, 'io')
        o.a.set(max(t0 + entra, t1 - sale), 1, 'hold'); o.a.set(t1, 0, 'io')
        if deriva and t1 - t0 > 0.9:
            # nada del todo quieto: el papel respira un 1,6 % y gira medio grado a lo largo del
            # plano. El margen de arriba reserva el crecimiento, asi que no rompe la regla 1.
            o.sc.set(t0, k * 0.984, 'hold'); o.sc.set(t1, k, 'io')
            o.rot.set(t0, -0.5, 'hold'); o.rot.set(t1, 0.5, 'io')
        if sfx: M.ev(t0, sfx, 0.5)
        self.sc.add_hud(o)
        return o, k

    def _card(self, txt, cuerpo, tcolor=TINTA, color=PAPEL, sello=False):
        """Tarjeta de papel con el CUERPO pedido. Parte el texto en 2 lineas como maximo y solo
        achica la letra si ni asi entra (y entonces `check` lo caza y avisa con el texto)."""
        # presupuesto real de ancho: lo que `hud()` deja (0,94 del cuadro menos los margenes) menos
        # los 70 px de papel que `props.card` anade alrededor del texto
        ancho = self.W * 0.94 - 40 - 78
        d0 = ImageDraw.Draw(Image.new('L', (8, 8)))
        lineas = txt.split(NL)
        for _ in range(10):
            f = PR.FONT(max(12, int(cuerpo)))
            if len(lineas) == 1 and d0.textlength(lineas[0], font=f) > ancho:
                pal = lineas[0].split(); mejor = None
                for k in range(1, len(pal)):
                    a, b = ' '.join(pal[:k]), ' '.join(pal[k:])
                    m = max(d0.textlength(a, font=f), d0.textlength(b, font=f))
                    if mejor is None or m < mejor[0]: mejor = (m, [a, b])
                if mejor: lineas = mejor[1]
            if max(d0.textlength(l, font=f) for l in lineas) <= ancho: break
            cuerpo *= 0.93
        t = NL.join(lineas)
        im = (PR.sello(t, color=tcolor, size=int(cuerpo)) if sello
              else PR.card(t, size=int(cuerpo), color=color, tcolor=tcolor))
        return im, int(cuerpo), t

    # ---------------------------------------------------------- el UNICO rojo
    def arbitrar_rojo(self, eventos):
        """UN rojo por cuadro, decidido ANTES de dibujar nada.

        Tiene que ser una pasada previa y no una decision sobre la marcha: la ruta pide el rojo en
        el segundo 41 y la cifra que se lo quita entra en el 45, cuando la ruta ya esta dibujada y
        el color ya no se puede cambiar. Prioridad: CIFRA > RUTA > SELLO > TARJETA roja."""
        # Antes de repartir nada: lo que ya trae rojo IMPRESO se queda con el rojo de esos
        # segundos. La barra de INTEREST, la curva de 1946 y el TOTAL del recibo son rojos que
        # nadie escribio en la anotacion y que el arbitro no veia; el resultado era una cifra roja
        # encima de un papel rojo, o sea dos rojos, y `check` marcandolo sin que hubiera forma de
        # arreglarlo desde el guion.
        for e in eventos:
            if e['verbo'] not in ('DOC', 'PROP', 'SECUENCIA', 'SELLO'): continue
            nom = e['args'][0] if e['args'] else ''
            # de una secuencia se mide el ULTIMO cuadro: el primero de una curva que se dibuja
            # esta practicamente en blanco y decia que el prop no lleva rojo.
            if e['verbo'] == 'SECUENCIA':
                n = int(e['args'][1]) if len(e['args']) > 1 else 13
                nom = '%s%02d' % (nom, max(0, n - 1))
            if _prop_rojo(self, nom) < 0.004: continue
            fin = max(float(e.get('t_off', 0) or 0), float(e.get('t_fin_plano', 0) or 0))
            self.rojo.append((e['t'], max(e['t'] + 1.0, fin)))
        cand = []
        for e in eventos:
            k = {'CIFRA': 'cifra', 'RUTA': 'ruta', 'SELLO': 'sello'}.get(e['verbo'])
            if e['verbo'] == 'TARJETA' and str(e['kw'].get('color', '')).lower() in ('rojo', 'red'):
                k = 'tarjeta'
            if not k: continue
            # la ruta solo reclama el rojo MIENTRAS SE DIBUJA: despues queda como rastro ocre
            # la ruta reclama el rojo SOLO mientras se dibuja: es la accion, no el rastro
            fin = min(e['t_off'], e['t'] + 3.2) if k == 'ruta' else e['t_off']
            if k != 'ruta': fin = min(fin, _releva_en(eventos, e))
            cand.append((PRIO_ROJO[k], e['t'], fin, e))
        for prio, a, b, e in sorted(cand, key=lambda c: (c[0], c[1])):
            libre = all(not (a < y - 0.05 and b > x + 0.05) for x, y in self.rojo)
            e['rojo'] = libre
            if libre: self.rojo.append((a, b))
            else: self.avisos.append('%s en %.2f s pasa a tinta/ocre: ya hay un rojo en pantalla'
                                     % (e['verbo'], a))

    # ---------------------------------------------------------- registro
    def registrar(self, o, kind, familia, banda, cuerpo=None, rect=None, linea=-1, sitio=None,
                  mundo=False, texto='', on=None, off=None):
        self.objetos.append({'obj': o, 'kind': kind, 'familia': familia, 'banda': banda,
                             'cuerpo': cuerpo, 'on': on if on is not None else o.on,
                             'off': off if off is not None else o.off, 'linea': linea,
                             'sitio': sitio, 'mundo': mundo, 'texto': texto,
                             'rect': rect or (0, 0, 0, 0)})
        return o


FAMILIA = {'CIFRA': 'cifra', 'TARJETA': 'texto', 'SELLO': 'objeto', 'PROP': 'objeto',
           'PERSONAJE': 'objeto', 'SECUENCIA': 'objeto', 'DOC': 'objeto'}


_ROJO_PROP = {}


def _prop_rojo(C, nombre):
    """Fraccion de pixeles claramente ROJOS de un prop, sobre lo que no es transparente."""
    if not nombre: return 0.0
    if nombre in _ROJO_PROP: return _ROJO_PROP[nombre]
    im = _imagen(C, nombre, mudo=True)
    if im is None:
        _ROJO_PROP[nombre] = 0.0; return 0.0
    a = np.asarray(im.resize((min(im.width, 240), min(im.height, 240))).convert('RGBA'))
    op = a[:, :, 3] > 40
    r, g, b = a[:, :, 0].astype(np.int16), a[:, :, 1].astype(np.int16), a[:, :, 2].astype(np.int16)
    rojo = op & (r > 120) & (r - g > 55) & (r - b > 45)
    _ROJO_PROP[nombre] = float(rojo.sum()) / max(1, int(op.sum()))
    return _ROJO_PROP[nombre]


def _releva_en(eventos, e):
    """Cuando le van a quitar el sitio a este objeto: el proximo verbo de su misma familia, o el
    proximo cambio de escenario. Lo necesita el arbitraje del rojo, que corre ANTES de colocar
    nada y por tanto antes de que `_relevo` acorte las vidas de verdad."""
    fam = FAMILIA.get(e['verbo'])
    for f in eventos:
        if f['t'] <= e['t'] + 0.05 or f is e: continue
        if f['verbo'] in ('DOC', 'MESA') or FAMILIA.get(f['verbo']) == fam: return f['t']
    return 1e9


# ============================================================== 5. LOS VERBOS
def _ejecutar(C, eventos):
    for e in eventos:
        if e['verbo'] == 'MESA':
            # `COMPO.md` §3: «MESA · cambia de escenario a mesa sin documento (el mundo se oscurece)».
            # Hasta el 16-sep el velo SOLO lo registraba `DOC` (`C.mesas.append` en `_v_doc`): un MESA a
            # secas abria plano pero dejaba el mapa a plena luz. En la S13 eso daba cortes mapa->"mesa"
            # entre dos zonas de tierra casi iguales, que ni el ojo ni `ritmo.py` leen como corte (un
            # plano de 9,25 s en la pieza 1).
            C.mesas.append((e['t'], e['t_fin_plano']))
            continue
        if e['verbo'] == 'MAPA': continue                     # ya esta en la camara
        {'PINTA': _v_pinta, 'RUTA': _v_ruta, 'CIFRA': _v_cifra, 'TARJETA': _v_tarjeta,
         'SELLO': _v_sello, 'DOC': _v_doc, 'PROP': _v_prop, 'PERSONAJE': _v_personaje,
         'SECUENCIA': _v_secuencia, 'ROTULO': _v_rotulo}[e['verbo']](C, e)
    # Tramos de mesa que se tocan (un MESA seguido de un DOC en el mismo tramo) se funden en UNO:
    # dos pares de keyframes solapados se pisan y el velo parpadea.
    fundidos = []
    for t0, t1 in sorted(C.mesas):
        if fundidos and t0 <= fundidos[-1][1] + 0.05:
            fundidos[-1] = (fundidos[-1][0], max(fundidos[-1][1], t1))
        else:
            fundidos.append((t0, t1))
    C.mesas = fundidos
    # el velo de los planos de MESA, en una sola pasada (los keyframes no pueden pelearse)
    for t0, t1 in sorted(C.mesas):
        if t0 > 0.05:
            C.mu.dark.set(max(0.0, t0 - 0.16), C.mu.dark(max(0.0, t0 - 0.16)), 'hold')
            C.mu.dark.set(t0, OSCURO_MESA, 'io')
        else:
            C.mu.dark.set(0.0, OSCURO_MESA, 'hold')
        C.mu.dark.set(max(t0 + 0.2, t1 - 0.14), OSCURO_MESA, 'hold'); C.mu.dark.set(t1, 0.0, 'io')


def _columnas(C, e, t):
    """Columnas candidatas, la mejor primero. En vertical el cuadro es angosto y solo hay una; en
    horizontal el texto va al lado CONTRARIO de lo que se esta mirando: el sitio del que habla la
    linea y, si hay uno vivo, el personaje (que manda, porque ocupa el centro)."""
    if C.formato == 'vertical': return [0.5]
    izq, der = COLUMNAS['horizontal']['izq'], COLUMNAS['horizontal']['der']
    x = None
    for a, b, rig in C.rigs:
        if a - 0.3 <= t < b:
            bb = rig.bbox(min(t, C.dur - 0.01))
            if bb: x = C.pantalla(((bb[0] + bb[2]) / 2, bb[1]), t)[0]; break
    if x is None and e.get('sitio'):
        try: x = C.pantalla(C.P(e['sitio']), t)[0]
        except SystemExit: x = None
    if x is None: return [der, izq]
    return [der, izq] if x < C.W * 0.5 else [izq, der]


def _fx(C, e, t):
    return _columnas(C, e, t)[0]


def _poner_texto(C, e, kind, familia, txt, cuerpo_rel, tcolor, pie=None, sello=False, z=None):
    """Coloca una tarjeta (o una cifra) en el hueco libre: elige el cuerpo, parte el texto, busca
    hueco, releva al anterior del mismo slot y, si no entra, lo achica hasta el minimo antes de
    rendirse (y entonces avisa)."""
    t0, t1 = e['t'], e['t_off']
    cols = _columnas(C, e, t0)
    fx = cols[0]
    cuerpo = max(MIN_CUERPO[kind] * C.H, C.H * cuerpo_rel)
    im = cu = tx = None; im_pie = None; cu_pie = 0
    fy = banda = None; mejor = None
    for intento in range(4):
        im, cu, tx = C._card(txt, cuerpo, tcolor=tcolor, sello=sello)
        if pie: im_pie, cu_pie, _ = C._card(pie, MIN_CUERPO['pie'] * C.H * 1.08, tcolor=TINTA)
        alto = im.height * (1.06 if kind == 'cifra' else 1.0) + (im_pie.height + 14 if im_pie else 0)
        for c in cols:                    # primero la columna buena; si no entra, la otra
            fy, banda, sol = C._hueco(familia, t0, t1, e.get('sitio'), im.width, alto, c)
            if mejor is None or sol < mejor[0]:
                mejor = (sol, fy, banda, c, im, cu, tx, im_pie, cu_pie)
            if sol <= 0.001: fx = c; break
        if mejor and mejor[0] <= 0.001: break
        cuerpo = max(MIN_CUERPO[kind] * C.H, cuerpo * 0.86)
        if intento == 3 or cuerpo <= MIN_CUERPO[kind] * C.H + 1: break
    # ni al minimo tamano hay un hueco limpio: se usa el MENOS malo y se dice cual es
    sol, fy, banda, fx, im, cu, tx, im_pie, cu_pie = mejor
    if sol > 0.001:
        C.avisos.append('linea %d: %r no encuentra hueco limpio; va donde menos estorba (se pisa '
                        'el %.0f %% de su alto)' % (e['linea'], txt.replace(NL, ' ')[:34], 100 * sol))
    # El cartel cruza el corte, pero no a cualquier precio: si mas adelante la camara le mete
    # debajo el pin del sitio del que habla la linea, se va ANTES de que eso pase.
    # se mira el sitio de SU linea y el de la siguiente: el cartel cruza el corte y el sitio del
    # que habla la voz cambia con el (paso con Beijing y «THE RETIREMENT MONEY»)
    for _s in {e.get('sitio'), e.get('sitio_sig')} - {None}:
        t1 = min(t1, C._hasta_sin_pin(_s, t0, t1, fx, im.width, im.height, fy))
    C._relevo(familia, t0)
    dy = (im_pie.height + 14) / 2 / C.H if im_pie else 0.0
    o, k = C.hud(im, t0, t1, fx, fy - dy, z=z or (62 if kind == 'cifra' else 56),
                 entra=0.12 if kind == 'cifra' else 0.24,
                 sfx='stamp' if kind == 'cifra' else 'pop',
                 nombre=('cifra:' if kind == 'cifra' else 'card:') + tx.replace(NL, ' '))
    if kind == 'cifra':
        o.sy.set(t0, 0.06, 'hold'); o.sy.set(t0 + 0.30, 1.0, 'back')     # flipin: la cifra golpea
    r = (o.x(t1) - im.width * k / 2, o.y(t1) - im.height * k / 2 * 1.04,
         o.x(t1) + im.width * k / 2, o.y(t1) + im.height * k / 2 * 1.04)
    C.registrar(o, kind, familia, banda, cuerpo=cu * k, rect=r, linea=e['linea'],
                sitio=e.get('sitio'), texto=tx)
    if im_pie:
        fy2 = (r[3] + 14 + im_pie.height / 2) / C.H
        op, kp = C.hud(im_pie, t0 + 0.14, t1, fx, fy2, z=58, sfx=None,
                       nombre='card:' + pie.replace(NL, ' '))
        rp = (op.x(t1) - im_pie.width * kp / 2, op.y(t1) - im_pie.height * kp / 2,
              op.x(t1) + im_pie.width * kp / 2, op.y(t1) + im_pie.height * kp / 2)
        C.registrar(op, 'pie', familia, banda, cuerpo=cu_pie * kp, rect=rp, linea=e['linea'],
                    texto=pie)
        C.objetos[-1]['padre'] = o          # la cifra y su pie son UN bloque: se van juntos
    return o


def _v_cifra(C, e):
    txt = e['args'][0] if e['args'] else '?'
    pie = e['args'][1] if len(e['args']) > 1 else None
    _poner_texto(C, e, 'cifra', 'cifra', txt, 0.088, ROJO if e.get('rojo') else TINTA, pie=pie)


def _v_tarjeta(C, e):
    txt = e['args'][0] if e['args'] else '?'
    col = TINTA
    if str(e['kw'].get('color', '')).lower() in ('rojo', 'red'):
        col = ROJO if e.get('rojo') else TINTA
    _poner_texto(C, e, 'tarjeta', 'texto', txt, 0.046, col)


def _v_sello(C, e):
    arg = e['args'][0] if e['args'] else 'SEALED'
    rojo = bool(e.get('rojo'))
    im = _imagen(C, arg, mudo=True)
    if im is None:                                   # texto: el sello se dibuja y el color se elige
        o = _poner_texto(C, e, 'tarjeta', 'objeto', arg, 0.052, ROJO if rojo else TINTA, sello=True)
        o.rot.set(e['t'], -7, 'hold'); o.rot.set(e['t'] + 0.22, 2.0, 'back')
        o.rot.set(e['t'] + 0.5, 0.0, 'soft')
        C.sc.shake(e['t'] + 0.2, 5, 0.22)
        C.objetos[-1]['kind'] = 'sello'
        return
    t0, t1 = e['t'], e['t_off']
    alto = C.H * 0.115; k = alto / im.height
    fy, banda, _s = C._hueco('objeto', t0, t1, e.get('sitio'), im.width * k, alto, _fx(C, e, t0))
    C._relevo('objeto', t0)
    o, k = C.hud(im, t0, t1, _fx(C, e, t0), fy, escala=k, z=52, entra=0.12, sfx='stamp',
                 nombre='prop:' + arg)
    o.rot.set(t0, -7, 'hold'); o.rot.set(t0 + 0.22, 2.0, 'back'); o.rot.set(t0 + 0.5, 0.0, 'soft')
    C.sc.shake(t0 + 0.2, 5, 0.22)
    r = (o.x(t0) - im.width * k / 2, o.y(t0) - im.height * k / 2,
         o.x(t0) + im.width * k / 2, o.y(t0) + im.height * k / 2)
    C.registrar(o, 'sello', 'objeto', banda, rect=r, linea=e['linea'], texto='')
    C.objetos[-1]['horneado'] = _texto_prop(C, arg)


def _v_rotulo(C, e):
    txt = e['args'][0] if e['args'] else ''
    im, cu, tx = C._card(txt, max(MIN_CUERPO['rotulo'] * C.H, C.H * 0.028))
    o, k = C.hud(im, e['t'], e['t_off'], 0.5, ROTULO_FY[C.formato], z=58, sfx=None, deriva=False,
                 nombre='rotulo:' + tx.replace(NL, ' '))
    r = (o.x(e['t']) - im.width * k / 2, o.y(e['t']) - im.height * k / 2,
         o.x(e['t']) + im.width * k / 2, o.y(e['t']) + im.height * k / 2)
    C.registrar(o, 'rotulo', 'rotulo', None, cuerpo=cu * k, rect=r, linea=e['linea'], texto=tx)


def _v_pinta(C, e):
    """El color narra: el pais se pinta EN EL INSTANTE en que la voz lo nombra."""
    q = e['args'][0] if e['args'] else ''
    alias = _alias_capa(C, q)
    if alias is None:
        C.avisos.append('linea %d: PINTA(%s) no encuentra esa capa en el mundo' % (e['linea'], q))
        return
    if alias in C.capas_on: return
    C.capas_on[alias] = e['t']
    C.mu.add_layer(C.mu.meta['capas'][alias], e['t'], 1.3, mode='fade')
    # Los enclaves que Natural Earth 50m mete DENTRO del vecino se pintan despues: gana el de
    # arriba. Sin esto el mapa afirma lo contrario que el guion (Ceuta del color de Marruecos).
    for hijo in (getattr(C.mu, 'spec', {}).get('encima', {}) or {}).get(alias, []):
        if hijo in C.mu.meta['capas']:
            C.mu.add_layer(C.mu.meta['capas'][hijo], e['t'] + 0.35, 1.1, mode='fade')
            C.capas_on[hijo] = e['t'] + 0.35
    if 'marcas' in C.mu.meta['capas'] and 'marcas' not in C.capas_on:
        C.mu.add_layer(C.mu.meta['capas']['marcas'], e['t'] + 0.5, 0.3, mode='fade')
        C.capas_on['marcas'] = e['t'] + 0.5


def _alias_capa(C, q):
    spec = getattr(C.mu, 'spec', {})
    capas = spec.get('capas') or {}
    if q in capas: return q
    for k, v in capas.items():
        if q in v[0] or q.upper() in [str(x).upper() for x in v[0]]: return k
    for k, v in (spec.get('capas_geojson') or {}).items():
        if q == k or q in v[1]: return k
    return None


def _v_ruta(C, e):
    nombres = []
    for a in e['args']:
        p = C.P(a); nm = '_ruta_%s' % _norm(a)
        C.mu.pts[nm] = [p[0], p[1]]; nombres.append(nm)
    t0 = e['t']; t1 = min(e['t_off'], t0 + 3.2)
    frac = _agua(C, nombres)
    if frac is not None:
        C.avisos.append('linea %d: la ruta va %.0f %% por agua DIBUJADA en su tramo de en medio'
                        % (e['linea'], 100 * frac))
        if frac < 0.90:
            C.avisos.append('linea %d: OJO, la ruta pisa tierra: mover los puntos' % e['linea'])
    an = max(9, int(C.mu.w * 0.0046))
    hasta = float(e['kw'].get('hasta', C.dur))
    # La ruta va ROJA MIENTRAS SE DIBUJA (es la accion de la pieza) y despues se queda como RASTRO
    # ocre. Asi el recorrido no compite por el unico rojo con las cifras que vienen despues, que es
    # lo que pide la regla, y el momento en que la linea cruza el agua sigue siendo el rojo del
    # cuadro. Son dos rutas: la roja con `t_off`, y la ocre ya dibujada a partir de ahi.
    corte = min(hasta, t1 + 0.15)
    if e.get('rojo', True): C.rojo_mapa.append((t0, corte))
    C.mu.route(nombres, t0, t1, color=ROJO if e.get('rojo', True) else OCRE, width=an, t_off=corte)
    if hasta > corte + 0.05:
        C.mu.route(nombres, corte - 0.02, corte, color=OCRE, width=an,
                   t_off=None if hasta >= C.dur else hasta)
    M.ev(t0, 'whoosh', 0.45)


def _agua(C, nombres):
    """Comprueba SOBRE EL PNG del mundo que el tramo de en medio va por agua DIBUJADA. Natural
    Earth 50m no resuelve una bahia chica: lo honesto es verificar lo que se ve, no el poligono."""
    try: base = np.asarray(C.mu.base.convert('RGB')).astype(int)
    except Exception: return None
    es_agua = (base[:, :, 2] - base[:, :, 0]) > 25
    pts = [C.mu.pts[n] for n in nombres]
    segs = list(zip(pts, pts[1:]))
    if len(segs) < 3: return None
    tot = moj = 0
    for si, ((x0, y0), (x1, y1)) in enumerate(segs):
        if not (1 <= si < len(segs) - 1): continue
        pasos = max(2, int(math.hypot(x1 - x0, y1 - y0) / 4))
        for k in range(pasos + 1):
            u = k / pasos
            x, y = int(round(x0 + (x1 - x0) * u)), int(round(y0 + (y1 - y0) * u))
            if not (0 <= x < base.shape[1] and 0 <= y < base.shape[0]): continue
            tot += 1; moj += bool(es_agua[y, x])
    return moj / max(1, tot)


_CACHE_IM = {}
_CACHE_TXT = {}


def _texto_prop(C, nombre):
    """El texto HORNEADO en un PNG: de `TEXTOS_PROPS` o de un `prop_<nombre>.txt` al lado del PNG.
    `None` = nadie lo declaro (y entonces `check` lo marca: un papel con letras sin declarar es
    exactamente el «LEASE 99 YEARS» de la pieza 3)."""
    if nombre in TEXTOS_PROPS: return TEXTOS_PROPS[nombre]
    if nombre in _CACHE_TXT: return _CACHE_TXT[nombre]
    for base in _dirs_props(C):
        p = os.path.join(base, 'prop_%s.txt' % nombre)
        if os.path.exists(p):
            _CACHE_TXT[nombre] = open(p, encoding='utf-8').read().strip(); return _CACHE_TXT[nombre]
    _CACHE_TXT[nombre] = None
    return None


def _dirs_props(C):
    cand = [os.path.join(C.base, 'arte', 'assets'), os.path.join(C.base, 'assets'),
            os.path.abspath(os.path.join(C.base, '..', '..', 'arte', 'assets')),
            os.path.join(AQUI, 'assets')]
    for d in sorted(os.listdir(os.path.join(RAIZ, 'videos'))):
        cand.append(os.path.join(RAIZ, 'videos', d, 'arte', 'assets'))
    return cand


def _imagen(C, nombre, mudo=False):
    if nombre in _CACHE_IM: return _CACHE_IM[nombre]
    for base in _dirs_props(C):
        p = os.path.join(base, 'prop_%s.png' % nombre)
        if os.path.exists(p):
            _CACHE_IM[nombre] = Image.open(p).convert('RGBA'); return _CACHE_IM[nombre]
    if mudo: return None
    raise SystemExit('compo: falta el prop %r (dibujalo en arte/props_*.py)' % nombre)


def _v_doc(C, e):
    """Plano de MESA. **Nunca una hoja rayada a pantalla completa** (es el look que Agustin rechazo
    el 15-sep): el mundo se oscurece, el DOCUMENTO entra grande —el documento ES el papel— y dos o
    tres props de escritorio se quedan de fondo en las esquinas. El mapa sigue viendose debajo."""
    doc = e['args'][0] if e['args'] else 'sentencia'
    sub = e['args'][1] if len(e['args']) > 1 else None
    # Un documento tiene NOMBRE: `DOC(informe)` a secas pone un papel generico que puede decir
    # cualquier cosa. `DOC(informe, "EIA · WEEKLY PETROLEUM STATUS REPORT")` dice cual es.
    if not sub and not (TEXTOS_PROPS.get(doc) or _texto_prop(C, doc)):
        raise SystemExit('compo: DOC(%s) sin titulo. Un documento se nombra: DOC(%s, "EL NOMBRE '
                         'REAL DEL PAPEL"). Si el PNG ya lo trae impreso, declaralo en '
                         'TEXTOS_PROPS o en prop_%s.txt.' % (doc, doc, doc))
    if sub and all(w.lower() in PLACEHOLDERS or len(w) < 3 for w in re.findall(r'\w+', sub)):
        raise SystemExit('compo: DOC(%s, "%s") es un placeholder. El titulo tiene que nombrar el '
                         'papel del que habla la voz.' % (doc, sub))
    t0, t1 = e['t'], e['t_fin_plano']
    C.mesas.append((t0, t1))
    for nom, fx, fy, al in (getattr(C.mu, 'spec', {}).get('escritorio') or ESCRITORIO):
        im = _imagen(C, nom, mudo=True)
        if im is None: continue
        o, _k = C.hud(im, t0, t1, fx, fy, escala=(C.H * al) / im.height, z=12, bg=True,
                      entra=0.30, sale=0.22, sfx=None, nombre='mesa:' + nom, deriva=False)
        o.rot.set(t0, -0.8, 'hold'); o.rot.set(t1, 0.8, 'io')
    im = _imagen(C, doc)
    # con subtitulo, el documento cede un 8 % de alto: si no, no queda hueco legible para la
    # tarjeta ni arriba ni abajo (el documento ya ocupa medio cuadro)
    k = (C.H * DOC_ALTO[C.formato] * (0.92 if sub else 1.0)) / im.height
    C._relevo('objeto', t0)
    k0 = min(k, (C.W * 0.94 - 40) / im.width)
    C._relevo_rect((C.W / 2 - im.width * k0 / 2, C.H * DOC_FY[C.formato] - im.height * k0 / 2,
                    C.W / 2 + im.width * k0 / 2, C.H * DOC_FY[C.formato] + im.height * k0 / 2), t0)
    o, k = C.hud(im, t0 + 0.05, t1 - 0.05, 0.5, DOC_FY[C.formato], escala=k, z=40, entra=0.34,
                 sale=0.26, sfx='paper', nombre='doc:' + doc,
                 alto_max=DOC_ALTO[C.formato] + 0.06, deriva=False)
    # El documento CRECE HACIA la escala que ya entra (nunca a partir de ella: multiplicarla al
    # final lo sacaba del cuadro) y gira 2,6 grados: un plano de mesa quieto es una foto.
    o.sc.set(t0 + 0.05, k / 1.12, 'hold'); o.sc.set(t1 - 0.05, k, 'io')
    o.rot.set(t0 + 0.05, -1.3, 'hold'); o.rot.set(t1 - 0.05, 1.3, 'io')
    r = (o.x(t0) - im.width * k / 2 * 1.02, o.y(t0) - im.height * k / 2 * 1.02,
         o.x(t0) + im.width * k / 2 * 1.02, o.y(t0) + im.height * k / 2 * 1.02)
    C.registrar(o, 'doc', 'objeto', 'doc', rect=r, linea=e['linea'], texto=doc)
    C.objetos[-1]['horneado'] = _texto_prop(C, doc)
    if sub:
        _poner_texto(C, dict(e, t=t0 + 0.20, t_off=t1 - 0.05), 'tarjeta', 'texto', sub, 0.046,
                     TINTA, z=57)
        C.objetos[-1]['de_doc'] = True      # el titulo del documento es del documento: no se estira


def _v_prop(C, e):
    """`sobre=<sitio>` ancla el prop al MAPA (px de mundo, regla 24); `sobre=izq|centro|der` lo pone
    en un tercio de PANTALLA."""
    nom = e['args'][0] if e['args'] else '?'
    im = _imagen(C, nom)
    sobre = e['kw'].get('sobre') or (e['args'][1] if len(e['args']) > 1 else None)
    esc = float(e['kw'].get('escala', 1.0))
    t0, t1 = e['t'], e['t_off']
    if sobre and sobre in TERCIOS[C.formato]:
        fx, _fy0 = TERCIOS[C.formato][sobre]
        k = (C.W * MIN_PROP_W * 1.5 * esc) / im.width
        fy, banda, _s = C._hueco('objeto', t0, t1, e.get('sitio'), im.width * k, im.height * k, fx)
        C._relevo('objeto', t0)
        o, k = C.hud(im, t0, t1, fx, fy, escala=k, z=48, entra=0.20, sfx='pop', nombre='prop:' + nom)
        r = (o.x(t0) - im.width * k / 2, o.y(t0) - im.height * k / 2,
             o.x(t0) + im.width * k / 2, o.y(t0) + im.height * k / 2)
        C.registrar(o, 'prop', 'objeto', banda, rect=r, linea=e['linea'], texto=nom)
        C.objetos[-1]['horneado'] = _texto_prop(C, nom)
        return
    p = C.P(sobre) if sobre else C.P(e.get('sitio') or list(C.mu.pts)[0])
    t1 = max(min(t1, e['t_fin_plano']), min(C.dur - 0.05, t0 + 1.8))
    o = M.Obj(im, z=46); o.name = 'prop:' + nom; o.shadow = True
    o.x = M.Track(p[0]); o.y = M.Track(p[1])
    o.wobble = 0.0; o.bob = 0.0; o.vida = 0.0; o.on, o.off = t0, t1
    # EL ANCHO EN PANTALLA SE FIJA (46 % del cuadro) y la escala del objeto compensa el zoom de la
    # camara cuadro a cuadro. Si no, el mismo prop mide el 46 % en un plano cerrado y el 11 % en el
    # abierto siguiente: o no se lee, o se sale (regla 1). La POSICION sigue siendo el px de mundo
    # del sitio, asi que la regla 24 se cumple igual.
    objetivo = C.W * 0.46 * esc
    t = t0
    while t <= t1 + 1e-6:
        o.sc.set(round(t, 3), (objetivo / max(1e-6, C.sc.zoom(t))) / im.width, 'lin')
        t += 0.4
    o.a.set(t0, 0, 'hold'); o.a.set(t0 + 0.24, 1, 'io')
    o.a.set(max(t0 + 0.3, t1 - 0.25), 1, 'hold'); o.a.set(t1, 0, 'io')
    o.rot.set(t0, -1.2, 'hold'); o.rot.set(t1, 1.2, 'io')
    C.sc.add(o)
    _encajar(C, o, t0, t1)
    M.ev(t0, 'stamp', 0.45)
    C._relevo('objeto', t0)
    C.registrar(o, 'prop', 'objeto', 'mapa', rect=C.caja_mundo(o, t0, t1), linea=e['linea'],
                sitio=sobre, mundo=True, texto=nom)
    C.objetos[-1]['horneado'] = _texto_prop(C, nom)


def _a_tierra(C, p, avisos=None, quien=''):
    """Lleva un punto al pixel de TIERRA mas cercano. Un rig de pie sobre el mar no esta de pie:
    flota. El punto de partida sigue saliendo de lon/lat (regla 24); esto solo lo despega de la
    costa lo justo, y lo dice."""
    m, _f, _i = tierra_mundo(C.mu)
    red = C.mu._tierra[3]
    x, y = int(p[0] / red), int(p[1] / red)
    h, w = m.shape
    if 0 <= y < h and 0 <= x < w and m[y, x]: return p
    for r in range(1, 60):
        for dy in range(-r, r + 1):
            for dx in (-r, r) if abs(dy) != r else range(-r, r + 1):
                yy, xx = y + dy, x + dx
                if 0 <= yy < h and 0 <= xx < w and m[yy, xx]:
                    q = ((xx + 0.5) * red, (yy + 0.5) * red)
                    if avisos is not None:
                        avisos.append('%s caia en el agua: se corre %.0f px de mundo a la costa'
                                      % (quien, math.hypot(q[0] - p[0], q[1] - p[1])))
                    return q
    return p


def _zoom_min(C, t0, t1):
    z = 1e9; t = t0
    while t <= t1 + 1e-6: z = min(z, C.sc.zoom(t)); t += 0.2
    return z if z < 1e8 else C.zmin


def _vida_mundo(C, t0, t_max, rango=1.55, minimo=2.2):
    """Hasta donde puede vivir un objeto ANCLADO AL MAPA. Un rig no puede reescalarse, asi que si su
    vida cruza un corte que abre el plano a la mitad de zoom, el rig se queda en el 17 % del alto y
    deja de leerse (medido en la primera corrida de la pieza 4). Se corta la vida donde el zoom se
    sale de `rango` veces el minimo visto, con un piso de `minimo` segundos."""
    z0 = C.sc.zoom(t0); zlo = zhi = z0; t = t0
    fin = t0
    while t <= t_max + 1e-6:
        z = C.sc.zoom(t)
        if max(zhi, z) / max(1e-6, min(zlo, z)) > rango: break
        zlo, zhi = min(zlo, z), max(zhi, z); fin = t; t += 0.2
    return min(C.dur - 0.05, max(fin, t0 + minimo))


def _encajar(C, o, t0, t1, margen=26, vueltas=3):
    """Lo corre lo justo para que entre ENTERO en la ventana durante todo el plano (regla 1). Los
    objetos del mundo se anclan por su centro y la ventana se mueve: ponerlos a ojo da violaciones
    de encuadre en cadena."""
    peor = (0.0, 0.0); t = t0 + 0.2
    while t < t1 - 0.1:
        b = o.bbox(t)
        if b is not None:
            vx0, vy0, vx1, vy1 = C.sc.window(t)
            dx = max(0.0, vx0 + margen - b[0]) - max(0.0, b[2] - (vx1 - margen))
            dy = max(0.0, vy0 + margen - b[1]) - max(0.0, b[3] - (vy1 - margen))
            if abs(dx) + abs(dy) > abs(peor[0]) + abs(peor[1]): peor = (dx, dy)
        t += 0.2
    if abs(peor[0]) + abs(peor[1]) > 0.5:
        o.x = M.Track(o.x(t0) + peor[0]); o.y = M.Track(o.y(t0) + peor[1])
        if vueltas > 1:                 # una sola pasada arregla el peor instante, no todos
            p2 = _encajar(C, o, t0, t1, margen, vueltas - 1)
            return (peor[0] + p2[0], peor[1] + p2[1])
    return peor


def _v_personaje(C, e):
    """Un rig DE PIE SOBRE EL MAPA, con peana y sombra de contacto, gesto por frase y `point_at`
    real. Sin la peana y la sombra el recorte flota y se lee como una calcomania pegada."""
    nombre = e['args'][0] if e['args'] else '01_burocrata'
    sobre = e['kw'].get('sobre') or (e['args'][1] if len(e['args']) > 1 else None)
    mira = e['kw'].get('senala') or e['kw'].get('sena') or e['kw'].get('mira')
    sc, mu = C.sc, C.mu
    t0 = e['t']
    # Un personaje que se ve dos segundos no es un personaje: es un parpadeo. Minimo `MIN_RIG_S`
    # segundos seguidos, que es lo que la reserva de camara de `planificar` hace posible.
    # la ventana que `planificar` le reservo a la camara (misma clase, mismo sitio). Los fundidos
    # de entrada y salida no cuentan como «visible», asi que la reserva ya trae 1,6 s de mas.
    t1 = min(C.dur - 0.05, (e.get('ventana_rig') or (t0, t0 + MIN_RIG_S + 1.6))[1])
    t1 = max(t1, t0 + 1.2)
    p = _a_tierra(C, C.P(sobre) if sobre else C.P(e.get('sitio') or list(mu.pts)[0]),
                  C.avisos, sobre or '?')
    rj = json.load(open(os.path.join(M.ELENCO, 'rig', nombre, 'rig.json'), encoding='utf-8'))
    tor = rj['piezas']['torso']
    alto_rel = float(e['kw'].get('alto', MIN_RIG_H[C.formato] + 0.03))
    # El rig NO puede cambiar de escala (las piezas se redimensionan al construirlo), asi que se
    # dimensiona contra el zoom MINIMO de su vida: en el plano mas abierto mide exactamente
    # `alto_rel` y en el resto, mas. `_vida_mundo` garantiza que ese "mas" no pasa de 1,55x.
    z_medio = max(1e-6, _zoom_min(C, t0, t1) * 1.04)
    alto_pieza = max(b[3] for b in rj['piezas'].values()) - min(b[1] for b in rj['piezas'].values())
    # Si a ese tamano no entra en la ventana, se ACHICA (hasta el minimo legible) en vez de
    # empujarlo: empujarlo lo saca del pais del que habla el guion y lo deja de pie sobre el mar.
    esc = (C.H * alto_rel / max(1e-6, z_medio)) / alto_pieza
    # ANCHO Y ALTO, cada uno contra su lado. Hasta el 16-sep se comparaba solo el ALTO del rig contra
    # min(alto, ancho) de la ventana: con los rigs del elenco, mas altos que anchos, daba igual. El de
    # Xi (`17_xi`, lienzo 864x738) es MAS ANCHO QUE ALTO y se salia 34 px por el costado en la S13
    # aunque su alto entraba de sobra. El 1,10 del ancho es el crecimiento de los brazos al gesticular.
    ancho_pieza = max(b[2] for b in rj['piezas'].values()) - min(b[0] for b in rj['piezas'].values())
    for _ in range(4):
        vent = [sc.window(min(tt, C.dur - 0.01)) for tt in (t0 + 0.4, (t0 + t1) / 2, t1 - 0.3)]
        cabe_h = min(v[3] - v[1] for v in vent) * 0.86
        cabe_w = min(v[2] - v[0] for v in vent) * 0.92 / 1.10
        nuevo = min(cabe_h / max(1e-6, alto_pieza), cabe_w / max(1e-6, ancho_pieza))
        if esc <= nuevo: break
        if nuevo * alto_pieza * _zoom_min(C, t0, t1) / C.H < MIN_RIG_H[C.formato]: break
        esc = nuevo
        C.avisos.append('linea %d: %s achicado para que entre entero en la ventana' % (e['linea'], nombre))
    ancho = int((tor[2] - tor[0]) * esc * 1.20)
    sh = Image.new('RGBA', (ancho + 90, 96), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([45, 30, ancho + 45, 72], fill=(20, 16, 12, 104))
    sh = sh.filter(ImageFilter.GaussianBlur(9))
    so = M.Obj(sh, z=40); so.name = 'sombra:' + nombre; so.bg = True; so.shadow = False
    so.x = M.Track(p[0]); so.y = M.Track(p[1] - 6); so.on, so.off = t0, t1
    so.a.set(t0, 0, 'hold'); so.a.set(t0 + 0.40, 1, 'io')
    so.a.set(max(t0 + 0.5, t1 - 0.35), 1, 'hold'); so.a.set(t1, 0, 'io')
    sc.add(so)
    pe = PR.rect(max(24, int(ancho * 0.60)), 16, MV.PAPEL, r=4)
    po = M.Obj(pe, z=41); po.name = 'peana:' + nombre; po.bg = True; po.shadow = False
    po.x = M.Track(p[0]); po.y = M.Track(p[1] - 2); po.on, po.off = t0, t1; po.a = so.a
    sc.add(po)
    r = M.Rig(nombre, 0, 0, sc=esc, z=44, on=t0, off=t1)
    r.x = M.Track(p[0] - (tor[0] + tor[2]) / 2 * esc); r.y = M.Track(p[1] - tor[3] * esc)
    r.name = nombre
    if mira: r.point_at(t0 + 0.9, C.P(mira), side='R', hold=min(2.6, max(1.0, t1 - t0 - 1.5)))
    r.nod(t0 + 0.45)
    g = t0 + 2.6; i = 0
    while g < t1 - 0.6: r.gesture(g, i); g += 2.6; i += 1     # un gesto chico por frase, automatico
    r.a.set(t0, 0, 'hold'); r.a.set(t0 + 0.45, 1, 'io')
    r.a.set(max(t0 + 0.6, t1 - 0.40), 1, 'hold'); r.a.set(t1, 0, 'io')
    sc.add(r)
    peor = _encajar(C, r, t0, t1, margen=24)
    if abs(peor[0]) + abs(peor[1]) > 0.5:
        # lo que se corrio se vuelve a apoyar en tierra: un rig no se queda flotando en el mar
        q = _a_tierra(C, (p[0] + peor[0], p[1] + peor[1]))
        r.x = M.Track(r.x(t0) + (q[0] - p[0] - peor[0])); r.y = M.Track(r.y(t0) + (q[1] - p[1] - peor[1]))
        so.x = M.Track(q[0]); so.y = M.Track(q[1] - 6)
        po.x = M.Track(q[0]); po.y = M.Track(q[1] - 2)
        C.avisos.append('linea %d: %s corrido %.0f,%.0f px de mundo para que entre entero y siga '
                        'en tierra' % (e['linea'], nombre, q[0] - p[0], q[1] - p[1]))
    C.rigs.append((t0, t1, r))
    C._relevo('objeto', t0)
    C._relevo_rect(C.caja_mundo(r, t0, min(t1, t0 + 4)), t0)     # el rig manda: el texto se corre
    C.registrar(r, 'rig', 'objeto', 'mapa', rect=C.caja_mundo(r, t0, t1), linea=e['linea'],
                sitio=sobre, mundo=True, texto=nombre, on=t0, off=t1)
    C.objetos[-1]['alto_rel'] = alto_rel


def _v_secuencia(C, e):
    """Cuadros pregenerados (`barra_d00..12`, `tanque_n00..12`): un deposito que se vacia, barras
    que crecen. No se escala la secuencia (la trampa conocida: `crecer` hace desaparecer props sin
    que el check lo note): se cambia de cuadro, y todos con la MISMA escala."""
    base = e['args'][0] if e['args'] else '?'
    n = int(e['args'][1]) if len(e['args']) > 1 else 13
    ims = [_imagen(C, '%s%02d' % (base, i)) for i in range(n)]
    t0 = e['t']; t1 = max(e.get('t_a') or e['t_off'], t0 + 1.2)
    hmax = max(i.height for i in ims); wmax = max(i.width for i in ims)
    k = (C.H * 0.30) / hmax
    if wmax * k > C.W * 0.86: k = (C.W * 0.86) / wmax
    fx = _fx(C, e, t0)
    fy, banda, _s = C._hueco('objeto', t0, e['t_off'], e.get('sitio'), wmax * k, hmax * k, fx)
    C._relevo('objeto', t0)
    paso = (t1 - t0) / max(1, n); ult = None
    for j, im in enumerate(ims):
        a = t0 + j * paso
        b = (e['t_off'] if j == n - 1 else a + paso + 0.012)
        o = M.Obj(im, z=50)
        o.name = ('prop:' + base) if j == n - 1 else 'seq:%s%02d' % (base, j)
        o.bg = False; o.shadow = False; o.wobble = 0.0; o.bob = 0.0; o.vida = 0.0
        o.sc = M.Track(k)
        o.x = M.Track(min(max(C.W * fx, im.width * k / 2 + 18), C.W - im.width * k / 2 - 18))
        o.y = M.Track(min(max(C.H * fy, im.height * k / 2 + 18), C.H - im.height * k / 2 - 18))
        o.on, o.off = a, b
        o.a = M.Track(1.0)
        if j == 0: o.a.set(a, 0, 'hold'); o.a.set(a + 0.22, 1, 'io')
        if j == n - 1: o.a.set(max(a + 0.22, b - 0.30), 1, 'hold'); o.a.set(b, 0, 'io')
        C.sc.add_hud(o); M.ev(a, 'tick', 0.16); ult = o
    r = (ult.x(t1) - wmax * k / 2, ult.y(t1) - hmax * k / 2,
         ult.x(t1) + wmax * k / 2, ult.y(t1) + hmax * k / 2)
    C.registrar(ult, 'secuencia', 'objeto', banda, rect=r, linea=e['linea'], texto=base,
                on=t0, off=e['t_off'])
    C.objetos[-1]['horneado'] = _texto_prop(C, '%s00' % base)


# ============================================================== 6. CHROME AUTOMATICO
def _resaltar(G, mu, T):
    """Palabras en rojo en el subtitulo: cifras, numeros dichos en letras, sitios y nombres propios.
    No hace falta escribirlas en la anotacion."""
    import sync
    res = set(x.lower() for x in G['resaltar'])
    sitios = {s.lower() for s in mu.pts if not s.startswith('_')}
    for ln in T['lineas']:
        pal = str(ln.get('texto', '')).split()
        for i, p in enumerate(pal):
            q = p.strip('.,;:!?"’“”').lower()
            if not q: continue
            if any(c.isdigit() for c in q) or q in sync.U or q in sync.MUL or q in sitios \
                    or q.split('-')[0] in sync.U:
                res.add(q)
            elif i and p[:1].isupper() and pal[i - 1][-1:] not in '.!?':
                res.add(q)
    return sorted(res)


def _gancho(C, G):
    """La tarjeta de gancho de un short: los primeros `HOOK` s, y SIEMPRE sobre el mapa en
    movimiento (por eso el compositor empuja cualquier MESA fuera de esa ventana)."""
    if not G['gancho']: return
    import shorts as SH
    card = SH.tarjeta_hook(list(G['gancho']), G['rojo'], size=int(C.W * 0.095),
                           ancho_max=int(C.W * 0.88))
    o, k = C.hud(card, 0.0, HOOK, 0.5, PREFERIDAS[C.formato]['alto'], z=80, entra=0.30, sale=0.35,
                 sfx=None, nombre='card:GANCHO', alto_max=0.30)
    r = (o.x(0) - card.width * k / 2, o.y(0) - card.height * k / 2,
         o.x(0) + card.width * k / 2, o.y(0) + card.height * k / 2)
    C.registrar(o, 'gancho', 'texto', 'alto', rect=r, linea=0, texto=' '.join(G['gancho']))


def _chip_barra(C, serie):
    """Chip `PART n OF N` y barra de progreso. Los pone el compositor para que el cuerpo se pueda
    mirar solo; si despues se arma con `shorts.armar_vertical`, se llama con `serie=None`."""
    if not serie: return
    W, H = C.W, C.H
    chip = PR.card('PART %d OF %d' % serie, size=int(W * 0.026), color=PAPEL, tcolor=TINTA)
    C.hud(chip, 0.0, C.dur, 0.5, 0.028, z=90, sfx=None, bg=True, nombre='chip:parte', deriva=False)
    alto = max(6, int(H * 0.005))
    barra = PR.rect(int(W * 0.92), alto, OCRE, r=alto // 2)
    o = M.Obj(barra, z=92); o.name = 'barra:progreso'; o.bg = True; o.shadow = False
    o.wobble = 0.0; o.bob = 0.0; o.vida = 0.0; o.on, o.off = 0.0, C.dur
    # `sc` escala los DOS ejes: `sy` compensa el alto (sc=p, sy=1/p) y queda una barra que crece de
    # verdad, sin 24 objetos y sin tocar el motor. Las dos pistas necesitan MUCHOS keyframes: 1/p no
    # es una recta, y con dos keyframes la barra salia cuatro veces mas gruesa a mitad del video.
    for i in range(41):
        t = C.dur * i / 40.0
        p = max(0.02, i / 40.0)
        o.sc.set(round(t, 3), p, 'lin')
        o.sy.set(round(t, 3), 1.0 / p, 'lin')
        o.x.set(round(t, 3), W * 0.04 + barra.width * p / 2, 'lin')
    o.y = M.Track(H - alto * 3)
    C.sc.add_hud(o)


def _huecos(C, t0, t1, paso=0.2):
    """[(a, b)] de los tramos sin ningun elemento de contenido, y el total."""
    gaps = []; ini = None; t = t0; tot = 0.0
    while t < t1:
        vis = [o for o in C.sc.visible(min(t, C.dur - 0.01))
               if not (getattr(o, 'name', '') or '').startswith(('rotulo:', 'sub:', 'mundo:'))]
        if not vis:
            tot += paso
            if ini is None: ini = t
        elif ini is not None:
            gaps.append((ini, t)); ini = None
        t += paso
    if ini is not None: gaps.append((ini, t1))
    return gaps, tot


def _mismo_tramo(C, t0, t1):
    """True si entre `t0` y `t1` no se cambia de escenario (mapa <-> mesa)."""
    tipos = {p[2] for p in C.planos if p[0] < t1 - 0.01 and p[1] > t0 + 0.01}
    return len(tipos) <= 1


def _rellenar(C, tope=0.6):
    """NINGUNA linea con pantalla vacia. Por linea, mientras el tiempo sin un solo elemento de
    contenido pase de `tope` segundos, estira el ultimo objeto que murio antes del hueco mas grande
    hasta que entra el siguiente. Es la bandera VACIO de `sync.py`, resuelta al COMPONER en vez de
    avisada despues.

    Lo que NO se estira, y por que: el gancho (dura lo que dura), el pie de una cifra (sin la cifra
    arriba no dice nada), el documento y su titulo (pertenecen a SU plano de mesa) y nada que al
    estirarse cruce a otro escenario o acabe encima del sitio del que habla la voz."""
    for l in C.T['lineas']:
        for _ in range(4):
            gaps, vac = _huecos(C, float(l['inicio']), min(float(l['fin']), C.dur))
            if vac <= tope or not gaps: break
            a, b = max(gaps, key=lambda g: g[1] - g[0])
            # se estira HASTA que entra el siguiente, ni un cuadro mas: si no, los dos coinciden en
            # pantalla y el hueco se cambia por un solape
            nxt = min([o['on'] for o in C.objetos if o['on'] > a + 0.01] or [C.dur - 0.02])
            objetivo = min(nxt, b + 0.05, C.dur - 0.02)
            cand = sorted([o for o in C.objetos
                           if o['off'] <= a + 0.1
                           and o['kind'] not in ('rotulo', 'pie', 'doc', 'gancho')
                           and not o.get('de_doc')], key=lambda x: -x['off'])
            # los sitios de TODAS las lineas que el estiron va a cruzar: el cartel no puede acabar
            # encima del pin del que habla la voz dos lineas despues
            sitios = {o0.get('sitio') for o0 in ()} | {None}
            for l2 in C.T['lineas']:
                if l2['fin'] > a - 0.2 and l2['inicio'] < objetivo + 0.2:
                    sitios.add(_sitio_de(l2.get('texto', ''), C.mu))
            sitios.discard(None)
            for o in cand[:6]:
                if not _mismo_tramo(C, o['off'] - 0.05, objetivo): continue
                if any(C._sin_pin(s, o['off'], objetivo, o['rect'], o['off']) < objetivo - 0.05
                       for s in sitios | ({o['sitio']} if o['sitio'] else set())): continue
                C.estirar(o, objetivo)
                C.avisos.append('%.2f-%.2f s sin contenido: se estira %r hasta %.2f s'
                                % (a, b, getattr(o['obj'], 'name', '')[:30], o['off']))
                break
            else:
                C.avisos.append('hueco de %.2f a %.2f s que no se puede tapar sin romper otra '
                                'regla: hace falta un verbo mas en esa linea' % (a, b))
                break


def _claves(texto, mu, n=4):
    """Las 2-4 palabras clave de una linea sin `V:`: cifras, nombres propios y sitios. Asi NINGUNA
    linea queda sin una imagen que diga lo que dice la voz."""
    pal = [p for p in re.split(r'\s+', str(texto)) if p]
    out = []
    for i, p in enumerate(pal):
        q = p.strip('.,;:!?"’“”—')
        if not q: continue
        if any(c.isdigit() for c in q) or q in mu.pts or (i and q[:1].isupper()): out.append(q.upper())
    if not out:
        out = [x.upper() for x in sorted([p.strip('.,;:!?"') for p in pal if len(p) > 4],
                                         key=len, reverse=True)[:2]]
    return ' '.join(out[:n])


# ============================================================== 7. BUILD
def build(guion, tiempos, palabras=None, formato='vertical', mundos=None, serie=None,
          beat=None, base=None, out=None, verbose=True, ini=None, fin=None):
    """Guion anotado -> (Scene, info). `info` lleva todo lo que `check` necesita mirar.

    `beat` puede ser un numero o una lista de numeros. `ini`/`fin` FUERZAN la ventana global del
    tramo (en segundos del `tiempos.json` entero) en vez de deducirla de la primera y la ultima
    linea. Es lo que necesita un EPISODIO: se compone por tramos —cada uno con su mundo— y los
    tramos tienen que quedar pegados al milisegundo, porque despues se concatenan bajo UNA voz.
    Sin esto, cada tramo se recorta a sus lineas (-0,45 / +0,70 s) y entre dos tramos quedaba un
    hueco de 0,35 s que el montaje no puede rellenar con nada."""
    M.EVENTS.clear()
    base = base or os.path.dirname(os.path.abspath(guion))
    G = leer_guion(guion)
    if serie is None and G['serie']: serie = G['serie']
    T = json.load(open(tiempos, encoding='utf-8')) if isinstance(tiempos, str) else dict(tiempos)
    if palabras is None and isinstance(tiempos, str):
        p = os.path.join(os.path.dirname(os.path.abspath(tiempos)), '_palabras.json')
        palabras = p if os.path.exists(p) else None
    # ---- mundo
    spec = G['mundo']
    if spec is None and mundos:
        spec = json.load(open(mundos, encoding='utf-8')) if isinstance(mundos, str) else mundos
    if spec is None:
        for c in (os.path.join(base, 'mundo.json'),
                  os.path.abspath(os.path.join(base, '..', '..', 'mundo.json'))):
            if os.path.exists(c): spec = json.load(open(c, encoding='utf-8')); break
    if spec is None: raise SystemExit('compo: falta el mundo (bloque ```mundo o mundo.json)')
    arte = spec.get('out_dir') or os.path.join(base, 'arte', 'assets')
    if not os.path.isabs(arte): arte = os.path.abspath(os.path.join(base, arte))
    mu = mundo_de(spec, arte)
    # ---- recorte por beat (un episodio se compone beat a beat)
    L = list(T['lineas'])
    if beat is not None:
        bs = set(beat) if isinstance(beat, (list, tuple, set)) else {beat}
        L = [l for l in L if l.get('b') in bs]
        if not L: raise SystemExit('compo: el beat %s no tiene lineas en tiempos.json' % beat)
    if ini is not None or fin is not None:
        a_, b_ = (-1e9 if ini is None else float(ini)), (1e9 if fin is None else float(fin))
        L = [l for l in L if a_ - 1e-6 <= float(l['inicio']) < b_ - 1e-6]
        if not L: raise SystemExit('compo: la ventana %s-%s no tiene lineas' % (ini, fin))
    t_ini = float(ini) if ini is not None else float(L[0]['inicio']) - 0.45
    _dur = (float(fin) - t_ini) if fin is not None else (float(L[-1]['fin']) - t_ini + 0.7)
    T2 = {'lineas': [dict(l, inicio=float(l['inicio']) - t_ini, fin=float(l['fin']) - t_ini)
                     for l in L],
          'dur': _dur}
    praw = json.load(open(palabras, encoding='utf-8')) if isinstance(palabras, str) else (palabras or [])
    _p0 = t_ini - 0.15 if ini is not None else float(L[0]['inicio']) - 0.6
    _p1 = t_ini + _dur + 0.15 if fin is not None else float(L[-1]['fin']) + 0.6
    praw = [[w, float(a) - t_ini, float(b) - t_ini] for w, a, b in praw
            if _p0 <= float(a) <= _p1]
    if not praw:           # sin timestamps de la voz: reparto por caracteres dentro de cada linea
        for l in T2['lineas']:
            ws = str(l['texto']).split(); n = sum(len(w) for w in ws) or 1; t = l['inicio']
            for w in ws:
                d = (l['fin'] - l['inicio']) * len(w) / n
                praw.append([w, t, t + d]); t += d
    P = Palabras(praw)
    C = Compo(mu, formato, T2, P, G, serie=serie, base=base)
    # ---- casar las lineas del guion con las de tiempos.json (por TEXTO, no por orden ciego)
    gl = _casar(G['lineas'], T2['lineas'], C.avisos)
    # ---- eventos: cada verbo con su instante real
    eventos = []
    for i, ln in enumerate(T2['lineas']):
        t0, t1 = float(ln['inicio']), float(ln['fin'])
        verbos = list(gl[i]['verbos']) if gl[i] else []
        if not verbos:
            txt = _claves(ln.get('texto', ''), mu)
            verbos = [{'verbo': 'TARJETA', 'args': [txt], 'kw': {}, 'ancla': None, 'off': 0.0,
                       'fuente': 'auto'}]
            C.avisos.append('linea %d SIN V:: se pone TARJETA("%s") con las palabras clave' % (i, txt))
        sitio = _sitio_de(ln.get('texto', ''), mu)
        # El instante de cada verbo sale de SU palabra. El orden en que estan escritos solo desempata
        # los que caen a la vez: forzar el orden de escritura movia una tarjeta anclada a la primera
        # palabra de la linea detras de un PINTA anclado a la quinta, y dejaba tres segundos de mapa
        # sin nada encima.
        ts = []
        for v in verbos:
            t = t0 + 0.05
            if v['ancla']:
                tt = P.t(v['ancla'], desde=t0 - 0.8, hasta=t1 + 0.6, avisos=C.avisos, linea=i)
                if tt is not None: t = tt
            ts.append(max(t0 + 0.02, min(t + v['off'], C.dur - 0.5)))
        ult = -1e9
        for k in sorted(range(len(verbos)), key=lambda j: (ts[j], j)):
            if ts[k] < ult + 0.25: ts[k] = ult + 0.25
            ult = ts[k]
        for v, t in zip(verbos, ts):
            if v['verbo'] in ('DOC', 'MESA') and G['gancho'] and t < HOOK + 0.1:
                C.avisos.append('linea %d: la MESA caia dentro del gancho (%.2f s); se corre a '
                                '%.2f s (el gancho va sobre el MAPA en movimiento)' % (i, t, HOOK + 0.1))
                t = HOOK + 0.1
            # S13 (16-sep): una TARJETA/CIFRA/SELLO/ROTULO anclada dentro del gancho lo RELEVABA (misma
            # familia `texto`) y el short arrancaba sin gancho: en la pieza 2 «THIRD OF JANUARY» en
            # «third» (1,2 s) lo borro. Ningun chequeo lo vio; salio mirando cuadros del render.
            if v['verbo'] in ('TARJETA', 'CIFRA', 'SELLO', 'ROTULO') and G['gancho'] and t < HOOK + 0.1:
                C.avisos.append('linea %d: %s caia dentro del gancho (%.2f s); se corre a %.2f s'
                                % (i, v['verbo'], t, HOOK + 0.1))
                t = HOOK + 0.1
            e = dict(v); e.update({'t': round(t, 3), 'linea': i, 't_linea': (t0, t1),
                                   'sitio': (v['args'][0] if (v['verbo'] == 'MAPA' and v['args'])
                                             else sitio),
                                   'sitio_sig': _sitio_de(T2['lineas'][i + 1].get('texto', ''), mu)
                                   if i + 1 < len(T2['lineas']) else None})
            if v['verbo'] == 'SECUENCIA':
                a = P.t(v['kw'].get('de', ''), t0 - 0.8, t1 + 0.4) if v['kw'].get('de') else t
                b = P.t(v['kw'].get('a', ''), t0 - 0.8, t1 + 1.2) if v['kw'].get('a') else t1
                e['t'] = round(a or t, 3); e['t_a'] = round(b or t1, 3)
            eventos.append(e)
    eventos.sort(key=lambda e: e['t'])
    # ---- vida: hasta que otro ocupe su slot (`_relevo`) o hasta el fin de la linea siguiente
    for e in eventos:
        i = e['linea']
        fin_sig = float(T2['lineas'][min(i + 1, len(T2['lineas']) - 1)]['fin'])
        # hasta el fin de la linea SIGUIENTE (asi un cartel cruza el corte, que es lo que el HUD del
        # v4 permite y el v3 no), pero nunca mas de 3 s despues de la suya: en un short las lineas
        # duran 8-13 s y sin este tope un sello se quedaba ocho segundos apilado bajo la cifra
        # siguiente.
        off = min(fin_sig, float(T2['lineas'][i]['fin']) + 3.0, e['t'] + VIDA_MAX, C.dur - 0.05)
        e['t_off'] = round(max(e['t'] + VIDA_MIN, off), 3)
        if i >= len(T2['lineas']) - 1: e['t_off'] = round(C.dur - 0.02, 3)
    # ---- camara
    C.planificar(eventos)
    for e in eventos:
        e['t_fin_plano'] = _fin_tramo(C.planos, e['t'], C.dur)
    C.arbitrar_rojo(eventos)
    _gancho(C, G)
    _ejecutar(C, eventos)
    if beat is not None:
        # el titulo del beat QUE SE ESTA COMPONIENDO (el de las lineas casadas), no el del primero
        # del guion: un guion de episodio entero trae once `## BEAT` y el rotulo salia siempre el
        # del cold open. Y si la anotacion ya puso un ROTULO, no se duplica.
        tit = next((x['beat_titulo'] for x in gl if x and x.get('beat_titulo')), '')
        if any(o['kind'] == 'rotulo' for o in C.objetos): tit = ''
        if tit:
            _v_rotulo(C, {'args': [tit.upper()[:26]], 't': 0.35, 't_off': min(C.dur - 0.1, 8.0),
                          'linea': 0, 'kw': {}})
    _rellenar(C)
    res = _resaltar(G, mu, T2)
    C.sc.subtitulos(P.pal, estilo='banda', fy=SUB_FY[formato], resaltar=res, ancho=0.88,
                    size=int(C.W * (0.060 if formato == 'vertical' else 0.026)))
    _chip_barra(C, serie)
    C.sc.dur = C.dur
    info = {'formato': formato, 'W': C.W, 'H': C.H, 'dur': C.dur, 'mundo': mu, 'compo': C,
            'lineas': T2['lineas'], 'planos': C.planos, 'objetos': C.objetos, 'rigs': C.rigs,
            'eventos': eventos, 'avisos': C.avisos, 'guion': guion, 'base': base,
            'anotaciones': G['n_anot'], 'out': out or os.path.join(base, '_qc'), 't_ini': t_ini,
            'resaltar': res, 'serie': serie, 'texto_ok': G['texto_ok']}
    if verbose:
        print('compo: %s %dx%d · %.2f s · %d lineas · %d verbos · %d planos · %d objetos · %d '
              'lineas de anotacion' % (formato, C.W, C.H, C.dur, len(T2['lineas']), len(eventos),
                                       len(C.planos), len(C.objetos), G['n_anot']))
        for a in C.avisos: print('   aviso: ' + a)
    return C.sc, info


def _fin_tramo(planos, t, dur):
    """Fin del TRAMO (planos seguidos del mismo tipo), no del plano: un DOC que dura 5,3 s se parte
    en dos planos y el documento tiene que seguir ahi al otro lado del corte."""
    i = next((k for k, p in enumerate(planos) if p[0] - 0.01 <= t < p[1]), None)
    if i is None: return dur
    tipo = planos[i][2]; fin = planos[i][1]
    for p in planos[i + 1:]:
        if p[2] != tipo: break
        fin = p[1]
    return fin


def _casar(gl, tl, avisos):
    """Empareja las lineas `A:` del guion con las de `tiempos.json`. Por TEXTO normalizado, no por
    indice: un guion con una linea de mas dejaria toda la partitura corrida medio video."""
    out = [None] * len(tl); usadas = set(); j = 0
    for i, t in enumerate(tl):
        q = _norm_linea(t.get('texto', ''))
        mejor, punt = None, 0.0
        for k in range(max(0, j - 1), len(gl)):
            if k in usadas: continue
            p = _parecido(q, _norm_linea(gl[k]['texto']))
            if p > punt: mejor, punt = k, p
            if p > 0.97: break
        if mejor is not None and punt >= 0.45:
            out[i] = gl[mejor]; usadas.add(mejor); j = mejor + 1
        else:
            avisos.append('linea %d de tiempos.json no casa con ninguna A: del guion (%r)'
                          % (i, str(t.get('texto', ''))[:44]))
    return out


def _parecido(a, b):
    sa, sb = set(a.split()), set(b.split())
    if not sa or not sb: return 0.0
    return len(sa & sb) / len(sa | sb)


def _sitio_de(texto, mu):
    for s in mu.pts:
        if s.startswith('_'): continue
        if re.search(r'\b%s\b' % re.escape(s), str(texto), re.I): return s
    return None


# ============================================================== 8. CHECK
def _regiones(mask, min_area):
    """Regiones conectadas de una mascara booleana, sin scipy. Devuelve [(area, cx, cy)]."""
    h, w = mask.shape
    vis = np.zeros_like(mask, dtype=bool); out = []
    ys, xs = np.nonzero(mask)
    for y0, x0 in zip(ys, xs):
        if vis[y0, x0]: continue
        pila = [(y0, x0)]; vis[y0, x0] = True; n = 0; sx = sy = 0
        while pila:
            y, x = pila.pop(); n += 1; sx += x; sy += y
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not vis[yy, xx]:
                    vis[yy, xx] = True; pila.append((yy, xx))
        if n >= min_area: out.append((n, sx / n, sy / n))
    return out


def _palabras_de(txt):
    return {w.lower() for w in re.findall(r'[A-Za-zÀ-ÿ]+', str(txt)) if len(w) >= 3}


def _mags(txt):
    import sync
    return sync.magnitudes(str(txt).replace(NL, ' '))


_FTE = {}


def _fuentes(base):
    """La hoja de fuentes de la produccion (`fuentes/referencia.md`), como palabras y magnitudes.
    Es la tercera y ultima justificacion posible de un texto en pantalla: lo que no dice la voz
    pero SI dice el documento verificado (el nombre del tribunal, el ano de la sentencia)."""
    d = os.path.abspath(base)
    if d in _FTE: return _FTE[d]
    txt = ''
    for _ in range(5):
        p = os.path.join(d, 'fuentes', 'referencia.md')
        if os.path.exists(p): txt = open(p, encoding='utf-8').read(); break
        d = os.path.dirname(d)
    _FTE[os.path.abspath(base)] = (_palabras_de(txt), _mags(txt))
    return _FTE[os.path.abspath(base)]


def _dicho(w, palabras):
    """`w` esta dicho si aparece igual, si una contiene a la otra (>= 4 letras) o si comparten 5
    letras de raiz: «supremo» y «supreme» son la misma palabra en dos idiomas."""
    if w in palabras: return True
    for q in palabras:
        if len(w) >= 4 and (w.startswith(q[:len(w)]) or q.startswith(w[:len(q)])) and \
                min(len(w), len(q)) >= 4: return True
        if len(w) >= 5 and len(q) >= 5 and w[:5] == q[:5]: return True
    return False


def _cajas(info, C, t):
    """Los rectangulos de PANTALLA de todo lo vivo y visible en `t` (los del mundo, proyectados)."""
    out = []
    for o in info['objetos']:
        ob = o['obj']
        if not (o['on'] - 0.01 <= t < o['off']) or getattr(ob, 'bg', False): continue
        b = ob.bbox(t)
        if b is None: continue
        if o['mundo']:
            p0 = C.pantalla((b[0], b[1]), t); p1 = C.pantalla((b[2], b[3]), t)
            b = (p0[0], p0[1], p1[0], p1[1])
            if b[2] < 0 or b[0] > C.W or b[3] < 0 or b[1] > C.H: continue
        out.append((o, b))
    return out


def check(sc, info, paso=0.2, paso_rojo=2.0, out=None, abortar=True, verbose=True):
    """Las reglas de composicion, verificadas por codigo. Devuelve la lista de fallos y escribe
    `_qc/compo.md`. Aborta si hay alguno: es el punto de todo esto, que la calidad no dependa de
    que alguien mire la hoja de contacto linea por linea."""
    C = info['compo']; W, H = info['W'], info['H']; dur = info['dur']
    fallos = []
    def F(t, regla, txt, linea=None):
        fallos.append({'t': round(float(t), 2), 'regla': regla, 'linea': linea, 'texto': txt})
    lin = info['lineas']
    def _linea(t):
        for i, l in enumerate(lin):
            if l['inicio'] - 0.3 <= t <= l['fin'] + 0.3: return i
        return None

    # ---- (c) tamanos minimos
    for o in info['objetos']:
        k = o['kind']; nm = getattr(o['obj'], 'name', '') or ''
        if k in MIN_CUERPO and o['cuerpo'] and o['cuerpo'] / H < MIN_CUERPO[k] - 1e-6:
            F(o['on'], 'c-cuerpo', '%s %r con cuerpo %.0f px = %.1f %% del alto (minimo %.1f %%)'
              % (k, nm[:40], o['cuerpo'], 100 * o['cuerpo'] / H, 100 * MIN_CUERPO[k]), o['linea'])
        if k in ('tarjeta', 'cifra', 'sello'):
            for l in str(o.get('texto', '')).split(NL):
                # los signos sueltos no son palabras: `29 · VI · 2026` son tres, no cinco
                if len([p for p in l.split() if re.search(r'[A-Za-z0-9]', p)]) > MAX_PALABRAS:
                    F(o['on'], 'c-palabras', 'tarjeta con mas de %d palabras por linea: %r'
                      % (MAX_PALABRAS, l[:44]), o['linea'])
            if len(str(o.get('texto', '')).split(NL)) > 2:
                F(o['on'], 'c-lineas', 'tarjeta de mas de 2 lineas: %r' % nm[:44], o['linea'])
        if k == 'prop' and not o['mundo']:
            b = o['rect']
            if (b[2] - b[0]) / W < MIN_PROP_W - 1e-6:
                F(o['on'], 'c-prop', 'prop %r ocupa %.1f %% del ancho (minimo %.0f %%)'
                  % (nm, 100 * (b[2] - b[0]) / W, 100 * MIN_PROP_W), o['linea'])
        if k == 'prop' and o['mundo']:
            peor = None
            for u in (0.15, 0.5, 0.85):
                t = o['on'] + (o['off'] - o['on']) * u
                bb = o['obj'].bbox(t)
                if not bb: continue
                an = (bb[2] - bb[0]) * sc.zoom(t) / W
                if peor is None or an < peor[1]: peor = (t, an)
            if peor and peor[1] < MIN_PROP_W - 1e-6:
                F(peor[0], 'c-prop', 'prop de mapa %r se ve al %.1f %% del ancho (minimo %.0f %%)'
                  % (nm, 100 * peor[1], 100 * MIN_PROP_W), o['linea'])
        if k == 'rig':
            peor = None
            for u in (0.18, 0.5, 0.85):
                t = o['on'] + (o['off'] - o['on']) * u
                bb = o['obj'].bbox(t)
                if not bb: continue
                alto = (bb[3] - bb[1]) * sc.zoom(t) / H
                if peor is None or alto < peor[1]: peor = (t, alto)
            if peor and peor[1] < MIN_RIG_H[info['formato']] - 0.02:
                F(peor[0], 'c-rig', 'rig %r mide %.0f %% del alto (minimo %.0f %%)'
                  % (nm, 100 * peor[1], 100 * MIN_RIG_H[info['formato']]), o['linea'])

    # ---- (a) solape · (b) texto sobre el pin · (e) densidad
    t = 0.0; vistos = set()
    while t < dur:
        cajas = _cajas(info, C, t)
        cuenta = [o for o, b in cajas if o['kind'] not in ('rotulo', 'pie')]
        if len(cuenta) + 1 > MAX_ELEM and 'e|%d' % len(cuenta) not in vistos:
            vistos.add('e|%d' % len(cuenta))
            F(t, 'e-densidad', '%d elementos a la vez (+ subtitulo): %s'
              % (len(cuenta), ', '.join(getattr(o['obj'], 'name', '')[:20] for o in cuenta)), _linea(t))
        for i in range(len(cajas)):
            for j in range(i + 1, len(cajas)):
                (oa, a), (ob_, b) = cajas[i], cajas[j]
                ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
                iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
                if ix <= 0 or iy <= 0: continue
                menor = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
                if menor <= 0: continue
                if ix * iy / menor > MAX_SOLAPE:
                    k = 'a|%s|%s' % (getattr(oa['obj'], 'name', ''), getattr(ob_['obj'], 'name', ''))
                    if k in vistos: continue
                    vistos.add(k)
                    F(t, 'a-solape', '%r y %r se pisan el %.0f %% del menor'
                      % (getattr(oa['obj'], 'name', '')[:28], getattr(ob_['obj'], 'name', '')[:28],
                         100 * ix * iy / menor), _linea(t))
        li = _linea(t)
        if li is not None:
            s = _sitio_de(lin[li].get('texto', ''), info['mundo'])
            caja = C.caja_pin(s, t) if s else None
            if caja:
                area = max(1.0, (caja[2] - caja[0]) * (caja[3] - caja[1]))
                for o, b in cajas:
                    if o['kind'] not in ('cifra', 'tarjeta', 'pie', 'sello', 'gancho'): continue
                    ix = max(0.0, min(b[2], caja[2]) - max(b[0], caja[0]))
                    iy = max(0.0, min(b[3], caja[3]) - max(b[1], caja[1]))
                    if ix * iy / area > 0.30:
                        k = 'b|%s|%s' % (s, getattr(o['obj'], 'name', ''))
                        if k in vistos: continue
                        vistos.add(k)
                        F(t, 'b-pin', 'el texto %r tapa el sitio %s del que habla la linea'
                          % (getattr(o['obj'], 'name', '')[:32], s), li)
        t += paso

    # ---- (f) ningun plano de mas de MAX_PLANO s sin cambio de contenido
    for p in info['planos']:
        if p[1] - p[0] > MAX_PLANO + 0.35:
            if not [o for o in info['objetos'] if p[0] + 0.3 < o['on'] < p[1] - 0.3]:
                F(p[0], 'f-plano', 'plano de %.1f s sin corte ni objeto nuevo' % (p[1] - p[0]),
                  _linea(p[0]))

    # ---- (g) cada linea con al menos un elemento de contenido
    for i, l in enumerate(lin):
        vac = 0.0; t = float(l['inicio'])
        while t < float(l['fin']):
            vis = [o for o in sc.visible(min(t, dur - 0.01))
                   if not (getattr(o, 'name', '') or '').startswith(('rotulo:', 'sub:', 'mundo:'))]
            if not vis: vac += 0.2
            t += 0.2
        if vac > 0.8:
            F(float(l['inicio']), 'g-vacio', 'la linea %d pasa %.1f s sin ningun elemento de '
              'contenido sobre el mapa' % (i, vac), i)

    # ---- (h) TEXTO_NO_DICHO: nada dice en pantalla lo que la voz no dice
    dicho_linea = [_palabras_de(l.get('texto', '')) for l in lin]
    dicho_beat = set().union(*dicho_linea) if dicho_linea else set()
    mag_linea = [_mags(l.get('texto', '')) for l in lin]
    mag_beat = set().union(*mag_linea) if mag_linea else set()
    fte, mag_fte = _fuentes(info['base'])
    libre = set(TEXTO_LIBRE) | {w.lower() for w in info.get('texto_ok', [])}
    # TEXTO_OK vale tambien para las CIFRAS: el valor nominal de un bono («$100») es la identidad
    # del papel, no una afirmacion sobre esta linea. Se declara y se ve, como todo lo demas.
    mag_ok = _mags(' '.join(str(x) for x in info.get('texto_ok', [])))
    for o in info['objetos']:
        txts = []
        if o['kind'] in ('tarjeta', 'cifra', 'pie', 'rotulo', 'sello', 'gancho'):
            txts.append(str(o.get('texto', '')))
        if o.get('horneado') is not None: txts.append(str(o['horneado']))
        elif o['kind'] in ('doc', 'prop', 'secuencia'):
            F(o['on'], 'h-sin-declarar', 'el prop %r puede llevar texto horneado y nadie lo declaro '
              '(TEXTOS_PROPS o prop_%s.txt)' % (o.get('texto', ''), o.get('texto', '')), o['linea'])
        li = o['linea'] if 0 <= o['linea'] < len(lin) else None
        dl = dicho_linea[li] if li is not None else set()
        ml = mag_linea[li] if li is not None else set()
        for txt in txts:
            for w in _palabras_de(txt):
                if w in libre or len(w) < 3: continue
                if _dicho(w, dl) or _dicho(w, dicho_beat) or _dicho(w, fte): continue
                F(o['on'], 'h-texto', 'en pantalla dice %r y la voz no lo dice ni esta en las '
                  'fuentes (%r)' % (w, txt.replace(NL, ' ')[:38]), o['linea'])
            for v in _mags(txt):
                import sync as _s
                if any(_s._casan(v, b) for b in (ml | mag_beat | mag_fte | mag_ok)): continue
                F(o['on'], 'h-cifra', 'en pantalla dice la cifra %g y la voz no la dice ni esta en '
                  'las fuentes (%r)' % (v, txt.replace(NL, ' ')[:38]), o['linea'])

    # ---- (i) TIERRA_EN_CUADRO: nada de planos de mar vacio con un pin
    for p in info['planos']:
        if p[2] != 'mapa': continue
        for u in (0.1, 0.5, 0.9):
            t = p[0] + (p[1] - p[0]) * u
            v = sc.window(min(t, dur - 0.01))
            ft = frac_tierra(info['mundo'], v)
            if ft >= MIN_TIERRA: continue
            cont = sum(max(0.0, min(b[2], W) - max(b[0], 0)) * max(0.0, min(b[3], H) - max(b[1], 0))
                       for _o, b in _cajas(info, C, min(t, dur - 0.01))) / (W * H)
            if ft + cont < MIN_TIERRA:
                F(t, 'i-tierra', 'la ventana tiene %.0f %% de tierra y %.0f %% de contenido '
                  '(minimo %.0f %% entre las dos)' % (100 * ft, 100 * cont, 100 * MIN_TIERRA),
                  _linea(t))
                break

    # ---- (j) PERSONAJE visible: de pie, sobre tierra y en pantalla `MIN_RIG_S` s seguidos
    for o in info['objetos']:
        if o['kind'] != 'rig': continue
        segs = 0.0; t = o['on']
        while t < o['off']:
            b = o['obj'].bbox(t)
            if b is not None:
                v = sc.window(min(t, dur - 0.01))
                dentro = (b[0] >= v[0] - 4 and b[1] >= v[1] - 4 and b[2] <= v[2] + 4 and b[3] <= v[3] + 4)
                if dentro and o['obj'].a(t) > 0.5: segs += 0.2
            t += 0.2
        if segs < MIN_RIG_S - 0.25:
            F(o['on'], 'j-rig', 'el rig %r se ve %.1f s enteros dentro de la ventana (minimo '
              '%.0f s)' % (getattr(o['obj'], 'name', ''), segs, MIN_RIG_S), o['linea'])
        m, _f, _i = tierra_mundo(info['mundo']); red = info['mundo']._tierra[3]
        x, y = int(o['obj'].x(o['on'] + 0.5) / red), int(o['obj'].y(o['on'] + 0.5) / red)
        # los pies caen abajo del ancla del rig (el rig se posiciona por su esquina superior)
        bb = o['obj'].bbox(o['on'] + 0.5)
        if bb: x, y = int((bb[0] + bb[2]) / 2 / red), int(bb[3] / red)
        if 0 <= y < m.shape[0] and 0 <= x < m.shape[1] and not m[y, x]:
            F(o['on'], 'j-agua', 'el rig %r esta de pie sobre el agua'
              % getattr(o['obj'], 'name', ''), o['linea'])

    # ---- regla 1 del canal: nada parcialmente cortado
    for t, nm, b, v in sc.check_framing(0.0, dur, step=0.25)[:20]:
        F(t, 'regla1', '%s sale del cuadro (bbox %s en %s)' % (nm, b, v), _linea(t))

    # ---- (d) un solo rojo saturado por cuadro
    # Se mide sobre el render a 405 px (el ancho de un telefono), en la ZONA DE COMPOSICION: la
    # franja del subtitulo queda fuera porque su resalte rojo es parte del subtitulo, esta siempre y
    # no compite por la mirada con el rojo del cuadro.
    t = 0.6
    hsub = int(405 * H / W * (SUB_FY[info['formato']] - 0.075))
    while t < dur:
        im = sc.render(min(t, dur - 0.01)).convert('RGB').resize((405, int(405 * H / W)), Image.LANCZOS)
        a = np.asarray(im).astype(int)[:hsub]
        m = (a[:, :, 0] > 170) & (a[:, :, 1] < 90) & (a[:, :, 2] < 80)
        if m.any():
            # Las letras de una cifra son manchas separadas: se dilata para que el texto de UNA
            # tarjeta cuente como UNA mancha. Y las manchas que caen DENTRO del mismo objeto (la
            # fecha y el sello «FIRME» impresos en el documento) cuentan como UN rojo: la regla es
            # un ELEMENTO rojo por cuadro, no una mancha.
            d = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(
                ImageFilter.MaxFilter(17))) > 127
            ar = _regiones(d, 120)
            cajas = _cajas(info, C, min(t, dur - 0.01))
            k = 405.0 / W
            grupos = {}
            for area, cx, cy in ar:
                due = 'mapa'
                for o, b in cajas:
                    if not (b[0] * k <= cx <= b[2] * k and b[1] * k <= cy <= b[3] * k): continue
                    # una mancha mas grande que el objeto no es del objeto: es el territorio que
                    # tiene debajo (Xi de pie sobre una China pintada de rojo)
                    if area > 1.5 * abs((b[2] - b[0]) * (b[3] - b[1])) * k * k: continue
                    due = id(o['obj']); break
                grupos[due] = grupos.get(due, 0) + area
            # Un TERRITORIO pintado de rojo (el rol `deudor`) no es un punto de atencion que compita
            # con una cifra: es el suelo narrando. Lo que si compite —y baja a ocre— es el pin o la
            # ruta, que son manchas chicas. El corte esta en el 8 % del cuadro.
            # El rojo que hay SOBRE EL MAPA solo cuenta si lo puso el compositor (una ruta que se
            # esta dibujando). Un territorio pintado por rol, o el trozo de ese territorio que
            # asoma por un borde, es el suelo narrando: no compite por la mirada con una cifra.
            if not any(x - 0.1 <= t <= y + 0.1 for x, y in C.rojo_mapa): grupos.pop('mapa', None)
            if len(grupos) > 1:
                F(t, 'd-rojo', '%d elementos rojos en el mismo cuadro (areas %s)'
                  % (len(grupos), sorted(grupos.values(), reverse=True)[:4]), _linea(t))
        t += paso_rojo

    out = out or info['out']
    os.makedirs(out, exist_ok=True)
    md = ['# Composicion — las reglas, verificadas', '',
          'Generado por `produccion/compo.py::check`. **%d fallos.**' % len(fallos), '',
          '| t | regla | linea | detalle |', '|---|---|---|---|']
    for f in sorted(fallos, key=lambda x: x['t']):
        md.append('| %.2f | %s | %s | %s |' % (f['t'], f['regla'],
                                               '-' if f['linea'] is None else f['linea'],
                                               f['texto'].replace('|', '/')))
    md += ['', '## Avisos del compositor (lo que se corrigio solo)', '']
    md += ['- ' + a for a in info['avisos']] or ['- ninguno']
    md += ['', '## Planos', '', '| # | t0 | t1 | tipo | zoom | sitio |', '|---|---|---|---|---|---|']
    for i, p in enumerate(info['planos']):
        md.append('| %d | %.2f | %.2f | %s | %.2f -> %.2f | %s |' % (i, p[0], p[1], p[2], p[4], p[6], p[7]))
    md += ['', '## Objetos', '', '| t | tipo | slot | cuerpo | texto |', '|---|---|---|---|---|']
    for o in sorted(info['objetos'], key=lambda x: x['on']):
        md.append('| %.2f-%.2f | %s | %s | %s | %s |'
                  % (o['on'], o['off'], o['kind'], o['banda'],
                     '%.0f px' % o['cuerpo'] if o['cuerpo'] else '-',
                     str(o.get('texto', '')).replace(NL, ' / ').replace('|', '/')[:42]))
    p_md = os.path.join(out, 'compo.md')
    open(p_md, 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    if verbose:
        print('check: %d fallos  ->  %s' % (len(fallos), p_md))
        for f in sorted(fallos, key=lambda x: x['t'])[:30]:
            print('   %6.2f  %-12s  %s' % (f['t'], f['regla'], f['texto'][:104]))
    if fallos and abortar:
        raise SystemExit('compo.check: %d reglas de composicion rotas (ver %s)' % (len(fallos), p_md))
    return fallos


# ============================================================== 9. SALIDAS
def hoja(sc, info, out=None, n=16, cols=4, w=300):
    """Hoja de contacto de `n` cuadros REALES + la vista a 405 px: lo que se mira antes de render."""
    out = out or info['out']; os.makedirs(out, exist_ok=True)
    W, H = info['W'], info['H']; dur = info['dur']
    h = int(w * H / W); rows = (n + cols - 1) // cols
    q = Image.new('RGB', (cols * w, rows * h), (18, 17, 15)); d = ImageDraw.Draw(q)
    for i in range(n):
        t = min(dur - 0.02, dur * (i + 0.5) / n)
        q.paste(sc.render(t).convert('RGB').resize((w, h), Image.LANCZOS),
                ((i % cols) * w, (i // cols) * h))
        d.rectangle([(i % cols) * w, (i // cols) * h, (i % cols) * w + 66, (i // cols) * h + 20],
                    fill=(0, 0, 0))
        d.text(((i % cols) * w + 5, (i // cols) * h + 2), '%.1fs' % t, fill=(255, 220, 120),
               font=PR.FONTC(18))
    p = os.path.join(out, 'compo_hoja.jpg'); q.save(p, quality=90)
    tw = 405; th = int(tw * H / W)
    p2 = os.path.join(out, 'compo_405.png')
    sc.render(dur * 0.45).convert('RGB').resize((tw, th), Image.LANCZOS).save(p2)
    print('hoja ->', p); print('405 px ->', p2)
    return p, p2


def auditar(sc, info, paso=1, hojas=True):
    """`sync.py` sobre la escena ya compuesta. Los tiempos van RECORTADOS al beat y corridos al
    cero de la escena, que es lo que el compositor construyo."""
    import sync
    r = sync.auditar(sc, {'lineas': info['lineas'], 'dur': info['dur']}, out=info['out'],
                     dur=info['dur'], paso=paso, hojas=hojas)
    print('sync:', {k: v for k, v in r.items() if not k.startswith('_')})
    return r


def _build_env():
    """Lo llama cada worker del pool de `M.render`: reconstruye la escena con los mismos argumentos."""
    kw = json.loads(os.environ['COMPO_ARGS'])
    kw['verbose'] = False
    if kw.get('serie'): kw['serie'] = tuple(kw['serie'])
    sc, _ = build(**kw)
    return sc


def render(sc, info, salida, audio=None, frames=None, kwargs=None, dur=None):
    os.environ['COMPO_ARGS'] = json.dumps(kwargs or {})
    os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True)
    return M.render('compo', '_build_env', dur or info['dur'], salida, audio=audio,
                    frames=frames or os.path.join(info['base'], '_frames_compo'))


def _tramo_audio(wav, t0, dur, destino):
    """El trozo de voz que le toca a este beat. `M.render` no sabe de beats: se le pasa un wav que
    ya empieza donde empieza la escena."""
    import subprocess
    os.makedirs(os.path.dirname(os.path.abspath(destino)), exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '%.3f' % t0, '-t', '%.3f' % (dur + 0.4),
                    '-i', wav, destino], check=True)
    return destino


# ============================================================== 10. CLI
def _resolver(d, pieza):
    """`<dir_produccion> --pieza 4` -> la carpeta de la pieza (S12: `shorts/04_ceuta`)."""
    d = os.path.abspath(d)
    if pieza is None: return d
    sh = os.path.join(d, 'shorts')
    if os.path.isdir(sh):
        for nom in sorted(os.listdir(sh)):
            if re.match(r'0*%d[_-]' % pieza, nom): return os.path.join(sh, nom)
    return d


def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return
    def opt(k, d=None): return a[a.index(k) + 1] if k in a else d
    pieza = opt('--pieza'); pieza = int(pieza) if pieza else None
    d = _resolver(a[0], pieza)
    guion = opt('--guion') or next((os.path.join(d, f) for f in ('guion_v.md', 'guion.md')
                                    if os.path.exists(os.path.join(d, f))), None)
    if not guion: raise SystemExit('compo: no encuentro guion_v.md ni guion.md en %s' % d)
    beat = opt('--beat'); serie = opt('--serie')
    kw = dict(guion=os.path.abspath(guion),
              tiempos=os.path.abspath(opt('--tiempos') or os.path.join(d, 'audio', 'tiempos.json')),
              formato=opt('--formato', 'vertical'),
              beat=int(beat) if beat else None,
              serie=tuple(int(x) for x in serie.split('/')) if serie else None,
              base=os.path.dirname(os.path.abspath(guion)),
              out=os.path.abspath(opt('--out') or os.path.join(d, '_qc')),
              mundos=opt('--mundo'))
    sc, info = build(**kw)
    if '--render' in a:
        check(sc, info, out=kw['out'], abortar='--forzar' not in a)
        sal = os.path.abspath(opt('--salida') or os.path.join(d, '_compo_test', 'cuerpo.mp4'))
        dur = min(float(opt('--dur', info['dur'])), info['dur'])
        wav = opt('--audio') or next((os.path.join(d, 'audio', f) for f in ('voz.wav', 'voz.mp3')
                                      if os.path.exists(os.path.join(d, 'audio', f))), None)
        if wav and info['t_ini'] > 0.5:
            wav = _tramo_audio(wav, info['t_ini'], dur,
                               os.path.join(os.path.dirname(sal), 'voz_tramo.wav'))
        print(render(sc, info, sal, audio=wav, frames=opt('--frames'), kwargs=kw, dur=dur))
    elif '--hoja' in a:
        hoja(sc, info, kw['out'])
    elif '--sync' in a:
        auditar(sc, info)
    else:
        check(sc, info, out=kw['out'], abortar='--forzar' not in a)


if __name__ == '__main__':
    main()
