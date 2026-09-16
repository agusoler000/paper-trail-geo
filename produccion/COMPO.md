# COMPO — el compositor declarativo (motor v4)

> `produccion/compo.py`. Convierte un guion ANOTADO en una coreografía completa y **correcta por
> construcción**. Lo que antes eran 500-1000 líneas de partitura a mano por pieza son ahora 12-25
> líneas `V:`. Lo que el motor v4 garantiza (nada cortado, nada vacío, puntos exactos) sigue igual;
> lo que **esto** garantiza es la composición: jerarquía, legibilidad a 405 px y una imagen por frase.
>
> Regla de oro: **si un cuadro sale mal, es un bug del compositor, no del guion.** Se arregla acá.

```
python produccion/compo.py <dir>  --pieza 4                       # check (aborta si falla)
python produccion/compo.py <dir>  --pieza 4 --hoja                # 16 cuadros reales + vista 405 px
python produccion/compo.py <dir>  --pieza 4 --sync                # sync.py sobre la escena
python produccion/compo.py <dir>  --pieza 4 --render              # cuerpo.mp4 (check primero)
python produccion/compo.py <dir>  --beat 4 --formato horizontal   # un beat de un episodio, 16:9
```
Opciones: `--guion` `--tiempos` `--mundo` `--serie 4/4` `--out` `--salida` `--dur` `--forzar`.

```python
import compo
sc, info = compo.build('guion_v.md', 'audio/tiempos.json', 'audio/_palabras.json',
                       formato='vertical', mundos='mundo.json', serie=(4, 4), beat=None)
compo.check(sc, info)          # aborta con la lista de reglas rotas
compo.hoja(sc, info); compo.auditar(sc, info)
```

---

## 1. Lo único que se escribe: el guion anotado

Una línea `V:` por línea `A:` (pueden ser varias `V:` seguidas; se concatenan). Los verbos se separan
con `·`. Cada verbo puede anclarse a una palabra real de la voz con `@ "palabra"` y un desfase
opcional `+0.30` / `-0.20`; **sin `@` entra al empezar la línea**.

```
A: On the twenty-ninth of June, a Spanish court published a ruling. Thirty-two days later, forty-nine thousand people crossed into Ceuta in twenty-four hours.
V: MAPA(Ceuta, abrir) · DOC(sentencia, "29 · VI · 2026") @ "published" · MAPA(Ceuta, cerrar) @ "forty-nine" · CIFRA(49,000, "IN 24 HOURS") @ "forty-nine" +0.30
```

El instante sale de **la palabra, no del orden de escritura**: dos verbos anclados a la misma palabra
se separan 0,25 s en el orden en que están escritos, y nada más. `@ "palabra"` se busca en
`_palabras.json` dentro de la línea y hasta 4 s después; si no está, el objeto entra al empezar la
línea y **se avisa** (mirá la transcripción: puede estar escrita en cifras — «1 . 13 trillion»).

Cabecera opcional, cada una en su línea:

| Línea | Para qué |
|---|---|
| `SERIE 4/4` | chip `PART n OF N` + barra de progreso |
| `RESALTAR a, b` | palabras extra en rojo en el subtítulo (las cifras, los sitios y los nombres propios ya van solos) |
| `TEXTO_OK firme, day` | la **única** salida de la regla TEXTO_NO_DICHO, y a la vista |
| ` ```mundo {json} ``` ` | el mundo dentro del guion (si no, `mundo.json` al lado) |
| `**Gancho ... (la 2 en rojo):**` + bloque ``` | la tarjeta de gancho de un short (3,5 s) |
| `## BEAT 4 · TÍTULO` | separa beats en un episodio; el título va de rótulo |

**Sin `V:`** el compositor pone una `TARJETA` con las 2-4 palabras clave de la línea (mayúsculas,
cifras, sitios) y avisa. Ninguna línea queda sin imagen que diga lo que dice la voz.

### `mundo.json` (una vez por producción)

```json
{"nombre": "estrecho_c", "bbox": [-5.95, -4.85, 35.40, 36.45], "w": 2600,
 "out_dir": "../../_compo_test/assets", "etiquetas": false,
 "sitios": {"Ceuta": [-5.3213, 35.8894], "Fnideq": [-5.3567, 35.8500]},
 "puntos": {"valla": [-5.3460, 35.8770], "jurista": [-5.5020, 36.1760]},
 "agua": [["STRAIT OF GIBRALTAR", -5.63, 36.02, 54]],
 "rotulos_extra": [["SPAIN", -5.55, 36.30, 84]],
 "capas": {"esp": [["ESP"], "institucion", 210], "mar": [["MAR"], "acreedor", 205]},
 "capas_geojson": {"ceuta": ["fuentes/mapas/ne_10m_ceuta_melilla.geojson", ["Ceuta"], "institucion"]},
 "encima": {"mar": ["ceuta"]},
 "pins": {"Ceuta": {"color": "ocre", "r": 14, "size": 46, "off": [2.0, -0.3]}},
 "escritorio": [["lupa", 0.130, 0.820, 0.078], ["moneda", 0.888, 0.848, 0.042]]}
```

- `sitios` = puntos rotulados (pin + etiqueta). `puntos` = anclas sin rotular (el extremo de una
  valla, los saltos de una ruta, dónde se para un rig). **Todo sale de lon/lat** (regla 24) y
  `mapa_v2.mundo` aborta si un sitio cae a más de 3 px de su proyección.
- `capas` = el color que **narra**: no se hornea, se enciende con `PINTA` cuando la voz lo nombra.
  `encima` pinta un enclave DESPUÉS del país que se lo come (Ceuta sobre Marruecos).
- **Los pines van en ocre**, no en rojo: el rojo es de los datos (ver regla d).
- El bbox tiene que ser **más alto que ancho** en vertical, y con **≥ 35 % de tierra** (si no, avisa).

---

## 2. La rejilla

El compositor **no** usa cajas fijas: calcula el hueco libre real contra lo que ya está vivo. Lo que
sí es fijo son los límites y las bandas preferidas.

```
 VERTICAL 1080x1920                        HORIZONTAL 1920x1080
 ┌───────────────────────────┐ 0.00        ┌───────────────────────────────────────┐ 0.00
 │ chip        [ ROTULO ]    │ .05-.09     │        [ ROTULO ]  .06-.10            │
 ├───────────────────────────┤ .095 ─┐     ├───────────────────────────────────────┤ .105 ┐
 │                           │       │     │            │             │            │      │
 │   ░ banda ALTO  fy .232 ░ │ .14-.34     │  [ IZQ ]   │   rig /     │  [ DER ]   │ .33  │ franja
 │                           │       │     │  fx .230   │   objeto    │  fx .770   │      │ legible
 │  ░ tercios izq/centro/der │ .34-.62  franja │        │             │            │      │
 │      objetos y rigs       │       │ legible│  cifra arriba · tarjeta abajo      │ .69  │
 │   ░ banda BAJO  fy .672 ░ │ .55-.81     │            │             │            │      │
 ├───────────────────────────┤ .830 ─┘     ├───────────────────────────────────────┤ .845 ┘
 │ ▓▓▓ SUBTITULO  fy .885 ▓▓ │             │ ▓▓▓▓▓ SUBTITULO  fy .905 ▓▓▓▓▓        │
 │ ─── barra de progreso ─── │ 1.00        │ ─────── barra de progreso ─────────── │ 1.00
 └───────────────────────────┘             └───────────────────────────────────────┘
```

Cómo elige el hueco, en este orden:

1. **Columna** (solo en 16:9): el lado CONTRARIO de lo que se está mirando — el personaje si hay uno
   vivo (manda, ocupa el centro), si no el sitio del que habla la línea.
2. **Banda**: se recorre la franja legible de 8 en 8 milésimas y gana la posición con menos solape
   contra lo vivo (otro texto, el documento, el rig, **el pin y el rótulo del sitio nombrado**),
   desempatando por cercanía a la banda preferida (arriba si el sitio está abajo, y al revés).
3. Si no hay ninguna posición limpia, se achica la letra hasta el mínimo y, si aun así no hay, se
   pone **donde menos estorba** y se avisa con el porcentaje.
4. **Relevo**: un objeto nuevo apaga al anterior de su familia (`cifra` · `texto` · `objeto`) con
   0,25 s de fundido, terminando justo cuando el nuevo empieza a entrar: **nunca coinciden**.
5. **Vida**: hasta que otro ocupe su slot, o hasta el fin de la línea siguiente, con techo de 3 s
   después de su propia línea y 9 s en total; mínimo 2,2 s. El último objeto se queda hasta el final.

Máximo simultáneo: **1 CIFRA + 1 TARJETA + 1 objeto/rig + subtítulo** (el rótulo no cuenta).

---

## 3. El vocabulario (12 verbos)

| Verbo | Qué hace · defaults |
|---|---|
| `MAPA(sitio, abrir\|medio\|cerrar)` | corte + UN viaje hacia el sitio. `abrir` ≈ ver el mundo entero, `medio` 1,0-1,3, `cerrar` 1,85-2,4 (escalado al formato). El recorrido es del 30 % de la ventana y el sentido alterna. Sin argumentos: cambia de escenario a mapa. |
| `MESA` | cambia de escenario a mesa sin documento (el mundo se oscurece). |
| `PINTA(ISO\|alias)` | enciende la capa de país en ese instante (1,3 s de fundido) y, detrás, sus enclaves y las marcas. |
| `RUTA(a, b, c, …)` | ruta que se dibuja entre sitios o `puntos`; **roja mientras se dibuja, ocre después**. Comprueba sobre el PNG que el tramo de en medio va por agua dibujada. `hasta=` para que desaparezca. |
| `CIFRA(valor, "pie")` | el objeto grande del beat: cuerpo ≥ 8 % del alto, entra con flipin y sello. Roja si le toca el rojo del cuadro. El `pie` va pegado debajo, en tinta. |
| `TARJETA("texto")` | tarjeta de papel, cuerpo ≥ 4,2 %, ≤ 4 palabras por línea y ≤ 2 líneas (`\|` parte la línea). `color=rojo` la pide roja. |
| `SELLO("texto"\|prop)` | sello que cae con sacudida de cámara. Con texto, el compositor elige el color; con un prop, usa el PNG. |
| `DOC(prop, "TÍTULO REAL")` | plano de MESA: mundo a `dark` 0,58 + el documento grande (50 % del alto) + 2-3 props de escritorio de fondo. **Nunca una hoja rayada.** El título es obligatorio y no puede ser `REPORT`/`DECREE` a secas. |
| `PROP(nombre, sobre=sitio)` | prop anclado al MAPA (px de mundo), con la escala compensando el zoom para que siempre mida el 46 % del ancho. `sobre=izq\|centro\|der` lo pone en pantalla. `escala=` lo ajusta. |
| `PERSONAJE(rig, sobre=sitio, senala=sitio)` | rig **de pie sobre el mapa**, con peana y sombra de contacto, gesto por frase y `point_at` real. El compositor le reserva la cámara (misma clase y mismo sitio) ≥ 6 s, lo achica si no entra y lo apoya en tierra. `alto=` cambia su altura. |
| `SECUENCIA(base, n, de="pal", a="pal")` | cuadros pregenerados (`barra_d00..12`) entre dos palabras, todos a la misma escala. |
| `ROTULO("texto")` | el rótulo corto de arriba. No cuenta como contenido (`sync` lo ignora a propósito). |

Ejemplo de cada uno, tal como están en producción:

```
MAPA(Ceuta, cerrar) @ "fence"                      PINTA(ESP) @ "Spain"
MESA                                               RUTA(Fnideq, ag1, ag2, ag3, Ceuta) @ "went"
CIFRA(+2,400%, "CAPACITY EXCEEDED") @ "exceeded"   TARJETA("OPEN WATER|AT BOTH ENDS") @ "water"
SELLO("141 DIED") @ "forty-one"                    DOC(sentencia, "TRIBUNAL SUPREMO")
PROP(cerca, sobre=valla) @ "fence"                 ROTULO("THE SUPREME COURT")
PERSONAJE(05_jurista, sobre=jurista, senala=Ceuta) @ "narrower" +0.30
SECUENCIA(barra_d, 13, de="fell", a="percent")
```

Automático, no se escribe: subtítulo palabra a palabra con las cifras y los nombres propios en rojo,
rótulo del beat en un episodio, gancho, chip `PART n OF N` y barra de progreso.

---

## 4. Las reglas que verifica `compo.check` (aborta si falla)

| | Regla | Qué mide |
|---|---|---|
| regla 1 | Nada cortado | `Scene.check_framing` sobre toda la pieza |
| a | Solape | dos elementos no-bg pisándose más del 8 % del menor, muestreado cada 0,2 s |
| b | Texto sobre el sitio | un cartel encima del pin o del rótulo del sitio que nombra la línea (> 30 % de su caja) |
| c | Tamaños | cifra ≥ 8 % del alto · tarjeta ≥ 4,2 % · rótulo ≥ 2,6 % · ≤ 4 palabras por línea y ≤ 2 líneas · prop ≥ 14 % del ancho · rig ≥ 26 % del alto (42 % en 16:9) |
| d | Un rojo por cuadro | sobre el render a 405 px: píxeles `r>170, g<90, b<80`, dilatados y agrupados **por elemento**. Cuentan las manchas de un objeto como una; **no** cuenta el subtítulo (su resalte es parte del subtítulo) ni un territorio pintado de rojo (> 8 % del cuadro: es el suelo narrando, no un punto de atención) |
| e | Densidad | más de 4 elementos no-bg a la vez |
| f | Plano largo | un plano de más de 5 s sin corte y sin que entre nada |
| g | Pantalla vacía | una línea con más de 0,8 s sin un solo elemento de contenido sobre el mapa |
| h | **TEXTO_NO_DICHO** | toda palabra y toda cifra que se ve —tarjetas, sellos y **el texto horneado en los props**— tiene que estar dicha en la línea, en el beat o en `fuentes/referencia.md`. Los props declaran su texto en `TEXTOS_PROPS` o en un `prop_<n>.txt` al lado del PNG; un prop sin declarar también falla |
| i | **TIERRA_EN_CUADRO** | un plano de mapa con menos del 40 % de tierra (o de tierra + contenido) en la ventana |
| j | **PERSONAJE visible** | un rig que no está entero dentro de la ventana 6 s seguidos, o que está de pie sobre el agua |

Salida: la lista con tiempo, regla y línea, más `_qc/compo.md` (fallos + avisos + planos + objetos).

## 5. Lo que el compositor corrige solo (y escribe en los avisos)

MESA que cae dentro del gancho → se corre detrás de los 3,5 s · corte que no se leería como corte →
se separa el zoom (o el encuadre, si hay un personaje) · plano de mapa con poca tierra → se corre el
centro · rig que no entra → se achica, y si se lo corre se lo vuelve a apoyar en tierra · rig cuya
cámara se iba → se le reserva clase y sitio · dos rojos → el de menor prioridad baja a tinta/ocre
(CIFRA > RUTA > SELLO > TARJETA) · hueco sin contenido → estira el último objeto hasta que entra el
siguiente · texto que acabaría sobre el pin → se acorta antes.

Cuando no puede arreglarlo sin romper otra regla **lo dice con nombre y tiempo** («hace falta un
verbo más en esa línea»), y `check` marca el fallo.

## 6. Un short y un episodio

- **Short**: `videos/<serie>/shorts/<n>/` con `guion_v.md` + `mundo.json` + `audio/`.
  `--pieza N` resuelve la carpeta. Formato vertical, `SERIE n/N` en la cabecera, gancho en el guion.
  Referencia completa: `videos/S12_recibos/shorts/04_ceuta/guion_v.md` (12 líneas `V:` para 73 s).
- **Episodio**: `videos/<NN_tema>/guion_v.md` + `mundo.json` + `audio/tiempos.json` con `b` por beat.
  Se compone **un beat por vez** (`--beat 4 --formato horizontal`), y el título del `## BEAT` va de
  rótulo. Referencia: `videos/09_deuda_eeuu/guion_v.md`.

## 7. Límites conocidos

- Una `Scene` tiene UN mundo: un beat que cambia de mapa son dos construcciones.
- `sync.magnitudes` no entiende «eight and a half trillion» (da 8, no 8,5): `CIFRA($8.5T)` sale
  marcada como CIFRA_SIN_PANTALLA aunque esté bien. La regla h sí la valida contra las fuentes.
- `PROP_HUERFANO` de `sync.py` compara el nombre del objeto con el texto de la línea, así que un
  prop en castellano (`doc:sentencia`) sobre un guion en inglés siempre sale marcado. Es un aviso.
- Los rótulos del mundo están horneados: en un plano muy cerrado se agrandan y pueden salirse por el
  borde. Se controla con el tamaño en `agua`/`rotulos_extra`, medido contra la ventana.
- Un `PERSONAJE` le reserva la cámara 6 s: si la anotación pide otro sitio antes, la reserva se corta
  ahí y `check` marca el rig corto en vez de decidir por el guion.
