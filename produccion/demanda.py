#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
demanda.py - Paso 0 del pipeline: validar que un tema tiene demanda ANTES de producirlo.

    python produccion/demanda.py "saudi arabia oil pipeline" --geo US
    python produccion/demanda.py "britain poorer than mississippi" --geo GB

Cuatro senales, todas gratis y sin cuenta (comprobadas el 2026-09-15):

  A - INTERES EN YOUTUBE    Google Trends con la propiedad "Busquedas de YouTube" (gprop='youtube'),
                            que es la que importa: mide lo que la gente busca DENTRO de YouTube, no
                            en la web. Da nivel y direccion (sube o baja).
  B - IDEA PROBADA          La misma idea pego en anios distintos? (yt-dlp)
  C - LA OLA                Sigue viva o ya paso? Ultimos 7 dias en YouTube.
  D - EL HUECO              Quien ocupa la ola: medios o creadores?

Ademas, `--titulo "a,b,c"` compara hasta 5 terminos candidatos por interes de busqueda EN YOUTUBE
y dice cual va adelante en el titulo y en la miniatura (regla 27). Ejemplo real: en US, 'national
debt' marca 39,2 y 'debt default' 2,2 - el titulo dice national debt, no default.

La senal D es la que faltaba y la que explica el 14-sep: el video de diesel/Saudi tenia
la ola ABIERTA (Fox 99k, 7NEWS 108k, Bloomberg 46k el mismo dia) y aun asi hizo 4 vistas.
El tema era bueno; el problema fue entrar a competir con Bloomberg en una noticia de ultima
hora. Contra un medio establecido, un canal chico no gana la busqueda de la noticia: gana el
angulo que el medio no da.

Ver `canal/MONETIZACION_2027.md` y la regla del paso 0 en la skill paper-trail-video.
"""

import argparse
import json
import re
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta

NS = '{https://trends.google.com/trending/rss}'

# Cabeceras de medios establecidos. Si estos ocupan la ola, la busqueda de la noticia
# ya tiene dueno y no somos nosotros.
MEDIOS = [
    'bbc', 'reuters', 'bloomberg', 'cnbc', 'cnn', 'fox', 'al jazeera', 'dw ', 'dw news',
    'abc news', 'nbc', 'cbs', 'sky news', 'guardian', 'the times', 'wsj', 'wall street',
    'pbs', 'afp', 'associated press', ' ap ', 'ft.com', 'financial times', 'ndtv',
    'channel 4', 'euronews', 'france 24', 'the economist', 'newsweek', 'forbes',
    'business standard', 'times now', 'india today', 'msnbc', 'npr', 'telegraph',
    'independent', 'mirror', 'express', 'daily mail', 'usa today', 'washington post',
    'new york times', 'nytimes', 'yahoo finance', 'wion', 'firstpost', 'global news',
    'ktla', 'king 5', 'kvue', 'whas', 'wfaa', '7news', '9news', 'itv', 'gb news',
]

UA = {'User-Agent': 'Mozilla/5.0 (paper-trail demanda.py)'}


def _print(s=''):
    """Imprime sin morir por la consola de Windows (cp1252)."""
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode('ascii', 'replace').decode('ascii'))


# Afiliadas locales de EE.UU.: WQAD, KVUE, WHAS, KTLA... empiezan por K o W + 2-3 mayusculas.
# Heuristica deliberadamente generosa: un falso positivo solo nos vuelve mas cautos.
AFILIADA = re.compile(r'^[KW][A-Z]{2,3}\b')


def es_medio(canal):
    c = (canal or '').lower()
    if any(m in c for m in MEDIOS):
        return True
    return bool(AFILIADA.match((canal or '').strip())) and len((canal or '').split()) <= 3


# ---------------------------------------------------------------- SENAL A

def _trends(kws, geo, timeframe='today 12-m'):
    """Google Trends con la propiedad 'Busquedas de YouTube'. Devuelve el DataFrame o None."""
    try:
        import warnings
        warnings.filterwarnings('ignore')
        from pytrends.request import TrendReq
    except ImportError:
        return None, 'pytrends no instalado (pip install pytrends)'
    try:
        p = TrendReq(hl='en-US', tz=0)
        p.build_payload(kws[:5], timeframe=timeframe, geo=geo, gprop='youtube')
        df = p.interest_over_time()
        if df is None or df.empty:
            return None, 'Trends no devolvio datos para ese termino'
        return df, None
    except Exception as e:
        # Google devuelve 429 cuando se le pide demasiado seguido.
        return None, f'Trends no respondio ({type(e).__name__}); se sigue sin esta senal'


VACIAS = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'of', 'to', 'in', 'on', 'for', 'its',
          'it', 'this', 'that', 'what', 'why', 'how', 'when', 'who', 'and', 'or', 'not',
          'cannot', 'can', 'will', 'would', 'has', 'have', 'does', 'do', 'be', 'been'}


def nucleo(frase, n=2):
    """Trends no entiende frases largas: necesita el termino corto. De 'the us cannot repay
    its national debt' saca 'national debt'."""
    palabras = [p for p in re.findall(r"[\w']+", frase.lower()) if p not in VACIAS]
    return ' '.join(palabras[-n:]) if palabras else frase


def senal_a(tema, geo, kw=None):
    """Interes de busqueda DENTRO de YouTube: nivel y direccion.

    Es la propiedad que importa. La busqueda web mide a gente que lee un articulo y se va;
    esta mide a gente que busca un VIDEO, que es la que nos da horas de visualizacion."""
    termino = kw or tema
    df, err = _trends([termino], geo)
    if df is None and not kw:
        # la frase larga no tiene volumen: reintentar con el nucleo
        termino = nucleo(tema)
        if termino != tema:
            df, err = _trends([termino], geo)
    if df is None:
        return None, err
    usado = termino
    col = df.columns[0]
    serie = df[col][~df.get('isPartial', False).astype(bool)] if 'isPartial' in df else df[col]
    if len(serie) < 8:
        return None, 'serie demasiado corta'
    medio = float(serie.mean())
    reciente = float(serie.tail(4).mean())
    previo = float(serie.tail(12).head(8).mean()) if len(serie) >= 12 else medio
    if reciente > previo * 1.25:
        direccion = 'SUBIENDO'
    elif reciente < previo * 0.75:
        direccion = 'BAJANDO'
    else:
        direccion = 'estable'
    return {'medio': medio, 'reciente': reciente, 'direccion': direccion,
            'pico': float(serie.max()), 'termino': usado}, None


def tendencias_del_dia(geo):
    """RSS de trending del pais. Contexto suelto para cuando NO se sabe que buscar;
    viene cargado de queries de navegacion ('latest news', 'stock market today')."""
    url = f'https://trends.google.com/trending/rss?geo={geo}'
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            root = ET.fromstring(r.read())
    except Exception as e:
        return None, f'no se pudo leer ({e})'
    out = []
    for it in root.iter('item'):
        out.append((it.findtext(NS + 'approx_traffic') or '?', it.findtext('title') or ''))
    return out, None


def comparar_titulos(terminos, geo):
    """Regla 27: cual es LA palabra que se busca. Medido en YouTube, no en la web."""
    df, err = _trends(terminos, geo)
    if df is None:
        return None, err
    cols = [c for c in df.columns if c != 'isPartial']
    doce = df[cols].mean().sort_values(ascending=False)
    cuatro = df[cols].tail(4).mean().sort_values(ascending=False)
    return {'12m': doce, '4sem': cuatro}, None


# ---------------------------------------------------------------- yt-dlp

def buscar_youtube(query, n=20):
    """Devuelve [{fecha, vistas, canal, titulo}] via yt-dlp. Requiere una peticion por
    video (flat-playlist no trae ni fecha ni vistas en las busquedas)."""
    cmd = [
        'yt-dlp', '--no-update', '--skip-download', '--ignore-errors',
        '--print', '%(upload_date)s\t%(view_count)s\t%(channel)s\t%(title)s',
        f'ytsearch{n}:{query}',
    ]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
                           encoding='utf-8', errors='replace')
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        _print(f'  !! yt-dlp fallo: {e}')
        return []
    res = []
    for ln in (p.stdout or '').splitlines():
        parts = ln.split('\t')
        if len(parts) < 4:
            continue
        fecha, vistas, canal, titulo = parts[0], parts[1], parts[2], '\t'.join(parts[3:])
        if not re.fullmatch(r'\d{8}', fecha or ''):
            continue
        try:
            v = int(vistas)
        except (TypeError, ValueError):
            continue
        res.append({'fecha': fecha, 'vistas': v, 'canal': canal, 'titulo': titulo})
    return res


# ---------------------------------------------------------------- SENAL B

def senal_b(videos, umbral=300_000):
    """Idea probada = la misma idea pego en anios DISTINTOS. Un solo exito es
    una casualidad; tres anios seguidos es demanda estructural."""
    por_anio = defaultdict(int)
    mejor = {}
    for v in videos:
        anio = v['fecha'][:4]
        if v['vistas'] > por_anio[anio]:
            por_anio[anio] = v['vistas']
            mejor[anio] = v
    anios_ok = sorted(a for a, mx in por_anio.items() if mx >= umbral)
    return anios_ok, [mejor[a] for a in anios_ok]


# ---------------------------------------------------------------- SENAL C

def senal_c(videos, dias=7, umbral=20_000):
    """La ola. Medida en YouTube a proposito: la demanda que nos paga es la de
    YouTube, no la del buscador. Referencia real (Nepal, sep-2025): el pico cae
    entre el dia 1 y el 4 del evento (549k, 406k, 395k) y al dia 6 ya esta en
    104k/31k. La ventana de una noticia son 3-5 dias."""
    hoy = datetime.now()
    recientes = []
    for v in videos:
        try:
            d = datetime.strptime(v['fecha'], '%Y%m%d')
        except ValueError:
            continue
        edad = (hoy - d).days
        if edad <= dias:
            recientes.append(dict(v, edad=edad))
    recientes.sort(key=lambda x: -x['vistas'])
    viva = any(v['vistas'] >= umbral for v in recientes)
    return viva, recientes


# ---------------------------------------------------------------- SENAL D

def senal_d(videos):
    """DE QUIEN ES ESTE TEMA. La senal decisiva, calibrada contra los 8 largos del canal.

    No es cuantas vistas se llevan los medios, sino si en ese tema la audiencia premia
    a un CREADOR que explica o a un MEDIO que informa. Se mide comparando el mejor video
    de creador contra el mejor video de medio:

        tema        mejor creador        mejor medio      nos dio
        AfD         TLDR      611k       BBC     221k       478
        Falklands   OverSimp 29.8M       -                  278
        AI economia Econ Expl 1.18M      MS NOW  5.6k       250
        diesel      Steve Ram  92k       DW      713k         4

    Donde gana el creador, nuestro formato tiene sitio. Donde gana el medio, la audiencia
    va a buscar la noticia a Bloomberg y se va."""
    creadores = [v for v in videos if not es_medio(v['canal'])]
    medios = [v for v in videos if es_medio(v['canal'])]
    mejor_c = max(creadores, key=lambda x: x['vistas']) if creadores else None
    mejor_m = max(medios, key=lambda x: x['vistas']) if medios else None
    if not mejor_c:
        return 'medios', 0.0, mejor_c, mejor_m
    if not mejor_m:
        return 'creadores', 99.0, mejor_c, mejor_m
    ratio = mejor_c['vistas'] / max(mejor_m['vistas'], 1)
    if ratio >= 1.5:
        dueno = 'creadores'
    elif ratio <= 0.7:
        dueno = 'medios'
    else:
        dueno = 'disputado'
    return dueno, ratio, mejor_c, mejor_m


# ---------------------------------------------------------------- veredicto

def veredicto(anios_ok, ola_viva, dueno, ratio):
    """Primero se pregunta de quien es el tema; solo despues, si hay prisa."""
    probada = len(anios_ok) >= 2

    if dueno == 'medios':
        return 'NO - ES DE LOS MEDIOS', (
            f'El video mas visto del tema es de un medio y le saca {1/max(ratio,0.01):.1f}x al mejor '
            'creador. La audiencia de este tema quiere la noticia, no la explicacion: va a Bloomberg '
            'y se va. Es el caso exacto del video de diesel del 14-sep (4 vistas) con la ola abierta. '
            'Si aun asi interesa, va al diario o al Brief, nunca a un Dispatch de 20 minutos.')

    if dueno == 'disputado':
        return 'GRIS - SOLO CON ANGULO', (
            'Creadores y medios empatan. Se puede entrar, pero NO con el video del hecho: solo con lo '
            'que el medio no da (el recibo, el mecanismo, el precedente). Si el titulo promete la '
            'noticia, perdemos contra la cabecera.')

    # dueno == creadores
    if probada:
        return 'LUZ VERDE - EVERGREEN', (
            f'El tema es de los creadores (x{ratio:.1f}) y la idea pego en {len(anios_ok)} anios '
            'distintos. Es el mejor caso posible: demanda estructural, sin reloj. Se produce cuando '
            'convenga y se puede repetir (Malvinas y IA, nuestros numeros 2 y 3, son de esta clase).')
    if ola_viva:
        return 'VERDE CON RELOJ', (
            f'El tema es de los creadores (x{ratio:.1f}) y la ola esta abierta, pero la idea no tiene '
            'historial: es reactiva. La ventana medida en Nepal es de 3 a 5 dias desde el hecho '
            '(pico 549k-406k-395k los dias 1-4; al dia 6 ya 104k). Si no sale en esa ventana, no sale.')
    return 'NO - SIN DEMANDA', (
        'El tema es de los creadores pero ni hay idea probada ni ola abierta. Nadie lo esta buscando '
        'y nadie demostro que funcione: no producir.')


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description='Paso 0: validar demanda antes de producir.')
    ap.add_argument('tema', help='la frase tal como la buscaria el espectador')
    ap.add_argument('--geo', default='US', help='pais para las tendencias del dia (US, GB, ...)')
    ap.add_argument('-n', type=int, default=20, help='cuantos videos mirar (def. 20)')
    ap.add_argument('--kw', help='termino corto para Trends si el automatico no acierta')
    ap.add_argument('--titulo', help='compara hasta 5 terminos separados por coma (regla 27)')
    ap.add_argument('--hoy', action='store_true', help='ademas, que se busca hoy en el pais (RSS)')
    ap.add_argument('--json', action='store_true', help='salida en JSON')
    a = ap.parse_args()

    _print(f'== DEMANDA · "{a.tema}" · geo={a.geo} · {datetime.now():%Y-%m-%d %H:%M} ==')

    # --titulo: comparar candidatos y salir
    if a.titulo:
        terminos = [t.strip() for t in a.titulo.split(',') if t.strip()][:5]
        _print(f'\n-- LA PALABRA DEL TITULO · interes de busqueda EN YOUTUBE ({a.geo})')
        comp, err = comparar_titulos(terminos, a.geo)
        if err:
            _print(f'   {err}')
            sys.exit(1)
        _print('   12 meses            ultimas 4 semanas')
        d12, d4 = comp['12m'], comp['4sem']
        for i in range(len(d12)):
            _print(f'   {d12.iloc[i]:6.1f} | {d12.index[i][:22]:22}   {d4.iloc[i]:6.1f} | {d4.index[i][:22]}')
        _print(f'\n   -> al titulo y a la miniatura va: "{d4.index[0]}"')
        return

    # A
    _print(f'\n-- A · interes de busqueda DENTRO de YouTube ({a.geo})')
    ia, err = senal_a(a.tema, a.geo, a.kw)
    if err:
        _print(f'   {err}')
    else:
        extra = f'  [termino: "{ia["termino"]}"]' if ia['termino'] != a.tema else ''
        _print(f'   nivel medio 12 meses: {ia["medio"]:.1f}   ultimas 4 semanas: {ia["reciente"]:.1f}'
               f'   (pico {ia["pico"]:.0f}){extra}')
        _print(f'   direccion: {ia["direccion"]}')

    if a.hoy:
        _print(f'\n-- que se busca hoy en {a.geo} (contexto suelto, no veredicto)')
        trends, err2 = tendencias_del_dia(a.geo)
        if err2:
            _print(f'   {err2}')
        else:
            for tr, ti in trends[:8]:
                _print(f'   {tr:>8} | {ti}')

    # datos
    _print(f'\n-- consultando YouTube ({a.n} resultados)...')
    videos = buscar_youtube(a.tema, a.n)
    if not videos:
        _print('   sin resultados utilizables. Probar otra frase (la que buscaria el espectador).')
        sys.exit(1)

    # B
    anios_ok, mejores = senal_b(videos)
    _print(f'\n-- B · idea probada: {len(anios_ok)} anio(s) con un video > 300k')
    for v in sorted(mejores, key=lambda x: x['fecha']):
        _print(f'   {v["fecha"][:4]} | {v["vistas"]:>9,} | {v["canal"][:18]:18} | {v["titulo"][:46]}')
    if not anios_ok:
        top = sorted(videos, key=lambda x: -x['vistas'])[:3]
        _print('   (nada supera 300k; lo mas alto:)')
        for v in top:
            _print(f'   {v["fecha"][:4]} | {v["vistas"]:>9,} | {v["canal"][:18]:18} | {v["titulo"][:46]}')

    # C
    ola_viva, recientes = senal_c(videos)
    _print(f'\n-- C · la ola (ultimos 7 dias): {"ABIERTA" if ola_viva else "cerrada"}')
    for v in recientes[:6]:
        marca = 'medio ' if es_medio(v['canal']) else 'creador'
        _print(f'   hace {v["edad"]}d | {v["vistas"]:>9,} | {marca} | {v["canal"][:16]:16} | {v["titulo"][:38]}')
    if not recientes:
        _print('   nadie publico sobre esto en 7 dias.')

    # D
    dueno, ratio, mejor_c, mejor_m = senal_d(videos)
    _print(f'\n-- D · de quien es el tema: {dueno.upper()}' +
           (f' (el mejor creador le saca x{ratio:.1f} al mejor medio)' if mejor_c and mejor_m
            else ''))
    if mejor_c:
        _print(f'   creador | {mejor_c["vistas"]:>9,} | {mejor_c["canal"][:18]:18} | {mejor_c["titulo"][:42]}')
    if mejor_m:
        _print(f'   medio   | {mejor_m["vistas"]:>9,} | {mejor_m["canal"][:18]:18} | {mejor_m["titulo"][:42]}')

    # veredicto
    v, razon = veredicto(anios_ok, ola_viva, dueno, ratio)
    _print(f'\n== VEREDICTO: {v}')
    for ln in _envolver(razon, 92):
        _print(f'   {ln}')

    if a.json:
        _print('\n' + json.dumps({
            'tema': a.tema, 'geo': a.geo, 'anios_probados': anios_ok,
            'ola_viva': ola_viva, 'dueno': dueno, 'ratio': round(ratio, 2), 'veredicto': v,
        }, ensure_ascii=False, indent=2))


def _envolver(texto, ancho):
    palabras, linea, out = texto.split(), '', []
    for p in palabras:
        if len(linea) + len(p) + 1 > ancho:
            out.append(linea)
            linea = p
        else:
            linea = f'{linea} {p}'.strip()
    if linea:
        out.append(linea)
    return out


if __name__ == '__main__':
    main()
