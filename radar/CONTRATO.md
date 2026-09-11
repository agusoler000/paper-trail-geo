# CONTRATO de interfaces — Radar + formato diario

> Fijado 2026-09-11. **Todo módulo se atiene a estas firmas exactas.** Si una firma no alcanza, se
> extiende con parámetros opcionales con valor por defecto; nunca se cambia lo que ya está escrito acá.
> Arquitectura: `RADAR.md`. Formato del video: `videos/DAILY/DIARIO.md`.

## Reglas transversales

- **Python 3.12, stdlib primero.** Disponibles: `numpy`, `requests`, `httpx`, `openai`, `anthropic`,
  `jsonschema`, `mcp`, `fastapi`, `uvicorn`, `googleapiclient`, `google.auth`, `PIL`, `sqlalchemy`.
  **NO disponibles y no se usan:** `feedparser`, `psycopg`, `sentence_transformers`, `sklearn`.
  **Agregada el 2026-09-11:** `fastembed` (ONNX, sin torch) — imprescindible, ver `RADAR.md` §4bis.
  RSS se parsea con `xml.etree.ElementTree`. Postgres se habla por `sqlalchemy` (el driver lo pone el VPS);
  para test local, SQLite.
- **Sin dependencias nuevas sin decirlo.** Si un módulo necesita una, lo escribe en su docstring.
- **Nada de `Date.now()` implícito en datos**: toda hora es UTC y aware (`datetime.now(timezone.utc)`).
- **Comentarios y docstrings en castellano**, como el resto del repo. Sin tildes en el código.
- **Cada módulo corre solo**: `python -m radar.<modulo> --autotest` hace una prueba mínima y sale 0/1.

## Tipos compartidos (dicts planos, sin clases)

```python
ARTICULO = {
  "source_id": str, "url": str, "url_hash": str, "title_simhash": int,
  "wire_origin": str|None,     # 'reuters'|'ap'|'afp'|None(propio) — ANTI DOBLE CONTEO
  "title": str, "summary": str|None,
  "published_at": datetime|None, "detected_at": datetime, "lang": str|None,
  "event_id": int|None, "raw": dict,
}
EVENTO = {
  "id": int, "titulo": str, "first_detected": datetime, "last_updated": datetime,
  "estado": "breaking"|"developing"|"watchlist"|"closed",
  "importancia": int|None, "video_score": int|None,
  "paises": [str], "actores": [str], "topics": [str],
  "requiere_agustin": bool, "motivo_bandera": str|None,
  "riesgo_escalada": "bajo"|"medio"|"alto"|None,
}
STATEMENT = {
  "tipo": "fact"|"claim"|"disputed", "texto": str,
  "actor": str|None,            # OBLIGATORIO si tipo=='claim'
  "evidence": "official_doc"|"satellite"|"own_reporting"|"osint"|"none",
  "n_indep": int, "article_ids": [int], "disputa_de": int|None,
}
NARRATIVA = {"bloque": str, "resumen": str, "enfasis": str|None, "omite": str|None,
             "article_ids": [int]}
```

## radar/almacen.py — la capa de datos

```python
def conectar(dsn: str|None = None) -> "Almacen"
    """dsn None -> SQLite en radar/_radar.db (test local). postgresql://... -> Postgres."""

class Almacen:
    def init_esquema(self) -> None
    def cargar_fuentes(self, path_json: str) -> int          # devuelve nº de fuentes activas
    def fuentes(self, solo_activas=True) -> list[dict]
    def marcar_fuente(self, source_id, ok: bool, error: str|None = None) -> None
    def guardar_articulo(self, art: dict) -> int|None        # None si ya existia (url_hash)
    def articulos(self, desde=None, sin_evento=False, limite=500) -> list[dict]
    def guardar_vector(self, article_id: int, vec) -> None    # vec: list[float]
    def vecinos(self, vec, desde, umbral=0.78, limite=20) -> list[tuple[int,int,float]]
        """(article_id, event_id, similitud), solo articulos CON evento. Postgres: pgvector.
           SQLite: fuerza bruta con numpy."""
    def crear_evento(self, titulo: str, articulo_id: int, vec) -> int
    def adjuntar(self, evento_id: int, articulo_id: int, vec) -> None
    def actualizar_evento(self, evento_id: int, **campos) -> None
    def evento(self, evento_id: int) -> dict      # EVENTO + articulos + statements + narrativas
    def buscar_eventos(self, pais=None, actor=None, topic=None, desde=None, hasta=None,
                       min_importancia=None, min_video=None, estado=None, limite=50) -> list[dict]
    def guardar_statement(self, evento_id: int, st: dict) -> int
    def guardar_narrativa(self, evento_id: int, na: dict) -> int
    def registrar(self, etapa: str, ok: bool, n_in=0, n_out=0, error=None) -> None
    def ultima_corrida(self, etapa: str) -> dict|None
```

**Invariante que la base hace cumplir** (no un prompt): un `fact` exige `n_indep >= 2` **o**
`evidence == 'official_doc'`; un `claim` exige `actor`. En Postgres son `CHECK`; en SQLite se valida en
`guardar_statement` y se levanta `ValueError`.

## radar/ingesta.py

```python
FRESCURA_HORAS = 72
def leer_feed(feed: dict, timeout=20) -> tuple[list[dict], str|None]
    """feed: una entrada de radar/fuentes.json. Devuelve (articulos, error).
       Parsea RSS y Atom con xml.etree. Rellena wire_origin detectando 'Reuters'/'AP'/'AFP'
       en titulo/autor/fuente. Calcula url_hash (sha1) y title_simhash (64 bits)."""
def tick(almacen, solo=None, workers=12) -> dict
    """Recorre las fuentes activas en paralelo, guarda lo nuevo, marca feeds.
       CHEQUEO DE FRESCURA: si el item mas nuevo es > FRESCURA_HORAS, o hay 3 fallos
       seguidos, desactiva la fuente y lo deja en el dict devuelto.
       -> {leidos, nuevos, feeds_ok, feeds_muertos:[(id,motivo)]}"""
```

## radar/vectores.py

```python
def vectorizar(textos: list[str], dim=512) -> "np.ndarray"
    """TF-IDF de n-gramas de caracteres (3-5) proyectado a `dim` por hashing, L2-normalizado.
       Elegido en vez de un modelo: cero descarga, determinista, y a nivel de caracter
       tolera multi-idioma, que es justo lo que pide TASS + Infobae + Xinhua en la misma base.
       La interfaz queda igual si algun dia entra un modelo real."""
def similitud(a, b) -> float     # coseno; vectores ya normalizados -> producto punto
```

## radar/semantica.py  (agregado 2026-09-11 — reemplaza a vectores.py en el agrupamiento)

```python
def vectorizar(textos) -> "np.ndarray"      # (n, 384) normalizado, via fastembed
def similitud(a, b) -> float
class IdfEntidades:  __init__(corpus); ancla(a, b) -> 0..1
def decidir(semantico, ancla=0.0) -> "si"|"duda"|"no"
    """El ancla NUNCA promueve a 'si'. Solo lleva a 'duda', y ahi decide el LLM."""
def mismo_hecho(a, b, llm=None) -> bool     # resuelve el margen con un modelo Flash
```
`vectores.py` (TF-IDF) queda como respaldo sin red, pero **no sirve para agrupar**: RADAR.md §4bis.

## radar/agrupar.py

```python
VENTANA_HORAS = 72
def agrupar(almacen, umbral=UMBRAL, ventana=VENTANA_HORAS) -> dict
    """Incremental: por cada articulo sin evento, vectoriza, busca vecinos en la ventana,
       adjunta al evento del mejor vecino si supera el umbral, si no crea evento nuevo.
       -> {procesados, eventos_nuevos, adjuntados}"""
```

## radar/puntajes.py — funciones PURAS, sin base

```python
PESO_PAIS = {...}   # US/CN/RU 1.0 · DE/FR/GB/JP/IN 0.8 · ...
def importancia(ev: dict, articulos: list[dict], fuentes: dict) -> tuple[int, dict]
    """Formula de RADAR.md §6: 0.22 fuentes_indep + 0.18 cross_bloc + 0.15 tier
       + 0.15 velocidad + 0.15 actores + 0.10 dominio + 0.05 primaria.
       fuentes_indep cuenta wire_origin DISTINTOS (BBC+Yahoo con el mismo cable de
       Reuters = 1, no 2). Devuelve (0..100, desglose por componente)."""
def video_score(ev, articulos, ctx: dict) -> tuple[int, dict]
    """ctx: {'mapa_disponible': bool, 'assets': int, 'competencia': int, 'llm': {...}}"""
def banderas(ev, statements) -> tuple[bool, str|None]
    """requiere_agustin segun MONETIZACION.md e IDEOLOGIA.md."""
def clasificar(importancia: int) -> str   # 'breaking'|'high'|'relevant'|'low'
```

## radar/llm.py — el router con cascada

```python
RUTAS = {
  "masivas":      [("opencode","glm-5.3-flash"), ("opencode","deepseek-v4-flash")],   # SIN red a Claude
  "analisis":     [("opencode","kimi-k3"), ("opencode","glm-5.3"), ("claude", None)],
  "guion":        [("opencode","gpt-5.6-luna"), ("opencode","kimi-k3"), ("claude", None)],
  "investigacion":[("opencode","grok-4.6"), ("claude", None)],
}
FORMATO = {  # tres formas de API distintas, verificado en opencode.ai/docs/go
  "gpt-5.6-luna": "responses", "grok-4.6": "responses",
  "glm-5.3-flash": "chat", "glm-5.3": "chat", "kimi-k3": "chat",
  "deepseek-v4-flash": "chat", "deepseek-v4-pro": "chat",
}
BASE_OPENCODE = "https://opencode.ai/zen/go/v1"

def llm(tarea: str, prompt: str, esquema: dict|None = None, sistema: str|None = None,
        max_reintentos=2) -> str|dict
    """Recorre RUTAS[tarea]. Con `esquema`, valida con jsonschema; si no valida, reintenta;
       al agotar reintentos baja al siguiente modelo de la cascada.
       Baja tambien ante 429 / cuota agotada / error de red.
       'masivas' NO tiene red a Claude a proposito (100 llamadas/dia escalando a Claude es
       como se va la cuenta sin que nadie lo note): si se agotan los dos Flash, levanta
       CuotaAgotada y el llamador DEGRADA a los N eventos mas importantes.
       SIEMPRE devuelve por que modelo salio: el llamador lo registra en run_log."""

class CuotaAgotada(RuntimeError): ...
def ultimo_modelo() -> str    # que modelo sirvio la ultima llamada
```

Claves de entorno: `OPENCODE_API_KEY` y `ANTHROPIC_API_KEY`.

## videos/DAILY/fichas.py — el panel derecho

```python
W_FICHA, H_FICHA = 960, 1080
TIPOS = ["mapa","versus","titular","dato","serie","cronologia","calendario","plano"]
def render_ficha(tipo: str, datos: dict, size=(W_FICHA,H_FICHA), t=0.0) -> "PIL.Image"
    """t = segundos desde que entro la ficha, para animaciones de entrada.
       Paleta cerrada de ESTILO.md §2.2. UN SOLO elemento rojo por ficha."""
```

Datos por tipo (lo que emite el guion):
```
mapa       {"hoja": "mundo|europa|...", "puntos":[{"nombre","lat","lon","rojo":bool}], "flechas":[...]}
versus     {"titulo", "izq":{"actor","dice","fuentes"}, "der":{...}, "pie"}
titular    {"medio","fecha","titular","bajada"}
dato       {"numero","unidad","etiqueta","contexto"}
serie      {"titulo","unidad","puntos":[[x,y],...],"nota"}
cronologia {"titulo","hitos":[{"hora","texto"}]}
calendario {"titulo","fechas":[{"cuando","que","donde"}]}
plano      {"imagen": ruta, "pie"}
```

## videos/DAILY/escena.py — guion a cuadros

```python
W, H, FPS = 1920, 1080, 24
def cargar_guion(path: str) -> dict          # valida contra ESQUEMA_GUION
def construir(guion: dict, presentadores: dict) -> "Escena"
class Escena:
    dur: float
    def cuadro(self, t: float) -> "PIL.Image"   # 1920x1080 RGB, lista para motor.render
```

`ESQUEMA_GUION` (JSON Schema, lo que el LLM del guion debe emitir):
```json
{"bloques":[{"nombre":"THE POWERS","presentador":"A",
  "beats":[{"t":0.0,"texto":"...","ficha":"versus","datos":{...},"pose":"senala"}]}]}
```

## videos/DAILY/subir.py

```python
def subir(video: str, miniatura: str|None, titulo: str, descripcion: str,
          etiquetas: list[str], publicar_en: "datetime", lista: str|None = None) -> str
    """YouTube Data API v3, subida resumible. privacyStatus='private' + publishAt
       para que YouTube lo publique solo. Devuelve video_id.
       Credenciales: radar/_yt_token.json (refresh token, OAuth una sola vez)."""
def cuota_estimada() -> int   # 1600 insert + 50 thumbnail + 50 lista
```

## videos/DAILY/daily.py — el orquestador

```python
ETAPAS = ["recolectar","guion","voz","alinear","coreo","render","mezcla","miniatura","subir"]
def correr(fecha: str, desde: str|None = None, solo: str|None = None) -> dict
    """Etapas idempotentes. Cada una consulta run_log: si ya corrio OK para esa fecha, la saltea.
       El render es RESUMIBLE: cuadros en videos/DAILY/_frames_<fecha>/, arranca desde el
       ultimo escrito (NO borra el directorio: esa es la diferencia con motor.render)."""
def vigilante(fecha: str) -> dict
    """A las 10:00 UTC: ¿hay video subido y programado? Si no, que etapa fallo."""
```
