# -*- coding: utf-8 -*-
"""Los dos puntajes del Radar: importancia (aritmetica pura) y video_score (oportunidad de video),
mas las banderas que frenan la automatizacion y el corte en categorias.

Funciones PURAS: reciben dicts, no tocan la base, no hacen red, no importan nada del repo.
El reloj entra por parametro (`ahora`) para que el autotest sea determinista; si no se pasa, se
usa datetime.now(timezone.utc).

LO UNICO QUE HAY QUE ENTENDER DE ESTE MODULO (RADAR.md 5 y 6):

    BBC, Yahoo y veinte medios mas publicando el mismo cable de Reuters son UNA fuente
    independiente, no veinte.

Por eso la independencia NO se cuenta sobre articulos sino sobre CUBOS DE ORIGEN:
  - articulo con wire_origin           -> cubo 'wire:<agencia>'   (todos los que levanten ese
                                          cable caen en el MISMO cubo, sean uno o cuarenta)
  - articulo de fuente con reporteria propia (wire_propio) y sin wire -> cubo 'src:<source_id>'
  - articulo de un republicador (wire_propio=False) sin wire detectado -> NO acredita origen:
    no se puede atribuir a nadie. Cuenta para cobertura y velocidad, no para independencia.
  - y como red de seguridad: dos cubos con titulares de simhash casi identico (<= UMBRAL_SIMHASH
    bits de distancia) se FUNDEN, porque eso es el mismo cable con la deteccion de wire fallada.

Ante la duda el modulo SUBCUENTA. Un `fact` de menos es barato; un `fact` que en realidad dijo
una sola redaccion cuesta el canal.

El resto de los componentes (cross_bloc, velocidad) se calcula sobre TODOS los articulos, y es a
proposito: que TASS levante el cable de Reuters no agrega independencia, pero si dice que la
noticia cruzo a otro espacio informativo, que es exactamente lo que mide cross_bloc.

Formula de importancia, al pie de RADAR.md 6:

    100 * ( 0.22 fuentes_indep + 0.18 cross_bloc + 0.15 tier + 0.15 velocidad
          + 0.15 actores       + 0.10 dominio    + 0.05 primaria )

Las dos funciones de puntaje devuelven SIEMPRE (entero 0..100, desglose) para poder depurarlas.
En el desglose, las claves sin '_' adelante son los componentes; las que empiezan con '_' son
metadatos (total, bruto, cubos de origen, bloques, avisos).

Autotest:  python radar/puntajes.py --autotest     (o  python -m radar.puntajes --autotest)
"""
from __future__ import annotations
import json, math, os, re, sys, unicodedata
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------- pesos y tablas fijas

PESOS = {'fuentes_indep': 0.22, 'cross_bloc': 0.18, 'tier': 0.15, 'velocidad': 0.15,
         'actores': 0.15, 'dominio': 0.10, 'primaria': 0.05}          # suma 1.00, RADAR.md 6
ORDEN = ('fuentes_indep', 'cross_bloc', 'tier', 'velocidad', 'actores', 'dominio', 'primaria')

TOPE_INDEP = 8          # mas de 8 origenes distintos no agrega nada: ya es "todo el mundo"
UMBRAL_SIMHASH = 3      # bits de distancia para considerar dos titulares el mismo cable
VENTANA_VELOCIDAD = 3.0 # horas de cada mitad de la comparacion
TOPE_VELOCIDAD = 4.0    # x4 respecto de la ventana previa ya es "explotando"

# tier NO es confianza (fuentes.json _meta): pondera cuanto pesa que ESA redaccion lo cubra
TIER_PESO = {1: 1.0, 2: 0.72, 3: 0.45}
TIER_DEFECTO = 0.45

# Los 7 bloques de RADAR.md 6 / tabla narrative. El denominador es 7 y no se toca.
BLOQUES = ('western', 'russian', 'chinese', 'arab', 'israeli', 'apac', 'latam')
# russian_ind (Meduza, Moscow Times) es prensa rusa: suma al bloque ruso. El resto de los
# source_type de fuentes.json (official, osint, ukrainian, iranian, aggregator) NO son un bloque
# de los 7: se reportan en _bloques_no_contados para que se vea, pero no puntuan.
ALIAS_BLOQUE = {'russian_ind': 'russian'}

# peso de actores. US/CN/RU = 1.0 . DE/FR/GB/JP/IN = 0.8 . el resto, escalado.
PESO_PAIS = {
    'US': 1.00, 'CN': 1.00, 'RU': 1.00,
    'DE': 0.80, 'FR': 0.80, 'GB': 0.80, 'JP': 0.80, 'IN': 0.80,
    'IL': 0.70, 'IR': 0.70, 'UA': 0.70, 'TW': 0.70, 'SA': 0.70, 'KP': 0.70, 'TR': 0.70,
    'IT': 0.60, 'ES': 0.60, 'PL': 0.60, 'CA': 0.60, 'AU': 0.60, 'BR': 0.60, 'KR': 0.60,
    'MX': 0.55, 'NL': 0.55, 'EG': 0.55, 'QA': 0.55, 'AE': 0.55, 'PK': 0.55, 'ID': 0.55,
    'AR': 0.50, 'VE': 0.50, 'SY': 0.50, 'LB': 0.50, 'YE': 0.50, 'NG': 0.50, 'ZA': 0.50,
    'CL': 0.40, 'CO': 0.40, 'PE': 0.40, 'NZ': 0.40, 'PH': 0.40, 'VN': 0.40, 'TH': 0.40,
}
PESO_PAIS_DEFECTO = 0.35


# Agrupaciones geograficas. Las tres primeras son los bloques del video diario
# (videos/DAILY/DIARIO.md §4); las demas sirven para filtrar en el MCP.
REGIONES = {
    "powers":      ["US", "CN", "RU", "DE", "FR", "GB", "EU", "UA", "PL", "TR", "IT", "ES", "NL"],
    "south":       ["AR", "BR", "CL", "UY", "PY", "BO", "PE", "CO", "VE", "EC", "MX", "CU", "NI"],
    "pacific":     ["AU", "NZ", "JP", "KR", "TW", "PH", "ID", "VN", "TH", "MY", "SG", "IN", "PG"],
    "europe":      ["DE", "FR", "GB", "IT", "ES", "PL", "NL", "BE", "SE", "NO", "FI", "DK", "EU",
                    "UA", "RO", "HU", "CZ", "AT", "PT", "GR", "IE", "CH"],
    "middle_east": ["IL", "IR", "SA", "AE", "QA", "EG", "JO", "LB", "SY", "IQ", "YE", "TR", "PS"],
    "africa":      ["ZA", "NG", "ET", "KE", "EG", "MA", "DZ", "SD", "LY", "GH", "TZ", "ML", "CD"],
    "north_america": ["US", "CA", "MX"],
}


def region_de(paises):
    """Primer bloque del video diario que toca alguno de estos paises. Por defecto, powers."""
    s = set(paises or [])
    for nombre in ("south", "pacific", "powers"):
        if s & set(REGIONES[nombre]):
            return nombre
    return "powers"

# actores que no son paises (organismos) y lideres que se resuelven a su pais
PESO_ACTOR = {'NATO': 0.90, 'OTAN': 0.90, 'EU': 0.90, 'EUROPEAN UNION': 0.90, 'UE': 0.90,
              'FED': 0.85, 'FEDERAL RESERVE': 0.85, 'G7': 0.80, 'OPEC': 0.80, 'OPEP': 0.80,
              'ECB': 0.80, 'BCE': 0.80, 'IMF': 0.75, 'FMI': 0.75, 'BRICS': 0.70, 'WTO': 0.70,
              'OMC': 0.70, 'UN': 0.70, 'ONU': 0.70, 'IAEA': 0.65, 'OIEA': 0.65,
              'HAMAS': 0.60, 'HEZBOLLAH': 0.60, 'HOUTHIS': 0.55, 'WAGNER': 0.55,
              'TALIBAN': 0.55, 'MERCOSUR': 0.45, 'ASEAN': 0.50, 'AUKUS': 0.60, 'QUAD': 0.60}
NOMBRE_PAIS = {
    'UNITED STATES': 'US', 'USA': 'US', 'U.S.': 'US', 'AMERICA': 'US', 'WASHINGTON': 'US',
    'WHITE HOUSE': 'US', 'PENTAGON': 'US', 'TRUMP': 'US', 'BIDEN': 'US', 'RUBIO': 'US',
    'CHINA': 'CN', 'BEIJING': 'CN', 'PEKIN': 'CN', 'XI JINPING': 'CN', 'XI': 'CN', 'PLA': 'CN',
    'RUSSIA': 'RU', 'KREMLIN': 'RU', 'MOSCOW': 'RU', 'MOSCU': 'RU', 'PUTIN': 'RU', 'LAVROV': 'RU',
    'GERMANY': 'DE', 'BERLIN': 'DE', 'MERZ': 'DE', 'SCHOLZ': 'DE',
    'FRANCE': 'FR', 'PARIS': 'FR', 'MACRON': 'FR',
    'UNITED KINGDOM': 'GB', 'UK': 'GB', 'BRITAIN': 'GB', 'LONDON': 'GB', 'STARMER': 'GB',
    'JAPAN': 'JP', 'TOKYO': 'JP', 'INDIA': 'IN', 'MODI': 'IN', 'NEW DELHI': 'IN',
    'ISRAEL': 'IL', 'NETANYAHU': 'IL', 'IDF': 'IL', 'IRAN': 'IR', 'TEHRAN': 'IR', 'IRGC': 'IR',
    'UKRAINE': 'UA', 'KYIV': 'UA', 'ZELENSKY': 'UA', 'ZELENSKYY': 'UA',
    'TAIWAN': 'TW', 'TAIPEI': 'TW', 'SAUDI ARABIA': 'SA', 'RIYADH': 'SA', 'MBS': 'SA',
    'NORTH KOREA': 'KP', 'KIM JONG UN': 'KP', 'SOUTH KOREA': 'KR', 'TURKEY': 'TR',
    'ERDOGAN': 'TR', 'ITALY': 'IT', 'MELONI': 'IT', 'SPAIN': 'ES', 'POLAND': 'PL',
    'CANADA': 'CA', 'AUSTRALIA': 'AU', 'BRAZIL': 'BR', 'LULA': 'BR',
    'ARGENTINA': 'AR', 'MILEI': 'AR', 'VENEZUELA': 'VE', 'MADURO': 'VE',
    'EL SALVADOR': 'SV', 'BUKELE': 'SV', 'MEXICO': 'MX', 'SHEINBAUM': 'MX',
    'NEW ZEALAND': 'NZ', 'PHILIPPINES': 'PH', 'VIETNAM': 'VN', 'INDONESIA': 'ID',
}
PESO_ACTOR_DEFECTO = 0.30

# dominio: la unica categoria que aporta el LLM a la formula (RADAR.md 6). Categoria, no numero.
# OJO: las claves tienen que cubrir el vocabulario que REALMENTE emite radar/extraccion.py, que
# es un enum cerrado ("military_escalation", "domestic_politics", "other", ...). Si una clave del
# enum falta aca, ese evento cae en DOMINIO_DEFECTO y un hecho militar puntua igual que uno menor.
DOMINIO_PESO = {'nuclear': 1.00, 'militar': 0.95, 'guerra': 0.95, 'military': 0.95,
                'military_escalation': 0.95,
                'seguridad': 0.85, 'security': 0.85, 'sanciones': 0.80, 'sanctions': 0.80,
                'energia': 0.80, 'energy': 0.80, 'economia': 0.75, 'economy': 0.75,
                'finanzas': 0.75, 'finance': 0.75,
                'comercio': 0.75, 'trade': 0.75, 'tecnologia': 0.70, 'tech': 0.70,
                'diplomacia': 0.65, 'diplomacy': 0.65, 'diplomatic': 0.65,
                'politica': 0.60, 'politics': 0.60, 'domestic_politics': 0.60,
                'elecciones': 0.60, 'elections': 0.60,
                'legal': 0.55, 'migracion': 0.55, 'migration': 0.55,
                'clima': 0.45, 'climate': 0.45, 'otro': 0.30, 'other': 0.30,
                'alto': 1.00, 'medio': 0.60, 'bajo': 0.30}
DOMINIO_DEFECTO = 0.50   # sin categoria del LLM: neutro, y queda avisado en el desglose

CORTES = ((80, 'breaking'), (60, 'high'), (40, 'relevant'))   # RADAR.md 6: 80+ / 60-79 / 40-59 / <40

# ---------------------------------------------------------------- video_score

PESOS_VIDEO = {'importancia': 0.25, 'conflicto': 0.15, 'sorpresa': 0.12, 'explicabilidad': 0.12,
               'consecuencias': 0.11, 'competencia': 0.10, 'mapa': 0.08, 'assets': 0.07}
ORDEN_VIDEO = ('importancia', 'conflicto', 'sorpresa', 'explicabilidad', 'consecuencias',
               'competencia', 'mapa', 'assets')
CATEGORIA = {'alto': 1.0, 'alta': 1.0, 'high': 1.0, 'si': 1.0, 'medio': 0.6, 'media': 0.6,
             'medium': 0.6, 'bajo': 0.25, 'baja': 0.25, 'low': 0.25, 'no': 0.0, 'ninguno': 0.0}
TOPE_ASSETS = 6

# ---------------------------------------------------------------- banderas (MONETIZACION / IDEOLOGIA)

DIAS_EVENTO_SENSIBLE = 7

# Marcadores fuertes: si aparecen y el hecho es de los ultimos 7 dias, bandera. La lista es corta
# a proposito: la compuerta invertida de RADAR.md 10 solo sirve si NO se dispara todos los dias,
# y la cobertura de guerra rutinaria (frente, drones, sanciones) no es "atentado o masacre".
PAT_ATENTADO = re.compile(r'\b('
    r'terror attack|terrorist attack|terror plot|atentado|atentados|'
    r'suicide bomb\w*|car bomb\w*|truck bomb\w*|ied attack|'
    r'bombing|bombings|mass shooting|school shooting|shooting spree|gunman|gunmen|'
    r'stabbing|stabbings|knife attack|tiroteo|apunalamiento|'
    r'massacre|massacres|masacre|matanza|atrocity|atrocities|ethnic cleansing|genocide|genocidio|'
    r'hostage-taking|hostages taken|toma de rehenes|beheading|decapitacion'
    r')\b', re.I)
# Marcadores debiles: solo cuentan si ademas hay un blanco civil en el mismo texto.
PAT_VICTIMAS = re.compile(r'\b(death toll|killed|dead|casualties|victims|wounded|muertos|'
                          r'fallecidos|heridos|victimas)\b', re.I)
PAT_BLANCO_CIVIL = re.compile(r'\b(civilians|civiles|school|schools|escuela|hospital|market|mercado|'
                              r'mosque|mezquita|church|iglesia|synagogue|sinagoga|worshippers|'
                              r'concert|festival|nightclub|commuters|crowd|bus stop|refugee camp|'
                              r'campo de refugiados|apartment block|residential)\b', re.I)
# IDEOLOGIA.md: cultura, aborto y genero se preguntan SIEMPRE antes de escribir.
PAT_IDEOLOGIA = re.compile(r'\b('
    r'abortion|aborto|pro-choice|pro-life|roe v wade|'
    r'gender|genero|transgender|trans rights|gender identity|gender-affirming|'
    r'lgbt|lgbtq|lgbtq\+|same-sex|matrimonio igualitario|drag|'
    r'culture war|guerra cultural|woke|blasphemy|blasfemia|'
    r'hijab|niqab|burqa|veil ban|sharia|velo islamico'
    r')\b', re.I)
# Persona privada nombrada: el LLM deberia marcarlo (ev['personas_privadas']); esto es la red.
PAT_PERSONA_PRIVADA = re.compile(
    r'\b(identified as|named as|the suspect,|the victim,|the gunman,|the attacker,|'
    r'identificado como|la victima,|el sospechoso,)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})')

MOTIVOS = {   # orden = severidad, el primero manda en motivo_bandera
    'evento_sensible': 'atentado o masacre de los ultimos %d dias (MONETIZACION.md 1: eventos sensibles)' % DIAS_EVENTO_SENSIBLE,
    'persona_privada': 'nombra a una persona privada (MONETIZACION.md 1: acoso y ataques a personas)',
    'fact_sin_respaldo': 'hay un fact con una sola fuente independiente y sin documento oficial (RADAR.md 5)',
    'ideologia_preguntar': 'toca cultura, aborto o genero: IDEOLOGIA.md manda preguntar antes de escribir',
}
ORDEN_MOTIVOS = ('evento_sensible', 'persona_privada', 'fact_sin_respaldo', 'ideologia_preguntar')


# ================================================================ utilidades

def _aware(dt):
    """Toda hora es UTC aware. Naive -> se asume UTC. No-datetime -> None."""
    if not isinstance(dt, datetime):
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _ahora(ahora=None):
    return _aware(ahora) or datetime.now(timezone.utc)


def _sin_tildes(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s or '') if unicodedata.category(c) != 'Mn')


def _indice_fuentes(fuentes):
    """Acepta el dict {source_id: fuente} del contrato, o una lista de fuentes (defensivo)."""
    if isinstance(fuentes, dict):
        return fuentes
    return {f.get('id'): f for f in (fuentes or []) if isinstance(f, dict)}


def _tipo_fuente(f):
    """fuentes.json usa 'tipo'; el esquema SQL usa 'source_type'. Se aceptan los dos."""
    return (f.get('source_type') or f.get('tipo') or '').strip().lower()


def _hamming(a, b):
    return bin((int(a) ^ int(b)) & ((1 << 64) - 1)).count('1')


def _clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else (hi if x > hi else x)


def _cat(v, defecto=None):
    """Categoria del LLM ('alto'/'medio'/'bajo') o float 0..1 -> float 0..1."""
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        return _clamp(float(v))
    if isinstance(v, str):
        k = _sin_tildes(v).strip().lower()
        if k in CATEGORIA:
            return CATEGORIA[k]
    return defecto


# ================================================================ cubos de origen: el corazon

def cubos_origen(articulos, fuentes, fusionar=True):
    """Agrupa los articulos en ORIGENES INDEPENDIENTES. Devuelve (cubos, avisos).

    cubos: {clave: {'arts': [...], 'tier': int|None, 'primaria': bool, 'fuentes': set}}
    Un cubo = una redaccion que reporto por su cuenta, o una agencia cuyo cable levantaron N medios.
    Los articulos que no acreditan origen (republicador sin wire detectado) quedan fuera de los
    cubos y se cuentan en avisos['sin_atribuir'].
    """
    idx = _indice_fuentes(fuentes)
    cubos, sin_atribuir = {}, 0
    for a in (articulos or []):
        sid = a.get('source_id') or ''
        f = idx.get(sid) or {}
        wire = (a.get('wire_origin') or '').strip().lower() or None
        if wire:
            clave = 'wire:' + wire                       # el cable manda sobre quien lo publica
        elif f.get('wire_propio', True):
            clave = 'src:' + (sid or a.get('url_hash') or '?')
        else:
            sin_atribuir += 1                            # republicador sin wire: no acredita a nadie
            continue
        c = cubos.setdefault(clave, {'arts': [], 'tier': None, 'primaria': False, 'fuentes': set()})
        c['arts'].append(a)
        c['fuentes'].add(sid)
        t = f.get('tier')
        if isinstance(t, int) and (c['tier'] is None or t < c['tier']):
            c['tier'] = t                                # del cubo vale el mejor tier que lo publico
        if f.get('primaria'):
            c['primaria'] = True

    fundidos = 0
    if fusionar and len(cubos) > 1:
        cubos, fundidos = _fundir_por_simhash(cubos)
    return cubos, {'sin_atribuir': sin_atribuir, 'cubos_fundidos': fundidos}


def _fundir_por_simhash(cubos):
    """Red de seguridad: dos cubos con titulares de simhash casi identico son el mismo cable con
    la deteccion de wire fallada. Se funden. Puede subcontar (dos redacciones que escriben el
    mismo titular literal), y eso es lo que se quiere: el error barato es hacia abajo."""
    claves = list(cubos)
    padre = {k: k for k in claves}

    def raiz(k):
        while padre[k] != k:
            padre[k] = padre[padre[k]]
            k = padre[k]
        return k

    hashes = {k: [a['title_simhash'] for a in cubos[k]['arts']
                  if isinstance(a.get('title_simhash'), int)] for k in claves}
    n = 0
    for i, ka in enumerate(claves):
        for kb in claves[i + 1:]:
            if raiz(ka) == raiz(kb):
                continue
            if any(_hamming(ha, hb) <= UMBRAL_SIMHASH for ha in hashes[ka] for hb in hashes[kb]):
                padre[raiz(kb)] = raiz(ka)
                n += 1
    if not n:
        return cubos, 0
    fusion = {}
    for k in claves:
        r = raiz(k)
        d = fusion.setdefault(r, {'arts': [], 'tier': None, 'primaria': False, 'fuentes': set()})
        d['arts'].extend(cubos[k]['arts'])
        d['fuentes'] |= cubos[k]['fuentes']
        d['primaria'] = d['primaria'] or cubos[k]['primaria']
        t = cubos[k]['tier']
        if isinstance(t, int) and (d['tier'] is None or t < d['tier']):
            d['tier'] = t
    return fusion, n


# ================================================================ componentes de importancia

def _c_fuentes_indep(cubos, avisos):
    """0.22 . Log-escalado, tope TOPE_INDEP. Esta es LA cuenta del modulo."""
    n = len(cubos)
    v = math.log(1 + min(n, TOPE_INDEP)) / math.log(1 + TOPE_INDEP) if n else 0.0
    return v, {'n_indep': n, 'tope': TOPE_INDEP, 'origenes': sorted(cubos),
               'sin_atribuir': avisos['sin_atribuir'], 'cubos_fundidos': avisos['cubos_fundidos']}


def _c_cross_bloc(articulos, fuentes):
    """0.18 . Cuantos de los 7 bloques cubren el hecho. Se cuenta sobre TODOS los articulos:
    que TASS levante el cable de Reuters no agrega independencia, pero si dice que la noticia
    cruzo al espacio informativo ruso, que es la senal que mide este componente."""
    idx = _indice_fuentes(fuentes)
    dentro, fuera = set(), set()
    for a in (articulos or []):
        t = _tipo_fuente(idx.get(a.get('source_id') or '') or {})
        if not t:
            continue
        t = ALIAS_BLOQUE.get(t, t)
        (dentro if t in BLOQUES else fuera).add(t)
    return len(dentro) / float(len(BLOQUES)), {'bloques': sorted(dentro),
                                               'bloques_no_contados': sorted(fuera),
                                               'de': len(BLOQUES)}


def _c_tier(cubos, articulos, fuentes):
    """0.15 . Promedio del tier de los ORIGENES (no de los articulos): veinte republicaciones
    tier 1 de un mismo cable no valen mas que el cable."""
    if cubos:
        pesos = [TIER_PESO.get(c['tier'], TIER_DEFECTO) for c in cubos.values()]
        return sum(pesos) / len(pesos), {'tiers': sorted(c['tier'] for c in cubos.values()
                                                         if c['tier'] is not None),
                                         'sobre': 'origenes'}
    idx = _indice_fuentes(fuentes)                      # sin origenes atribuibles: red minima
    sids = {a.get('source_id') for a in (articulos or [])}
    pesos = [TIER_PESO.get((idx.get(s) or {}).get('tier'), TIER_DEFECTO) for s in sids if s]
    v = (sum(pesos) / len(pesos)) if pesos else 0.0
    return v, {'tiers': [], 'sobre': 'articulos (ningun origen atribuible)'}


def _c_velocidad(articulos, ahora):
    """0.15 . Articulos de las ultimas 3 h sobre los de las 3 h previas, con tope.
    Suavizado de Laplace (+1 arriba y abajo): mide ACELERACION, no volumen. El volumen ya lo
    mide fuentes_indep, y si no se suaviza, veinte copias de un cable ganan por ruido."""
    t1 = ahora - timedelta(hours=VENTANA_VELOCIDAD)
    t0 = ahora - timedelta(hours=2 * VENTANA_VELOCIDAD)
    rec = prev = 0
    for a in (articulos or []):
        t = _aware(a.get('detected_at')) or _aware(a.get('published_at'))
        if t is None:
            continue
        if t >= t1:
            rec += 1
        elif t >= t0:
            prev += 1
    ratio = (rec + 1.0) / (prev + 1.0)
    return _clamp(min(ratio, TOPE_VELOCIDAD) / TOPE_VELOCIDAD), {
        'recientes': rec, 'previos': prev, 'ratio': round(ratio, 2),
        'ventana_h': VENTANA_VELOCIDAD, 'tope': TOPE_VELOCIDAD}


def _peso_de(nombre):
    """Pais, organismo o lider -> peso 0..1."""
    s = _sin_tildes(str(nombre or '')).strip().upper()
    if not s:
        return None, ''
    if len(s) == 2 and s in PESO_PAIS:
        return PESO_PAIS[s], s
    if s in NOMBRE_PAIS:
        c = NOMBRE_PAIS[s]
        return PESO_PAIS.get(c, PESO_PAIS_DEFECTO), c
    if s in PESO_ACTOR:
        return PESO_ACTOR[s], s
    for nom, c in NOMBRE_PAIS.items():                  # 'Xi Jinping visits' -> CN
        if len(nom) > 4 and nom in s:
            return PESO_PAIS.get(c, PESO_PAIS_DEFECTO), c
    for org, p in PESO_ACTOR.items():
        if len(org) > 2 and re.search(r'\b%s\b' % re.escape(org), s):
            return p, org
    return None, s


def _c_actores(ev):
    """0.15 . Tabla fija. El primero pesa 0.75 y el segundo 0.25: un evento bilateral entre dos
    potencias satura, uno de una sola potencia no (US solo = 0.75, US+CN = 1.0)."""
    pesos, resueltos, desconocidos = [], [], []
    for nombre in list(ev.get('paises') or []) + list(ev.get('actores') or []):
        p, clave = _peso_de(nombre)
        if p is None:
            desconocidos.append(clave or str(nombre))
            p = PESO_ACTOR_DEFECTO
        else:
            resueltos.append('%s=%.2f' % (clave, p))
        pesos.append(p)
    if not pesos:
        return 0.0, {'resueltos': [], 'desconocidos': [], 'nota': 'evento sin paises ni actores'}
    pesos.sort(reverse=True)
    p0 = pesos[0]
    p1 = pesos[1] if len(pesos) > 1 else 0.0
    return _clamp(0.75 * p0 + 0.25 * p1), {'resueltos': resueltos, 'desconocidos': desconocidos,
                                           'top2': [round(p0, 2), round(p1, 2)]}


def _c_dominio(ev):
    """0.10 . Lo unico que aporta el LLM a esta formula, y como categoria, no como numero.

    `dominio` HOY no viaja en el EVENTO: no es campo del contrato, no hay columna en esquema.sql
    y extraccion.py lo devuelve pero no lo guarda. Sin red, este componente valdria 0.50 fijo para
    el 100% de los eventos, o sea seria peso muerto. Por eso, si no hay `dominio`, se cae a
    `topics`, que SI es campo del contrato y SI se persiste, tomando el topic mas pesado (un hecho
    militar-y-diplomatico es un hecho militar). Cuando `dominio` exista, gana el.
    """
    d = ev.get('dominio')
    if d is None:
        mejor, cual = None, None
        for t in (ev.get('topics') or []):
            k = _sin_tildes(str(t)).strip().lower()
            p = DOMINIO_PESO.get(k)
            if p is not None and (mejor is None or p > mejor):
                mejor, cual = p, k
        if mejor is not None:
            return mejor, {'dominio': None, 'desde_topics': cual,
                           'nota': 'sin dominio: se uso el topic mas pesado'}
        return DOMINIO_DEFECTO, {'dominio': None, 'desde_topics': None,
                                 'nota': 'sin dominio ni topics conocidos: neutro'}
    if isinstance(d, (int, float)) and not isinstance(d, bool):
        return _clamp(float(d)), {'dominio': d, 'nota': 'numero, no categoria'}
    k = _sin_tildes(str(d)).strip().lower()
    if k in DOMINIO_PESO:
        return DOMINIO_PESO[k], {'dominio': k}
    return DOMINIO_DEFECTO, {'dominio': k, 'nota': 'categoria desconocida: neutro'}


def _c_primaria(cubos, articulos, fuentes):
    """0.05 . Fuente primaria del actor (el feed de la Comision, Casa Rosada, Federal Register)."""
    if any(c['primaria'] for c in cubos.values()):
        return 1.0, {'primaria': True}
    idx = _indice_fuentes(fuentes)
    if any(_tipo_fuente(idx.get(a.get('source_id') or '') or {}) == 'official'
           for a in (articulos or [])):
        return 0.5, {'primaria': False, 'nota': 'fuente official pero no marcada primaria'}
    return 0.0, {'primaria': False}


# ================================================================ los dos puntajes

def importancia(ev, articulos, fuentes, ahora=None, fusionar=True):
    """Formula de RADAR.md 6: 0.22 fuentes_indep + 0.18 cross_bloc + 0.15 tier
       + 0.15 velocidad + 0.15 actores + 0.10 dominio + 0.05 primaria.
       fuentes_indep cuenta wire_origin DISTINTOS (BBC+Yahoo con el mismo cable de
       Reuters = 1, no 2). Devuelve (0..100, desglose por componente).

    ev:        EVENTO (usa paises, actores, dominio). articulos: los del evento.
    fuentes:   {source_id: fuente} de fuentes.json (o lista; se indexa sola).
    ahora:     inyectable para que el autotest sea determinista. Por defecto, now(UTC).
    fusionar:  funde cubos con titulares de simhash casi identico (ver _fundir_por_simhash).
    """
    t = _ahora(ahora)
    arts = list(articulos or [])
    cubos, avisos = cubos_origen(arts, fuentes, fusionar=fusionar)

    valores = {}
    valores['fuentes_indep'] = _c_fuentes_indep(cubos, avisos)
    valores['cross_bloc'] = _c_cross_bloc(arts, fuentes)
    valores['tier'] = _c_tier(cubos, arts, fuentes)
    valores['velocidad'] = _c_velocidad(arts, t)
    valores['actores'] = _c_actores(ev or {})
    valores['dominio'] = _c_dominio(ev or {})
    valores['primaria'] = _c_primaria(cubos, arts, fuentes)

    desglose, bruto = {}, 0.0
    for k in ORDEN:
        v, detalle = valores[k]
        v = _clamp(v)
        aporta = PESOS[k] * v
        bruto += aporta
        desglose[k] = {'valor': round(v, 4), 'peso': PESOS[k], 'aporta': round(100 * aporta, 2),
                       'detalle': detalle}
    score = int(round(100 * _clamp(bruto)))
    desglose['_total'] = score
    desglose['_bruto'] = round(bruto, 4)
    desglose['_n_articulos'] = len(arts)
    desglose['_n_origenes'] = len(cubos)
    # SOLO-OFICIAL: si NINGUN medio lo cubrio y solo esta en boletines oficiales, es un
    # documento administrativo, no un acontecimiento. Medido el 2026-09-11: sin esta regla el
    # top del dia se llenaba de "Indonesia travel advice" (uk_fcdo) y "Federal Reserve Board
    # issues enforcement action", que no son noticia aunque vengan de fuente primaria tier 1.
    tipos = {(fuentes.get(a.get('source_id'), {}) or {}).get('source_type')
             or (fuentes.get(a.get('source_id'), {}) or {}).get('tipo')
             for a in (articulos or [])}
    solo_oficial = bool(tipos) and tipos <= {'official', None}
    desglose['_solo_oficial'] = solo_oficial
    if solo_oficial:
        score = min(score, 35)      # queda en watchlist: visible, pero nunca abre el programa
    desglose['_total'] = score
    desglose['_clase'] = clasificar(score)
    return score, desglose


def clasificar(importancia):
    """Corte de RADAR.md 6: 80-100 breaking . 60-79 high . 40-59 relevant . <40 low."""
    n = int(importancia or 0)
    for corte, nombre in CORTES:
        if n >= corte:
            return nombre
    return 'low'


def _c_competencia(n):
    """Ni cero ni multitud. Cero suele significar que no hay demanda; mucha, que se llega tarde.
    La franja del medio es donde el video tiene sentido (RADAR.md 6)."""
    n = int(n or 0)
    if n <= 0:
        return 0.25, 'sin competencia: probablemente no hay demanda'
    if n <= 2:
        return 0.70, 'poca competencia'
    if n <= 8:
        return 1.00, 'franja del medio: hay demanda y todavia hay lugar'
    if n <= 20:
        return 0.55, 'saturado'
    return 0.20, 'se llego tarde'


def video_score(ev, articulos, ctx):
    """ctx: {'mapa_disponible': bool, 'assets': int, 'competencia': int, 'llm': {...}}

    llm aporta categorias ('alto'/'medio'/'bajo'), no numeros: conflicto, sorpresa,
    explicabilidad, consecuencias. Si falta 'consecuencias', cae a ev['riesgo_escalada'].
    mapa_disponible y assets son senales de COSTE que solo salen del repo de Agustin
    (hojas de produccion/mapa_*.py y hits de indice_assets.py).

    La bandera requiere_agustin NO baja este puntaje (RADAR.md 6): no es un evento peor,
    es un evento que no se automatiza. Se reporta en el desglose y listo.
    """
    ev = ev or {}
    ctx = ctx or {}
    llm = ctx.get('llm') or {}
    avisos = []

    imp = ev.get('importancia')
    if imp is None:
        imp, _ = 0, None
        avisos.append('evento sin importancia calculada: el componente vale 0')
    v_imp = _clamp(float(imp) / 100.0)

    def cat(nombre, alterno=None):
        v = _cat(llm.get(nombre))
        if v is None and alterno is not None:
            v = _cat(alterno)
            if v is not None:
                avisos.append('%s: se uso riesgo_escalada' % nombre)
        if v is None:
            avisos.append('%s: sin categoria del LLM, neutro 0.5' % nombre)
            v = 0.5
        return v

    v_comp, nota_comp = _c_competencia(ctx.get('competencia'))
    n_assets = max(0, int(ctx.get('assets') or 0))      # negativo -> 0; math.log(1+n) reventaba
    v_assets = math.log(1 + min(n_assets, TOPE_ASSETS)) / math.log(1 + TOPE_ASSETS) if n_assets else 0.0

    valores = {
        'importancia': (v_imp, {'importancia': imp}),
        'conflicto': (cat('conflicto'), {'llm': llm.get('conflicto')}),
        'sorpresa': (cat('sorpresa'), {'llm': llm.get('sorpresa')}),
        'explicabilidad': (cat('explicabilidad'), {'llm': llm.get('explicabilidad')}),
        'consecuencias': (cat('consecuencias', ev.get('riesgo_escalada')),
                          {'llm': llm.get('consecuencias'), 'riesgo_escalada': ev.get('riesgo_escalada')}),
        'competencia': (v_comp, {'n': ctx.get('competencia'), 'nota': nota_comp}),
        'mapa': (1.0 if ctx.get('mapa_disponible') else 0.0,
                 {'mapa_disponible': bool(ctx.get('mapa_disponible'))}),
        'assets': (v_assets, {'hits': n_assets, 'tope': TOPE_ASSETS}),
    }

    desglose, bruto = {}, 0.0
    for k in ORDEN_VIDEO:
        v, detalle = valores[k]
        v = _clamp(v)
        aporta = PESOS_VIDEO[k] * v
        bruto += aporta
        desglose[k] = {'valor': round(v, 4), 'peso': PESOS_VIDEO[k],
                       'aporta': round(100 * aporta, 2), 'detalle': detalle}
    score = int(round(100 * _clamp(bruto)))
    desglose['_total'] = score
    desglose['_bruto'] = round(bruto, 4)
    desglose['_requiere_agustin'] = bool(ev.get('requiere_agustin'))
    desglose['_avisos'] = avisos
    # lo que el LLM haya propuesto viaja con el puntaje para que el brief lo imprima entero
    for k in ('angulos', 'titulos', 'pregunta_central'):
        if llm.get(k):
            desglose['_' + k] = llm[k]
    return score, desglose


# ================================================================ banderas

def banderas(ev, statements, ahora=None):
    """requiere_agustin segun MONETIZACION.md e IDEOLOGIA.md.

    Marca True si:
      1. atentado o masacre de los ultimos 7 dias  (MONETIZACION.md 1, eventos sensibles)
      2. tema donde IDEOLOGIA.md manda preguntar: cultura, aborto, genero
      3. un fact que quedo con una sola fuente independiente y sin documento oficial (RADAR.md 5)
      4. una persona privada nombrada  (MONETIZACION.md 1, acoso y ataques a personas)

    Sobre (3): la invariante del contrato acepta `fact` con n_indep=1 SI evidence=='official_doc'
    (la Comision publica su propio paquete de sanciones). Ese caso NO levanta bandera: si lo
    hiciera, la compuerta invertida de RADAR.md 10 se dispararia casi todos los dias y Agustin
    volveria a aprobar a mano, que es justo lo que la compuerta evita. Si el criterio tiene que ser
    literal ("una sola fuente, siempre"), es esta linea la que se cambia.

    Sobre (1): la fecha del hecho sale de ev['fecha_hecho'] o ev['first_detected']. Si no hay
    fecha, se asume reciente: el error barato es preguntar de mas.

    Devuelve (requiere_agustin, motivo_bandera). El motivo junta todas las razones con ' . ',
    la mas grave primero.
    """
    ev = ev or {}
    sts = list(statements or [])
    t = _ahora(ahora)
    motivos = []

    partes = [str(ev.get('titulo') or '')]
    partes += [str(x) for x in (ev.get('topics') or [])]
    partes += [str(x) for x in (ev.get('actores') or [])]
    textos_st = [str(s.get('texto') or '') for s in sts]
    partes += textos_st
    texto = _sin_tildes(' . '.join(partes))

    # 1. evento sensible reciente
    fecha = _aware(ev.get('fecha_hecho')) or _aware(ev.get('first_detected'))
    reciente = (fecha is None) or ((t - fecha) <= timedelta(days=DIAS_EVENTO_SENSIBLE))
    fuerte = bool(PAT_ATENTADO.search(texto))
    debil = bool(PAT_VICTIMAS.search(texto)) and bool(PAT_BLANCO_CIVIL.search(texto))
    if reciente and (fuerte or debil):
        motivos.append('evento_sensible')

    # 2. IDEOLOGIA.md: cultura, aborto, genero -> preguntar siempre
    if PAT_IDEOLOGIA.search(texto):
        motivos.append('ideologia_preguntar')

    # 3. fact que quedo solo
    for s in sts:
        if (s.get('tipo') == 'fact' and int(s.get('n_indep') or 0) < 2
                and s.get('evidence') != 'official_doc'):
            motivos.append('fact_sin_respaldo')
            break

    # 4. persona privada nombrada: primero lo que marco el LLM, despues la red lexica
    if ev.get('personas_privadas') or any(s.get('persona_privada') for s in sts):
        motivos.append('persona_privada')
    else:
        # se normaliza igual que `texto`: el patron esta escrito sin tildes y el nombre se captura
        # con [A-Z][a-z]+, asi que sobre el crudo "la victima, Juan Perez" no matchea nunca.
        for txt in [str(ev.get('titulo') or '')] + textos_st:
            if PAT_PERSONA_PRIVADA.search(_sin_tildes(txt)):
                motivos.append('persona_privada')
                break

    if not motivos:
        return False, None
    orden = [m for m in ORDEN_MOTIVOS if m in motivos]
    return True, ' . '.join(MOTIVOS[m] for m in orden)


# ================================================================ depuracion

def formatear_desglose(desglose, orden=ORDEN):
    """Una linea por componente, para mirar por que salio ese numero."""
    out = ['  %-15s %5.3f x %.2f = %5.2f' % (k, desglose[k]['valor'], desglose[k]['peso'],
                                             desglose[k]['aporta'])
           for k in orden if desglose.get(k)]
    out.append('  %-15s %23s' % ('TOTAL', desglose.get('_total')))
    return '\n'.join(out)


def comparar_desgloses(da, db, ta='A', tb='B', orden=ORDEN):
    """Los dos desgloses lado a lado. Es la vista que sirve cuando un puntaje sorprende."""
    L = []
    L.append('  %-15s | %-22s | %-22s' % ('componente', ta, tb))
    L.append('  %-15s-+-%-22s-+-%-22s' % ('-' * 15, '-' * 22, '-' * 22))
    for k in orden:
        a, b = da.get(k), db.get(k)
        if not a or not b:
            continue
        ca = '%5.3f x %.2f = %5.2f' % (a['valor'], a['peso'], a['aporta'])
        cb = '%5.3f x %.2f = %5.2f' % (b['valor'], b['peso'], b['aporta'])
        marca = '  ' if abs(a['aporta'] - b['aporta']) < 0.01 else ('<<' if a['aporta'] > b['aporta'] else '>>')
        L.append('  %-15s | %-22s | %-22s %s' % (k, ca, cb, marca))
    L.append('  %-15s-+-%-22s-+-%-22s' % ('-' * 15, '-' * 22, '-' * 22))
    L.append('  %-15s | %-22s | %-22s' % ('TOTAL', da.get('_total'), db.get('_total')))
    L.append('  %-15s | %-22s | %-22s' % ('origenes indep', da.get('_n_origenes'), db.get('_n_origenes')))
    L.append('  %-15s | %-22s | %-22s' % ('articulos', da.get('_n_articulos'), db.get('_n_articulos')))
    return '\n'.join(L)


# ================================================================ autotest

def _art(sid, wire=None, h=None, horas=1.0, base=None):
    """Articulo sintetico. horas = cuantas horas atras se detecto."""
    base = base or _BASE_T
    return {'source_id': sid, 'url': 'http://x/%s/%s' % (sid, horas), 'url_hash': '%s%s' % (sid, horas),
            'title_simhash': h, 'wire_origin': wire, 'title': 't', 'summary': None,
            'published_at': base - timedelta(hours=horas), 'detected_at': base - timedelta(hours=horas),
            'lang': 'en', 'event_id': 1, 'raw': {}}


_BASE_T = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)

_FUENTES_TEST = {
    'reuters':   {'id': 'reuters', 'tipo': 'western', 'tier': 1, 'wire_propio': True},
    'bbc':       {'id': 'bbc', 'tipo': 'western', 'tier': 1, 'wire_propio': True},
    'yahoo':     {'id': 'yahoo', 'tipo': 'western', 'tier': 3, 'wire_propio': False},
    'nyt':       {'id': 'nyt', 'tipo': 'western', 'tier': 1, 'wire_propio': True},
    'guardian':  {'id': 'guardian', 'tipo': 'western', 'tier': 1, 'wire_propio': True},
    'tass':      {'id': 'tass', 'tipo': 'russian', 'tier': 2, 'wire_propio': True},
    'meduza':    {'id': 'meduza', 'tipo': 'russian_ind', 'tier': 2, 'wire_propio': True},
    'xinhua':    {'id': 'xinhua', 'tipo': 'chinese', 'tier': 2, 'wire_propio': True},
    'aljazeera': {'id': 'aljazeera', 'tipo': 'arab', 'tier': 1, 'wire_propio': True},
    'timesofisrael': {'id': 'timesofisrael', 'tipo': 'israeli', 'tier': 2, 'wire_propio': True},
    'infobae':   {'id': 'infobae', 'tipo': 'latam', 'tier': 2, 'wire_propio': True},
    'lowy':      {'id': 'lowy', 'tipo': 'apac', 'tier': 2, 'wire_propio': True},
    'fedreg':    {'id': 'fedreg', 'tipo': 'official', 'tier': 1, 'wire_propio': True, 'primaria': True},
    'agregador': {'id': 'agregador', 'tipo': 'aggregator', 'tier': 3, 'wire_propio': False},
}


def _autotest():
    ok = [0, 0]

    def chk(cond, msg):
        ok[0 if cond else 1] += 1
        print('%s %s' % ('OK   ' if cond else 'FALLA', msg))
        return bool(cond)

    def saltea(msg):
        print('SALTEA: %s' % msg)

    T = _BASE_T
    print('== puntajes.py -- autotest (reloj fijo %s) ==' % T.isoformat())

    # ------------------------------------------------------------ 1. el caso clave
    # A: 20 articulos que son TODOS el mismo cable de Reuters, republicado por medios occidentales.
    cable = [_art('bbc', 'reuters', 0x1111111111111111, 1.0)]
    for i in range(19):
        cable.append(_art('yahoo%d' % i, 'reuters', 0x1111111111111111, 0.5 + i * 0.1))
    for i in range(19):
        _FUENTES_TEST['yahoo%d' % i] = {'id': 'yahoo%d' % i, 'tipo': 'western', 'tier': 3,
                                        'wire_propio': False}
    ev_cable = {'id': 1, 'titulo': 'EU announces trade measure', 'paises': ['US'],
                'actores': ['European Commission'], 'topics': ['trade'], 'dominio': 'comercio',
                'first_detected': T - timedelta(hours=2)}

    # B: 3 articulos de TRES wire_origin distintos, y ademas de tres bloques distintos.
    tres = [_art('reuters', 'reuters', 0x2222222222222222, 1.0),
            _art('tass', 'tass', 0x3333333333333333, 1.5),
            _art('xinhua', 'xinhua', 0x4444444444444444, 2.0)]
    ev_tres = dict(ev_cable, id=2, titulo='US and China trade measure')

    s_cable, d_cable = importancia(ev_cable, cable, _FUENTES_TEST, ahora=T)
    s_tres, d_tres = importancia(ev_tres, tres, _FUENTES_TEST, ahora=T)

    print('')
    print('  --- EL CASO CLAVE: 20 copias de un cable de Reuters vs 3 wires distintos ---')
    print(comparar_desgloses(d_cable, d_tres, '20 arts / 1 cable Reuters', '3 arts / 3 wires'))
    print('')

    chk(d_cable['fuentes_indep']['detalle']['n_indep'] == 1,
        '20 articulos del mismo cable de Reuters = 1 fuente independiente (da %s)'
        % d_cable['fuentes_indep']['detalle']['n_indep'])
    chk(d_tres['fuentes_indep']['detalle']['n_indep'] == 3,
        '3 articulos con 3 wire_origin distintos = 3 fuentes independientes (da %s)'
        % d_tres['fuentes_indep']['detalle']['n_indep'])
    chk(s_tres > s_cable,
        'CASO CLAVE: 3 wires distintos (%d) puntua MAS que 20 copias de un cable (%d)'
        % (s_tres, s_cable))
    chk(d_cable['velocidad']['valor'] == d_tres['velocidad']['valor'],
        'velocidad no premia el volumen: las dos rafagas valen igual (%.3f)'
        % d_cable['velocidad']['valor'])

    # ------------------------------------------------------------ 2. cubos de origen
    mixto = [_art('reuters', 'reuters', 0x5555555555555555, 1.0),
             _art('bbc', 'reuters', 0x5555555555555555, 1.1),
             _art('nyt', None, 0x6666666666666666, 1.2),
             _art('guardian', None, 0x7777777777777777, 1.3),
             _art('agregador', None, 0x8888888888888888, 1.4)]
    cubos, avisos = cubos_origen(mixto, _FUENTES_TEST)
    chk(len(cubos) == 3, 'reuters+bbc(mismo cable)+nyt+guardian+agregador = 3 origenes (da %d)' % len(cubos))
    chk(avisos['sin_atribuir'] == 1, 'el agregador sin wire no acredita origen (sin_atribuir=%d)'
        % avisos['sin_atribuir'])
    chk('wire:reuters' in cubos and len(cubos['wire:reuters']['arts']) == 2,
        'reuters y bbc caen en el mismo cubo wire:reuters')

    # fusion por simhash: dos redacciones propias con el MISMO titular = un cable no detectado
    gemelos = [_art('nyt', None, 0xABCDEF0123456789, 1.0),
               _art('guardian', None, 0xABCDEF012345678F, 1.1)]   # 0x9 ^ 0xF = 0b0110: 2 bits
    c2, _ = cubos_origen(gemelos, _FUENTES_TEST, fusionar=True)
    c3, _ = cubos_origen(gemelos, _FUENTES_TEST, fusionar=False)
    chk(len(c2) == 1, 'dos titulares casi identicos se funden en 1 origen (da %d)' % len(c2))
    chk(len(c3) == 2, 'con fusionar=False quedan 2 origenes, para poder comparar (da %d)' % len(c3))
    chk(_hamming(0xABCDEF0123456789, 0xABCDEF012345678F) == 2, 'hamming de 64 bits cuenta bien')
    chk(_hamming(0x0F0F0F0F0F0F0F0F, 0xF0F0F0F0F0F0F0F0) == 64, 'hamming con todo distinto = 64')

    lejanos = [_art('nyt', None, 0x0F0F0F0F0F0F0F0F, 1.0),
               _art('guardian', None, 0xF0F0F0F0F0F0F0F0, 1.1)]
    c4, _ = cubos_origen(lejanos, _FUENTES_TEST)
    chk(len(c4) == 2, 'titulares distintos NO se funden (da %d)' % len(c4))

    # ------------------------------------------------------------ 3. cross_bloc
    seis = [_art('nyt', None, 1, 1.0), _art('tass', None, 2, 1.0), _art('meduza', None, 3, 1.0),
            _art('xinhua', None, 4, 1.0), _art('aljazeera', None, 5, 1.0),
            _art('timesofisrael', None, 6, 1.0), _art('infobae', None, 7, 1.0),
            _art('lowy', None, 8, 1.0), _art('fedreg', None, 9, 1.0)]
    v, det = _c_cross_bloc(seis, _FUENTES_TEST)
    chk(sorted(det['bloques']) == sorted(BLOQUES),
        'los 7 bloques cuentan y russian_ind suma al ruso (%s)' % det['bloques'])
    chk(det['bloques_no_contados'] == ['official'],
        'official no es uno de los 7 bloques pero se reporta (%s)' % det['bloques_no_contados'])
    chk(abs(v - 1.0) < 1e-9, 'cross_bloc = 7/7 = 1.0 (da %.3f)' % v)
    v1, _ = _c_cross_bloc([_art('nyt', None, 1, 1.0)], _FUENTES_TEST)
    chk(abs(v1 - 1 / 7.0) < 1e-9, 'un solo bloque = 1/7 (da %.3f)' % v1)

    # ------------------------------------------------------------ 4. velocidad
    subiendo = [_art('nyt', None, 1, 0.5), _art('bbc', None, 2, 1.0), _art('tass', None, 3, 2.0)]
    bajando = [_art('nyt', None, 1, 4.0), _art('bbc', None, 2, 4.5), _art('tass', None, 3, 5.0),
               _art('xinhua', None, 4, 5.5), _art('meduza', None, 5, 5.9)]
    vs, ds = _c_velocidad(subiendo, T)
    vb, db = _c_velocidad(bajando, T)
    chk(vs > vb, 'evento que sube (%.3f) supera a uno que se apaga (%.3f)' % (vs, vb))
    chk(ds['recientes'] == 3 and ds['previos'] == 0, 'ventanas de 3h bien cortadas (%s)' % ds)
    vz, _ = _c_velocidad([], T)
    chk(0.0 <= vz <= 1.0, 'sin articulos la velocidad no explota (da %.3f)' % vz)

    # ------------------------------------------------------------ 5. actores
    va, da_ = _c_actores({'paises': ['US', 'CN'], 'actores': []})
    vb2, _ = _c_actores({'paises': ['US'], 'actores': []})
    vc, _ = _c_actores({'paises': ['AR'], 'actores': []})
    vd, _ = _c_actores({'paises': [], 'actores': []})
    chk(abs(va - 1.0) < 1e-9, 'US+CN satura el componente de actores (da %.3f)' % va)
    chk(abs(vb2 - 0.75) < 1e-9, 'US solo = 0.75 (da %.3f)' % vb2)
    chk(vc < vb2, 'Argentina sola pesa menos que EEUU solo (%.3f < %.3f)' % (vc, vb2))
    chk(vd == 0.0, 'evento sin actores = 0 y queda avisado')
    ve, de_ = _c_actores({'paises': [], 'actores': ['Vladimir Putin', 'NATO']})
    chk(ve > 0.9, 'Putin se resuelve a RU y NATO a 0.90 (da %.3f, %s)' % (ve, de_['resueltos']))

    # ------------------------------------------------------------ 6. clasificar
    chk(clasificar(100) == 'breaking' and clasificar(80) == 'breaking', 'clasificar 80+ = breaking')
    chk(clasificar(79) == 'high' and clasificar(60) == 'high', 'clasificar 60-79 = high')
    chk(clasificar(59) == 'relevant' and clasificar(40) == 'relevant', 'clasificar 40-59 = relevant')
    chk(clasificar(39) == 'low' and clasificar(0) == 'low', 'clasificar <40 = low')

    # ------------------------------------------------------------ 7. rango y determinismo
    s2, _ = importancia(ev_tres, tres, _FUENTES_TEST, ahora=T)
    chk(s2 == s_tres, 'importancia es determinista: dos corridas, el mismo numero (%d)' % s2)
    s_vacio, d_vacio = importancia({}, [], {}, ahora=T)
    chk(0 <= s_vacio <= 100, 'evento vacio queda en rango (da %d)' % s_vacio)
    chk(clasificar(s_vacio) == 'low', 'evento vacio clasifica low (%d)' % s_vacio)
    chk(abs(sum(PESOS.values()) - 1.0) < 1e-9, 'los pesos de la formula suman 1.00')
    chk('TOTAL' in formatear_desglose(d_tres) and 'fuentes_indep' in formatear_desglose(d_tres),
        'formatear_desglose imprime los 7 componentes y el total')
    chk([round(PESOS[k], 2) for k in ORDEN] == [0.22, 0.18, 0.15, 0.15, 0.15, 0.10, 0.05],
        'los pesos son los de RADAR.md 6, al pie')

    # ------------------------------------------------------------ 8. orden esperado de un ranking
    ev_top = {'id': 3, 'titulo': 'US and China clash over Taiwan strait', 'paises': ['US', 'CN', 'TW'],
              'actores': ['Xi Jinping'], 'topics': ['security'], 'dominio': 'militar',
              'first_detected': T - timedelta(hours=3)}
    arts_top = [_art('reuters', 'reuters', 0xA1, 0.5), _art('nyt', None, 0xB2, 0.7),
                _art('tass', None, 0xC3, 1.0), _art('xinhua', None, 0xD4, 1.2),
                _art('lowy', None, 0xE5, 1.5), _art('fedreg', None, 0xF6, 2.0)]
    ev_chico = {'id': 4, 'titulo': 'Local port strike', 'paises': ['PE'], 'actores': [],
                'topics': ['trade'], 'dominio': 'otro', 'first_detected': T - timedelta(hours=5)}
    arts_chico = [_art('infobae', None, 0x11, 2.0), _art('infobae', None, 0x22, 2.5)]
    s_top, d_top = importancia(ev_top, arts_top, _FUENTES_TEST, ahora=T)
    s_chico, d_chico = importancia(ev_chico, arts_chico, _FUENTES_TEST, ahora=T)
    ranking = sorted([('top', s_top), ('tres_wires', s_tres), ('cable20', s_cable),
                      ('chico', s_chico)], key=lambda x: -x[1])
    print('')
    print('  ranking: ' + ' > '.join('%s(%d)' % (n, s) for n, s in ranking))
    print('')
    chk([n for n, _ in ranking] == ['top', 'tres_wires', 'cable20', 'chico'],
        'orden esperado top > tres_wires > cable20 > chico')
    chk(clasificar(s_top) in ('breaking', 'high'), 'el evento grande cae en breaking/high (%s)'
        % clasificar(s_top))

    # ------------------------------------------------------------ 9. video_score
    ctx_bueno = {'mapa_disponible': True, 'assets': 5, 'competencia': 4,
                 'llm': {'conflicto': 'alto', 'sorpresa': 'alto', 'explicabilidad': 'alto',
                         'consecuencias': 'alto'}}
    ctx_pobre = {'mapa_disponible': False, 'assets': 0, 'competencia': 60,
                 'llm': {'conflicto': 'bajo', 'sorpresa': 'bajo', 'explicabilidad': 'bajo',
                         'consecuencias': 'bajo'}}
    ev_v = dict(ev_top, importancia=s_top)
    vs1, dv1 = video_score(ev_v, arts_top, ctx_bueno)
    vs2, dv2 = video_score(ev_v, arts_top, ctx_pobre)
    chk(vs1 > vs2, 'video_score: contexto bueno (%d) supera al pobre (%d)' % (vs1, vs2))
    chk(0 <= vs1 <= 100 and 0 <= vs2 <= 100, 'video_score en rango 0..100')
    chk(abs(sum(PESOS_VIDEO.values()) - 1.0) < 1e-9, 'los pesos de video_score suman 1.00')
    c0, _ = _c_competencia(0)
    c4_, _ = _c_competencia(4)
    c40, _ = _c_competencia(40)
    chk(c4_ > c0 and c4_ > c40, 'competencia: la franja del medio gana (0:%.2f 4:%.2f 40:%.2f)'
        % (c0, c4_, c40))
    sin_mapa = video_score(ev_v, arts_top, dict(ctx_bueno, mapa_disponible=False))[0]
    chk(vs1 > sin_mapa, 'tener la hoja de mapa sube el video_score (%d > %d)' % (vs1, sin_mapa))
    marcado = video_score(dict(ev_v, requiere_agustin=True), arts_top, ctx_bueno)
    chk(marcado[0] == vs1 and marcado[1]['_requiere_agustin'] is True,
        'requiere_agustin NO baja el video_score, solo se reporta (RADAR.md 6)')
    sin_llm = video_score(ev_v, arts_top, {'mapa_disponible': True, 'assets': 5, 'competencia': 4})
    chk(0 <= sin_llm[0] <= 100 and sin_llm[1]['_avisos'],
        'sin categorias del LLM sale un numero neutro y quedan los avisos (%d)' % sin_llm[0])
    cons = video_score(dict(ev_v, riesgo_escalada='alto'), arts_top,
                       {'competencia': 4, 'llm': {'conflicto': 'alto'}})[1]
    chk(cons['consecuencias']['valor'] == 1.0, 'consecuencias cae a riesgo_escalada si falta')

    # ------------------------------------------------------------ 10. banderas
    ev_normal = {'titulo': 'ECB holds rates', 'topics': ['economy'], 'actores': ['ECB'],
                 'first_detected': T - timedelta(hours=2)}
    st_ok = [{'tipo': 'fact', 'texto': 'The ECB held rates at 2 percent', 'n_indep': 3,
              'evidence': 'own_reporting'}]
    b, m = banderas(ev_normal, st_ok, ahora=T)
    chk(b is False and m is None, 'evento normal no levanta bandera (la compuerta invertida sirve)')

    ev_atentado = {'titulo': 'Car bombing in Ankara kills 12', 'topics': ['terrorism'],
                   'first_detected': T - timedelta(days=2)}
    b, m = banderas(ev_atentado, st_ok, ahora=T)
    chk(b and 'eventos sensibles' in (m or ''), 'atentado de hace 2 dias levanta bandera')
    ev_viejo = dict(ev_atentado, first_detected=T - timedelta(days=30))
    b2, m2 = banderas(ev_viejo, st_ok, ahora=T)
    chk(b2 is False, 'el mismo atentado hace 30 dias ya no levanta bandera (%s)' % m2)

    ev_civil = {'titulo': 'Strike on market leaves 30 dead among civilians', 'topics': [],
                'first_detected': T - timedelta(days=1)}
    chk(banderas(ev_civil, [], ahora=T)[0], 'victimas + blanco civil levanta bandera')
    ev_guerra = {'titulo': 'Drone strikes hit energy infrastructure near the front line',
                 'topics': ['military'], 'first_detected': T - timedelta(days=1)}
    chk(banderas(ev_guerra, [], ahora=T)[0] is False,
        'cobertura de guerra rutinaria NO levanta bandera (si no, salta todos los dias)')

    ev_ideo = {'titulo': 'Court rules on abortion law', 'topics': ['politics'],
               'first_detected': T - timedelta(days=1)}
    b3, m3 = banderas(ev_ideo, [], ahora=T)
    chk(b3 and 'IDEOLOGIA' in (m3 or ''), 'aborto levanta bandera de IDEOLOGIA.md')
    chk(banderas({'titulo': 'New transit corridor opens', 'first_detected': T}, [], ahora=T)[0] is False,
        '"transit" no se confunde con "trans" (limites de palabra)')

    st_solo = [{'tipo': 'fact', 'texto': 'X happened', 'n_indep': 1, 'evidence': 'own_reporting'}]
    b4, m4 = banderas(ev_normal, st_solo, ahora=T)
    chk(b4 and 'una sola fuente' in (m4 or ''), 'fact con una sola fuente levanta bandera')
    st_oficial = [{'tipo': 'fact', 'texto': 'X published', 'n_indep': 1, 'evidence': 'official_doc'}]
    chk(banderas(ev_normal, st_oficial, ahora=T)[0] is False,
        'fact con 1 fuente pero documento oficial no levanta bandera (invariante del contrato)')

    st_priv = [{'tipo': 'claim', 'actor': 'police',
                'texto': 'Police said the suspect, John Miller, was arrested', 'n_indep': 1}]
    chk(banderas(ev_normal, st_priv, ahora=T)[0], 'persona privada nombrada levanta bandera')
    chk(banderas({'titulo': 'x', 'personas_privadas': ['Ana Gomez'], 'first_detected': T},
                 [], ahora=T)[0], 'personas_privadas del LLM levanta bandera')

    b5, m5 = banderas(dict(ev_atentado, personas_privadas=['John Miller']), st_solo, ahora=T)
    chk(b5 and m5.count(' . ') >= 2, 'varios motivos se juntan, el mas grave primero')
    chk(m5.startswith('atentado'), 'el motivo mas grave encabeza motivo_bandera')

    ev_sin_fecha = {'titulo': 'Massacre reported in border town'}
    chk(banderas(ev_sin_fecha, [], ahora=T)[0],
        'sin fecha se asume reciente: preguntar de mas es barato')

    # el texto de la bandera de persona privada llega en castellano CON tildes desde los feeds
    # en español (Infobae, Clarin). Si no se normaliza, el patron no matchea nunca.
    ev_es = {'titulo': 'Ataque en Rosario', 'first_detected': T}
    st_tilde = [{'tipo': 'claim', 'actor': 'policia', 'n_indep': 1,
                 'texto': 'La policia dijo que la victima, Juan Perez, murio en el lugar'}]
    st_tilde_acentuado = [dict(st_tilde[0],
                               texto='La policía dijo que la víctima, Juan Pérez, murió en el lugar')]
    chk(banderas(ev_es, st_tilde, ahora=T)[0], 'persona privada en castellano sin tildes')
    chk(banderas(ev_es, st_tilde_acentuado, ahora=T)[0],
        'persona privada en castellano CON tildes tambien levanta bandera (se normaliza)')

    # ------------------------------------------------------------ 10b. dominio: vocabulario real
    # DOMINIO_PESO tiene que cubrir el enum que emite radar/extraccion.py. Si no, un hecho militar
    # y uno menor caen los dos en DOMINIO_DEFECTO y el componente deja de discriminar.
    ENUM_DOMINIO = ['military_escalation', 'nuclear', 'trade', 'energy', 'diplomatic',
                    'domestic_politics', 'finance', 'tech', 'other']
    ENUM_TOPICS = ['military', 'diplomacy', 'trade', 'energy', 'sanctions', 'elections',
                   'tech', 'finance', 'migration', 'legal']
    faltan = [d for d in ENUM_DOMINIO + ENUM_TOPICS if d not in DOMINIO_PESO]
    chk(not faltan, 'DOMINIO_PESO cubre el enum de extraccion.py y los topics (faltan: %s)' % faltan)
    chk(_c_dominio({'dominio': 'military_escalation'})[0] > _c_dominio({'dominio': 'other'})[0],
        'military_escalation pesa mas que other (%.2f vs %.2f)'
        % (_c_dominio({'dominio': 'military_escalation'})[0], _c_dominio({'dominio': 'other'})[0]))

    ruta_ex = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extraccion.py')
    m_enum = None
    if os.path.exists(ruta_ex):
        m_enum = re.search(r'"dominio":\s*\{[^}]*?"enum":\s*\[(.*?)\]',
                           open(ruta_ex, encoding='utf-8').read(), re.S)
    if not m_enum:
        saltea('no se pudo leer el enum de dominio de extraccion.py; se valida el hardcodeado')
    else:
        vivo = re.findall(r'"([a-z_]+)"', m_enum.group(1))
        chk(set(vivo) <= set(DOMINIO_PESO),
            'el enum VIVO de extraccion.py esta cubierto (sobra: %s)' % sorted(set(vivo) - set(DOMINIO_PESO)))

    # sin `dominio` (hoy no hay columna en esquema.sql) se cae a topics, que si se persiste
    v_mil, d_mil = _c_dominio({'topics': ['military', 'diplomacy']})
    v_neutro, _ = _c_dominio({'topics': []})
    chk(v_mil == DOMINIO_PESO['military'] and d_mil['desde_topics'] == 'military',
        'sin dominio se usa el topic mas pesado (%.2f, %s)' % (v_mil, d_mil['desde_topics']))
    chk(v_neutro == DOMINIO_DEFECTO, 'sin dominio ni topics conocidos, neutro (%.2f)' % v_neutro)
    chk(_c_dominio({'dominio': 'nuclear', 'topics': ['legal']})[0] == 1.00,
        'si hay dominio, gana el dominio y no el topic')

    # el LLM puede mandar basura: nunca revienta ni sale de rango
    for basura in ('', '   ', 'no_existe_esto', 3.7, -2, True):
        vv, _ = _c_dominio({'dominio': basura})
        if not (0.0 <= vv <= 1.0):
            chk(False, 'dominio basura %r sale de rango (%.2f)' % (basura, vv))
            break
    else:
        chk(True, 'dominio con valores basura queda en 0..1 y no revienta')

    # assets negativo: math.log(1+n) con n<0 reventaba con ValueError
    neg = video_score({'importancia': 50}, [], {'assets': -3, 'competencia': 3})
    chk(neg[1]['assets']['valor'] == 0.0, 'assets negativo se trata como 0, no revienta')

    # ------------------------------------------------------------ 11. contra fuentes.json real
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fuentes.json')
    if not os.path.exists(ruta):
        saltea('radar/fuentes.json no esta aca; no se valida el vocabulario de source_type')
    else:
        try:
            datos = json.load(open(ruta, encoding='utf-8'))
            feeds = datos.get('feeds') or []
            tipos = {(f.get('tipo') or '').lower() for f in feeds}
            conocidos = set(BLOQUES) | set(ALIAS_BLOQUE) | {'official', 'osint', 'ukrainian',
                                                            'iranian', 'aggregator'}
            chk(tipos <= conocidos, 'todo source_type de fuentes.json es conocido (sobra: %s)'
                % sorted(tipos - conocidos))
            idx = {f['id']: f for f in feeds}
            chk(all(isinstance(f.get('tier'), int) for f in feeds),
                'todas las fuentes traen tier entero')
            # sin simhash a proposito: aca se prueba el cubeo por fuente, no la fusion por titular
            reales = [_art(f['id'], None, None, 1.0) for f in feeds[:12]]
            cub, _ = cubos_origen(reales, idx)
            propias = sum(1 for f in feeds[:12] if f.get('wire_propio', True))
            chk(len(cub) == propias,
                'con fuentes reales, los origenes = las que reportan propio (%d de 12)' % len(cub))
            s_real, _ = importancia({'paises': ['US'], 'dominio': 'economia'}, reales, idx, ahora=T)
            chk(0 <= s_real <= 100, 'importancia con fuentes reales queda en rango (%d)' % s_real)
        except Exception as e:
            chk(False, 'leyendo fuentes.json: %r' % (e,))

    saltea('nada de esto toca Postgres, red ni credenciales: el modulo es puro por contrato')

    print('')
    print('%d OK, %d FALLA' % (ok[0], ok[1]))
    return 0 if ok[1] == 0 else 1


if __name__ == '__main__':
    if '--autotest' in sys.argv:
        sys.exit(_autotest())
    print(__doc__)
