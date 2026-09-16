#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
escalera.py - medir MUCHOS terminos en UNA sola escala comparable.

El problema que resuelve
------------------------
Google Trends solo compara 5 terminos por consulta y normaliza cada consulta contra
SU PROPIO pico. Dos consultas distintas NO son comparables. Peor: dentro de una misma
consulta, todo lo que esta muy por debajo del maximo se redondea a 0,0 y se pierde.

El 15-sep esto ya nos mordio (canal/TANDA_SHORTS_2026-09-15.md seccion 1.2: 'space weapons'
parecia 41,2 contra 'iran war' 8,8 y en realidad era 0,0). El 16-sep volvio a morder:
se encadenaron anclas de 14,4 y de 0,144, y cada eslabon flojo multiplica el error.

La escalera
-----------
Se mide por peldanos. Cada peldano lleva un ANCLA que ya tiene escala conocida y hasta
4 terminos nuevos. Del resultado se aceptan solo los terminos que RESUELVEN BIEN
(>= MIN_FIABLE por ciento del maximo del grupo); el resto baja al peldano siguiente, donde
el ancla pasa a ser el termino mas chico que si resolvio. Asi cada comparacion se hace
entre terminos de magnitud parecida y el error no se acumula.

Cada valor sale con su CADENA (por cuantos eslabones paso). Cadena 0 = medido directo
en el grupo de cabeza. Cuantos mas eslabones, mas ancha la barra de error.

Uso
---
    python produccion/escalera.py US "now 7-d" "iran war,venezuela,taiwan,inflation"
    python produccion/escalera.py GB "now 7-d" --archivo candidatos_gb.txt
"""

import argparse
import sys
import time
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

MIN_FIABLE = 4.0     # por debajo de este % del maximo del grupo, el valor no es de fiar
PAUSA = 9            # segundos entre consultas; Trends devuelve 429 si se le insiste
REINTENTOS = 5


def _print(s=''):
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode('ascii', 'replace').decode('ascii'))


def _consulta(p, kws, geo, timeframe):
    """Una consulta a Trends con la propiedad Busquedas de YouTube. Devuelve termino->media."""
    for i in range(REINTENTOS):
        try:
            p.build_payload(list(kws), timeframe=timeframe, geo=geo, gprop='youtube')
            df = p.interest_over_time()
            if df is None or df.empty:
                return None
            cols = [c for c in df.columns if c != 'isPartial']
            if 'isPartial' in df:
                df = df[~df['isPartial'].astype(bool)]
            if df.empty:
                return None
            return {c: float(df[c].mean()) for c in cols}
        except Exception as e:
            _print(f'   . reintento {i+1}/{REINTENTOS} ({type(e).__name__})')
            time.sleep(PAUSA * (i + 2))
    return None


def escalera(terminos, geo, timeframe):
    """Devuelve escala {termino: valor}, eslabon {termino: saltos} y la lista de peldanos."""
    from pytrends.request import TrendReq
    p = TrendReq(hl='en-US', tz=0)

    pendientes = list(dict.fromkeys(terminos))
    escala = {}
    eslabon = {}
    peldanos = []
    ancla = None
    factor = 1.0

    while pendientes:
        nuevos_n = 4 if ancla else 5
        grupo = ([ancla] if ancla else []) + pendientes[:nuevos_n]
        res = _consulta(p, grupo, geo, timeframe)
        time.sleep(PAUSA)
        if res is None:
            peldanos.append((grupo, 'SIN DATOS'))
            _print(f'   !! sin datos: {grupo}')
            pendientes = pendientes[nuevos_n:]
            continue

        if ancla:
            if res.get(ancla, 0) <= 0:
                _print(f'   !! el ancla "{ancla}" dio 0 en su propio grupo; se corta la cadena')
                factor = 1.0
                base_eslabon = 0
            else:
                factor = escala[ancla] / res[ancla]
                base_eslabon = eslabon[ancla] + 1
        else:
            base_eslabon = 0

        mx = max(res.values()) or 1.0
        nuevos = [t for t in grupo if t != ancla]
        resueltos, flojos = [], []
        for t in nuevos:
            v = res.get(t, 0.0)
            if v / mx * 100 >= MIN_FIABLE:
                escala[t] = v * factor
                eslabon[t] = base_eslabon
                resueltos.append(t)
            else:
                flojos.append(t)

        peldanos.append((grupo, {t: round(res.get(t, 0), 1) for t in grupo}))
        pendientes = [t for t in pendientes if t not in resueltos]

        if not resueltos:
            candidatos = [t for t in escala if escala[t] > 0]
            if ancla and candidatos and min(candidatos, key=lambda x: escala[x]) == ancla:
                # ya estamos en el peldano mas bajo disponible: esto no se resuelve
                _print(f'   !! por debajo del suelo de Trends: {flojos}')
                for t in flojos:
                    escala[t] = 0.0
                    eslabon[t] = -1
                pendientes = [t for t in pendientes if t not in flojos]
                continue
            if not candidatos:
                _print(f'   !! nada con que anclar: {flojos}')
                for t in flojos:
                    escala[t] = 0.0
                    eslabon[t] = -1
                pendientes = [t for t in pendientes if t not in flojos]
                continue
            ancla = min(candidatos, key=lambda x: escala[x])
        else:
            ancla = min(resueltos, key=lambda x: escala[x])

    return escala, eslabon, peldanos


def main():
    ap = argparse.ArgumentParser(description='Medir muchos terminos en una escala comparable.')
    ap.add_argument('geo')
    ap.add_argument('timeframe')
    ap.add_argument('terminos', nargs='?', default='', help='separados por coma')
    ap.add_argument('--archivo', help='uno por linea')
    ap.add_argument('--ref', help='termino que vale 100 en la salida (def. el mayor)')
    a = ap.parse_args()

    if a.archivo:
        terms = [l.strip() for l in open(a.archivo, encoding='utf-8')
                 if l.strip() and not l.startswith('#')]
    else:
        terms = [t.strip() for t in a.terminos.split(',') if t.strip()]
    if not terms:
        ap.error('hacen falta terminos')

    _print(f'== ESCALERA | geo={a.geo} | {a.timeframe} | {len(terms)} terminos '
           f'| {datetime.now():%Y-%m-%d %H:%M} ==')
    _print('   propiedad: Busquedas de YouTube (gprop=youtube)')

    escala, eslabon, peldanos = escalera(terms, a.geo, a.timeframe)

    _print('\n-- peldanos (valores crudos de cada consulta, NO comparables entre si)')
    for grupo, res in peldanos:
        if isinstance(res, str):
            _print(f'   [{res}] {grupo}')
        else:
            _print('   ' + '  '.join(f'{k}={v}' for k, v in res.items()))

    vivos = {k: v for k, v in escala.items() if v > 0}
    ref = a.ref if a.ref in vivos else (max(vivos, key=lambda x: vivos[x]) if vivos else None)
    if not ref:
        _print('\n   sin resultados')
        sys.exit(1)
    base = escala[ref] or 1.0

    _print(f'\n-- ESCALA COMUN ("{ref}" = 100)')
    _print('   valor  esl  termino')
    for t in sorted(escala, key=lambda x: -escala[x]):
        v = escala[t] / base * 100
        e = eslabon[t]
        marca = 'n/r' if e < 0 else str(e)
        _print(f'   {v:8.2f}  {marca:>3}  {t}')
    _print('\n   esl = eslabones de la cadena. 0 = medido directo en el grupo de cabeza.')
    _print('   n/r = no resolvio ni en su peldano mas bajo: por debajo del suelo de Trends.')


if __name__ == '__main__':
    main()
