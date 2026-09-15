# -*- coding: utf-8 -*-
"""PRUEBA de ritmo visual — 25 s de la pieza 4 (Ceuta), al estilo de la referencia que paso Agustin.

    python prueba_vida.py cuadro      # cuadros fijos (regla de Agustin: primero el cuadro)
    python prueba_vida.py hoja        # 12 cuadros, para ver el recorrido entero
    python prueba_vida.py render      # los 25 s -> salida/_prueba_vida.mp4
    python prueba_vida.py medir       # ritmo.py sobre el resultado

**v3, reescrita por calidad.** La v2 perseguia el numero de `ritmo.py` en vez del video: diez saltos
secos de camara en 25 s subian el movimiento medio de 3,05 a 4,58 y quedaba mal, porque **esos
saltos no iban a ningun sitio** — la camara se movia entre dos vistas del mismo mapa sin que nada en
la frase lo pidiera. Agustin: *«es muy grotesco... enfocate en calidad»*. Tenia razon.

El criterio de la v3:

  - **La camara hace CINCO movimientos en 25 s**, lentos, con easing, y **cada uno va hacia lo que
    la voz esta diciendo**. Ni un salto seco.
  - **El ritmo lo dan los objetos que entran y salen**, anclados a la camara (`encamara`): la
    sentencia, el calendario de 32 dias, la cifra, la bandera, la valla. Es movimiento con sentido,
    y ademas es lo que hace la referencia: ahi lo que cambia todo el rato no es el encuadre, son los
    elementos.
  - **El color narra.** Espana se pinta cuando la voz dice «Ceuta is Spain»; Marruecos, en «on the
    African mainland». En la v2 entraban por un fade global sin motivo.
  - **Subtitulo limpio** (banda translucida + texto crema), no la tarjeta de papel con marco.
  - **El mapa tiene profundidad**: bajio, sombra proyectada y grano de papel. Ver `arte/mapa.py`.
  - **Nuestro personaje**, no los chibi de la referencia (decision de Agustin): el jurista del
    elenco, que ya esta pagado.

**Los tiempos son sinteticos.** La voz de la pieza 4 todavia no esta generada, asi que las 47
palabras del guion real se reparten a 1,88 palabras/segundo, la cadencia medida de George. Sirve
para lo que mide esta prueba; los tiempos reales entran con `audio/tiempos.json`.

La regla 24 se cumple por construccion: cada punto sale de `mapa12_pts.json`, que lo escribe
`arte/mapa.py` con la proyeccion Mercator real.
"""
import json, os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, '..', '..'))
PROD = os.path.join(RAIZ, 'produccion')
sys.path.insert(0, PROD); sys.path.insert(0, AQUI)
import motor as M, props as PR
from PIL import Image, ImageDraw

ARTE = os.path.join(AQUI, 'arte', 'assets')
W, H = M.W, M.H
DUR = 25.0
OUT = os.path.join(AQUI, 'shorts', '04_ceuta', 'salida'); os.makedirs(OUT, exist_ok=True)
PTS = json.load(open(os.path.join(ARTE, 'mapa12_pts.json'), encoding='utf-8'))
NL = chr(10)

# Las dos primeras lineas del guion real de la pieza 4, en grupos de subtitulo.
GRUPOS = [
    'On the 29th of June', 'a Spanish court', 'published a ruling.',
    'Thirty-two days later', 'forty-nine thousand people', 'crossed into Ceuta',
    'in twenty-four hours.',
    'Ceuta is Spain', 'on the African mainland.', 'A European border',
    'with a land fence', 'and open water', 'at both ends of it.',
]
PAL_POR_S = 1.88                      # cadencia medida de George en el canal


def imagen(name):
    for base in (ARTE, os.path.join(PROD, 'assets')):
        p = os.path.join(base, 'prop_%s.png' % name)
        if os.path.exists(p): return Image.open(p).convert('RGBA')
    raise SystemExit('falta el prop: %s' % name)


def _mapa_lienzo():
    """La hoja escalada para CUBRIR 1920x1080, mas la conversion de un punto del mapa al lienzo.

    `Scene.window()` limita la camara al lienzo base, asi que el 'mundo' por el que se vuela son
    estos 1920x1080 y el zoom recorta dentro. La hoja es 3000x1688 (16:9), asi que cubre exacto.
    """
    hoja = Image.open(os.path.join(ARTE, 'mapa12_base.png')).convert('RGBA')
    k = max(W/hoja.width, H/hoja.height)
    nw, nh = int(hoja.width*k), int(hoja.height*k)
    ox, oy = (W-nw)//2, (H-nh)//2
    def al_lienzo(nombre):
        px, py = PTS[nombre]
        return (ox + px*k, oy + py*k)
    return hoja, k, (nw, nh), (ox, oy), al_lienzo


def capa(nombre, k, size, off):
    im = Image.open(os.path.join(ARTE, nombre)).convert('RGBA').resize(size, Image.LANCZOS)
    o = M.Obj(im, z=3); o.bg = True; o.name = nombre
    o.at(0, off[0]+size[0]/2, off[1]+size[1]/2, 'hold')
    return o


def sub(sc, texto, t0, t1):
    """Subtitulo limpio: banda oscura translucida + texto crema, sin marco.

    La v2 usaba `PR.card`, la tarjeta de papel con borde y sombra. En un subtitulo que cambia cada
    segundo eso es un objeto pesado entrando y saliendo trece veces, y se ve recargado. Un subtitulo
    tiene que ser legible sin competir con el mapa.
    """
    f = PR.FONTC(70)
    tmp = ImageDraw.Draw(Image.new('L', (10, 10)))
    bb = tmp.textbbox((0, 0), texto.upper(), font=f)
    im = Image.new('RGBA', (bb[2]-bb[0]+92, bb[3]-bb[1]+70), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.width-1, im.height-1], radius=16, fill=(26, 24, 21, 212))
    cx, cy = im.width/2, im.height/2
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        d.text((cx+dx, cy+dy), texto.upper(), font=f, fill=(16, 15, 13, 235), anchor='mm')
    d.text((cx, cy), texto.upper(), font=f, fill=(247, 241, 226, 255), anchor='mm')
    o = M.Obj(im, z=95); o.name = 'sub:'+texto
    o.on = t0; o.off = t1
    paso = 0.10
    for i in range(int((t1-t0)/paso)+2):
        s = min(t0+i*paso, t1)
        x0, y0, x1, y1 = sc.window(min(s, DUR-0.01))
        o.at(s, (x0+x1)/2, y0+(y1-y0)*0.845, 'hold')
        o.sc.set(s, 1.0/sc.zoom(min(s, DUR-0.01)), 'hold')
    o.a.set(t0, 0, 'hold'); o.a.set(t0+0.13, 1, 'io')
    o.a.set(t1-0.13, 1, 'hold'); o.a.set(t1, 0, 'io')
    sc.add(o)
    return o


def encamara(sc, im, t0, t1, fx, fy, alto_rel, z=50, entra=0.45, sale=0.40, sfx='pop',
             deriva=1.0):
    """Coloca un objeto ANCLADO A LA CAMARA, a tamano fijo en pantalla.

    Es lo que permite que el ritmo lo den los OBJETOS y no la camara: mientras la camara hace un
    unico movimiento lento y motivado, por delante entran y salen la sentencia, el calendario, la
    cifra. Sin este anclaje, un objeto puesto en coordenadas del mapa se va de cuadro en cuanto la
    camara se mueve — que es lo que obligaba a la v2 a cortar cada dos segundos.

    Entra y sale con alpha y nada mas: el `pop` elastico del motor, repetido diez veces en 25 s, es
    justo lo que se veia aparatoso.

    **`deriva`** mueve el objeto unos pocos pixeles y lo inclina medio grado a lo largo de su vida.
    Nace de una medicion: con los planos de mesa quietos, `ritmo.py` daba 31,3 % de cuadros
    congelados aunque la camara SI hacia un push — porque la hoja de papel es tan lisa que un
    desplazamiento de dos pixeles sobre ella no cambia nada medible, ni se nota. En la mesa el
    movimiento tienen que darlo los objetos. `deriva=0` lo apaga.
    """
    k0 = (H*alto_rel)/im.height
    o = M.Obj(im, z=z); o.name = 'oc'
    o.on = t0; o.off = t1
    vida = max(0.001, t1-t0)
    dx = 13.0*deriva*(1 if int(t0*10) % 2 else -1)
    dy = 8.0*deriva*(1 if int(t0*7) % 2 else -1)
    paso = 0.10
    for i in range(int((t1-t0)/paso)+2):
        s = min(t0+i*paso, t1)
        x0, y0, x1, y1 = sc.window(min(s, DUR-0.01))
        zz = sc.zoom(min(s, DUR-0.01))
        u = (s-t0)/vida
        o.at(s, x0+(x1-x0)*fx + dx*u, y0+(y1-y0)*fy + dy*u, 'hold')
        o.sc.set(s, (k0/zz)*(1.0 + 0.045*deriva*u), 'hold')
    if deriva:
        o.rot.set(t0, -0.55*deriva, 'hold'); o.rot.set(t1, 0.55*deriva, 'io')
    o.a.set(t0, 0, 'hold'); o.a.set(t0+entra, 1, 'io')
    o.a.set(t1-sale, 1, 'hold'); o.a.set(t1, 0, 'io')
    M.ev(t0, sfx, 0.5)
    sc.add(o)
    return o


def build():
    del M.EVENTS[:]
    sc = M.Scene(os.path.join(ARTE, 'fondo.png'))
    hoja, k, size, off, al_lienzo = _mapa_lienzo()

    # ---------------- DOS ESCENARIOS, y el corte es pasar de uno a otro
    #
    # La v3 medida daba quietos 6,1 % y ocupacion 77 % —las dos metas— pero **0,0 cortes/min**
    # contra los 66,5 de la referencia. El error era entender «corte» como «salto de camara», que
    # es lo que hacia la v2 y lo que quedaba grotesco. En la referencia el corte **cambia el
    # CONTENIDO**: del mapa a una foto de satelite, a una playa, a un retrato. No sacuden el
    # encuadre: cambian de plano.
    #
    # Nuestro equivalente no hay que inventarlo, es el estilo del canal desde el episodio 1: **la
    # mesa con el documento encima**. Asi que la pieza alterna dos escenarios —MAPA y MESA— y cada
    # cambio es un corte de verdad, con contenido distinto a los dos lados.
    #
    # El mapa se monta como varios objetos con `on`/`off`: donde el mapa se apaga, queda a la vista
    # el fondo de madera de `Scene`, que ya es la mesa.
    MAPA = [(2.55, 8.55), (9.45, 17.70), (21.45, DUR)]
    MESA = [(0.0, 2.55), (8.55, 9.45), (17.70, 21.45)]

    base = hoja.resize(size, Image.LANCZOS)
    CEUTA = al_lienzo('Ceuta')
    CENTRO = al_lienzo('Center')
    MEDIO = (CEUTA[0]*0.62 + CENTRO[0]*0.38, CEUTA[1]*0.62 + CENTRO[1]*0.38)

    for i, (a, b) in enumerate(MAPA):
        mp = M.Obj(base, z=1); mp.bg = True; mp.name = 'mapa%d' % i
        mp.on, mp.off = a, b
        mp.at(a, off[0]+size[0]/2, off[1]+size[1]/2, 'hold')
        sc.add(mp)
        M.ev(a, 'tick', 0.35)

        # el color narra: cada pais se pinta CUANDO la voz lo nombra, y solo en el tramo que toca
        if a <= 13.1 < b:
            es = capa('mapa12_es.png', k, size, off)
            es.on, es.off = 13.1, b; es.fade(13.1, 14.8, 0, 1); sc.add(es)
            ma = capa('mapa12_ma.png', k, size, off)
            ma.on, ma.off = 15.4, b; ma.fade(15.4, 17.2, 0, 1); sc.add(ma)
        elif a > 17.0:
            es = capa('mapa12_es.png', k, size, off); es.on, es.off = a, b; sc.add(es)
            ma = capa('mapa12_ma.png', k, size, off); ma.on, ma.off = a, b; sc.add(ma)
        # Las marcas van ENCIMA del color: Natural Earth 50m no separa el enclave, asi que al
        # pintar Marruecos la peninsula de Ceuta quedaba ocre y el mapa afirmaba lo contrario.
        mk = capa('mapa12_marcas.png', k, size, off); mk.z = 6
        mk.on, mk.off = a, b; sc.add(mk)

    for a, b in MESA:
        M.ev(a, 'tick', 0.35)

    # ---------------- la camara: dentro de cada plano, UN movimiento lento y motivado
    # En los cortes la camara se recoloca de golpe, que es lo que hace un corte; dentro del plano no
    # salta nunca. Es la diferencia con la v2: alli el salto ocurria DENTRO del mismo plano y sin
    # motivo, y por eso se veia como una sacudida en vez de como un montaje.
    # El encuadre de mesa NO es el centro del lienzo: `fondo.png` tiene la hoja de trabajo en
    # x 0..1116, y 436..1064, y el resto es madera. Encuadrar al centro dejaba media hoja y media
    # mesa vacia, que es lo que se veia descolocado en la primera pasada con cortes. Estas son las
    # mismas coordenadas del plano 'CTR' que usa `coreo.py` en toda la serie.
    MESA_C = (556, 750)
    Z_MESA = 1.72

    def plano(t0, t1, xy0, z0, xy1, z1):
        """Un plano = recolocacion seca en t0 + UN movimiento lento hasta t1."""
        for pista, v in ((sc.cx, xy0[0]), (sc.cy, xy0[1]), (sc.zoom, z0)):
            pista.set(max(0.0, t0-0.001), pista(max(0.0, t0-0.001)), 'hold')
            pista.set(t0, v, 'hold')
        sc.cam(t0, t1, xy1, z1, 'io')

    plano(0.0,   2.55, MESA_C, Z_MESA, (MESA_C[0]+34, MESA_C[1]-12), Z_MESA*1.20)  # MESA · la sentencia
    P1 = (CENTRO[0]*0.72 + CEUTA[0]*0.28, CENTRO[1]*0.72 + CEUTA[1]*0.28)
    plano(2.55,  8.55, CENTRO, 1.20, P1, 1.40)                  # MAPA · el Estrecho
    plano(8.55,  9.45, MESA_C, Z_MESA*1.14, (MESA_C[0]-18, MESA_C[1]), Z_MESA*1.30)  # MESA · el golpe
    plano(9.45, 13.00, CEUTA,  1.86, CEUTA, 2.18)               # MAPA · la camara VA a Ceuta
    plano(13.00, 17.70, MEDIO, 1.28, (MEDIO[0]-46, MEDIO[1]-14), 1.54)  # MAPA · se pintan los paises
    # Z_MESA es el suelo, no un punto medio: `fondo.png` tiene pared clara por encima de y=436 y
    # con zoom 1,62 la ventana subia hasta y=412 y metia una franja clara sin contenido.
    plano(17.70, 21.45, MESA_C, Z_MESA, (MESA_C[0]-40, MESA_C[1]+10), Z_MESA*1.22)  # MESA · la valla
    plano(21.45, DUR,   CEUTA, 2.05, CEUTA, 2.34)               # MAPA · cierra sobre el istmo

    # ---------------- el ritmo: POCOS objetos, uno por idea, y ninguno encima de una etiqueta
    #
    # La primera version de la v3 tenia diez y se notaba: la bandera espanola y la valla flotaban
    # sobre el mar sin relacion con nada, el calendario `cal20` decia «20» en una frase sobre 32
    # dias, y la cifra 49.000 caia justo encima de la etiqueta CEUTA·SPAIN. Un objeto que flota
    # sobre el agua sin motivo no es ritmo: es relleno, y se ve barato.
    #
    # Quedan SEIS, y cada uno esta colocado en el lado que el mapa deja libre en ese momento: el
    # Atlantico a la izquierda mientras la camara esta abierta, el Mediterraneo a la derecha cuando
    # cierra sobre Ceuta. La etiqueta CEUTA·SPAIN sale del punto hacia la derecha, asi que en los
    # planos cerrados nada entra por encima de fy 0,30-0,45.
    # --- MESA 1 (0-2,55): el documento. La pieza abre con el papel, que es lo que es el canal.
    encamara(sc, imagen('sentencia'), 0.10, 2.50, 0.345, 0.50, 0.74, z=52, entra=0.55)
    encamara(sc, PR.card('A SPANISH COURT', size=58, color=PR.PAPEL, tcolor=PR.TINTA),
             1.15, 2.50, 0.735, 0.395, 0.070, z=54)
    encamara(sc, PR.card('29 · VI · 2026', size=72, color=PR.PAPEL, tcolor=PR.ROJO),
             1.60, 2.50, 0.735, 0.545, 0.085, z=54, sfx='stamp')

    # --- MAPA 1 (2,55-8,55): donde pasa, y cuanto tardo
    encamara(sc, PR.card('32 DAYS' + NL + 'LATER', size=72, color=PR.PAPEL, tcolor=PR.TINTA),
             6.75, 8.45, 0.790, 0.630, 0.145, z=54)

    # --- MESA 2 (8,55-9,45): un golpe de 0,9 s. La cifra, sola, sobre la mesa.
    encamara(sc, PR.card('49,000', size=150, color=PR.PAPEL, tcolor=PR.ROJO),
             8.62, 9.42, 0.50, 0.455, 0.235, z=56, entra=0.22, sale=0.14, sfx='stamp')
    encamara(sc, PR.card('IN 24 HOURS', size=56, color=PR.PAPEL, tcolor=PR.TINTA),
             8.95, 9.42, 0.50, 0.650, 0.065, z=56, entra=0.18, sale=0.12)

    # --- MAPA 2 (9,45-17,70): la camara va a Ceuta y despues se pintan los paises.
    # Del 13,0 en adelante NADA por delante: el color cuenta solo, y una tarjeta encima seria
    # explicar dos veces lo mismo.
    encamara(sc, PR.card('49,000 CROSSED', size=56, color=PR.PAPEL, tcolor=PR.ROJO),
             10.10, 12.85, 0.775, 0.700, 0.070, z=56)

    # --- MESA 3 (17,70-21,45): la valla, en esquema declarado sobre la mesa. Nunca sobre el mapa:
    # a la escala de la valla Natural Earth 50m no da (ver arte/mapa.py).
    encamara(sc, imagen('cerca'), 18.35, 21.35, 0.545, 0.395, 0.075, z=44, entra=0.5)
    encamara(sc, PR.card('A EUROPEAN BORDER', size=62, color=PR.PAPEL, tcolor=PR.TINTA),
             17.85, 21.35, 0.50, 0.175, 0.080, z=54)
    encamara(sc, imagen('gota'), 19.35, 21.35, 0.235, 0.395, 0.060, z=46)
    encamara(sc, imagen('gota'), 19.65, 21.35, 0.860, 0.395, 0.060, z=46)
    encamara(sc, PR.card('WATER', size=46, color=PR.PAPEL, tcolor=PR.ROJO),
             19.95, 21.35, 0.235, 0.530, 0.048, z=54)
    encamara(sc, PR.card('WATER', size=46, color=PR.PAPEL, tcolor=PR.ROJO),
             20.15, 21.35, 0.860, 0.530, 0.048, z=54)

    # --- MAPA 3 (21,45-25): el cierre
    encamara(sc, PR.card('8 KM OF FENCE' + NL + 'WATER AT BOTH ENDS', size=52,
                         color=PR.PAPEL, tcolor=PR.ROJO),
             21.85, DUR-0.25, 0.755, 0.675, 0.125, z=56, sfx='stamp')

    # ---------------- nuestro personaje: entra UNA vez, en el plano de MESA, y senala la valla
    # Va en la mesa y no sobre el mapa: un rig de pie sobre el mar no se sostiene, y en la mesa es
    # donde el canal lo ha puesto siempre.
    T_J0, T_J1 = 17.80, 21.35
    # OJO con el ancla del Rig: `motor.Rig` documenta «Posicion = donde cae el pixel (0,0) de la
    # imagen original», o sea la esquina SUPERIOR IZQUIERDA, no los pies. Con y=1010 el rig entero
    # caia por debajo del lienzo y no se veia: en la hoja de contacto los dos planos de mesa salian
    # sin personaje. La ventana de MESA va de y=412 a y=1080, y el rig mide ~276 px a esta escala.
    # Sin `enter`/`exit`: esas acciones traen al rig desde x=-700 y lo devuelven fuera, y en un
    # plano de 3,6 s el personaje se pasa media aparicion entrando cortado por el borde. Aparece y
    # se va con alpha, que ademas es lo que hace el resto de la pieza.
    # Sin `enter`/`exit`: esas acciones traen al rig desde x=-700 y lo devuelven fuera, y en un
    # plano de 3,6 s el personaje se pasa media aparicion entrando cortado por el borde. Aparece y
    # se va con alpha, que ademas es lo que hace el resto de la pieza.
    #
    # Y la posicion NO se pone a ojo: se crea el rig, se mide su caja real con `bbox()` y se
    # desplaza lo justo para que entre con margen en la ventana del plano. A ojo salieron 14
    # violaciones de la regla 1 seguidas, porque `Rig` se ancla por la esquina superior izquierda
    # y su alto depende de la pose.
    jur = M.Rig('05_jurista', 300, 690, sc=0.44, z=42, on=T_J0, off=T_J1)
    jur.point(T_J0+1.5, 'R', hold=1.9)
    jur.nod(T_J0+0.8)
    MG = 26
    peor = None
    for i in range(int((T_J1-T_J0)/0.15)+1):
        tt = T_J0+0.5+i*0.15
        if tt >= T_J1-0.2: break
        b = jur.bbox(tt)
        if b is None: continue
        vx0, vy0, vx1, vy1 = sc.window(tt)
        dx = max(0.0, vx0+MG-b[0]) - max(0.0, b[2]-(vx1-MG))
        dy = max(0.0, vy0+MG-b[1]) - max(0.0, b[3]-(vy1-MG))
        if peor is None or abs(dx)+abs(dy) > abs(peor[0])+abs(peor[1]): peor = (dx, dy)
    if peor:
        jur.x = M.Track(300+peor[0]); jur.y = M.Track(690+peor[1])
    jur.a.set(T_J0, 0, 'hold'); jur.a.set(T_J0+0.45, 1, 'io')
    jur.a.set(T_J1-0.40, 1, 'hold'); jur.a.set(T_J1, 0, 'io')
    sc.add(jur)

    # ---------------- subtitulo, en grupos cortos, RECORTADO en cada corte de plano
    # En el instante del corte la ventana salta, y un subtitulo que lo cruza queda un cuadro con
    # las coordenadas del plano viejo: `check_framing` lo marcaba como cortado. Cada grupo se parte
    # en los limites de plano y cada trozo se coloca contra su propia ventana.
    CORTES = sorted(set([a for a, _ in MAPA] + [a for a, _ in MESA] + [DUR]))
    t = 0.45
    for g in GRUPOS:
        dur = max(0.70, len(g.split())/PAL_POR_S)
        a, b = t, t+dur-0.03
        for c in CORTES:
            if a < c < b:
                if c-a > 0.30: sub(sc, g, a, c-0.05)
                a = c+0.02
        if b-a > 0.30: sub(sc, g, a, b)
        M.ev(t, 'tick', 0.12)
        t += dur

    sc.dur = DUR
    return sc


# ------------------------------------------------------------------ utilidades
def cuadro(ts=(2.5, 8.0, 14.5, 22.5)):
    sc = build()
    for i, tt in enumerate(ts):
        f = os.path.join(OUT, '_prueba_cuadro_%02d.png' % i)
        sc.render(tt).convert('RGB').save(f)
        print('cuadro t=%.1f ->' % tt, f)


def hoja12():
    sc = build()
    cols, rows = 4, 3
    cw, ch = 480, 270
    q = Image.new('RGB', (cols*cw, rows*ch), (20, 20, 20))
    for i in range(cols*rows):
        tt = DUR*(i+0.5)/(cols*rows)
        fr = sc.render(tt).convert('RGB').resize((cw, ch), Image.LANCZOS)
        d = ImageDraw.Draw(fr); d.text((8, 6), '%.1fs' % tt, fill=(255, 220, 120))
        q.paste(fr, ((i % cols)*cw, (i//cols)*ch))
    f = os.path.join(OUT, '_prueba_hoja.jpg'); q.save(f, quality=90)
    print('hoja ->', f)


def render():
    f = os.path.join(OUT, '_prueba_vida.mp4')
    M.render('prueba_vida', 'build', DUR, f, frames=os.path.join(AQUI, '_frames_prueba'))
    print('OK', f)


def medir():
    os.system('python "%s" "%s" --contacto' % (os.path.join(PROD, 'ritmo.py'),
                                               os.path.join(OUT, '_prueba_vida.mp4')))


if __name__ == '__main__':
    modo = sys.argv[1] if len(sys.argv) > 1 else 'cuadro'
    {'cuadro': cuadro, 'hoja': hoja12, 'render': render, 'medir': medir}[modo]()
