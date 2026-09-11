# -*- coding: utf-8 -*-
"""Vectorizacion de titulares para el Radar, sin modelos pesados.

TF-IDF de n-gramas de CARACTERES (3 a 5), proyectado por hashing a dim=512 y normalizado L2.

Por que esto y no un modelo de embeddings:
  - cero descarga y cero GPU. Entra en el VPS que ya corre Supabase, n8n y el render (RADAR.md §4),
    donde hay 5,6 GB libres y sin swap: bajar 470 MB de pesos y tenerlos residentes no es gratis.
  - determinista. El mismo titular da el mismo vector hoy y en marzo, y en otro proceso: el hash
    es crc32, no el hash() de Python, que cambia con PYTHONHASHSEED en cada arranque.
  - a nivel de caracter aguanta multi-idioma sin un diccionario por idioma, que es justo lo que
    pide tener TASS, Infobae y Xinhua en la misma base.
  - la interfaz no cambia si algun dia entra un modelo real: vectorizar() y similitud() siguen igual.

Limites conocidos, y el autotest los MIDE en vez de esconderlos. Esto compara GRAFIA, no significado:
  - Dos titulares del mismo hecho en alfabetos distintos (Xinhua en chino vs Reuters en ingles) NO
    se parecen (medido: en-ru 0.00, en-zh -0.02). Para el Radar alcanza porque casi todo entra en
    ingles (Google News de puente, TASS y Xinhua en sus ediciones inglesas), pero hay que saberlo
    antes de encender un feed en cirilico.
  - El rango util de coseno es MUCHO mas bajo que el de un modelo denso. El autotest imprime la
    matriz y el umbral que la separacion medida sugiere; el UMBRAL=0.78 de CONTRATO.md esta escrito
    pensando en un modelo denso y NO sirve tal cual con esto. Ver la linea "umbral sugerido".
  - No sabe que Washington es EEUU ni que Moscu es Rusia, y en titulares eso pasa todo el tiempo.
    Por eso existe ALIAS/USAR_ALIAS mas abajo, apagado por defecto: medido sobre las 29 cabeceras
    del autotest, encenderlo sube el peor par del mismo hecho de 0.20 a 0.45 y es lo unico que
    hace que un umbral unico separe bien. Prenderlo obliga a re-vectorizar la base.

Decisiones medidas (el autotest y los numeros de arriba salen de comparar las variantes):
  - hashing CON signo, no sin: sin signo todo sube, pero el piso de ruido sube mas (0.038 -> 0.184),
    o sea que discrimina peor. Lo que importa no es el coseno alto, es la distancia al ruido.
  - n-gramas que CRUZAN los espacios, no por palabra: por palabra sube el par facil (AB 0.48 -> 0.63)
    pero tambien confunde "Brazil central bank cuts" con "Turkey central bank raises" (0.27 -> 0.34).

Uso:
    v   = vectorizar(["titular uno", "titular dos"])   # el IDF se ajusta sobre el lote
    idf = ajustar_idf(corpus)                          # dict plano, json.dump y listo
    u   = vectorizar_uno("titular nuevo", idf)         # incremental: uno contra un IDF ya ajustado
    s   = similitud(u, v[0])

Dependencias: numpy (ya en el stack). Todo lo demas es stdlib.
"""
import itertools, json, math, os, subprocess, sys, unicodedata, zlib
from collections import Counter
from functools import lru_cache
import numpy as np

DIM = 512             # celdas del hashing; 512 entra comodo en pgvector y en RAM
N_MIN, N_MAX = 3, 5   # largo de los n-gramas de caracteres
SIGNO_ALTERNO = True  # hashing con signo: las colisiones se cancelan en promedio en vez de sumar
IDF_ACTUAL = None     # ultimo IDF ajustado, para que vectorizar_uno(texto) ande sin pasarselo

# Metonimia de titular. APAGADO por defecto (USAR_ALIAS): cambia el vector de un mismo texto, asi
# que prenderlo a mitad de camino deja los vectores viejos de la base incomparables con los nuevos
# -> si se prende, hay que re-vectorizar. Lo decide quien escriba agrupar.py, con el numero medido.
USAR_ALIAS = False
ALIAS = {
    'washington': 'us', 'white house': 'us', 'the pentagon': 'us', 'state department': 'us',
    'moscow': 'russia', 'the kremlin': 'russia', 'beijing': 'china', 'kyiv': 'ukraine',
    'brussels': 'eu', 'tehran': 'iran', 'tel aviv': 'israel', 'pyongyang': 'north korea',
}
_ALIAS_ORD = sorted(ALIAS.items(), key=lambda kv: -len(kv[0]))   # las frases antes que las palabras

# ---------------------------------------------------------------- normalizacion
def normalizar(texto, alias=None):
    """Minusculas, sin acentos, sin puntuacion, espacios colapsados.
    Conserva letras y digitos de cualquier alfabeto (cirilico, arabe, CJK): saca diacriticos
    combinantes pero recompone despues, asi el hangul no queda partido en jamo.
    `alias` None = lo que diga USAR_ALIAS; True/False para forzarlo (lo usa el autotest)."""
    t = unicodedata.normalize('NFKD', str(texto or ''))
    t = ''.join(c for c in t if not unicodedata.combining(c))
    t = unicodedata.normalize('NFC', t).lower()
    t = ''.join(c if c.isalnum() else ' ' for c in t)   # puntuacion y simbolos -> espacio
    t = ' '.join(t.split())
    if alias if alias is not None else USAR_ALIAS:
        s = ' %s ' % t
        for k, v in _ALIAS_ORD: s = s.replace(' %s ' % k, ' %s ' % v)
        t = s.strip()
    return t

def ngramas(texto, n_min=N_MIN, n_max=N_MAX):
    """Counter de n-gramas de caracteres sobre el texto ya normalizado, con un espacio de padding
    a cada lado para que los arranques y finales de palabra sean n-gramas propios."""
    s = ' %s ' % normalizar(texto)
    c = Counter()
    for n in range(n_min, n_max + 1):
        for i in range(len(s) - n + 1): c[s[i:i + n]] += 1
    return c

# ---------------------------------------------------------------- hashing
@lru_cache(maxsize=1 << 20)
def _h(g):
    """crc32 del n-grama. Estable entre procesos y entre corridas; hash() de Python no lo es."""
    return zlib.crc32(g.encode('utf-8'))

def _celda(h, dim): return (h >> 8) % dim           # bits altos para la celda...
def _signo(h): return 1.0 if (h & 1) else -1.0      # ...y el bit 0 para el signo, sin solaparse.
                                                    # Con dim potencia de 2, h%dim y h&1 comparten
                                                    # el bit 0 y el signo dejaria de ser aleatorio.

def _pesos_idf(idf):
    """Vector (dim,) de pesos IDF suavizados: log((1+N)/(1+df)) + 1.
    El +1 es lo que evita que en un lote chico el termino que comparten tres titulares del mismo
    hecho ('sanctions') valga cero justamente por ser el que comparten."""
    n = float(idf.get('n_docs') or 0)
    df = np.asarray(idf['df'], dtype=np.float64)
    return np.log((1.0 + n) / (1.0 + df)) + 1.0

def _dims(idf, dim):
    """Resuelve dim/n_min/n_max cuando viene un IDF ya ajustado: manda el dim del IDF.
    Si el llamador pide un dim distinto de DIM, es un error y levanta, no un arreglo silencioso.
    LIMITE CONOCIDO (el autotest lo deja fijado): `dim=DIM` no se distingue del valor por defecto de
    la firma, asi que un `vectorizar(t, dim=512, idf=idf_de_256)` devuelve 256 sin avisar. No se
    puede arreglar sin cambiar el `dim=512` que fija CONTRATO.md; en el radar no aparece porque
    ajustar_idf siempre se llama sin dim."""
    if idf is None: return dim, N_MIN, N_MAX
    if dim != idf['dim'] and dim != DIM:
        raise ValueError('el IDF se ajusto con dim=%d y pediste dim=%d' % (idf['dim'], dim))
    return idf['dim'], idf.get('n_min', N_MIN), idf.get('n_max', N_MAX)

def _vector(texto, dim, n_min, n_max, pesos):
    """Un texto -> vector (dim,) L2. tf sublineal (1+log tf), signo por hash, IDF por celda."""
    v = np.zeros(dim, dtype=np.float64)
    for g, tf in ngramas(texto, n_min, n_max).items():
        h = _h(g); w = 1.0 + math.log(tf)
        if SIGNO_ALTERNO: w *= _signo(h)
        v[_celda(h, dim)] += w
    if pesos is not None: v *= pesos
    n = math.sqrt(float(v.dot(v)))
    return v / n if n > 0.0 else v                  # texto vacio -> vector de ceros, no NaN

# ---------------------------------------------------------------- API
def ajustar_idf(corpus, dim=DIM, n_min=N_MIN, n_max=N_MAX):
    """Cuenta document frequency POR CELDA, o sea despues del hashing: el modelo son `dim`
    enteros y no un vocabulario que crece sin techo. Dict plano: json.dump(idf, f) y se relee
    sin nada especial, que es lo que hace falta para el caso incremental entre corridas.
    Deja el resultado en IDF_ACTUAL para que vectorizar_uno(texto) funcione sin pasarselo."""
    global IDF_ACTUAL
    df = [0] * dim; n_docs = 0
    for t in corpus:
        n_docs += 1
        for b in {_celda(_h(g), dim) for g in ngramas(t, n_min, n_max)}: df[b] += 1
    IDF_ACTUAL = {'dim': dim, 'n_min': n_min, 'n_max': n_max, 'n_docs': n_docs, 'df': df}
    return IDF_ACTUAL

def actualizar_idf(idf, textos):
    """Suma documentos nuevos al IDF sin recontar la base entera. El ingest corre cada 30 min:
    si nadie lo alimenta, el IDF envejece y deja de describir lo que esta entrando."""
    d, nmin, nmax = idf['dim'], idf.get('n_min', N_MIN), idf.get('n_max', N_MAX)
    for t in textos:
        idf['n_docs'] += 1
        for b in {_celda(_h(g), d) for g in ngramas(t, nmin, nmax)}: idf['df'][b] += 1
    return idf

def vectorizar(textos, dim=DIM, idf=None):
    """list[str] -> np.ndarray (n, dim), filas L2-normalizadas.
    Si `idf` es None el IDF se ajusta SOBRE EL LOTE y queda en IDF_ACTUAL; pasando `idf` se
    reusa uno ya ajustado (y ahi el dim sale del IDF)."""
    textos = list(textos)
    if idf is None: idf = ajustar_idf(textos, dim)
    d, nmin, nmax = _dims(idf, dim)
    pesos = _pesos_idf(idf)
    m = np.zeros((len(textos), d), dtype=np.float64)
    for i, t in enumerate(textos): m[i] = _vector(t, d, nmin, nmax, pesos)
    return m

def vectorizar_uno(texto, idf=None, dim=DIM):
    """Un articulo nuevo contra un IDF YA ajustado -> np.ndarray (dim,).
    Sin esto el clustering incremental de agrupar.py no existe: no se puede reajustar el IDF de
    toda la base cada vez que entra un titular, y si cada tanda usara su propio IDF los vectores
    guardados ayer no serian comparables con los de hoy."""
    idf = idf if idf is not None else IDF_ACTUAL
    if idf is None: raise ValueError('no hay IDF ajustado: llama a ajustar_idf(corpus) o pasa idf=')
    d, nmin, nmax = _dims(idf, dim)
    return _vector(texto, d, nmin, nmax, _pesos_idf(idf))

def similitud(a, b):
    """Coseno. Los vectores ya salen normalizados, asi que es el producto punto; renormaliza
    igual por si llega algo de la base que no lo esta.
    Vector nulo, con NaN o con infinitos -> 0.0: un vector corrupto tiene que leerse como
    'no se parece a nada'. OJO con el clamp: min(1.0, nan) devuelve 1.0 en Python, asi que
    sin estos chequeos un embedding roto de la base sale como coseno 1.0 y agrupar.py lo
    adjunta al primer evento contra el que lo compare. Por eso se corta antes del clamp."""
    a = np.asarray(a, dtype=np.float64); b = np.asarray(b, dtype=np.float64)
    na = math.sqrt(float(a.dot(a))); nb = math.sqrt(float(b.dot(b)))
    if not (na > 0.0 and nb > 0.0): return 0.0              # cero, o NaN (nan > 0 es False)
    if not (math.isfinite(na) and math.isfinite(nb)): return 0.0
    s = float(a.dot(b)) / (na * nb)
    return float(max(-1.0, min(1.0, s))) if math.isfinite(s) else 0.0

def matriz_similitud(vecs, otros=None):
    """Coseno de todos contra todos (o contra `otros`). Asume filas ya normalizadas, que es lo
    que devuelve vectorizar(). Es la operacion que mira agrupar.py."""
    a = np.asarray(vecs, dtype=np.float64)
    b = a if otros is None else np.asarray(otros, dtype=np.float64)
    return a.dot(b.T)

# ---------------------------------------------------------------- autotest
# Los tres primeros son el MISMO hecho dicho de tres formas; los dos ultimos no tienen nada que ver.
PRUEBA = [
    ('A', 'US announces new sanctions on Russia'),
    ('B', 'US imposes new Russia sanctions'),
    ('C', 'Washington introduces new sanctions against Moscow'),
    ('D', 'Taiwan reports Chinese aircraft near its airspace'),
    ('E', 'Argentina inflation slows for the third month'),
]
# Ruido realista, para que el IDF se ajuste sobre un lote parecido al de una corrida de verdad y no
# sobre cinco titulares (con cinco, 'sanctions' aparece en 3 de 5 y el IDF lo castiga de mas).
RUIDO = [
    'European Commission adopts 19th sanctions package against Russia',
    'Ukraine says drone attack hit refinery in Samara region',
    'China coast guard enters waters near disputed islands',
    'Fed holds rates steady as inflation cools',
    'Milei government sends budget bill to Congress',
    'Oil prices rise after OPEC output decision',
    'NATO defence ministers meet in Brussels',
    'Israel strikes targets in southern Lebanon',
    'India and Japan sign defence technology pact',
    'Brazil central bank cuts benchmark rate',
    'Taiwan holds annual air defence drills',
    'Germany approves new military aid for Kyiv',
    'Iran resumes talks with European powers',
    'North Korea test fires ballistic missile',
    'Australia announces critical minerals deal with US',
    'Mexico peso weakens after election result',
    'Turkey central bank raises interest rates again',
    'Egypt signs gas export agreement with Italy',
    'Poland closes border crossing with Belarus',
    'Chile lithium output falls in second quarter',
    'Saudi Arabia and Russia extend production cuts',
    'Philippines files protest over South China Sea incident',
    'Nigeria naira hits record low against dollar',
    'Vietnam and US upgrade diplomatic ties',
]

def _autotest():
    global USAR_ALIAS
    fallas = []
    def chk(cond, msg, det=''):
        print(('OK    ' if cond else 'FALLA ') + msg + (('  -> ' + det) if det and not cond else ''))
        if not cond: fallas.append(msg)

    print('== normalizacion ==')
    chk(normalizar('  ¿Qué  pasó, EEUU?! ') == 'que paso eeuu',
        'normalizar: acentos, puntuacion y espacios', repr(normalizar('  ¿Qué  pasó, EEUU?! ')))
    chk(normalizar('Кремль заявил') ==
        'кремль заявил', 'normalizar conserva cirilico')
    chk(normalizar('中国宣布新措施') == '中国宣布新措施',
        'normalizar conserva CJK')
    chk(normalizar(None) == '' and normalizar('') == '', 'normalizar tolera None y vacio')
    chk(len(ngramas('abcdef')) > 0 and ngramas('') == Counter(), 'ngramas: cuenta y tolera vacio')
    chk(USAR_ALIAS is False and normalizar('Washington and Moscow') == 'washington and moscow',
        'los alias vienen APAGADOS: normalizar no toca los nombres')
    chk(normalizar('White House warned Moscow', alias=True) == 'us warned russia',
        'con alias=True la metonimia de titular se canoniza',
        repr(normalizar('White House warned Moscow', alias=True)))

    print('== forma y determinismo ==')
    textos = [t for _, t in PRUEBA]
    v = vectorizar(textos)
    chk(v.shape == (5, 512), 'vectorizar devuelve (n, 512)', str(v.shape))
    normas = np.sqrt((v * v).sum(axis=1))
    chk(np.allclose(normas, 1.0, atol=1e-12), 'todas las filas quedan L2 = 1', str(normas))
    chk(np.array_equal(v, vectorizar(textos)), 'determinista dentro del proceso')
    vacio = vectorizar(['', '   ', '!!'])
    chk(vacio.shape == (3, 512) and not np.isnan(vacio).any() and (vacio == 0).all(),
        'texto vacio -> fila de ceros, sin NaN')
    chk(vectorizar([]).shape == (0, 512), 'lote vacio no rompe')

    # crc32 no depende de PYTHONHASHSEED: se verifica en procesos nuevos, que es donde hash() falla
    ruta = os.path.dirname(os.path.abspath(__file__))
    cod = ('import sys; sys.path.insert(0, r"%s"); import vectores as V; '
           'v = V.vectorizar([t for _, t in V.PRUEBA]); '
           'print(round(float(v.sum()), 12), round(float(abs(v).sum()), 12))' % ruta)
    try:
        salidas = []
        for semilla in ('0', '1', '12345'):
            env = dict(os.environ); env['PYTHONHASHSEED'] = semilla
            r = subprocess.run([sys.executable, '-c', cod], capture_output=True, text=True,
                               env=env, timeout=180)
            salidas.append(r.stdout.strip() or ('ERR ' + r.stderr.strip()[-200:]))
        propio = '%s %s' % (round(float(v.sum()), 12), round(float(abs(v).sum()), 12))
        chk(len(set(salidas)) == 1 and salidas[0] == propio,
            'determinista entre procesos con PYTHONHASHSEED distinto', ' | '.join(salidas + [propio]))
    except Exception as e:
        print('SALTEA: no se pudo lanzar el subproceso de determinismo (%s)' % e)

    print('== similitud ==')
    chk(abs(similitud(v[0], v[0]) - 1.0) < 1e-9, 'similitud consigo mismo = 1')
    chk(abs(similitud(v[0], v[3]) - similitud(v[3], v[0])) < 1e-12, 'similitud simetrica')
    chk(all(-1.0 <= similitud(v[i], v[j]) <= 1.0 for i in range(5) for j in range(5)),
        'similitud en [-1, 1]')
    chk(similitud(np.zeros(512), v[0]) == 0.0, 'similitud con vector nulo = 0, no NaN')
    chk(abs(similitud(list(v[0]), list(v[1])) - similitud(v[0], v[1])) < 1e-12,
        'similitud acepta listas')
    # Un embedding corrupto que sale 1.0 es peor que uno que rompe: agrupar.py lo adjunta al
    # primer evento que mire. min(1.0, nan) devuelve 1.0 en Python, asi que esto hay que medirlo.
    roto = {'nan': np.full(512, np.nan), 'inf': np.where(np.arange(512) == 0, np.inf, 0.0),
            'desborde': np.where(np.arange(512) < 2, 1e200, 0.0)}
    with np.errstate(over='ignore', invalid='ignore'):   # el ruido lo hace el dato roto a proposito
        for nombre, x in roto.items():
            chk(similitud(x, v[0]) == 0.0 and similitud(x, x) == 0.0,
                'vector con %s -> 0.0, nunca 1.0' % nombre,
                'da %.3f contra otro y %.3f contra si mismo' % (similitud(x, v[0]), similitud(x, x)))

    print('== lo que importa: separa el mismo hecho de los que no lo son ==')
    res = {}
    for etiqueta, con_ruido in (('IDF del lote de 5', False), ('IDF de lote realista (29 titulares)', True)):
        vv = vectorizar(textos, idf=ajustar_idf(textos + RUIDO)) if con_ruido else vectorizar(textos)
        M = matriz_similitud(vv)
        print('')
        print('  -- %s --' % etiqueta)
        print('        ' + '  '.join('%6s' % n for n, _ in PRUEBA))
        for i, (n, _) in enumerate(PRUEBA):
            print('   %s   ' % n + '  '.join('%6.3f' % M[i, j] for j in range(5)))
        intra = {PRUEBA[i][0] + PRUEBA[j][0]: M[i, j] for i, j in ((0, 1), (0, 2), (1, 2))}
        inter = {PRUEBA[i][0] + PRUEBA[j][0]: M[i, j] for i in (0, 1, 2) for j in (3, 4)}
        print('   mismo hecho : ' + '  '.join('%s=%.3f' % (k, x) for k, x in intra.items()))
        print('   distinto    : ' + '  '.join('%s=%.3f' % (k, x) for k, x in inter.items()) +
              '  DE=%.3f' % M[3, 4])
        peor_intra, mejor_inter = min(intra.values()), max(inter.values())
        margen = peor_intra - mejor_inter
        print('   peor del mismo hecho %.3f | mejor entre ajenos %.3f | margen %.3f' %
              (peor_intra, mejor_inter, margen))
        print('   umbral sugerido para agrupar.py: %.2f  (CONTRATO.md dice 0.78, que es de un modelo denso)' %
              ((peor_intra + mejor_inter) / 2.0))
        res[etiqueta] = (M, peor_intra, mejor_inter, margen)
        chk(margen > 0.05, 'separacion con %s (margen %.3f)' % (etiqueta, margen),
            'peor mismo hecho %.3f <= mejor ajeno %.3f' % (peor_intra, mejor_inter))
        vecinos_ok = all(int(np.argmax(np.where(np.arange(5) == i, -9.0, M[i]))) in (0, 1, 2)
                         for i in (0, 1, 2))
        chk(vecinos_ok, 'A, B y C: su vecino mas cercano es otro de A/B/C (lo que hace agrupar.py)')
        chk(all(M[i, j] > 0 for i in (0, 1, 2) for j in (0, 1, 2)),
            'ninguna pareja del mismo hecho da coseno negativo')

    print('')
    # C es el caso duro: no comparte casi palabras con A ni con B. Va con el numero, no tapado.
    M, _, mejor_inter, _ = res['IDF de lote realista (29 titulares)']
    c_peor = min(M[0, 2], M[1, 2])
    print('   C ("Washington/Moscow", sin palabras en comun con A) contra A/B: AC=%.3f BC=%.3f' %
          (M[0, 2], M[1, 2]))
    print('   el mejor de A/B/C contra un titular ajeno es %.3f' % mejor_inter)
    chk(c_peor > mejor_inter, 'C separa de los titulares ajenos (%.3f vs %.3f)' % (c_peor, mejor_inter),
        'C NO separa: %.3f contra %.3f' % (c_peor, mejor_inter))

    # Separar A/B/C de D y E es el pedido, y pasa. Pero agrupar.py no compara contra dos titulares
    # elegidos: compara contra todo lo que entro en 72 h. Asi que medimos el piso de ruido de verdad.
    print('== piso de ruido sobre las 29 cabeceras (lo que agrupar.py tiene que no confundir) ==')
    corpus = textos + RUIDO
    for modo in (False, True):
        USAR_ALIAS = modo
        Mc = matriz_similitud(vectorizar(corpus, idf=ajustar_idf(corpus)))
        peor = min(Mc[0, 1], Mc[0, 2], Mc[1, 2])
        pares = sorted(((Mc[i, j], corpus[i], corpus[j])
                        for i, j in itertools.combinations(range(len(corpus)), 2)
                        if not (i < 3 and j < 3)), reverse=True)
        p = np.array([x[0] for x in pares])
        print('  -- USAR_ALIAS=%s --  peor par del mismo hecho %.3f' % (modo, peor))
        print('     resto de los pares: media %.3f  p95 %.3f  p99 %.3f  max %.3f' %
              (p.mean(), np.percentile(p, 95), np.percentile(p, 99), p.max()))
        for s, a, b in pares[:3]: print('     %.3f  %-42s | %s' % (s, a[:42], b[:42]))
        if peor > p.max():
            print('     SEPARA: un umbral entre %.2f y %.2f agrupa A/B/C sin juntar nada mas.' %
                  (p.max(), peor))
        else:
            print('     SOLAPA: no hay umbral unico. Agrupar A/B/C obliga a juntar tambien el par de')
            print('     arriba (%.3f), que son dos titulares distintos del mismo tema.' % p.max())
        if modo:
            chk(peor > p.max(), 'con USAR_ALIAS=True hay umbral unico sobre las 29 (%.3f vs %.3f)' %
                (peor, p.max()))
    USAR_ALIAS = False

    print('== incremental (lo que usa agrupar.py) ==')
    idf = ajustar_idf(RUIDO)
    lote = vectorizar(textos, idf=idf)
    uno = np.vstack([vectorizar_uno(t, idf) for t in textos])
    chk(np.allclose(lote, uno, atol=1e-15), 'vectorizar_uno == vectorizar contra el mismo IDF',
        str(float(np.abs(lote - uno).max())))
    ajustar_idf(RUIDO)
    chk(np.allclose(vectorizar_uno(textos[0]), lote[0]), 'vectorizar_uno(texto) usa IDF_ACTUAL')
    idf2 = json.loads(json.dumps(idf))
    chk(np.allclose(vectorizar_uno(textos[0], idf2), lote[0]), 'el IDF sobrevive un round-trip por JSON')
    # Que sume no alcanza: tiene que sumar IGUAL que reajustar todo. Si el IDF incremental se
    # desviara del completo, los vectores de hoy quedarian pesados distinto de los de ayer y
    # nadie se enteraria, que es exactamente lo que rompe un clustering incremental.
    inc = actualizar_idf(ajustar_idf(RUIDO), textos)
    total = ajustar_idf(RUIDO + textos)
    distintas = sum(1 for x, y in zip(inc['df'], total['df']) if x != y)
    chk(inc['n_docs'] == total['n_docs'] and inc['df'] == total['df'],
        'actualizar_idf(A, B) da el MISMO idf que ajustar_idf(A+B)',
        'n_docs %d vs %d, celdas distintas %d' % (inc['n_docs'], total['n_docs'], distintas))
    try:
        vectorizar(textos, dim=256, idf=total); ok = False
    except ValueError:
        ok = True
    chk(ok, 'dim en conflicto con el IDF levanta ValueError en vez de arreglarlo solo')
    # El otro lado de esa moneda, medido y no escondido: dim=DIM no se distingue del default de
    # la firma que fija CONTRATO.md, asi que contra un IDF de otro dim gana el IDF sin avisar.
    chk(vectorizar(textos, dim=DIM, idf=ajustar_idf(textos, dim=256)).shape[1] == 256,
        'LIMITE: dim=DIM explicito no se distingue del default, manda el dim del IDF')

    print('== multi-idioma ==')
    es = ['Estados Unidos anuncia nuevas sanciones contra Rusia',
          'EEUU impone nuevas sanciones a Rusia',
          'La inflacion de Argentina baja por tercer mes']
    ve = vectorizar(es)
    chk(similitud(ve[0], ve[1]) > similitud(ve[0], ve[2]),
        'castellano: mismo hecho > hecho ajeno (%.3f vs %.3f)' % (similitud(ve[0], ve[1]), similitud(ve[0], ve[2])))
    ru = ['США объявили новые '
          'санкции против '
          'России',
          'США вводят новые '
          'санкции в отношении '
          'России',
          'Инфляция в Аргентине '
          'замедлилась третий '
          'месяц подряд']
    vr = vectorizar(ru)
    chk(similitud(vr[0], vr[1]) > similitud(vr[0], vr[2]),
        'ruso: mismo hecho > hecho ajeno (%.3f vs %.3f)' % (similitud(vr[0], vr[1]), similitud(vr[0], vr[2])))
    zh = ['美国宣布对俄罗斯实施新制裁',
          '美国对俄罗斯实施新的制裁',
          '阿根廷通胀连续第三个月放缓']
    vz = vectorizar(zh)
    chk(similitud(vz[0], vz[1]) > similitud(vz[0], vz[2]),
        'chino: mismo hecho > hecho ajeno (%.3f vs %.3f)' % (similitud(vz[0], vz[1]), similitud(vz[0], vz[2])))
    mix = vectorizar([PRUEBA[0][1], es[0], ru[0], zh[0]])
    print('   LIMITE MEDIDO (no es una falla, es el metodo): el mismo hecho en otro alfabeto no se parece.')
    print('   en-es=%.3f  en-ru=%.3f  en-zh=%.3f' %
          (similitud(mix[0], mix[1]), similitud(mix[0], mix[2]), similitud(mix[0], mix[3])))
    chk(similitud(mix[0], mix[2]) < 0.2 and similitud(mix[0], mix[3]) < 0.2,
        'cross-alfabeto da casi cero (limite conocido, documentado en el docstring)')

    print('== rendimiento ==')
    import time
    grande = textos * 600 + RUIDO * 25          # ~3.600 titulares, el tamano de una corrida real
    t0 = time.time(); vectorizar(grande); dt = time.time() - t0
    print('   %d titulares en %.2f s (%.0f/s)' % (len(grande), dt, len(grande) / max(dt, 1e-9)))
    chk(dt < 30.0, 'vectoriza ~3.600 titulares en menos de 30 s', '%.1f s' % dt)

    print('')
    if fallas:
        print('FALLAS: %d -> %s' % (len(fallas), '; '.join(fallas)))
        return 1
    print('TODO OK')
    return 0

if __name__ == '__main__':
    if '--autotest' in sys.argv: sys.exit(_autotest())
    print(__doc__)
