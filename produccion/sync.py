# -*- coding: utf-8 -*-
"""AUDITORIA GUION -> IMAGEN (motor v4, `canal/AUDITORIA_MOTOR_2026-09-15.md` §6.2). 0 creditos.

Es el chequeo que faltaba. `coreo.py check` verifica que nada este cortado, que los puntos del mapa
sean exactos y que haya cortes por minuto; **no verifica que lo que se ve sea lo que se dice**. El
ep. 09 pasaba el check con 24 s de pantalla vacia en el acto II y con «22 cents» dicho mientras en
pantalla ponia «AND 78 CENTS».

    python produccion/sync.py <coreo.py|modulo> <tiempos.json> [--pts pts.json] [--out _qc]
                              [--build build] [--paso 1] [--sin-hojas] [--guion guion.md]

o desde la coreo, con la escena ya construida:

    import sync
    r = sync.auditar(sc, 'audio/tiempos.json', out='_qc')
    if r['VACIO']: sys.exit('hay pantalla vacia')

Por cada linea A: muestrea tres instantes (inicio+0,3 · centro · fin-0,3) y registra la ventana de
camara, los objetos que cuentan como contenido, los textos en pantalla, las capas de mapa activas y
si hay mapa. Escribe `_qc/sync.md` y hojas `_qc/sync_NN.jpg` con UN CUADRO REAL por linea y el texto
de la linea debajo — que es lo que hay que mirar antes de renderizar.

Banderas:
  VACIO               mas de 0,8 s de la linea sin ningun objeto que cuente (`Scene.visible`, que
                      NO cuenta rotulos de plano ni etiquetas de region: contarlos es lo que dejaba
                      pasar los cuadros vacios del ep. 09).   -> obligatorio 0 para renderizar.
  CIFRA_SIN_PANTALLA  la linea dice una cantidad y esa cantidad no esta en ninguna tarjeta, prop o
                      HUD visible entre inicio-1,5 s y fin+1,5 s (comparada por MAGNITUD: «1.13T»,
                      «1,13 trillion» y «1130000000000» son la misma cifra).
                      **LIMITE CONOCIDO**: el texto en pantalla se lee del NOMBRE del objeto
                      (`card:$1.13T`), no de sus pixeles. Una cifra dibujada DENTRO de un prop —una
                      tabla, un grafico de barras— es invisible para esta bandera y da un falso
                      positivo: en el ep. 09 pasa con las cuatro cifras de la tabla del Tesoro. Por
                      eso esta avisa y no aborta; la que aborta es VACIO.
  LUGAR_SIN_MAPA      la linea nombra un sitio del pts.json y el punto no esta dentro de la ventana.
  TEXTO_VIEJO         un texto nacido hace mas de 12 s sigue en pantalla.
  PROP_HUERFANO       un objeto entra en una linea que no lo nombra (ni su V:). Aviso, no aborta.
"""
import json, math, os, re, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
if AQUI not in sys.path: sys.path.insert(0, AQUI)
import motor as M

TEXTUALES = ('card:', 'sello:', 'sub:', 'texto:', 'cifra:', 'rotulo:', 'region:', 'chip:', 'tab:')
NO_CUENTAN = ('rotulo:', 'region:', 'sub:', 'mundo:')


# ---------------------------------------------------------------- numeros
# El parser de numeros en letras es el de `guiones/checklist.py` (que lo usa para cruzar las cifras
# del guion contra la hoja de fuentes), extendido para leer TAMBIEN lo que hay en pantalla:
# «$1.13T», «49,000», «17 %». Los dos lados se reducen a una MAGNITUD y se comparan por valor, que
# es lo unico que permite decir que «1,13 trillion» y «$1.13T» son la misma cifra.
U = {'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7,
     'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14,
     'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
     'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90}
MUL = {'hundred': 100.0, 'thousand': 1e3, 'million': 1e6, 'billion': 1e9, 'trillion': 1e12,
       'k': 1e3, 'm': 1e6, 'bn': 1e9, 'b': 1e9, 't': 1e12, 'tn': 1e12}
_TOK = re.compile(r"\d[\d.,]*|[a-z]+(?:-[a-z]+)?|%")


def _val(tok):
    """'1,130' -> 1130 · '1.13' -> 1.13 · '49,000' -> 49000. La coma es separador de miles en
    ingles; el punto, decimal. Si hay las dos, la coma es de miles."""
    t = tok.replace('$', '')
    if re.match(r'^\d{1,3}(,\d{3})+(\.\d+)?$', t): t = t.replace(',', '')
    else: t = t.replace(',', '.') if (',' in t and '.' not in t and len(t.split(',')[-1]) != 3) else t.replace(',', '')
    try: return float(t)
    except ValueError: return None


def magnitudes(txt):
    """Todas las cantidades de un texto, como floats. Sirve para la voz y para lo que hay en
    pantalla. Descarta 0, 1 y 2 sueltos (no son cifras, son articulos)."""
    if not txt: return set()
    toks = _TOK.findall(txt.lower().replace('\n', ' '))
    out, cur, total = [], 0.0, 0.0
    dec = [False, '']            # dentro de un decimal dicho en letras, y sus digitos
    def cerrar_dec():
        nonlocal cur
        if dec[0]:
            if dec[1]: cur += float('0.' + dec[1])
            dec[0] = False; dec[1] = ''
    def flush():
        nonlocal cur, total
        cerrar_dec()
        v = total + cur
        if v: out.append(v)
        cur = total = 0.0
    i = 0
    while i < len(toks):
        tk = toks[i]
        if re.match(r'\d', tk):
            flush()
            v = _val(tk)
            if v is not None:
                nxt = toks[i + 1] if i + 1 < len(toks) else ''
                if nxt in MUL: v *= MUL[nxt]; i += 1
                out.append(v)
            i += 1; continue
        # «one point one three trillion» = 1,13 billones. El parser de checklist.py se saltaba el
        # 'point' y sumaba 1+1+3 = 5: la cifra del ep. 09 quedaba mal leida. Aca los digitos que
        # siguen a 'point' son decimales, no sumandos.
        if tk == 'point' and (cur or total):
            dec[0] = True; dec[1] = ''; i += 1; continue
        partes = tk.split('-')
        if dec[0] and len(partes) == 1 and tk in U and U[tk] < 10:
            dec[1] += str(U[tk]); i += 1; continue
        if all(p in U for p in partes):
            cerrar_dec()
            val = float(sum(U[p] for p in partes))
            # 'nineteen | seventy-nine' son dos numeros (un anio), pero 'nine hundred and
            # thirty-one' es uno solo: el corte vale solo cuando lo acumulado es de dos cifras.
            if 10 <= cur < 100 and val >= 20: out.append(cur); cur = 0.0
            cur += val; i += 1; continue
        if tk in MUL:
            cerrar_dec()
            out.append(cur or 1.0)                                    # la base: 'ten billion' -> 10
            if tk == 'hundred': cur = (cur or 1.0) * 100
            else: total += (cur or 1.0) * MUL[tk]; cur = 0.0
            i += 1; continue
        if tk in ('and', 'a', 'point', 'half', 'quarter', 'percent', 'per', 'cent', '%'):
            i += 1; continue
        flush(); i += 1
    flush()
    # "twenty twenty-seven" -> 2027
    for k in range(len(out) - 1):
        a, b = out[k], out[k + 1]
        if a == int(a) and b == int(b) and 10 <= a < 100 and 0 < b < 100:
            out.append(a * 100 + b)
    return {round(v, 6) for v in out if v not in (0.0, 1.0, 2.0)}


def _casan(a, b, tol=0.02):
    """Dos magnitudes son la misma si coinciden al 2 % o si sus digitos son el mismo numero a otra
    escala (1,13 y 1.130.000.000.000 son la misma cifra dicha de dos maneras)."""
    if a == b: return True
    if a and b and abs(a - b) <= tol * max(abs(a), abs(b)): return True
    for k in (1e2, 1e3, 1e6, 1e9, 1e12):
        if b and abs(a - b * k) <= tol * max(abs(a), abs(b * k)): return True
        if a and abs(b - a * k) <= tol * max(abs(b), abs(a * k)): return True
    return False


# ---------------------------------------------------------------- muestreo
def _textos(objs):
    out = []
    for o in objs:
        n = getattr(o, 'name', '') or ''
        for p in TEXTUALES:
            if n.startswith(p): out.append(n[len(p):]); break
    return out


def _todos_visibles(sc, t):
    """Todo lo visible en `t` (contenido + textos), sin filtrar prefijos: para buscar cifras."""
    vis = list(sc.visible(t, ignorar=()))
    return vis


def auditar(sc, tiempos, pts=None, P=None, out=None, dur=None, guion=None, paso=1,
            hojas=True, lugares_extra=(), verbose=True):
    """Audita una escena ya construida contra `tiempos.json`. Devuelve el dict de conteos."""
    if isinstance(tiempos, str): tiempos = json.load(open(tiempos, encoding='utf-8'))
    L = tiempos['lineas']
    DUR = dur or tiempos.get('dur') or (L[-1]['fin'] + 1.0)
    out = out or os.path.join(os.getcwd(), '_qc')
    os.makedirs(out, exist_ok=True)

    # --- de donde salen los sitios del mapa
    if P is None:
        if getattr(sc, 'mundo', None) is not None:
            P = sc.mundo.P; pts = pts if pts is not None else sc.mundo.pts
        else:
            for o in sc.layers:
                if isinstance(o, M.MapSheet):
                    P = o.P; pts = pts if pts is not None else o.pts; break
    if isinstance(pts, str): pts = json.load(open(pts, encoding='utf-8'))
    pts = pts or {}
    LUG = {k: k for k in pts}
    for k in lugares_extra: LUG[k] = k

    # --- V: del guion por beat (para PROP_HUERFANO)
    VE = {}
    if guion and os.path.exists(guion):
        b = -1
        for ln in open(guion, encoding='utf-8').read().split('\n'):
            if ln.startswith('## '): b += 1
            elif ln.startswith('V:') or ln.startswith('**V:**'):
                VE.setdefault(b, []).append(re.sub(r'^\**V:\**\s*', '', ln).lower())

    hay_mapa_global = (getattr(sc, 'mundo', None) is not None
                       or any(isinstance(o, M.MapSheet) for o in sc.layers))
    filas = []; conteo = {'VACIO': 0, 'CIFRA_SIN_PANTALLA': 0, 'LUGAR_SIN_MAPA': 0,
                          'TEXTO_VIEJO': 0, 'PROP_HUERFANO': 0}
    detalle = {k: [] for k in conteo}
    vistos_antes = set()

    for li, ln in enumerate(L):
        if li % paso: continue
        t0, t1 = float(ln['inicio']), float(ln['fin'])
        txt = ln.get('texto', '')
        ts = [min(DUR - 0.01, t0 + 0.30), min(DUR - 0.01, (t0 + t1) / 2), max(0.0, min(DUR - 0.01, t1 - 0.30))]
        ts = sorted(set(round(x, 3) for x in ts))
        nombres = set(); textos = set(); capas = set(); ventana = None; mapa = False
        # El VACIO se mide con un barrido fino (0,25 s), no con los tres instantes del registro:
        # la bandera dice «mas de 0,8 s sin nada», y con tres muestras en una linea de doce segundos
        # cada hueco valdria cuatro. Los tres instantes son para ANOTAR que se ve; esto, para medir.
        vac = 0.0; paso_v = 0.25; tv = t0
        while tv < t1:
            if not sc.visible(min(DUR - 0.01, tv), ignorar=NO_CUENTAN):
                vac += min(paso_v, t1 - tv)
            tv += paso_v
        for k, t in enumerate(ts):
            vis = sc.visible(t, ignorar=NO_CUENTAN)
            todo = _todos_visibles(sc, t)
            nombres |= {(getattr(o, 'name', '') or type(o).__name__) for o in vis}
            textos |= set(_textos(todo))
            ventana = sc.window(t)
            if getattr(sc, 'mundo', None) is not None:
                mapa = True
                for lay, tr, mode, _xy in sc.mundo.layers:
                    if tr(t) > 0.05: capas.add(id(lay))
            elif hay_mapa_global:
                for o in sc.layers:
                    if isinstance(o, M.MapSheet) and t >= o.on and o.a(t) > 0.05 and o.reveal(t) > 0.05:
                        mapa = True
        bander = []
        # ---- VACIO
        if vac > 0.8:
            bander.append('VACIO'); conteo['VACIO'] += 1
            detalle['VACIO'].append((li, round(t0, 1), txt[:70]))
        # ---- CIFRA_SIN_PANTALLA
        mag = magnitudes(txt)
        if mag:
            en_pantalla = set()
            k = t0 - 1.5
            while k <= t1 + 1.5:
                for o in _todos_visibles(sc, max(0.0, min(DUR - 0.01, k))):
                    n = getattr(o, 'name', '') or ''
                    for p in TEXTUALES:
                        if n.startswith(p): en_pantalla |= magnitudes(n[len(p):]); break
                k += 0.5
            if not any(_casan(a, b) for a in mag for b in en_pantalla):
                bander.append('CIFRA_SIN_PANTALLA'); conteo['CIFRA_SIN_PANTALLA'] += 1
                detalle['CIFRA_SIN_PANTALLA'].append((li, round(t0, 1), sorted(mag)[:4], txt[:70]))
        # ---- LUGAR_SIN_MAPA
        if mapa and P is not None:
            faltan = []
            for nm in LUG:
                if not re.search(r'\b%s\b' % re.escape(nm), txt, re.I): continue
                if nm not in pts: continue
                px, py = P(nm)
                if ventana and ventana[0] <= px <= ventana[2] and ventana[1] <= py <= ventana[3]: continue
                faltan.append(nm)
            if faltan:
                bander.append('LUGAR_SIN_MAPA:' + ','.join(faltan))
                conteo['LUGAR_SIN_MAPA'] += 1
                detalle['LUGAR_SIN_MAPA'].append((li, round(t0, 1), faltan, txt[:70]))
        # ---- TEXTO_VIEJO
        viejos = []
        for o in _todos_visibles(sc, ts[len(ts) // 2]):
            n = getattr(o, 'name', '') or ''
            if not any(n.startswith(p) for p in ('card:', 'sello:', 'texto:', 'cifra:')): continue
            nac = getattr(o, 'on', 0.0)
            if getattr(o, 'off', 1e9) - nac > 0.6 * DUR: continue      # chrome permanente
            if ts[len(ts) // 2] - nac > 12.0: viejos.append(n)
        if viejos:
            bander.append('TEXTO_VIEJO'); conteo['TEXTO_VIEJO'] += 1
            detalle['TEXTO_VIEJO'].append((li, round(t0, 1), viejos[:3], txt[:70]))
        # ---- PROP_HUERFANO
        ve = ' '.join(VE.get(ln.get('b', -1), []))
        nuevos = [n for n in nombres if n not in vistos_antes]
        vistos_antes |= nombres
        huer = [n for n in nuevos
                if not n.startswith(TEXTUALES)
                and len(n) > 3
                and n.split('_')[0].lower() not in txt.lower()
                and n.split('_')[0].lower() not in ve]
        if huer:
            bander.append('PROP_HUERFANO'); conteo['PROP_HUERFANO'] += 1
            detalle['PROP_HUERFANO'].append((li, round(t0, 1), huer[:4], txt[:70]))
        filas.append({'i': li, 't0': round(t0, 2), 't1': round(t1, 2), 'texto': txt,
                      'ventana': [int(v) for v in (ventana or (0, 0, 0, 0))],
                      'mapa': mapa, 'capas': len(capas),
                      'visibles': sorted(nombres)[:8], 'textos': sorted(textos)[:6],
                      'banderas': bander, 'vacio_s': round(vac, 2)})

    # ---- informe
    md = ['# Sincronia guion -> imagen', '',
          'Generado por `produccion/sync.py`. Un cuadro REAL por linea en `sync_NN.jpg`.', '',
          '| # | t | linea | plano (ventana) | que se ve | textos | banderas |',
          '|---|---|-------|-----------------|-----------|--------|----------|']
    for f in filas:
        v = f['ventana']
        md.append('| %d | %.1f | %s | %d,%d %dx%d%s | %s | %s | %s |'
                  % (f['i'], f['t0'], f['texto'][:60].replace('|', '/'),
                     v[0], v[1], v[2] - v[0], v[3] - v[1], ' MAPA' if f['mapa'] else '',
                     ', '.join(f['visibles'])[:60], ', '.join(f['textos'])[:50].replace('|', '/'),
                     ' '.join(f['banderas'])))
    md += ['', '## Conteos', '']
    for k, v in conteo.items(): md.append('- **%s**: %d' % (k, v))
    md += ['', '## Detalle', '']
    for k, v in detalle.items():
        if not v: continue
        md.append('### %s (%d)' % (k, len(v)))
        for it in v[:40]: md.append('- ' + str(it))
        md.append('')
    p_md = os.path.join(out, 'sync.md')
    open(p_md, 'w', encoding='utf-8').write('\n'.join(md) + '\n')

    if hojas: _hojas(sc, filas, out, DUR)
    if verbose:
        print('sync: %d lineas  ->  %s' % (len(filas), p_md))
        print('  ' + '  '.join('%s=%d' % (k, v) for k, v in conteo.items()))
    conteo['lineas'] = len(filas); conteo['_md'] = p_md; conteo['_filas'] = filas
    return conteo


def _hojas(sc, filas, out, DUR, cols=6, por_hoja=24, w=320):
    """Un cuadro REAL (`sc.render`) por linea, con el texto de la linea debajo. Lo que se mira."""
    from PIL import Image, ImageDraw
    import props as PR
    fw, fh = sc.W, sc.H
    h = int(w * fh / fw); pie = 54
    fnt = PR.FONTC(17)
    n_h = (len(filas) + por_hoja - 1) // por_hoja
    for k in range(n_h):
        trozo = filas[k * por_hoja:(k + 1) * por_hoja]
        filas_n = (len(trozo) + cols - 1) // cols
        q = Image.new('RGB', (cols * w, filas_n * (h + pie)), (18, 17, 15))
        d = ImageDraw.Draw(q)
        for i, f in enumerate(trozo):
            t = min(DUR - 0.01, (f['t0'] + f['t1']) / 2)
            fr = sc.render(t).convert('RGB').resize((w, h), Image.LANCZOS)
            x, y = (i % cols) * w, (i // cols) * (h + pie)
            q.paste(fr, (x, y))
            col = (255, 110, 90) if f['banderas'] else (200, 200, 190)
            d.rectangle([x, y, x + 74, y + 18], fill=(0, 0, 0))
            d.text((x + 4, y + 2), '%d  %.1fs' % (f['i'], f['t0']), fill=(255, 220, 120), font=fnt)
            txt = f['texto']
            linea = ''
            for pal in txt.split():
                if d.textlength(linea + ' ' + pal, font=fnt) > w - 12 and linea: break
                linea = (linea + ' ' + pal).strip()
            d.text((x + 5, y + h + 5), linea[:60], fill=col, font=fnt)
            if f['banderas']:
                d.text((x + 5, y + h + 27), ' '.join(f['banderas'])[:48], fill=(255, 110, 90), font=fnt)
                d.rectangle([x, y, x + w - 2, y + h - 2], outline=(220, 60, 50), width=3)
        p = os.path.join(out, 'sync_%02d.jpg' % k)
        q.save(p, quality=86)
        print('  hoja ->', p)


# ---------------------------------------------------------------- CLI
def _cargar(ruta, func='build'):
    """Importa un coreo.py por ruta (o un modulo ya en sys.path) y devuelve su escena."""
    import importlib, importlib.util
    if os.path.exists(ruta):
        d = os.path.dirname(os.path.abspath(ruta))
        sys.path.insert(0, d); os.chdir(d)
        nom = os.path.splitext(os.path.basename(ruta))[0]
        m = importlib.import_module(nom)
    else:
        m = importlib.import_module(ruta)
    return getattr(m, func)()


def main():
    a = sys.argv[1:]
    if len(a) < 2: print(__doc__); return
    def opt(k, d=None): return a[a.index(k) + 1] if k in a else d
    coreo, tiempos = a[0], os.path.abspath(a[1])
    sal = os.path.abspath(opt('--out', os.path.join(os.path.dirname(tiempos), '..', '_qc')))
    pts = opt('--pts'); pts = os.path.abspath(pts) if pts else None
    guion = opt('--guion'); guion = os.path.abspath(guion) if guion else None
    sc = _cargar(coreo, opt('--build', 'build'))
    r = auditar(sc, tiempos, pts=pts, out=sal, guion=guion, paso=int(opt('--paso', 1)),
                hojas='--sin-hojas' not in a)
    sys.exit(2 if r['VACIO'] else 0)


if __name__ == '__main__':
    main()
