# -*- coding: utf-8 -*-
"""Partitura de la serie S12 («THE RECEIPT», tanda del 2026-09-15). Cuatro funciones, `e01`-`e04`,
ancladas a las lineas de cada guion.

Cada paso es una tupla anclada a una linea. `i` entero = inicio de la linea i; `(i, off)` = inicio de
la linea i + off segundos; `-i` = FIN de la linea i.

**Lo nuevo de esta tanda es el verbo `seq`** (pedido de Agustin del 15-sep: *«meterle alguna
animacion en el medio o algo para darle un toque mas atractivo»*). Cada pieza lleva **un mecanismo
animado en el medio** que dice el dato moviendose, en vez de una tarjeta quieta con el numero:

  - **01 · el tanque** — el deposito se vacia de 100 % a 39 % contra una regla graduada fija,
    mientras la flecha del precio sube por el otro lado. Las dos cosas a la vez SON el argumento:
    bajo el que tenia que subir y subio el que tenia que bajar.
  - **02 · los barcos** — doce petroleros cruzando se apagan de izquierda a derecha hasta quedar
    uno, mientras la prima del seguro sube. El estrecho no se cierra con fuego: se cierra con una
    cifra.
  - **03 · las dos barras** — el dinero llega al 76 % del ancho y la gente al 35 %. La distancia
    entre las dos puntas es la pieza entera y se entiende sin leer. Despues la pila de libras crece
    de 4,5bn a 15,3bn y cae el sello SAME CONTRACT.
  - **04 · el papel y la valla** — la hoja del Estrecho situa Ceuta, y despues, en un esquema
    declarado sobre la mesa (no sobre el mapa), la linea roja rodea el extremo de la valla por el
    agua. El papel dice «la valla»; la linea pasa por donde la valla se acaba.

**El vocabulario es corto y VUELVE**, una terna por pieza. El objeto que abre es el que cierra.

**Composicion: nunca un objeto solo** (leccion 3 del S03). Objeto a la izquierda (fx ~0,28),
contraparte a la derecha (fx ~0,73). WALL va centrado y a dos alturas.

**El primer objeto NO puede ser un `dr`** (leccion 1 del S03): el post-pase de encuadre muestrea
0,10 s despues del corte y a esa altura una caida esta a medias sobre el borde.

**`crecer` por paso.** Con dos objetos en el beat se baja a ~0,45; con tres, a ~0,30. Y ojo con la
trampa conocida (`reference-coreo-crecer-y-props`): el `crecer` puede hacer desaparecer props sin que
el check lo note. Mirar el PNG, no solo el numero.

Regla 1 de Agustin: nada cortado. `python coreo.py check <n>` tiene que dar 0.
"""

NL = chr(10)


def correr(A, pasos):
    """Interprete de la partitura. Copia del de la S04 mas el verbo `seq`.

    Se escribe aca en vez de cargar el de la S04 por ruta justamente para poder anadir `seq`: el de
    la S04 no lo tiene y modificarlo tocaria una serie ya publicada.
    """
    L, E = A['L'], A['E']
    cut, card, P, drop, stamp = A['cut'], A['card'], A['P'], A['drop'], A['stamp']
    girar, latir, PR, mapa = A['girar'], A['latir'], A['PR'], A['mapa']
    secuencia = A['secuencia']

    def T(i):
        if isinstance(i, tuple): return max(0.06, T(i[0])+i[1])
        return max(0.06, E(-i) if i < 0 else L(i))

    CORTES = sorted(T(q[1]) for q in pasos if q[0] == 'cut')

    def hasta(t):
        for c in CORTES:
            if c > t+0.35: return max(2.6, c-t+0.9)
        return max(2.6, A['DUR']-t)

    def antes(t, t_paso):
        """Nada NACE despues del corte siguiente: un ancla con offset puede caer del otro lado de un
        corte declarado mas abajo en la lista y el objeto se colocaria con las coordenadas del plano
        VIEJO, apareciendo cortado en el nuevo."""
        for c in CORTES:
            if t_paso < c <= t: return max(t_paso+0.1, c-0.35)
        return t

    ult = [0.0]
    for p in pasos:
        k = p[0]
        if k == 'cut':
            ult[0] = T(p[1]); cut(T(p[1]), p[2], *(p[3:]))
        elif k == 'mapa':
            i = p[1]; t = antes(T(i), ult[0])
            mapa(t, dur=hasta(t), **({'sangre': p[2]} if len(p) > 2 else {}))
        elif k in ('card', 'rojo'):
            i, txt, fx, fy, size = p[1:6]; t = antes(T(i), ult[0])
            card(txt, t, fx=fx, fy=fy, size=size, dur=hasta(t),
                 tcolor=PR.ROJO if k == 'rojo' else PR.TINTA)
        elif k in ('P', 'dr'):
            i, name, fx, fy, sc_ = p[1:6]; t = antes(T(i), ult[0])
            kw = {'crecer': p[6]} if len(p) > 6 else {}
            (P if k == 'P' else drop)(name, t, fx=fx, fy=fy, sc_=sc_, dur=hasta(t), **kw)
        elif k == 'st':
            i, name, fx, fy, sc_ = p[1:6]; t = antes(T(i), ult[0])
            stamp(name, t, fx=fx, fy=fy, sc_=sc_, dur=hasta(t),
                  **({'crecer': p[6]} if len(p) > 6 else {}))
        elif k == 'seq':
            # ('seq', i, j, base, n, fx, fy, sc_[, crecer[, hold]])
            i, j, base, n, fx, fy, sc_ = p[1:8]
            crecer = p[8] if len(p) > 8 else None
            hold = p[9] if len(p) > 9 else 1.2
            t0 = antes(T(i), ult[0])
            secuencia(base, t0, T(j), n, fx=fx, fy=fy, sc_=sc_, crecer=crecer, hold=hold)
        elif k == 'gira':
            i, j, name, fx, fy, sc_ = p[1:7]
            v = p[7] if len(p) > 7 else 1.0
            o = P(name, T(i), fx=fx, fy=fy, sc_=sc_, dur=T(j)-T(i)+0.6)
            girar(o, T(i)+0.5, T(j)-0.2, v)
        elif k == 'late':
            i, j, name, fx, fy, sc_ = p[1:7]
            o = P(name, T(i), fx=fx, fy=fy, sc_=sc_, dur=T(j)-T(i)+0.6)
            latir(o, T(i)+0.6, T(j)-0.3)
        else:
            raise SystemExit('paso desconocido: ' + k)


# ============================================================ 1 · THE EMPTY TANK
def e01(A):
    """8 lineas. El vocabulario: el DEPOSITO (cuanto queda), la FLECHA (el precio) y la BANDERA
    (de quien es el problema).

    La animacion central va en la linea 4 —«The price went up seventeen percent»— que es la linea
    mas corta del guion y la que mas necesita imagen: el deposito baja mientras la flecha sube.
    """
    correr(A, [
        # --- 0 · el golpe: 39 %. El deposito entero, solo, grande.
        ('cut',  (0, -0.45), 'CTR'),
        ('P',     0, 'deposito_oil', 0.30, 0.52, 1.0, 0.50),
        ('rojo', (0, 1.8), '39%' + NL + 'FULL', 0.73, 0.34, 108),
        ('card', (0, 4.6), 'LOWEST' + NL + 'SINCE 1982', 0.73, 0.70, 60),

        # --- 1 · el numero, y de donde sale
        ('cut',   1, 'WALL'),
        ('card',  1, '285,360,000', 0.50, 0.40, 104),
        ('card', (1, 3.2), 'BARRELS  ·  WEEK OF SEPT 4', 0.50, 0.74, 48),
        ('cut',  (1, 6.4), 'CTR'),
        ('P',    (1, 6.6), 'bandera_us', 0.28, 0.40, 1.0, 0.42),
        ('card', (1, 7.0), 'BUILT FOR' + NL + '727,000,000', 0.73, 0.52, 62),

        # --- 2 · como se vacio: la fecha y la cantidad
        ('cut',   2, 'CTR'),
        ('P',     2, 'decreto', 0.30, 0.48, 1.0, 0.46),
        ('card', (2, 1.6), '11 MARCH', 0.73, 0.32, 86),
        ('rojo', (2, 5.0), '172 MILLION' + NL + 'BARRELS OUT', 0.73, 0.68, 62),

        # ============ LA ANIMACION CENTRAL ============
        # Linea 3: «The price went up seventeen percent.» El deposito se vacia a la izquierda
        # mientras la flecha del precio sube a la derecha. Trece cuadros contra la regla graduada.
        ('cut',   3, 'CTR'),
        ('seq',   3, -4, 'tanque_n', 13, 0.28, 0.52, 1.0, 0.44, 1.4),
        ('P',    (3, 0.9), 'flecha_arriba', 0.75, 0.56, 1.0, 0.30),
        ('rojo', (3, 1.9), '+17%', 0.75, 0.26, 96),
        # ==============================================

        # --- 4 · las cinco semanas y el precio de cierre
        ('cut',   4, 'WALL'),
        ('card',  4, '5 WEEKS  ·  19,000,000 BARRELS', 0.50, 0.42, 56),
        ('cut',  (4, 4.2), 'CTR'),
        ('P',    (4, 4.4), 'barril', 0.28, 0.54, 1.0, 0.40),
        ('rojo', (4, 5.2), '$104.61', 0.73, 0.44, 104),

        # --- 5 · para que existe una reserva
        ('cut',   5, 'CTR'),
        ('P',     5, 'deposito_oil', 0.29, 0.52, 1.0, 0.44),
        ('card', (5, 2.0), 'FOR ONE DAY', 0.73, 0.36, 76),
        ('st',   (5, 5.0), 'sello_notin', 0.73, 0.70, 1.0, 0.34),

        # --- 6 · el cierre que manda a la pieza 2
        ('cut',   6, 'WALL'),
        ('rojo',  6, 'WHO PROFITS?', 0.50, 0.44, 104),

        # --- 7 · la pregunta al espectador
        ('cut',   7, 'CTR'),
        ('P',     7, 'bandera_us', 0.28, 0.46, 1.0, 0.40),
        ('card', (7, 1.2), 'YES OR NO' + NL + 'COMMENTS', 0.73, 0.50, 66),
    ])


# ============================================================ 2 · THE CHEAPEST WEAPON
def e02(A):
    """7 lineas. El vocabulario: el PETROLERO (lo que no pasa), la POLIZA (por que no pasa) y la
    BANDERA IRANI (quien lo hizo sin disparar).

    La animacion central va en la linea 3 —«Here is the mechanism»—, que es literalmente la linea
    que anuncia un mecanismo: doce barcos apagandose mientras la prima sube.
    """
    correr(A, [
        # --- 0 · el golpe: tres cifras y ningun hundimiento
        ('cut',  (0, -0.45), 'CTR'),
        ('P',     0, 'petrolero', 0.50, 0.44, 1.0, 0.54),
        ('rojo', (0, 2.0), '-95%', 0.26, 0.74, 104),
        ('card', (0, 4.4), '+3,600%', 0.74, 0.74, 96),

        # --- 1 · cien barcos antes, diez ahora
        ('cut',   1, 'WALL'),
        ('card',  1, '100+ SHIPS A DAY', 0.50, 0.40, 76),
        ('cut',  (1, 3.6), 'WALL'),
        ('rojo', (1, 3.8), 'NOW: 10', 0.50, 0.44, 112),

        # --- 2 · no falta petroleo, faltan barcos dispuestos
        ('cut',   2, 'CTR'),
        ('P',     2, 'barril', 0.28, 0.48, 1.0, 0.40),
        ('card', (2, 1.8), 'NOT A SHORTAGE' + NL + 'OF OIL', 0.73, 0.50, 62),

        # ============ LA ANIMACION CENTRAL ============
        # Linea 3: «Here is the mechanism.» La poliza entra a la derecha y la prima sube mientras,
        # a la izquierda, el petrolero se queda solo. El seguro es el arma.
        ('cut',   3, 'CTR'),
        ('P',     3, 'petrolero', 0.28, 0.40, 1.0, 0.34),
        ('P',    (3, 1.2), 'poliza', 0.74, 0.44, 1.0, 0.34),
        ('card', (3, 3.0), 'WAR RISK', 0.74, 0.16, 58),
        ('rojo', (3, 5.6), '7.5% - 10%' + NL + 'OF THE HULL', 0.74, 0.74, 62),
        ('rojo', (3, 9.0), '$3M - $21M' + NL + 'PER VOYAGE', 0.28, 0.76, 58),
        # ==============================================

        # --- 4 · quien cobra el riesgo
        ('cut',   4, 'CTR'),
        ('P',     4, 'lingote', 0.29, 0.50, 1.0, 0.38),
        ('card', (4, 2.2), '36x' + NL + 'SINCE JANUARY', 0.73, 0.46, 62),
        ('cut',  (4, 6.4), 'WALL'),
        ('rojo', (4, 6.6), 'BRENT  $104', 0.50, 0.44, 100),

        # --- 5 · la frase de la pieza
        ('cut',   5, 'CTR'),
        ('P',     5, 'bandera_ir', 0.28, 0.44, 1.0, 0.42),
        ('card', (5, 2.4), 'NOT SUNK.', 0.73, 0.36, 82),
        ('st',   (5, 4.6), 'sello_no', 0.73, 0.70, 1.0, 0.34),

        # --- 6 · el cierre
        ('cut',   6, 'WALL'),
        ('rojo',  6, 'UNINSURABLE.', 0.50, 0.42, 104),
        ('cut',  (6, 4.0), 'CTR'),
        ('P',    (6, 4.2), 'poliza', 0.30, 0.50, 1.0, 0.44),
        ('card', (6, 5.0), 'A PIECE' + NL + 'OF PAPER', 0.73, 0.50, 70),
    ])


# ============================================================ 3 · EIGHT MILLION A DAY
def e03(A):
    """8 lineas. El vocabulario: el HOTEL (donde va el dinero), la PILA DE LIBRAS (cuanto) y el
    SELLO SAME CONTRACT (que nada cambio salvo el precio).

    Dos animaciones, y es la pieza que mas las necesita porque es toda numeros: las DOS BARRAS en la
    linea 4 y la PILA QUE CRECE en la linea 2.
    """
    correr(A, [
        # --- 0 · el golpe: 8 millones al dia, y el 6 del dia anterior
        ('cut',  (0, -0.45), 'CTR'),
        ('P',     0, 'hotel', 0.30, 0.50, 1.0, 0.50),
        ('rojo', (0, 2.0), '£8,000,000' + NL + 'A DAY', 0.73, 0.40, 66),
        ('card', (0, 6.0), 'THE DAY BEFORE:' + NL + '£6M', 0.73, 0.76, 52),

        # --- 1 · no es una estimacion: son sus cuentas
        ('cut',   1, 'CTR'),
        ('P',     1, 'libro_mayor', 0.29, 0.50, 1.0, 0.44),
        ('card', (1, 1.8), 'THEIR OWN' + NL + 'ACCOUNTS', 0.73, 0.48, 66),

        # ============ ANIMACION 1: LA PILA QUE CRECE ============
        # Linea 2: 4.500 millones presupuestados -> 15.300 esperados. La pila sube mientras se dice.
        ('cut',   2, 'CTR'),
        ('seq',   2, -2, 'torre_n', 13, 0.30, 0.54, 1.0, 0.40, 1.0),
        ('card', (2, 1.0), '2019' + NL + '£4.5bn', 0.74, 0.30, 58),
        ('rojo', (2, 6.2), 'NOW' + NL + '£15.3bn', 0.74, 0.68, 64),
        # =======================================================

        # --- 3 · el sello: mismo contrato
        ('cut',   3, 'WALL'),
        ('card',  3, 'SAME CONTRACTS.  SAME TEN YEARS.', 0.50, 0.40, 50),
        ('st',   (3, 2.6), 'sello_same', 0.50, 0.76, 1.0, 0.40),

        # ============ ANIMACION 2: LAS DOS BARRAS ============
        # Linea 4: «Hotels take 76 % of the cost and house 35 % of the people.» Las dos barras
        # crecen a la vez y se quedan a distinta altura. La distancia entre las puntas es la pieza.
        ('cut',   4, 'CTR'),
        ('seq',   4, (4, 5.0), 'barra_d', 13, 0.50, 0.34, 1.0, 0.88, 3.0),
        ('seq',  (4, 1.0), (4, 6.0), 'barra_g', 13, 0.50, 0.60, 1.0, 0.88, 2.0),
        ('rojo', (4, 6.6), '76%  vs  35%', 0.50, 0.84, 76),
        # =====================================================

        # --- 5 · el total y el precio por noche
        ('cut',   5, 'WALL'),
        ('card',  5, '£4.2bn  ·  YEAR TO MARCH', 0.50, 0.40, 62),
        ('cut',  (5, 3.4), 'CTR'),
        ('P',    (5, 3.6), 'factura', 0.29, 0.50, 1.0, 0.42),
        ('rojo', (5, 4.4), '£107' + NL + 'PER PERSON' + NL + 'PER DAY', 0.73, 0.50, 58),

        # --- 6 · la linea que separa esto del otro debate
        ('cut',   6, 'CTR'),
        ('P',     6, 'bandera_uk', 0.28, 0.44, 1.0, 0.40),
        ('card', (6, 2.4), 'NOT THAT' + NL + 'ARGUMENT', 0.73, 0.40, 66),
        ('rojo', (6, 5.4), 'A PRICE' + NL + 'PER NIGHT', 0.73, 0.76, 56),

        # --- 7 · cierre
        ('cut',   7, 'WALL'),
        ('rojo',  7, 'WHO PAYS?', 0.50, 0.44, 112),
    ])


# ============================================================ 4 · THE PAPER THAT MOVED 49,000
def e04(A):
    """8 lineas. El vocabulario: la SENTENCIA (el papel), la VALLA (lo que el papel nombra) y el
    MAPA (donde se acaba la valla).

    **La hoja de mapa entra una sola vez**, en la linea 1, que es donde el mapa DICE algo que una
    tarjeta no puede: que Ceuta es Espana pegada a Marruecos. Todo lo demas —el esquema de la valla
    y el agua— va con props sobre la mesa y se lee como esquema, porque a la escala de la valla
    Natural Earth 50m no da (ver `arte/mapa.py`).
    """
    correr(A, [
        # --- 0 · el golpe: una sentencia, 32 dias, 49.000 personas
        ('cut',  (0, -0.45), 'CTR'),
        ('P',     0, 'resolucion', 0.30, 0.48, 1.0, 0.48),
        ('card', (0, 1.6), '29 JUNE', 0.73, 0.30, 88),
        ('rojo', (0, 4.6), '32 DAYS LATER' + NL + '49,000', 0.73, 0.66, 64),

        # --- 1 · donde esta Ceuta. LA HOJA DE MAPA, una vez.
        ('cut',   1, 'MAP'),
        ('mapa',  1),
        ('card', (1, 3.0), 'SPANISH TERRITORY', 0.50, 0.12, 54),

        # --- 2 · lo que el tribunal NO hizo, y lo que si
        ('cut',   2, 'CTR'),
        ('P',     2, 'martillo_juez', 0.29, 0.46, 1.0, 0.40),
        ('card', (2, 2.4), 'THE FENCE:' + NL + 'SUMMARY RETURN', 0.73, 0.38, 54),
        ('rojo', (2, 8.0), 'AT SEA:' + NL + 'ORDINARY PROCEDURE', 0.73, 0.74, 52),

        # ============ LA ANIMACION CENTRAL: EL ESQUEMA ============
        # Linea 3: «They went around the end of the fence, through the water.» La valla ocupa el
        # centro; la linea roja la rodea por donde se acaba. Es un ESQUEMA declarado sobre la mesa,
        # no una marca sobre un mapa: por eso puede decir esto sin deberle precision a nadie.
        ('cut',   3, 'CTR'),
        ('P',     3, 'cerca', 0.42, 0.42, 1.0, 0.62),
        ('card', (3, 1.2), 'THE FENCE', 0.42, 0.18, 52),
        ('P',    (3, 2.6), 'gota', 0.82, 0.60, 1.0, 0.16),
        ('rojo', (3, 3.4), 'AROUND' + NL + 'THE END', 0.80, 0.82, 56),
        # =========================================================

        # --- 4 · la escala: 80.000, el 2.400 % y los muertos
        ('cut',   4, 'WALL'),
        ('card',  4, '80,000 TRIED', 0.50, 0.40, 88),
        ('cut',  (4, 3.6), 'CTR'),
        ('rojo', (4, 3.8), 'CAPACITY' + NL + 'EXCEEDED BY' + NL + '2,400%', 0.30, 0.50, 58),
        ('st',   (4, 8.0), 'sello_loss', 0.73, 0.44, 1.0, 0.34),
        ('rojo', (4, 8.8), 'AT LEAST 141' + NL + 'DIED', 0.73, 0.76, 54),

        # --- 5 · la vuelta
        ('cut',   5, 'WALL'),
        ('card',  5, '3 AUGUST  ·  ~70,000 WENT BACK', 0.50, 0.42, 52),

        # --- 6 · el remate
        ('cut',   6, 'CTR'),
        ('P',     6, 'resolucion', 0.29, 0.48, 1.0, 0.42),
        ('card', (6, 1.4), 'NO NEW LAW.', 0.73, 0.34, 70),
        ('card', (6, 3.2), 'NO NEW FENCE.', 0.73, 0.60, 70),
        ('cut',  (6, 6.6), 'WALL'),
        ('rojo', (6, 6.8), 'ONE RULING.', 0.50, 0.44, 112),

        # --- 7 · cierre de serie
        ('cut',   7, 'CTR'),
        ('P',     7, 'bandera_es', 0.28, 0.46, 1.0, 0.40),
        ('card', (7, 1.2), 'FOLLOW' + NL + 'THE PAPER', 0.73, 0.48, 70),
    ])
