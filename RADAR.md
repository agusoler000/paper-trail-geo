# RADAR — arquitectura, y el sistema construido sobre ella

> Escrito 2026-09-11 a pedido de Agustín como propuesta para revisar. **Construido el mismo día**, a
> pedido suyo: el código vive en `radar/` y `videos/DAILY/`, con autotest por módulo y una corrida real
> contra 3.850 artículos de las 79 fuentes. Lo que cambió al construirlo está marcado §4bis y §11bis. Todo lo que dice "medido" se midió de verdad contra los endpoints reales el 2026-09-11;
> el detalle por fuente está en `radar/fuentes.json`.
> Complementa `COSTOS.md` (economía), `FORMATOS.md` (Dispatch/Brief), `MONETIZACION.md` (riesgos),
> `IDEOLOGIA.md` (postura) y `ANIMACION.md` (motor de render).

---

## 0. El diagnóstico en una línea

> **ACTUALIZADO 2026-09-11, después de la propuesta de formato de Agustín (§10bis).** El diagnóstico de
> abajo era correcto para el formato de episodio bespoke. **El formato de dos paneles que propuso Agustín
> — presentador fijo a la izquierda, animación de la noticia a la derecha — disuelve el problema**: la
> coreografía deja de escribirse y pasa a elegirse de un catálogo de fichas. Lo dejo escrito porque explica
> por qué esa decisión suya vale tanto.

**El Radar es la mitad fácil, y es barata, fiable y útil desde la primera semana. El video diario de 20
minutos no se traba en la recolección ni en los dólares: se traba en `escena.py`.**

`COSTOS.md` ya lo había escrito, antes de esta conversación, y sigue siendo verdad:

> "El render sí escala (40 min × 30 = 20 h/mes, corre solo de noche). **Lo que no escala es la coreografía
> a mano.** El pendiente #4 de la skill — `escena.py` — deja de ser una mejora y pasa a ser el requisito
> para que la cadencia diaria exista."

Hoy un episodio de 12 min pide un archivo de coreografía de ~600 líneas escrito a mano. Uno de 20 min pide
~1.000. Ningún radar arregla eso. Por eso la propuesta de abajo trata el Radar y el video diario como
**dos proyectos con dependencias distintas**, y el orden importa: el Radar sirve solo (te dice qué hacer);
el video diario no sirve sin el Radar ni sin `escena.py`.

Esto no es una objeción a que hagas el video diario. Es dónde está el trabajo real, para que lo decidas vos.

---

## 1. Análisis de tu arquitectura

Tu propuesta:

```
RSS / APIs / GDELT / Official → n8n → Normalization → Dedup/Clustering
    → PostgreSQL + pgvector → Event/Narrative Engine → MCP Server → Claude / Dashboard
```

### Lo que está bien y no tocaría

- **Postgres + pgvector, una sola base.** Correcto. No hace falta Qdrant ni Pinecone: pgvector con índice
  HNSW hace el vecino más cercano sobre 200k artículos sin despeinarse, y te ahorra mantener dos sistemas
  que se desincronizan.
- **MCP como interfaz.** Correcto, y es la decisión que más rinde: convierte el sistema en algo que se
  consulta hablando, en vez de una web que hay que mirar.
- **Clasificar fuentes por perspectiva y no por veracidad.** Esto es lo mejor de tu documento y es lo que
  casi todos hacen mal. La mayoría de los agregadores "anti-sesgo" terminan siendo un ranking de confianza
  disfrazado. Vos lo planteaste bien: la etiqueta sirve para **detectar narrativas**, no para decidir quién
  tiene razón.
- **Separar HECHO de AFIRMACIÓN.** Es la pieza de más valor de todo el sistema y la que te distingue de un
  agregador. Le dedico la §5.

### Los cuatro cambios que sí propongo

**(a) n8n no debe hacer el pipeline. Debe dispararlo.**
Es el cambio más importante. Dos razones, una de diseño y una técnica dura:

- *Técnica:* n8n pasa **todos los ítems en memoria** entre nodos. 3.000 artículos con texto atravesando 15
  nodos revienta la RAM de un VPS chico. No es una opinión: es cómo funciona el motor de ejecución.
- *De diseño:* una lógica de clustering y scoring dentro de nodos Code de n8n no se versiona en git de forma
  útil, no se testea, y no se depura. El día que el video no salga a las 12:00 vas a querer un stack trace,
  no un grafo de 40 cajas.

n8n se queda con lo que hace bien: **cron, reintentos, Telegram, y la vista de "¿corrió o no corrió?"**.
La lógica va en un servicio Python que n8n llama por HTTP.

**(b) Dos etapas, no una: filtro barato primero, LLM después.**
No podés pasar un LLM por 3.000 artículos diarios y que sea gratis. El orden correcto es:
dedup por hash → embeddings → clustering → **y recién ahí** el LLM, sobre ~60-100 representantes de cluster.
Eso es lo que hace que el coste de inteligencia sea ~0 en vez de ~$200/mes.

**(c) El score de importancia no lo calcula un LLM.**
Pedirle a un modelo "dame un 0-100" da números que no son reproducibles entre corridas y que derivan con el
tiempo. El score se calcula con **aritmética sobre datos** (cuántas fuentes independientes, qué bloques lo
cubren, velocidad de propagación, peso de los actores) y el LLM aporta sólo las **categorías** que no se
pueden contar (riesgo de escalada: bajo/medio/alto). Detalle en §6.

**(d) El dashboard no es una app.**
Un React con filtros y páginas de evento son semanas. Vos ya pediste el MCP, que *es* la interfaz. El
dashboard arranca como **una página HTML servida por el mismo FastAPI**, leyendo de Postgres. 200 líneas.
Si en tres meses la usás todos los días, ahí se invierte en hacerla linda.

---

## 2. Fuentes: qué encontré midiendo, no recordando

Probé 88 endpoints en la primera ronda y 87 candidatos alternativos en la segunda. **56 y 35 vivos.**
El registro completo, listo para que lo lea el código, está en `radar/fuentes.json`.

### Las cuatro noticias que cambian el diseño

**1. Reuters y AP no tienen RSS. Punto.**
`reuters.com/arc/outboundfeeds/rss` → 404. `reuters.com/world/rss` → 401. `apnews.com/*.rss` → 403 a
cualquier bot. Esto confirma lo que ya estaba en `fuentes/FUENTES.md` sobre el MCP de Reuters (sólo para
clientes de agencia). Las dos agencias que más pesan en tu lista son las dos que no se pueden leer directo.

**2. El puente es Google News RSS, y funciona para todas las difíciles.**
Medido, las cinco devuelven contenido fresco hoy:

| Fuente | Ruta propia | Vía Google News |
|---|---|---|
| Reuters | 404 / 401 | **100 ítems** |
| AP | 403 | **100 ítems** |
| NATO | 404 en todas las rutas | **76 ítems** |
| ISW | 403 / 404 | **47 ítems** |
| Xinhua | 404 | **100 ítems** |

La consulta es `news.google.com/rss/search?q=when:1d+site:reuters.com&hl=en-US&gl=US&ceid=US:en`.
Da **titular, link y fecha — no el texto**. Que no dé el texto no es un problema: es exactamente lo que
querés guardar por el lado legal (§10). Para el resumen usás el titular y, si hace falta, el artículo se
lee en el momento de escribir el guion.

**3. Varios feeds responden 200 y están muertos por dentro.**
Trampa real: `feeds.a.dj.com` (WSJ) devuelve 200 con 20 ítems y el más nuevo es de **enero de 2025**.
`csis.org/rss.xml` devuelve 200 con el último ítem de **2016**. El del Parlamento Europeo, de 2023.
**Un chequeo de HTTP 200 no alcanza**: el ingestor tiene que validar frescura (¿el ítem más nuevo es de
menos de 72 h?) y apagar la fuente sola, avisando por Telegram. Esto va en el MVP, no después.

**4. Los think tanks occidentales bloquean bots casi todos.**
CSIS, CFR, RUSI, Chatham House, IISS, IMF: 403 o 404. Los que sí andan: **Atlantic Council (100),
Lowy Interpreter (50, y te cubre Australia), ECFR (21), The Diplomat (96), Stimson (12), Bellingcat (9),
Oryx (8)**.

### Lo que sí funciona y no estaba en tu lista

- **Wikipedia `Portal:Current_events/2026_September_11`** vía Action API — **172 ms**, sin key. Es una lista
  curada por humanos de los hechos del día, con referencias. No la uses como fuente: usala como **red de
  seguridad**. Si un hecho está ahí y tu radar no lo tiene, te falta un feed. Es el mejor test de cobertura
  gratis que existe.
- **Federal Register API** — 320 ms, sin key, texto completo, dominio público. Órdenes ejecutivas de EEUU
  en fuente primaria dura.
- **Guardian Open Platform** — key gratis, y es **la única fuente grande que te da el TEXTO COMPLETO de forma
  legal y sin pagar**. Vale la pena pedirla.
- **Buenos Aires Times** (`batimes.com.ar/feed`, 100 ítems) — Argentina **en inglés**, te ahorra traducir
  para el bloque argentino.
- **MercoPress** — Cono Sur en inglés, cubre Atlántico Sur y Malvinas (o sea, continuidad con el ep. 04).
- **Meduza y The Moscow Times** — ruso independiente en el exilio. Los agregué porque tu lista rusa era
  TASS + RT + oficial, es decir, **tres fuentes con la misma línea**. Sin un ruso independiente, el sistema
  no puede distinguir "Rusia dice X" de "la prensa rusa coincide en X", que es una diferencia enorme para
  el análisis de narrativas.

### Argentina: las rutas que circulan están mal

`infobae.com/feeds/rss/` → 404. La que anda es `infobae.com/arc/outboundfeeds/rss/?outputType=xml` (75).
`bcra.gob.ar/Noticias/RSS.xml` → 404, y no encontré reemplazo. Casa Rosada sí anda, por una ruta rara de
Joomla: `casarosada.gob.ar/informacion/discursos?format=feed&type=rss` (40).

### GDELT: gratis, potente y lento

Medido: **11 a 18 segundos por consulta**, y **HTTP 429 si hacés más de una cada 5 segundos**. El mensaje de
error lo dice literalmente. Esto es un dato de arquitectura, no un detalle: GDELT **no es un poller**, es una
**cola secuencial**. Con 20 consultas por ciclo son ~7 minutos de reloj. Entra perfecto en un ciclo de 30-60
min; no entra en uno de 5.

Lo que GDELT te da y nadie más: **cobertura en 65 idiomas**. Es cómo detectás que un tema explotó en la
prensa turca o india antes de que llegue a la occidental.

---

## 3. MCPs que ya existen (no escribir lo que ya está escrito)

Para GDELT hay tres servidores comunitarios; **no vale la pena escribir uno**:
- [`cyanheads/gdelt-mcp-server`](https://github.com/cyanheads/gdelt-mcp-server) — el más completo (DOC API + TV API, STDIO y HTTP).
- [`MissionSquad/mcp-gdelt`](https://github.com/MissionSquad/mcp-gdelt) y [`anysiteio/GDELT-mcp`](https://github.com/anysiteio/GDELT-mcp) — más simples, sin auth.
- [`marc-shade/world-intel-mcp`](https://github.com/marc-shade/world-intel-mcp) — 120 herramientas, GDELT + 119 RSS + ACLED. Demasiado para vos, pero su **lista de feeds vale como referencia cruzada**.
- [`soxoj/awesome-osint-mcp-servers`](https://github.com/soxoj/awesome-osint-mcp-servers) — índice de MCPs OSINT.

**Lo que sí hay que escribir es el MCP del Radar**, porque lo valioso no es consultar GDELT: es consultar
*tus* eventos, *tus* narrativas y *tus* scores. Ese no existe.

Reuters MCP: confirmado que sigue siendo sólo para clientes de agencia (`fuentes/FUENTES.md` §2).

---

## 4. Arquitectura definitiva

```
  ┌─ FUENTES ──────────────────────────────────────────────┐
  │  78 feeds RSS   ·   Google News (puente)   ·   GDELT    │
  │  APIs sin key: Wikipedia · Federal Register · ECB       │
  └────────────────────────┬───────────────────────────────┘
                           │  HTTP, condicional (ETag / If-Modified-Since)
  ┌────────────────────────▼───────────────────────────────┐
  │  radar-ingest  (Python, corre cada 30 min)              │
  │  · fetch con backoff y respeto de rate limits           │
  │  · normaliza → Article                                  │
  │  · dedup por url_hash + simhash de título               │
  │  · CHEQUEO DE FRESCURA → apaga feeds zombie             │
  └────────────────────────┬───────────────────────────────┘
                           ▼
  ┌────────────────────────────────────────────────────────┐
  │  radar-cluster  (mismo proceso, etapa 2)                │
  │  · embeddings: paraphrase-multilingual-MiniLM vía       │
  │    fastembed (ONNX, SIN torch, 480 textos/s en CPU)     │
  │  · clustering incremental contra pgvector, ventana 72 h │
  │  · el margen dudoso lo resuelve un modelo Flash         │
  └────────────────────────┬───────────────────────────────┘
                           ▼
  ┌────────────────────────────────────────────────────────┐
  │  radar-analyze  (etapa 3 — la ÚNICA que usa LLM)        │
  │  · sólo sobre clusters nuevos o que crecieron           │
  │  · extrae: actores, países, statements (fact/claim)     │
  │  · narrativas por bloque                                │
  │  · categorías para el score (escalada, dominio)         │
  │  ~60-100 llamadas/día, no 3.000                         │
  └────────────────────────┬───────────────────────────────┘
                           ▼
  ┌────────────────────────────────────────────────────────┐
  │  PostgreSQL 16 + pgvector  (un solo almacén)            │
  └──────┬──────────────────┬──────────────────┬───────────┘
         │                  │                  │
   ┌─────▼─────┐   ┌────────▼────────┐   ┌─────▼──────────┐
   │ MCP server│   │ FastAPI + HTML  │   │ n8n            │
   │ (Claude)  │   │ (dashboard)     │   │ cron + Telegram│
   └───────────┘   └─────────────────┘   └─────┬──────────┘
                                                │ 04:00 UTC
                                    ┌───────────▼──────────┐
                                    │  PIPELINE DEL VIDEO  │
                                    │  (§8)                │
                                    └──────────────────────┘
```

**Todo en un VPS, en Docker Compose.** Cinco contenedores: `postgres`, `radar` (FastAPI + worker),
`mcp`, `n8n`, `caddy` (TLS). El render del video corre fuera de Docker, directo en el host, para que pueda
tomar todos los núcleos.

### Dimensionado del VPS — esto importa

El motor (`produccion/motor.py`) es **PIL + multiprocessing + ffmpeg, CPU puro**, 1920×1080 a 24 fps, con
`workers = cpu_count - 2`. Portable a Linux sin cambios. Medido en tu laptop: **12 min de video = 40 min de
render** ≈ 7,2 cuadros/s.

### El VPS real (medido 2026-09-11)

```
Contabo · vmi3215844 · Lauterbourg, FRANCIA (UE)
6 vCPU AMD EPYC · 11 GB RAM (6,1 en uso, 5,6 libres) · SIN SWAP
193 GB disco, 143 libres · Ubuntu 24.04 · Python 3.12.3 · ffmpeg 6.1.1
Ya corriendo: Coolify, Supabase completo (~12 contenedores), n8n,
Evolution API, umami, traefik, 2 postgres, redis
```

**Veredicto: entra, pero con tres condiciones.**

| | dato | consecuencia |
|---|---|---|
| **6 vCPU** | `workers = 6-2 = 4` | 20 min de video ≈ **3-4,5 h de render** (hay que medirlo, no estimarlo). Entra en la ventana 05:00→12:00 UTC, pero deja el server lento 4 horas. |
| **5,6 GB libres y SIN swap** | 4 workers de PIL a 1080p | **Este es el riesgo real.** Un pico de memoria sin swap no mata el render: mata contenedores. Te puede tirar Supabase, n8n o Evolution API. |
| **Francia = UE** | sanciones a medios rusos | RT y Sputnik dejan de ser una duda teórica (§12.1). Hay que verificar la lista vigente antes de encender esos feeds. |

**Las tres condiciones, concretas:**
1. **Crear swap** (8 GB) antes del primer render. Una línea de `fallocate`. Sin esto no se renderiza nada.
2. **Bajar a 3 workers** y correr con `nice -n 19` + `cpulimit`, para que el render nunca compita con
   Supabase y n8n. Cuesta ~25 % más de reloj y elimina el riesgo de tumbar servicios de producción.
3. **Reusar el Postgres que ya está.** `supabase/postgres:15.8` ya trae pgvector. No hace falta un
   contenedor nuevo: una base `radar` dentro del Postgres existente y listo.

Si en algún momento el render molesta demasiado, la salida no es achicar el video: es un segundo VPS chico
sólo para renderizar. Un Hetzner CAX31 (8 vCPU ARM, 16 GB) son €12,5/mes y deja este server tranquilo.

---

## 4bis. Agrupamiento: tres intentos y lo que midió cada uno

> Construido y medido el 2026-09-11 contra 3.850 artículos reales de las 79 fuentes. Detalle técnico
> en `radar/semantica.py`; lo que sigue es por qué el diseño terminó siendo así.

| Método | Eventos | Artículos agrupados | Qué pasó |
|---|---|---|---|
| TF-IDF de caracteres, umbral 0,78 | 3.748 | **103** | no agrupaba nada |
| embeddings + ancla sumando al puntaje | 1.015 | 2.819 | fundía a Messi con "tech wars" |
| **embeddings, el ancla sólo pregunta** | **2.217** | **2.100** | clusters coherentes |

**Por qué falló el primero.** El atajo era evitar bajar un modelo. El número que lo mató:

```
"Washington introduces new sanctions against Moscow"
"Вашингтон вводит новые санкции против Москвы"     (el MISMO hecho, en ruso)
    TF-IDF de caracteres : 0,002        embeddings : 0,940
```

Y peor: dos hechos **distintos** daban 0,244 mientras el **mismo** hecho contado de dos formas daba
0,136. No hay umbral que separe eso, porque TF-IDF compara palabras y esto pide comparar significado.

**El caso difícil, que ningún umbral arregla.** *"Russia says air defences downed 20 drones over
Belgorod"* contra *"Fire reported at Belgorod oil refinery"*: es el mismo incidente contado por los
dos bandos y **por eso** dicen cosas opuestas — similitud 0,065. No es un defecto del modelo: es la
naturaleza del hecho, y es exactamente el material de la ficha `versus`.

**La solución, en tres decisiones.**

1. **Ancla de entidad rara.** Los dos comparten "Belgorod", que aparece en 0 de 3.850 titulares del
   día. Compartir "Russia" (121 de 3.850) no dice nada. Por eso el ancla se pesa por IDF de entidad
   y no por Jaccard, que diluye justamente lo raro.
2. **Precisión antes que cobertura.** Partir un acontecimiento en dos es redundante y se ve en el
   orden del día; fundir dos en uno es un error editorial que sale al aire.
3. **El ancla pregunta, nunca afirma.** Ésta costó una corrida entera: con el ancla sumando directo
   al puntaje, un cluster llamado *"The tech wars are about to enter a fiery new phase"* se había
   tragado un puente en Nueva Zelanda y el pase de Messi, porque compartir una entidad medio rara
   sumaba 0,40 y con eso cruzaba el umbral. Ahora: **semántica ≥ 0,60 → mismo hecho. Entre 0,35 y
   0,60, o con ancla fuerte desde 0,18 → se le pregunta a un modelo Flash** (~50 pares por día,
   centavos). Debajo, evento nuevo.

**Dependencia nueva y por qué vale:** `fastembed` (ONNX, **sin torch**, ~100 MB). 480 textos/s en
CPU: los 3.900 titulares del día se vectorizan en **8 segundos**.

## 5. La capa de verificación (§4 de tu pedido) — la pieza que hay que hacer bien

Tu instinto es correcto y es lo más valioso del sistema. El problema de implementación tiene un nombre:

> **Reuters, BBC, Yahoo y otros treinta medios publicando el mismo cable de Reuters NO son treinta fuentes
> independientes. Son una.**

Si el contador de "fuentes independientes" no sabe eso, la regla "hecho = 2+ fuentes independientes" se
rompe en el primer día y el sistema empieza a etiquetar como HECHO cosas que dijo una sola redacción.
Por eso `radar/fuentes.json` lleva el campo `wire_propio`, y el esquema lleva `wire_origin`.

Las tres etiquetas, con su regla:

| Etiqueta | Regla | Ejemplo |
|---|---|---|
| `fact` | ≥2 fuentes con **`wire_origin` distinto** lo reportan como reporte propio (sin verbo de atribución), **o** 1 fuente primaria oficial del actor que lo hizo | "La Comisión Europea publicó el paquete 19 de sanciones" (está en el feed de la Comisión) |
| `claim` | Hay verbo de atribución ("claims", "says", "announced", "according to") → se guarda **con el actor que lo dice** | `claim(actor=RU_MoD, "derribó 20 drones ucranianos")` — nunca `fact("Rusia derribó 20 drones")` |
| `disputed` | Dos `claim` sobre la misma proposición con valores incompatibles | Ucrania dice X · Rusia dice Y · evidencia independiente insuficiente |

Regla dura que propongo y que decidís vos: **`fact` con una sola fuente independiente no existe.** Si sólo
lo tiene una, es `claim` con esa redacción como actor. Es más conservador que la mayoría de los sistemas, y
es lo que hace que puedas usar la salida para escribir un guion sin volver a verificar todo a mano.

Y el campo que va con cada statement: `evidence` — qué lo respalda (documento oficial, imagen satelital,
reporte propio, OSINT verificado, nada).

---

## 6. Los dos scores (§6 y §7 de tu pedido)

### Importancia — aritmética, no adivinación

```
IMPORTANCIA = 100 × ( 0.22·fuentes_indep + 0.18·cross_bloc + 0.15·tier
                    + 0.15·velocidad     + 0.15·peso_actores
                    + 0.10·dominio       + 0.05·fuente_primaria )
```

- `fuentes_indep` — cuántos `wire_origin` distintos, log-escalado, tope 8. **Calculado.**
- `cross_bloc` — **de cuántos bloques distintos (western / russian / chinese / arab / israeli / apac /
  latam) hay cobertura, sobre 7. Calculado.** Este es el que casi nadie usa y es el mejor de todos: un
  hecho que cubren Reuters *y* TASS *y* Xinhua a la vez es estructuralmente más importante que uno que
  cubren veinte medios occidentales. Es una señal de relevancia que no depende de la opinión de nadie.
- `velocidad` — artículos en las últimas 3 h ÷ las 3 h previas, con tope. **Calculado.**
- `peso_actores` — tabla fija (US/CN/RU = 1,0 · DE/FR/GB/JP/IN = 0,8 · ...). **Calculado.**
- `dominio` y riesgo de escalada — **lo único que aporta el LLM**, y como categoría, no como número.

Ventaja: es reproducible, lo podés depurar, lo podés ajustar mirando qué salió mal, y es gratis.

Corte: 🔴 80-100 · 🟠 60-79 · 🟡 40-59 · ⚪ <40, como pediste.

### Video Opportunity — con dos señales que sólo vos podés tener

Además de lo obvio (conflicto, sorpresa, explicabilidad, consecuencias), dos que salen de **tu propio repo**
y que ningún sistema genérico puede calcular:

- **`mapa_disponible`** — ¿la geografía del evento ya tiene hoja en `produccion/mapa_*.py`? Si el hecho pasa
  en una región que ya tenés dibujada, producirlo cuesta mucho menos. Es una señal de coste real.
- **`assets_disponibles`** — cuántos hits da `indice_assets.py buscar <actores>`. Los 49 créditos de assets
  ya pagados valen más en un evento que los reusa.

Y una señal externa: **competencia**, vía YouTube Data API (gratis, 10.000 unidades/día) — cuántos videos de
canales grandes salieron sobre el tema en 48 h. La relación no es lineal: competencia **cero** suele
significar que no hay demanda; competencia **alta** significa que llegás tarde. El puntaje premia la franja
del medio.

Salida, como pediste: `VIDEO OPPORTUNITY: 91/100` + ángulos posibles + títulos posibles + la pregunta
central. Los títulos salen con la fórmula de `CANAL.md` y el criterio de `feedback-titulos-sensacionalistas`.

**Una marca que va aparte del score:** si el evento toca los temas donde `IDEOLOGIA.md` dice *preguntar
antes* (cultura, aborto, género) o donde `MONETIZACION.md` marca zona sensible (atentado o masacre de los
últimos 7 días), el evento sale con bandera `requiere_agustin`. No baja el score. Bloquea la automatización.

---

## 7. Esquema de base de datos

```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- Registro de fuentes. Se carga desde radar/fuentes.json.
CREATE TABLE source (
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

CREATE TABLE article (
  id            bigserial PRIMARY KEY,
  source_id     text REFERENCES source(id),
  url           text NOT NULL,
  url_hash      text NOT NULL UNIQUE,     -- dedup exacto
  title_simhash bigint,                   -- dedup casi-exacto (mismo cable)
  wire_origin   text,                     -- 'reuters'|'ap'|'afp'|NULL(propio) → ANTI DOBLE CONTEO
  title         text NOT NULL,
  summary       text,                     -- resumen NUESTRO, no el texto del medio (§10)
  published_at  timestamptz,
  detected_at   timestamptz DEFAULT now(),
  lang          text,
  embedding     vector(384),
  event_id      bigint REFERENCES event(id),
  raw           jsonb
);
CREATE INDEX ON article USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON article (detected_at DESC);
CREATE INDEX ON article (event_id);

CREATE TABLE event (
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
CREATE INDEX ON event (importancia DESC, last_updated DESC);
CREATE INDEX ON event (video_score DESC) WHERE estado <> 'closed';

-- HECHO vs AFIRMACIÓN vs DISPUTADO. El corazón del sistema.
CREATE TABLE statement (
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

CREATE TABLE narrative (
  id         bigserial PRIMARY KEY,
  event_id   bigint REFERENCES event(id) ON DELETE CASCADE,
  bloque     text NOT NULL,   -- western|russian|chinese|arab|israeli|latam|apac
  resumen    text NOT NULL,
  enfasis    text,            -- qué destaca este bloque
  omite      text,            -- qué NO menciona (a menudo lo más revelador)
  article_ids bigint[]
);

-- Historial: así se detecta DEVELOPING (la importancia sube) vs cerrado.
CREATE TABLE score_history (
  event_id bigint REFERENCES event(id) ON DELETE CASCADE,
  t timestamptz DEFAULT now(),
  importancia smallint, n_articulos smallint, n_bloques smallint
);

CREATE TABLE alert_rule (
  id bigserial PRIMARY KEY, nombre text,
  filtro jsonb,                -- {paises:[CN,TW], min_importancia:75}
  canal text DEFAULT 'telegram',
  activa boolean DEFAULT true, ultimo_disparo timestamptz
);

CREATE TABLE run_log (
  id bigserial PRIMARY KEY, etapa text, t_inicio timestamptz, t_fin timestamptz,
  ok boolean, n_in int, n_out int, error text
);
```

Las dos `CHECK` no son decorativas: **hacen que la base rechace un `fact` con una sola fuente**. La regla
editorial queda escrita en el esquema, no en un prompt que el modelo puede ignorar un martes.

---

## 8. El MCP

Tu lista tiene 15 herramientas. Propongo **8**, porque menos herramientas con buenos parámetros hacen que
el modelo elija mejor que muchas herramientas estrechas (con 15, Claude duda entre `get_events_by_country`
y `search_events` y a veces llama a la peor).

| Herramienta | Reemplaza a | Parámetros |
|---|---|---|
| `search_events` | get_breaking_events, get_events_by_country, get_events_by_topic, get_video_opportunities | `pais, region, actor, topic, desde, hasta, min_importancia, min_video_score, estado, limit` |
| `get_event` | get_event | `event_id` → ficha completa: timeline, facts, claims, narrativas, fuentes |
| `search_news` | search_news, get_latest_news | `q, source_type, lang, desde, limit` (artículos sueltos, sin agrupar) |
| `compare_narratives` | compare_narratives | `event_id` → tabla por bloque con énfasis **y omisiones** |
| `get_evidence` | get_confirmed_facts, get_disputed_claims | `event_id, tipo=fact\|claim\|disputed` |
| `get_sources` | get_sources | `source_type` → estado de salud de cada feed |
| `brief_del_dia` | — | `fecha, formato=guion\|lista` → el insumo del video diario |
| `marcar` | — | `event_id, estado` → escribir: descartar, mandar a watchlist, aprobar para video |

`marcar` es la que falta en tu lista y la que hace que el sistema aprenda de vos: si descartás eventos, eso
es señal de entrenamiento para el `video_score`.

Todas devuelven **siempre las URLs originales**, como pediste.

---

## 9. El flujo de n8n

**Lo que hace n8n (5 workflows chicos, no uno grande):**

1. **`radar-tick`** — cron cada 30 min → `POST /ingest/tick` → si responde error, Telegram.
2. **`radar-gdelt`** — cron cada 60 min → `POST /ingest/gdelt` (el servicio hace la cola de 5 s adentro).
3. **`radar-alertas`** — webhook: el servicio llama a n8n cuando un evento cruza un umbral → Telegram con
   título, score, 3 links.
4. **`brief-diario`** — cron 04:15 UTC → `GET /brief` → Telegram con el orden del día y las banderas rojas.
5. **`video-diario`** — cron 04:30 UTC → dispara el pipeline del video (§10) y reporta cada etapa.

**Lo que NO hace n8n:** parsear, embeber, clusterizar, puntuar, llamar al LLM. Por §1(a).

---

## 10. El video diario

### Horario: publicar a las 12:00 UTC

Es la hora que junta más público en inglés: **08:00 Nueva York** (el commute) + **14:00 Berlín / 13:00
Londres** (la tarde europea) + 09:00 Buenos Aires. Australia y NZ quedan en la noche, pero son la porción
chica de los cuatro bloques que pediste.

### La cadena, hacia atrás desde las 12:00 UTC

```
01:00 UTC  el Radar sigue corriendo (ciclo de 30 min, como siempre)
04:00      CIERRE DE VENTANA. Último ingest. Ranking de eventos.
04:15      Selección: ~25-30 eventos repartidos por bloque
04:30      Guion (Claude en el VPS) — ~3.000 palabras
04:35      TELEGRAM: orden del día + banderas rojas + los 6 pasajes más riesgosos
04:40      Voz (ElevenLabs George) — ~3 min de proceso
04:45      Coreografía generada por escena.py  ←── LA PIEZA QUE NO EXISTE
05:00      Render arranca
05:00-07:15  render (2,2 h en 8 vCPU · 1,1 h en 16)
07:30      Mezcla, miniatura, subida como privado + programado 12:00
11:00      Último momento para que Agustín conteste si hubo bandera roja
12:00      PUBLICA
```

### La compuerta humana, invertida

Una compuerta que te obligue a aprobar todos los días a las 04:35 UTC (01:35 de Argentina) no la vas a
sostener una semana. Propongo invertirla:

- **Sin banderas rojas → publica solo.** No hace falta que hagas nada.
- **Con bandera roja → NO publica hasta que contestes.** Tenés desde que te despertás hasta las 11:00 UTC.

Bandera roja = la versión automática de reglas que ya escribiste vos: atentado o masacre de los últimos
7 días (`MONETIZACION.md`), tema donde `IDEOLOGIA.md` dice preguntar, un `fact` que se quedó con una sola
fuente, o una persona privada nombrada.

Así la automatización es total los días normales, y el humano aparece exactamente en los días en que hace
falta. Es lo único que hace sostenible una cadencia diaria para una persona sola.

### 10bis. El formato de dos paneles — la decisión que destraba todo

> Propuesta de Agustín, 2026-09-11: *"podría ser simplemente un mismo personaje con un mic del lado
> izquierdo contando la noticia, y del lado derecho que salga una animación MUY BIEN HECHA de lo que pasa."*

**Esto resuelve el cuello de botella de §0, y conviene entender por qué.**

Las 1.400 líneas de coreografía por episodio existen porque hoy **cada episodio es una composición única a
pantalla completa**: otro encuadre, otros movimientos de cámara, otra puesta en escena en cada beat. Eso es
lo que no se puede generar y hay que escribir a mano.

Un formato fijo de dos paneles rompe eso en dos problemas separados, y los dos son fáciles:

**Panel izquierdo — el presentador.** Un solo rig, construido una vez, reusado siempre. Lip-sync con
Rhubarb (ya está en el stack, `ANIMACION.md`), respiración/idle, y cuatro o cinco gestos. **Trabajo por
episodio: cero.** Y trae un regalo de rendimiento: como el cuerpo no cambia, el panel se **compone** a
partir de ~9 formas de boca sobre poses fijas en vez de **dibujarse** cuadro por cuadro. Puede bajar el
coste de render a la mitad, que es justo lo que este VPS necesita.

**Panel derecho — la ficha.** Cada noticia llena el panel con **una ficha de un catálogo cerrado**. Ahí está
la clave: no es un motor de animación general, es un renderizador de ~8 tipos de ficha. Y cada tipo mapea
exactamente contra un campo que el Radar **ya produce**:

| Ficha | Qué muestra | De dónde sale del Radar |
|---|---|---|
| `mapa` | hoja + puntos + flechas | `event.paises`, `event.actores` — y ya existe (`mapa_*.py`, regla 24) |
| `versus` | dos actores, sus versiones enfrentadas | `narrative` + `statement(tipo=disputed)` ← **la ficha estrella** |
| `titular` | recorte de prensa con el medio y la fecha | `article` — y es la estética de Paper Trail literalmente |
| `dato` | un número grande con su etiqueta | `statement(tipo=fact)` con cifra |
| `serie` | una curva en el tiempo | ECB / EIA / Federal Register |
| `cronologia` | qué pasó a qué hora | el timeline del evento |
| `calendario` | fechas que vienen | bloque WHAT TO WATCH |
| `plano` | una imagen generada, para los momentos hero | fal.ai, 1-2 por episodio |

Con esto, **el guion deja de producir coreografía y produce una lista de fichas**: `{"t": 142.5, "ficha":
"versus", "izq": {...}, "der": {...}}`. Eso un LLM lo emite perfecto, es validable contra un esquema, y
`escena.py` pasa de ser "un motor de animación genérico" (difícil, meses) a "ocho renderizadores de ficha"
(acotado, semanas, y cada uno se prueba solo).

**El otro beneficio:** la animación sólo tiene que estar muy bien hecha en **960×1080**, no en pantalla
completa. Menos superficie donde fallar, y todo el esfuerzo de calidad concentrado en un marco fijo.

**Lo único a decidir del presentador:** vos escribiste "un mismo personaje que sea random". Para un diario
conviene que sea **siempre el mismo** — la cara repetida es lo que construye el hábito y la marca; un
presentador distinto cada día no acumula nada. Pero cuál sea ese personaje da igual y lo elegís vos.
Antes de animar nada va un **cuadro fijo del layout para aprobar**, como manda tu regla.

### Estructura del episodio (~20 min)

El tercer tema que te faltaba: propongo **Tecnología y Energía**. Es donde la política y la economía chocan
de verdad hoy (chips, tierras raras, LNG, IA) y es exactamente el eje del ep. 06.

| Bloque | Min | Contenido |
|---|---|---|
| Cold open | 0:45 | El hecho del día, con las preguntas cortas + "stay to the end" |
| Intro fija | 0:14 | La de siempre |
| **THE POWERS** | 7:00 | EEUU · Europa · China · Rusia — política y seguridad |
| **THE MONEY** | 4:00 | Economía, mercados, energía, comercio |
| **TECH & ENERGY** | 2:30 | Chips, IA, tierras raras, ductos |
| **THE SOUTH** | 3:00 | Latinoamérica, con Argentina primero |
| **THE PACIFIC** | 2:00 | Australia, NZ, Indo-Pacífico |
| **WHAT TO WATCH** | 2:00 | El calendario de lo que viene — tu "lo que va a pasar" |
| Outro fija | 0:20 | La de siempre |

**WHAT TO WATCH es la firma del formato.** Un repaso de noticias lo hace cualquiera; un calendario de lo que
viene (elecciones, cumbres, vencimientos de deuda, reuniones de bancos centrales, fallos judiciales) es lo
que hace que alguien vuelva mañana. Y se arma solo: sale de fuentes con fecha futura, no de predicción.

**Nombre del formato:** propongo **THE LEDGER** — diario, encaja con Paper Trail, y se distingue de
DISPATCH y BRIEF en el sello de papel. Lo decidís vos.

### El cuello de botella, revisado

`escena.py` sigue siendo la línea 04:45 del cronograma y sigue sin existir. Lo que cambió con el formato de
dos paneles (§10bis) es **su tamaño**: ya no es "un motor de animación genérico que convierta cualquier
guion en una puesta en escena", que es un proyecto de meses; es **un rig de presentador + ocho
renderizadores de ficha**, que se construyen y se prueban de a uno.

Sigue siendo la parte difícil y sigue siendo lo primero que hay que empezar. Pero ahora es un problema con
fondo, y las reglas 24 (puntos de mapa exactos, el render aborta si no) y 25 (bloque de cambio de acto)
viven dentro de una sola ficha cada una, en vez de estar desparramadas por 1.400 líneas.

---

## 11. Costes

| Partida | Mensual | Nota |
|---|---|---|
| **Voz ElevenLabs (20 min/día)** | **$54-60** | ~18.000 chars/día × $0,10/1.000. **El 80 % del total.** |
| VPS | €12-25 | 8 vCPU ≈ €12,5 · 16 vCPU ≈ €25 (Hetzner ARM) |
| Postgres + pgvector | $0 | self-hosted |
| Embeddings | **$0** | MiniLM multilingüe local en CPU. (Alternativa OpenAI: $0,40/mes) |
| LLM de extracción y análisis | **$10** | OpenCode Go, ya contratado — ver §11bis |
| Guion diario | $0 | Claude Code en el VPS, dentro de tu plan |
| GDELT · Wikipedia · Federal Register · ECB | $0 | sin key |
| Guardian / NYT / YouTube Data | $0 | keys gratis |
| Imágenes fal.ai | $0-30 | $0 si reusa assets; el tope de USD 4 por producción no fue pensado para 30/mes |
| **TOTAL** | **≈ $70-110/mes** | contra los ~$7,50/mes de hoy |

**Los dos números que hay que mirar:**

1. **La voz es el 80 %.** Cualquier discusión de costes que no sea sobre la voz es ruido. Y el tope de
   USD 4 por producción (`COSTOS.md`) fue definido para 2 episodios al mes. A 30 al mes, ese tope y esta
   cadencia no describen el mismo sistema: **hace falta que decidas un presupuesto mensual nuevo**, no que
   yo recorte el video.
2. **La inteligencia es casi gratis.** El diseño de dos etapas (§1b) es lo que lo logra: el LLM ve 100
   clusters, no 3.000 artículos.

---

## 11bis. Enrutado de modelos con OpenCode Go (propuesta de Agustín, 2026-09-11)

> Agustín propuso: investigación → Grok 4.6 · análisis → GPT-5.6 Luna / Kimi K3 · guion → GPT-5.6 Luna ·
> tareas masivas → GLM-5.3 Flash / DeepSeek V4 Flash. Verificado el 2026-09-11.

**Sí se puede usar desde el pipeline, y esto era lo que había que confirmar.** OpenCode corre sin TUI:
`opencode serve` levanta un servidor HTTP local y `opencode run --attach http://localhost:4096` evita
pagar el arranque en cada llamada. Y lo más importante para una cadena desatendida: **en ejecuciones
programadas, `OPENCODE_PERMISSION` deniega las preguntas**, así que un job de cron no se queda colgado
esperando una aprobación que nadie va a dar a las 4 de la mañana.

### Los límites mandan sobre el diseño

OpenCode Go: **USD 10/mes**, y los topes están en *valor de uso*, no en requests:
**USD 12 cada 5 horas · USD 30 por semana · USD 60 por mes.**

Carga estimada del diario: ~100 extracciones (2,5K tokens c/u) + ~30 narrativas (3K) + 1 guion (45K)
= **~385K tokens/día ≈ 11,5M/mes**.

| Si eso corre en… | Costo/mes aprox. | ¿Entra en los USD 60? |
|---|---|---|
| Flash (GLM-5.3 Flash, DeepSeek V4 Flash) | **USD 1-6** | sí, con muchísimo margen |
| Un modelo premium para todo | **USD 35-170** | **no** |

**Conclusión: el enrutado que propuso Agustín no es una optimización, es el requisito para que el plan
alcance.** La etapa masiva tiene que ir en Flash o el tope mensual se come el proyecto.

### El tope de 5 horas, que es el que muerde

USD 12 cada 5 horas es un tope de **ráfaga**, y el diario es exactamente una ráfaga: las 100 extracciones
salen todas entre 04:00 y 04:30. Si esa tanda va en un modelo caro, se puede chocar el tope **a mitad de
la corrida** y el video no sale ese día. Dos mitigaciones, las dos baratas:
la tanda masiva en Flash (la ráfaga queda en centavos), y un limitador que reparta las llamadas en la
media hora en vez de dispararlas juntas.

### Los topes son POR MODELO, no una bolsa común (verificado en opencode.ai/docs/go)

Esto es lo que más cambia el plan, y no es lo que yo había asumido. Cada modelo trae su propio tope, y
van de USD 15 a USD 60 mensuales:

| Modelo | 5 h / semana / mes | req. estimadas por 5 h | Formato de API |
|---|---|---|---|
| **GPT 5.6 Luna** | 12 / 30 / 60 | **2.050** | `/zen/go/v1/responses` |
| **Grok 4.6** | 12 / 30 / 60 | — | `/zen/go/v1/responses` |
| **GLM-5.3-Flash** | 12 / 30 / 60 | **6.320** | `/zen/go/v1/chat/completions` |
| **DeepSeek V4 Flash** | 6 / 15 / 30 | **13.000** | `/zen/go/v1/chat/completions` |
| **Kimi K3** | **3 / 7,50 / 15** | **110** ⚠ | `/zen/go/v1/chat/completions` |
| GLM-5.3 | 3 / 7,50 / 15 | — | `/zen/go/v1/chat/completions` |
| DeepSeek V4 Pro | 3 / 7,50 / 15 | — | `/zen/go/v1/chat/completions` |
| Qwen3.8 Flash | 6 / 15 / 30 | — | `/zen/go/v1/messages` |

**Lo que confirman los números: el enrutado de Agustín es correcto.** Con 6.320 y 13.000 requests por
5 horas, la tanda masiva de ~100 extracciones no despeina a los Flash. Y Luna con 2.050 por 5 horas sobra
para un guion diario.

**La advertencia: Kimi K3 son ~110 requests por 5 horas.** Es el modelo más ajustado de todo el plan.
Para las ~30 narrativas del día alcanza, pero deja poco margen de reintento y **no tolera que otra etapa
lo comparta**. Si el análisis va en K3, que sea lo único que use K3.

**Discrepancia a verificar en la cuenta:** la página de modelos da a Luna un tope mensual de USD 60 y la
página comercial dice USD 15. No lo puedo resolver desde afuera; con 15 igual entra un guion diario, pero
conviene mirarlo antes de apoyarse en él.

### Tres correcciones a la propuesta

1. ~~Luna no está en el catálogo~~ — **estaba equivocado: Luna sí está en OpenCode Go**, lo anunció
   OpenCode. La propuesta de Agustín se sostiene tal cual.
   Lo que sí apareció es que **la API es compatible con OpenAI**, y con un detalle que importa: **hay tres
   formatos distintos según el modelo** — `responses` (Luna, Grok), `chat/completions` (GLM, Kimi,
   DeepSeek) y `messages` (MiniMax, Qwen, y el mismo formato que usa Claude). Esto convierte la
   "función única" de más abajo de recomendación en **requisito**: cambiar de Luna a Kimi no es cambiar un
   nombre, es cambiar la forma del request.
   (Dato descartado: una búsqueda devolvió que Luna tendría un tope de 220 tokens de salida. La
   documentación oficial **no publica límites por request** de ningún modelo. Era ruido del resumidor.)
2. **"Investigación" con Grok choca con el principio del Radar.** Si un modelo sale a buscar a la web y
   devuelve un resumen, se pierde todo lo que hace valioso al sistema: el conteo de fuentes independientes,
   el `wire_origin`, la comparación de narrativas por bloque y el enlace original que va citado en el video.
   Queda un resumen seguro y sin rastro, que es justo lo que el diseño evita.
   **Cómo acotarlo sin perderlo:** Grok no busca noticias, **cubre huecos que el Radar marcó** ("de este
   evento no tengo fuente asiática, buscá"). Y lo que traiga entra a la base como `claim` con
   `evidence: none` hasta que una fuente real lo respalde. Nunca como `fact`, nunca directo al guion.
3. **Los modelos Flash rompen JSON.** La etapa 2 de `videos/DAILY/DIARIO.md` §5.1 aborta si el JSON no
   valida, así que la etapa masiva necesita: salida estructurada activada, validación contra esquema,
   2 reintentos, y **escalar a un modelo más fuerte al tercer fallo** en vez de tirar el día.

### Cómo decidir cuál escribe el guion: midiendo, no por fama

Agustín ya tiene el mejor banco de pruebas posible: **seis episodios escritos con la voz de la casa**.
El bake-off es media hora: mismo brief y mismos documentos de estilo (`ESTILO.md`, `IDEOLOGIA.md`,
`CANAL.md`), N modelos, comparación a ciegas contra el guion real del episodio. Para la etapa masiva la
métrica es aún más simple y objetiva: **% de JSON válido a la primera** y aciertos en `fact` vs `claim`
sobre 50 enunciados etiquetados a mano.

Una nota sobre el guion que no depende de qué modelo gane: **conviene fijarlo y no rotarlo.** Un diario
vive de sonar igual todos los días; cambiar el modelo del guion cambia el registro, y el público lo nota
antes que uno.

### La cascada: OpenCode primero, Claude del VPS como red

Decisión de Agustín (2026-09-11): **OpenCode es la primera opción para todo. Si se agotan los créditos,
ahí entra el Claude que ya corre en el VPS.** No reemplaza nada de lo ya definido; es un añadido con
failover.

Todas las llamadas pasan por **una sola función**, `llm(tarea, prompt, esquema=None)`, que resuelve tres
cosas: qué modelo le toca a esa tarea, en qué formato de API hablarle (son tres, ver arriba), y a quién
caer si falla.

| Tarea | 1.ª opción | 2.ª | Red | Nota |
|---|---|---|---|---|
| **masivas** (extracción, clasificación fact/claim) | GLM-5.3-Flash | DeepSeek V4 Flash | **ninguna: degrada** | ver abajo |
| **análisis** (narrativas, escalada) | Kimi K3 | GLM-5.3 | Claude VPS | K3 no lo comparte con nadie |
| **guion** | GPT-5.6 Luna | Kimi K3 | Claude VPS | fijo, no rota (ver abajo) |
| **investigación** (huecos marcados) | Grok 4.6 | — | Claude VPS | acotada, ver punto 2 |

**La excepción importante: la etapa masiva NO cae en Claude.** Cien llamadas diarias escalando al plan de
Claude es exactamente cómo se va la cuenta sin que nadie lo note. Si los dos Flash se agotan, la etapa
**degrada**: procesa sólo los N eventos de mayor importancia y marca el resto como pendientes. Un día con
menos eventos analizados es mucho mejor que una factura sorpresa.

Y algo que la cascada necesita para no ser una caja negra: **cada llamada registra en `run_log` qué modelo
la sirvió de verdad.** Sin eso no hay forma de darse cuenta de que hace tres semanas todo viene saliendo
por la red de emergencia.

El otro beneficio de la función única: si algún día conviene salir de la suscripción, DeepSeek, GLM y Kimi
tienen APIs directas y baratas. Cambiarlo es una línea, no una refactorización.

## 11ter. Qué hay gratis de verdad (investigado 2026-09-11)

> Agustín se quedó sin cuota semanal de OpenCode y al límite de su suscripción de Claude, y preguntó
> por OpenRouter. Investigado contra la documentación oficial de cada proveedor.

### El ganador no es OpenRouter

| Proveedor | ¿Gratis permanente? | Alcanza para las 100 masivas | Alcanza para el guion |
|---|---|---|---|
| **Mistral La Plateforme** | **sí — USD 10/mes de crédito recurrente, sin tarjeta** | sí | **sí, y es el único con buen escritor** |
| **Google Gemini (AI Studio)** | sí | sí, con muchísimo margen | sí, pero sólo Flash (los Pro salieron del gratuito en abril) |
| Groq | sí | **no**: el tope es 200.000 tokens/día por modelo y la etapa masiva pide 250.000 | no |
| OpenRouter | sí | **no**: 50 requests/día, y la etapa masiva son 100 | entra (1 llamada), pero ningún modelo `:free` escribe bien |
| Cerebras | **no** — mataron el tier gratuito el 17-ago-2026 | — | — |
| SambaNova | sí, pero 20 req/**día** | no | no |
| GitHub Models | **muerto**, retirado el 30-jul-2026 | — | — |
| Together · Fireworks · DeepSeek · Hyperbolic · Alibaba · Scaleway | no: sólo crédito de prueba | — | — |

**Mistral gana por una razón sencilla:** el plan Free da **USD 10 por mes de crédito de API,
recurrentes y sin tarjeta**, y la carga completa cuesta **~USD 5,27/mes** (masivas y análisis en
Small 4, el guion en Medium 3.5). Es el único que cubre las dos etapas incluyendo un escritor
decente sin poner plata.

### Dos trampas de OpenRouter que conviene saber

1. **Son 50 requests por día, no 200.** Los blogs que dicen 200 están desactualizados; la
   documentación oficial dice 50. Sube a 1.000/día si alguna vez compraste USD 10 en créditos —
   compra **acumulada histórica**, no saldo: se compra una vez y el escalón queda para siempre.
2. **Sólo 5 de sus 19 modelos gratuitos soportan salida estructurada**, y un modelo que no la
   soporta **no degrada: la llamada falla**. Por eso las peticiones a OpenRouter van con
   `provider: {require_parameters: true}` (ya implementado en `EXTRA_CUERPO`), o el router te manda
   a un endpoint incapaz y el pipeline aborta de forma intermitente.

### La privacidad decide el orden de la cascada

**El tier gratis de Gemini y el free mode de Mistral entrenan con lo que les mandás.** Los términos
de Google son explícitos: *"human reviewers may read, annotate, and process your API input and
output"*. Mistral deja desactivarlo a mano (Admin Console → Privacy); el tier gratuito de Google no.

Esto importa porque **la etapa `guion` es la única que manda `ESTILO.md` e `IDEOLOGIA.md`** — tu
postura política y tus reglas editoriales. Las otras etapas sólo mandan titulares que ya son
públicos. Por eso:

```
guion     OpenCode → Mistral Medium → Gemini Flash → Claude
masivas   OpenCode ×2 → Gemini Flash → Mistral Small → OpenRouter    (sin red a Claude)
analisis  OpenCode ×2 → Gemini Flash → Mistral Small → Claude
```

Mistral va antes que Gemini en `guion` a propósito. **Antes de la primera llamada a Mistral hay que
hacer el opt-out de entrenamiento.**

### Cómo se agrega un proveedor

`radar/llm.py` tiene una tabla `PROVEEDORES`: agregar uno es **una fila**, no código. Los siete
compatibles con OpenAI ya están precargados y probados. Y si falta la clave de uno, **la cascada lo
saltea y sigue** — se pueden tener tres configurados y usar el que tenga cuota ese día.

## 12. Legal y técnico

**Lo que sí se puede, sin dudas:**
- Leer RSS. Los feeds se publican para eso.
- Guardar **titular + link + fecha + un resumen escrito por vos**. Citar y enlazar.
- GDELT: explícitamente libre. Federal Register: dominio público. Wikipedia: CC-BY-SA (citar).

**Lo que no:**
- **Guardar o republicar el texto completo de los artículos.** Por eso el esquema tiene `summary` (nuestro)
  y no `body`. Esto no es una precaución exagerada: es lo que separa "herramienta de investigación" de
  "infracción a escala".
- Reuters y AP bajo licencia de agencia. Ni con el MCP (que no tenés) podrías usarlo de base para un video
  monetizado sin contrato.

**Los cuatro riesgos concretos, por orden de gravedad:**

1. **RT y Sputnik están sancionados en la UE.** Si el VPS está en Alemania (Hetzner) o en cualquier país de
   la UE, esto no es teórico. Leer para analizar no es lo mismo que redistribuir, pero la línea existe y no
   la puedo trazar por vos. **No sé con certeza el estado exacto de la lista hoy ni si TASS entró en algún
   paquete posterior — hay que verificarlo antes de encender esos feeds.** Mitigación de diseño: guardar de
   RT/TASS únicamente `claim` con atribución, nunca texto, y nunca citarlos en pantalla como fuente de un
   hecho, sólo como "esto es lo que dice Moscú". Eso además es lo correcto editorialmente.
2. **Google News RSS a alto volumen.** Es un feed público, pero martillarlo con cientos de consultas por
   hora va contra el espíritu de sus términos y te ganás un bloqueo por IP. Mitigación: pocas consultas por
   ciclo (una por fuente puente, 6 en total), cachear, y `If-Modified-Since`.
3. **Monetización de YouTube.** Un video diario que habla de conflictos activos pega de lleno en la política
   de "eventos sensibles". Tu `MONETIZACION.md` ya tiene el criterio; el riesgo nuevo es **publicar sin que
   nadie lo lea**. Un solo encuadre automático desafortunado sobre un atentado puede costarte el canal, no
   un video. Por eso la compuerta invertida de §10 no es burocracia: es la protección del activo.
4. **GDELT 429.** Técnico y seguro si se respeta la cola de 5 s. Medido.

---

## 13. MVP — cuatro fases

**Fase 0 · "¿son las fuentes correctas?" (un fin de semana)**
Ingest de los 78 feeds → Postgres → un mensaje de Telegram a las 06:00 con los titulares del día agrupados
por bloque. Sin clustering, sin LLM, sin scores. **Valor inmediato:** en una semana sabés si te falta una
fuente, comparándolo contra el Portal:Current_events de Wikipedia.

**Fase 1 · "¿qué pasó hoy?" (1 semana)**
+ embeddings, clustering incremental, score de importancia, **y el MCP**. Desde acá, Claude te contesta
"¿qué pasó entre EEUU y China hoy?" con eventos agrupados y fuentes. **Acá el Radar ya sirve solo**, aunque
nunca hagas el video diario: te elige los temas de los Dispatch y los Brief que ya hacés.

**Fase 2 · "¿quién dice qué?" (1 semana)**
+ statements con fact/claim/disputed, narrativas por bloque, `compare_narratives`, video_score, alertas,
dashboard HTML.

**Fase 3 · el video diario**
+ `brief_del_dia` → guion → **`escena.py`** → render → subida programada. El 80 % de esta fase es
`escena.py`, y no depende del Radar: se puede empezar en paralelo desde el día uno.

### Una recomendación sobre el orden, que decidís vos

Después de la Fase 1 el Radar ya te sirve para elegir temas de los Dispatch y Brief que hacés hoy, sin
cambiar nada de tu proceso. Yo arrancaría por ahí y usaría ese período para construir `escena.py` con calma,
en vez de saltar de "ep. 6, quincenal" a "20 min diarios automáticos" de una. Pero el formato lo decidís vos
y si querés ir directo a la Fase 3, se hace: sólo quería que supieras dónde está el trabajo pesado antes de
elegir.

---

## 14. Lo que necesito que decidas antes de escribir código

1. **¿Cuántos vCPU y cuánta RAM tiene el VPS, y dónde está alojado?** Define si el render de 20 min entra
   (§4) y si los feeds rusos son un problema legal (§12.1).
2. **Presupuesto mensual.** El tope de USD 4 por producción no describe una cadencia diaria (§11). ¿Cuál es
   el número nuevo?
3. **¿El diario reemplaza o convive con Dispatch/Brief?** Cambia el calendario y el diseño de la miniatura.
4. **¿Aceptás la compuerta invertida** (publica solo salvo bandera roja) o querés aprobar todos los días?
5. **¿Enciendo RT/TASS** desde el arranque, o el Radar empieza sólo con occidentales + chinos + OSINT hasta
   que verifiquemos las sanciones?
6. **El tercer tema: ¿Tecnología y Energía?** Y el nombre del formato: ¿THE LEDGER?
