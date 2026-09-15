# -*- coding: utf-8 -*-
"""S12 · la PARTITURA de las cuatro piezas sobre el motor v4. El motor esta en `coreo4.py`.

Manda `PLAN_VISUAL_V4.md` (no `escenas.py` v1, que era «plano fijo + cartel»).

COMO SE LEE UNA PARTITURA

  · Cada `pieza_N(p)` declara primero los ANCLAJES (`p.t('fortynine')` = cuando George dice
    «forty-nine»), despues los PLANOS y despues el contenido. Nada esta atado al principio de una
    linea: todo cuelga de la palabra real, asi que si se regenera la voz la coreografia se mueve
    con ella en vez de quedarse descolgada.
  · `p.plano(t0, t1, centro0, z0, centro1, z1, tipo)` = un corte + UN viaje motivado.
  · `tipo='mesa'` ademas oscurece el mundo y pone el documento; `tipo='mapa'` lo deja a la vista.
  · Los planos van seguidos y sin huecos: el `t1` de uno es el `t0` del siguiente.

LAS TRES CORRECCIONES DE LA AUDITORIA, APLICADAS AQUI

  1. MESA = mundo oscurecido + DOCUMENTO grande + props de escritorio. **Ninguna hoja rayada.**
  2. En la pieza 4, Ceuta se pinta de espanol POR ENCIMA de Marruecos (`_capas_ceuta`).
  3. El primer plano de las cuatro es MAPA con la camara viajando, y dura mas que el gancho
     (`HOOK` = 3,5 s). `coreo4.Pieza.cerrar()` lo comprueba y aborta si no.

UNA DESVIACION DEL PLAN, A PROPOSITO. `PLAN_VISUAL_V4.md` §1 pedia que la linea 5 de la pieza 1
(«The Strait of Hormuz is that day») se fuera al `mundo_hormuz` de la pieza 2. Una `Scene` tiene UN
mundo: hacerlo obligaria a dos escenas y dos renders por pieza, y a pegarlos. Se resuelve con un
plano de MESA (el mapa oscurecido no afirma ninguna geografia) y el petrolero grande. Queda anotado
en `PRODUCCION_V4.md`.
"""
import os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import props as PR
import mapa_v2 as MV
from coreo4 import HOOK, ESCRITORIO

NL = chr(10)
ROJO = PR.ROJO


# ===================================================================== PIEZA 4 · CEUTA
def pieza_4(p):
    """THE PAPER THAT MOVED 49,000 — una sentencia, 32 dias y una frontera que dejo de funcionar.

    TODOS los tiempos salen de ANCLAJES, ninguno es un numero suelto. Es lo que permite recompactar
    la voz (o regenerarla) sin volver a escribir la coreografia: los cortes se mueven con ella.
    """
    P_ = p.P
    CE, FN, TA, AL, GI, TG, TE = (P_('Ceuta'), P_('Fnideq'), P_('Tarifa'), P_('Algeciras'),
                                  P_('Gibraltar'), P_('Tangier'), P_('Tetouan'))
    Z = p.zmin
    D = p.dur

    # ---------------- anclajes (la voz manda)
    t_ruling = p.t('ruling')                       # «published a ruling»
    t_32 = p.t('thirtytwo')
    t_49 = p.t('fortynine')
    t_ceuta1 = p.t('ceuta')
    t_hours = p.t('twentyfour', desde=t_ceuta1)
    t_ceuta2 = p.t('ceuta', desde=t_ceuta1 + 1.0)
    t_spain = p.t('spain', desde=t_ceuta2)
    t_main = p.t('mainland')
    t_fence1 = p.t('fence', desde=t_main)
    t_water1 = p.t('water', desde=t_fence1)
    t_ends = p.t('ends', desde=t_water1)
    t_years = p.t('years', desde=t_ends)
    t_supreme = p.t('supreme')
    t_notstrike = p.t('not', desde=t_supreme)
    t_down = p.t('down', desde=t_notstrike)
    t_narrow = p.t('narrower')
    t_fence2 = p.t('fence', desde=t_narrow)
    t_sea = p.t('sea', desde=t_fence2)
    t_swim = p.t('swim', desde=t_sea)
    t_ord = p.t('ordinary', desde=t_swim)
    t_pub = p.t('published', desde=t_ord)
    t_spread = p.t('spread', desde=t_pub)
    t_went = p.t('went', desde=t_spread)
    t_fence3 = p.t('fence', desde=t_went)
    t_water2 = p.t('water', desde=t_fence3)
    t_80 = p.t('eighty', desde=t_water2)
    t_tried = p.t('tried', desde=t_80)
    t_exc = p.t('exceeded', desde=t_tried)
    t_pct = p.t('percent', desde=t_exc)
    t_141 = p.t('fortyone', desde=t_pct)
    t_died = p.t('died', desde=t_141)
    t_aug = p.t('august', desde=t_died)
    t_70 = p.t('seventy', desde=t_aug)
    t_law = p.t('law', desde=t_70)
    t_fence4 = p.t('fence', desde=t_law)
    t_clar = p.t('clarified', desde=t_fence4)
    t_four = p.t('four', desde=t_clar + 2.0)
    t_com = p.t('comments', desde=t_four)

    # ---------------- el color narra, y Ceuta gana a Marruecos (correccion 2)
    C = p.mu.meta['capas']
    p.mu.add_layer(C['esp'], t_spain, 1.3, mode='fade')
    if 'ceuta' in C:
        p.mu.add_layer(C['mar'], t_main, 1.5, mode='fade')
        # la peninsula, del color de Espana, DESPUES de Marruecos: gana la de arriba
        p.mu.add_layer(C['ceuta'], t_main + 0.35, 1.1, mode='fade')
    else:
        print('   AVISO pieza 4: sin capa de enclaves -> NO se pinta Marruecos (antes un mapa sin '
              'color que un mapa que diga que Ceuta es Marruecos)')
    p.mu.add_layer(C['marcas'], t_spain, 0.3, mode='fade')      # las marcas, siempre por encima

    # ---------------- los cortes, por anclaje
    K = [0.0,
         t_ruling + 0.60,          # 1 -> 2   a la MESA: acaba de decir «published a ruling»
         t_ceuta1 - 0.25,          # 2 -> 3   al MAPA, cerrando sobre Ceuta
         t_ceuta2 + 0.70,          # 3 -> 4   abierto: «Ceuta is Spain»
         t_fence1 + 0.10,          # 4 -> 5   cerrado sobre el istmo: «a land fence»
         t_ends + 1.70,            # 5 -> 6   abierto: «water at both ends»
         p.L(2)[0] - 0.06,         # 6 -> 7   MESA: la sentencia
         t_down + 0.90,            # 7 -> 8   MAPA cerrado: «something much narrower»
         t_fence2 - 0.30,          # 8 -> 9   MAPA abierto: el jurista
         p.L(3)[0] - 0.08,         # 9 -> 10  MESA: «the ruling was published»
         t_pub + 0.55,             # 10 -> 11 MAPA: la ruta empieza
         t_fence3 - 0.25,          # 11 -> 12 MAPA cerrado: «through the water»
         p.L(4)[0] - 0.07,         # 12 -> 13 MAPA abierto: 80.000
         t_exc + 0.00,             # 13 -> 14 MAPA cerrado: +2.400 %
         p.L(5)[0] - 0.11,         # 14 -> 15 MESA: los muertos
         t_aug + 0.50,             # 15 -> 16 MAPA: la vuelta
         p.L(6)[0] - 0.13,         # 16 -> 17 MESA: «nobody changed a law»
         t_clar + 0.50,            # 17 -> 18 MAPA cerrado: «one ruling»
         p.L(7)[0] - 0.20,         # 18 -> 19 MAPA abierto: el cierre
         D]

    # ---------------- planos. ABIERTO y CERRADO se ALTERNAN a proposito.
    # Dos planos de mapa seguidos con zoom parecido no se leen como un corte: la camara salta pero
    # la pantalla no cambia. El primer montaje de esta pieza tenia asi un tramo de 20 s que
    # `ritmo.py` contaba —con razon— como UN plano. `Pieza._cortes_flojos()` lo avisa ahora.
    MED_CF = ((CE[0] + FN[0]) / 2, (CE[1] + FN[1]) / 2)
    MED_TC = ((TA[0] + CE[0]) / 2, (TA[1] + CE[1]) / 2)
    PLAN = [
        ('mapa', (MED_TC[0] - 40, MED_TC[1] + 150), Z + 0.02, (CE[0] - 30, CE[1] + 40), Z + 0.34),
        ('mesa', (CE[0] - 70, CE[1] + 30), 1.05, (CE[0] + 30, CE[1] - 30), 1.732),
        ('mapa', (CE[0] + 110, CE[1] + 120), 1.95, (CE[0] - 20, CE[1] - 10), 2.45),
        ('mapa', (MED_TC[0], MED_TC[1] + 60), Z + 0.10, (CE[0] - 40, CE[1] + 20), Z + 0.42),
        ('mapa', (CE[0] - 90, CE[1] + 150), 2.05, (CE[0] + 40, CE[1] + 40), 2.55),
        ('mapa', (CE[0] + 70, CE[1] + 90), Z + 0.18, (CE[0] - 50, CE[1] + 180), Z + 0.52),
        ('mesa', (CE[0] - 60, CE[1] - 40), 1.08, (CE[0] + 40, CE[1] + 40), 1.782),
        ('mapa', (CE[0] - 80, CE[1] + 130), 2.10, (CE[0] + 30, CE[1] + 30), 2.60),
        ('mapa', (1180, 980), 0.98, (1330, 1120), 1.30),                      # 9 · el jurista
        ('mesa', (CE[0] + 40, CE[1] - 30), 1.06, (CE[0] - 50, CE[1] + 40), 1.749),
        ('mapa', (MED_CF[0] + 90, MED_CF[1] + 40), 1.28, (MED_CF[0] - 30, MED_CF[1] - 30), 1.72),
        ('mapa', (MED_CF[0] - 60, MED_CF[1] + 60), 2.45, (CE[0] - 10, CE[1] + 20), 2.85),
        ('mapa', (CE[0] + 90, CE[1] + 140), Z + 0.14, (CE[0] - 40, CE[1] - 20), Z + 0.46),
        ('mapa', (CE[0] - 70, CE[1] + 40), 2.00, (CE[0] + 50, CE[1] + 130), 2.45),
        ('mesa', (CE[0] + 40, CE[1] - 30), 1.12, (CE[0] - 50, CE[1] + 40), 1.848),
        ('mapa', (FN[0] + 110, FN[1] - 90), 1.44, (TE[0] - 40, TE[1] - 60), 1.06),
        ('mesa', (CE[0] - 50, CE[1] + 30), 1.08, (CE[0] + 40, CE[1] - 30), 1.782),
        ('mapa', (CE[0] + 60, CE[1] + 60), 2.05, (CE[0] - 30, CE[1] - 20), 2.50),
        ('mapa', (MED_TC[0] + 60, MED_TC[1] + 40), Z + 0.30, (MED_TC[0] - 60, MED_TC[1] + 190), Z + 0.02),
    ]
    for i, (tipo, c0, z0, c1, z1) in enumerate(PLAN):
        p.plano(K[i], K[i + 1], c0, z0, c1, z1, tipo)

    # ---------------- MESA: los documentos (correccion 1 · ninguna hoja rayada)
    p.mesa(K[1], K[2], 'sentencia', fy=0.42, alto=0.52)
    p.mesa(K[6], K[7], 'sentencia', fy=0.40, alto=0.46,
           escritorio=[('martillo_juez', 0.175, 0.775, 0.115), ('lupa', 0.130, 0.820, 0.078),
                       ('regla', 0.858, 0.150, 0.022)])
    p.mesa(K[9], K[10], 'sentencia', fy=0.40, alto=0.46,
           escritorio=[('lupa', 0.130, 0.820, 0.078), ('moneda', 0.888, 0.848, 0.042)])
    p.mesa(K[14], K[15], 'resolucion', fy=0.40, alto=0.44,
           escritorio=[('lupa', 0.130, 0.820, 0.078), ('regla', 0.858, 0.150, 0.022)])
    p.mesa(K[16], K[17], 'sentencia', fy=0.42, alto=0.50)

    # ---------------- contenido, beat por beat
    # Durante el gancho (0-3,5 s) la tarjeta grande la pone `armar_vertical`, pero el cuerpo no
    # puede estar vacio: la fecha entra ya y va ABAJO, fuera de donde cae el gancho.
    p.cifra('29 JUNE 2026', 0.10, K[1] + 0.35, fy=0.625, alto=0.070, size=96)
    p.rotulo('THE RULING', K[1] + 0.25, K[2] - 0.10)
    p.card('A SPANISH COURT', K[1] + 0.40, K[2] - 0.15, fy=0.735, alto=0.050, size=60, z=54)
    p.cifra('29 · VI · 2026', K[1] + 0.80, K[2] - 0.15, fy=0.825, alto=0.062, size=84)
    p.card('32 DAYS LATER', t_32 + 0.35, K[2] - 0.15, fy=0.905, alto=0.052, size=62, z=54)

    # LA CIFRA CRUZA EL CORTE. Es lo nuevo del v4: en la v3 los carteles vivian en coordenadas de
    # mundo y el post-pass los APAGABA en cada corte, y cada juntura dejaba medio segundo de
    # pantalla muda. Aca entra en la MESA y sigue viva sobre el mapa.
    p.cifra('49,000', t_49 + 0.10, K[3] - 0.30, fy=0.325, alto=0.150, size=210)
    p.card('IN 24 HOURS', t_hours + 0.15, K[3] - 0.15, fy=0.470, alto=0.048, size=62, z=60)
    p.rotulo('INTO CEUTA', t_hours - 0.20, K[3] - 0.10)

    p.card('CEUTA IS SPAIN', t_ceuta2 + 0.05, K[4] + 0.20, fy=0.655, alto=0.055, size=70, z=56)
    p.card('ON THE AFRICAN' + NL + 'MAINLAND', t_main + 0.20, K[4] + 0.20, fy=0.760, alto=0.082,
           size=64, tcolor=ROJO, z=56)
    p.prop('cerca', K[4] + 0.02, K[5] - 0.10, 0.50, 0.415, 0.086, z=46, entra=0.12, sfx='stamp')
    p.card('A LAND FENCE', t_fence1 + 0.15, K[5] - 0.10, fy=0.545, alto=0.048, size=60, z=54,
           entra=0.14)
    p.prop('gota', t_water1 + 0.10, K[6] - 0.10, 0.190, 0.415, 0.052, z=48)
    p.prop('gota', t_water1 + 0.35, K[6] - 0.10, 0.810, 0.415, 0.052, z=48)
    p.card('OPEN WATER' + NL + 'AT BOTH ENDS', t_water1 + 0.55, K[6] - 0.10, fy=0.560, alto=0.080,
           size=58, tcolor=ROJO, z=54)
    p.card('FOR YEARS:' + NL + 'RETURNED ON THE SPOT', t_years + 0.20, K[6] + 0.30, fy=0.755,
           alto=0.078, size=56, z=54)

    p.rotulo('THE SUPREME COURT', t_supreme + 0.10, K[7] - 0.10)
    p.card('DID NOT STRIKE' + NL + 'THAT DOWN', t_notstrike + 0.20, K[7] - 0.10, fy=0.730,
           alto=0.088, size=64, tcolor=ROJO, z=56)
    p.rotulo('SOMETHING NARROWER', t_narrow - 0.20, K[8] - 0.10)
    # Las dos vias conviven en pantalla a proposito: la distancia entre las dos ES la sentencia.
    # Apiladas, no encimadas (regla 22).
    p.card('THE FENCE' + NL + 'SUMMARY RETURN', K[7] - 0.25, K[9] - 0.05, fy=0.650, alto=0.086,
           size=58, z=56)
    p.card('AT SEA' + NL + 'ORDINARY PROCEDURE', t_sea - 0.35, K[9] - 0.05, fy=0.800, alto=0.086,
           size=58, tcolor=ROJO, z=56)
    p.rotulo('TWO PROCEDURES', K[8] + 0.10, K[9] - 0.05)
    # Sale antes del final del plano: la tarjeta «SWIM AROUND THE BARRIER» entra arriba y con el rig
    # todavia en pantalla le caia en la cara (visto en la hoja de contacto).
    p.figura('05_jurista', K[8] + 0.15, min(K[9] - 0.15, t_swim - 0.20), sobre=(-5.502, 36.176),
             mira='Ceuta', alto_rel=0.25, gestos=(K[8] + 1.8,))
    p.card('SWIM AROUND' + NL + 'THE BARRIER', t_swim + 0.10, K[10] - 0.10, fy=0.185, alto=0.078,
           size=58, z=54)
    p.card('THE ORDINARY PROCEDURE', t_ord + 0.10, K[10] - 0.10, fy=0.310, alto=0.050, size=58,
           tcolor=ROJO, z=54)

    p.card('THE RULING' + NL + 'WAS PUBLISHED', t_pub + 0.10, K[11] - 0.10, fy=0.185, alto=0.078,
           size=60, z=54)
    p.card('THE INSTRUCTIONS SPREAD', t_spread + 0.15, K[11] - 0.10, fy=0.310, alto=0.052,
           size=58, z=54)

    # LA RUTA: rodea el extremo de la valla POR EL AGUA. Los puntos se comprueban contra el PNG del
    # mundo (`coreo4.Pieza.ruta`): Natural Earth 50m no resuelve la bahia, asi que lo que se
    # verifica es el agua DIBUJADA, que es la que se ve. Los tres tramos de en medio dan 100 %.
    p.ruta([(-5.3568, 35.8501), (-5.3302, 35.8419), (-5.2963, 35.8556), (-5.2815, 35.8711),
            (-5.2963, 35.8813), (-5.3213, 35.8896)],
           t_went - 0.70, K[12] - 0.35, width=12, verificar='agua')
    p.card('AROUND THE END' + NL + 'OF THE FENCE', t_went + 0.10, K[12] - 0.10, fy=0.175,
           alto=0.080, size=58, tcolor=ROJO, z=56)
    p.card('THROUGH THE WATER', t_water2 + 0.10, K[12] - 0.10, fy=0.300, alto=0.050, size=58, z=56)

    p.cifra('80,000', t_80 + 0.10, K[13] + 0.12, fy=0.320, alto=0.135, size=195)
    p.card('TRIED', t_tried + 0.10, K[13] - 0.10, fy=0.450, alto=0.044, size=58, z=60)
    p.cifra('+2,400%', t_pct - 0.60, K[14] - 0.10, fy=0.320, alto=0.135, size=190)
    p.card('CAPACITY EXCEEDED', K[13] + 0.02, K[14] - 0.10, fy=0.470, alto=0.072, size=76, z=60,
           entra=0.12, sfx='stamp')

    p.prop('sello_loss', t_141 - 0.30, K[15] - 0.10, 0.50, 0.400, 0.105, z=52, entra=0.30,
           sfx='stamp')
    p.card('AT LEAST 141 DIED', t_141 + 0.25, K[15] - 0.10, fy=0.720, alto=0.055, size=64,
           tcolor=ROJO, z=56)

    p.card('3 AUGUST', t_aug - 0.45, K[16] - 0.10, fy=0.180, alto=0.055, size=72, z=56)
    p.cifra('~70,000' + NL + 'WENT BACK', t_70 + 0.20, K[16] - 0.10, fy=0.360, alto=0.135, size=120)

    p.card('NOBODY CHANGED A LAW', t_law - 0.30, K[17] - 0.10, fy=0.735, alto=0.052, size=60, z=56)
    p.card('NOBODY MOVED A FENCE', t_fence4 - 0.20, K[17] - 0.10, fy=0.830, alto=0.052, size=60,
           z=56)
    # ONE RULING cruza el corte de K[18] (lo que el HUD del v4 permite y el v3 no).
    p.cifra('ONE RULING.', t_clar + 0.20, K[18] + 1.20, fy=0.330, alto=0.115, size=150)
    # FOUR DAYS arranca DENTRO de la linea 6: el reparto por linea la corta antes, pero la voz
    # sigue diciendo «...stopped working for four days». Sin esto, `sync` marca CIFRA_SIN_PANTALLA
    # en la linea 6, y tiene razon.
    p.card('FOUR DAYS', K[18] + 0.05, D - 0.80, fy=0.180, alto=0.060, size=76, tcolor=ROJO, z=58)
    p.card('FOLLOW' + NL + 'THE PAPER', K[18] + 1.35, D - 0.10, fy=0.330, alto=0.105, size=96, z=58)
    p.card('COMMENTS', t_com - 0.40, D - 0.10, fy=0.480, alto=0.046, size=60, tcolor=ROJO, z=58)

    p.subtitulos(['twenty-ninth', 'June,', 'Thirty-two', 'forty-nine', 'thousand', 'Ceuta',
                  'Ceuta.', 'Spain,', 'Spain.', 'not', 'fence,', 'fence.', 'sea.', 'water.',
                  'Eighty', 'thousand.', 'percent.', 'forty-one', 'died.', 'seventy', 'law.',
                  'four', 'days.'])


# ===================================================================== PIEZA 1 · EL TANQUE
def pieza_1(p):
    """THE EMPTY TANK — la reserva estrategica de EE. UU. al nivel de 1982, con la guerra empezada."""
    P_ = p.P
    FR, WI, LC, BR, HO, NO = (P_('Freeport'), P_('Winnie'), P_('Lake Charles'),
                              P_('Baton Rouge'), P_('Houston'), P_('New Orleans'))
    Z = p.zmin
    D = p.dur
    MED = ((FR[0] + BR[0]) / 2, (FR[1] + BR[1]) / 2)
    MAR = (MED[0], MED[1] + 620)                 # mar abierto: encuadre de tono distinto

    t_march = p.t('march')
    t_amer = p.t('america')
    t_res = p.t('reserve', desde=t_amer)
    t_up = p.t('up', desde=t_res)
    t_39a = p.t('thirtynine', desde=t_up)
    t_full = p.t('full', desde=t_39a)
    t_reagan = p.t('reagan')
    t_term = p.t('term', desde=t_reagan)
    t_filing = p.t('filing')
    t_285 = p.t('eightyfive', desde=t_filing)
    t_barrels1 = p.t('barrels', desde=t_285)
    t_sept = p.t('september', desde=t_barrels1)
    t_727 = p.t('twentyseven', desde=t_sept)
    t_empt = p.t('emptied', desde=t_727)
    t_11 = p.t('eleventh', desde=t_empt)
    t_172 = p.t('seventytwo', desde=t_11)
    t_agreed = p.t('agreed', desde=t_172)
    t_17 = p.t('seventeen', desde=t_agreed)
    t_5w = p.t('five', desde=t_17)
    t_19 = p.t('nineteen', desde=t_5w)
    t_brent = p.t('brent', desde=t_19)
    t_61 = p.t('sixtyone', desde=t_brent)
    t_oneday = p.t('exactly', desde=t_61)
    t_stops = p.t('stops', desde=t_oneday)
    t_hormuz = p.t('hormuz', desde=t_stops)
    t_39b = p.t('thirtynine', desde=t_hormuz)
    t_money = p.t('money', desde=t_39b)
    t_should = p.t('should', desde=t_money)
    t_com = p.t('comments', desde=t_should)

    C = p.mu.meta['capas']
    p.mu.add_layer(C['usa'], t_amer + 0.10, 1.4, mode='fade')
    p.mu.add_layer(C['marcas'], t_amer + 0.10, 0.3, mode='fade')

    K = [0.0,
         t_res + 0.55,          # 1 -> 2   cierra sobre los domos
         t_up + 0.60,           # 2 -> 3   MESA: el deposito
         t_reagan - 0.55,       # 3 -> 4   MAPA abierto: Reagan
         t_term + 0.60,         # 4 -> 5   MESA: el parte semanal
         t_filing + 0.80,       # 5 -> 6   MAPA cerrado: 285 millones
         t_sept + 0.90,         # 6 -> 7   MESA: 727 millones
         p.L(2)[0] - 0.05,      # 7 -> 8   MAPA abierto: el burocrata
         t_11 - 0.55,           # 8 -> 9   MESA: el decreto
         t_172 + 0.90,          # 9 -> 10  MAPA cerrado: 172 millones (el plano 9 daba 6,05 s)
         p.L(3)[0] - 0.05,      # 10 -> 11 MAPA: el tanque se vacia
         t_17 - 0.55,           # 11 -> 12 MAPA cerrado: +17 %
         p.L(4)[0] - 0.05,      # 12 -> 13 MAPA abierto: cinco semanas
         t_brent + 0.55,        # 13 -> 14 MESA: Brent
         p.L(5)[0] - 0.05,      # 14 -> 15 MESA: el petrolero
         t_stops - 0.45,        # 15 -> 16 MESA: el deposito vacio / Hormuz
         p.L(6)[0] - 0.05,      # 16 -> 17 MAPA cerrado: vuelve el 39 %
         t_money - 0.80,        # 17 -> 18 MAPA abierto: la moneda
         p.L(7)[0] - 0.05,      # 18 -> 19 MAPA: la pregunta
         D]

    PLAN = [
        ('mapa', (MED[0] + 60, MED[1] + 300), Z + 0.02, (MAR[0] + 20, MAR[1] + 190), Z + 0.34),
        ('mapa', (WI[0] - 40, WI[1] - 300), Z + 0.95, (WI[0] + 60, WI[1] - 20), Z + 1.42),
        ('mesa', (MED[0] - 60, MED[1] + 40), 1.02, (MED[0] + 50, MED[1] - 40), 1.683),
        ('mapa', (MAR[0] - 80, MAR[1] - 40), Z + 0.06, (LC[0] + 40, LC[1] + 220), Z + 0.38),
        ('mesa', (MED[0] + 60, MED[1] - 30), 1.06, (MED[0] - 50, MED[1] + 50), 1.749),
        ('mapa', (FR[0] + 90, FR[1] + 150), Z + 0.52, (FR[0] - 40, FR[1] + 10), Z + 0.96),
        ('mesa', (MED[0] + 50, MED[1] - 40), 1.10, (MED[0] - 60, MED[1] + 40), 1.815),
        ('mapa', (1120, 1180), Z + 0.10, (1280, 1320), Z + 0.44),          # 8 · el burocrata
        ('mesa', (MED[0] - 60, MED[1] + 50), 1.04, (MED[0] + 50, MED[1] - 40), 1.716),
        ('mapa', (BR[0] - 60, BR[1] + 130), Z + 0.56, (BR[0] + 50, BR[1] - 20), Z + 1.00),
        ('mapa', (MAR[0] + 60, MAR[1] + 30), Z + 0.04, (WI[0] - 30, WI[1] + 40), Z + 0.46),
        ('mesa', (WI[0] - 60, WI[1] + 120), 1.06, (WI[0] + 70, WI[1] - 30), 1.749),
        ('mapa', (MAR[0] - 40, MAR[1] + 60), Z + 0.02, (LC[0] + 30, LC[1] + 30), Z + 0.44),
        ('mesa', (LC[0] + 60, LC[1] + 120), 1.08, (LC[0] - 70, LC[1] - 10), 1.782),
        ('mesa', (MED[0] - 50, MED[1] + 40), 1.02, (MED[0] + 60, MED[1] - 40), 1.683),
        ('mesa', (MED[0] + 60, MED[1] - 40), 1.08, (MED[0] - 50, MED[1] + 50), 1.782),
        ('mapa', (FR[0] + 60, FR[1] + 140), Z + 0.58, (FR[0] - 50, FR[1] - 10), Z + 0.98),
        ('mesa', (MAR[0] + 40, MAR[1] - 260), 1.06, (LC[0] - 40, LC[1] - 260), 1.749),
        ('mapa', (MAR[0] + 20, MAR[1] + 240), Z + 0.02, (FR[0] + 40, FR[1] - 40), Z + 0.44),
    ]
    for i, (tipo, c0, z0, c1, z1) in enumerate(PLAN):
        p.plano(K[i], K[i + 1], c0, z0, c1, z1, tipo)

    p.mesa(K[2], K[3], 'deposito_oil', fy=0.400, alto=0.420)
    p.mesa(K[4], K[5], 'informe', fy=0.400, alto=0.460)
    p.mesa(K[6], K[7], 'informe', fy=0.400, alto=0.460,
           escritorio=[('lupa', 0.130, 0.820, 0.078), ('regla', 0.858, 0.150, 0.022)])
    p.mesa(K[8], K[9], 'decreto', fy=0.400, alto=0.480)
    p.mesa(K[11], K[12], 'flecha_arriba', fy=0.400, alto=0.330,
           escritorio=[('moneda', 0.888, 0.848, 0.042)])
    p.mesa(K[13], K[14], 'barril', fy=0.405, alto=0.330,
           escritorio=[('lupa', 0.130, 0.820, 0.078), ('regla', 0.858, 0.150, 0.022)])
    p.mesa(K[14], K[15], 'petrolero', fy=0.410, alto=0.300)
    p.mesa(K[17], K[18], 'moneda', fy=0.400, alto=0.260,
           escritorio=[('lupa', 0.130, 0.820, 0.078)])
    # El plano 16 usa OTRO objeto a proposito: dos planos de mesa seguidos con el mismo documento
    # no se leen como un corte (el documento es HUD y no se mueve con la camara).
    p.mesa(K[15], K[16], 'deposito_oil', fy=0.400, alto=0.400,
           escritorio=[('lupa', 0.130, 0.820, 0.078)])

    p.rotulo('THE RESERVE', 0.85, K[1] - 0.10)
    p.cifra('OPENED IN MARCH', 0.10, K[1] + 0.25, fy=0.640, alto=0.062, size=84,
            tcolor=PR.TINTA)
    p.card('TO PUSH THE PRICE DOWN', t_res + 0.20, K[2] - 0.10, fy=0.745, alto=0.048, size=58,
           z=54)
    p.cifra('THE PRICE WENT UP', t_up + 0.05, K[3] - 0.10, fy=0.185, alto=0.058, size=76)
    # el deposito dice el dato ANTES que la tarjeta: se vacia hasta el 39 %
    p.secuencia('tanque_n', K[2] + 0.15, t_39a - 0.10, 12, 5, 0.50, 0.400, 0.330, z=44,
                nombre='prop:deposito_oil')
    p.cifra('39% FULL', t_39a + 0.10, K[3] - 0.10, fy=0.690, alto=0.115, size=150)
    p.card('LAST TIME THIS LOW:' + NL + 'RONALD REAGAN, FIRST TERM', K[3] - 0.15, K[4] + 0.20,
           fy=0.190, alto=0.082, size=54, z=54)
    p.cifra('1982', t_reagan + 0.55, K[4] + 0.20, fy=0.330, alto=0.090, size=130)

    p.rotulo('ITS OWN WEEKLY FILING', K[4] + 0.30, K[5] - 0.10)
    p.card('NOT AN ESTIMATE', K[4] + 0.45, K[5] + 0.85, fy=0.735, alto=0.048, size=60, z=54)
    p.cifra('285,360,000', t_285 + 0.10, K[6] + 0.25, fy=0.330, alto=0.105, size=132)
    p.card('BARRELS', t_barrels1 + 0.10, K[6] + 0.25, fy=0.430, alto=0.042, size=56, z=60)
    p.card('WEEK OF SEPT 4', t_sept + 0.15, K[6] + 0.25, fy=0.510, alto=0.046, size=54, z=54)
    p.rotulo('BUILT TO HOLD', K[6] + 0.30, K[7] - 0.10)
    p.cifra('727,000,000', t_727 + 0.10, K[7] + 0.35, fy=0.700, alto=0.105, size=132,
            tcolor=PR.TINTA)

    p.figura('01_burocrata', K[7] + 0.20, K[8] - 0.20, sobre=(-94.80, 31.30), mira='Freeport',
             alto_rel=0.25, gestos=(K[7] + 1.9,))
    p.cifra('THIS IS HOW IT EMPTIED', t_empt - 0.25, K[8] + 0.25, fy=0.735, alto=0.058, size=72,
            tcolor=PR.TINTA)
    p.rotulo('THE RELEASE', K[8] + 0.35, K[9] - 0.10)
    p.cifra('11 MARCH', t_11 + 0.10, K[9] - 0.10, fy=0.700, alto=0.070, size=92)
    p.cifra('172,000,000 OUT', t_172 + 0.15, K[10] - 0.10, fy=0.320, alto=0.105, size=112)
    p.card('THE LARGEST EMERGENCY' + NL + 'RELEASE EVER AGREED', t_agreed - 0.90, K[10] + 0.30,
           fy=0.450, alto=0.078, size=52, z=54)

    # LA ANIMACION CENTRAL: el deposito se vacia mientras la flecha del precio sube. Las dos cosas
    # a la vez son el argumento entero — bajo el que tenia que subir y subio el que tenia que bajar.
    p.secuencia('tanque_n', K[10] + 0.15, K[11] - 0.25, 12, 0, 0.275, 0.400, 0.300, z=46,
                nombre='prop:deposito_oil')
    p.card('THE PRICE WENT UP', K[10] + 0.10, K[11] - 0.10, fy=0.175, alto=0.050, size=62, z=54)
    p.cifra('+17%', K[11] - 0.15, K[12] - 0.10, fy=0.640, alto=0.120, size=180)

    p.cifra('5 WEEKS', t_5w + 0.05, K[13] - 0.10, fy=0.180, alto=0.060, size=84, tcolor=PR.TINTA)
    p.cifra('-19,000,000', t_19 + 0.10, K[13] + 0.30, fy=0.320, alto=0.110, size=132)
    p.cifra('$104.61', t_61 - 0.55, K[14] + 0.35, fy=0.660, alto=0.110, size=150)
    p.rotulo('BRENT, LAST WEEK', t_brent + 0.20, K[14] - 0.10)

    p.cifra('A RESERVE EXISTS' + NL + 'FOR EXACTLY ONE DAY', t_oneday - 0.85, K[15] + 0.25,
            fy=0.730, alto=0.090, size=62, tcolor=PR.TINTA)
    p.rotulo('THE DAY THE OIL STOPS', K[15] + 0.35, K[16] - 0.10)
    p.cifra('THE STRAIT' + NL + 'OF HORMUZ', t_hormuz - 0.55, K[16] + 0.35, fy=0.735, alto=0.105,
            size=90)

    p.secuencia('tanque_n', K[16] + 0.15, K[16] + 1.70, 0, 5, 0.500, 0.400, 0.320, z=46,
                nombre='prop:deposito_oil')
    p.cifra('39%', K[16] + 1.55, K[17] + 0.20, fy=0.690, alto=0.125, size=200)
    p.card('SOMEBODY IS' + NL + 'MAKING MONEY ON THIS', t_money - 0.55, K[18] + 0.05, fy=0.700,
           alto=0.086, size=58, tcolor=ROJO, z=56)
    p.card('SHOULD A COUNTRY SPEND' + NL + 'ITS RESERVE TO MOVE A PRICE?', K[18] + 0.02,
           D - 0.10, fy=0.330, alto=0.098, size=54, z=58, entra=0.14)
    p.card('COMMENTS', t_com - 0.30, D - 0.10, fy=0.460, alto=0.046, size=60, tcolor=ROJO, z=58)

    p.subtitulos(['thirty-nine', 'percent', 'Reagan', 'eighty-five', 'million', 'seven',
                  'twenty-seven', 'seventy-two', 'went', 'up', 'seventeen', 'nineteen',
                  'sixty-one', 'one', 'day.', 'Hormuz', 'money'])


# ===================================================================== PIEZA 2 · HORMUZ
def pieza_2(p):
    """THE CHEAPEST WEAPON — Hormuz no esta cerrado por la fuerza, esta cerrado por el seguro."""
    P_ = p.P
    HZ, BA, FU, RT, KW, DO, MU = (P_('Hormuz'), P_('Bandar Abbas'), P_('Fujairah'),
                                  P_('Ras Tanura'), P_('Kuwait City'), P_('Doha'), P_('Muscat'))
    Z = p.zmin
    D = p.dur
    MED = ((RT[0] + HZ[0]) / 2, (RT[1] + HZ[1]) / 2)

    t_hz1 = p.t('hormuz')
    t_95 = p.t('ninetyfive', desde=t_hz1)
    t_pct1 = p.t('percent', desde=t_95)
    t_3600 = p.t('three', desde=t_pct1)
    t_pct2 = p.t('percent', desde=t_3600 + 0.6)
    t_100 = p.t('hundred', desde=t_pct2)
    t_ships1 = p.t('ships', desde=t_100)
    t_ten = p.t('ten', desde=p.L(1)[1] - 1.2)
    t_short = p.t('shortage', desde=t_ten)
    t_oil = p.t('oil', desde=t_short)
    t_ships2 = p.t('ships', desde=t_oil)
    t_willing = p.t('willing', desde=t_ships2)
    t_mech = p.t('mechanism', desde=t_willing)
    t_ins = p.t('insurance', desde=t_mech)
    t_err = p.t('error', desde=t_ins)
    t_75 = p.t('seven', desde=t_err)
    t_hull = p.t('hull', desde=t_75)
    t_21 = p.t('twentyone', desde=t_hull)
    t_voy = p.t('voyage', desde=t_21)
    t_owner = p.t('owner', desde=t_voy)
    t_risk = p.t('risk', desde=t_owner)
    t_fund = p.t('fund', desde=t_risk)
    t_36 = p.t('thirtysix', desde=t_fund)
    t_brent = p.t('brent', desde=t_36)
    t_iran = p.t('iran', desde=t_brent)
    t_sink = p.t('sink', desde=t_iran)
    t_unins = p.t('uninsurable', desde=t_sink)
    t_paper = p.t('paper', desde=t_unins)
    t_com = p.t('comments', desde=t_paper)

    C = p.mu.meta['capas']
    p.mu.add_layer(C['golfo'], 0.6, 1.5, mode='fade')
    p.mu.add_layer(C['iran'], t_iran + 0.10, 1.2, mode='fade')
    p.mu.add_layer(C['marcas'], 0.6, 0.3, mode='fade')
    # la ruta de los petroleros: Ras Tanura -> Hormuz -> Golfo de Oman, por agua dibujada
    # Puntos sacados de la mascara de agua del propio mundo, no a ojo: sale de Ras Tanura, baja por
    # el centro del Golfo, pasa por el estrecho y sigue al Golfo de Oman. La primera version cruzaba
    # Qatar y los EAU por tierra (40 % de agua) y el verificador la rechazo, que es para lo que esta.
    p.ruta([(50.1580, 26.6927), (50.8000, 26.5000), (52.2000, 26.5000), (53.8000, 26.5000),
            (55.2000, 26.5000), (56.6000, 26.7000), (57.5000, 25.5000), (58.2000, 25.0000)],
           1.1, 8.5, color=MV.OCRE, width=9, dotted=True, verificar='agua', tol=0.90)

    K = [0.0,
         t_hz1 + 0.80,          # 1 -> 2   cierra sobre el estrecho
         t_pct1 + 0.70,         # 2 -> 3   abre: el fondo
         t_pct2 + 0.75,         # 3 -> 4   cierra: los cien barcos
         t_ships1 + 1.40,       # 4 -> 5   abre: se apagan
         p.L(2)[0] - 0.05,      # 5 -> 6   cierra sobre Ras Tanura
         t_oil + 0.80,          # 6 -> 7   abre: no es escasez de petroleo
         p.L(3)[0] - 0.05,      # 7 -> 8   MESA: la poliza
         t_err + 0.80,          # 8 -> 9   MESA (misma poliza, otro encuadre de cifra)
         t_hull + 0.75,         # 9 -> 10  MAPA cerrado: 3-21 M
         p.L(4)[0] - 0.05,      # 10 -> 11 MAPA abierto: el ejecutivo
         t_risk + 0.60,         # 11 -> 12 MAPA: el fondo sube
         t_36 + 1.10,           # 12 -> 13 MAPA cerrado: Brent
         p.L(5)[0] - 0.05,      # 13 -> 14 MAPA: Iran se pinta
         t_unins - 1.60,        # 14 -> 15 MAPA cerrado: UNINSURABLE (el plano 14 se pasaba de 6 s)
         p.L(6)[0] - 0.05,      # 15 -> 16 MESA: el papel
         D]

    PLAN = [
        ('mapa', (MED[0] - 40, MED[1] + 120), Z + 0.02, (MED[0] + 60, MED[1] + 40), Z + 0.30),
        ('mapa', (HZ[0] - 140, HZ[1] - 540), Z + 0.95, (HZ[0] - 40, HZ[1] - 20), Z + 1.45),
        ('mapa', (MED[0] + 90, MED[1] + 180), Z + 0.04, (MED[0] - 70, MED[1] - 40), Z + 0.34),
        ('mapa', (HZ[0] - 110, HZ[1] + 110), Z + 0.50, (HZ[0] + 40, HZ[1] - 30), Z + 0.92),
        ('mapa', (MED[0] - 60, MED[1] + 150), Z + 0.02, (HZ[0] - 30, HZ[1] + 60), Z + 0.32),
        ('mapa', (RT[0] + 120, RT[1] + 110), Z + 0.52, (RT[0] - 40, RT[1] - 20), Z + 0.94),
        ('mapa', (MED[0] + 70, MED[1] + 160), Z + 0.04, (MED[0] - 60, MED[1] - 30), Z + 0.34),
        ('mesa', (MED[0] - 50, MED[1] + 40), 1.04, (MED[0] + 60, MED[1] - 40), 1.716),
        ('mesa', (MED[0] + 60, MED[1] - 40), 1.10, (MED[0] - 50, MED[1] + 50), 1.815),
        ('mapa', (HZ[0] + 60, HZ[1] + 130), Z + 0.56, (HZ[0] - 50, HZ[1] - 10), Z + 0.98),
        ('mapa', (1620, 1520), Z + 0.06, (1760, 1400), Z + 0.38),          # 11 · el ejecutivo
        ('mapa', (MU[0] - 140, MU[1] - 160), Z + 0.48, (FU[0] + 40, FU[1] + 30), Z + 0.90),
        ('mapa', (MED[0] - 40, MED[1] + 170), Z + 0.02, (RT[0] + 60, RT[1] + 80), Z + 0.32),
        ('mapa', (BA[0] + 110, BA[1] + 120), Z + 0.52, (BA[0] - 30, BA[1] - 20), Z + 0.94),
        ('mesa', (MED[0] + 50, MED[1] + 140), 1.04, (HZ[0] - 40, HZ[1] + 40), 1.716),
        ('mesa', (MED[0] + 50, MED[1] - 30), 1.06, (MED[0] - 50, MED[1] + 40), 1.749),
    ]
    for i, (tipo, c0, z0, c1, z1) in enumerate(PLAN):
        p.plano(K[i], K[i + 1], c0, z0, c1, z1, tipo)

    p.mesa(K[7], K[8], 'poliza', fy=0.400, alto=0.460)
    p.mesa(K[8], K[9], 'factura', fy=0.400, alto=0.450,
           escritorio=[('lupa', 0.130, 0.820, 0.078), ('moneda', 0.888, 0.848, 0.042)])
    p.mesa(K[14], K[15], None, oscuro=0.62, escritorio=[('lupa', 0.130, 0.820, 0.078)])
    p.mesa(K[15], D, 'poliza', fy=0.400, alto=0.480)

    p.rotulo('THE STRAIT OF HORMUZ', 0.85, K[1] - 0.10)
    p.cifra('ALMOST NOTHING' + NL + 'HAS BEEN SUNK', 0.10, K[1] + 1.55, fy=0.640, alto=0.090,
            size=62, tcolor=PR.TINTA)
    p.cifra('-95%', t_95 + 0.10, K[2] + 2.30, fy=0.300, alto=0.130, size=190)
    p.card('TRAFFIC THROUGH IT', t_95 + 0.55, K[2] + 2.30, fy=0.425, alto=0.042, size=56, z=60)
    p.cifra('+3,600%', t_3600 + 0.20, K[3] + 0.25, fy=0.300, alto=0.125, size=175)
    p.card('ONE SHIPPING FUND', t_3600 + 0.60, K[3] + 0.25, fy=0.420, alto=0.044, size=56, z=60)

    # LOS DOCE PETROLEROS: cruzan en fila y se apagan de izquierda a derecha hasta quedar UNO.
    # El estrecho no se cierra con fuego: se cierra con una cifra que sube.
    for i in range(12):
        x = 0.115 + i * 0.0705
        p.prop('petrolero', K[3] + 0.20 + i * 0.09, K[4] + 0.30 + i * 0.24, x, 0.245, 0.030,
               z=44, entra=0.14, sale=0.12, sfx=None, nombre='prop:petrolero%d' % i)
    p.cifra('100+ SHIPS A DAY', t_100 - 0.30, K[4] + 0.30, fy=0.150, alto=0.058, size=76,
            tcolor=PR.TINTA)
    p.prop('petrolero', K[4] + 0.35, K[6] - 0.10, 0.500, 0.245, 0.042, z=45, entra=0.20,
           nombre='prop:petrolero_ultimo')
    p.cifra('NOW: 10 A DAY', t_ten + 0.10, K[5] + 0.25, fy=0.330, alto=0.095, size=104)

    p.prop('barril', K[5] + 0.05, K[6] - 0.10, 0.500, 0.450, 0.165, z=46, entra=0.14, sfx='stamp')
    p.cifra('NOT A SHORTAGE OF OIL', t_short + 0.20, K[6] + 1.35, fy=0.640, alto=0.058, size=70,
            tcolor=PR.TINTA)
    p.cifra('A SHORTAGE OF SHIPS' + NL + 'WILLING TO GO', t_ships2 + 0.15, K[7] + 0.35,
            fy=0.320, alto=0.090, size=62)
    p.rotulo('HERE IS THE MECHANISM', t_mech - 0.25, K[7] - 0.10)

    p.rotulo('WAR-RISK INSURANCE', K[7] + 0.25, K[8] - 0.10)
    p.card('USED TO BE' + NL + 'A ROUNDING ERROR', t_err - 0.75, K[8] + 0.25, fy=0.740,
           alto=0.080, size=58, z=54)
    p.cifra('7.5% - 10%', t_75 + 0.10, K[9] + 0.25, fy=0.700, alto=0.105, size=150)
    p.card('OF THE VALUE OF THE HULL', t_hull + 0.10, K[9] + 0.25, fy=0.800, alto=0.044, size=54,
           z=60)
    p.cifra('$3M - $21M', t_21 - 0.40, K[10] + 0.05, fy=0.330, alto=0.110, size=150)
    p.card('PER SINGLE VOYAGE', t_voy + 0.10, K[10] + 0.05, fy=0.440, alto=0.044, size=56, z=60)

    p.figura('03_ejecutivo', K[10] + 0.20, K[11] - 0.20, sobre=(55.90, 24.60), mira='Hormuz',
             alto_rel=0.25, gestos=(K[10] + 2.0,))
    p.card('THE OWNER CHARGES' + NL + 'FOR THE RISK', K[10] + 0.08, K[11] + 0.25, fy=0.760,
           alto=0.082, size=58, z=56)
    p.prop('flecha_arriba', K[11] + 0.10, K[12] - 0.10, 0.760, 0.420, 0.190, z=46, entra=0.35)
    p.card('THE COST OF MOVING' + NL + 'OIL BY SEA', t_fund + 0.20, K[12] - 0.10, fy=0.185,
           alto=0.078, size=56, z=54)
    p.cifra('36x SINCE' + NL + 'JANUARY', t_36 + 0.10, K[12] + 0.25, fy=0.660, alto=0.115,
            size=110)
    p.prop('barril', K[12] + 0.05, K[13] + 3.55, 0.290, 0.430, 0.150, z=46, entra=0.14,
           sfx='stamp')
    p.cifra('$104', t_brent + 0.55, K[13] + 3.55, fy=0.660, alto=0.110, size=170)
    p.rotulo('BRENT', t_brent + 0.20, K[13] + 3.55)

    p.prop('bandera_ir', t_iran + 0.25, K[14] + 0.05, 0.500, 0.235, 0.085, z=46, entra=0.16)
    p.cifra('DID NOT HAVE TO' + NL + 'SINK THE TANKERS', t_sink - 0.25, K[14] + 0.05, fy=0.680,
            alto=0.090, size=62, tcolor=PR.TINTA)
    p.cifra('IT ONLY HAD TO' + NL + 'MAKE THEM...', K[14] + 0.08, K[15] + 0.30, fy=0.640,
            alto=0.090, size=62, tcolor=PR.TINTA)
    p.cifra('UNINSURABLE', t_unins + 0.10, K[15] + 0.30, fy=0.330, alto=0.105, size=132)
    p.prop('sello_no', t_unins + 0.50, K[15] + 0.30, 0.500, 0.480, 0.105, z=52, sfx='stamp',
           entra=0.14)
    p.cifra('A PIECE OF PAPER', t_paper - 0.60, D - 0.10, fy=0.730, alto=0.098, size=104)
    p.card('COMMENTS', t_com - 0.30, D - 0.10, fy=0.845, alto=0.046, size=60, tcolor=ROJO, z=58)

    p.subtitulos(['ninety-five', 'percent', 'nothing', 'hundred', 'ten.', 'willing',
                  'rounding', 'error.', 'seven', 'ten', 'twenty-one', 'thirty-six',
                  'uninsurable.', 'paper.'])


# ===================================================================== PIEZA 3 · LOS HOTELES
def pieza_3(p):
    """EIGHT MILLION A DAY — el recibo del alojamiento de asilo britanico.

    REGLA 13: el sujeto es EL CONTRATO y EL DEPARTAMENTO. Ni una tarjeta pone a un colectivo de
    personas como sujeto: se habla de contratos, de cuentas y de coste por noche."""
    P_ = p.P
    LO, MA, BI, GL = P_('London'), P_('Manchester'), P_('Birmingham'), P_('Glasgow')
    Z = p.zmin
    D = p.dur
    MED = ((LO[0] + MA[0]) / 2, (LO[1] + MA[1]) / 2)
    MAR = (LO[0] + 620, LO[1] - 260)             # el Mar del Norte: encuadre de otro tono

    t_sec = p.t('secretary')
    t_hotels = p.t('hotels', desde=t_sec)
    t_six = p.t('six', desde=t_hotels)
    t_acc1 = p.t('accounts', desde=t_six)
    t_eight1 = p.t('eight', desde=t_acc1)
    t_eight2 = p.t('eight', desde=t_eight1 + 0.8)
    t_est = p.t('newspaper', desde=t_eight2)
    t_acc2 = p.t('accounts', desde=t_est)
    t_worse = p.t('worse', desde=t_acc2)
    t_2019 = p.t('twentynineteen', desde=t_worse)
    t_45 = p.t('billion', desde=t_2019)
    t_tenyears = p.t('ten', desde=t_45)
    t_153 = p.t('fifteen', desde=t_tenyears)
    t_same = p.t('same', desde=t_153)
    t_3x = p.t('three', desde=t_same + 1.5)
    t_money = p.t('money', desde=t_3x)
    t_76 = p.t('seventysix', desde=t_money)
    t_p76 = p.t('percent', desde=t_76)
    t_35 = p.t('thirtyfive', desde=t_p76)
    t_p35 = p.t('percent', desde=t_35)
    t_cheap = p.t('cheaper', desde=t_p35)
    t_42 = p.t('four', desde=t_cheap)
    t_107 = p.t('hundred', desde=t_42 + 2.0)
    t_person = p.t('person', desde=t_107)
    t_argue = p.t('argue', desde=t_person)
    t_notthat = p.t('not', desde=t_argue + 2.0)
    t_proc = p.t('procurement', desde=t_notthat)
    t_night = p.t('night', desde=t_proc)
    t_com = p.t('comments', desde=t_night)

    C = p.mu.meta['capas']
    p.mu.add_layer(C['gbr'], 0.6, 1.5, mode='fade')
    p.mu.add_layer(C['irl'], 0.6, 1.5, mode='fade')
    p.mu.add_layer(C['marcas'], 0.6, 0.3, mode='fade')

    K = [0.0,
         t_sec + 0.85,          # 1 -> 2   cierra sobre los hoteles (el plano 1 daba 7,1 s)
         t_six + 1.70,          # 2 -> 3   abre: el burocrata
         p.L(1)[0] - 0.05,      # 3 -> 4   MESA: las cuentas
         t_est + 1.00,          # 4 -> 5   MAPA cerrado: la cifra
         p.L(2)[0] - 0.05,      # 5 -> 6   MESA: el contrato
         t_45 - 0.55,           # 6 -> 7   MESA: la torre crece (el plano 6 daba 7,1 s)
         t_153 + 1.30,          # 7 -> 8   MAPA abierto: el sello
         p.L(3)[0] + 1.60,      # 8 -> 9   MESA: tres veces la cuenta
         t_3x + 1.30,           # 9 -> 10  MAPA cerrado: las barras (el plano 8 daba 7,2 s)
         t_p76 + 1.20,          # 10 -> 11 MAPA abierto: la segunda barra
         t_p35 + 1.30,          # 11 -> 12 MAPA cerrado: mas barato
         p.L(5)[0] - 0.05,      # 12 -> 13 MESA: la factura
         t_107 - 0.55,          # 13 -> 14 MESA -> MAPA: 107 por noche
         p.L(6)[0] - 0.05,      # 14 -> 15 MAPA abierto: el argumento
         t_notthat - 0.45,      # 15 -> 16 MAPA cerrado: no es ese argumento
         p.L(7)[0] - 0.45,      # 16 -> 17 MAPA: el cierre
         D]

    PLAN = [
        ('mapa', (MED[0] - 40, MED[1] - 320), Z + 0.02, (LO[0] + 30, LO[1] - 60), Z + 0.30),
        ('mapa', (LO[0] - 110, LO[1] + 120), Z + 0.92, (LO[0] + 40, LO[1] - 30), Z + 1.40),
        ('mapa', (1300, 1900), Z + 0.06, (1420, 1780), Z + 0.38),          # 3 · el burocrata
        ('mesa', (MED[0] - 50, MED[1] + 40), 1.02, (MED[0] + 60, MED[1] - 40), 1.683),
        ('mapa', (BI[0] + 90, BI[1] + 110), Z + 0.52, (BI[0] - 50, BI[1] - 20), Z + 0.94),
        ('mesa', (MED[0] + 60, MED[1] - 40), 1.08, (MED[0] - 50, MED[1] + 50), 1.782),
        ('mesa', (MED[0] - 60, MED[1] + 50), 1.12, (MED[0] + 50, MED[1] - 40), 1.848),
        ('mapa', (MAR[0] - 60, MAR[1] + 40), Z + 0.04, (MED[0] + 40, MED[1] + 120), Z + 0.34),
        ('mesa', (MED[0] - 60, MED[1] + 40), 1.06, (MED[0] + 50, MED[1] - 40), 1.749),
        ('mapa', (LO[0] - 110, LO[1] + 100), Z + 0.50, (LO[0] + 40, LO[1] - 40), Z + 0.92),
        ('mesa', (MAR[0] + 40, MAR[1] - 60), 1.04, (MED[0] - 40, MED[1] + 160), 1.716),
        ('mapa', (MA[0] - 70, MA[1] + 110), Z + 0.95, (MA[0] + 50, MA[1] - 20), Z + 1.42),
        ('mesa', (MED[0] + 50, MED[1] - 40), 1.04, (MED[0] - 60, MED[1] + 50), 1.716),
        ('mapa', (LO[0] + 80, LO[1] + 120), Z + 0.52, (LO[0] - 40, LO[1] - 20), Z + 0.94),
        ('mapa', (MAR[0] - 40, MAR[1] + 80), Z + 0.02, (MED[0] + 60, MED[1] - 120), Z + 0.30),
        ('mapa', (GL[0] + 60, GL[1] + 130), Z + 0.48, (GL[0] - 50, GL[1] + 10), Z + 0.88),
        ('mapa', (MED[0] - 60, MED[1] + 60), Z + 0.26, (MAR[0] + 40, MAR[1] + 180), Z + 0.02),
    ]
    for i, (tipo, c0, z0, c1, z1) in enumerate(PLAN):
        p.plano(K[i], K[i + 1], c0, z0, c1, z1, tipo)

    p.mesa(K[3], K[4], 'libro_mayor', fy=0.400, alto=0.460)
    p.mesa(K[5], K[6], 'contrato99', fy=0.395, alto=0.440)
    p.mesa(K[6], K[7], 'libro_mayor', fy=0.400, alto=0.455,
           escritorio=[('lupa', 0.130, 0.820, 0.078), ('moneda', 0.888, 0.848, 0.042)])
    p.mesa(K[8], K[9], 'contrato99', fy=0.395, alto=0.440,
           escritorio=[('regla', 0.858, 0.150, 0.022)])
    p.mesa(K[10], K[11], None, oscuro=0.60, escritorio=[('lupa', 0.130, 0.820, 0.078)])
    p.mesa(K[12], K[13], 'factura', fy=0.400, alto=0.450)

    p.rotulo('ASYLUM ACCOMMODATION', 0.85, K[1] - 0.10)
    p.cifra('THE DAY BEFORE', 0.10, K[1] + 0.30, fy=0.640, alto=0.062, size=88, tcolor=PR.TINTA)
    for i, (fx, dt) in enumerate(((0.235, 0.00), (0.500, 0.30), (0.765, 0.60))):
        p.prop('hotel', t_hotels - 0.85 + dt, K[2] + 0.25, fx, 0.360, 0.125, z=46, entra=0.16,
               sfx=None, nombre='prop:hotel%d' % i)
    p.card('THE HOME SECRETARY SAID', t_sec + 0.15, K[2] + 0.25, fy=0.560, alto=0.048, size=58,
           z=54)
    p.cifra('GBP 6M A DAY', t_six + 0.10, K[2] + 0.25, fy=0.660, alto=0.105, size=140,
            tcolor=PR.TINTA)
    p.figura('01_burocrata', K[2] + 0.20, K[3] - 0.20, sobre=(-1.45, 52.25), mira='London',
             alto_rel=0.24, gestos=(K[2] + 2.0,))
    p.cifra('THE ACCOUNTS SAID', t_acc1 - 0.30, K[3] + 0.25, fy=0.735, alto=0.058, size=72)

    # LA CIFRA CRUZA EL CORTE: entra sobre el mapa y sigue viva sobre el libro mayor
    p.cifra('GBP 8M A DAY', t_eight1 - 0.15, K[5] + 0.35, fy=0.300, alto=0.120, size=150)
    p.rotulo('HOME OFFICE · ANNUAL ACCOUNTS', K[3] + 0.30, K[4] - 0.10)
    p.card('NOT A NEWSPAPER ESTIMATE', t_est + 0.10, K[4] + 0.25, fy=0.430, alto=0.046, size=56,
           z=54)
    p.card('IN THE DEPARTMENT’S' + NL + 'OWN ACCOUNTS', t_acc2 - 1.00, K[5] + 0.35, fy=0.560,
           alto=0.078, size=56, z=54)
    p.cifra('AND A WORSE NUMBER', t_worse + 0.10, K[5] + 0.25, fy=0.175, alto=0.058, size=72)

    p.rotulo('CONTRACTS SIGNED · 2019', t_2019 - 0.55, K[7] - 0.10)
    # la torre crece: 4,5 bn -> 15,3 bn. El mismo contrato, tres veces la cuenta.
    p.secuencia('torre_n', K[5] + 0.25, t_45 - 0.20, 0, 5, 0.500, 0.395, 0.290, z=46,
                nombre='prop:torre_n')
    p.cifra('GBP 4.5bn', t_45 - 0.45, K[6] + 0.25, fy=0.665, alto=0.105, size=155,
            tcolor=PR.TINTA)
    p.card('OVER TEN YEARS', t_tenyears + 0.10, K[6] + 0.25, fy=0.775, alto=0.042, size=54, z=60)
    p.secuencia('torre_n', K[6] + 0.25, t_153 - 0.20, 5, 12, 0.500, 0.395, 0.290, z=46,
                nombre='prop:torre_n')
    p.cifra('GBP 15.3bn', t_153 + 0.10, K[7] + 0.25, fy=0.665, alto=0.110, size=155)
    p.card('THE SAME CONTRACTS' + NL + 'THE SAME TEN YEARS', t_same + 0.10, K[8] + 0.25,
           fy=0.790, alto=0.078, size=54, z=54)
    p.prop('sello_same', K[7] + 0.10, K[8] + 0.25, 0.500, 0.235, 0.105, z=52, sfx='stamp',
           entra=0.14)
    p.cifra('MORE THAN 3x THE BILL', t_3x + 0.10, K[9] + 0.35, fy=0.700, alto=0.078, size=76)

    p.rotulo('WHERE THE MONEY GOES', t_money - 0.20, K[10] - 0.10)
    # DOS BARRAS QUE NO COINCIDEN: la distancia entre las dos puntas es la pieza entera
    p.secuencia('barra_d', K[9] + 0.20, t_76 - 0.15, 0, 12, 0.500, 0.330, 0.085, z=46,
                nombre='prop:barra_dinero', hold_final=0.60)
    p.cifra('76%', t_76 + 0.10, K[11] - 0.10, fy=0.445, alto=0.100, size=160)
    p.card('OF THE MONEY', t_p76 + 0.10, K[11] - 0.10, fy=0.545, alto=0.040, size=54, z=60)
    p.secuencia('barra_g', K[10] + 0.20, t_35 - 0.15, 0, 4, 0.500, 0.650, 0.085, z=46,
                nombre='prop:barra_gente')
    p.cifra('35%', t_35 + 0.10, K[12] + 0.35, fy=0.730, alto=0.100, size=160)
    p.card('OF THE PEOPLE IN IT', t_p35 + 0.10, K[12] + 0.35, fy=0.830, alto=0.040, size=54,
           z=60)
    p.cifra('HOUSED CHEAPER', t_cheap - 0.45, K[12] + 0.25, fy=0.180, alto=0.058, size=76,
            tcolor=PR.TINTA)

    p.rotulo('YEAR TO MARCH', K[12] + 0.30, K[13] - 0.10)
    p.cifra('GBP 4.2 BILLION', t_42 + 0.10, K[13] + 0.80, fy=0.700, alto=0.105, size=140)
    p.cifra('GBP 107', t_107 + 0.10, K[14] + 0.05, fy=0.330, alto=0.115, size=185)
    p.card('PER PERSON, PER NIGHT', t_person + 0.10, K[14] + 0.05, fy=0.440, alto=0.044, size=56,
           z=60)

    p.card('YOU CAN ARGUE ABOUT' + NL + 'HOW MANY SHOULD COME', K[14] + 0.08, K[15] + 0.25,
           fy=0.180, alto=0.082, size=56, z=54)
    p.cifra('THIS IS NOT' + NL + 'THAT ARGUMENT', t_notthat - 0.20, K[16] + 0.25, fy=0.330,
            alto=0.105, size=104, tcolor=PR.TINTA)
    p.card('A PROCUREMENT FAILURE', t_proc + 0.10, K[16] + 1.40, fy=0.475, alto=0.048, size=60,
           z=58)
    p.cifra('A PRICE PER NIGHT', t_night - 0.35, D - 0.10, fy=0.330, alto=0.098, size=96)
    p.card('WHO PAYS?', K[16] + 0.60, D - 0.10, fy=0.455, alto=0.058, size=76, tcolor=PR.TINTA,
           z=58)
    p.card('COMMENTS', t_com - 0.30, D - 0.10, fy=0.560, alto=0.046, size=60, tcolor=ROJO, z=58)

    p.subtitulos(['six', 'eight.', 'eight', 'accounts.', 'accounts', 'twenty-nineteen',
                  'billion', 'fifteen', 'three', 'times', 'seventy-six', 'percent',
                  'thirty-five', 'cheaper.', 'hundred', 'seven', 'night.'])


PARTITURA = {1: pieza_1, 2: pieza_2, 3: pieza_3, 4: pieza_4}
