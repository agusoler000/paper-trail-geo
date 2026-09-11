# ESTRUCTURA — una producción, un directorio

> **Regla de Agustín (2026-09-08, literal):** *"Es muy importante que cada producción final tenga su directorio.
> Si es un short tenga su carpeta y si es un video largo + shorts que esté bien en su directorio.
> TODO LO REFERENTE A UN VIDEO ESTARÁ EN SU DIRECTORIO."*
>
> Lo que sigue después de §1 (el árbol concreto, qué queda compartido, el plan de migración) es **propuesta del
> asistente** para cumplir esa regla sin romper lo que ya funciona. Los números y nombres los cambia él cuando quiera.

---

## 1. Qué es "una producción"

Hay **tres tipos** y cada uno es una carpeta:

| Tipo | Cómo arranca la conversación | Carpeta | Qué contiene |
|---|---|---|---|
| **A · Episodio + shorts** | "hacemos un video de X" | `videos/<NN>_<tema>/` | el largo (Dispatch o Brief) **y** sus 3-5 shorts, con guion propio. Con "solo el video" queda `shorts/` vacío |
| **B · Serie de shorts** | "hacemos una serie de shorts sobre X" | `videos/S<NN>_<tema>/` | producción completa en formato short: un tema, **una subtemática por short**, numerados y encadenados |
| **C · Short suelto** | "hacemos un short de X" | `videos/S<NN>_<tema>/` | igual que B con una sola pieza (una serie de 1) |

El tipo se decide **en la primera pregunta de la conversación** y se escribe en la primera línea de
`videos/<dir>/README.md`. No se cambia a mitad de producción sin decirlo.

### Serie de shorts (tipo B) — pedido de Agustín, 2026-09-08

> *"También podemos generar una serie de shorts de una misma temática pero con varias subtemáticas. Por ejemplo el
> 11-S: un short con los hechos, otro de cómo se planeó, otro del origen, otro de las consecuencias en nuestra vida
> cotidiana, etc. Pero serán todos de una misma serie."*

Una serie es **una sola producción**: una investigación, un interrogatorio de postura, un set de arte, una tanda de
voz. Lo que cambia por pieza es el ángulo. Cada short es una carpeta numerada dentro de `shorts/`:

```
videos/S01_11s/
  README.md              ← tipo: serie · tema: 11-S · 5 piezas · estado de cada una
  postura.md  fuentes/  arte/            ← una vez para toda la serie
  shorts/
    serie.json           ← nombre en pantalla, orden, cuántas, cómo se encadenan
    01_hechos/           guion.md  audio/  coreo.py  _frames/  salida/
    02_plan/             …
    03_origen/           …
    04_consecuencias/    …
    05_hoy/              …
  publicar/              ← PLAN_SUBIDA.json de la serie + la playlist
```

Reglas de serie (propuesta del asistente, §3 de `SHORTS.md` tiene el detalle):
- **Numeración en pantalla**: sello de papel `PART 2 OF 5` en la esquina, misma posición en las cinco.
- **Cada pieza se entiende sola** (alguien va a entrar por la 4) **y cierra abriendo la siguiente**.
- **Playlist propia** en YouTube con el nombre de la serie; las cinco entran ahí y el enlace va en las cinco descripciones.
- **Una por día**, en orden, misma hora. Publicadas en desorden la serie no existe.
- El "video relacionado" de cada short apunta a la pieza anterior de la serie; si la serie desemboca en un episodio
  largo del mismo tema, todas apuntan al episodio y ese es el mejor uso de una serie.

---

## 2. El árbol de una producción

```
videos/04_malvinas/                    ← TODO lo de este video vive acá
  README.md                            ← ficha: tipo, formato, estado, gasto, links publicados
  postura.md                           ← interrogatorio de IDEOLOGIA.md §2
  guion.md                             ← guion del largo (A:/V:)
  direccion.py                         ← dirección de actor por línea
  fuentes/                             ← transcripciones + <tema>_referencia.md
  arte/
    props.py                           ← props del episodio (importa el props.py compartido)
    mapa.py                            ← hoja de mapa del episodio
    assets/                            ← mapa_*.png, mapa_pts.json, hero/, sets/
  audio/                               ← beats de voz, .wav, .tiempos.json, mezcla, música elegida
  coreo.py                             ← coreografía del cuerpo (ex ep<NN>.py)
  eventos.json                         ← efectos para la mezcla
  _frames/                             ← frames del render (privado: ya no se pisan entre producciones)
  salida/
    cuerpo.mp4  final.mp4  SUBIR_1440p.mp4  _720p.mp4  _540p.mp4
    _hoja.jpg  _uniones.jpg            ← chequeos visuales
  publicar/
    SUBIR.md  miniatura_A/B/C.png  sourcesheet.md
  shorts/                              ← los 3-5 shorts de ESTE episodio
    guion.md                           ← GUION EXCLUSIVO, no es un recorte del largo
    shorts.json                        ← ficha de cada short (gancho, título, desc, orden)
    coreo.py                           ← coreografía vertical
    audio/  _frames/
    salida/  01_*.mp4 … + _up/ + PUBLICAR.md + PLAN_SUBIDA.json
  _log/                                ← *.sh, *.log de renders desprendidos
```

Una **serie de shorts** (`videos/S<NN>_<tema>/`) es el mismo árbol **sin** `guion.md`, `coreo.py`, `eventos.json`,
`salida/` ni `publicar/` del largo: `postura.md`, `fuentes/` y `arte/` quedan en la raíz porque son de la producción
entera, y cada pieza tiene su subcarpeta numerada dentro de `shorts/` con su guion, su voz, su coreografía y sus
frames propios.

---

## 3. Lo que NO va adentro (y por qué)

"Todo lo referente a un video" es lo que **cambia por video**. Lo que es del canal se comparte, porque duplicarlo
significa arreglar el mismo bug cinco veces y varios GB repetidos en disco:

| Compartido | Dónde sigue | Motivo |
|---|---|---|
| Motor de animación | `produccion/motor.py` | un solo motor; un fix vale para todos |
| Props base (49 objetos) | `produccion/props.py` | los `props<NN>.py` lo importan |
| Generador de shorts | `produccion/shorts.py` | herramienta, no contenido |
| Entrega / intro / outro | `produccion/entregar.py`, `intro_outro.py`, `intro_canal.mp4`, `outro_canal.mp4` | son la marca |
| Texturas | `produccion/assets/madera_*.png`, `papel_*.png` | idénticas siempre |
| Elenco (rigs de papel) | `pruebas/elenco/rig/<nombre>/` | se acumulan: el ep. 5 usa los rigs del 1 al 4 |
| Música | `produccion/musica/cue_*.mp3`, `tema_canal.mp3` | las cues se reutilizan entre episodios |
| Voz (herramientas) | `voz/dirigir.py`, `alinear.py`, `voz_fal.py` | herramienta |
| Documentos del canal | `canal/*.md`, `ESTILO.md`, `ANIMACION.md`, `COSTOS.md` | son del canal |

Regla corta: **contenido adentro, herramienta afuera.** Si al borrar la carpeta de la producción se pierde algo que
otro video necesita, ese algo estaba mal ubicado.

Todo lo compartido de esta tabla que **costó créditos** (rigs, cues, sets, hero) está indexado en
`canal/INDICE_ASSETS.md`, y **antes de generar nada nuevo hay que buscar ahí** (`canal/ASSETS.md`). Un asset que nació
dentro de una producción y sirve para todas se **promueve** a compartido: se mueve a la carpeta común y se anota en
`canal/assets_catalogo.json`. Es la única razón legítima para sacar algo de la carpeta de una producción.

---

## 4. Qué hay que tocar en el código (una sola vez)

1. **`motor.py:427`** — hoy hace `rmtree(produccion/_frames)` al arrancar el render. Es la razón de que **no se pueda
   renderizar dos cosas a la vez**. Pasa a aceptar el directorio de salida (`Scene.render(..., frames=<dir>)`), y cada
   producción usa el suyo. Con esto, el largo y sus shorts pueden renderizar en paralelo.
2. **Bootstrap de imports** — `coreo.py` vive en `videos/<dir>/` pero importa `motor`, `props`, `shorts`. Cada
   producción arranca con tres líneas que meten `produccion/` en `sys.path`. Sin esto no anda ningún script movido.
3. **`shorts.py`** — hoy lee `guiones/<ep>/shorts.json` y escribe en `produccion/shorts/<ep>/`. Pasa a trabajar
   contra `videos/<dir>/shorts/`, y gana el modo nuevo (`--de-coreo`) además del viejo (`--de-master`).
4. **`entregar.py`, `checklist.py`, `dirigir.py`, `alinear.py`** — reciben rutas, no las arman. Cambio chico.
5. **Skill `youtube-shorts-upload`** — apunta a `produccion/shorts/<ep>/`: hay que actualizar la ruta.

---

## 5. Cuándo entra en vigor

- **Ep. 4 (Malvinas), en producción ahora mismo en otra sesión: no se mueve nada.** Todo `produccion/*.py` se importa
  por nombre plano y todo cuelga de `produccion/`; mover archivos con una sesión trabajando (y posiblemente
  renderizando) rompe imports y puede tirar un render de 45 minutos. El ep. 4 termina donde está.
- **Sus shorts sí nacen con el modelo nuevo**: 3-5 con guion exclusivo, en `videos/04_malvinas/shorts/`.
- **Desde la producción siguiente**, todo nuevo nace en `videos/<dir>/`.
- **Eps. 1-3 se migran en frío** (sin nada corriendo), moviendo archivos y dejando el `produccion/` viejo vacío de
  contenido. Es un rato de trabajo y no urge: son videos ya entregados.

---

## 6. Cómo se ve hoy (el problema que esto arregla)

Lo de un episodio está repartido en seis lugares distintos: `guiones/03_kiev_belarus/` (guion, postura, shorts.json),
`produccion/ep03.py` + `props03.py` + `mapa_kiev.py` + `eventos_03.json` (sueltos entre los de los otros episodios),
`produccion/assets/mapa03_*` (mezclados con los del 1 y el 2), `produccion/audio/03_*` (mezclados), `produccion/*.mp4`
(23 masters de tres episodios en la misma carpeta), `produccion/shorts/03_kiev_belarus/`, `canal/SUBIR_03.md`,
`fuentes/kiev_referencia.md`. Más ~90 archivos `_*` de trabajo (logs, hojas de contacto, tramos) sin dueño.

Con la estructura nueva: `videos/03_kiev_belarus/` y se acabó.
