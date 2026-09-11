# ESTADO — dónde está el sistema y qué sigue

> **Si sos una sesión de Claude arrancando en el VPS: leé esto entero antes de tocar nada.**
> Actualizado 2026-09-11. Escrito por la sesión que construyó el sistema, para la que lo continúe.

---

## 1. Qué es esto, en un párrafo

Dos cosas que comparten motor. **El Radar** lee 79 fuentes de noticias de siete perspectivas
distintas (occidental, rusa, china, árabe, israelí, latinoamericana, Asia-Pacífico), agrupa las que
hablan del mismo acontecimiento y separa **hechos** de **afirmaciones**. **THE LEDGER** es un
informativo diario de ~20 minutos que se produce y publica solo a las 12:00 UTC, con tres
presentadores de papel recortado y un catálogo cerrado de ocho fichas visuales.

Arquitectura y todo lo medido: `RADAR.md`. Manual del formato: `videos/DAILY/DIARIO.md`.
Firmas entre módulos: `radar/CONTRATO.md`. Despliegue: `despliegue/README.md`.

**El dueño es Agustín.** Canal de YouTube en inglés, sin ingresos todavía, sin presupuesto.
Todas las decisiones editoriales son suyas.

---

## 2. Dónde está todo, exactamente

| | |
|---|---|
| App | `/opt/papertrail` (clonado de github.com/agusoler000/paper-trail-geo) |
| Python | `/opt/papertrail/.venv/bin/python` — **usar siempre este, no el del sistema** |
| Base | contenedor `papertrail-db`, Postgres 16 + pgvector, **127.0.0.1:5442**, base `radar` |
| Config | `/opt/papertrail/.env` (chmod 600) |
| VPS | Contabo, Ubuntu 24.04, 6 vCPU, 11 GB (5,6 libres), 8 GB de swap, **Francia** |
| Ya corriendo antes | Coolify, Supabase, n8n, Evolution API — **no tocar nada de eso** |

Comprobación de una línea, dice qué falta y con qué comando se arregla:

```bash
cd /opt/papertrail && .venv/bin/python despliegue/comprobar.py
```

---

## 3. Estado ahora mismo

### Funciona y está verificado en este VPS

- Los **13 módulos** pasan su autotest acá, no sólo en la máquina de desarrollo.
- **Ingesta:** 3.358 artículos de 71 fuentes en 40 s. La deduplicación anda (segunda corrida: sólo
  80 nuevos). El chequeo de frescura detectó y apagó feeds zombie que devuelven HTTP 200 con
  contenido de hace días (Bellingcat, Economist, Ynet).
- **Agrupamiento:** 80 artículos en 15 s con el índice HNSW de pgvector.
- **Voz:** las tres voces de Piper bajadas y probadas. Cuesta cero.
- **Rigs:** los tres presentadores cortados en 6 piezas cada uno.

### Timers de systemd

| Timer | Estado | Qué hace |
|---|---|---|
| `papertrail-radar` | **activo**, cada 30 min | ingesta + agrupa + puntúa |
| `papertrail-vigilante` | **activo**, 10:00 UTC | avisa si no hay video subido |
| `papertrail-diario` | **APAGADO A PROPÓSITO** | produce y sube el video a las 04:00 UTC |

El diario está apagado porque **todavía no se aprobó ningún guion**. No lo enciendas sin que
Agustín haya leído uno y dado el visto bueno.

### Claves en `.env`

| Variable | Estado |
|---|---|
| `MISTRAL_API_KEY` | **puesta.** Es la que atiende todo hoy |
| `OPENCODE_API_KEY` | puesta, pero **sin cuota semanal** — se repone sola |
| `RADAR_DSN` | puesta, la escribió el instalador |
| `GEMINI_API_KEY` | **vacía a propósito.** Decisión de Agustín: no se fía de la injerencia de Google en sus guiones. **No la agregues.** |
| `ANTHROPIC_API_KEY` | vacía. Es opcional, sólo red de la cascada |

---

## 4. EL PRÓXIMO PASO, y es uno solo

**Generar el primer guion y que Agustín lo lea.** Es lo único del sistema que todavía no se probó,
y lo que decide si el formato existe. Todo lo demás está verificado.

```bash
cd /opt/papertrail
.venv/bin/python videos/DAILY/daily.py --correr $(date -u +%F) --solo recolectar
.venv/bin/python videos/DAILY/daily.py --correr $(date -u +%F) --solo guion
cat videos/DAILY/_dias/$(date -u +%F)/guion.json
```

La primera no gasta nada (es todo local). La segunda gasta del crédito de Mistral (~USD 0,10).

**Qué mirar en ese guion, en este orden:**

1. ¿Suena a Paper Trail o suena a IA? Ese es el único criterio que importa.
2. ¿Lo que un gobierno **afirma** está narrado como afirmación, con el actor nombrado? Nunca como
   hecho. Es la regla editorial central del canal.
3. ¿Usa la ficha `versus` cuando hay versiones enfrentadas? Es la firma del formato.
4. ¿Los bloques tienen el tiempo que merecen ese día? Los minutos varían según el peso real de las
   noticias (`videos/DAILY/escaleta.py`).

Si el guion no convence, **el trabajo es el prompt de `etapa_guion` en `videos/DAILY/daily.py`**, no
el resto del pipeline.

### Después del guion, en orden

1. Autorizar YouTube una vez: `.venv/bin/python videos/DAILY/subir.py --autorizar`
2. Primer video completo, subido como **privado** y mirado entero antes de publicar nada.
3. Recién ahí: `sudo systemctl enable --now papertrail-diario.timer`

---

## 5. Trampas ya encontradas — NO las redescubras

Cada una costó una corrida entera. Están arregladas; esto es para que no se vuelvan a introducir.

**1. El `.env` no se carga solo en una corrida a mano.** Los timers lo leen con `EnvironmentFile`;
el shell no. Cuando pasó, `RADAR_DSN` vino vacío, el sistema cayó a SQLite y se puso a comparar
3.321 vectores de a uno en Python: no fallaba, no terminaba. Ahora lo carga `radar/entorno.py`, que
llaman todos los puntos de entrada. **Si agregás un punto de entrada nuevo, llamalo ahí.**

**2. `puntajes` devuelve dicts, no números.** Cada componente del desglose es
`{valor, peso, aporta, detalle}`. Las columnas `s_*` son `real`. SQLite aceptaba el dict; Postgres
lo rechaza. Hay una guardia en `almacen.actualizar_evento` que ahora lo dice claro.

**3. El ancla de entidad NUNCA promueve a "mismo acontecimiento".** Sólo lleva un par a "duda",
donde decide un LLM barato. Con el ancla sumando directo al puntaje, un cluster llamado *"The tech
wars are about to enter a fiery new phase"* se tragó un puente en Nueva Zelanda y el pase de Messi.
Está en `radar/semantica.py` con los números medidos.

**4. Un `fact` con una sola fuente independiente no existe.** BBC, Yahoo y veinte medios publicando
el mismo cable de Reuters son **una** fuente, no veinte. El conteo va por `wire_origin` distintos y
la regla vive en un `CHECK` de la base, no en un prompt. **No la relajes.**

**5. `.gitignore` no acepta comentarios al final de la línea.** El `#` sólo comenta si abre la
línea; al final se vuelve parte del patrón y la regla deja de funcionar en silencio.

**6. Un feed que devuelve HTTP 200 puede estar muerto.** El de WSJ devolvía contenido de enero de
2025. Por eso hay chequeo de frescura, y por eso apaga fuentes solo.

---

## 6. Reglas de Agustín que hay que respetar

- **Los números que da son referencia, no especificación.** Si pide "5 segundos" y sale 7, está
  bien. Sólo es literal si dice **"exactamente"** o hace énfasis. Ver `feedback-limites-no-literales`.
- **El formato lo decide él.** No proponer acortar el video para ahorrar créditos.
- **Respuestas cortas.** El detalle va a documentos; el chat, en pocas líneas.
- **Nunca cerrar sus pestañas ni sesiones del navegador.**
- **Antes de generar una imagen, buscar en el índice de assets.** Hay créditos ya pagados.
- **Tope de fal.ai: USD 4 por producción.** Es un techo, no un presupuesto.
- **No subir al repo videos, guiones, audio ni sus documentos editoriales.** Sólo la estructura.
  `canal/IDEOLOGIA.md` y `canal/MONETIZACION.md` viven en el VPS a mano, fuera de git, porque son
  su postura política y su criterio de monetización.

---

## 7. Comandos que vas a necesitar

```bash
# ver el entorno cargado, sin revelar las claves
.venv/bin/python radar/entorno.py

# los timers: cuándo corren y cuándo corrieron
systemctl list-timers 'papertrail-*'
journalctl -u papertrail-radar -n 40 --no-pager

# consultar el Radar hablando (8 herramientas MCP)
.venv/bin/python radar/mcp_server.py

# retomar un día que se cortó (las etapas son idempotentes)
.venv/bin/python videos/DAILY/daily.py --correr 2026-09-12
.venv/bin/python videos/DAILY/daily.py --correr 2026-09-12 --desde render

# el autotest de un módulo
.venv/bin/python radar/semantica.py --autotest
```

**El render es resumible:** los cuadros van a `videos/DAILY/_frames_<fecha>/` y arranca desde el
último escrito. `produccion/motor.py` sí borra su directorio al arrancar — no lo uses para el diario.

---

## 8. Lo que falta, sin maquillar

- **El guion nunca se generó.** Es el único paso sin probar y el que decide todo.
- **La ficha `mapa`** dibuja una proyección simple; falta engancharla a las hojas reales de
  `produccion/mapa_*.py` para cumplir la regla 24 (los puntos son exactos y el render aborta si no).
- **El brazo del presentador C en pose `senala`** cruza el pliegue y se mete en el panel de la ficha.
- **Sin `topics`** (los pone el LLM en la extracción), el brief tira todo a THE POWERS.
- **La etapa `investigacion`** se quedó sin proveedor: sólo la atendía OpenCode. No bloquea nada.
