# -*- coding: utf-8 -*-
"""Ep. 13 · la partitura: que se ve en cada linea. El motor y los helpers estan en `coreo13.py`.

Una funcion por beat. Cada una recibe la batuta `d` y usa:
    d.L(beat, linea) -> (t0, t1) de esa linea de voz
    d.B(beat)        -> (t0, t1) del beat entero
    d.t('palabra')   -> el instante EXACTO en que la voz dice esa palabra
    d.P('Perim')     -> px de mundo del sitio (regla 24: sale de lon/lat, nada a ojo)

Reglas que se respetan aqui y que conviene no relajar:
  - **Cada linea tiene algo encima del mapa.** El mundo es `bg` y NO cuenta como contenido (§7 del
    motor v4): si una linea se queda solo con el mapa, `sync.py` la marca VACIO y el render aborta.
  - **Ningun plano de mas de 6 s sin cambio** (`ritmo.py`). Las lineas largas se parten en dos planos.
  - **Dos planos de mapa seguidos con zoom y centro parecidos no se leen como corte**: hay que
    alternar escala (regional <-> estrecho) o meter un plano de mesa.

Zoom, medido sobre este mundo (9000x7697, 333 px/grado, zmin = 0,213):
    0,25 = la region entera (las dos puertas)   ·   0,55 = el Mar Rojo
    1,20 = Yemen                                 ·   2,60 = el estrecho
"""
import motor as M
import props as PR

REG, MARROJO, YEMEN, ESTRECHO = 0.26, 0.58, 1.15, 1.90


def escribir(d):
    b00(d); b01(d); b02(d); b03(d); b04(d)
    d.acto('ACT I', 'The Gate', d.t_['actos'][0]['t0']);      b05(d)
    d.acto('ACT II', 'Who They Are', d.t_['actos'][1]['t0']); b06(d)
    d.acto('ACT III', 'Eleven Years', d.t_['actos'][2]['t0']); b07(d)
    d.acto('ACT IV', 'The Pincer', d.t_['actos'][3]['t0']);   b08(d)
    d.acto('ACT V', 'The Receipt', d.t_['actos'][4]['t0']);   b09(d)
    b10(d); b11(d)


# ====================================================================== 00 · preguntas
def b00(d):
    t0, t1 = d.B(0)
    a = d.L(0, 0); b = d.L(0, 1); c = d.L(0, 2); e = d.L(0, 3)
    # el gancho va sobre el MAPA en movimiento, no sobre una hoja quieta
    d.plano(t0, b[1], 'Hormuz', 0.42, 'Bab el-Mandeb', REG + 0.05)
    d.card('WHO CLOSED' + chr(10) + 'THE RED SEA?', a[0], a[1] + 0.3, fy=0.40, alto=0.175, size=112,
           tcolor=PR.ROJO)
    d.card('FROM A VILLAGE' + chr(10) + 'TO A STRAIT?', b[0], b[1] + 0.3, fy=0.40, alto=0.155, size=100)
    d.plano(c[0], e[1], 'Bab el-Mandeb', YEMEN * 0.7, 'Sanaa', YEMEN)
    d.card('ELEVEN YEARS' + chr(10) + 'OF BOMBING?', c[0], c[1] + 0.3, fy=0.38, alto=0.155, size=100)
    d.card('STAY TO THE END', e[0], e[1] + 0.4, fy=0.42, alto=0.075, size=62, tcolor=PR.ROJO)
    d.card('PAPER TRAIL', e[0] + 0.5, e[1] + 0.4, fy=0.60, alto=0.040, size=44, sfx='stamp')


# ====================================================================== 01 · cold open
def b01(d):
    L = lambda i: d.L(1, i)
    a, b, c, e, f, g = L(0), L(1), L(2), L(3), L(4), L(5)
    # la isla, vacia
    d.plano(a[0], b[1], 'Perim', ESTRECHO * 0.75, 'Perim', ESTRECHO)
    d.prop('fusil', a[0] + 0.2, a[1], 0.44, 0.45, 0.105)
    d.prop('fusil', a[0] + 0.5, a[1], 0.52, 0.47, 0.095)
    d.card('10 SEP', a[0] + 0.3, a[1], fx=0.845, fy=0.155, alto=0.050, size=54, tcolor=PR.ROJO)
    d.prop('barco_vela', b[0], b[1], 0.60, 0.52, 0.11)
    d.sello('NO BATTLE', b[0] + 1.0, b[1], fx=0.30, fy=0.34, alto=0.085, size=52)
    # la ficha de la isla
    d.plano(c[0], e[1], 'Perim', ESTRECHO, 'Perim', ESTRECHO * 1.25)
    d.card('PERIM' + chr(10) + '13 km2', c[0], e[1], fx=0.255, fy=0.40, alto=0.135, size=84)
    d.prop('faro', c[0] + 0.6, e[1], 0.63, 0.40, 0.145)          # el faro
    for i, (p, fx) in enumerate((('gota', 0.36), ('arbol', 0.50), ('casa', 0.64))):
        o = d.prop(p, e[0] + 0.25 * i, e[1], fx, 0.66, 0.072)
        d.sello('X', e[0] + 0.25 * i + 0.45, e[1], fx=fx, fy=0.66, alto=0.045, size=34)
    # una de cada veinte
    d.plano(f[0], f[1], 'Bab el-Mandeb', ESTRECHO * 0.8, 'Bab el-Mandeb', ESTRECHO * 1.1)
    d.cifra('1 IN 20', f[0] + 0.4, f[1], fx=0.50, fy=0.30, alto=0.150, size=170)
    d.prop('barril', f[0] + 0.8, f[1], 0.50, 0.60, 0.13)
    d.plano(g[0], g[1], 'Perim', ESTRECHO * 1.1, 'Perim', ESTRECHO * 1.4)
    d.card('A DIFFERENT FLAG', g[0] + 0.2, g[1], fy=0.36, alto=0.070, size=64, tcolor=PR.ROJO)


# ====================================================================== 02 · hook · LAS DOS PUERTAS
def b02(d):
    L = lambda i: d.L(2, i)
    a, b, c, e, f, g, h, i2 = L(0), L(1), L(2), L(3), L(4), L(5), L(6), L(7)
    d.mu.add_layer(d.mu.meta['capas']['sau'], a[0] + 0.4, 1.4, t_off=b[1], dur_off=1.0)
    d.plano(a[0], a[1], 'Abqaiq', REG * 1.5, 'Abqaiq', REG * 1.8)
    d.prop('torre_petroleo', a[0] + 0.3, b[1], 0.50, 0.44, 0.17)
    d.card('TWO DOORS', a[0] + 1.0, a[1], fy=0.75, alto=0.070, size=60, tcolor=PR.ROJO)
    # puerta 1: Ormuz
    d.plano(b[0], b[1], 'Hormuz', 0.75, 'Hormuz', 0.95)
    d.card('HORMUZ', b[0] + 0.2, b[1], fx=0.28, fy=0.22, alto=0.055, size=58)
    d.cifra('20.9 Mb/d', d.t(('twenty', '20'), b[0]), b[1], fx=0.50, fy=0.40, alto=0.140)
    d.card('A FIFTH OF ALL OIL', d.t('fifth', b[0]), b[1], fy=0.70, alto=0.055, size=52)
    # puerta 2: el Mar Rojo
    d.plano(c[0], e[1], 'Yanbu', MARROJO * 0.8, 'Bab el-Mandeb', MARROJO)
    d.card('RED SEA', c[0] + 0.3, c[1], fx=0.30, fy=0.20, alto=0.055, size=58)
    d.card('BAB EL-MANDEB', d.t('bab', c[0]), e[1], fx=0.62, fy=0.78, alto=0.052, size=54,
           tcolor=PR.ROJO)
    d.cifra('9.3 Mb/d', d.t(('nine', '9'), e[0] - 0.5), e[1], fx=0.32, fy=0.40, alto=0.140)
    d.card('2023', e[0] + 0.2, e[1], fx=0.32, fy=0.55, alto=0.045, size=48)
    # las dos se cierran
    d.plano(f[0], g[1], 'Riyadh', REG, 'Riyadh', REG * 1.12)
    d.prop('barrera', f[0] + 0.15, g[1], 0.24, 0.46, 0.13)
    d.prop('barrera', f[0] + 0.30, g[1], 0.76, 0.46, 0.13)
    d.sello('CLOSED', f[0] + 0.7, g[1], fx=0.24, fy=0.66, alto=0.075, size=46)
    d.sello('CLOSED', f[0] + 0.9, g[1], fx=0.76, fy=0.66, alto=0.075, size=46)
    d.card('MARCH: A GOVERNMENT', g[0] + 0.2, g[1], fy=0.20, alto=0.055, size=54)
    d.plano(h[0], i2[1], 'Bab el-Mandeb', YEMEN * 0.8, 'Bab el-Mandeb', YEMEN)
    d.card('SEPTEMBER: A MOVEMENT', h[0] + 0.2, h[1], fy=0.20, alto=0.055, size=54, tcolor=PR.ROJO)
    d.prop('fusil', h[0] + 0.6, h[1], 0.50, 0.46, 0.115)
    d.mesa(i2[0], i2[1], 'libro_mayor')


# ====================================================================== 03 · shape of the problem
def b03(d):
    L = lambda i: d.L(3, i)
    ls = [L(i) for i in range(10)]
    d.rotulo('THE GEOGRAPHY IS THE ARGUMENT', ls[0][0], ls[1][1])
    d.plano(ls[0][0], ls[1][1], 'Bab el-Mandeb', YEMEN, 'Bab el-Mandeb', ESTRECHO * 0.85)
    d.prop('lupa', ls[0][0] + 0.25, ls[0][1], 0.72, 0.42, 0.135)
    d.card('THE WHOLE ARGUMENT', ls[0][0] + 0.45, ls[0][1], fx=0.32, fy=0.34, alto=0.055, size=54)
    d.prop('regla_30', ls[1][0] + 0.2, ls[1][1], 0.50, 0.52, 0.035)
    d.cifra('30 km', d.t(('thirty', '30'), ls[1][0]), ls[1][1], fx=0.50, fy=0.33, alto=0.120, size=150)
    # Perim parte el canal
    d.plano(ls[2][0], ls[3][1], 'Perim', ESTRECHO * 2.45, 'Perim', ESTRECHO * 2.15)
    d.prop('isla', ls[2][0] + 0.2, ls[3][1], 0.50, 0.47, 0.085)
    d.card('TWO LANES', ls[2][0] + 0.8, ls[3][1], fx=0.24, fy=0.24, alto=0.055, size=56)
    d.prop('barco_vela', ls[3][0] + 0.2, ls[3][1], 0.30, 0.70, 0.085)
    d.prop('barco_vela', ls[3][0] + 0.5, ls[3][1], 0.70, 0.70, 0.085)
    # los numeros
    d.mesa(ls[4][0], ls[6][1], 'libro_mayor', alto=0.50)
    d.cifra('9.3', ls[4][0] + 0.5, ls[5][0] + 0.4, fx=0.33, fy=0.36, alto=0.185, size=220)
    d.cifra('4.1', d.t(('four', '4'), ls[5][0]), ls[6][1], fx=0.67, fy=0.36, alto=0.185, size=220)
    d.card('2023', ls[4][0] + 0.7, ls[5][0] + 0.4, fx=0.33, fy=0.53, alto=0.042, size=46)
    d.card('2024', d.t(('four', '4'), ls[5][0]) + 0.2, ls[6][1], fx=0.67, fy=0.53, alto=0.042, size=46)
    d.sello('ALREADY HALVED', ls[6][0] + 0.3, ls[6][1], fx=0.50, fy=0.72, alto=0.080, size=48)
    # y entonces cambia de manos
    d.plano(ls[7][0], ls[7][1], 'Mocha', ESTRECHO * 0.8, 'Perim', ESTRECHO * 1.1)
    for i, s in enumerate(('Mocha', 'Hanish Is.', 'Perim')):
        d.sello('TAKEN', ls[7][0] + 0.35 * i, ls[7][1], fx=0.28 + 0.22 * i, fy=0.30 + 0.12 * i,
                alto=0.058, size=38)
    d.plano(ls[8][0], ls[9][1], 'Bab el-Mandeb', ESTRECHO * 0.9, 'Suez', MARROJO * 0.62)
    d.cifra('30 - 15', ls[8][0] + 0.3, ls[8][1], fx=0.50, fy=0.30, alto=0.150, size=170)
    for i in range(4):
        d.prop('tanquero', ls[8][0] + 0.3 + 0.2 * i, ls[8][1] - 0.1 * i, 0.20 + 0.20 * i, 0.68, 0.062)
    d.card('EUROPE, VIA SUEZ', ls[9][0] + 0.2, ls[9][1], fy=0.22, alto=0.055, size=54)


# ====================================================================== 04 · who is lying
def b04(d):
    L = lambda i: d.L(4, i)
    ls = [L(i) for i in range(9)]
    d.rotulo('WHO IS LYING', ls[0][0], ls[4][1])
    d.mesa(ls[0][0], ls[4][1], 'recibo_usd', alto=0.46)
    d.cifra('500+', ls[1][0] + 0.3, ls[3][1], fx=0.26, fy=0.34, alto=0.130, size=160)
    d.card('SAYS THE GOVERNMENT SIDE', ls[1][0] + 0.6, ls[3][1], fx=0.26, fy=0.50, alto=0.038, size=40)
    d.cifra('1,000+', ls[2][0] + 0.3, ls[3][0] + 0.8, fx=0.74, fy=0.34, alto=0.130, size=160)
    d.card('SAYS THE SAME SIDE', ls[2][0] + 0.6, ls[3][0] + 0.8, fx=0.74, fy=0.50, alto=0.038, size=40)
    d.cifra('332', d.t(('three', '332', '33'), ls[3][0]), ls[4][1], fx=0.74, fy=0.34, alto=0.150, size=190)
    d.card('CONFIRMED BY FUNERALS', d.t(('three', '332', '33'), ls[3][0]) + 0.3, ls[4][1], fx=0.74, fy=0.52,
           alto=0.038, size=40)
    d.prop('lupa', ls[4][0] + 0.3, ls[4][1], 0.74, 0.34, 0.16)
    # el oleoducto
    d.plano(ls[5][0], ls[6][1], 'Abqaiq', 0.62, 'Yanbu', 0.70)
    d.mu.route(['Abqaiq', 'Yanbu'], ls[5][0] + 0.2, ls[5][0] + 1.6, color=PR.OCRE, width=16)
    d.card('EAST-WEST PIPELINE', ls[5][0] + 0.3, ls[6][1], fy=0.20, alto=0.052, size=54)
    d.prop('dron', d.t('drones', ls[5][0]), ls[6][1], 0.38, 0.40, 0.085)
    d.prop('dron', d.t('drones', ls[5][0]) + 0.3, ls[6][1], 0.58, 0.34, 0.075)
    d.sello('SHUT DOWN', ls[5][1] - 0.6, ls[6][1], fx=0.50, fy=0.68, alto=0.080, size=48)
    d.card('RIYADH BLAMES IRAN', ls[6][0] + 0.3, ls[6][1], fy=0.82, alto=0.048, size=50)
    # probably
    d.mesa(ls[7][0], ls[8][1], 'recibo_usd', alto=0.44)
    d.sello('PROBABLY', ls[7][0] + 0.3, ls[7][1], fx=0.50, fy=0.30, alto=0.095, size=56)
    d.card('NO RECEIPT SHOWN', ls[7][0] + 0.8, ls[7][1], fy=0.74, alto=0.050, size=52)
    d.card('FACT', ls[8][0] + 0.4, ls[8][1], fx=0.32, fy=0.28, alto=0.060, size=58)
    d.sello('CLAIMS', ls[8][0] + 0.8, ls[8][1], fx=0.68, fy=0.28, alto=0.075, size=48)


# ====================================================================== 05 · ACT I · the gate
def b05(d):
    L = lambda i: d.L(5, i)
    ls = [L(i) for i in range(18)]
    d.rotulo('WHAT A CHOKEPOINT IS', ls[0][0], ls[1][1])
    d.mesa(ls[0][0], ls[1][1], 'manual', alto=0.46)
    d.card('CHEAPEST ROUTE' + chr(10) + '= ONLY ROUTE', ls[1][0] + 0.2, ls[1][1], fy=0.40,
           alto=0.120, size=76, tcolor=PR.ROJO)
    # las dos rutas
    d.plano(ls[2][0], ls[4][1], 'Bab el-Mandeb', MARROJO * 0.75, 'Suez', MARROJO * 0.62)
    d.mu.route(['Bab el-Mandeb', 'Suez'], ls[2][0] + 0.3, ls[2][1], color=PR.OCRE, width=14)
    d.card('UP THE RED SEA', ls[2][0] + 0.4, ls[3][0], fx=0.30, fy=0.20, alto=0.050, size=52)
    d.card('OR AROUND AFRICA', ls[3][0], ls[4][1], fx=0.70, fy=0.20, alto=0.050, size=52)
    d.cifra('+10 DAYS', d.t(('ten', '10'), ls[3][0]), ls[4][1], fx=0.50, fy=0.36, alto=0.130, size=160)
    for i, p in enumerate(('deposito_fuel', 'recluta', 'poliza')):
        d.prop(p, ls[3][0] + 0.4 + 0.3 * i, ls[4][1], 0.28 + 0.22 * i, 0.66, 0.085)
    # suez en numeros
    d.mesa(ls[5][0], ls[7][1], 'barriles', alto=0.48)
    d.cifra('4.9', ls[5][0] + 0.4, ls[6][0] + 0.5, fx=0.34, fy=0.36, alto=0.170, size=205)
    d.cifra('8.8', d.t(('eight', '8'), ls[6][0]), ls[7][1], fx=0.66, fy=0.36, alto=0.170, size=205)
    d.card('1H 2025', ls[5][0] + 0.6, ls[6][0] + 0.5, fx=0.34, fy=0.53, alto=0.040, size=44)
    d.card('2023', d.t(('eight', '8'), ls[6][0]) + 0.2, ls[7][1], fx=0.66, fy=0.53, alto=0.040, size=44)
    d.card('IT GETS MORE EXPENSIVE', ls[7][0] + 0.3, ls[7][1], fy=0.76, alto=0.050, size=52,
           tcolor=PR.ROJO)
    # la ofensiva, dia a dia
    d.plano(ls[8][0], ls[9][1], 'Saada', YEMEN * 0.85, 'Mocha', YEMEN)
    d.mu.add_layer(d.mu.meta['capas']['avance'], ls[8][0] + 0.5, 2.0, t_off=ls[13][1], dur_off=1.2)
    d.card('3 SEP: THE OFFENSIVE', ls[8][0] + 0.3, ls[9][1], fy=0.20, alto=0.052, size=54,
           tcolor=PR.ROJO)
    d.prop('megafono', ls[9][0] + 0.2, ls[9][1], 0.30, 0.46, 0.115)
    d.card('YAHYA SAREE', ls[9][0] + 0.4, ls[9][1], fx=0.30, fy=0.64, alto=0.042, size=46)
    d.plano(ls[10][0], ls[11][1], 'Mocha', ESTRECHO * 0.72, 'Perim', ESTRECHO * 0.95)
    d.card('10 SEP' + chr(10) + 'MOCHA', ls[10][0] + 0.2, ls[10][1], fx=0.27, fy=0.32, alto=0.105,
           size=68, tcolor=PR.ROJO)
    d.card('11 SEP' + chr(10) + 'PERIM', ls[11][0] + 0.2, ls[11][1], fx=0.73, fy=0.32, alto=0.105,
           size=68, tcolor=PR.ROJO)
    d.plano(ls[12][0], ls[13][1], 'Dhubab', ESTRECHO * 0.9, 'Perim', ESTRECHO * 1.2)
    d.cifra('5,400 km2', ls[12][0] + 0.3, ls[12][1], fx=0.50, fy=0.30, alto=0.135, size=160)
    d.sello('CLAIMS', ls[12][0] + 0.9, ls[12][1], fx=0.80, fy=0.46, alto=0.060, size=40)
    d.card('DHUBAB', ls[13][0] + 0.2, ls[13][1], fx=0.32, fy=0.24, alto=0.050, size=52)
    # los dos conos de vision
    d.plano(ls[14][0], ls[15][1], 'Perim', ESTRECHO * 1.1, 'Bab el-Mandeb', ESTRECHO * 1.35)
    d.prop('isla', ls[14][0] + 0.3, ls[15][1], 0.36, 0.44, 0.105)
    d.prop('isla', ls[14][0] + 0.6, ls[15][1], 0.64, 0.52, 0.105)
    d.card('BOTH LANES, BOTH SIDES', ls[14][0] + 0.9, ls[15][0], fy=0.78, alto=0.050, size=52)
    d.sello('A FIRING POSITION', ls[15][0] + 0.3, ls[15][1], fx=0.50, fy=0.30, alto=0.085, size=50)
    # nadie la tomo
    d.plano(ls[16][0], ls[17][1], 'Perim', ESTRECHO * 1.2, 'Perim', ESTRECHO * 1.5)
    d.card('THEY LEFT THE DAY BEFORE', ls[16][0] + 0.3, ls[16][1], fy=0.24, alto=0.055, size=56)
    d.prop('mano_abierta', ls[17][0] + 0.2, ls[17][1], 0.50, 0.42, 0.145)
    d.sello('PUT DOWN', ls[17][0] + 0.7, ls[17][1], fx=0.50, fy=0.70, alto=0.080, size=48)


# ====================================================================== 06 · ACT II · who they are
def b06(d):
    L = lambda i: d.L(6, i)
    ls = [L(i) for i in range(21)]
    d.rotulo('WHO WALKED IN', ls[0][0], ls[1][1])
    d.mesa(ls[0][0], ls[2][1], 'recibo_usd', alto=0.46)
    d.card('ANSAR ALLAH', ls[1][0] + 0.2, ls[2][1], fy=0.34, alto=0.080, size=72, tcolor=PR.ROJO)
    d.card('"SUPPORTERS OF GOD"', ls[1][0] + 0.7, ls[2][1], fy=0.48, alto=0.045, size=48)
    d.card('HUSSEIN AL-HOUTHI, 2004', ls[2][0] + 0.3, ls[2][1], fy=0.74, alto=0.048, size=50)
    # el norte
    d.plano(ls[3][0], ls[4][1], 'Saada', YEMEN * 0.9, 'Sanaa', YEMEN * 1.15)
    d.mu.add_layer(d.mu.meta['capas']['yem'], ls[3][0] + 0.4, 1.6, t_off=ls[4][1], dur_off=1.0)
    d.card('ZAIDI SHIA' + chr(10) + 'THE POOR NORTH', ls[3][0] + 0.3, ls[4][1], fx=0.28, fy=0.34,
           alto=0.105, size=66)
    d.card('A REGIONAL INSURGENCY', ls[4][0] + 0.3, ls[4][1], fy=0.80, alto=0.048, size=50)
    # 2014
    d.mesa(ls[5][0], ls[6][1], 'cartel_protesta', alto=0.44)
    d.card('JULY 2014' + chr(10) + 'FUEL SUBSIDIES CUT', ls[5][0] + 0.2, ls[6][1], fy=0.34,
           alto=0.110, size=68)
    d.prop('flecha_arriba', ls[5][0] + 0.8, ls[6][1], 0.78, 0.40, 0.10)
    d.card('SECURITY FORCES FIRE', ls[6][0] + 0.3, ls[6][1], fy=0.76, alto=0.048, size=50,
           tcolor=PR.ROJO)
    # la toma de Sanaa
    d.plano(ls[7][0], ls[8][1], 'Saada', YEMEN, 'Sanaa', YEMEN * 1.5)
    d.mu.route(['Saada', 'Sanaa'], ls[7][0] + 0.2, ls[7][1], color=PR.ROJO, width=14)
    d.cifra('21 SEP 2014', ls[7][0] + 0.4, ls[8][1], fx=0.50, fy=0.30, alto=0.130, size=155)
    d.card('SANAA FALLS', ls[7][0] + 0.9, ls[8][1], fy=0.48, alto=0.052, size=54)
    d.mesa(ls[9][0], ls[10][1], 'cal_sep20', alto=0.42)
    d.card('21 SEP 2014', ls[9][0] + 0.2, ls[10][1], fx=0.30, fy=0.36, alto=0.070, size=64)
    d.card('21 SEP 2026', ls[9][0] + 0.6, ls[10][1], fx=0.70, fy=0.36, alto=0.070, size=64,
           tcolor=PR.ROJO)
    d.cifra('12 YEARS', ls[10][0] + 0.2, ls[10][1], fx=0.50, fy=0.60, alto=0.115, size=140)
    d.plano(ls[11][0], ls[12][1], 'Sanaa', YEMEN * 0.9, 'Bab el-Mandeb', YEMEN * 1.2)
    d.mu.route(['Sanaa', 'Bab el-Mandeb'], ls[11][0] + 0.2, ls[11][1], color=PR.ROJO, width=14)
    d.prop('barco_vela', ls[11][0] + 0.5, ls[12][1], 0.62, 0.62, 0.10)
    d.prop('barrera', ls[12][0] + 0.2, ls[12][1], 0.62, 0.44, 0.105)
    # 2023: el Galaxy Leader
    d.plano(ls[13][0], ls[14][1], 'Bab el-Mandeb', MARROJO * 0.9, 'Hanish Is.', MARROJO * 1.15)
    d.card('NOV 2023', ls[13][0] + 0.2, ls[14][1], fx=0.26, fy=0.20, alto=0.052, size=54,
           tcolor=PR.ROJO)
    d.prop('cohete', ls[13][0] + 0.5, ls[13][1], 0.42, 0.50, 0.095)
    d.prop('cohete', ls[13][0] + 0.8, ls[13][1], 0.56, 0.42, 0.085)
    d.mesa(ls[14][0], ls[15][1], 'recibo_usd', alto=0.44)
    d.card('GALAXY LEADER', ls[14][0] + 0.2, ls[15][1], fy=0.32, alto=0.070, size=64)
    d.cifra('25 CREW', ls[14][0] + 0.7, ls[15][0] + 0.5, fx=0.50, fy=0.50, alto=0.110, size=135)
    d.cifra('14 MONTHS', ls[15][0] + 0.3, ls[15][1], fx=0.50, fy=0.50, alto=0.110, size=135)
    # prosperity guardian
    d.plano(ls[16][0], ls[17][1], 'Hanish Is.', MARROJO, 'Bab el-Mandeb', MARROJO * 1.2)
    for i in range(4):
        d.prop('buque_guerra', ls[16][0] + 0.25 * i, ls[17][1], 0.20 + 0.20 * i, 0.44, 0.080)
    d.card('PROSPERITY GUARDIAN', ls[16][0] + 0.4, ls[17][1], fy=0.20, alto=0.052, size=54)
    d.cifra('20+ NATIONS', ls[17][0] + 0.2, ls[17][1], fx=0.50, fy=0.70, alto=0.110, size=135)
    # y el trafico no volvio
    d.mesa(ls[18][0], ls[19][1], 'barriles', alto=0.50)
    d.cifra('9.3', ls[18][0] + 0.4, ls[19][1], fx=0.33, fy=0.34, alto=0.175, size=210)
    d.cifra('4.1', d.t(('four', '4'), ls[18][0] + 1.0), ls[19][1], fx=0.67, fy=0.34, alto=0.175, size=210)
    d.sello('NEVER CAME BACK', ls[19][0] + 0.3, ls[19][1], fx=0.50, fy=0.72, alto=0.085, size=50)
    d.plano(ls[20][0], ls[20][1], 'Perim', ESTRECHO * 0.9, 'Perim', ESTRECHO * 1.15)
    d.card('CLOSED IN 2023.' + chr(10) + 'MOVED IN 2026.', ls[20][0] + 0.2, ls[20][1], fy=0.34,
           alto=0.115, size=72, tcolor=PR.ROJO)


# ====================================================================== 07 · ACT III · eleven years
def b07(d):
    L = lambda i: d.L(7, i)
    ls = [L(i) for i in range(16)]
    d.rotulo('MARCH 2015', ls[0][0], ls[1][1])
    d.plano(ls[0][0], ls[1][1], 'Riyadh', REG * 1.5, 'Sanaa', REG * 1.9)
    for i in range(3):
        d.prop('avion_gris', ls[0][0] + 0.3 * i, ls[1][1], 0.26 + 0.24 * i, 0.32 + 0.06 * i, 0.075)
    d.card('SAUDI-LED COALITION', ls[0][0] + 0.4, ls[1][0], fy=0.72, alto=0.052, size=54)
    d.card('"FEAR OF IRANIAN INFLUENCE OVER' + chr(10) + 'THE ENTRANCE TO THE RED SEA"',
           ls[1][0] + 0.2, ls[1][1], fy=0.44, alto=0.115, size=58)
    d.plano(ls[2][0], ls[3][1], 'Bab el-Mandeb', ESTRECHO * 0.75, 'Perim', ESTRECHO)
    d.card('THE ENTRANCE TO THE RED SEA', ls[2][0] + 0.2, ls[2][1], fy=0.24, alto=0.055, size=56,
           tcolor=PR.ROJO)
    d.card('HELD BY THEM NOW', ls[3][0] + 0.3, ls[3][1], fy=0.38, alto=0.065, size=62, tcolor=PR.ROJO)
    d.sello('HELD BY THEM', ls[3][0] + 0.8, ls[3][1], fx=0.50, fy=0.70, alto=0.080, size=48)
    # el coste
    d.mesa(ls[4][0], ls[5][1], 'memorial', alto=0.46)
    d.card('HUNDREDS OF THOUSANDS DEAD', ls[4][0] + 0.2, ls[5][1], fy=0.34, alto=0.055, size=56)
    d.sello('FAILED', ls[5][0] + 0.3, ls[5][1], fx=0.50, fy=0.62, alto=0.095, size=56)
    # la factura
    d.mesa(ls[6][0], ls[8][1], 'recibo_usd', alto=0.50)
    d.card('NOT ON 11 SEPTEMBER.', ls[7][0] + 0.2, ls[7][1], fy=0.30, alto=0.050, size=52)
    d.cifra('2015 - 2026', ls[7][0] + 0.8, ls[8][1], fx=0.50, fy=0.46, alto=0.125, size=150)
    d.card('NO ENDING WRITTEN INTO IT', ls[8][0] + 0.3, ls[8][1], fy=0.70, alto=0.048, size=50)
    # washington
    d.mesa(ls[9][0], ls[9][1], 'tratado', alto=0.46)
    d.card('SOLD THE WEAPONS.' + chr(10) + 'REFUELLED THE AIRCRAFT.', ls[9][0] + 0.2, ls[9][1],
           fy=0.36, alto=0.105, size=62)
    # las dos coaliciones
    d.plano(ls[10][0], ls[12][1], 'Bab el-Mandeb', MARROJO * 0.85, 'Sanaa', MARROJO)
    d.sello('CAMPAIGN 2015', ls[10][0] + 0.3, ls[12][1], fx=0.28, fy=0.30, alto=0.075, size=44)
    d.sello('PROSPERITY 2023', ls[10][0] + 0.7, ls[12][1], fx=0.72, fy=0.30, alto=0.075, size=44)
    d.card('THE COUNTRY', ls[12][0] + 0.2, ls[12][1], fx=0.28, fy=0.56, alto=0.045, size=48)
    d.card('THE SEA', ls[12][0] + 0.5, ls[12][1], fx=0.72, fy=0.56, alto=0.045, size=48)
    d.plano(ls[13][0], ls[13][1], 'Sanaa', YEMEN * 0.9, 'Perim', YEMEN * 1.25)
    d.cifra('THEY HOLD BOTH', ls[13][0] + 0.1, ls[13][1], fx=0.50, fy=0.34, alto=0.125, size=150)
    # la moraleja
    d.mesa(ls[14][0], ls[15][1], 'libro_mayor', alto=0.48)
    d.card('A WAR WITH NO VICTORY' + chr(10) + 'DOES NOT END', ls[14][0] + 0.2, ls[14][1], fy=0.36,
           alto=0.115, size=68)
    d.card('AN INVOICE', ls[15][0] + 0.2, ls[15][1], fy=0.34, alto=0.075, size=68, tcolor=PR.ROJO)
    d.sello('ADDRESSED TO RIYADH' + chr(10) + 'AND WASHINGTON', ls[15][0] + 0.7, ls[15][1],
            fx=0.50, fy=0.62, alto=0.105, size=44)


# ====================================================================== 08 · ACT IV · the pincer
def b08(d):
    L = lambda i: d.L(8, i)
    ls = [L(i) for i in range(18)]
    d.rotulo('THE TWO DOORS', ls[0][0], ls[0][1])
    d.plano(ls[0][0], ls[1][1], 'Bab el-Mandeb', REG, 'Hormuz', REG * 1.15)
    d.prop('barrera', ls[0][0] + 0.25, ls[0][1], 0.26, 0.42, 0.105)
    d.prop('barrera', ls[0][0] + 0.45, ls[0][1], 0.74, 0.42, 0.105)
    d.card('BOTH OF THEM', ls[0][0] + 0.65, ls[0][1], fy=0.70, alto=0.055, size=56, tcolor=PR.ROJO)
    d.mu.add_layer(d.mu.meta['capas']['irn'], ls[1][0] + 0.3, 1.5, t_off=ls[3][1], dur_off=1.0)
    d.card('28 FEB', ls[1][0] + 0.2, ls[1][1], fx=0.24, fy=0.20, alto=0.052, size=54, tcolor=PR.ROJO)
    d.prop('fuego', ls[1][0] + 0.5, ls[1][1], 0.66, 0.42, 0.105)
    d.plano(ls[2][0], ls[3][1], 'Hormuz', 0.80, 'Hormuz', 1.05)
    d.card('27 MAR: HORMUZ CLOSED', ls[2][0] + 0.2, ls[3][1], fy=0.20, alto=0.052, size=54)
    d.prop('barrera', ls[2][0] + 0.6, ls[3][1], 0.50, 0.42, 0.125)
    d.cifra('20+  -  10', d.t(('twenty', '20'), ls[3][0] - 0.5), ls[3][1], fx=0.50, fy=0.68, alto=0.110,
            size=135)
    # la via de escape
    d.plano(ls[4][0], ls[6][1], 'Abqaiq', 0.60, 'Yanbu', 0.68)
    d.card('THE WAY OUT', ls[4][0] + 0.3, ls[4][1], fy=0.20, alto=0.052, size=54)
    d.mu.route(['Abqaiq', 'Yanbu'], ls[5][0] + 0.1, ls[5][1], color=PR.OCRE, width=18)
    d.card('EAST-WEST PIPELINE', ls[5][0] + 0.4, ls[6][1], fy=0.78, alto=0.052, size=54)
    d.prop('barril', ls[5][0] + 0.8, ls[5][1], 0.34, 0.44, 0.095)
    d.prop('dron', ls[6][0] + 0.2, ls[6][1], 0.44, 0.36, 0.085)
    d.prop('dron', ls[6][0] + 0.5, ls[6][1], 0.60, 0.30, 0.075)
    d.sello('SHUT DOWN', ls[6][0] + 0.9, ls[6][1], fx=0.50, fy=0.56, alto=0.085, size=50)
    # el mismo dia
    d.plano(ls[7][0], ls[8][1], 'Perim', ESTRECHO * 0.8, 'Perim', ESTRECHO * 1.05)
    d.card('THE SAME DAY', ls[7][0] + 0.2, ls[7][1], fy=0.24, alto=0.055, size=56, tcolor=PR.ROJO)
    d.prop('isla', ls[7][0] + 0.5, ls[8][1], 0.50, 0.44, 0.115)
    d.card('20 JULY: BLOCKADE DECLARED', ls[8][0] + 0.3, ls[8][1], fy=0.78, alto=0.050, size=52)
    d.mesa(ls[9][0], ls[10][1], 'decreto', alto=0.44)
    d.card('SEVEN WEEKS LATER', ls[9][0] + 0.3, ls[9][1], fy=0.34, alto=0.055, size=58)
    d.sello('A PLAN WITH A TIMETABLE', ls[10][0] + 0.2, ls[10][1], fx=0.50, fy=0.40, alto=0.095,
            size=48)
    # la tenaza
    d.plano(ls[11][0], ls[12][1], 'Riyadh', REG * 1.05, 'Riyadh', REG * 1.25)
    d.prop('barrera', ls[11][0] + 0.2, ls[12][1], 0.22, 0.38, 0.115)
    d.prop('barrera', ls[11][0] + 0.4, ls[12][1], 0.78, 0.38, 0.115)
    d.prop('eslabon_rojo', ls[11][0] + 0.7, ls[12][1], 0.50, 0.44, 0.095)
    d.cifra('PINCER', ls[12][0] + 0.1, ls[12][1], fx=0.50, fy=0.70, alto=0.135, size=165)
    # y funciono
    d.mesa(ls[13][0], ls[15][1], 'barriles', alto=0.50)
    d.cifra('400,000 b/d', ls[13][0] + 0.4, ls[14][0] + 0.4, fx=0.50, fy=0.34, alto=0.125, size=150)
    d.cifra('LOWEST SINCE 1990', ls[14][0] + 0.2, ls[15][1], fx=0.50, fy=0.34, alto=0.115, size=140)
    d.prop('cal20', ls[15][0] + 0.2, ls[15][1], 0.50, 0.62, 0.115)
    # el portavoz
    d.plano(ls[16][0], ls[17][1], 'Bab el-Mandeb', ESTRECHO * 0.85, 'Perim', ESTRECHO * 1.1)
    d.prop('megafono', ls[16][0] + 0.2, ls[17][1], 0.30, 0.42, 0.115)
    d.card('"SAFE FOR EVERYONE' + chr(10) + 'EXCEPT SAUDI SHIPS"', ls[16][0] + 0.4, ls[17][1],
           fx=0.66, fy=0.40, alto=0.115, size=58, tcolor=PR.ROJO)
    d.prop('barco_vela', ls[17][0] + 0.3, ls[17][1], 0.34, 0.72, 0.075)


# ====================================================================== 09 · ACT V · the receipt
def b09(d):
    L = lambda i: d.L(9, i)
    ls = [L(i) for i in range(17)]
    d.rotulo('THE RECEIPT', ls[0][0], ls[0][1])
    d.mesa(ls[0][0], ls[4][1], 'recibo_usd', alto=0.52)
    d.cifra('$99.85', ls[1][0] + 0.3, ls[2][0] + 0.4, fx=0.28, fy=0.34, alto=0.145, size=175)
    d.card('8 SEP', ls[1][0] + 0.6, ls[2][0] + 0.4, fx=0.28, fy=0.50, alto=0.040, size=44)
    d.cifra('$108.92', ls[2][0] + 0.3, ls[3][0] + 0.4, fx=0.50, fy=0.34, alto=0.145, size=175)
    d.card('11 SEP', ls[2][0] + 0.6, ls[3][0] + 0.4, fx=0.50, fy=0.50, alto=0.040, size=44)
    d.cifra('$109.21', ls[3][0] + 0.3, ls[4][1], fx=0.72, fy=0.34, alto=0.145, size=175)
    d.card('15 SEP', ls[3][0] + 0.6, ls[4][1], fx=0.72, fy=0.50, alto=0.040, size=44)
    d.cifra('+$9 IN 7 DAYS', ls[4][0] + 0.2, ls[4][1], fx=0.50, fy=0.70, alto=0.110, size=135)
    # la cadena
    d.plano(ls[5][0], ls[6][1], 'Bab el-Mandeb', YEMEN * 0.8, 'Aden', YEMEN)
    for i, p in enumerate(('barril', 'tanquero', 'carro')):
        d.prop(p, ls[5][0] + 0.3 + 0.35 * i, ls[6][1], 0.26 + 0.24 * i, 0.44, 0.105)
    d.card('OIL - DIESEL - EVERYTHING YOU BUY', ls[5][0] + 0.5, ls[6][1], fy=0.76, alto=0.048,
           size=50)
    # la eleccion
    d.plano(ls[7][0], ls[8][1], 'Bab el-Mandeb', MARROJO * 1.25, 'Suez', MARROJO * 0.62)
    d.card('WAR-RISK PREMIUM', ls[7][0] + 0.2, ls[8][1], fx=0.28, fy=0.24, alto=0.050, size=52)
    d.card('OR +10 DAYS', ls[7][0] + 0.5, ls[8][1], fx=0.72, fy=0.24, alto=0.050, size=52)
    d.prop('poliza', ls[7][0] + 0.7, ls[8][1], 0.28, 0.50, 0.105)
    d.prop('reloj_arena', ls[7][0] + 0.9, ls[8][1], 0.72, 0.50, 0.105)
    d.prop('recibo_usd', ls[8][0] + 0.3, ls[8][1], 0.50, 0.72, 0.095)
    # todos aprendieron
    d.mesa(ls[9][0], ls[11][1], 'libro_mayor', alto=0.48)
    d.card('SQUEEZING A ROUTE IS' + chr(10) + "EVERYONE'S TOOL", ls[9][0] + 0.2, ls[9][1], fy=0.36,
           alto=0.115, size=66)
    d.cifra('$4.8 BN', ls[10][0] + 0.3, ls[11][1], fx=0.50, fy=0.34, alto=0.145, size=175)
    d.card('IRANIAN OIL REVENUE, GONE', ls[10][0] + 0.7, ls[11][1], fy=0.52, alto=0.045, size=48)
    d.sello('IT WORKED', ls[11][0] + 0.3, ls[11][1], fx=0.50, fy=0.72, alto=0.085, size=50)
    # el recibo, y la pregunta
    d.mesa(ls[12][0], ls[13][1], 'recibo_usd', alto=0.50)
    d.sello('THE RECEIPT', ls[12][0] + 0.3, ls[13][1], fx=0.50, fy=0.36, alto=0.095, size=54)
    d.card("SOMEBODY ELSE'S WAR." + chr(10) + 'PRICED INTO YOUR WEEK.', ls[13][0] + 0.2, ls[13][1],
           fy=0.62, alto=0.105, size=60)
    d.plano(ls[14][0], ls[16][1], 'Bab el-Mandeb', ESTRECHO * 0.8, 'Bab el-Mandeb', ESTRECHO)
    d.card('YOUR ANSWER', ls[14][0] + 0.2, ls[14][1], fy=0.22, alto=0.055, size=56)
    d.cifra('NAVY IN?' + chr(10) + 'OR STAY OUT?', ls[15][0] + 0.2, ls[16][1], fx=0.50, fy=0.40,
            alto=0.185, size=115)
    d.prop('buque_guerra', ls[16][0] + 0.2, ls[16][1], 0.22, 0.72, 0.085)
    d.prop('sello_no', ls[16][0] + 0.4, ls[16][1], 0.78, 0.72, 0.075)


# ====================================================================== 10 · close
def b10(d):
    L = lambda i: d.L(10, i)
    ls = [L(i) for i in range(9)]
    # el matiz honesto
    d.plano(ls[0][0], ls[1][1], 'Taiz', YEMEN * 0.95, 'Taiz', YEMEN * 1.2)
    d.card('13 SEP: TAIZ, PARTLY BACK', ls[0][0] + 0.2, ls[1][1], fy=0.22, alto=0.052, size=54)
    d.prop('escoba', ls[1][0] + 0.2, ls[1][1], 0.50, 0.46, 0.115)
    d.card('NOT FINISHED', ls[1][0] + 0.5, ls[1][1], fy=0.74, alto=0.055, size=56)
    # el veredicto
    d.mesa(ls[2][0], ls[4][1], 'decreto', alto=0.50)
    d.card('A STRAIGHT ANSWER', ls[2][0] + 0.2, ls[2][1], fy=0.32, alto=0.060, size=60)
    d.prop('barrera', ls[3][0] + 0.2, ls[3][1], 0.34, 0.44, 0.115)
    d.prop('fusil', ls[3][0] + 0.4, ls[3][1], 0.66, 0.44, 0.105)
    d.cifra('A TOLL BOOTH' + chr(10) + 'WITH RIFLES', ls[3][0] + 0.7, ls[3][1], fx=0.50, fy=0.64,
            alto=0.135, size=88)
    d.sello('AGGRESSION', ls[4][0] + 0.4, ls[4][1], fx=0.50, fy=0.40, alto=0.100, size=56)
    # la segunda conclusion
    d.plano(ls[5][0], ls[6][1], 'Riyadh', REG * 1.2, 'Sanaa', REG * 1.45)
    d.card('NOBODY IN RIYADH OR WASHINGTON' + chr(10) + 'WILL SAY THIS OUT LOUD', ls[5][0] + 0.2,
           ls[5][1], fy=0.40, alto=0.115, size=58)
    for i, p in enumerate(('cal20', 'escudo', 'avion_gris', 'bandera_us')):
        d.prop(p, ls[6][0] + 0.2 * i, ls[6][1], 0.20 + 0.20 * i, 0.44, 0.085)
    d.plano(ls[7][0], ls[8][1], 'Perim', ESTRECHO * 0.85, 'Perim', ESTRECHO * 1.1)
    d.card('THEY HANDED OVER THE EXACT THING' + chr(10) + 'THE WAR WAS DECLARED TO PROTECT',
           ls[7][0] + 0.2, ls[7][1], fy=0.30, alto=0.115, size=56, tcolor=PR.ROJO)
    d.sello('AGGRESSION', ls[8][0] + 0.3, ls[8][1], fx=0.28, fy=0.46, alto=0.095, size=52)
    d.sello('FAILURE', ls[8][0] + 0.5, ls[8][1], fx=0.72, fy=0.46, alto=0.095, size=52)
    d.card('BOTH ARE TRUE', ls[8][0] + 0.9, ls[8][1], fy=0.74, alto=0.058, size=58)


# ====================================================================== 11 · next
def b11(d):
    L = lambda i: d.L(11, i)
    a, b, c = L(0), L(1), L(2)
    d.plano(a[0], b[1], 'Bab el-Mandeb', REG * 1.1, 'Hormuz', 0.85)
    d.card('NEXT ON PAPER TRAIL', a[0] + 0.2, a[1], fy=0.22, alto=0.055, size=56)
    d.prop('barrera', a[0] + 0.6, b[1], 0.50, 0.42, 0.115)
    d.card('THE FIRST DOOR', a[0] + 0.9, b[1], fy=0.62, alto=0.052, size=54, tcolor=PR.ROJO)
    d.prop('recibo_usd', b[0] + 0.2, b[1], 0.26, 0.70, 0.095)
    # El plano llega hasta el FINAL de la escena, no hasta el final de la voz. El wav lleva 8 s de
    # post-roll (§2.3) y sin esto la coreografia se acababa en 926,9 s sobre 933,8: casi 7 s con la
    # camara clavada, que `ritmo.py` mide como un plano de 8,25 s y suspende la tercera prueba. El
    # cierre de marca ocupa esa cola, que es para lo que esta.
    d.plano(c[0], d.dur, 'Hormuz', 0.85, 'Bab el-Mandeb', 0.62)
    d.card('FOLLOW THE PAPER', c[0], d.dur - 0.3, fy=0.42, alto=0.085, size=76, sfx='stamp')
