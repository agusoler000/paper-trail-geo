-- Esquema del Radar. Postgres 16 + pgvector. Es el DDL de RADAR.md seccion 7.
--
-- Cuatro cambios minimos respecto del texto de RADAR.md, todos por necesidad y ninguno de diseno:
--   1. IF NOT EXISTS en todo. init_esquema() se llama en cada arranque y tiene que ser idempotente.
--   2. La FK article.event_id se agrega con ALTER TABLE despues de crear event. En RADAR.md la tabla
--      article se declara ANTES que event, y una referencia hacia adelante no existe en Postgres.
--      Va con ON DELETE SET NULL: borrar un evento no puede borrar los articulos (statement,
--      narrative y score_history si van en CASCADE, porque son del evento y de nadie mas).
--   3. Los indices llevan nombre; hace falta para poder decir IF NOT EXISTS.
--   4. El indice parcial de video_score usa "estado IS DISTINCT FROM 'closed'" en vez de <>, para que
--      un evento con estado NULL tambien entre (con <> un NULL queda afuera del indice y la consulta
--      que lo use pierde filas).
--
-- Dimension del vector: 384 (MiniLM, RADAR.md seccion 4). OJO: radar/vectores.py del CONTRATO usa 512.
-- almacen.conectar(dsn, dim=...) reemplaza el 384 de este archivo por la dimension real antes de
-- ejecutarlo, asi que el DDL queda como lo escribio RADAR.md y el codigo se adapta.
--
-- Las dos CHECK del final de statement no son decorativas: son la regla editorial del sistema metida
-- en la base, donde ningun prompt la puede ablandar un martes. Un fact exige dos fuentes
-- independientes o un documento oficial; un claim exige el actor que lo dice.

CREATE EXTENSION IF NOT EXISTS vector;

-- Registro de fuentes. Se carga desde radar/fuentes.json.
CREATE TABLE IF NOT EXISTS source (
  id            text PRIMARY KEY,
  nombre        text NOT NULL,
  url           text NOT NULL,
  source_type   text NOT NULL,      -- western|russian|russian_ind|chinese|arab|israeli|iranian|
                                    -- ukrainian|osint|official|latam|apac|aggregator
  tier          smallint NOT NULL,  -- 1..3, pondera el score; NO es confianza
  pais          text, lang text,
  wire_propio   boolean DEFAULT true,  -- false = republica cables de otros
  primaria      boolean DEFAULT false, -- fuente primaria del actor
  activa        boolean DEFAULT true,
  ultimo_ok     timestamptz,           -- chequeo de frescura
  ultimo_error  text,
  fallos_seguidos smallint DEFAULT 0
);

CREATE TABLE IF NOT EXISTS article (
  id            bigserial PRIMARY KEY,
  source_id     text REFERENCES source(id),
  url           text NOT NULL,
  url_hash      text NOT NULL UNIQUE,     -- dedup exacto
  title_simhash bigint,                   -- dedup casi-exacto (mismo cable)
  wire_origin   text,                     -- 'reuters'|'ap'|'afp'|NULL(propio) -> ANTI DOBLE CONTEO
  title         text NOT NULL,
  summary       text,                     -- resumen NUESTRO, no el texto del medio (RADAR.md 12)
  published_at  timestamptz,
  detected_at   timestamptz DEFAULT now(),
  lang          text,
  embedding     vector(384),
  event_id      bigint,                   -- la FK se agrega abajo, cuando event ya existe
  raw           jsonb
);
CREATE INDEX IF NOT EXISTS article_embedding_hnsw ON article USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS article_detected_idx   ON article (detected_at DESC);
CREATE INDEX IF NOT EXISTS article_event_idx      ON article (event_id);

CREATE TABLE IF NOT EXISTS event (
  id              bigserial PRIMARY KEY,
  titulo          text NOT NULL,
  first_detected  timestamptz NOT NULL,
  last_updated    timestamptz NOT NULL,
  estado          text DEFAULT 'developing',  -- breaking|developing|watchlist|closed
  importancia     smallint,
  video_score     smallint,
  centroide       vector(384),
  paises          text[], actores text[], topics text[],
  requiere_agustin boolean DEFAULT false,
  motivo_bandera  text,
  -- desglose del score, para poder depurarlo
  s_fuentes_indep real, s_cross_bloc real, s_velocidad real,
  s_actores real, s_dominio real,
  riesgo_escalada text                       -- bajo|medio|alto (LLM)
);
CREATE INDEX IF NOT EXISTS event_importancia_idx ON event (importancia DESC, last_updated DESC);
CREATE INDEX IF NOT EXISTS event_video_idx       ON event (video_score DESC)
  WHERE estado IS DISTINCT FROM 'closed';

-- Cambio 2: la referencia hacia adelante de article, ahora que event existe.
ALTER TABLE article DROP CONSTRAINT IF EXISTS article_event_fk;
ALTER TABLE article ADD  CONSTRAINT article_event_fk
  FOREIGN KEY (event_id) REFERENCES event(id) ON DELETE SET NULL;

-- HECHO vs AFIRMACION vs DISPUTADO. El corazon del sistema.
CREATE TABLE IF NOT EXISTS statement (
  id            bigserial PRIMARY KEY,
  event_id      bigint REFERENCES event(id) ON DELETE CASCADE,
  tipo          text NOT NULL,     -- fact|claim|disputed
  texto         text NOT NULL,
  actor         text,              -- OBLIGATORIO si tipo='claim'
  evidence      text,              -- official_doc|satellite|own_reporting|osint|none
  n_indep       smallint,          -- wire_origin distintos que lo sostienen
  article_ids   bigint[],
  disputa_de    bigint REFERENCES statement(id),
  creado        timestamptz DEFAULT now(),
  CONSTRAINT claim_necesita_actor CHECK (tipo <> 'claim' OR actor IS NOT NULL),
  CONSTRAINT fact_necesita_dos    CHECK (tipo <> 'fact'  OR n_indep >= 2 OR evidence = 'official_doc')
);

CREATE TABLE IF NOT EXISTS narrative (
  id         bigserial PRIMARY KEY,
  event_id   bigint REFERENCES event(id) ON DELETE CASCADE,
  bloque     text NOT NULL,   -- western|russian|chinese|arab|israeli|latam|apac
  resumen    text NOT NULL,
  enfasis    text,            -- que destaca este bloque
  omite      text,            -- que NO menciona (a menudo lo mas revelador)
  article_ids bigint[]
);

-- Historial: asi se detecta DEVELOPING (la importancia sube) vs cerrado.
CREATE TABLE IF NOT EXISTS score_history (
  event_id bigint REFERENCES event(id) ON DELETE CASCADE,
  t timestamptz DEFAULT now(),
  importancia smallint, n_articulos smallint, n_bloques smallint
);
CREATE INDEX IF NOT EXISTS score_history_idx ON score_history (event_id, t DESC);

CREATE TABLE IF NOT EXISTS alert_rule (
  id bigserial PRIMARY KEY, nombre text,
  filtro jsonb,                -- paises CN/TW y min_importancia 75, por ejemplo
  canal text DEFAULT 'telegram',
  activa boolean DEFAULT true, ultimo_disparo timestamptz
);

CREATE TABLE IF NOT EXISTS run_log (
  id bigserial PRIMARY KEY, etapa text, t_inicio timestamptz, t_fin timestamptz,
  ok boolean, n_in int, n_out int, error text
);
CREATE INDEX IF NOT EXISTS run_log_idx ON run_log (etapa, id DESC);
