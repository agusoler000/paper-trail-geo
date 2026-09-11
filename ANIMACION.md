# SISTEMA DE ANIMACIÓN — canal de geopolítica

> Ley de producción. Todo plano animado sale de acá.
> Creado: 2026-08-31. Motor verificado empíricamente el mismo día (render real, no documentación).
> Dirección de arte y narrativa: `ESTILO.md`.

---

## 0. La conclusión que ordena todo

**La IA de video no puede ser el motor del canal.** La aritmética lo cierra sin discusión, verificada
en vivo contra la API con `picsart_preflight` (dry-run, no cobra):

| Modelo | Costo real medido |
|---|---|
| Hailuo 2.3 Fast (i2v, 720p) | 6 cr / 6 s · 10 cr / 10 s → **1 crédito = 1 segundo** |
| Seedance 2.0 Fast (480p, 4 s, sin audio) | 8 cr → 2 cr/s, **pero acepta `startFrame` + `endFrame`** |
| Kling V3 Turbo | 20 cr |
| Grok Imagine 1.0 / LTX 2.3 Fast | 12 cr |

500 créditos/mes = **500 segundos = 8 min 20 s de video generado**, asumiendo que toda toma sale
perfecta a la primera. Con una tasa realista de 3-4 intentos por toma usable en estilo cartoon
consistente, quedan **2-3 minutos usables al mes**. No es un problema de elegir mejor modelo: es un
déficit de un orden de magnitud.

**Trampas confirmadas del proveedor:**
- Los créditos **no se acumulan** y el ciclo **no es el mes calendario**: el reset real de esta cuenta
  es el **día 14**. Hoy hay 366 créditos que se evaporan el 14/09 si no se usan.
- `hailuo-2.3-fast` **no hace texto-a-video**: exige imagen de inicio. Cada clip consume además un
  frame de SDXL.
- Los Terms de PicsArt **no dicen nada explícito sobre derechos comerciales del output de IA**.
  Hueco legal real sobre el único insumo pago del proyecto — verificarlo antes del primer sponsor.

### 0.1 Reparto de la cuota con el otro canal (decidido 2026-08-31 — DEROGADO 2026-09-07)

> **Decisión de Agustín (2026-09-07):** geopolítica es la apuesta máxima y Marlowe no tiene prioridad.
> **Los 500 créditos por ciclo son de este canal.** El presupuesto vigente está en `canal/CALENDARIO.md` §1.
> Lo que sigue queda como registro de los costos medidos, que siguen valiendo.

Los 500 créditos/mes son **una sola cuota compartida** con Marlowe's Alley (`../canal_youtube/`),
que ya presupuestó 384 cr/mes y tiene prioridad declarada.

Costos reales medidos con `picsart_preflight` (dry-run, no cobra):

| Pieza | Costo |
|---|---|
| **MP Scene** (compositor: anima y renderiza) | **0** |
| **Remove Background** (`picsart-sod-v8-2`) | **0** — ilimitado |
| SDXL local en la 3070 · formas vectoriales nativas | 0 |
| Recraft Vectorize (raster→SVG) | 1 |
| Recraft V4.1 Vector (SVG nativo) | 3 |
| Video generativo (Hailuo, Seedance…) | 1-2 **por segundo** |

**Reparto:** geopolítica corre a **0 cr/mes de base** (vector puro + SDXL local + recortes gratis),
con un techo de reserva de 40 cr/mes. Marlowe conserva los 500. Geopolítica **no compite por dinero
con el otro canal — compite por tiempo del operador.**

**Regla del día 14.** Los créditos no se acumulan y el ciclo no es el mes calendario: el reset real
es el **14**. Eso abre una ventana programada: **del 7 al 13, lo que Marlowe no gastó lo quema
geopolítica** — y solo en **ciclos reutilizables** (una caminata, un gesto de entrega, un
asentimiento), nunca en planos de un solo uso. Gastar por activo y no por plano es lo que hace que
40 créditos rindan como 400.

---

## 1. El motor: MP Scene (compositor JSON de PicsArt)

Nueve frentes de investigación recomendaron construir un motor de rig cutout desde cero (Remotion) o
aprender uno (Blender Grease Pencil). Ninguno revisó que **la cuenta ya incluye uno**.

MP Scene no es un compositor de slideshow: es un **motor de animación vectorial clase After Effects,
nativo en JSON**, que renderiza **gratis** hasta 1920 px.

**Verificado interrogando el schema y renderizando de verdad:**

| Capacidad | Estado |
|---|---|
| Shape layers vectoriales nativas (rect, ellipse, polystar, path, gradientes, merge, repeater) | ✅ |
| `trim` de trazo animable → **la línea que se dibuja sola** (rutas, fronteras) | ✅ |
| Grupos **anidados recursivamente**, cada uno con `anchor`/`rotation`/`scale`/`opacity`/`skew` propios y animables | ✅ **← el hallazgo clave** |
| Expresiones **Lua por frame** (`time`, `value`, `ctx:loopOut()`, `math.*`, `Vec.v2`) | ✅ |
| Easing incl. `cubic_bezier`, motion blur por capa, cámara, máscaras, blend modes, adjustment layers | ✅ |
| Ingesta de SVG y Lottie como assets | ✅ |
| Límites | 1920 px/lado · 100 capas · 20 pistas de audio · 3600 s |
| **Costo de render** | **0 créditos** — verificado: 366 antes y 366 después de exportar un MP4 1080p de 7 s |

**Por qué los grupos anidados lo cambian todo.** El verificador adversarial reportó "no hay parenting
entre capas: si rotás el hombro, el antebrazo no lo sigue". Es cierto **a nivel de capa** y falso a
nivel de grupo: un grupo lleva su propia transformada y contiene hijos, así que
`brazo > antebrazo > mano` es **cinemática directa nativa**. Dos consecuencias:

1. No hay que calcular FK en el generador.
2. **Un personaje entero = 1 capa**, no 8-15. El techo de 100 capas deja de ser una restricción real.

---

## 2. Reglas del motor (obtenidas a la mala — respetarlas al pie de la letra)

> El motor tiene un modo de falla feo: **hay documentos que validan sin una sola advertencia, pasan la
> consulta de layout, y renderizan la capa entera en blanco, sin error**. Estas reglas son el resultado
> de aislar esos casos uno por uno. Es también la razón por la que el generador debe mantener una
> representación intermedia propia (§5).

| ✅ Hacer | ❌ Nunca |
|---|---|
| **Traslación** con `layer.animations.position` (keyframes vec2) | **`group.position` distinto de `[0,0]`** — valida, consulta bien, y **renderiza en blanco toda la capa** |
| **Colocación** con `layer.transform.position` (píxeles de composición) | Animar `anchor` (no es expresable; V3 pivota sobre el centro) |
| **Articulación** con `group.rotation` (keyframes o expresión) | Morph de paths (`path` y rampas de gradiente son **hold-only**, nunca interpolan) |
| **Pivote** con `group.anchor` estático en la junta | Expresión sin `return` — es error de sintaxis y **blanquea el frame entero** |
| Un elemento pintado = **un grupo propio** (scope de pintado aislado) | Mezclar geometrías y pinturas en un mismo scope sin querer |

### 2.1 Escala: la geometría va en píxeles de composición, 1 a 1 (corregido 2026-09-02)

> **La "regla del 640" documentada el 2026-08-31 era falsa.** Toda la geometría de un shape layer
> (`size`, `position` de items, `roundness`, `anchor`, `width` de trazos) se autoría en **píxeles de
> composición**, igual que las posiciones de capa. Verificado con `picsart_media_query_layout`
> (reporta las cajas 1:1) y con un export real a 1080p.

**De dónde salió el error.** `picsart_media_contact_sheet` con una `resolution` reducida (480 o 640
de ancho) **no escala la geometría de las formas**, solo las posiciones de capa. Por eso en una
miniatura de 640 una comp de 960 parecía 1,5× y una de 1920 parecía 3×. El demo original se
"corrigió" dividiendo por 3 y el MP4 salió con todo a un tercio del tamaño: personajes de 40 px.

**Regla operativa:** para previsualizar, pedir la hoja de contacto **a la resolución de la
composición** (`resolution: {width: 1920, height: 1080}`), o fiarse de `query_layout`. Nunca
calibrar tamaños contra una miniatura reducida.

### 2.2 Orden de pintado

- **Array de `layers`**: de atrás hacia adelante (el último está encima).
- **`contents` de un grupo**: al revés — **índice 0 está encima**.
- Dentro de un scope el renderer camina hacia adelante: la geometría **se acumula** y `fill`/`stroke`
  dibujan lo acumulado hasta ese punto. Por eso `[ellipse, trim, stroke]` es correcto para media
  circunferencia y `[ellipse, stroke, trim]` no lo es.

---

## 2.3 Rig de imagen (recorte de papel real) — aprendido el 2026-09-02

El look aprobado usa **personajes generados como imagen** (Flux 2 Pro, 1 cr) y no formas vectoriales.
Eso cambia el rig: las piezas son capas `media` con `asset: {type:"image", uri, width, height}`
(el campo es **`uri`, no `url`**) y `bounds` en píxeles de composición.

| Regla | Detalle |
|---|---|
| **Sin parenting entre capas** | La cinemática se calcula en Python y se **hornea por frame** (posición + rotación, 30 kf/s). `escena_burocrata.py` rota cada pieza alrededor de su junta real (el remache) y emite la posición del centro resultante. |
| **`motionBlur: true` hace desaparecer la capa** cuando se mueve rápido | Verificado: personaje entero invisible durante la entrada, cabeza invisible durante el asentimiento. **Siempre `motionBlur: false`** en capas media animadas. |
| Hosting de piezas | Presigned URL de Higgsfield (`media_upload` → PUT → CloudFront público). **CloudFront cachea por clave**: cada versión de un archivo va a una clave nueva, nunca se re-sube a la misma. |
| Escena por URL | Con keyframes por frame el JSON pesa ~100 KB; se sube y se pasa la URL a validate/contact_sheet/export en vez de pegarlo inline. |
| **El hueco bajo el brazo** | Al recortar un brazo que cruza el pecho queda un hueco en el torso. Parche plano/espejado se nota. **Solución real: generar cada personaje de la biblioteca con los brazos separados del cuerpo** (hoja de piezas), no recortar de una pose cerrada. Qwen image-edit (4 cr) para quitar el brazo NO sirvió: inventó otro brazo y re-encuadró. |

Prueba: `pruebas/look/burocrata_anim_v4.mp4` (7 s, 0 créditos de render). Scripts y piezas en `pruebas/look/rig/`.

## 3. La prueba (`pruebas/`)

`pruebas/build_demo.py` → `pruebas/demo_mesa_de_mapas.json` → `pruebas/demo_mesa_de_mapas_v2.mp4`

> `demo_mesa_de_mapas.mp4` (v1) es el render roto a 1/3 de escala; se conserva solo como evidencia.

7 segundos, 1920×1080, 30 fps, **0 créditos**, sin una sola imagen generada ni un solo modelo de
difusión. Lo que demuestra:

- Brazo de **dos segmentos** que articula desde hombro y codo, con **anticipación** (baja antes de
  subir) y ease de golpe.
- **Segundo personaje que entra en cuadro** deslizándose y frena con rebote.
- **Ficha que se desliza por la mesa y se vuelca**, con rebote de asentamiento.
- **Respiración procedural** — una línea de Lua, cero keyframes:
  `return value * (1 + 0.02 * math.sin(2*math.pi*time/2.6))`
- Motion blur por capa.

El diseño es tosco a propósito: son ~60 líneas de Python. Lo que se estaba probando es el
**movimiento**, no el dibujo.

**Pendiente de resolver en el demo:** el `trim` de la ruta marítima no se ve en el render pese a
validar. Probablemente `start`/`end` no estén en escala 0-100. Revisar antes de usar rutas animadas
en producción.

---

## 4. La pirámide de planos

```
¿El plano necesita un personaje ACTUANDO (gesticula, señala, entrega, entra)?
├── SÍ ──> ¿es el cold open o el giro del episodio?
│          ├── SÍ ──> CAPA D · hero shot (créditos)
│          └── NO ──> CAPA A · rig cutout en MP Scene   [costo 0]
└── NO ──> ¿hay mapa, objeto o dato que se transforma?
           ├── SÍ ──> CAPA B · mundo animado sin personaje  [costo 0]
           └── NO ──> CAPA C · tipografía y datos en movimiento  [costo 0]
```

Presupuesto por video de 7-8 min (ver `ESTILO.md` §6): **A = 90-120 s · B ≈ 180 s · C ≈ 90 s ·
D = 12-20 s**.

### Capa D — cómo gastar los créditos bien

No en i2v libre. **En interpolación**, que es un problema mucho más fácil y por lo tanto con muchísimo
menos descarte:

1. Generá **pose A** y **pose B** gratis con SDXL local (mismo seed, mismo character sheet).
2. Pasálas como `startFrame` + `endFrame` a **`seedance-2.0-fast`** (2 cr/s a 480p).
   El modelo no inventa el personaje: lo interpola. Es un ToonCrafter hospedado.
3. `returnLastFrame: true` devuelve el último cuadro para usarlo como `startFrame` del siguiente clip
   → encadena planos manteniendo identidad.

**Y la jugada de verdad: no gastes créditos por plano, gastalos por ACTIVO.** Un ciclo de caminata o
un gesto generado una vez se reusa en los 52 videos del año. Presupuestá ~10-15 clips cortos (2-4 s)
por mes, y que la mitad sean ciclos reutilizables, no planos de un solo uso.

**Sin probar todavía, y vale una tarde:** `kling-motion-control-v3` mapea el movimiento de un video de
referencia sobre una figura. Filmarte gesticulando con el celular una tarde y construir una biblioteca
de 20-30 movimientos sería captura de performance sin traje ni software. El schema dice
`Person Photo (upper body)`, así que puede no funcionar sobre dibujo plano. Probarlo con 1 clip antes
de planificar nada encima.

---

## 4.1 Descubrimiento del 2026-09-03: hay un render local a 0 créditos

`pruebas/elenco/animar.py --local` compone las piezas con PIL y arma el MP4 con ffmpeg en ~2 min por
clip de 7 s a 1080p, sin subir nada y sin créditos. El render de MP Scene con la misma escena horneada
sale **idéntico**. Consecuencia: MP Scene deja de ser obligatorio para los planos de personaje; queda como
opción para lo que PIL no hace bien (motion blur real, máscaras, cámara, Lottie). La previsualización y
la iteración van siempre por el backend local.

## 5. Arquitectura del generador

```
guion.yaml  (columna AUDIO + columna VIDEO, una fila por beat)
    │
    ├─> voz.py      Kokoro/Chatterbox ──> WAV + faster-whisper (timings por palabra)
    │
    └─> escena.py   IR propia ──[backend]──> JSON de MP Scene ──> export ──> MP4
                        │
                        └─ backend alternativo: Remotion (escape hatch, §6)
```

**Regla de arquitectura no negociable:** la lógica de animación vive en una **representación
intermedia propia** (personajes, poses, tiempos, geometría), y el emisor de JSON de MP Scene es un
**backend intercambiable**. Motivos concretos: (a) MP Scene es un servicio propietario atado a la
cuota de PicsArt — si cambian los límites de render gratis, se pierde el motor de un día para el otro;
(b) el motor tiene fallos de render silenciosos (§2). La biblioteca de videos no puede depender de eso.

**Reparto entre máquinas:**
- **Laptop** (Core Ultra 7, iGPU Arc, 32 GB): n8n, generador de escenas, Rhubarb, ffmpeg. Todo CPU.
- **Fábrica** (RTX 3070, 16 GB RAM): ComfyUI/SDXL para piezas de arte. Nada más.

> ⚠️ **La 3070 no sirve para video generativo local, y el límite no es la VRAM: son los 16 GB de RAM
> del sistema.** `mmgp` —el gestor de memoria de Wan2GP, el proyecto "para el GPU poor"— documenta
> cinco perfiles y **el menos exigente pide 24 GB de RAM**. Además la 3070 es Ampere y **no tiene
> FP8**: todo benchmark de "corre en 8 GB" de 2025-2026 asume RTX 40+, y los checkpoints `_fp8_scaled`
> se dequantizan a fp16 en vuelo. Un número medido en una 4060 8 GB puede ser 2-4× optimista acá.
> Cerrar esta puerta explícitamente para que nadie la reabra: **Wan local, LTX-2 y ToonCrafter están
> fuera de alcance.**

---

## 6. Escape hatch documentado: Remotion

Si MP Scene se cae, sube de precio o sus fallos de render se vuelven insostenibles:

- **Licencia verificada en `LICENSE.md`** (no en marketing): gratis para *"an individual"*, **sin tope
  de facturación**. El disparador de licencia paga es tener 4+ empleados. Podés facturar en sponsors
  y seguir sin pagar.
- Vivísimo: v4.0.519 publicada el 31/08/2026, releases casi diarias. Tiene 12 Agent Skills oficiales,
  incluida **`/remotion-maps`** (animaciones de mapas, rutas, marcadores) — hecha para este nicho.
- **GSAP es 100 % gratis desde 2025**, MorphSVG y DrawSVG incluidos.
- Renderiza en Chrome/CPU: **no compite por la VRAM con ComfyUI**.

**Advertencias:** `@remotion/gsap` se publicó el 25/08/2026 — tenía días de vida. Remotion **no tiene
ni un solo antecedente público de animación de personajes** (su showcase es motion graphics y video de
producto), y no publica requisitos de sistema ni throughput. Antes de migrar: `npx remotion benchmark`
con una escena realista.

**Descartados con evidencia, no reabrir:** Rive (export de video recién en Voyager, 32 USD/mes) ·
Live2D Cubism FREE (export capado a 1280×720 con logo) · Cartoon Animator (149 USD y el trial
**prohíbe uso comercial**) · Adobe Character Animator (Adobe discontinuó Animate: fin de venta
01/03/2026, soporte individual hasta 01/03/2027) · Motion Canvas (un commit administrativo en
17 meses) · AnimatedDrawings (archivado 03/09/2025, **nunca probado en Windows**, y siempre tuvo un
paso manual de corrección de articulaciones por dibujo).

---

## 7. Orden de trabajo

1. ⬜ **Mirar el demo y decidir si el look cierra como identidad de marca.** Es cutout rígido tipo
   Gilliam: no hay squash-and-stretch ni deformación de malla. Si la expectativa interna de "caricatura
   animada" es más alta que eso, hay que saberlo **antes** de construir el sistema, no después.
2. ✅ Biblioteca de rigs hecha el 2026-09-03 (`pruebas/elenco/`, ver `RETOMAR.md`). Original:
   para que un solo script anime a cualquiera.
3. ⬜ `escena.py`: traductor de intenciones (`X señala el mapa`, `X entra por la derecha`,
   `la ficha se vuelca`) a keyframes. **Es la mayor inversión de tiempo del plan y la única con retorno
   compuesto.**
4. ⬜ Lip-sync por capas: faster-whisper (ya instalado) da timings por palabra → swap de la capa de
   boca. Gratis, estable, consistente. *Alternativa considerada y descartada por ahora: no animar la
   boca en absoluto — History Matters lo probó, quedaba creepy, y resolvieron con carteles. Es un tic
   de marca y elimina el problema entero.*
5. ⬜ Test de una tarde: `kling-motion-control-v3` sobre un personaje plano.
6. ⬜ Resolver el `trim` de la ruta (§3).

> **Límite duro de ingeniería:** ningún sprint de tooling puede durar más que la producción de un
> video. El modo de falla más común en este perfil es construir la fábrica perfecta durante tres meses
> y publicar cero videos. El pipeline se construye **detrás** de videos ya publicados.

## Reglas de cartel (Agustín, 2026-09-09, mirando el ep. 4)

> *"QUE NO SE QUEDEN CORTOS LOS RECUADROS Y QUE NO SE SUPERPONGAN CARTELES SALVO QUE SEA LA INTENCIÓN."*

1. **El recuadro se mide, no se estima.** `props.tab()` y los helpers `tabimg()`/`card()` tienen que calcular el
   ancho con `textbbox` sobre la fuente y el cuerpo reales, más el relleno. La cuenta vieja (`len(txt)*17+60`,
   píxeles por cantidad de letras) falla con mayúsculas anchas: en el ep. 4 se desbordaron **31 de 48** etiquetas,
   la peor por 88 px. Una "W" no mide lo mismo que una "I".
2. **Dos carteles no se pisan.** Si dos textos coinciden en pantalla y se solapan más de ~20 %, el que estaba antes
   se va cuando entra el nuevo. En el ep. 4 quedaron **40 pares** superpuestos, varios al 100 %. Va como pase
   automático al final de `build()`, igual que el post-pass de encuadre: se detecta por bbox y se apaga el más viejo.
   La excepción es el solapamiento buscado (un sello que cae ENCIMA de un papel, una pila): ahí se marca a mano.
3. Los dos chequeos se corren en `check` **antes** de renderizar, y salen en el informe junto a las violaciones de
   encuadre y el ritmo. Un cartel cortado o pisado cuesta el mismo re-render de dos horas que un objeto fuera de cuadro.

---

## Precisión geográfica (Agustín, 2026-09-09, mirando el ep. 5)

> *"cuando se señalan puntos en los mapas NO SON PRECISOS y te había dicho antes TENÍAN QUE SER 100 %
> precisos y vuelves a cometer el mismo error?"* — y el ejemplo concreto: *"en un momento dice que IRAQ
> invade KWAIT y señala Qatar y no kwait"*.

Es la regla 2 y **no se cumplía**. Eran tres fallos distintos, todos invisibles para los chequeos que había:

### a) La hoja está inclinada y `P()` no lo aplicaba — afectaba a TODOS los episodios
`MapSheet.draw()` compone la hoja rotada (`im.rotate(-self.r, expand=True)`) y recentrada, pero `P()`
devolvía el punto **como si la hoja estuviera derecha**. Todos los episodios usan la hoja con una
inclinación de 0,3° a 1°. Medido en el ep. 5 con 0,35°: hasta **4,7 px de error sobre la hoja**, que en
un plano cerrado (zoom 4,6) son **22 px en pantalla**.
**Corregido en `produccion/motor.py::MapSheet.P()`**, que ahora aplica la misma rotación que `draw()`.

### b) Lo que representa un RECORRIDO no puede tener tamaño fijo
La flecha de «Iraq invades Kuwait» medía 152 px y **Bagdad–Kuwait son 46 px**. Centrada en el punto
medio, la punta llegaba a 99 px de Bagdad, o sea **53 px más allá de Kuwait**: caía sobre Dhahran/Qatar.
**Todo lo que une dos lugares se construye desde los dos anclajes**, nunca con una escala elegida a mano:

```python
entre('flecha', t, G('Baghdad'), G('Kuwait'))   # se escala al largo real y se gira a esa dirección
perp('muro',   t, G('Baghdad'), G('Tehran'))    # atravesado, perpendicular al eje
```

### c) Lo que marca un sitio tiene un tope de tamaño MEDIDO EN GRADOS
Los props que marcaban una ciudad medían entre 8 y 19 grados de longitud. **Kuwait mide 2.** Por eso la
alfombra de La Meca tapaba media Arabia y el billete de Peshawar tapaba Pakistán.

| Qué marca | Tope | Ejemplo |
|---|---|---|
| Una ciudad | **4-6 grados** | la chincheta de Washington, el documento de Ginebra |
| Un país | **8-12 grados** | la estrella soviética sobre Afganistán, la bandera talibán |
| Nunca | más de 14 | lo bloquea `check_geo` |

Se pasa como `P(..., grados=5, sitio='Mecca')`.

### Cómo se verifica (obligatorio, aborta el render)
1. **`python coreo.py check`** corre `check_geo()`, que comprueba tres cosas y **frena el render** si algo falla:
   **A.** todo prop declarado con `sitio=` cae a menos de 3 px de ese sitio;
   **B.** todo prop hecho con `entre()` empieza y termina en sus dos anclajes;
   **C.** nada apoyado en la hoja pasa de 14 grados de longitud.
2. **`python _prueba_geo.py`** renderiza cada instante en que la voz nombra un lugar y le dibuja una cruz
   sobre el sitio real. **Si la animación no coincide con la cruz, el anclaje está mal.** Se mira siempre,
   con los ojos, antes de dar por bueno un episodio.

## Transición de acto (Agustín, 2026-09-09)

> *"Cuando pasa de un ACT a otro tenemos que hacerlo bien, pasa del III al IV se ve super rápido.
> deberíamos estandarizar eso... Eso tiene que tener un tiempo, y un 'efecto de sonido' que lo indique.
> Y si tiene un título, se tiene que leer con otra voz."*

**Es igual en todos los actos y en todos los episodios.** Bloque **fijo de 4,4 s** metido EN EL AUDIO
(no es un cartel encima de la narración: la voz principal se calla).

| t dentro del bloque | Qué pasa |
|---|---|
| 0,00 | corte a `WALL` |
| 0,10 | **stinger + thump** y sacudón de cámara — el golpe que marca el cambio |
| 0,10-0,55 | una regla de papel cruza el cuadro |
| 0,30 | un velo de papel apaga el mapa: el cartel de acto queda solo |
| 0,22 | cae `ACT N` |
| 0,55 | **la segunda voz lee el título** y la tarjeta entra girando al mismo tiempo |
| 1,50 | ficha `PAPER TRAIL` debajo |
| 3,85-4,40 | todo se apaga, el velo se levanta y se corta al primer plano del acto |

**La segunda voz** es distinta a la del narrador: George (`JBFqnCBsd6RMkjVDRZzb`) narra, y el título de
acto lo lee `21m00Tcm4TlvDq8ikWAM`. Cuesta ~USD 0,03 los cinco actos de un episodio.

Implementación: `voz_ep.py` mete el bloque al concatenar (`BEATS_ACTO`, `PAUSA_ACTO`, `ACTO_T0`) y guarda
los tiempos en `audio/tiempos.json` bajo `actos`; `coreo.py::acto(num, txt, beat)` lo llena.
**Si se cambia la duración de los bloques no hace falta volver a correr whisper**: las palabras cacheadas
en `audio/_palabras.json` se desplazan por cálculo exacto.
