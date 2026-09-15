# -*- coding: utf-8 -*-
"""Coreografia de la serie S10 («What Sweden Paid For»). Tres piezas; la partitura esta en `escenas.py`.

    python coreo.py check 1          # hoja de contacto + violaciones de encuadre
    python coreo.py render 1         # cuerpo 16:9 -> shorts/01_aviso/salida/cuerpo.mp4
    python coreo.py tramo 1 10 25    # tramo de prueba

Copia del motor de la serie S02 (encajar / CRECER / post-pase de solape / post-pase de encuadre /
pase de ritmo), que es hoy la plantilla de cualquier tanda de shorts. Lo unico que cambia es el arte
y una decision:

  **Esta pieza NO lleva hoja de mapa.** La historia pasa en una llamada, un expediente y un
  calendario, no en un territorio; y la hoja de mapa disponible (la del ep. 06, 2400x746, 8,5 px por
  grado) no permite un primer plano honesto de Tel Aviv ni de Abu Dabi — un sello de papel centrado
  en una ciudad ocupa 33 grados de longitud, que es justo lo que la regla 24 prohibe. Las tres
  banderas que se ven son **props sobre la mesa**, no marcas sobre un sitio: no afirman un lugar y
  por eso no le deben precision a nadie. Es la misma decision que tomo la S02.

Los props compartidos (`produccion/assets`) se buscan solos: `imagen()` mira primero el arte del
short, despues el del ep. 06 y por ultimo el catalogo del canal. De ahi salen cohete, dron, cerca,
moto, despertador, mazo y urna sin dibujar nada (regla 19).
"""
import json, os, sys, math
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
PROD = os.path.join(RAIZ, 'produccion')
sys.path.insert(0, PROD); sys.path.insert(0, AQUI)     # los workers de multiprocessing importan 'coreo'
import motor as M, props as PR
from PIL import Image

ARTE = os.path.join(AQUI, 'arte', 'assets')
EP06 = os.path.join(RAIZ, 'videos', '06_ia_economia_politica', 'arte', 'assets')
S05A = os.path.join(RAIZ, 'videos', 'S05_mapa_alianzas', 'arte', 'assets')   # bandera_tr
S01A = os.path.join(RAIZ, 'videos', 'S01_11s', 'arte', 'assets')             # escuela
EP05 = os.path.join(RAIZ, 'videos', '05_11s', 'arte', 'assets')              # billete
S = os.path.join(AQUI, 'shorts')
SERIE = json.load(open(os.path.join(S, 'serie.json'), encoding='utf-8'))
W, H = M.W, M.H



def pieza(n):
    for s in SERIE['shorts']:
        if s['n'] == n: return s
    raise SystemExit('pieza %s no existe' % n)


def imagen(name):
    """prop de la serie -> S05 / S01 / ep. 05 / ep. 06 (reuso) -> prop compartido del canal"""
    for base in (ARTE, S05A, S01A, EP05, EP06, os.path.join(PROD, 'assets')):
        p = os.path.join(base, 'prop_%s.png' % name)
        if os.path.exists(p): return Image.open(p).convert('RGBA')
    raise SystemExit('falta el prop: %s' % name)


def build(n=None):
    n = n or int(os.environ.get('PIEZA', '1'))
    P_ = pieza(n)
    d = os.path.join(S, P_['dir'])
    T = json.load(open(os.path.join(d, 'audio', 'tiempos.json'), encoding='utf-8'))
    LN = T['lineas']; DUR = T['dur']
    def L(i): return LN[min(i, len(LN)-1)]['inicio']
    def E(i): return LN[min(i, len(LN)-1)]['fin']

    del M.EVENTS[:]
    sc = M.Scene(os.path.join(ARTE, 'fondo.png'))

    # ---------------- planos: pocos y grandes (en el feed el cuadro se ve a 1000x563)
    # Las tres ventanas estan calculadas para CABER en su superficie (se comprobo con cuadros reales,
    # no con la hoja de contacto): CTR entero sobre la hoja de trabajo (x 0..1116, y 436..1064) y WALL
    # entero sobre la pared (y 0..415, con la mesa en 420).
    SH = {'WIDE': ((960, 600), 1.0),
          'CTR':  ((556, 750), 1.72),                    # la hoja de trabajo
          'MAP':  ((556, 742), 1.66),                    # la hoja de mapa (S04): un pelo mas abierta
          'WALL': ((960, 207), 2.60)}                    # la pared, limpia: tarjetas grandes
    def win(name):
        (cx, cy), z = SH[name]; w, h = W/z, H/z
        if z > 1.005: cx = min(max(cx, w/2), W-w/2); cy = min(max(cy, h/2), H-h/2)
        return (cx-w/2, cy-h/2, w, h, z)
    def at(name, fx, fy):
        x0, y0, w, h, z = win(name); return (x0+fx*w, y0+fy*h)
    PUSH = 0.05
    CRECER = 0.62                                       # la S02 usaba 0,52 y el cuadro quedaba vacio
    cur = ['WIDE']; CUTS = []
    def cut(t, name, push=PUSH):
        CUTS.append((t-0.02, name, push)); cur[0] = name; M.ev(t, 'tick', 0.25)

    def finalize_cam():
        CUTS.sort(key=lambda c: c[0])
        for i, (t, name, push) in enumerate(CUTS):
            x0, y0, w, h, z = win(name); cx, cy = x0+w/2, y0+h/2
            t1 = (CUTS[i+1][0] if i+1 < len(CUTS) else DUR)-0.06
            sc.cx.set(t, cx, 'hold'); sc.cy.set(t, cy, 'hold'); sc.zoom.set(t, z, 'hold')
            if push and t1 > t+0.5:
                sc.cx.set(t1, cx, 'lin'); sc.cy.set(t1, cy, 'lin'); sc.zoom.set(t1, z*(1+push), 'lin')

    # ---------------- encaje automatico: la regla 1 (nada cortado) por construccion
    def encajar(im, sc_, x, y, shot=None, m=0.80, crecer=0.0):
        s = shot or cur[0]; x0, y0, w, h, z = win(s)
        w2, h2 = w/(1+PUSH), h/(1+PUSH)
        x0 += (w-w2)/2; y0 += (h-h2)/2; w, h = w2, h2
        mw, mh = w*m, h*m
        OVER = 1.12
        if crecer > 0:
            g = min(w*crecer/max(1.0, im.width*sc_), h*crecer/max(1.0, im.height*sc_))
            if g > 1.0: sc_ *= g
        k = min(1.0, mw/max(1.0, im.width*sc_*OVER), mh/max(1.0, im.height*sc_*OVER))
        sc2 = sc_*k
        hw, hh = im.width*sc2*OVER/2+8, im.height*sc2*OVER/2+8
        x = min(max(x, x0+hw), x0+w-hw); y = min(max(y, y0+hh), y0+h-hh)
        return sc2, x, y

    # ---------------- helpers (mismos nombres que en los episodios y en la S01)
    def card(txt, t, fx=0.5, fy=0.24, shot=None, size=86, dur=None, color=PR.PAPEL, tcolor=PR.TINTA,
             z=80, spin=0):
        s = shot or cur[0]; x, y = at(s, fx, fy); zz = win(s)[4]
        im = PR.card(txt, size=max(20, int(size/zz)), color=color, tcolor=tcolor)
        _s, x, y = encajar(im, 1.0, x, y, s)
        if _s < 1.0: im = im.resize((max(1, int(im.width*_s)), max(1, int(im.height*_s))), Image.LANCZOS)
        o = M.Obj(im, z=z)
        o.wobble = 0.8; o.name = 'card:'+txt.replace(chr(10), ' '); o.pop(t, x, y)
        o.rot.set(t, spin-5, 'hold'); o.rot.set(t+0.7, spin, 'back')
        if dur: o.unpop(t+dur)
        sc.add(o); return o

    def P(name, t, fx=0.5, fy=0.5, shot=None, z=20, sc_=1.0, rot=0, dur=None, sfx=None, crecer=None):
        """Coloca un prop POR FRACCION de la ventana del plano: en un short no hay coordenadas
        absolutas utiles, porque cada plano es un recorte distinto de la misma mesa."""
        s = shot or cur[0]; x, y = at(s, fx, fy)
        im = imagen(name)
        sc_, x, y = encajar(im, sc_, x, y, s, crecer=CRECER if crecer is None else crecer)
        o = M.Obj(im, z=z, rot=rot); o.name = name
        o.sfx = sfx or ('stamp' if name.startswith('sello') else 'pop')
        o.on = t; o.at(t, x, y, 'hold'); o.scale(t, t+0.5, 0.2*sc_, sc_, 'back'); o.fade(t, t+0.15, 0, 1)
        M.ev(t, o.sfx)
        if dur: o.unpop(t+dur)
        sc.add(o); return o

    def drop(name, t, fx=0.5, fy=0.5, shot=None, z=20, sc_=1.0, dur=None, crecer=None):
        s = shot or cur[0]; x, y = at(s, fx, fy)
        im = imagen(name)
        sc_, x, y = encajar(im, sc_, x, y, s, crecer=CRECER if crecer is None else crecer)
        o = M.Obj(im, z=z); o.name = name; o.sfx = 'thump'
        o.drop(t, x, y, sc_=sc_)
        if dur: o.unpop(t+dur)
        sc.add(o); return o

    def stamp(name, t, fx=0.5, fy=0.5, shot=None, z=85, sc_=1.0, dur=None, crecer=0.60):
        # `crecer` es parametro desde el S05: con dos o tres sellos en el mismo beat, el 0,60
        # fijo los hacia solaparse y el post-pase apagaba al que habia entrado antes.
        s = shot or cur[0]; x, y = at(s, fx, fy)
        im = imagen(name); S0 = 1.45
        sfit, x, y = encajar(im, sc_*S0, x, y, s, crecer=crecer)
        sc_ = sfit/S0
        o = M.Obj(im, z=z); o.name = name; o.on = t; o.at(t, x, y, 'hold')
        o.scale(t, t+0.35, S0*sc_, sc_, 'in'); o.fade(t, t+0.1, 0, 1); M.ev(t+0.3, 'stamp', 0.9)
        sc.shake(t+0.3, 5, 0.2)
        if dur: o.unpop(t+dur)
        sc.add(o); return o

    def mapa(t, dur=None, shot='MAP', sangre=1.06):
        """La hoja de mapa, como FONDO del plano (no como prop).

        Va con `bg=True` a proposito: es una superficie, no un objeto. Los dos post-pases
        —solape y encuadre— la saltan, igual que saltan la mesa. Si entrara como prop normal,
        `encajar` la meteria al 80 % de la ventana y quedaria una franja de madera alrededor,
        que es exactamente la falla de la v1.9.0 («la hoja tiene que llenar el cuadro»).
        Por eso SANGRA un 6 % por los cuatro lados.

        Regla 24 (los puntos son exactos): las marcas ya vienen horneadas en
        `mapa10_ciudades.png`, que las dibuja con la proyeccion Mercator real de `arte/mapa.py`
        y ademas comprueba al generarse que ningun punto caiga fuera de la hoja y que Estocolmo
        y Sodertalje se separen. Aca no se coloca ni un punto a ojo."""
        x0, y0, w, h, z = win(shot)
        im = Image.open(os.path.join(ARTE, 'mapa10_ciudades.png')).convert('RGBA')
        
        k = max(w/im.width, h/im.height)*sangre
        im = im.resize((max(1, int(im.width*k)), max(1, int(im.height*k))), Image.LANCZOS)
        o = M.Obj(im, z=2); o.name = 'mapa_golfo'; o.bg = True
        o.on = t; o.at(t, x0+w/2, y0+h/2, 'hold')
        o.scale(t, t+0.7, 1.04, 1.0, 'io'); o.fade(t, t+0.45, 0, 1)
        if dur: o.unpop(t+dur)
        sc.add(o); return o

    def shake(o, t, n=6, deg=9, step=0.09):
        for k in range(n): o.rot.set(t+k*step, (-deg, deg)[k % 2], 'io')
        o.rot.set(t+n*step, 0, 'io')

    def girar(o, t0, t1, vueltas=1.0):
        """Giro continuo: para el vortice y para todo lo que tenga que estar VIVO en pantalla."""
        n = max(2, int((t1-t0)*4))
        for k in range(n+1):
            o.rot.set(t0+(t1-t0)*k/n, 360*vueltas*k/n, 'lin')
        return o

    def latir(o, t0, t1, a=0.06, per=1.1):
        """Respiracion lenta de escala: nada queda congelado (regla 3)."""
        k, t = 0, t0
        s0 = o.sc(t0) if hasattr(o, 'sc') else 1.0
        while t < t1:
            o.sc.set(t, s0*(1+a*(1 if k % 2 else -1)), 'io'); t += per/2; k += 1
        o.sc.set(min(t, t1), s0, 'io'); return o

    API = dict(sc=sc, L=L, E=E, LN=LN, DUR=DUR, cut=cut, at=at, card=card, P=P,
               drop=drop, stamp=stamp, shake=shake, girar=girar, mapa=mapa,
               latir=latir, imagen=imagen, PR=PR, M=M, W=W, H=H, cur=cur, win=win)
    import escenas
    getattr(escenas, 'e%02d' % n)(API)

    # ---- pase de ritmo (reglas 3 y 6: siempre algo en movimiento, >=10 cortes/min)
    def _gaps():
        ts = sorted(set(x[0] for x in M.EVENTS if 0 <= x[0] <= DUR))
        g = []; prev = 0.0
        for x in ts+[DUR]:
            if x-prev > 5.5: g.append((prev, x))
            prev = x
        return g
    for _ in range(6):
        gs = _gaps()
        if not gs: break
        for (a, b) in gs:
            tm = a+(b-a)/2
            plano = 'WIDE'
            for (tc, nm, ph) in sorted(CUTS):
                if tc <= tm: plano = nm
            cut(tm, plano, push=0.07)
    finalize_cam()

    # post-pase de SOLAPE (regla 22 de Agustin): dos cosas no se pisan salvo que sea a proposito.
    # Si un objeto nuevo tapa mas del 25 % del area de uno que ya estaba, el viejo se apaga al entrar
    # el nuevo. El 25 % deja pasar el apoyo de esquina de dos fichas —que se lee como una pila— y
    # atrapa lo que de verdad molesta: una tarjeta de texto encima de otra.
    obs = [o for o in sc.layers if not getattr(o, 'bg', False)]
    obs.sort(key=lambda o: o.on)
    for j, b in enumerate(obs):
        tb = b.on+0.40
        bb = b.bbox(tb)
        if bb is None: continue
        for a in obs[:j]:
            if not (a.on <= tb < a.off): continue
            ba = a.bbox(tb)
            if ba is None: continue
            ix = max(0.0, min(ba[2], bb[2])-max(ba[0], bb[0]))
            iy = max(0.0, min(ba[3], bb[3])-max(ba[1], bb[1]))
            if ix <= 0 or iy <= 0: continue
            menor = min((ba[2]-ba[0])*(ba[3]-ba[1]), (bb[2]-bb[0])*(bb[3]-bb[1]))
            if menor > 0 and (ix*iy)/menor > 0.25:
                a.off = min(a.off, b.on-0.05)

    # post-pase de encuadre: en cada corte se apaga lo que quedaria PARCIALMENTE visible
    for (tc, nombre, push) in CUTS:
        X0, Y0, W0, H0, z = win(nombre)                      # la ventana del CORTE (sin push)
        x0 = X0+(W0-W0/(1+push))/2; y0 = Y0+(H0-H0/(1+push))/2
        w, h = W0/(1+push), H0/(1+push)                      # la ventana al FINAL del push-in
        # `dentro` se juzga con la ventana chica (tiene que entrar durante todo el push) y `fuera` con
        # la grande: juzgar las dos con la chica dejaba pasar objetos que asoman 3 px en el instante
        # del corte y el chequeo de encuadre los marcaba despues.
        for o in sc.layers:
            if getattr(o, 'bg', False): continue
            tt = tc+0.10
            if not (o.on <= tt < o.off): continue
            b = o.bbox(tt)
            if b is None: continue
            dentro = b[0] >= x0-3 and b[1] >= y0-3 and b[2] <= x0+w+3 and b[3] <= y0+h+3
            fuera = b[2] < X0 or b[0] > X0+W0 or b[3] < Y0 or b[1] > Y0+H0
            if not dentro and not fuera:
                o.off = min(o.off, tc-0.02)
    sc.dur = DUR
    return sc


def _dir(n): return os.path.join(S, pieza(n)['dir'])


def check(n):
    sc = build(n)
    T = json.load(open(os.path.join(_dir(n), 'audio', 'tiempos.json'), encoding='utf-8'))
    dur = T['dur']
    bad = sc.check_framing(0.05, dur)
    for t_, nm, b, w in bad[:20]:
        print('CORTADO %-22s t=%6.2f bbox=%s ventana=%s' % (nm, t_, b, w))
    print('violaciones de encuadre:', len(bad))
    r = sc.report(0.0, dur)
    print('ritmo: huecos>6s=%s  cortes=%s  cortes/min=%s' % (r['huecos'], r['cortes'], r['cortes_por_min']))
    od = os.path.join(_dir(n), 'salida'); os.makedirs(od, exist_ok=True)
    cols, rows = 4, 3; cw, ch = 480, 270
    hoja = Image.new('RGB', (cols*cw, rows*ch), (20, 20, 20))
    for i in range(cols*rows):
        fr = sc.render(dur*(i+0.5)/(cols*rows)).convert('RGB').resize((cw, ch), Image.LANCZOS)
        hoja.paste(fr, ((i % cols)*cw, (i//cols)*ch))
    hoja.save(os.path.join(od, '_hoja.jpg'), quality=88)
    print('hoja de contacto ->', os.path.join(od, '_hoja.jpg'))
    return len(bad)


def render(n):
    d = _dir(n)
    T = json.load(open(os.path.join(d, 'audio', 'tiempos.json'), encoding='utf-8'))
    od = os.path.join(d, 'salida'); os.makedirs(od, exist_ok=True)
    os.environ['PIEZA'] = str(n)
    M.render('coreo', 'build', T['dur'], os.path.join(od, 'cuerpo.mp4'),
             audio=os.path.join(d, 'audio', 'voz.wav'),
             frames=os.path.join(d, '_frames'))
    print('OK', os.path.join(od, 'cuerpo.mp4'))


if __name__ == '__main__':
    modo = sys.argv[1]; n = int(sys.argv[2])
    os.environ['PIEZA'] = str(n)
    if modo == 'check': sys.exit(1 if check(n) else 0)
    elif modo == 'render': render(n)
    elif modo == 'tramo':
        t0, t1 = float(sys.argv[3]), float(sys.argv[4])
        M.render('coreo', 'build', t1, os.path.join(_dir(n), 'salida', '_tramo.mp4'),
                 audio=os.path.join(_dir(n), 'audio', 'voz.wav'), t0=t0,
                 frames=os.path.join(_dir(n), '_frames'))
