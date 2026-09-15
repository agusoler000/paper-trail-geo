# -*- coding: utf-8 -*-
"""Coreografia de la serie S12 («THE RECEIPT», tanda del 2026-09-15). Partitura en `escenas.py`.

    python coreo.py check 1          # hoja de contacto + violaciones de encuadre
    python coreo.py render 1         # cuerpo 16:9 -> shorts/01_tanque/salida/cuerpo.mp4
    python coreo.py tramo 1 10 25    # tramo de prueba

Copia del motor de la S10/S02 (encajar / CRECER / post-pase de solape / post-pase de encuadre / pase
de ritmo). **Dos cosas son nuevas y las dos salen del pedido de Agustin del 15-sep** («meterle alguna
animacion en el medio o algo para darle un toque mas atractivo»):

  1. **`secuencia()`** — el verbo de animacion. Enciende en orden N cuadros pregenerados del mismo
     objeto, en la misma posicion y a la misma escala: el deposito que se vacia (pieza 1), las barras
     que crecen y la pila que sube (pieza 3). Los cuadros los dibuja `arte/props_s12.py`.

  2. **El PASO 1 de `canal/PLAN_PASADA_DE_VIDA.md`** — el push de camara deja de ser un porcentaje
     por plano y pasa a ser una VELOCIDAD con tope, mas una deriva lateral que alterna el sentido.
     Es la raiz medida de que los videos se vean quietos (`canal/POR_QUE_SON_SOSOS_2026-09-15.md`).

**Las dos viven aca, en el coreo LOCAL, y no en `produccion/motor.py`.** El 15-sep a las 12:20
arranco el render del ep. 09 con ~22 procesos que importan el motor; editarlo a mitad de camino
mezcla codigo viejo y nuevo en el mismo video (§0 del plan). Los pasos 2 y 4 del plan —idle, wobble
y `depth` en props— si tocan el motor y quedan para cuando ese render termine.

Los props compartidos (`produccion/assets`) se buscan solos: `imagen()` mira primero el arte de esta
serie y despues el catalogo del canal. De ahi salen `bandera_us`, `bandera_uk`, `bandera_es`,
`barril`, `deposito_oil`, `cerca`, `barrera`, `resolucion`, `poliza` y `flecha_arriba` sin dibujar
nada (regla 19).

Regla 1 de Agustin: nada cortado. `python coreo.py check <n>` tiene que dar 0.
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
    # WIDE pasa de 1,0 a 1,03: `Scene.window()` devuelve el cuadro ENTERO cuando zoom <= 1,005, asi
    # que un plano a 1,0 no tiene margen por donde derivar y el paso 1 no le hace nada. El 3 % recorta
    # un 1,5 % por lado, que `check_framing()` vigila y aborta si molesta.
    SH = {'WIDE': ((960, 600), 1.03),
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
    def cut(t, name, push=None):
        """`push=None` = velocidad automatica (ver finalize_cam). Un numero explicito sigue mandando."""
        CUTS.append((t-0.02, name, push)); cur[0] = name; M.ev(t, 'tick', 0.25)

    # ---------------- PASO 1 de canal/PLAN_PASADA_DE_VIDA.md, aplicado SOLO aca
    # El push era un porcentaje por plano: el zoom iba de z a z*(1+push) entre corte y corte, durase
    # el plano 2 s o 30. Resultado medido en el ep. 06: 6,58 de movimiento en los planos de 2,3 s y
    # 0,58 en uno de 30 s. Once veces menos por durar mas, que es justo al reves de lo que hace falta.
    # Aca `push` pasa a ser VELOCIDAD (% de zoom por segundo) con tope, y se le suma una deriva
    # lateral que alterna el sentido en cada corte para que no todo sea un acercamiento frontal.
    #
    # Va en el coreo LOCAL de la serie y no en produccion/motor.py a proposito: hoy 15-sep hay un
    # render del ep. 09 corriendo con ~22 procesos que importan el motor, y tocarlo a mitad mezcla
    # codigo viejo y nuevo en el mismo video (§0 del plan).
    PUSH_V = 0.010          # 1,0 % de zoom por segundo
    PUSH_MAX = 0.14         # ningun plano se acerca mas de un 14 %
    DERIVA = 9.0            # px de deriva lateral en el plano, alternando el sentido

    def finalize_cam():
        CUTS.sort(key=lambda c: c[0])
        for i, (t, name, push) in enumerate(CUTS):
            x0, y0, w, h, z = win(name); cx, cy = x0+w/2, y0+h/2
            t1 = (CUTS[i+1][0] if i+1 < len(CUTS) else DUR)-0.06
            sc.cx.set(t, cx, 'hold'); sc.cy.set(t, cy, 'hold'); sc.zoom.set(t, z, 'hold')
            if t1 > t+0.4:
                k = min(PUSH_V*(t1-t), PUSH_MAX) if push is None else push
                if k:
                    s = 1 if i % 2 else -1
                    sc.cx.set(t1, cx+s*DERIVA, 'lin')
                    sc.cy.set(t1, cy+(DERIVA*0.45 if i % 3 == 0 else -DERIVA*0.30), 'lin')
                    sc.zoom.set(t1, z*(1+k), 'lin')

    # ---------------- encaje automatico: la regla 1 (nada cortado) por construccion
    def encajar(im, sc_, x, y, shot=None, m=0.80, crecer=0.0):
        # Con el push convertido en velocidad, el acercamiento de un plano largo llega hasta
        # PUSH_MAX. El margen se calcula contra ese peor caso, no contra el 0,05 de antes: si se
        # dejara en 0,05, un plano de 14 s se acercaria mas de lo que el encaje previo.
        s = shot or cur[0]; x0, y0, w, h, z = win(s)
        w2, h2 = w/(1+PUSH_MAX), h/(1+PUSH_MAX)
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

        Regla 24 (los puntos son exactos): las marcas vienen horneadas en `mapa12_ciudades.png`, que
        las dibuja con la proyeccion Mercator real de `arte/mapa.py` y comprueba al generarse que
        Ceuta caiga sobre tierra y se separe de Fnideq. Aca no se coloca ni un punto a ojo."""
        x0, y0, w, h, z = win(shot)
        im = Image.open(os.path.join(ARTE, 'mapa12_ciudades.png')).convert('RGBA')
        
        k = max(w/im.width, h/im.height)*sangre
        im = im.resize((max(1, int(im.width*k)), max(1, int(im.height*k))), Image.LANCZOS)
        o = M.Obj(im, z=2); o.name = 'mapa_estrecho'; o.bg = True
        o.on = t; o.at(t, x0+w/2, y0+h/2, 'hold')
        o.scale(t, t+0.7, 1.04, 1.0, 'io'); o.fade(t, t+0.45, 0, 1)
        if dur: o.unpop(t+dur)
        sc.add(o); return o

    def secuencia(base, t0, t1, n_cuadros, fx=0.5, fy=0.5, shot=None, z=30, sc_=1.0,
                  crecer=None, hold=0.0):
        """**El verbo de animacion de esta tanda** (pedido de Agustin del 15-sep).

        Enciende en orden los `n_cuadros` de una secuencia de props (`base` + `%02d`) en la MISMA
        posicion y a la MISMA escala, entre `t0` y `t1`. El resultado es un objeto que se mueve de
        verdad —un deposito que se vacia, una barra que crece, una pila que sube— en vez de una
        tarjeta quieta con el numero escrito.

        Por que asi y no con keyframes: el motor no tiene deformacion por eje (`Obj.sc` es una escala
        unica), asi que un nivel que baja no se puede hacer escalando. Con cuadros pregenerados el
        resultado es exacto, se puede mirar uno a uno ANTES de renderizar, y **no hace falta tocar
        `produccion/motor.py`** —que hoy esta ocupado con el render del ep. 09.

        Detalles que importan:
          - La escala y la posicion se calculan UNA vez, con el primer cuadro, y se reusan. Si cada
            cuadro pasara por `encajar` por su cuenta, los que tienen mas tinta encajarian distinto y
            la secuencia temblaria.
          - Los cuadros se solapan 0,05 s para que no haya un hueco negro entre uno y otro.
          - Solo el primero entra con `pop`; el resto aparece ya colocado, o cada cuadro daria un
            respingo.
          - `hold`: segundos que el ULTIMO cuadro se queda despues de t1. Es el que lleva el dato
            final, asi que casi siempre conviene que se quede.
          - Van marcados con `.seq = <base>` para que el post-pase de solape no los apague entre si:
            justamente se tapan a proposito. El post-pase de ENCUADRE si los mira (regla 1).
        """
        s = shot or cur[0]; x, y = at(s, fx, fy)
        im0 = imagen('%s%02d' % (base, 0))
        sfit, x, y = encajar(im0, sc_, x, y, s, crecer=CRECER if crecer is None else crecer)
        paso = (t1-t0)/max(1, n_cuadros-1)
        objs = []
        for i in range(n_cuadros):
            im = imagen('%s%02d' % (base, i))
            if im.size != im0.size:
                raise SystemExit('secuencia %s: el cuadro %d mide distinto que el 00 (%s vs %s). '
                                 'Todos los cuadros tienen que compartir lienzo.'
                                 % (base, i, im.size, im0.size))
            o = M.Obj(im, z=z); o.name = '%s%02d' % (base, i); o.seq = base
            ti = t0 + i*paso
            o.on = ti
            o.off = (t1 + hold + 0.6) if i == n_cuadros-1 else (ti + paso + 0.05)
            o.at(ti, x, y, 'hold')
            if i == 0:
                o.scale(ti, ti+0.45, 0.25*sfit, sfit, 'back'); o.fade(ti, ti+0.15, 0, 1)
                M.ev(ti, 'pop')
            else:
                o.sc.set(ti, sfit, 'hold'); o.a.set(ti, 1.0, 'hold')
                M.ev(ti, 'tick', 0.16)      # el pase de ritmo ve la secuencia como movimiento
            sc.add(o); objs.append(o)
        return objs

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
               latir=latir, imagen=imagen, PR=PR, M=M, W=W, H=H, cur=cur, win=win,
               secuencia=secuencia)
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
    # Los cuadros de UNA MISMA `secuencia` se tapan entre si a proposito —son el mismo objeto en
    # instantes distintos—, asi que esa pareja se salta. Todo lo demas sigue entrando: una secuencia
    # que tape una tarjeta ajena tiene que apagarla igual que cualquier otro objeto, o el pase se
    # convertiria en un agujero por donde colar solapes.
    obs = [o for o in sc.layers if not getattr(o, 'bg', False)]
    obs.sort(key=lambda o: o.on)
    for j, b in enumerate(obs):
        tb = b.on+0.40
        bb = b.bbox(tb)
        if bb is None: continue
        for a in obs[:j]:
            if not (a.on <= tb < a.off): continue
            sa, sb = getattr(a, 'seq', None), getattr(b, 'seq', None)
            if sa and sa == sb: continue        # dos cuadros de la misma secuencia
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
        pk = PUSH_MAX if push is None else push              # push automatico -> peor caso
        x0 = X0+(W0-W0/(1+pk))/2; y0 = Y0+(H0-H0/(1+pk))/2
        w, h = W0/(1+pk), H0/(1+pk)                          # la ventana al FINAL del push-in
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
