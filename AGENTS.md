# AGENTS.md — Paper Trail (geopolítica + THE LEDGER + Radar)

Canal de YouTube **en inglés**, animación de recorte de papel, costo ~$0. Dos productos que comparten
motor, y ninguno se toca entre sí:

1. **Paper Trail** — Dispatch/Brief producidos a mano por episodio (motor + coreografía).
2. **THE LEDGER** — informativo diario ~20 min que se produce y publica solo, a las 12:00 UTC, sobre el Radar.

**Idioma: con Agustín (el dueño) en español, respuestas cortas. Contenido del canal: inglés.**
Toda decisión editorial es de Agustín. **Nunca publicar ni subir nada sin su QC humano: la subida es siempre su decisión.**

## Al arrancar (leer en este orden)

1. `RETOMAR.md` — bitácora real: qué se produjo último, dónde quedó, decisiones vigentes. Es el punto de entrada.
2. `ESTADO.md` — estado del sistema en el VPS, el próximo paso y las trampas ya pagadas (§5).
3. Skill **`paper-trail-video`** (`C:\Users\agust\.claude\skills\paper-trail-video\SKILL.md`) — la ley del formato largo: reglas 1-25 de Agustín + pipeline §2. Para subir shorts: skill `youtube-shorts-upload`.
4. `README.md` — qué es el repo (solo estructura; no hay videos/guiones/audio/claves).

## Sistemas (no mezclar)

| Dir | Qué | Documento |
|---|---|---|
| `radar/` | Radar: ingesta 79 fuentes → embeddings → clustering → fact/claim → scores → MCP | `RADAR.md`, `radar/CONTRATO.md` |
| `videos/DAILY/` | THE LEDGER: guion + 8 fichas + 3 presentadores + lip-sync, 9 etapas idempotentes | `videos/DAILY/DIARIO.md` |
| `produccion/` + `guiones/` + `videos/<NN>_<tema>/` | motor de render compartido + coreografía a mano (Dispatch/Brief/Shorts) | skill `paper-trail-video` |
| `despliegue/` | instalador, comprobador y timers systemd del VPS | `despliegue/README.md` |

## Comandos exactos

```bash
# autotest de un módulo (cada uno corre solo y sale 0/1)
python -m radar.<modulo> --autotest
python radar/semantica.py --autotest
python videos/DAILY/daily.py --autotest

# chequeo completo: dice exactamente qué falta y con qué comando se arregla
python despliegue/comprobar.py

# el diario por etapas idempotentes (en el VPS: .venv/bin/python)
python videos/DAILY/daily.py --correr 2026-09-14 --solo recolectar
python videos/DAILY/daily.py --correr 2026-09-14 --desde render   # retoma donde quedó

# ANTES de generar cualquier asset con IA (regla 19)
python produccion/indice_assets.py buscar <lo que haga falta>
```

## Reglas duras (no relajar)

- **Un `fact` con una sola fuente independiente no existe.** BBC+Yahoo+20 medios con el mismo cable de
  Reuters = **una** fuente (`wire_origin`). La regla vive en un `CHECK` de la base, no en un prompt (`ESTADO.md` §5.4).
- **No commitear videos, audio, guiones ni documentos editoriales.** Solo la estructura. `canal/IDEOLOGIA.md`
  y `canal/MONETIZACION.md` van al VPS a mano (postura política y criterio de monetización: quedan indexados
  para siempre si entran a un repo público). Ver `.gitignore`.
- **Costo $0; tope fal.ai USD 4 por producción** (episodio + shorts juntos). Es un **techo, no un presupuesto**:
  gastar lo mínimo y reusar assets primero (regla 19).
- **Los números que da Agustín son referencia, no especificación.** Solo es literal si dice "exactamente".
- **Una producción, un directorio**: `videos/<NN>_<tema>/` (episodio+shorts), `videos/S<NN>_<tema>/` (serie/suelto).
- **Títulos**: la regla vive solo en `canal/CANAL.md` §7.1 (vigente 14-sep: pregunta + oración corta, sin prefijo
  emoción). No inventar reglas que Agustín no haya dado él.
- **Un solo render a la vez** (`produccion/_frames` es compartido). El render del diario sí es resumible (`_frames_<fecha>/`).

## Trampas ya pagadas (no redescubrir — detalle en `ESTADO.md` §5)

1. **El `.env` no se carga solo en una corrida a mano** → cae a SQLite y tarda infinito. Cargarlo SIEMPRE vía
   `radar/entorno.py`; todo punto de entrada nuevo lo llama.
2. **`puntajes` devuelve dicts, no números** (`{valor,peso,aporta,detalle}`); las columnas `s_*` son `real`.
   SQLite acepta dicts, Postgres los rechaza.
3. **El ancla de entidad NUNCA promueve a "mismo acontecimiento"**, solo a "duda" (decide un LLM barato).
4. **En `.gitignore` el `#` solo comenta al abrir la línea**; al final pasa a ser parte del patrón.
5. **Un feed con HTTP 200 puede estar muerto** (contenido de hace días). El chequeo de frescura (72 h) lo apaga solo.

## Convenciones de código (`radar/CONTRATO.md`)

- Python 3.12, **stdlib primero**. Disponible: numpy, requests, httpx, openai, anthropic, jsonschema, mcp,
  fastapi, uvicorn, googleapiclient, PIL, sqlalchemy, fastembed, piper-tts. **NO** feedparser/psycopg/sklearn/
  sentence_transformers (RSS con `xml.etree`; Postgres vía sqlalchemy; test local = SQLite).
- Comentarios y docstrings en **castellano**, sin tildes en el código.
- Horas siempre **UTC y aware**; nada de fecha local implícita.
- Tipos compartidos: dicts planos (`ARTICULO`, `EVENTO`, `STATEMENT`, `NARRATIVA`); firmas exactas en `radar/CONTRATO.md`.

## VPS (deploy)

- `sudo bash despliegue/instalar.sh` (idempotente: swap 8 GB, venv, modelos, base pgvector en contenedor
  `papertrail-db` 127.0.0.1:5442, timers systemd). Después `python despliegue/comprobar.py`.
- Timers: `papertrail-radar` (30 min) · `papertrail-diario` (04:00 UTC, **apagado a propósito** hasta que Agustín
  apruebe un guion) · `papertrail-vigilante` (10:00 UTC).
- **No tocar** lo que ya corre en el VPS: Coolify, Supabase, n8n, Evolution API.
