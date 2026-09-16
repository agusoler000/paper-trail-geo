# -*- coding: utf-8 -*-
"""Hoja de mapa del ep. 13 (Yemen / Bab el-Mandeb). 0 creditos: Natural Earth 50m + PIL.

**Por que el bbox es REGIONAL y no Yemen.** La primera version (16-sep) cubria solo Yemen
(41-46,6 E) y no servia: el angulo del episodio son **las dos puertas** del petroleo del Golfo
—Ormuz y el Mar Rojo— y el ACT IV las pone una al lado de la otra. Con la hoja de Yemen, Ormuz,
el oleoducto East-West, Yanbu y Suez se quedaban fuera del mundo y habria que contarlos con
carteles, que es justo lo que la regla 2 no quiere.

Este bbox (31,5-58,5 E · 9,5-31 N) entra: Suez, el Mar Rojo entero, Yemen, el golfo de Aden, la
peninsula, el Golfo Persico y Ormuz. A 9000 px de ancho son ~333 px por grado: un plano cerrado
sobre el estrecho (0,3 grados) da ~100 px de mundo, asi que **el detalle del Bab el-Mandeb se
cuenta con props de papel encima del mapa**, no con zoom. Es el lenguaje del canal.

La hoja BASE va sin roles: tierra kaki, oceano teal (se probaron los dos roles el 16-sep; 'sujeto'
celeste se confundia con el teal del oceano y 'acreedor' ocre se comia medio cuadro). El color va
en CAPAS que la coreografia enciende cuando la voz nombra el pais, que es para lo que existen.

Regla 24: `mundo()` comprueba cada sitio contra una proyeccion Mercator calculada aparte y aborta
si alguno se pasa de 3 px.
"""
import os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', '..', '..', 'produccion'))
import mapa_v2 as MV
from props import GRIS as PR_GRIS

BBOX = (31.5, 58.5, 9.5, 31.0)            # lon0, lon1, lat0, lat1
ANCHO = 9000

ROLES = {}                                 # la hoja base es neutra; el color va en capas

# El tercer valor es el ALPHA. `capa_pais` usa 226 por defecto y eso, en un plano cerrado, es una
# pared de color plano: en la primera hoja de contacto (16-sep) Arabia Saudi salia como un bloque
# azul y Yemen como un bloque naranja que se comian media pantalla. La capa tiene que TENIR, no
# tapar: el relieve y los rotulos de la hoja se siguen leyendo por debajo.
CAPAS = {
    'yem':    (['YEM'], MV.ROL['acreedor'], 58),       # Yemen, ocre
    'sau':    (['SAU'], MV.ROL['institucion'], 52),    # Arabia Saudi, azul
    'irn':    (['IRN'], MV.ROL['tercero'], 52),        # Iran, verde
    'avance': (['YEM'], MV.ROL['deudor'], 96),         # rojo: el avance hutie, si tiene que destacar
}

SITIOS = {
    # el estrecho y la costa que cae en septiembre
    'Bab el-Mandeb': (43.33, 12.58),
    'Perim':         (43.42, 12.65),
    'Mocha':         (43.25, 13.32),
    'Dhubab':        (43.35, 12.95),
    'Hanish Is.':    (42.75, 13.72),
    # Yemen
    'Sanaa':         (44.21, 15.35),
    'Saada':         (43.76, 16.94),
    'Taiz':          (44.02, 13.58),
    'Aden':          (45.04, 12.79),
    # la otra puerta y la via de escape saudi
    'Hormuz':        (56.25, 26.57),
    'Abqaiq':        (49.67, 25.93),      # origen del oleoducto East-West
    'Yanbu':         (38.06, 24.09),      # su terminal en el Mar Rojo
    'Riyadh':        (46.68, 24.71),
    'Medina':        (39.61, 24.47),
    'Suez':          (32.58, 30.02),
}


# `pins_opciones` es **por sitio** (`{nombre: {...}}`), no global: un `{'r': 13}` suelto se lee como
# un sitio llamado "r" y se ignora en silencio (paso el 16-sep y los puntos siguieron gigantes).
#
# r y size van en px de MUNDO. Con 9000 px de ancho el automatico da r=37 y texto de 130, que en un
# plano cerrado se ven como discos de 190 px: eran las "manchas rojas" de la hoja de contacto.
# Ademas se jerarquiza: los tres sitios que el episodio senala van marcados, y el resto queda de
# referencia, mas chico y en gris, para que no compitan.
_PROTA = ('Perim', 'Bab el-Mandeb', 'Mocha')
PINS = {}
for _s in SITIOS:
    if _s in _PROTA:
        PINS[_s] = {'r': 11, 'size': 30}
    else:
        PINS[_s] = {'r': 7, 'size': 24, 'color': PR_GRIS}


def build(force=False):
    return MV.mundo('yemen', BBOX, ANCHO, roles=ROLES, sitios=SITIOS,
                    out_dir=os.path.join(AQUI, 'assets'), capas=CAPAS,
                    pins_opciones=PINS, force=force)


if __name__ == '__main__':
    m = build(force='--force' in sys.argv)
    print('OK ->', m)
