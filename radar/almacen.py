# -*- coding: utf-8 -*-
"""Capa de datos del Radar: un solo almacen con dos motores detras.

    conectar(None)                 -> SQLite en radar/_radar.db   (desarrollo, tests, cualquier laptop)
    conectar("postgresql://...")   -> Postgres 16 + pgvector      (el VPS)

Las dos formas hablan por sqlalchemy y exponen la MISMA clase `Almacen` (radar/CONTRATO.md). Lo unico
que cambia de verdad entre motores son tres cosas, y estan aisladas en `self.V`, `self.J` y `vecinos`:

  vectores    Postgres guarda `vector(dim)` y busca el vecino con el operador `<=>` (coseno) sobre el
              indice HNSW. SQLite no tiene pgvector: guarda un blob de float32 little-endian y resuelve
              por fuerza bruta con numpy sobre la ventana temporal. Con la ventana de 72 h son unos
              pocos miles de filas: una multiplicacion de matrices y listo.
  arrays/json paises/actores/topics/article_ids son `text[]`/`bigint[]` en Postgres y JSON en SQLite
              (se consultan con json_each, que viene de fabrica). `raw` y `filtro` son jsonb / TEXT.
  fechas      Postgres devuelve timestamptz aware. SQLite guarda ISO-8601 en UTC y `_utc()` lo vuelve
              a convertir en datetime aware al leer. NUNCA sale de aca una fecha naive.

LA INVARIANTE EDITORIAL, que es el motivo por el que este modulo existe:
  un `fact` exige n_indep >= 2 O evidence == 'official_doc'; un `claim` exige `actor`.
En Postgres son dos CHECK del DDL (radar/esquema.sql). Ademas `guardar_statement` las valida en Python
en los DOS motores, antes de tocar la base: en SQLite porque es la unica red que hay, y en Postgres
porque un ValueError con el texto de la regla se lee mucho mejor que un IntegrityError.

Dependencias: numpy y sqlalchemy, las dos ya declaradas en CONTRATO.md. Ninguna nueva.
Autotest:  python radar/almacen.py --autotest      (o  python -m radar.almacen --autotest)
           Corre contra SQLite en un archivo aparte y lo borra al terminar. Si la variable de entorno
           RADAR_DSN tiene un DSN de Postgres, corre la misma bateria tambien ahi; si no, la SALTEA.
"""
import hashlib, json, os, re, sys
from datetime import datetime, timedelta, timezone

import numpy as np
from sqlalchemy import create_engine, event as sa_event, text

BASE = os.path.dirname(os.path.abspath(__file__))
ESQUEMA = os.path.join(BASE, 'esquema.sql')
DB_SQLITE = os.path.join(BASE, '_radar.db')
FUENTES = os.path.join(BASE, 'fuentes.json')

DIM = 384                 # la que dice esquema.sql; conectar(dim=...) la cambia si el vectorizador usa otra
FALLOS_MAX = 3            # tres fallos seguidos y el feed se apaga solo (RADAR.md 2)
TIPOS_ST = ('fact', 'claim', 'disputed')
EVIDENCIAS = ('official_doc', 'satellite', 'own_reporting', 'osint', 'none')
ESTADOS = ('breaking', 'developing', 'watchlist', 'closed')
RIESGOS = ('bajo', 'medio', 'alto')
# lo unico que actualizar_evento deja tocar; cualquier otra clave es un error del llamador
CAMPOS_EV = ('titulo', 'estado', 'importancia', 'video_score', 'paises', 'actores', 'topics',
             'requiere_agustin', 'motivo_bandera', 'riesgo_escalada', 'first_detected', 'last_updated',
             's_fuentes_indep', 's_cross_bloc', 's_velocidad', 's_actores', 's_dominio')
LISTAS_EV = ('paises', 'actores', 'topics')
FECHAS_EV = ('first_detected', 'last_updated')
COLS_ART = ('id,source_id,url,url_hash,title_simhash,wire_origin,title,summary,'
            'published_at,detected_at,lang,event_id,raw')
COLS_EV = ('id,titulo,first_detected,last_updated,estado,importancia,video_score,paises,actores,'
           'topics,requiere_agustin,motivo_bandera,riesgo_escalada,s_fuentes_indep,s_cross_bloc,'
           's_velocidad,s_actores,s_dominio')


def ahora():
    """La unica fuente de 'ahora' del modulo. Siempre UTC aware."""
    return datetime.now(timezone.utc)


def _utc(v):
    """texto ISO / datetime -> datetime aware EN UTC. None pasa de largo.

    Naive se asume UTC; aware en otro huso se CONVIERTE (no alcanza con dejarle su offset). Un RSS
    trae RFC 822 con '-0400' y parsedate_to_datetime devuelve ese offset tal cual: si eso se guardara
    asi, en SQLite las fechas son texto y '12:00:00-04:00' se compara por caracter contra
    '15:00:00+00:00', que es el mismo instante mas una hora y ordena al reves. La ventana de 72 h de
    vecinos()/articulos() se filtra con esa comparacion, o sea que el huso del que escribe decidiria
    que articulos entran al agrupamiento. Normalizar aca -- el unico lugar por donde pasan todas las
    fechas del modulo, de ida y de vuelta -- deja un solo sufijo '+00:00' y el orden del texto vuelve
    a ser el orden del tiempo."""
    if v is None:
        return None
    if isinstance(v, str):
        s = v.strip()
        if s.endswith('Z'):
            s = s[:-1] + '+00:00'
        if len(s) > 10 and s[10] == ' ':
            s = s[:10] + 'T' + s[11:]
        v = datetime.fromisoformat(s)
    return v.astimezone(timezone.utc) if v.tzinfo else v.replace(tzinfo=timezone.utc)


def _i64(v):
    """simhash de 64 bits -> bigint con signo. Sin esto, un simhash >= 2**63 no entra en Postgres."""
    if v is None:
        return None
    v = int(v) & 0xFFFFFFFFFFFFFFFF
    return v - (1 << 64) if v >= (1 << 63) else v


def _u64(v):
    """bigint con signo -> los mismos 64 bits sin signo. El inverso de _i64: el simhash sale como
       entro. Los dos _hamming del repo enmascaran a 64 bits, asi que el signo no les cambiaba la
       cuenta, pero un `bin(x).count('1')` sobre un numero negativo si da cualquier cosa."""
    return None if v is None else int(v) & 0xFFFFFFFFFFFFFFFF


def _vec_np(vec):
    """list / ndarray / blob float32 / texto '[1,2]' de pgvector -> ndarray float32 de una dimension."""
    if vec is None:
        return None
    if isinstance(vec, (bytes, bytearray, memoryview)):
        return np.frombuffer(bytes(vec), dtype='<f4')
    if isinstance(vec, str):
        return np.asarray(json.loads(vec), dtype=np.float32)
    return np.asarray(vec, dtype=np.float32).ravel()


def _norm(a):
    """L2. vectores.py ya normaliza, pero normalizar de nuevo es gratis y hace que el producto punto
       de SQLite y el <=> de pgvector midan exactamente lo mismo."""
    n = float(np.linalg.norm(a))
    return a.astype(np.float32) if n == 0 else (a / n).astype(np.float32)


def _lista_out(v):
    """text[] de Postgres o JSON de SQLite -> lista de Python."""
    if v is None:
        return []
    return list(v) if isinstance(v, (list, tuple)) else json.loads(v)


def _dic_out(v):
    if v is None:
        return {}
    return dict(v) if isinstance(v, dict) else json.loads(v)


def _sin_comentarios(sql):
    """Saca los comentarios de linea. El DDL no tiene cadenas con '--' adentro."""
    return '\n'.join(l.split('--')[0] for l in sql.splitlines())


def _sentencias(sql):
    """Parte un script en sentencias. El DDL no tiene ';' dentro de cadenas ni cuerpos $$."""
    return [s.strip() for s in _sin_comentarios(sql).split(';') if s.strip()]


# El espejo en SQLite de radar/esquema.sql. Mismas tablas, mismas columnas, mismos nombres: el autotest
# compara las dos listas y falla si alguien agrega una columna de un lado y se olvida del otro.
DDL_SQLITE = """
CREATE TABLE IF NOT EXISTS source (
  id TEXT PRIMARY KEY, nombre TEXT NOT NULL, url TEXT NOT NULL,
  source_type TEXT NOT NULL, tier INTEGER NOT NULL, pais TEXT, lang TEXT,
  wire_propio INTEGER DEFAULT 1, primaria INTEGER DEFAULT 0, activa INTEGER DEFAULT 1,
  ultimo_ok TEXT, ultimo_error TEXT, fallos_seguidos INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS event (
  id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT NOT NULL,
  first_detected TEXT NOT NULL, last_updated TEXT NOT NULL,
  estado TEXT DEFAULT 'developing', importancia INTEGER, video_score INTEGER,
  centroide BLOB, paises TEXT, actores TEXT, topics TEXT,
  requiere_agustin INTEGER DEFAULT 0, motivo_bandera TEXT,
  s_fuentes_indep REAL, s_cross_bloc REAL, s_velocidad REAL, s_actores REAL, s_dominio REAL,
  riesgo_escalada TEXT
);
CREATE TABLE IF NOT EXISTS article (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_id TEXT REFERENCES source(id), url TEXT NOT NULL, url_hash TEXT NOT NULL UNIQUE,
  title_simhash INTEGER, wire_origin TEXT, title TEXT NOT NULL, summary TEXT,
  published_at TEXT, detected_at TEXT, lang TEXT, embedding BLOB,
  event_id INTEGER REFERENCES event(id) ON DELETE SET NULL, raw TEXT
);
CREATE INDEX IF NOT EXISTS article_detected_idx ON article (detected_at DESC);
CREATE INDEX IF NOT EXISTS article_event_idx    ON article (event_id);
CREATE INDEX IF NOT EXISTS event_importancia_idx ON event (importancia DESC, last_updated DESC);
CREATE TABLE IF NOT EXISTS statement (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id INTEGER REFERENCES event(id) ON DELETE CASCADE,
  tipo TEXT NOT NULL, texto TEXT NOT NULL, actor TEXT, evidence TEXT, n_indep INTEGER,
  article_ids TEXT, disputa_de INTEGER REFERENCES statement(id), creado TEXT,
  CONSTRAINT claim_necesita_actor CHECK (tipo <> 'claim' OR actor IS NOT NULL),
  CONSTRAINT fact_necesita_dos    CHECK (tipo <> 'fact'  OR n_indep >= 2 OR evidence = 'official_doc')
);
CREATE TABLE IF NOT EXISTS narrative (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id INTEGER REFERENCES event(id) ON DELETE CASCADE,
  bloque TEXT NOT NULL, resumen TEXT NOT NULL, enfasis TEXT, omite TEXT, article_ids TEXT
);
CREATE TABLE IF NOT EXISTS score_history (
  event_id INTEGER REFERENCES event(id) ON DELETE CASCADE,
  t TEXT, importancia INTEGER, n_articulos INTEGER, n_bloques INTEGER
);
CREATE INDEX IF NOT EXISTS score_history_idx ON score_history (event_id, t DESC);
CREATE TABLE IF NOT EXISTS alert_rule (
  id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, filtro TEXT,
  canal TEXT DEFAULT 'telegram', activa INTEGER DEFAULT 1, ultimo_disparo TEXT
);
CREATE TABLE IF NOT EXISTS run_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT, etapa TEXT, t_inicio TEXT, t_fin TEXT,
  ok INTEGER, n_in INTEGER, n_out INTEGER, error TEXT
);
CREATE INDEX IF NOT EXISTS run_log_idx ON run_log (etapa, id DESC);
"""


def conectar(dsn=None, dim=DIM):
    """dsn None -> SQLite en radar/_radar.db (test local). postgresql://... -> Postgres.

    Tambien acepta una ruta de archivo o un sqlite:/// para apuntar a otra base (lo usa el autotest,
    que no toca la base de desarrollo). `dim` es la dimension del vector: esquema.sql la trae en 384 y
    se reemplaza al vuelo si el vectorizador devuelve otra cosa."""
    pg = bool(dsn) and dsn.startswith(('postgresql://', 'postgres://', 'postgresql+'))
    if pg:
        url = dsn.replace('postgres://', 'postgresql://', 1)
    elif dsn and dsn.startswith('sqlite'):
        url = dsn
    else:
        url = 'sqlite+pysqlite:///' + os.path.abspath(dsn or DB_SQLITE)
    eng = create_engine(url, future=True)
    if not pg:
        @sa_event.listens_for(eng, 'connect')
        def _pragmas(dbapi, _rec):        # las FK de SQLite son por conexion y vienen apagadas
            cur = dbapi.cursor()
            cur.execute('PRAGMA foreign_keys=ON')
            cur.execute('PRAGMA journal_mode=WAL')
            cur.close()
    return Almacen(eng, pg, int(dim))


class Almacen:
    """La base del Radar. Una instancia por proceso; los metodos abren su propia transaccion."""

    def __init__(self, eng, pg, dim):
        self.eng, self.pg, self.dim = eng, pg, dim
        self.V = 'CAST(:vec AS vector)' if pg else ':vec'    # como se escribe un vector en cada motor
        self.J = 'CAST(:{0} AS jsonb)' if pg else ':{0}'     # y como se escribe un json

    # ---------------------------------------------------------------- utilidades internas
    def _j(self, campo):
        return self.J.format(campo)

    def _t(self, v):
        """fecha hacia la base: aware en Postgres, ISO-8601 UTC en SQLite."""
        v = _utc(v)
        return v if (v is None or self.pg) else v.isoformat()

    def _lista(self, v):
        """lista hacia la base: nativa en Postgres, JSON en SQLite. Vacia -> NULL (en Postgres un
           ARRAY[] sin tipo no se puede adaptar, y NULL y [] significan lo mismo para nosotros)."""
        v = list(v) if v else None
        if v is None:
            return None
        return v if self.pg else json.dumps(v, ensure_ascii=False)

    def _vp(self, vec):
        """vector hacia la base: texto '[..]' para pgvector, blob float32 para SQLite. Siempre L2."""
        if vec is None:
            return None
        a = _norm(_vec_np(vec))
        return '[' + ','.join('%.7g' % x for x in a) + ']' if self.pg else a.tobytes()

    def _en(self, campo, val, tipo='text'):
        """fragmento 'val = ANY(columna)' segun motor, para paises/actores/topics."""
        if self.pg:
            return ' AND :%s = ANY(%s)' % (val, campo)
        return (' AND %s IS NOT NULL AND EXISTS (SELECT 1 FROM json_each(event.%s) WHERE value = :%s)'
                % (campo, campo, val))

    def _art(self, f):
        d = dict(f)
        d['published_at'] = _utc(d.get('published_at'))
        d['detected_at'] = _utc(d.get('detected_at'))
        d['title_simhash'] = _u64(d.get('title_simhash'))
        d['raw'] = _dic_out(d.get('raw'))
        return d

    def _ev(self, f):
        d = dict(f)
        for k in FECHAS_EV:
            d[k] = _utc(d.get(k))
        for k in LISTAS_EV:
            d[k] = _lista_out(d.get(k))
        d['requiere_agustin'] = bool(d.get('requiere_agustin'))
        return d

    @staticmethod
    def _filas(res):
        return [dict(r._mapping) for r in res]

    def _todos(self, q, **p):
        with self.eng.begin() as c:
            return self._filas(c.execute(text(q), p))

    def _uno(self, q, **p):
        f = self._todos(q, **p)
        return f[0] if f else None

    # ---------------------------------------------------------------- esquema
    def init_esquema(self):
        """Crea el esquema si falta. Idempotente: se puede llamar en cada arranque."""
        if self.pg:
            with open(ESQUEMA, encoding='utf-8') as fh:
                sql = fh.read()
            if self.dim != DIM:
                sql = sql.replace('vector(%d)' % DIM, 'vector(%d)' % self.dim)
        else:
            sql = DDL_SQLITE
        with self.eng.begin() as c:
            for s in _sentencias(sql):
                c.exec_driver_sql(s)

    # ---------------------------------------------------------------- fuentes
    def cargar_fuentes(self, path_json=FUENTES):
        """Vuelca fuentes.json['feeds'] en source y devuelve cuantas quedaron activas.

        Al recargar actualiza la ficha (nombre, url, tier, tipo...) pero NO pisa el estado de salud:
        si el chequeo de frescura apago un feed zombie, recargar el catalogo no lo resucita. Las
        entradas con clave 'ESTADO' (feeds que responden 200 y estan congelados por dentro: WSJ,
        Global Times) entran desactivadas de arranque."""
        with open(path_json, encoding='utf-8') as fh:
            d = json.load(fh)
        q = """INSERT INTO source (id,nombre,url,source_type,tier,pais,lang,wire_propio,primaria,activa)
               VALUES (:id,:nombre,:url,:tipo,:tier,:pais,:lang,:wire,:prim,:activa)
               ON CONFLICT (id) DO UPDATE SET nombre=excluded.nombre, url=excluded.url,
                 source_type=excluded.source_type, tier=excluded.tier, pais=excluded.pais,
                 lang=excluded.lang, wire_propio=excluded.wire_propio, primaria=excluded.primaria"""
        filas = [{'id': f['id'], 'nombre': f.get('nombre', f['id']), 'url': f['url'],
                  'tipo': f.get('tipo', 'western'), 'tier': int(f.get('tier', 3)),
                  'pais': f.get('pais'), 'lang': f.get('lang'),
                  'wire': bool(f.get('wire_propio', True)), 'prim': bool(f.get('primaria', False)),
                  'activa': 'ESTADO' not in f} for f in d.get('feeds', [])]
        with self.eng.begin() as c:
            if filas:
                c.execute(text(q), filas)          # executemany: las 81 fuentes en una transaccion
            return int(c.execute(text('SELECT count(*) FROM source WHERE activa')).scalar())

    def fuentes(self, solo_activas=True):
        q = ('SELECT id,nombre,url,source_type,tier,pais,lang,wire_propio,primaria,activa,'
             'ultimo_ok,ultimo_error,fallos_seguidos FROM source')
        if solo_activas:
            q += ' WHERE activa'
        fs = self._todos(q + ' ORDER BY tier, id')
        for f in fs:
            f['ultimo_ok'] = _utc(f['ultimo_ok'])
            for k in ('wire_propio', 'primaria', 'activa'):
                f[k] = bool(f[k])
        return fs

    def marcar_fuente(self, source_id, ok, error=None, desactivar=None):
        """Salud del feed. ok=True limpia el contador; ok=False lo incrementa y, al llegar a
           FALLOS_MAX, apaga la fuente sola. `desactivar=True` apaga ya mismo sin esperar los tres
           fallos (lo usa el chequeo de frescura de ingesta.tick); `desactivar=False` cancela el
           apagado automatico de esta llamada. Ninguna de las dos RE-ENCIENDE una fuente ya apagada:
           volver a prenderla es a mano, a proposito (RADAR.md 2)."""
        with self.eng.begin() as c:
            if ok:
                c.execute(text('UPDATE source SET ultimo_ok=:t, ultimo_error=NULL, fallos_seguidos=0 '
                               'WHERE id=:id'), {'t': self._t(ahora()), 'id': source_id})
            else:
                c.execute(text('UPDATE source SET ultimo_error=:e, fallos_seguidos=fallos_seguidos+1 '
                               'WHERE id=:id'), {'e': error, 'id': source_id})
            n = c.execute(text('SELECT fallos_seguidos FROM source WHERE id=:id'),
                          {'id': source_id}).scalar()
            apagar = desactivar if desactivar is not None else (not ok and (n or 0) >= FALLOS_MAX)
            if apagar:
                c.execute(text('UPDATE source SET activa=:f WHERE id=:id'),
                          {'f': False, 'id': source_id})

    # ---------------------------------------------------------------- articulos
    def guardar_articulo(self, art):
        """Devuelve el id nuevo, o None si el url_hash ya estaba (dedup exacto, RADAR.md 7)."""
        for k in ('source_id', 'url', 'title'):
            if not art.get(k):
                raise ValueError('articulo sin %s: %r' % (k, art.get('url') or art.get('title')))
        uh = art.get('url_hash') or hashlib.sha1(art['url'].encode('utf-8')).hexdigest()
        p = {'source_id': art['source_id'], 'url': art['url'], 'url_hash': uh,
             'title_simhash': _i64(art.get('title_simhash')), 'wire_origin': art.get('wire_origin'),
             'title': art['title'], 'summary': art.get('summary'),
             'published_at': self._t(art.get('published_at')),
             'detected_at': self._t(art.get('detected_at') or ahora()),
             'lang': art.get('lang'), 'event_id': art.get('event_id'),
             'raw': json.dumps(art.get('raw') or {}, ensure_ascii=False, default=str)}
        q = ("""INSERT INTO article (source_id,url,url_hash,title_simhash,wire_origin,title,summary,
                published_at,detected_at,lang,event_id,raw)
                VALUES (:source_id,:url,:url_hash,:title_simhash,:wire_origin,:title,:summary,
                :published_at,:detected_at,:lang,:event_id,%s)
                ON CONFLICT (url_hash) DO NOTHING RETURNING id""" % self._j('raw'))
        with self.eng.begin() as c:
            r = c.execute(text(q), p).first()
        return int(r[0]) if r else None

    def articulos(self, desde=None, sin_evento=False, limite=500):
        q = 'SELECT %s FROM article WHERE 1=1' % COLS_ART
        p = {'lim': int(limite)}
        if desde is not None:
            q += ' AND detected_at >= :desde'
            p['desde'] = self._t(desde)
        if sin_evento:
            q += ' AND event_id IS NULL'
        return [self._art(f) for f in self._todos(q + ' ORDER BY detected_at DESC, id DESC LIMIT :lim', **p)]

    # ---------------------------------------------------------------- vectores y vecinos
    def guardar_vector(self, article_id, vec):
        with self.eng.begin() as c:
            c.execute(text('UPDATE article SET embedding=%s WHERE id=:id' % self.V),
                      {'vec': self._vp(vec), 'id': int(article_id)})

    def vecinos(self, vec, desde, umbral=0.78, limite=20):
        """(article_id, event_id, similitud) de los articulos CON evento dentro de la ventana.

        Postgres: ORDER BY con el operador de distancia de pgvector, que es lo que usa el indice HNSW;
        el umbral se aplica despues (filtrar antes de ordenar le saca el indice). SQLite: fuerza bruta
        con numpy sobre las filas de la ventana, que con 72 h son unos pocos miles."""
        if vec is None:
            return []
        cond = 'event_id IS NOT NULL AND embedding IS NOT NULL'
        p = {}
        if desde is not None:
            cond += ' AND detected_at >= :desde'
            p['desde'] = self._t(desde)
        if self.pg:
            p['vec'] = self._vp(vec)
            p['lim'] = int(limite)
            q = ('SELECT id, event_id, 1 - (embedding <=> {0}) AS sim FROM article WHERE {1} '
                 'ORDER BY embedding <=> {0} LIMIT :lim').format(self.V, cond)
            filas = self._todos(q, **p)
            return [(int(f['id']), int(f['event_id']), float(f['sim']))
                    for f in filas if float(f['sim']) >= umbral]
        filas = self._todos('SELECT id, event_id, embedding FROM article WHERE ' + cond, **p)
        if not filas:
            return []
        v = _norm(_vec_np(vec))
        ids, evs, mat = [], [], []
        for f in filas:
            a = _vec_np(f['embedding'])
            if a is None or a.shape[0] != v.shape[0]:     # vector de otra dimension: no es comparable
                continue
            ids.append(int(f['id'])); evs.append(int(f['event_id'])); mat.append(_norm(a))
        if not ids:
            return []
        sims = np.asarray(mat, dtype=np.float32) @ v
        orden = np.argsort(-sims)[:int(limite)]
        return [(ids[i], evs[i], float(sims[i])) for i in orden if float(sims[i]) >= umbral]

    # ---------------------------------------------------------------- eventos
    def crear_evento(self, titulo, articulo_id, vec):
        """Evento nuevo con un articulo semilla. El centroide arranca siendo su vector."""
        a = self._uno('SELECT detected_at FROM article WHERE id=:id', id=int(articulo_id))
        t = _utc(a['detected_at']) if a and a.get('detected_at') else ahora()
        p = {'titulo': titulo, 'fd': self._t(t), 'lu': self._t(ahora()), 'vec': self._vp(vec)}
        with self.eng.begin() as c:
            ev = c.execute(text('INSERT INTO event (titulo,first_detected,last_updated,estado,centroide) '
                                "VALUES (:titulo,:fd,:lu,'developing',%s) RETURNING id" % self.V),
                           p).scalar()
            c.execute(text('UPDATE article SET event_id=:ev, embedding=%s WHERE id=:id' % self.V),
                      {'ev': int(ev), 'vec': p['vec'], 'id': int(articulo_id)})
        return int(ev)

    def adjuntar(self, evento_id, articulo_id, vec):
        """Suma el articulo al evento y corre el centroide. El centroide es la media movil de los
           vectores de sus articulos, renormalizada: no hace falta releer todos los miembros."""
        evento_id, articulo_id = int(evento_id), int(articulo_id)
        with self.eng.begin() as c:
            n = c.execute(text('SELECT count(*) FROM article WHERE event_id=:ev'), {'ev': evento_id}).scalar()
            cen = c.execute(text('SELECT centroide FROM event WHERE id=:ev'), {'ev': evento_id}).scalar()
            nuevo = _norm(_vec_np(vec))
            viejo = _vec_np(cen)
            if viejo is not None and viejo.shape == nuevo.shape and n:
                nuevo = _norm((_norm(viejo) * n + nuevo) / (n + 1))
            c.execute(text('UPDATE article SET event_id=:ev, embedding=%s WHERE id=:id' % self.V),
                      {'ev': evento_id, 'vec': self._vp(vec), 'id': articulo_id})
            c.execute(text('UPDATE event SET centroide=%s, last_updated=:lu WHERE id=:ev' % self.V),
                      {'vec': self._vp(nuevo), 'lu': self._t(ahora()), 'ev': evento_id})

    def actualizar_evento(self, evento_id, **campos):
        """Escribe los campos del EVENTO (solo los de CAMPOS_EV). Toca last_updated sola si no vino.
           Si viene `importancia`, deja ademas una fila en score_history: es de donde sale despues la
           diferencia entre un evento que crece (developing) y uno que se apago."""
        evento_id = int(evento_id)
        raras = [k for k in campos if k not in CAMPOS_EV]
        if raras:
            raise ValueError('campos de evento desconocidos: %s' % ', '.join(sorted(raras)))
        if campos.get('estado') is not None and campos['estado'] not in ESTADOS:
            raise ValueError('estado invalido: %r (esperaba %s)' % (campos['estado'], '|'.join(ESTADOS)))
        if campos.get('riesgo_escalada') is not None and campos['riesgo_escalada'] not in RIESGOS:
            raise ValueError('riesgo_escalada invalido: %r' % (campos['riesgo_escalada'],))
        if not campos:
            return
        campos.setdefault('last_updated', ahora())
        sets, p = [], {'ev': evento_id}
        for k, v in campos.items():
            if k in LISTAS_EV:
                v = self._lista(v)
            elif k in FECHAS_EV:
                v = self._t(v)
            elif k == 'requiere_agustin':
                v = bool(v)
            sets.append('%s=:%s' % (k, k))
            p[k] = v
        with self.eng.begin() as c:
            c.execute(text('UPDATE event SET %s WHERE id=:ev' % ', '.join(sets)), p)
            if campos.get('importancia') is not None:
                h = c.execute(text('SELECT count(*) AS n, count(DISTINCT s.source_type) AS b '
                                   'FROM article a LEFT JOIN source s ON s.id=a.source_id '
                                   'WHERE a.event_id=:ev'), {'ev': evento_id}).first()
                c.execute(text('INSERT INTO score_history (event_id,t,importancia,n_articulos,n_bloques) '
                               'VALUES (:ev,:t,:i,:n,:b)'),
                          {'ev': evento_id, 't': self._t(ahora()), 'i': int(campos['importancia']),
                           'n': int(h[0] or 0), 'b': int(h[1] or 0)})

    def importancia_previa(self, evento_id, antes_de=None):
        """La importancia ANTERIOR a la vigente, leida de score_history. None si todavia no hay con
           que comparar. Es lo que separa un evento que crece (developing) de uno que se apago;
           lo consume agrupar.estados(). No esta en CONTRATO.md: es un agregado, no un cambio."""
        q = 'SELECT importancia FROM score_history WHERE event_id=:ev'
        p = {'ev': int(evento_id)}
        if antes_de is not None:
            q += ' AND t < :t ORDER BY t DESC LIMIT 1'
            p['t'] = self._t(antes_de)
        else:
            q += ' ORDER BY t DESC LIMIT 1 OFFSET 1'     # la vigente es la primera; queremos la de antes
        f = self._uno(q, **p)
        return None if not f or f['importancia'] is None else int(f['importancia'])

    def evento(self, evento_id):
        """El EVENTO completo: la ficha mas sus articulos, statements y narrativas."""
        evento_id = int(evento_id)
        f = self._uno('SELECT %s FROM event WHERE id=:ev' % COLS_EV, ev=evento_id)
        if not f:
            return None
        d = self._ev(f)
        d['articulos'] = [self._art(a) for a in self._todos(
            'SELECT %s FROM article WHERE event_id=:ev ORDER BY detected_at, id' % COLS_ART, ev=evento_id)]
        d['statements'] = [self._st(s) for s in self._todos(
            'SELECT id,event_id,tipo,texto,actor,evidence,n_indep,article_ids,disputa_de,creado '
            'FROM statement WHERE event_id=:ev ORDER BY id', ev=evento_id)]
        d['narrativas'] = [self._na(n) for n in self._todos(
            'SELECT id,event_id,bloque,resumen,enfasis,omite,article_ids FROM narrative '
            'WHERE event_id=:ev ORDER BY id', ev=evento_id)]
        return d

    def buscar_eventos(self, pais=None, actor=None, topic=None, desde=None, hasta=None,
                       min_importancia=None, min_video=None, estado=None, limite=50):
        q = 'SELECT %s FROM event WHERE 1=1' % COLS_EV
        p = {'lim': int(limite)}
        if pais:
            q += self._en('paises', 'pais'); p['pais'] = pais
        if actor:
            q += self._en('actores', 'actor'); p['actor'] = actor
        if topic:
            q += self._en('topics', 'topic'); p['topic'] = topic
        if desde is not None:
            q += ' AND last_updated >= :desde'; p['desde'] = self._t(desde)
        if hasta is not None:
            q += ' AND last_updated <= :hasta'; p['hasta'] = self._t(hasta)
        if min_importancia is not None:
            q += ' AND importancia >= :mi'; p['mi'] = int(min_importancia)
        if min_video is not None:
            q += ' AND video_score >= :mv'; p['mv'] = int(min_video)
        if estado:
            q += ' AND estado = :estado'; p['estado'] = estado
        q += ' ORDER BY importancia DESC NULLS LAST, last_updated DESC LIMIT :lim'
        return [self._ev(f) for f in self._todos(q, **p)]

    # ---------------------------------------------------------------- statements y narrativas
    def _st(self, f):
        d = dict(f)
        d['article_ids'] = [int(x) for x in _lista_out(d.get('article_ids'))]
        d['creado'] = _utc(d.get('creado'))
        return d

    def _na(self, f):
        d = dict(f)
        d['article_ids'] = [int(x) for x in _lista_out(d.get('article_ids'))]
        return d

    @staticmethod
    def validar_statement(st):
        """LA invariante del sistema, en Python, para los dos motores (en Postgres ademas hay CHECK).

        Un `fact` con una sola fuente independiente NO EXISTE (RADAR.md 5): si solo lo tiene una
        redaccion, es un `claim` con esa redaccion como actor. La unica excepcion es el documento
        oficial del actor que hizo la cosa, que se sostiene solo."""
        tipo = st.get('tipo')
        if tipo not in TIPOS_ST:
            raise ValueError('tipo de statement invalido: %r (esperaba %s)' % (tipo, '|'.join(TIPOS_ST)))
        if not (st.get('texto') or '').strip():
            raise ValueError('statement sin texto')
        ev = st.get('evidence') or 'none'
        if ev not in EVIDENCIAS:
            raise ValueError('evidence invalida: %r (esperaba %s)' % (ev, '|'.join(EVIDENCIAS)))
        if tipo == 'claim' and not (st.get('actor') or '').strip():
            raise ValueError("un claim exige actor: quien lo dice va con el texto, no se pierde. "
                             "texto=%r" % st.get('texto')[:80])
        if tipo == 'fact' and int(st.get('n_indep') or 0) < 2 and ev != 'official_doc':
            raise ValueError("un fact exige n_indep>=2 o evidence='official_doc'; llegaron n_indep=%s "
                             "evidence=%r. Con una sola fuente esto es un claim, no un hecho. texto=%r"
                             % (st.get('n_indep'), ev, st.get('texto')[:80]))

    def guardar_statement(self, evento_id, st):
        """Guarda un fact/claim/disputed. Levanta ValueError si rompe la invariante editorial."""
        self.validar_statement(st)
        p = {'ev': int(evento_id), 'tipo': st['tipo'], 'texto': st['texto'], 'actor': st.get('actor'),
             'evidence': st.get('evidence') or 'none', 'n_indep': int(st.get('n_indep') or 0),
             'ids': self._lista([int(x) for x in (st.get('article_ids') or [])]),
             'dis': int(st['disputa_de']) if st.get('disputa_de') else None, 't': self._t(ahora())}
        with self.eng.begin() as c:
            return int(c.execute(text(
                'INSERT INTO statement (event_id,tipo,texto,actor,evidence,n_indep,article_ids,'
                'disputa_de,creado) VALUES (:ev,:tipo,:texto,:actor,:evidence,:n_indep,:ids,:dis,:t) '
                'RETURNING id'), p).scalar())

    def guardar_narrativa(self, evento_id, na):
        """Como cuenta el evento un bloque: que resume, que enfatiza y que OMITE (lo mas revelador)."""
        if not (na.get('bloque') or '').strip() or not (na.get('resumen') or '').strip():
            raise ValueError('narrativa sin bloque o sin resumen')
        p = {'ev': int(evento_id), 'bloque': na['bloque'], 'resumen': na['resumen'],
             'enfasis': na.get('enfasis'), 'omite': na.get('omite'),
             'ids': self._lista([int(x) for x in (na.get('article_ids') or [])])}
        with self.eng.begin() as c:
            return int(c.execute(text(
                'INSERT INTO narrative (event_id,bloque,resumen,enfasis,omite,article_ids) '
                'VALUES (:ev,:bloque,:resumen,:enfasis,:omite,:ids) RETURNING id'), p).scalar())

    # ---------------------------------------------------------------- bitacora de corridas
    def registrar(self, etapa, ok, n_in=0, n_out=0, error=None, t_inicio=None):
        """Una linea por etapa corrida. De aca sale la idempotencia de daily.py (si la etapa ya
           salio OK para esa fecha, se saltea) y el control de por que modelo salio cada llamada."""
        t = ahora()
        with self.eng.begin() as c:
            c.execute(text('INSERT INTO run_log (etapa,t_inicio,t_fin,ok,n_in,n_out,error) '
                           'VALUES (:e,:ti,:tf,:ok,:ni,:no,:err)'),
                      {'e': etapa, 'ti': self._t(t_inicio or t), 'tf': self._t(t), 'ok': bool(ok),
                       'ni': int(n_in), 'no': int(n_out), 'err': error})

    def ultima_corrida(self, etapa, solo_ok=False):
        q = 'SELECT id,etapa,t_inicio,t_fin,ok,n_in,n_out,error FROM run_log WHERE etapa=:e'
        if solo_ok:
            q += ' AND ok'
        f = self._uno(q + ' ORDER BY id DESC LIMIT 1', e=etapa)
        if not f:
            return None
        f['t_inicio'], f['t_fin'], f['ok'] = _utc(f['t_inicio']), _utc(f['t_fin']), bool(f['ok'])
        return f


# ====================================================================== autotest
_FALLAS = []


def _chk(cond, msg):
    print(('OK    ' if cond else 'FALLA ') + msg)
    if not cond:
        _FALLAS.append(msg)


def _levanta(fn, msg):
    """Espera un ValueError. Que la invariante RECHACE es tan importante como que acepte."""
    try:
        fn()
    except ValueError as e:
        print('OK    %s -> ValueError: %s' % (msg, str(e).split('.')[0][:90]))
        return
    except Exception as e:
        _chk(False, '%s -> esperaba ValueError y vino %s: %s' % (msg, type(e).__name__, e))
        return
    _chk(False, '%s -> NO levanto nada (la invariante no esta puesta)' % msg)


def _cols_ddl(txt):
    """{tabla: [columnas]} leyendo los CREATE TABLE de un script SQL. Sirve para que el DDL de
       Postgres y el espejo de SQLite no se separen sin que nadie se entere."""
    txt = _sin_comentarios(txt)
    out = {}
    for m in re.finditer(r'CREATE TABLE (?:IF NOT EXISTS )?(\w+)\s*\(', txt, re.I):
        i, prof = m.end(), 1
        while prof and i < len(txt):
            prof += (txt[i] == '(') - (txt[i] == ')')
            i += 1
        cuerpo, cols, frag, prof = txt[m.end():i - 1], [], '', 0
        for ch in cuerpo:
            prof += (ch == '(') - (ch == ')')
            if ch == ',' and prof == 0:
                cols.append(frag); frag = ''
            else:
                frag += ch
        cols.append(frag)
        limpias = []
        for c in cols:
            c = c.strip()
            if not c or c.split()[0].upper() in ('CONSTRAINT', 'PRIMARY', 'UNIQUE', 'CHECK', 'FOREIGN'):
                continue
            limpias.append(c.split()[0].lower())
        out[m.group(1).lower()] = limpias
    return out


def _bateria(al, etiqueta):
    """La misma prueba contra cualquier motor. La corre SQLite siempre y Postgres si hay RADAR_DSN."""
    print('\n--- %s ---' % etiqueta)
    t0 = ahora()
    al.init_esquema()
    al.init_esquema()                                        # idempotente: dos veces no rompe
    _chk(True, 'init_esquema corre dos veces sin romper')

    n = al.cargar_fuentes(FUENTES)
    n2 = al.cargar_fuentes(FUENTES)
    _chk(n > 60 and n == n2, 'cargar_fuentes: %d activas, y recargar no duplica (%d)' % (n, n2))
    fs = al.fuentes()
    ids = {f['id'] for f in fs}
    _chk('bbc_world' in ids, 'fuentes(): bbc_world esta en el catalogo')
    _chk('wsj_world' not in ids, 'fuentes(): wsj_world (feed congelado, clave ESTADO) entra apagado')
    _chk(len(al.fuentes(solo_activas=False)) > len(fs), 'fuentes(solo_activas=False) trae las apagadas')

    # --- articulos y dedup por url_hash
    base = {'source_id': 'bbc_world', 'wire_origin': 'reuters', 'lang': 'en'}
    a1 = al.guardar_articulo(dict(base, url='https://bbc.com/1', url_hash='h1',
                                  title='China halts rare earth exports to the US',
                                  title_simhash=(1 << 63) + 7,       # 64 bits sin signo: no debe desbordar
                                  detected_at=t0 - timedelta(hours=2),
                                  published_at=t0 - timedelta(hours=3), raw={'feed': 'bbc'}))
    a2 = al.guardar_articulo(dict(base, source_id='gn_reuters', url='https://reuters.com/2', url_hash='h2',
                                  title='Beijing suspends rare earth shipments',
                                  detected_at=t0 - timedelta(hours=1)))
    a3 = al.guardar_articulo(dict(base, source_id='tass_en', url='https://tass.com/3', url_hash='h3',
                                  title='Baltic pipeline damaged', detected_at=t0 - timedelta(hours=1)))
    a4 = al.guardar_articulo(dict(base, source_id='tass_en', url='https://tass.com/4', url_hash='h4',
                                  title='Vieja de hace diez dias', detected_at=t0 - timedelta(days=10)))
    dup = al.guardar_articulo(dict(base, url='https://bbc.com/1-otra-ruta', url_hash='h1',
                                   title='El mismo cable republicado'))
    _chk(all(isinstance(x, int) for x in (a1, a2, a3, a4)), 'guardar_articulo devuelve ids: %s' % [a1, a2, a3, a4])
    _chk(dup is None, 'guardar_articulo devuelve None con url_hash repetido (dedup exacto)')
    _levanta(lambda: al.guardar_articulo({'url': 'x', 'title': 'y'}), 'articulo sin source_id')

    arts = al.articulos(limite=10)
    _chk(len(arts) == 4, 'articulos(): %d filas' % len(arts))
    _chk(all(a['detected_at'].tzinfo is not None for a in arts), 'toda fecha que sale es UTC aware')
    _chk(arts[0]['raw'] == {} or isinstance(arts[0]['raw'], dict), 'raw vuelve como dict')
    uno = [a for a in arts if a['id'] == a1][0]
    _chk(uno['raw'] == {'feed': 'bbc'} and uno['wire_origin'] == 'reuters', 'raw y wire_origin ida y vuelta')
    _chk(len(al.articulos(sin_evento=True)) == 4, 'articulos(sin_evento=True) los trae todos todavia')

    # --- vectores, evento y vecinos
    d = al.dim
    v1 = np.zeros(d, dtype=np.float32); v1[0] = 1.0
    v1b = np.zeros(d, dtype=np.float32); v1b[0] = 0.97; v1b[1] = 0.24     # coseno ~0.97 con v1
    v2 = np.zeros(d, dtype=np.float32); v2[5] = 1.0                       # ortogonal
    ev1 = al.crear_evento('China frena las tierras raras', a1, v1)
    _chk(isinstance(ev1, int) and ev1 > 0, 'crear_evento -> id %s' % ev1)
    _chk(len(al.articulos(sin_evento=True)) == 3, 'el articulo semilla quedo enganchado al evento')

    vec = al.vecinos(v1b, desde=t0 - timedelta(hours=72))
    _chk(len(vec) == 1 and vec[0][0] == a1 and vec[0][1] == ev1 and vec[0][2] > 0.9,
         'vecinos() devuelve el articulo correcto: %s' % (vec,))
    _chk(al.vecinos(v2, desde=t0 - timedelta(hours=72)) == [],
         'vecinos() no devuelve nada por debajo del umbral (vector ortogonal)')

    al.adjuntar(ev1, a2, v1b)
    _chk(len(al.vecinos(v1, desde=t0 - timedelta(hours=72))) == 2, 'adjuntar() suma el articulo al evento')
    _chk(len(al.articulos(sin_evento=True)) == 2, 'quedan 2 articulos sin evento')

    ev2 = al.crear_evento('Evento viejo, fuera de la ventana', a4, v2)
    _chk(al.vecinos(v2, desde=t0 - timedelta(hours=72)) == [],
         'vecinos() respeta la ventana: el evento de hace 10 dias no aparece')
    vv = al.vecinos(v2, desde=t0 - timedelta(days=30))
    _chk(len(vv) == 1 and vv[0][1] == ev2, 'con la ventana ancha si aparece: %s' % (vv,))
    _chk(al.vecinos(v1b, desde=None, limite=1) and len(al.vecinos(v1b, desde=None, limite=1)) == 1,
         'vecinos() respeta el limite')

    # --- statements: la invariante editorial
    st_ok = al.guardar_statement(ev1, {'tipo': 'fact', 'texto': 'Pekin suspendio los envios',
                                       'evidence': 'own_reporting', 'n_indep': 2, 'article_ids': [a1, a2]})
    st_doc = al.guardar_statement(ev1, {'tipo': 'fact', 'texto': 'El MOFCOM publico la resolucion',
                                        'evidence': 'official_doc', 'n_indep': 1})
    st_cl = al.guardar_statement(ev1, {'tipo': 'claim', 'actor': 'RU_MoD',
                                       'texto': 'derribo 20 drones ucranianos', 'evidence': 'none'})
    st_di = al.guardar_statement(ev1, {'tipo': 'disputed', 'texto': 'cuantos drones fueron',
                                       'evidence': 'none', 'disputa_de': st_cl})
    _chk(all(isinstance(x, int) for x in (st_ok, st_doc, st_cl, st_di)),
         'guardar_statement acepta fact(2 fuentes), fact(official_doc), claim(con actor) y disputed')
    _levanta(lambda: al.guardar_statement(ev1, {'tipo': 'fact', 'texto': 'lo dijo una sola redaccion',
                                                'evidence': 'own_reporting', 'n_indep': 1}),
             'RECHAZA fact con n_indep=1')
    _levanta(lambda: al.guardar_statement(ev1, {'tipo': 'fact', 'texto': 'sin evidencia ni fuentes',
                                                'evidence': 'none', 'n_indep': 0}),
             'RECHAZA fact sin fuentes ni documento')
    _levanta(lambda: al.guardar_statement(ev1, {'tipo': 'claim', 'texto': 'alguien dijo algo',
                                                'evidence': 'osint'}),
             'RECHAZA claim sin actor')
    _levanta(lambda: al.guardar_statement(ev1, {'tipo': 'hecho', 'texto': 'x', 'n_indep': 9}),
             'RECHAZA un tipo que no existe')
    _levanta(lambda: al.guardar_statement(ev1, {'tipo': 'fact', 'texto': '', 'n_indep': 3}),
             'RECHAZA statement sin texto')

    # --- narrativas
    n1 = al.guardar_narrativa(ev1, {'bloque': 'western', 'resumen': 'Pekin usa las tierras raras como arma',
                                    'enfasis': 'dependencia occidental', 'omite': 'los controles de EEUU',
                                    'article_ids': [a1]})
    n2_ = al.guardar_narrativa(ev1, {'bloque': 'chinese', 'resumen': 'Medida tecnica y temporal',
                                     'enfasis': 'legalidad', 'omite': 'el impacto en la cadena',
                                     'article_ids': [a2]})
    _chk(isinstance(n1, int) and isinstance(n2_, int), 'guardar_narrativa devuelve ids')
    _levanta(lambda: al.guardar_narrativa(ev1, {'bloque': 'western'}), 'RECHAZA narrativa sin resumen')

    # --- ficha completa y busqueda
    al.actualizar_evento(ev1, importancia=82, video_score=91, estado='breaking',
                         paises=['CN', 'US'], actores=['China', 'Estados Unidos'], topics=['tierras raras'],
                         requiere_agustin=True, motivo_bandera='zona sensible', riesgo_escalada='medio')
    e = al.evento(ev1)
    _chk(e['importancia'] == 82 and e['estado'] == 'breaking' and e['requiere_agustin'] is True,
         'actualizar_evento + evento(): score, estado y bandera')
    _chk(e['paises'] == ['CN', 'US'] and e['topics'] == ['tierras raras'], 'las listas van y vuelven')
    _chk(len(e['articulos']) == 2 and len(e['statements']) == 4 and len(e['narrativas']) == 2,
         'evento() trae %d articulos, %d statements, %d narrativas'
         % (len(e['articulos']), len(e['statements']), len(e['narrativas'])))
    _chk(e['statements'][0]['article_ids'] == [a1, a2], 'article_ids del statement ida y vuelta')
    _chk(e['last_updated'].tzinfo is not None and e['first_detected'] <= e['last_updated'],
         'first_detected <= last_updated, las dos aware')
    _levanta(lambda: al.actualizar_evento(ev1, importanica=9), 'RECHAZA un campo de evento mal escrito')
    _levanta(lambda: al.actualizar_evento(ev1, estado='zombie'), 'RECHAZA un estado que no existe')

    sh = al._todos('SELECT * FROM score_history WHERE event_id=:e', e=ev1)
    _chk(len(sh) == 1 and sh[0]['importancia'] == 82 and sh[0]['n_articulos'] == 2,
         'score_history registro el cambio de importancia (%s)' % (sh and sh[0]['n_bloques'],))
    _chk(al.importancia_previa(ev1) is None, 'importancia_previa con una sola medicion -> None')
    al.actualizar_evento(ev1, importancia=88)
    _chk(al.importancia_previa(ev1) == 82 and al.evento(ev1)['importancia'] == 88,
         'importancia_previa devuelve la anterior (82) y el evento tiene la vigente (88)')

    _chk([x['id'] for x in al.buscar_eventos(pais='CN')] == [ev1], 'buscar_eventos por pais')
    _chk([x['id'] for x in al.buscar_eventos(actor='China', min_importancia=80)] == [ev1],
         'buscar_eventos por actor + min_importancia')
    _chk(al.buscar_eventos(pais='AR') == [], 'buscar_eventos por un pais que no esta -> vacio')
    _chk(al.buscar_eventos(min_importancia=90) == [], 'buscar_eventos con umbral alto -> vacio')
    _chk([x['id'] for x in al.buscar_eventos(topic='tierras raras', estado='breaking')] == [ev1],
         'buscar_eventos por topic + estado')
    _chk([x['id'] for x in al.buscar_eventos(min_video=90)] == [ev1], 'buscar_eventos por video_score')
    _chk(al.evento(999999) is None, 'evento() inexistente -> None')

    # --- salud de fuentes
    for i in range(FALLOS_MAX):
        al.marcar_fuente('tass_en', ok=False, error='timeout %d' % i)
    f = [x for x in al.fuentes(solo_activas=False) if x['id'] == 'tass_en'][0]
    _chk(f['fallos_seguidos'] == FALLOS_MAX and not f['activa'],
         'marcar_fuente apaga la fuente a los %d fallos seguidos' % FALLOS_MAX)
    al.marcar_fuente('tass_en', ok=True)
    f = [x for x in al.fuentes(solo_activas=False) if x['id'] == 'tass_en'][0]
    _chk(f['fallos_seguidos'] == 0 and f['ultimo_ok'] is not None and f['ultimo_ok'].tzinfo is not None,
         'marcar_fuente(ok=True) limpia el contador y sella ultimo_ok en UTC')
    _chk(not f['activa'], 'una fuente apagada NO se reenciende sola: volver a prenderla es a mano')
    al.marcar_fuente('rt_news', ok=True, desactivar=True)
    _chk(not [x for x in al.fuentes() if x['id'] == 'rt_news'],
         'marcar_fuente(desactivar=True) apaga a mano (chequeo de frescura de ingesta.tick)')
    _chk(al.cargar_fuentes(FUENTES) == n - 2,
         'recargar el catalogo NO resucita las dos fuentes apagadas (quedan %d de %d)' % (n - 2, n))

    # --- bitacora
    _chk(al.ultima_corrida('recolectar') is None, 'ultima_corrida sin corridas -> None')
    al.registrar('recolectar', ok=False, n_in=10, n_out=0, error='feed caido')
    al.registrar('recolectar', ok=True, n_in=120, n_out=37)
    r = al.ultima_corrida('recolectar')
    _chk(r['ok'] is True and r['n_out'] == 37 and r['t_fin'].tzinfo is not None,
         'registrar + ultima_corrida: %s' % {k: r[k] for k in ('ok', 'n_in', 'n_out')})
    _chk(al.ultima_corrida('recolectar', solo_ok=True)['ok'] is True, 'ultima_corrida(solo_ok=True)')

    # --- guardar_vector: el unico metodo del CONTRATO que el resto de la bateria no llegaba a llamar
    a5 = al.guardar_articulo(dict(base, url='https://bbc.com/5', url_hash='h5',
                                  title='Vector suelto, sin evento', detected_at=t0 - timedelta(hours=1)))
    _chk(al._uno('SELECT embedding FROM article WHERE id=:i', i=a5)['embedding'] is None,
         'un articulo recien guardado entra sin embedding')
    al.guardar_vector(a5, v1b)
    g = _vec_np(al._uno('SELECT embedding FROM article WHERE id=:i', i=a5)['embedding'])
    _chk(g is not None and g.shape[0] == d and float(_norm(g) @ _norm(v1b)) > 0.999,
         'guardar_vector escribe el vector y vuelve igual (coseno 1.0)')
    _chk(a5 not in [x[0] for x in al.vecinos(v1b, desde=t0 - timedelta(hours=72), limite=50)],
         'guardar_vector NO engancha a ningun evento: vecinos() sigue mirando solo los que tienen')

    # --- husos horarios. Este bloque es el que importa: la ventana de 72 h se filtra comparando
    # fechas, y en SQLite esas fechas son TEXTO. Si una entra con offset propio, el orden del texto
    # deja de ser el orden del tiempo y el agrupamiento pierde (o suma) articulos segun como haya
    # escrito la hora el que llamo. El mismo instante tiene que dar la misma respuesta siempre.
    tz_m4 = timezone(timedelta(hours=-4))
    tz_p5 = timezone(timedelta(hours=+5))
    aA = al.guardar_articulo(dict(base, url='https://bbc.com/6', url_hash='h6', title='A = 16:00Z',
                                  detected_at=datetime(2031, 1, 2, 12, 0, tzinfo=tz_m4),
                                  published_at=datetime(2031, 1, 2, 12, 0, tzinfo=tz_m4),
                                  title_simhash=(1 << 63) + 7))
    aB = al.guardar_articulo(dict(base, url='https://bbc.com/7', url_hash='h7', title='B = 15:00Z',
                                  detected_at=datetime(2031, 1, 2, 20, 0, tzinfo=tz_p5)))
    fa = [x for x in al.articulos(limite=50) if x['id'] == aA][0]
    _chk(fa['published_at'].utcoffset() == timedelta(0) and fa['published_at'].hour == 16,
         'una fecha que entra en -04:00 sale convertida a UTC (12:00-04:00 -> %s)'
         % fa['published_at'].strftime('%H:%MZ'))
    _chk(fa['title_simhash'] == (1 << 63) + 7,
         'title_simhash de 64 bits ida y vuelta sin signo: %s' % fa['title_simhash'])
    corte = datetime(2031, 1, 2, 15, 30, tzinfo=timezone.utc)
    dentro = [x['id'] for x in al.articulos(desde=corte, limite=50)]
    _chk(dentro == [aA], 'articulos(desde=) corta por INSTANTE, no por el reloj de pared: %s' % dentro)
    _chk([x['id'] for x in al.articulos(desde=corte.astimezone(tz_m4), limite=50)] == dentro,
         'el MISMO instante escrito en otro huso da el MISMO corte')
    al.crear_evento('Evento de 2031', aB, v2)
    _chk(al.vecinos(v2, desde=corte) == [] and
         al.vecinos(v2, desde=corte.astimezone(tz_p5)) == [],
         'vecinos() deja fuera de la ventana a B (15:00Z) mire el corte desde el huso que lo mire')

    # --- buscar_eventos por fecha (last_updated), que tampoco se estaba probando
    _chk([x['id'] for x in al.buscar_eventos(desde=t0 - timedelta(hours=1))] != [],
         'buscar_eventos(desde=) trae los eventos tocados recien')
    _chk(al.buscar_eventos(hasta=t0 - timedelta(days=1)) == [],
         'buscar_eventos(hasta=) de ayer no trae nada')


def autotest():
    print('== almacen.py --autotest ==')
    with open(ESQUEMA, encoding='utf-8') as fh:
        ddl_pg = _cols_ddl(fh.read())
    ddl_lite = _cols_ddl(DDL_SQLITE)
    _chk(set(ddl_pg) == set(ddl_lite),
         'esquema.sql y el espejo SQLite tienen las mismas tablas (%d): %s'
         % (len(ddl_pg), ' '.join(sorted(ddl_pg))))
    for t in sorted(set(ddl_pg) & set(ddl_lite)):
        _chk(ddl_pg[t] == ddl_lite[t], 'tabla %s: mismas columnas en los dos DDL%s' % (
            t, '' if ddl_pg[t] == ddl_lite[t] else ' (pg=%s lite=%s)' % (ddl_pg[t], ddl_lite[t])))

    prueba = os.path.join(BASE, '_radar_test.db')
    for suf in ('', '-wal', '-shm'):
        if os.path.exists(prueba + suf):
            os.remove(prueba + suf)
    al = conectar(prueba, dim=32)
    try:
        _bateria(al, 'SQLite %s (dim=%d)' % (os.path.basename(prueba), al.dim))
    finally:
        al.eng.dispose()
        for suf in ('', '-wal', '-shm'):
            if os.path.exists(prueba + suf):
                os.remove(prueba + suf)
        _chk(not os.path.exists(prueba), 'la base de prueba quedo borrada')

    dsn = os.environ.get('RADAR_DSN')
    if not dsn:
        print('\nSALTEA: sin RADAR_DSN no hay Postgres a mano. Sin probar aca: la extension pgvector, '
              'el indice HNSW, el operador <=>, los text[]/jsonb nativos y las dos CHECK del DDL '
              '(la misma invariante si se probo, validada en Python).')
    else:
        alp = conectar(dsn, dim=32)
        try:
            _bateria(alp, 'Postgres (RADAR_DSN)')
        finally:
            alp.eng.dispose()

    print('\n%s  (%d fallas)' % ('TODO OK' if not _FALLAS else 'HAY FALLAS', len(_FALLAS)))
    for f in _FALLAS:
        print('  - ' + f)
    return 0 if not _FALLAS else 1


if __name__ == '__main__':
    sys.exit(autotest() if '--autotest' in sys.argv else
             (print(__doc__) or 0))
