# -*- coding: utf-8 -*-
"""Partitura de la serie S10 («What Sweden Paid For»). Tres funciones, `e01`/`e02`/`e03`, ancladas
a las 7 lineas de cada guion.

Cada paso es una tupla anclada a una linea. `i` entero = inicio de la linea i; `(i, off)` = inicio de
la linea i + off segundos; `-i` = FIN de la linea i. El interprete (`correr`) es el del S04 y no se
copia: se carga por ruta.

**La hoja de mapa entra una vez por pieza** (decision de Agustin, 2026-09-14: *"pon mas mapas y
cosas de Suecia"*), y siempre donde el mapa DICE algo que una tarjeta no puede:

  - **01** — cuando la voz nombra Sodertalje: el punto rojo esta pegado a Estocolmo pero no es
    Estocolmo. El asesinato no fue en la capital.
  - **02** — «una mezquita chiita en las **afueras** de Estocolmo»: el mapa es el «afueras».
  - **03** — el 14 % es de **tres ciudades**, no de Suecia. El mapa las marca y evita la
    generalizacion que la nota del guion prohibe expresamente.

Todo sale de `arte/mapa.py`: Natural Earth 50m, Mercator, 229 px por grado, coordenadas reales
comprobadas al generar la hoja. Regla 24 cumplida por construccion, no a ojo.

**El vocabulario es corto y VUELVE**, una terna por pieza:

  - **01 · Momika** — el *encuadre en vivo* (como murio), el *libro quemado* (por que) y la
    *bandera sueca* (quien no lo protegio). El libro abre la pieza y vuelve en la linea 3, cuando
    se dice que por el se freno la OTAN: el mismo objeto, primero como delito y despues como
    politica exterior. Es el unico gag conceptual de la pieza.
  - **02 · Ibn Rushd** — el *cheque* (vuelve TRES veces, con importes distintos: 29 M, el corte y
    el cierre), la *bandera sueca* y los *sellos*. La repeticion del cheque es el argumento: no
    hace falta decir «otra vez» si el espectador ve el mismo papel por tercera vez.
  - **03 · Escuelas** — la *escuela* (lo que el Estado alcanza), el *pupitre* y la *mesa de cocina*
    (lo que no alcanza). La pieza entera es el corte entre esos dos muebles.

**Composicion: nunca un objeto solo** (leccion 3 del S03). Objeto a la izquierda (fx ~0,28),
contraparte a la derecha (fx ~0,73). WALL va centrado y a dos alturas.

**El primer objeto NO puede ser un `dr`** (leccion 1 del S03): el post-pase de encuadre muestrea
0,10 s despues del corte y a esa altura una caida esta a medias sobre el borde.

**`crecer` por paso.** Con dos objetos en el beat se baja a ~0,45; con tres, a ~0,30. Con el 0,62
por defecto se solapan y el post-pase apaga al que entro antes (paso en el S05: de tres banderas
quedaba una).

Regla 1 de Agustin: nada cortado. `python coreo.py check <n>` tiene que dar 0.
"""
import importlib.util as _u, os as _os

_ruta = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                      '..', 'S04_recibo_iran', 'escenas.py')
_spec = _u.spec_from_file_location('escenas_s04', _ruta)
_m = _u.module_from_spec(_spec); _spec.loader.exec_module(_m)
correr = _m.correr

NL = chr(10)


# ------------------------------------------------------- 1 · el hombre que quemo un libro
def e01(A):
    """Momika. 79,4 s · 7 lineas.

    La linea 0 es el GOLPE y dura 9,9 s: es la unica pieza de la serie que abre con el desenlace.
    Por eso el encuadre en vivo entra solo, grande y centrado los primeros segundos — y recien
    cuando la voz dice «for burning a book» aparece el libro al lado. Esa es la retencion de los
    3 s que decide el short entero (`canal/ENFOQUE_VISTAS_SUBS_2026-09-14.md` §3.2).
    """
    correr(A, [
        # --- 0 · el golpe. Camara en vivo primero; el libro entra con la palabra.
        ('cut',  (0, -0.45), 'CTR'),
        ('P',     0, 'camara_vivo', 0.30, 0.46, 1.0, 0.48),
        ('rojo', (0, 1.6), 'LIVE', 0.74, 0.30, 96),
        ('P',    (0, 3.4), 'libro_quemado', 0.74, 0.62, 1.0, 0.48),
        ('card', (0, 6.6), 'STOCKHOLM' + NL + '2025', 0.30, 0.86, 58),

        # --- 1 · quien era, y que era Suecia. 17,8 s: tres beats.
        ('cut',   1, 'CTR'),
        ('P',     1, 'bandera_se', 0.28, 0.50, 1.0, 0.52),
        ('card',  1, 'SALWAN' + NL + 'MOMIKA', 0.73, 0.36, 72),
        ('card', (1, 5.0), '2023', 0.73, 0.70, 104),
        ('cut',  (1, 10.8), 'WALL'),
        ('card', (1, 11.0), 'SWEDEN LET HIM', 0.50, 0.46, 96),

        # --- 2 · el asesinato. Vuelve el encuadre en vivo: mismo objeto, otro sentido.
        ('cut',   2, 'CTR'),
        ('P',     2, 'camara_vivo', 0.30, 0.44, 1.0, 0.50),
        ('rojo',  2, '29 JAN' + NL + '2025', 0.74, 0.34, 78),
        # El mapa entra JUSTO cuando la voz dice Sodertalje. Es el mejor uso del mapa de toda la
        # serie: el punto rojo esta al lado de Estocolmo pero no ES Estocolmo, y eso no se puede
        # decir con una tarjeta. Los dos puntos salen de la proyeccion (regla 24), no a ojo.
        ('cut',  (2, 5.0), 'MAP'),
        ('mapa', (2, 5.0)),
        ('card', (2, 6.8), 'NOT THE CAPITAL', 0.50, 0.88, 58),
        # 17,3 s son demasiados para un solo plano: en la hoja de contacto salieron tres cuadros
        # iguales. Corte a WALL con el dato del sospechoso, y vuelta a CTR para el sello.
        ('cut',  (2, 9.4), 'WALL'),
        ('card', (2, 9.6), 'A SUSPECT, NO CONVICTION', 0.50, 0.46, 74),
        ('cut',  (2, 13.6), 'CTR'),
        ('P',    (2, 13.8), 'camara_vivo', 0.30, 0.46, 1.0, 0.48),
        ('st',   (2, 14.6), 'sello_unsolved', 0.72, 0.62, 1.0, 0.44),

        # --- 3 · el precio exterior. El libro VUELVE, ahora como politica de defensa.
        ('cut',   3, 'CTR'),
        ('P',     3, 'bandera_tr', 0.28, 0.48, 1.0, 0.52),
        ('card', (3, 2.6), 'NATO' + NL + 'BLOCKED', 0.73, 0.36, 76),
        ('P',    (3, 7.6), 'libro_quemado', 0.73, 0.72, 1.0, 0.44),

        # --- 4 · la tesis. WALL, dos alturas, sin props: aca manda la frase.
        ('cut',   4, 'WALL'),
        ('card',  4, 'NOT ONE DEAD MAN', 0.50, 0.34, 88),
        ('rojo', (4, 4.8), 'ONE GUARANTEE', 0.50, 0.72, 96),

        # --- 5 · el cierre.
        ('cut',   5, 'CTR'),
        ('P',     5, 'casa_falu', 0.29, 0.48, 1.0, 0.50),
        ('rojo', (5, 1.4), 'SAY' + NL + 'ANYTHING', 0.73, 0.40, 82),
        ('card', (5, 3.4), 'SURVIVE IT?', 0.73, 0.76, 62),

        # --- 6 · la pregunta a los comentarios.
        ('cut',   6, 'WALL'),
        ('card',  6, 'ALLOWED TO BURN IT?', 0.50, 0.50, 86),
    ])


# ------------------------------------------------------- 2 · dieciseis anos de cheques
def e02(A):
    """Ibn Rushd. 82,6 s · 7 lineas.

    **El cheque vuelve tres veces** y es el argumento entero de la pieza: 29 M en la linea 0,
    otra vez en la 1 cuando la voz dice «again, and again, and again», y una tercera en el cierre
    con el sello encima. No hace falta narrar la repeticion si el espectador ve el mismo papel.
    """
    correr(A, [
        # --- 0 · el cheque, con nombre y apellido. 14,3 s.
        ('cut',  (0, -0.45), 'CTR'),
        ('P',     0, 'cheque', 0.50, 0.40, 1.0, 0.56),
        ('card', (0, 3.2), '16 YEARS', 0.28, 0.76, 78),
        ('card', (0, 6.4), 'MUSLIM' + NL + 'BROTHERHOOD', 0.74, 0.76, 52),
        # 14,3 s en un plano. Corte a WALL para el golpe de la linea, y vuelta.
        ('cut',  (0, 9.6), 'WALL'),
        ('rojo', (0, 9.8), 'NOT SECRETLY', 0.50, 0.46, 96),

        # --- 1 · la cronica. 18,6 s: el beat mas largo de la serie, tres momentos.
        ('cut',   1, 'CTR'),
        ('P',     1, 'bandera_se', 0.28, 0.46, 1.0, 0.52),
        ('card',  1, 'IBN RUSHD', 0.73, 0.34, 76),
        ('card', (1, 4.6), '2008' + NL + '2024', 0.73, 0.70, 72),
        ('cut',  (1, 10.4), 'WALL'),
        ('rojo', (1, 10.6), '29 000 000 A YEAR', 0.50, 0.46, 82),
        ('cut',  (1, 14.6), 'CTR'),
        ('P',    (1, 14.8), 'cheque', 0.50, 0.44, 1.0, 0.54),
        ('card', (1, 16.2), 'AGAIN', 0.50, 0.86, 72),

        # --- 2 · el corte. Los dos sellos de la pieza, separados para que no se tapen.
        ('cut',   2, 'CTR'),
        ('P',     2, 'riksdag', 0.28, 0.44, 1.0, 0.46),
        ('card', (2, 2.8), '2023' + NL + 'AUDIT', 0.73, 0.38, 66),
        ('st',   (2, 7.0), 'sello_cut', 0.50, 0.76, 1.0, 0.44),
        ('st',   (2, 12.0), 'sello_closed', 0.50, 0.90, 1.0, 0.44),

        # --- 3 · el juicio de la casa. WALL.
        ('cut',   3, 'WALL'),
        ('card',  3, 'SIXTEEN YEARS', 0.50, 0.34, 98),
        ('rojo', (3, 5.0), 'ALREADY FINISHED', 0.50, 0.72, 88),

        # --- 4 · sigue abierto.
        ('cut',   4, 'CTR'),
        ('P',     4, 'krona', 0.28, 0.48, 1.0, 0.50),
        ('card', (4, 2.4), 'MAY' + NL + '2026', 0.73, 0.36, 76),
        # «una mezquita chiita en las AFUERAS de Estocolmo»: el mapa dice el «afueras».
        ('cut',  (4, 5.2), 'MAP'),
        ('mapa', (4, 5.2)),
        ('rojo', (4, 6.4), 'IRANIAN REGIME', 0.50, 0.88, 64),

        # --- 5 · el cierre: el cheque por tercera vez, con el sello encima.
        ('cut',   5, 'CTR'),
        ('P',     5, 'cheque', 0.50, 0.42, 1.0, 0.52),
        ('st',   (5, 2.2), 'sello_revoked', 0.50, 0.82, 1.0, 0.44),

        # --- 6 · la pregunta.
        ('cut',   6, 'WALL'),
        ('card',  6, 'SHOULD SWEDEN HAVE PAID?', 0.50, 0.50, 78),
    ])


# ------------------------------------------------------- 3 · lo que no cierra
def e03(A):
    """Escuelas. 72,4 s · 7 lineas.

    La pieza es **un corte entre dos muebles**: la escuela y el pupitre (lo que el Estado alcanza)
    contra la mesa de cocina (lo que no). La linea 1 dura 13,7 s con una sola frase corta —es la
    bisagra, y la voz deja un silencio largo ahi—, asi que el beat lleva movimiento propio
    (`late`) para que nada quede congelado.
    """
    correr(A, [
        # --- 0 · lo que se cerro. 15,0 s.
        ('cut',  (0, -0.45), 'CTR'),
        ('P',     0, 'escuela', 0.30, 0.46, 1.0, 0.54),
        ('rojo', (0, 2.4), '17', 0.74, 0.34, 150),
        ('card', (0, 5.0), 'SHUT SINCE' + NL + '2019', 0.74, 0.70, 56),
        ('card', (0, 10.2), 'SAPO WARNED', 0.30, 0.86, 58),

        # --- 1 · la bisagra. Frase corta, 13,7 s de aire: el objeto TIENE que respirar.
        ('cut',   1, 'WALL'),
        ('card',  1, 'WHAT THE STATE CAN REACH', 0.50, 0.46, 76),
        ('cut',  (1, 7.0), 'CTR'),
        ('late', (1, 7.2), (1, 13.2), 'pupitre', 0.30, 0.50, 1.0),
        ('card', (1, 7.4), 'AND WHAT' + NL + 'IT CANNOT', 0.74, 0.46, 64),

        # --- 2 · el dato. 14,7 s.
        ('cut',   2, 'CTR'),
        ('P',     2, 'pupitre', 0.28, 0.46, 1.0, 0.52),
        ('card', (2, 2.6), '6 000' + NL + 'FIFTEEN-YEAR-OLDS', 0.73, 0.34, 54),
        # La encuesta es de TRES ciudades y el mapa las tiene las tres marcadas. Es la unica
        # forma honesta de decir en imagen que el 14 % no es «Suecia entera» (nota del guion).
        ('cut',  (2, 5.4), 'MAP'),
        ('mapa', (2, 5.4)),
        ('rojo', (2, 7.0), '14%', 0.50, 0.86, 120),
        ('cut',  (2, 10.2), 'CTR'),
        ('P',    (2, 10.4), 'pupitre', 0.28, 0.46, 1.0, 0.52),
        ('card', (2, 10.8), 'HONOUR NORMS', 0.73, 0.50, 58),

        # --- 3 · Sapo.
        ('cut',   3, 'WALL'),
        ('card',  3, 'ONE OF THE TWO', 0.50, 0.34, 84),
        ('rojo', (3, 4.2), 'BIGGEST THREATS', 0.50, 0.72, 92),

        # --- 4 · la eleccion.
        ('cut',   4, 'CTR'),
        ('P',     4, 'riksdag', 0.28, 0.46, 1.0, 0.44),
        ('rojo', (4, 2.0), '-11', 0.73, 0.42, 140),
        ('P',    (4, 4.2), 'papeleta', 0.30, 0.82, 1.0, 0.22),
        ('card', (4, 4.6), 'AND NO PROMISE', 0.73, 0.80, 56),

        # --- 5 · el cierre: la mesa de cocina, sola y grande. Es la imagen de la serie.
        ('cut',   5, 'CTR'),
        ('P',     5, 'mesa_cocina', 0.50, 0.44, 1.0, 0.58),
        ('card', (5, 2.2), 'NOBODY INSPECTS THIS', 0.50, 0.80, 58),

        # --- 6 · la pregunta.
        ('cut',   6, 'WALL'),
        ('card',  6, 'TOO LATE?', 0.50, 0.50, 104),
    ])
