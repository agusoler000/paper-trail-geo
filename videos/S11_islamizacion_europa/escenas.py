# -*- coding: utf-8 -*-
"""Partitura del short S11 («La islamizacion de Europa»). Una funcion, `e01`, anclada a las 24 lineas.

Vocabulario que vuelve (leccion 10 del ep. 06): **la mezquita** (el islam politico), **el grafico** (la
demografia), **el mapa** (el territorio) y **el sello rojo** (la conclusion). Las tarjetas rojas son los
golpes: «7.4 %», «1,400 CHILDREN», «317» y «ISLAMIZING».

Composicion (leccion del S03): nunca un objeto solo; cada beat abre a la izquierda (fx ~0,27) y a los
~2 s entra la contraparte a la derecha (fx ~0,72). WALL va centrado. El primer objeto NO es un `dr`.
"""


def correr(A, pasos):
    L, E = A['L'], A['E']
    cut, card, P, drop, stamp = A['cut'], A['card'], A['P'], A['drop'], A['stamp']
    girar, latir, PR = A['girar'], A['latir'], A['PR']

    def T(i):
        if isinstance(i, tuple): return max(0.06, T(i[0])+i[1])
        return max(0.06, E(-i) if i < 0 else L(i))

    CORTES = sorted(T(q[1]) for q in pasos if q[0] == 'cut')

    def hasta(t):
        for c in CORTES:
            if c > t+0.35: return max(2.6, c-t+0.9)
        return max(2.6, A['DUR']-t)

    def antes(t, t_paso):
        for c in CORTES:
            if t_paso < c <= t: return max(t_paso+0.1, c-0.35)
        return t

    ult = [0.0]
    for p in pasos:
        k = p[0]
        if k == 'cut':
            ult[0] = T(p[1]); cut(T(p[1]), p[2], *(p[3:]))
        elif k in ('card', 'rojo'):
            i, txt, fx, fy, size = p[1:6]; t = antes(T(i), ult[0])
            card(txt, t, fx=fx, fy=fy, size=size, dur=hasta(t),
                 tcolor=PR.ROJO if k == 'rojo' else PR.TINTA)
        elif k in ('P', 'dr'):
            i, name, fx, fy, sc_ = p[1:6]; t = antes(T(i), ult[0])
            (P if k == 'P' else drop)(name, t, fx=fx, fy=fy, sc_=sc_, dur=hasta(t))
        elif k == 'st':
            i, name, fx, fy, sc_ = p[1:6]; t = antes(T(i), ult[0])
            stamp(name, t, fx=fx, fy=fy, sc_=sc_, dur=hasta(t))
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


NL = chr(10)


def e01(A):
    correr(A, [
        # --- el enganche
        ('cut', (0, -0.45), 'CTR'),
        ('P',    0, 'mapa_europa', 0.27, 0.50, 0.95),
        ('card', (0, 2.0), 'JUST GETTING OLD?', 0.72, 0.42, 88),
        # --- la fuente
        ('cut',  1, 'WALL'),
        ('rojo', 1, 'PEW RESEARCH', 0.5, 0.30, 120),
        ('card', (1, 2.0), 'COUNTED THE' + NL + 'OTHER HALF', 0.5, 0.76, 86),
        # --- 2016
        ('cut',  2, 'CTR'),
        ('P',    2, 'grafico', 0.26, 0.48, 1.0),
        ('card', (2, 2.2), '4.9%' + NL + 'IN 2016', 0.74, 0.42, 88),
        # --- 7.4% con fronteras cerradas
        ('cut',  3, 'CTR'),
        ('P',    3, 'grafico', 0.26, 0.48, 1.0),
        ('rojo', (3, 2.0), '7.4%' + NL + 'BY 2050', 0.74, 0.42, 92),
        # --- medio y alto
        ('cut',  4, 'WALL'),
        ('card', 4, 'MEDIUM 11.2' + NL + 'HIGH 14', 0.5, 0.44, 100),
        # --- el no-musulman cae
        ('cut',  5, 'CTR'),
        ('P',    5, 'multitud', 0.27, 0.50, 1.0),
        ('card', (5, 2.0), 'NON-MUSLIMS' + NL + 'FALL IN ALL 3', 0.74, 0.44, 84),
        # --- 3.7 millones
        ('cut',  6, 'CTR'),
        ('P',    6, 'sobre', 0.26, 0.48, 1.0),
        ('card', (6, 2.0), '3.7M IN 6 YEARS' + NL + '60% OF GROWTH', 0.74, 0.44, 82),
        # --- la calle
        ('cut',  7, 'CTR'),
        ('P',    7, 'mapa_europa', 0.26, 0.48, 0.95),
        ('card', (7, 2.0), 'MALMO 1/3' + NL + 'BRADFORD 30.5' + NL + 'MOLENBEEK 25-40', 0.74, 0.42, 74),
        # --- suecia / francia / uk
        ('cut',  8, 'WALL'),
        ('rojo', 8, 'SWEDEN 8% -> 30%', 0.5, 0.30, 104),
        ('card', (8, 2.2), 'FRANCE & UK' + NL + 'NEAR 17%', 0.5, 0.76, 86),
        # --- tiene constructores
        ('cut',  9, 'CTR'),
        ('P',    9, 'mezquita', 0.27, 0.50, 1.0),
        ('dr',   (9, 2.0), 'sobre', 0.72, 0.44, 0.8),
        ('card', (9, 2.6), 'IT HAS' + NL + 'BUILDERS', 0.72, 0.80, 76),
        # --- hermanos musulmanes
        ('cut',  10, 'CTR'),
        ('P',    10, 'media_luna', 0.26, 0.48, 1.0),
        ('st',   (10, 2.0), 'sello_600', 0.73, 0.44, 0.9),
        # --- diyanet
        ('cut',  11, 'CTR'),
        ('P',    11, 'bandera_tr', 0.26, 0.46, 1.0),
        ('card', (11, 2.0), '900 MOSQUES' + NL + 'IN GERMANY', 0.74, 0.42, 86),
        # --- austria deporto imames
        ('cut',  12, 'WALL'),
        ('st',   12, 'sello_closed', 0.34, 0.44, 1.0),
        ('card', (12, 2.0), '40 IMAMS' + NL + 'DEPORTED', 0.72, 0.44, 86),
        # --- arabia y libia
        ('cut',  13, 'CTR'),
        ('P',    13, 'bandera_sa', 0.26, 0.46, 1.0),
        ('P',    (13, 1.9), 'bandera_li', 0.72, 0.46, 1.0),
        ('card', (13, 3.0), 'FUNDED SWEDEN\'S' + NL + 'LARGEST MOSQUES', 0.5, 0.84, 74),
        # --- viena
        ('cut',  14, 'CTR'),
        ('st',   14, 'sello_denied', 0.27, 0.44, 0.95),
        ('card', (14, 2.0), 'VIENNA:' + NL + 'PRO-HAMAS SERMONS', 0.73, 0.44, 82),
        # --- rotherham
        ('cut',  15, 'WALL'),
        ('rojo', 15, '1,400 CHILDREN', 0.5, 0.30, 118),
        ('card', (15, 2.2), 'ROTHERHAM' + NL + 'PAKISTANI-ORIGIN GANGS', 0.5, 0.76, 72),
        # --- suecia bombas
        ('cut',  16, 'CTR'),
        ('card', 16, '162 IN 2018', 0.27, 0.40, 88),
        ('rojo', (16, 2.0), '317 IN 2024', 0.73, 0.40, 92),
        # --- malmo judios
        ('cut',  17, 'CTR'),
        ('P',    17, 'sinagoga', 0.26, 0.46, 1.0),
        ('P',    (17, 1.9), 'fuego', 0.73, 0.46, 0.8),
        ('card', (17, 3.0), 'MALMO\'S JEWS:' + NL + '700 AND FALLING', 0.5, 0.84, 74),
        # --- francia
        ('cut',  18, 'WALL'),
        ('card', 18, 'THE LOST TERRITORIES' + NL + 'OF THE REPUBLIC', 0.5, 0.40, 96),
        ('card', (18, 2.4), '2002', 0.5, 0.80, 88),
        # --- solo un grupo crece
        ('cut',  19, 'CTR'),
        ('P',    19, 'multitud', 0.26, 0.48, 1.0),
        ('rojo', (19, 2.0), 'ONE GROUP' + NL + 'GROWS', 0.74, 0.44, 86),
        # --- los que pagaron
        ('cut',  20, 'CTR'),
        ('P',    20, 'media_luna', 0.26, 0.48, 1.0),
        ('card', (20, 2.0), 'THEY PAID' + NL + 'THE IMAMS', 0.74, 0.44, 86),
        # --- tendencia y territorio
        ('cut',  21, 'WALL'),
        ('st',   21, 'sello_trend', 0.32, 0.42, 1.0),
        ('st',   (21, 1.6), 'sello_territory', 0.68, 0.42, 1.0),
        # --- la conclusion
        ('cut',  22, 'WALL'),
        ('st',   22, 'sello_islamizing', 0.5, 0.46, 1.05),
        # --- la pregunta
        ('cut',  23, 'WALL'),
        ('rojo', 23, 'DRIFT OR PROJECT?', 0.5, 0.34, 104),
        ('card', (23, 1.6), 'FIVE WORDS. GO.', 0.5, 0.76, 80),
    ])
