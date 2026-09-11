# Despliegue — THE LEDGER en el VPS

> Todo lo necesario para que el diario salga solo, en orden. El VPS real: Contabo, Ubuntu 24.04,
> 6 vCPU, 11 GB, **Francia** (ver `RADAR.md` §12 sobre RT y Sputnik), con Coolify, Supabase, n8n y
> Evolution API ya corriendo. **Nada de esto los toca.**

## Por qué la app va al host y no a Docker

El render usa `multiprocessing` sobre todos los núcleos disponibles y corre con `nice -n 19` para no
competir con lo que ya está en producción. Meterlo en un contenedor agrega una capa entre el proceso
y el planificador del kernel justo donde importa que no la haya. La base sí va donde ya está: dentro
del Postgres de Supabase, en un `radar` aparte.

## Los cuatro pasos

### 1. Copiar el proyecto y ejecutar el instalador

```bash
rsync -az --exclude '_dias' --exclude '_frames_*' --exclude '*.db' \
      ./ usuario@vps:/opt/papertrail/
ssh usuario@vps 'sudo bash /opt/papertrail/despliegue/instalar.sh'
```

El instalador es **idempotente**: se puede correr las veces que haga falta. Hace, en orden:

| | Qué | Por qué |
|---|---|---|
| 1 | swap de 8 GB + `swappiness=10` | Hay 5,6 GB libres y **cero swap**. Un pico del render sin swap no arruina el render: **mata contenedores** y te tira Supabase o n8n. |
| 2 | `python3-venv`, `ffmpeg`, `git` | |
| 3 | venv en `/opt/papertrail/.venv` | Aislado del Python del sistema |
| 4 | modelos de Piper y de embeddings (~600 MB) | Una vez. Después todo es local y gratis. |
| 5 | base `radar` con `pgvector` dentro del Postgres de Supabase | Reusa lo que ya corre |
| 6 | los tres timers de systemd | |

### 2. Completar `.env`

```bash
nano /opt/papertrail/.env      # el instalador lo creó desde despliegue/env.ejemplo
chmod 600 /opt/papertrail/.env
```

Lo único imprescindible: `OPENCODE_API_KEY`, `ANTHROPIC_API_KEY` y `RADAR_DSN`.

### 3. Autorizar YouTube, una sola vez

```bash
cd /opt/papertrail && .venv/bin/python videos/DAILY/subir.py --autorizar
```

Abre el consentimiento de Google una vez y guarda el *refresh token*. A partir de ahí renueva solo y
no vuelve a pedir nada. **Es lo que hace que el video se publique a las 12:00 sin que nadie esté
despierto:** se sube como privado con `publishAt`, y YouTube lo publica por su cuenta.

### 4. Comprobar

```bash
cd /opt/papertrail && .venv/bin/python despliegue/comprobar.py
```

Revisa 40 cosas — sistema, swap, disco, dependencias, claves, modelos, los tres rigs, la base, la red
y el autotest de cada módulo — y **te dice exactamente qué falta y con qué comando se arregla**.
Sale 0 si el sistema puede producir un video hoy.

## La primera corrida, a mano y sin publicar nada

```bash
cd /opt/papertrail
.venv/bin/python videos/DAILY/daily.py --correr $(date -u +%F) --solo recolectar
.venv/bin/python videos/DAILY/daily.py --correr $(date -u +%F) --solo guion
cat videos/DAILY/_dias/$(date -u +%F)/guion.json
```

**Leé ese guion antes de seguir.** Es lo único del sistema que todavía no está probado, y es lo que
decide si el formato existe. Si convence, el resto de las etapas ya están verificadas.

## Los tres timers

| Timer | Cuándo | Qué hace |
|---|---|---|
| `papertrail-radar` | cada 30 min | Ingesta, agrupa, puntúa. `nice 10` |
| `papertrail-diario` | 04:00 UTC | Las 9 etapas. `nice 19`. Publica 12:00 UTC |
| `papertrail-vigilante` | 10:00 UTC | ¿Hay video subido? Si no, Telegram con la etapa que falló |

```bash
systemctl list-timers 'papertrail-*'          # cuándo corren
journalctl -u papertrail-diario -f            # mirar el diario en vivo
systemctl start papertrail-diario             # forzarlo ahora
```

## Si algo se corta

Las nueve etapas son **idempotentes**: cada una consulta su estado y si ya salió OK para esa fecha,
se saltea. Volver a lanzar el día entero después de un corte no rehace lo que ya estaba.

```bash
.venv/bin/python videos/DAILY/daily.py --correr 2026-09-12                 # retoma donde quedó
.venv/bin/python videos/DAILY/daily.py --correr 2026-09-12 --desde render  # forzar desde una etapa
.venv/bin/python videos/DAILY/daily.py --correr 2026-09-12 --solo subir    # una sola
```

**El render es resumible:** los cuadros van a `videos/DAILY/_frames_<fecha>/` y arranca desde el
último escrito. `produccion/motor.py` borra su directorio al arrancar — y está bien para lo que hace —
pero acá eso significaría que un corte a las 07:00 obliga a rehacer dos horas y el video no sale.

## n8n

Los timers de systemd son el mecanismo; n8n es opcional y sirve para **ver** y **avisar**. Si lo
querés usar, un workflow con un nodo Execute Command por etapa contra los mismos comandos alcanza.
Lo que n8n **no** debe hacer es el procesamiento: pasa todos los ítems en memoria entre nodos y
3.850 artículos atravesando quince nodos revientan la RAM (`RADAR.md` §1a).

## Espacio en disco

Un día de cuadros a 1080p son ~8 GB, que se borran al armar el mp4. Con 143 GB libres sobra, pero si
se acumulan días fallidos conviene limpiarlos:

```bash
find /opt/papertrail/videos/DAILY -maxdepth 1 -name '_frames_*' -mtime +3 -exec rm -rf {} +
```

## El MCP, para consultar el Radar hablando

En tu máquina, no en el VPS:

```bash
claude mcp add --transport stdio -s user radar -- \
  ssh usuario@vps '/opt/papertrail/.venv/bin/python /opt/papertrail/radar/mcp_server.py'
```

Y ahí ya podés preguntar "¿qué pasó hoy entre EEUU y China?" o "mostrame las narrativas del último
incidente" contra tu propia base.
