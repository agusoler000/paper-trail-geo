# -*- coding: utf-8 -*-
"""INTRO y OUTRO genericas del canal Paper Trail: dos clips independientes, iguales para TODOS los videos.

Decision de Agustin (2026-09-07): la intro presenta el canal y la outro pide la suscripcion; son del canal,
no del episodio (nada de mapa de Rusia ni del cliffhanger). Se renderizan UNA vez y se pegan por delante y
por detras de cada episodio con pegar_intro_outro.py.

v2 (2026-09-11, pedido de Agustin: "tienen que incentivar a suscribirse y a darle likes" + "mas emotivas y
altisima calidad"). Lo que cambia respecto de la v1:
  * **LIKE ademas de SUBSCRIBE**, en las dos piezas, con un pulgar de papel propio (props_canal.pulgar).
  * **La hoja llena el cuadro** (leccion v1.8.0 de la skill). La v1 dejaba un tercio de madera vacia a la
    derecha y dos franjas de pared: se veia barato.
  * **Luz y vineta** (props_canal.luz) sobre una clase Overlay que se reescala a la ventana de camara en
    cada cuadro; es lo que convierte la mesa plana en un set.
  * **Arco, no secuencia de tarjetas**: la intro va de tres expedientes que caen -> la mesa entera del mundo
    -> UNO que se levanta bajo la luz -> el sello del canal. La outro va de cerrar el archivo -> pedir el
    like con el motivo -> pedir la suscripcion -> firma.
  * **Todo anclado a la voz** por timestamps por caracter de ElevenLabs (audio/canal/*.json), no a tiempos
    escritos a mano: si se regenera la voz, la coreografia se reacomoda sola.

    python intro_outro.py            -> intro_canal.mp4 (~14 s) y outro_canal.mp4 (~20 s)
    python intro_outro.py intro      -> solo la intro
    python intro_outro.py check      -> encuadre + ritmo + hoja de contacto de cuadros REALES, sin renderizar

Voz: audio/canal/intro_v2.mp3 + .json y outro_v2.mp3 + .json (George eleven-v3 via fal, USD 0,05 las dos).
Frames: carpeta propia _frames_canal (NUNCA produccion/_frames, que usa el render de los episodios).
"""
import os, sys, json, subprocess, shutil
import numpy as np, soundfile as sf
import motor as M, props as PR, props_canal as PC
from PIL import Image
sys.path.insert(0, M.BASE)
import mezcla
from mezcla import cargar, db, pista_sfx, SR


def sfx_paper(dur=0.28):
    """papel que se apoya sobre la mesa: soplo grave y corto (reemplaza al 'slide' agudo, que Agustin rechazo)"""
    n = int(dur * SR); x = mezcla.lowpass(mezcla.noise(n), 900) * mezcla.env(n, 0.03, dur * 0.5, 0.25, dur * 0.4)
    t = np.arange(n) / SR; x += 0.25 * np.sin(2 * np.pi * 140 * t) * mezcla.env(n, 0.005, 0.08, 0.0, 0.05)
    return x.astype(np.float32) * 0.35
mezcla.SFX['paper'] = sfx_paper
mezcla.SFX['slide'] = sfx_paper     # en estos clips, todo deslizamiento (incluidos los del rig) usa el sonido grave

A = M.ASSETS; AUD = os.path.join(M.BASE, 'audio', 'canal'); MUS = os.path.join(M.BASE, 'musica')
VOZ_INTRO = os.path.join(AUD, 'intro_v2.mp3'); VOZ_OUTRO = os.path.join(AUD, 'outro_v2.mp3')
TEMA = os.path.join(MUS, 'tema_canal.mp3')      # cortina propia del canal (Lyria, sin derechos de terceros)

VOZ_T0_INTRO = 0.45     # la voz arranca cuando el primer expediente ya toco la mesa
VOZ_T0_OUTRO = 1.15     # la voz arranca cuando el Burocrata ya entro y esta apoyando la carpeta
COLA_INTRO = 0.95
COLA_OUTRO = 3.20       # cola larga a proposito: es la ventana de pantalla final de YouTube
HOME_L = (96, 342); SC = 0.55

SHEET_S = 1.36          # 1500x900 -> 2040x1224: SANGRA por los cuatro lados, nunca se ve el borde de la hoja
LUZ_ANCHA = PC.luz(cx=0.47, cy=0.42, r=0.76, a=72, vin=205)     # ambiente de la intro
LUZ_FOCO = PC.luz(cx=0.50, cy=0.55, r=0.58, a=70, vin=150)      # se cierra sobre el expediente elegido
LUZ_OUTRO = PC.luz(cx=0.45, cy=0.50, r=0.72, a=80, vin=225)     # la outro pasa entera bajo la lampara


# ---------------------------------------------------------------- utilidades
class Overlay(M.Obj):
    """Capa que SIEMPRE llena la ventana de camara (luz, vineta). Sin ella, al hacer zoom la vineta
    quedaria descentrada: se veria una esquina oscura flotando en medio del cuadro."""
    def __init__(self, img, escena, z=300, a=1.0):
        M.Obj.__init__(self, img, z=z, a=a)
        self.esc = escena; self.bg = True; self.shadow = False; self.name = 'overlay'

    def bbox(self, t): return None

    def draw(self, canvas, t, off=(0, 0)):
        if not (self.on <= t < self.off): return
        a = self.a(t)
        if a <= 0.01: return
        x0, y0, x1, y1 = self.esc.window(t)
        im = self.img.resize((max(1, int(round(x1 - x0))), max(1, int(round(y1 - y0)))), Image.BILINEAR)
        if a < 0.995:
            al = im.split()[3].point(lambda v: int(v * a)); im = im.copy(); im.putalpha(al)
        canvas.alpha_composite(im, (int(round(x0)), int(round(y0))))


def _voz(nombre, claves, t0):
    """(tiempos de cada frase clave, fin de la voz) desde los timestamps por caracter de ElevenLabs."""
    d = json.load(open(os.path.join(AUD, nombre + '.json'), encoding='utf-8'))['timestamps']
    ch = []; st = []; en = []
    for e in d:
        ch += e['characters']; st += e['character_start_times_seconds']
        en += e.get('character_end_times_seconds', e['character_start_times_seconds'])
    s = ''.join(ch); out = {}
    for k, frase in claves.items():
        i = s.find(frase)
        assert i >= 0, 'no aparece en la voz de %s: %r' % (nombre, frase)
        out[k] = round(t0 + st[i], 3)
    return out, round(t0 + en[-1], 3)


CLAVES_INTRO = {'BORDER': 'Every border', 'WAR': 'Every war', 'DEAL': 'Every deal', 'SOME': 'Somewhere',
                'PT': 'This is Paper', 'LIKE': 'Like it', 'SUB': 'subscribe', 'FOLLOW': 'follow the paper'}
CLAVES_OUTRO = {'CLOSED': "That's the file", 'WORTH': 'If it was worth', 'LIKE': 'leave a like',
                'ONE': 'one thing', 'ELSE': 'somebody else', 'NEXT': 'next dispute',
                'SUB': 'subscribe', 'FOLLOW': 'Follow the paper'}


def T_INTRO():
    _, fin = _voz('intro_v2', CLAVES_INTRO, VOZ_T0_INTRO); return round(fin + COLA_INTRO, 2)


def T_OUTRO():
    _, fin = _voz('outro_v2', CLAVES_OUTRO, VOZ_T0_OUTRO); return round(fin + COLA_OUTRO, 2)


def _mesa(luz=None):
    """Mesa del canal: la hoja del MUNDO llenando el cuadro + luz calida + vineta. Igual en las dos piezas."""
    sc = M.Scene(os.path.join(A, 'fondo_piloto.png'))
    mp = M.Obj(os.path.join(A, 'mapa_mundo.png'), x=960, y=540, z=1, rot=0.4, sc=SHEET_S)
    mp.bg = True; mp.shadow = False; mp.name = 'hoja_mundo'; sc.add(mp)
    sc.add(Overlay(luz if luz is not None else LUZ_ANCHA, sc, z=300))
    return sc


def _card(sc, txt, t, x, y, size=64, color=PR.PAPEL, tcolor=PR.TINTA, z=90, dur=None, wob=0.6, sfx=None, rot=0):
    o = M.Obj(PR.card(txt, size=size, color=color, tcolor=tcolor), z=z, rot=rot); o.wobble = wob
    o.name = txt.replace('\n', ' ')[:24]
    if sfx: o.sfx = sfx
    o.pop(t, x, y)
    if dur: o.unpop(t + dur)
    sc.add(o); return o


def _doc(sc, t, x, y, s, rot, banda, z, sello=None, firma=False, seed=0, h=0.0):
    """un expediente que CAE sobre la mesa (fisica de papel del motor v3)"""
    o = M.Obj(PC.documento(banda=banda, seed=seed, sello_txt=sello, firma=firma), z=z, sc=s, rot=rot)
    o.name = 'doc%02d' % seed; o.wobble = 0.25
    o.drop(t, x, y, dur=0.5, h=h or 90, sc_=s, tilt=4.0)
    sc.add(o); return o


# ---------------------------------------------------------------- INTRO
# Arco: tres expedientes que caen (border / war / deal) -> la mesa entera del mundo -> UNO bajo la luz
# -> el sello del canal -> like + subscribe -> la firma. Todo anclado a la voz.
DOCS_MESA = [   # (x, y, rot, banda, seed) — la mesa del mundo. Verificado por check_framing.
    (300, 300, -6, PR.AZUL, 1), (560, 235, 4, PR.ROJO, 2), (1390, 250, -3, PR.AZUL, 3),
    (1660, 320, 7, PR.VERDE, 4), (215, 600, 5, PR.ROJO, 5), (1745, 610, -5, PR.AZUL, 6),
    (330, 880, -4, PR.VERDE, 7), (640, 915, 6, PR.AZUL, 8), (1280, 905, -6, PR.ROJO, 9),
    (1620, 880, 3, PR.AZUL, 10), (1130, 250, 8, PR.VERDE, 11), (860, 235, -7, PR.AZUL, 12),
]


def build_intro():
    M.EVENTS.clear()
    q, fin = _voz('intro_v2', CLAVES_INTRO, VOZ_T0_INTRO)
    T = round(fin + COLA_INTRO, 2)
    sc = _mesa()
    sc.cx = M.Track(940); sc.cy = M.Track(560); sc.zoom = M.Track(1.11)   # el Track de t=0 manda (v1.8.0)
    sc.parallax = 1.0

    # ---- 0. la mesa ya estaba usada antes de que empiece el video (que el cuadro 0 no este vacio)
    mn = M.Obj(PC.mancha(r=104), x=330, y=905, z=4, a=0.9); mn.name = 'cafe'; mn.shadow = False; sc.add(mn)
    M.ev(0.06, 'tick', 0.5)

    # ---- 1. los tres expedientes: "Every border. Every war. Every deal."
    tri = []
    for k, (tk, x, y, r, banda, sel, fir) in enumerate((
            (q['BORDER'], 700, 540, -5, PR.AZUL, 'RATIFIED', False),
            (q['WAR'],    930, 615, 4, PR.ROJO, 'DECLARED', False),
            (q['DEAL'],  1160, 688, -3, PR.OCRE, None, True))):
        o = _doc(sc, tk - 0.16, x, y, 1.52, r, banda, 40 + k, sello=sel, firma=fir, seed=90 + k, h=170)
        o.depth = 1.10 + k * 0.02
        M.ev(tk + 0.20, 'thump', 0.55 + k * 0.12)
        sc.shake(tk + 0.20, amp=3 + k * 1.6, dur=0.20)
        tri.append(o)

    # ---- 2. la mesa del mundo: los tres se achican y encajan, y caen doce mas alrededor
    t_ab = q['DEAL'] + 0.55                      # arranca el retroceso
    finales = ((760, 520, -4), (960, 570, 3), (1165, 615, -2))
    for o, (fx, fy, fr) in zip(tri, finales):
        o.scale(t_ab, t_ab + 1.5, 1.52, 0.50, 'soft')
        o.move(t_ab, t_ab + 1.5, (o.x(t_ab), o.y(t_ab)), (fx, fy), 'soft')
        o.spin(t_ab, t_ab + 1.5, o.rot(t_ab), fr, 'soft')
        o.depth = 1.03
    for k, (x, y, r, banda, seed) in enumerate(DOCS_MESA):
        t = t_ab + 0.18 + k * 0.115
        o = _doc(sc, t, x, y, 0.50, r, banda, 20 + k, seed=seed, firma=(seed % 4 == 0), h=70)
        o.depth = 1.02
    sc.cam(t_ab, t_ab + 1.9, (960, 545), 1.02, 'soft')     # el retroceso de camara acompaña, no lidera

    # ---- 3. "Somewhere, a piece of paper decided it": uno se levanta y la luz se cierra sobre el
    tS = q['SOME']
    heroe = M.Obj(PC.documento(banda=PR.OCRE, seed=7, sello_txt='SETTLED', firma=True), z=70, sc=0.50, rot=-2)
    heroe.name = 'heroe'; heroe.wobble = 0.2
    heroe.drop(tS - 0.55, 960, 570, dur=0.45, h=60, sc_=0.50)
    heroe.raise_(tS + 0.05, dur=0.7, lift=1.0)
    heroe.scale(tS + 0.05, tS + 1.1, 0.50, 0.92, 'soft')
    heroe.move(tS + 0.05, tS + 1.1, (960, 570), (960, 615), 'soft')
    heroe.depth = 1.09
    sc.add(heroe)
    foco = Overlay(LUZ_FOCO, sc, z=301, a=0.0); foco.fade(tS, tS + 1.2, 0.0, 1.0); sc.add(foco)
    vecinos = []
    for o in sc.layers:                                    # el resto de la mesa se apaga un punto
        if getattr(o, 'name', '').startswith('doc') and o is not heroe:
            o.fade(tS + 0.1, tS + 1.0, 1.0, 0.62); vecinos.append(o)

    # ---- 3b. los tres segundos que la voz calla: la mesa converge sobre el elegido
    # (sin esto, `report` marcaba un hueco de 3,2 s: nada se movia y nada sonaba entre la frase y el sello)
    tK = tS + 1.45
    for k, o in enumerate(sorted(vecinos, key=lambda o: abs(o.x(tK) - 960) + abs(o.y(tK) - 615))[:5]):
        t = tK + k * 0.33
        x0, y0 = o.x(t), o.y(t)
        o.raise_(t, dur=0.18, lift=0.7)
        o.move(t + 0.1, t + 0.85, (x0, y0), (x0 + (960 - x0) * 0.10, y0 + (615 - y0) * 0.10), 'soft')
        o.settle(t + 0.85, dur=0.2); M.ev(t + 0.1, 'paper', 0.45)
    sc.cam(tS + 1.2, q['PT'] - 0.15, (960, 575), 1.045, 'soft')

    # ---- 4. "This is Paper Trail": el sello del canal cae sobre el expediente y golpea
    tP = q['PT']
    f = M.Obj(PR.chip(color=PR.OCRE, r=76), z=95, on=tP - 0.45); f.name = 'sello'; f.depth = 1.12
    f.transit.append((tP - 0.5, tP - 0.02))                # entra desde arriba del cuadro, a proposito
    f.x.set(tP - 0.45, 960, 'hold'); f.y.set(tP - 0.45, -160, 'hold'); f.y.set(tP + 0.02, 560, 'in')
    f.scale(tP + 0.02, tP + 0.14, 1.0, 1.14, 'out'); f.scale(tP + 0.14, tP + 0.30, 1.14, 1.0, 'io')
    sc.add(f)
    M.ev(tP - 0.45, 'stinger', 0.75); M.ev(tP + 0.02, 'thump', 1.0)
    sc.shake(tP + 0.02, amp=11, dur=0.30)
    heroe.settle(tP + 0.02, dur=0.12)
    _card(sc, 'PAPER TRAIL', tP + 0.10, 960, 250, size=104, color=PR.OCRE, wob=0.25, sfx='stamp', z=110)

    # ---- 5. "Like it, subscribe": el pedido, como dos sellos sobre la mesa
    tL = q['LIKE']
    pg = M.Obj(PC.pulgar(w=196, color=PR.OCRE), z=120, sc=1.0, rot=0); pg.name = 'pulgar'; pg.depth = 1.14
    pg.drop(tL, 545, 800, dur=0.42, h=190, sc_=1.0, tilt=6.0)
    sc.add(pg)
    M.ev(tL + 0.30, 'thump', 0.85); sc.shake(tL + 0.30, amp=7, dur=0.22)
    _card(sc, 'LIKE', tL + 0.34, 560, 965, size=54, color=PR.PAPEL, wob=0.4, sfx='stamp', rot=-6, z=121)

    tU = q['SUB']
    _card(sc, 'SUBSCRIBE', tU, 1360, 800, size=70, color=PR.OCRE, wob=0.25, sfx='stamp', rot=5, z=121)
    M.ev(tU + 0.06, 'thump', 0.8); sc.shake(tU + 0.06, amp=7, dur=0.22)

    # ---- 6. "and follow the paper": la firma del canal
    _card(sc, 'Follow the paper.', q['FOLLOW'], 960, 380, size=46, wob=0.5, sfx='paper', z=110)
    sc.cam(q['FOLLOW'], T, (960, 555), 1.06, 'soft')
    return sc


# ---------------------------------------------------------------- OUTRO
# Arco: se cierra el archivo -> por que importa el like -> la suscripcion -> la firma.
# Todo lo permanente queda en la mitad IZQUIERDA: la derecha es para la pantalla final de YouTube.
DOCS_OUTRO = [(1500, 250, -4, PR.AZUL, 31), (1720, 430, 6, PR.ROJO, 32), (1560, 690, -5, PR.VERDE, 33),
              (1655, 845, 4, PR.AZUL, 34), (1290, 880, -6, PR.ROJO, 35)]


def build_outro():
    M.EVENTS.clear()
    q, fin = _voz('outro_v2', CLAVES_OUTRO, VOZ_T0_OUTRO)
    T = round(fin + COLA_OUTRO, 2)
    sc = _mesa(LUZ_OUTRO)
    sc.cx = M.Track(960); sc.cy = M.Track(545); sc.zoom = M.Track(1.03)
    sc.cam(0, T, (900, 530), 1.08, 'soft')                 # push-in lentisimo de punta a punta

    # la mesa sigue puesta, a media luz, del lado que YouTube no usa
    volados = []
    for x, y, r, banda, seed in DOCS_OUTRO:
        o = M.Obj(PC.documento(banda=banda, seed=seed), z=20, sc=0.48, rot=r, a=0.72)
        o.name = 'doc%02d' % seed; o.wobble = 0.25; o.x = M.Track(x); o.y = M.Track(y); o.depth = 1.02
        sc.add(o); volados.append(o)

    # ---- el Burocrata entra con la carpeta atada y la apoya
    r = M.Rig('01_burocrata', HOME_L[0], HOME_L[1], sc=SC, z=50, on=0.0)
    r.enter(0.0, 'L', 1.1, home=HOME_L); sc.add(r)
    pie = M.Obj(PC.sombra_pie(360, 82), x=HOME_L[0] + 214, y=HOME_L[1] + 556, z=49, on=1.0)
    pie.bg = True; pie.shadow = False; pie.name = 'sombra_pie'; pie.fade(1.0, 1.35, 0.0, 1.0); sc.add(pie)
    mano = M.Obj(os.path.join(A, 'prop_carpeta_atada.png'), z=51, sc=0.88, off=q['CLOSED'] - 0.05)
    mano.name = 'carpeta_mano'; mano.bg = True; r.hold(mano, 'R', 0.0, q['CLOSED'] - 0.05)

    tC = q['CLOSED']
    carp = M.Obj(os.path.join(A, 'prop_carpeta_atada.png'), z=60, sc=1.38, rot=-3); carp.name = 'carpeta'
    carp.depth = 1.08; carp.drop(tC - 0.05, 880, 600, dur=0.45, h=150, sc_=1.38, tilt=6.0)
    sc.add(carp)
    M.ev(tC + 0.30, 'thump', 0.95); sc.shake(tC + 0.30, amp=9, dur=0.26)
    # abajo a la derecha de la carpeta: en el centro tapaba su propio rotulo CASE FILE y se leia un amasijo
    cerr = _card(sc, 'CLOSED', tC + 0.55, 980, 680, size=54, color=PR.PAPEL, tcolor=PR.ROJO,
                 wob=0.3, sfx='stamp', rot=-11, z=61)
    r.nod(tC + 0.6)

    # ---- "If it was worth your time, leave a like": el pulgar cae donde estaba la carpeta
    tW = q['WORTH']; tL = q['LIKE']
    r.point_at(tW, (880, 520), side='R', hold=2.6, ret=True)   # brazo de PANTALLA derecha: las tarjetas estan a su derecha
    carp.unpop(tL - 0.5, 0.35); cerr.unpop(tL - 0.5, 0.35)
    pg = M.Obj(PC.pulgar(w=300, color=PR.OCRE), z=120); pg.name = 'pulgar'; pg.depth = 1.12
    pg.drop(tL, 880, 540, dur=0.5, h=260, sc_=1.0, tilt=7.0)
    sc.add(pg)
    M.ev(tL + 0.34, 'thump', 1.0); sc.shake(tL + 0.34, amp=12, dur=0.30)
    lk = _card(sc, 'LIKE', tL + 0.40, 880, 830, size=64, color=PR.PAPEL, wob=0.35, sfx='stamp', rot=-5, z=121)

    # ---- "...puts this table in front of somebody else": los expedientes salen de la mesa
    tO = q['ONE']
    for k, o in enumerate(volados[:3]):
        t = tO + 0.35 + k * 0.42
        o.raise_(t, dur=0.2, lift=1.0)
        o.flyout(t + 0.2, t + 1.05, (2160, o.y(t) - 120), 'in')
        M.ev(t + 0.2, 'slide', 0.55)

    # ...y entra uno nuevo: el expediente del proximo, que es de lo que se trata suscribirse.
    # (ademas tapa el hueco de 3,2 s que `report` marcaba entre los que se van y la frase de la suscripcion)
    tIn = q['ELSE'] + 0.75
    nuevo = M.Obj(PC.documento(banda=PR.OCRE, seed=41), z=22, sc=0.48, rot=5, a=0.85)
    nuevo.name = 'doc41'; nuevo.on = tIn; nuevo.depth = 1.02; nuevo.wobble = 0.25
    nuevo.x.set(tIn, 2150, 'hold'); nuevo.x.set(tIn + 0.9, 1650, 'soft')
    nuevo.y.set(tIn, 330, 'hold'); nuevo.y.set(tIn + 0.9, 420, 'soft')
    nuevo.lift.set(tIn, 1.0, 'hold'); nuevo.lift.set(tIn + 0.95, 0.0, 'in')
    nuevo.transit.append((tIn - 0.05, tIn + 0.75))
    M.ev(tIn, 'slide', 0.6); M.ev(tIn + 0.95, 'clack', 0.55)
    sc.add(nuevo)
    r.look(tIn + 0.15, -8); r.nod(tIn + 1.0, 7); r.look(tIn + 1.9, 0)

    # ---- "if you want the next dispute on it: subscribe"
    tN = q['NEXT']; tU = q['SUB']
    pg.scale(tN, tN + 0.9, 1.0, 0.36, 'soft'); pg.move(tN, tN + 0.9, (880, 540), (600, 930), 'soft')
    pg.spin(tN, tN + 0.9, pg.rot(tN), -9, 'soft')
    lk.unpop(tN, 0.3)
    _card(sc, 'LIKE', tN + 0.75, 782, 930, size=34, color=PR.PAPEL, wob=0.4, sfx='paper', rot=-6, z=121)
    r.point(tN + 0.2, 'R', hold=2.2, ret=True)

    _card(sc, 'SUBSCRIBE', tU, 852, 420, size=72, color=PR.OCRE, wob=0.25, sfx='stamp', rot=3, z=122)
    M.ev(tU + 0.06, 'thump', 1.0); sc.shake(tU + 0.06, amp=12, dur=0.30)
    r.nod(tU + 0.5, 10)

    # ---- "Follow the paper": la firma, y la cola larga para la pantalla final
    tF = q['FOLLOW']
    _card(sc, 'PAPER TRAIL', tF, 852, 690, size=54, color=PR.OCRE, wob=0.25, sfx='stamp', z=122)
    _card(sc, 'Follow the paper.', tF + 0.75, 852, 795, size=40, wob=0.5, sfx='paper', z=122)
    r.nod(tF + 1.6, 9); r.lean(T - 2.4, deg=5, dur=0.5, hold=1.2)
    M.ev(T - 2.35, 'paper', 0.4)        # la cola de la pantalla final no queda muda del todo
    return sc


# ---------------------------------------------------------------- audio + render aislado
def _mezcla(voz_p, t_voz, dur, out_wav, cue=None, mus_db=-11.0, sfx_db=3.0, duck_db=-6.0,
            mus_off=0.0, swell=None, lufs=None):
    """swell = [(t, ganancia_lineal), ...]: curva de la cortina, para que la musica RESPIRE con el relato
    (baja en el susurro del principio, crece en la revelacion). Interpolacion lineal entre puntos."""
    n = int(dur * SR); out = np.zeros(n, np.float32)
    v = cargar(voz_p); v = v / (np.max(np.abs(v)) + 1e-9) * 0.7; i = int(t_voz * SR)
    m = min(len(v), n - i); voz = np.zeros(n, np.float32); voz[i:i + m] = v[:m]
    out += voz + pista_sfx(list(M.EVENTS), n) * db(sfx_db)
    cp = cue or (TEMA if os.path.exists(TEMA) else os.path.join(MUS, 'cue_01_intro.mp3'))
    if os.path.exists(cp):
        x = cargar(cp)
        if mus_off: x = x[int(mus_off * SR):]
        x = x / (np.sqrt(np.mean(x ** 2)) + 1e-9) * 0.1 * db(mus_db)
        if len(x) < n: x = np.tile(x, int(np.ceil(n / max(1, len(x)))))
        x = x[:n].copy()
        if swell:
            ts = np.array([p[0] for p in swell], np.float32); gs = np.array([p[1] for p in swell], np.float32)
            x *= np.interp(np.arange(n) / SR, ts, gs).astype(np.float32)
        F = int(0.6 * SR); x[:F] *= np.linspace(0, 1, F)
        Fo = int(2.5 * SR); x[-Fo:] *= np.linspace(1, 0, Fo)
        x = mezcla.ducking(x, voz, depth_db=duck_db) if hasattr(mezcla, 'ducking') else x
        out[:len(x)] += x
    out = out / max(1.0, np.max(np.abs(out)) / 0.95)
    sf.write(out_wav, out, SR)
    if lufs is not None: _normalizar(out_wav, lufs)
    return out_wav


def _normalizar(wav, I=-19.0, TP=-1.5, LRA=11.0):
    """loudnorm en dos pasadas hasta I LUFS. Sin esto la intro/outro quedan ~5 dB por debajo del cuerpo
    (medido: episodios -19,2 LUFS; la mezcla cruda de estos clips daba -23,7 / -24,0)."""
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', wav,
                        '-af', 'loudnorm=I=%s:TP=%s:LRA=%s:print_format=json' % (I, TP, LRA),
                        '-f', 'null', '-'], capture_output=True, text=True)
    txt = r.stderr[r.stderr.rfind('{'):r.stderr.rfind('}') + 1]
    m = json.loads(txt)
    filtro = ('loudnorm=I=%s:TP=%s:LRA=%s:measured_I=%s:measured_TP=%s:measured_LRA=%s:'
              'measured_thresh=%s:offset=%s:linear=true:print_format=summary'
              % (I, TP, LRA, m['input_i'], m['input_tp'], m['input_lra'], m['input_thresh'], m['target_offset']))
    tmp = wav + '.norm.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-af', filtro,
                    '-ar', str(SR), '-c:a', 'pcm_s16le', tmp], check=True)
    os.replace(tmp, wav); return wav


def render(func, dur, out_mp4, audio, workers=6):
    outdir = os.path.join(M.BASE, '_frames_canal'); shutil.rmtree(outdir, ignore_errors=True); os.makedirs(outdir)
    import multiprocessing as mp
    n = int(dur * M.FPS); step = max(24, n // (workers * 4))
    chunks = [('intro_outro', func, i, min(n, i + step), outdir) for i in range(0, n, step)]
    with mp.Pool(workers) as pool:
        for _ in pool.imap_unordered(M._worker, chunks): pass
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(M.FPS), '-i', os.path.join(outdir, 'f_%06d.jpg'), '-i', audio,
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '19', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2', '-shortest', out_mp4], check=True)
    shutil.rmtree(outdir, ignore_errors=True); return out_mp4


def hacer(cual):
    M.EVENTS.clear()
    if cual == 'intro':
        build_intro(); T = T_INTRO()
        q, _ = _voz('intro_v2', CLAVES_INTRO, VOZ_T0_INTRO)
        swell = [(0, 0.42), (q['DEAL'], 0.5), (q['DEAL'] + 1.3, 1.0), (q['SOME'], 0.72),
                 (q['PT'] - 0.5, 0.8), (q['PT'] + 0.2, 1.15), (T, 1.0)]
        wav = _mezcla(VOZ_INTRO, VOZ_T0_INTRO, T, os.path.join(AUD, 'intro_mezcla.wav'), swell=swell, lufs=-19.0)
        return render('build_intro', T, os.path.join(M.BASE, 'intro_canal.mp4'), wav)
    build_outro(); T = T_OUTRO()
    q, _ = _voz('outro_v2', CLAVES_OUTRO, VOZ_T0_OUTRO)
    swell = [(0, 0.55), (q['LIKE'], 0.72), (q['ELSE'], 1.0), (q['SUB'], 1.18), (T, 1.0)]
    wav = _mezcla(VOZ_OUTRO, VOZ_T0_OUTRO, T, os.path.join(AUD, 'outro_mezcla.wav'), mus_off=9.0, swell=swell, lufs=-19.0)
    return render('build_outro', T, os.path.join(M.BASE, 'outro_canal.mp4'), wav)


# ---------------------------------------------------------------- check (regla 1: nada cortado)
def check(cuales=('intro', 'outro'), hoja=True):
    qd = os.path.join(M.BASE, '_qc_canal'); os.makedirs(qd, exist_ok=True)
    ok = True
    for cual in cuales:
        M.EVENTS.clear()
        sc = build_intro() if cual == 'intro' else build_outro()
        T = T_INTRO() if cual == 'intro' else T_OUTRO()
        q, _ = _voz('intro_v2' if cual == 'intro' else 'outro_v2',
                    CLAVES_INTRO if cual == 'intro' else CLAVES_OUTRO,
                    VOZ_T0_INTRO if cual == 'intro' else VOZ_T0_OUTRO)
        bad = sc.check_framing(0.1, T - 0.05, step=0.1)
        rep = sc.report(0, T, gap=3.0)
        print('== %s  dur %.2f s' % (cual, T))
        print('   voz:', ' '.join('%s=%.2f' % kv for kv in sorted(q.items(), key=lambda x: x[1])))
        print('   violaciones de encuadre: %d' % len(bad))
        for b in bad[:8]: print('     ', b)
        print('   ritmo:', rep)
        ok = ok and not bad
        if hoja:   # cuadros REALES del render, no la previsualizacion (leccion v1.8.0)
            ts = [round(T * k / 11, 2) for k in range(12)]
            cols, filas = 3, 4
            g = Image.new('RGB', (cols * 640, filas * 360), (20, 18, 14))
            for i, t in enumerate(ts):
                fr = sc.render(t).convert('RGB').resize((640, 360), Image.LANCZOS)
                g.paste(fr, ((i % cols) * 640, (i // cols) * 360))
            p = os.path.join(qd, '%s_grid.jpg' % cual); g.save(p, quality=93); print('   hoja ->', p)
    return ok


if __name__ == '__main__':
    args = sys.argv[1:] or ['intro', 'outro']
    if args[0] == 'check':
        sys.exit(0 if check(tuple(args[1:]) or ('intro', 'outro')) else 1)
    for a in args: print('->', hacer(a))
