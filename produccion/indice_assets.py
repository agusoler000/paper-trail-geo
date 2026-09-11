# -*- coding: utf-8 -*-
"""
Indice de assets del canal. Recorre el repo, junta lo que costo creditos con lo que se genero por codigo
y escribe canal/INDICE_ASSETS.md + produccion/assets_indice.json.

Regla de Agustin (2026-09-08): antes de generar CUALQUIER cosa con IA hay que mirar este indice y reusar.
El tope de USD 4 por produccion es un TECHO, no un presupuesto para gastar.

Uso:
    python produccion/indice_assets.py            # regenera el indice
    python produccion/indice_assets.py buscar putin trump      # busca antes de generar
"""
import os, sys, json, io, datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
CAT = os.path.join(RAIZ, 'canal', 'assets_catalogo.json')


def rel(p):
    return os.path.relpath(p, RAIZ).replace('\\', '/')


def mb(p):
    try:
        return os.path.getsize(p) / 1e6
    except OSError:
        return 0.0


def catalogo():
    if os.path.exists(CAT):
        return json.load(io.open(CAT, encoding='utf-8'))
    return {}


def ficha_de(clave, cat, extra=None):
    """Metadatos del catalogo + lo que traiga una ficha .json al lado del archivo."""
    d = dict(cat.get(clave, {}))
    if extra and os.path.exists(extra):
        try:
            j = json.load(io.open(extra, encoding='utf-8'))
            for k in ('modelo', 'creditos', 'fecha', 'episodio', 'prompt', 'momento'):
                if k in j and k not in d:
                    d[k] = j[k]
            for sub in ('still', 'clip'):
                if isinstance(j.get(sub), dict):
                    d.setdefault('modelo', j[sub].get('modelo'))
                    d['creditos'] = (d.get('creditos') or 0) + (j[sub].get('creditos') or 0)
        except Exception:
            pass
    return d


def escanear():
    cat = catalogo()
    fam = []

    # ---------------------------------------------------------------- rigs (Flux, 1 cr c/u)
    rigdir = os.path.join(RAIZ, 'pruebas', 'elenco', 'rig')
    items = []
    if os.path.isdir(rigdir):
        for n in sorted(os.listdir(rigdir)):
            d = os.path.join(rigdir, n)
            if not os.path.isdir(d):
                continue
            piezas = [f for f in os.listdir(d) if f.endswith('.png')]
            f = ficha_de(n, cat, os.path.join(d, 'rig.json'))
            items.append({'clave': n, 'ruta': rel(d), 'piezas': len(piezas),
                          'origen': rel(os.path.join(RAIZ, 'pruebas', 'elenco', n + '.png')),
                          'preview': rel(os.path.join(rigdir, 'preview_%s.jpg' % n)),
                          'modelo': f.get('modelo', 'flux (sin ficha)'), 'creditos': f.get('creditos', 1),
                          'quien': f.get('quien', ''), 'usado_en': f.get('usado_en', []), 'notas': f.get('notas', '')})
    fam.append(('rigs', 'Personajes de papel recortados en piezas (cabeza, torso, 2 brazos x 2 segmentos). '
                        'REUSABLES SIEMPRE: el ep. 5 usa los del 1 al 4.', items))

    # ---------------------------------------------------------------- recortes sueltos
    cutdir = os.path.join(RAIZ, 'pruebas', 'elenco', 'cut')
    con_rig = {i['clave'] for i in items}
    items = []
    if os.path.isdir(cutdir):
        for f in sorted(os.listdir(cutdir)):
            if f.endswith('.png'):
                k = f[:-4]
                d = ficha_de(k, cat)
                tiene_rig = k in con_rig
                items.append({'clave': k, 'ruta': rel(os.path.join(cutdir, f)),
                              'modelo': d.get('modelo', 'flux (sin ficha)'),
                              'creditos': 0 if tiene_rig else d.get('creditos', 1),
                              'quien': (d.get('quien', '') + (' — fuente del rig, no cuesta aparte' if tiene_rig else '')).strip(' —'),
                              'usado_en': d.get('usado_en', []), 'notas': d.get('notas', '')})
    fam.append(('recortes', 'PNG sin fondo de cada personaje. Para los que ya tienen rig es el paso previo al mismo '
                            'asset (0 cr aparte); los que no lo tienen (manos, multitud) se usan enteros con cutout().', items))

    # ---------------------------------------------------------------- hojas de expresiones
    expdir = os.path.join(RAIZ, 'pruebas', 'elenco', 'expresiones')
    items = []
    if os.path.isdir(expdir):
        for f in sorted(os.listdir(expdir)):
            if f.endswith('.png'):
                k = f[:-4]
                d = ficha_de(k, cat)
                items.append({'clave': k, 'ruta': rel(os.path.join(expdir, f)),
                              'modelo': d.get('modelo', 'flux (sin ficha)'), 'creditos': d.get('creditos', 1),
                              'quien': d.get('quien', ''), 'usado_en': d.get('usado_en', []), 'notas': d.get('notas', '')})
    fam.append(('expresiones', 'Hojas de caras por personaje. Se cortan una vez y sirven para todos los episodios.', items))

    # ---------------------------------------------------------------- planos hero (i2v, 10-20 cr)
    herodir = os.path.join(AQUI, 'hero')
    items = []
    if os.path.isdir(herodir):
        for f in sorted(os.listdir(herodir)):
            if f.endswith('.json'):
                k = f[:-5]
                d = ficha_de(k, cat, os.path.join(herodir, f))
                vids = [v for v in os.listdir(herodir) if v.startswith(k) and v.endswith('.mp4')]
                items.append({'clave': k, 'ruta': rel(os.path.join(herodir, f)),
                              'clips': [rel(os.path.join(herodir, v)) for v in sorted(vids)],
                              'modelo': d.get('modelo', ''), 'creditos': d.get('creditos', 0),
                              'quien': d.get('momento', d.get('quien', '')),
                              'usado_en': d.get('usado_en', [d.get('episodio')] if d.get('episodio') else []),
                              'notas': d.get('notas', '')})
    fam.append(('hero', 'Planos generativos (still + image-to-video). Lo MAS caro que generamos: 10-20 cr por clip. '
                        'Cada uno con su ficha .json (modelo, prompt, creditos, que se descarto y por que).', items))

    # ---------------------------------------------------------------- sets / fondos
    setdir = os.path.join(AQUI, 'assets', 'sets')
    items = []
    if os.path.isdir(setdir):
        for f in sorted(os.listdir(setdir)):
            if f.endswith('.png'):
                k = f[:-4]
                d = ficha_de(k, cat)
                items.append({'clave': k, 'ruta': rel(os.path.join(setdir, f)),
                              'modelo': d.get('modelo', 'flux (sin ficha)'), 'creditos': d.get('creditos', 1),
                              'quien': d.get('quien', ''), 'usado_en': d.get('usado_en', []), 'notas': d.get('notas', '')})
    fam.append(('sets', 'Fondos de pared generados. Reusables como telon en cualquier episodio.', items))

    # ---------------------------------------------------------------- musica (Lyria, 3 cr c/u)
    musdir = os.path.join(AQUI, 'musica')
    items = []
    if os.path.isdir(musdir):
        for f in sorted(os.listdir(musdir)):
            if not f.endswith('.mp3'):
                continue
            k = f[:-4]
            propia = k.startswith('cue_') or k == 'tema_canal'
            d = ficha_de(k, cat)
            items.append({'clave': k, 'ruta': rel(os.path.join(musdir, f)),
                          'modelo': d.get('modelo', 'lyria-3-pro' if propia else 'biblioteca libre'),
                          'creditos': d.get('creditos', 3 if propia else 0),
                          'quien': d.get('quien', 'cue propia' if propia else 'de terceros, ver CREDITOS_MUSICA.md'),
                          'usado_en': d.get('usado_en', []), 'notas': d.get('notas', '')})
    fam.append(('musica', 'Cues propias (Lyria, 3 cr) y pistas de biblioteca. Las cues se REUSAN entre episodios: '
                          'antes de generar una nueva, escuchar estas.', items))

    # ---------------------------------------------------------------- hojas de mapa (0 cr, codigo)
    # Se miran los assets compartidos Y los de cada produccion (`videos/<dir>/arte/assets/`): un mapa
    # o un prop dibujado por codigo dentro de una produccion tambien se reusa, y si no sale en el
    # indice se vuelve a dibujar (regla 19: buscar antes de generar).
    adir = os.path.join(AQUI, 'assets')
    DIRS = [adir]
    _v = os.path.join(RAIZ, 'videos')
    if os.path.isdir(_v):
        DIRS += [os.path.join(_v, d, 'arte', 'assets') for d in sorted(os.listdir(_v))
                 if os.path.isdir(os.path.join(_v, d, 'arte', 'assets'))]
    items = []
    for _d in DIRS:
        grupos = {}
        for f in sorted(os.listdir(_d)):
            if f.startswith('mapa') and (f.endswith('.png') or f.endswith('.json')):
                pref = f.split('_')[0]
                grupos.setdefault(pref, []).append(f)
        adir_ = _d
        for pref, fs in sorted(grupos.items()):
            d = ficha_de(pref, cat)
            items.append({'clave': pref, 'ruta': rel(adir_), 'piezas': len(fs), 'capas': sorted(fs),
                          'modelo': '0 cr (Natural Earth + codigo)', 'creditos': 0,
                          'quien': d.get('quien', ''), 'usado_en': d.get('usado_en', []), 'notas': d.get('notas', '')})
    fam.append(('mapas', 'Hojas de mapa por region. 0 creditos pero HORAS de trabajo: si el tema cae en una region '
                         'que ya tenemos, se reusa la hoja y solo se agregan puntos a su pts.json.', items))

    # ---------------------------------------------------------------- props (0 cr, codigo)
    props = []
    for _d in DIRS:
        props += [(f, _d) for f in sorted(os.listdir(_d))
                  if f.startswith('prop_') and f.endswith('.png')]
    fam.append(('props', 'Objetos de papel dibujados por codigo (props*.py). 0 creditos. Antes de dibujar uno nuevo, '
                         'buscar aca: hay %d.' % len(props),
                [{'clave': f[5:-4], 'ruta': rel(os.path.join(dd, f)), 'modelo': '0 cr (codigo)', 'creditos': 0,
                  'quien': '', 'usado_en': [], 'notas': ''} for f, dd in props]))

    # ---------------------------------------------------------------- marca (voz e intro/outro ya pagadas)
    items = []
    for f, q in [('intro_canal.mp4', 'intro general del canal v2, 14 s (pide like y suscripcion)'),
                 ('outro_canal.mp4', 'outro del canal v2, 20 s (pide like y suscripcion)'),
                 ('intro03_canal.mp4', 'intro de preguntas del ep. 3 (plantilla)')]:
        p = os.path.join(AQUI, f)
        if os.path.exists(p):
            d = ficha_de(f[:-4], cat)
            items.append({'clave': f[:-4], 'ruta': rel(p), 'modelo': d.get('modelo', 'render local + voz pagada'),
                          'creditos': d.get('creditos', 0), 'quien': d.get('quien', q),
                          'usado_en': d.get('usado_en', []), 'notas': d.get('notas', '')})
    fam.append(('marca', 'Piezas fijas del canal ya renderizadas. Se pegan tal cual: NO se vuelven a generar.', items))

    # ------------------------------------------------- assets generados dentro de una produccion (videos/<dir>/arte)
    # Desde `canal/ESTRUCTURA.md` cada produccion tiene su carpeta; lo que se genera con IA ahi tambien
    # cuesta creditos y tambien se reusa, asi que tiene que salir en el indice.
    items = []
    vdir = os.path.join(RAIZ, 'videos')
    if os.path.isdir(vdir):
        for prod in sorted(os.listdir(vdir)):
            ad = os.path.join(vdir, prod, 'arte', 'assets')
            if not os.path.isdir(ad): continue
            for f in sorted(os.listdir(ad)):
                if not f.endswith('.png'): continue
                clave = f[5:-4] if f.startswith('prop_') else f[:-4]
                d = ficha_de(clave, cat)
                if not d.get('creditos'): continue        # los de codigo ya salen en 'props'
                items.append({'clave': clave, 'ruta': rel(os.path.join(ad, f)),
                              'modelo': d.get('modelo', '?'), 'creditos': d.get('creditos', 0),
                              'quien': d.get('quien', ''), 'usado_en': d.get('usado_en', [prod]),
                              'notas': d.get('notas', '')})
    fam.append(('produccion', 'Assets con costo generados dentro de una produccion (`videos/<dir>/arte/assets/`). '
                              'Se pueden reusar en otras: buscar aca antes de volver a generar.', items))

    return fam


def escribir(fam):
    total_cr = sum(i.get('creditos') or 0 for _, _, items in fam for i in items)
    hoy = datetime.date.today().isoformat()

    js = {'generado': hoy, 'creditos_acumulados': total_cr,
          'familias': {n: {'que_es': q, 'items': items} for n, q, items in fam}}
    json.dump(js, io.open(os.path.join(AQUI, 'assets_indice.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    L = []
    L.append('# INDICE DE ASSETS — generado por `produccion/indice_assets.py`')
    L.append('')
    L.append('> **No editar a mano.** Se regenera con `python produccion/indice_assets.py`.')
    L.append('> Regla y criterios en `canal/ASSETS.md`. Los metadatos que el disco no sabe (modelo, prompt, quien es,')
    L.append('> en que episodio se uso) salen de `canal/assets_catalogo.json` y de las fichas `.json` al lado del archivo.')
    L.append('')
    L.append('Generado: **%s** · assets con costo acumulado: **%d creditos** (~USD %.2f a $0,029/cr).'
             % (hoy, total_cr, total_cr * 0.029))
    L.append('')
    for n, q, items in fam:
        cr = sum(i.get('creditos') or 0 for i in items)
        L.append('## %s — %d %s' % (n, len(items), 'creditos' if cr else '(0 cr)'))
        L.append('')
        L.append(q)
        L.append('')
        if not items:
            L.append('_vacio_')
            L.append('')
            continue
        if n == 'props':
            L.append('`' + '` · `'.join(i['clave'] for i in items) + '`')
            L.append('')
            continue
        L.append('| Clave | Que es | Modelo | Cr | Usado en | Ruta |')
        L.append('|---|---|---|---|---|---|')
        for i in items:
            L.append('| `%s` | %s | %s | %s | %s | `%s` |' % (
                i['clave'], (i.get('quien') or i.get('notas') or '—')[:80], i.get('modelo') or '—',
                i.get('creditos') if i.get('creditos') else '0',
                ', '.join(i.get('usado_en') or []) or '—', i['ruta']))
        L.append('')
    io.open(os.path.join(RAIZ, 'canal', 'INDICE_ASSETS.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    return total_cr


def buscar(terminos, fam):
    t = [x.lower() for x in terminos]
    print('Buscando %s en el indice de assets:\n' % ' + '.join(t))
    hits = 0
    for n, _, items in fam:
        for i in items:
            blob = json.dumps(i, ensure_ascii=False).lower()
            if all(x in blob for x in t):
                hits += 1
                print('  [%s] %s — %s (%s cr) -> %s' % (n, i['clave'], i.get('quien') or '', i.get('creditos') or 0, i['ruta']))
    if not hits:
        print('  nada. Si de verdad no existe, generalo Y anotalo en canal/assets_catalogo.json.')
    else:
        print('\n  %d coincidencias: REUSAR antes de gastar un credito.' % hits)


if __name__ == '__main__':
    fam = escanear()
    if len(sys.argv) > 1 and sys.argv[1] == 'buscar':
        buscar(sys.argv[2:], fam)
    else:
        cr = escribir(fam)
        n = sum(len(i) for _, _, i in fam)
        print('canal/INDICE_ASSETS.md + produccion/assets_indice.json: %d assets, %d creditos acumulados.' % (n, cr))
