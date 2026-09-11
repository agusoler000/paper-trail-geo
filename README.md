# paper-trail-geo

Sistema de producción del canal **Paper Trail** (geopolítica, en inglés). Dos cosas que comparten motor:

1. **El Radar** — un radar geopolítico que lee 79 fuentes de siete perspectivas distintas, agrupa lo
   que habla del mismo acontecimiento y separa **hechos** de **afirmaciones**.
2. **THE LEDGER** — un informativo diario de ~20 min que se produce y se publica solo, todos los días
   a las 12:00 UTC.

> **¿Retomando en otra máquina o en otra sesión? Leé [`ESTADO.md`](ESTADO.md) primero.** Dice dónde
> está todo, qué funciona, cuál es el próximo paso y qué trampas ya se encontraron.

> Este repo es **sólo la estructura**: el código y lo necesario para levantar el sistema en otra
> máquina. No hay videos, ni guiones, ni audio, ni bases, ni claves.

---

## Qué hace, en una pasada

```
79 feeds RSS + Google News (puente) + GDELT + APIs oficiales
            ↓   cada 30 min
   ingesta · dedup por wire · chequeo de frescura
            ↓
   embeddings multilingües + ancla de entidad rara  →  acontecimientos
            ↓
   hecho / afirmación / disputado   ·   importancia 0-100
            ↓
   ┌─────────────┬──────────────────────┐
   │  MCP server │  video diario 12:00  │
   │  (Claude)   │  UTC, sin intervenir │
   └─────────────┴──────────────────────┘
```

## La decisión que define el sistema

**El modelo no decide qué es un hecho.** Extrae proposiciones con su atribución; el código cuenta
fuentes independientes y decide la etiqueta:

- `fact` — 2+ fuentes con **`wire_origin` distinto**, o un documento oficial del propio actor
- `claim` — todo lo demás, guardado **con el actor que lo afirma**
- `disputed` — dos versiones incompatibles del mismo asunto

La sutileza que lo sostiene: BBC, Yahoo y veinte medios más publicando el mismo cable de Reuters son
**una** fuente independiente, no veinte. Si el contador no lo sabe, el sistema etiqueta como hecho lo
que dijo una sola redacción. La regla vive en `CHECK` de la base, no en un prompt.

## Estructura

| | |
|---|---|
| `radar/` | ingesta, semántica, agrupamiento, puntajes, extracción, MCP, almacén |
| `videos/DAILY/` | el formato diario: escaleta, escena, fichas, voz, orquestador, subida |
| `videos/DAILY/presentador/` | los tres rigs de papel recortado y las bocas del lip-sync |
| `produccion/` | el motor de render compartido con el formato largo (PIL + ffmpeg) |
| `despliegue/` | instalador, chequeo previo y timers de systemd para el VPS |

Documentos: [`RADAR.md`](RADAR.md) (arquitectura y lo medido), [`videos/DAILY/DIARIO.md`](videos/DAILY/DIARIO.md)
(el manual del formato), [`radar/CONTRATO.md`](radar/CONTRATO.md) (las firmas entre módulos).

## Levantarlo en otra máquina

```bash
sudo bash despliegue/instalar.sh      # swap, venv, modelos, base, timers
python despliegue/comprobar.py        # dice exactamente qué falta y con qué comando se arregla
```

Detalle en [`despliegue/README.md`](despliegue/README.md).

## Coste

**Cero por video.** Embeddings y voz corren locales (fastembed y Piper, los dos sin GPU); los feeds
son gratis; el render es CPU; la subida no cuesta. Lo único que se paga es la suscripción de
OpenCode que escribe el guion.

## Probarlo

Cada módulo se verifica solo:

```bash
python radar/semantica.py --autotest
python videos/DAILY/daily.py --autotest
```

## Lo que no está acá

`canal/IDEOLOGIA.md` y `canal/MONETIZACION.md` — el sistema los lee para armar el prompt del guion,
pero son criterio editorial propio y van al VPS a mano. Ver `.gitignore`.
