# DIARIO — manual del formato de video diario

> Creado 2026-09-11. **Documentación propia de este formato.** Nace de una decisión de Agustín:
> *"esto es diferente a otro tipo de videos que generamos, no tiene que afectar a nada de lo que venimos
> haciendo, simplemente será algo nuevo"*.

## 0. Qué es, y qué no toca

Un video **diario** de 15-25 min que relata las noticias del día: lo que pasó y lo que va a pasar,
separado por tema y por región. Dos paneles fijos: **presentador con micrófono a la izquierda, animación
de la noticia a la derecha.**

**Lo que NO toca:** los Dispatch y los Brief siguen exactamente como están (`canal/FORMATOS.md`), con su
calendario, su estructura de 11 beats, su coreografía a mano y su nivel de acabado. Este formato **no los
reemplaza, no los modifica y no compite por su lugar**. Es un producto nuevo, con su propio manual (este
archivo), su propio directorio (`videos/DAILY/`) y sus propias reglas.

Lo único que comparte con el canal: la **paleta de 7 colores** y la **técnica de recorte de papel**
(`ESTILO.md` §2.1 y §2.2). Es la familia visual; todo lo demás es propio.

## 1. El layout

```
┌───────────────────────────┬───────────────────────────┐
│                           │                           │
│      PRESENTADOR          │         LA FICHA          │
│      960 × 1080           │        960 × 1080         │
│                           │                           │
│   rig fijo, siempre el    │   cambia con cada         │
│   mismo, lip-sync         │   noticia: mapa, versus,  │
│   + idle + 4-5 gestos     │   titular, dato, serie... │
│                           │                           │
│   micrófono abajo         │                           │
└───────────────────────────┴───────────────────────────┘
                     1920 × 1080
```

**Por qué este layout y no otro:** un episodio del canal hoy pide ~1.400 líneas de coreografía escritas a
mano porque cada plano es una composición única. Con dos paneles fijos, el panel izquierdo no cambia nunca
y el derecho se elige de un catálogo cerrado. El guion deja de producir coreografía y pasa a producir
**una lista de fichas**. Eso es lo que hace posible la cadencia diaria.

Beneficio extra de rendimiento: como el cuerpo del presentador no cambia, el panel izquierdo se **compone**
a partir de ~9 formas de boca (visemas de Rhubarb) sobre poses fijas, en vez de **dibujarse** cuadro por
cuadro. Con 6 vCPU en el VPS, esto no es un lujo.

## 2. La mesa: tres presentadores con puesto fijo

> Decisión de Agustín, 2026-09-11: los tres candidatos entran. *"Podríamos hacer los guiones con los 3, e
> ir inventando y dando roles según lo que viene en la información."*

Tres presentadores en vez de uno, por una razón de retención: **un solo busto parlante durante 20 minutos
es lo que hace que la gente se vaya.** El pase de uno a otro es un corte de atención natural, y es cómo
funciona un noticiero de verdad.

**Los puestos son fijos; lo que varía es qué noticia le toca a cada uno.** Ésta es la diferencia que hace
que funcione: si los roles se improvisan cada día, el público nunca aprende quién es quién y el generador
de guion vuelve a decidir a mano en cada episodio. Con puestos fijos, "según lo que viene en la
información" se resuelve solo: la noticia cae en el bloque que le corresponde y el bloque ya tiene dueño.

| | Personaje | Puesto fijo | Por qué encaja |
|---|---|---|---|
| **A** | El corresponsal — traje azul, anteojos rectangulares, anchor | **THE POWERS** · abre el cold open y cierra el programa | Es la cara institucional. Lo genérico, que como presentador único era su defecto, acá es exactamente lo que se le pide al ancla. |
| **C** | El archivista — chaleco, moño, pluma, anteojos redondos | **THE MONEY** + **TECH & ENERGY** + **WHAT TO WATCH** | Es el hombre del expediente: números, series, documentos y el calendario de lo que viene. Su papel literal. |
| **B** | El analista — joven, mangas arrolladas, tiradores | **THE SOUTH** + **THE PACIFIC** | El corresponsal regional, fuera de la mesa central. Su registro más liviano, que desentonaba en una nota de guerra, acá juega a favor. |

**Lo que esto habilita y con uno solo era imposible:** en un evento `disputed`, **dos presentadores
sostienen las dos lecturas en pantalla**. La separación HECHO / AFIRMACIÓN deja de ser una tarjeta y pasa a
ser una discusión. Es la mejor versión de la ficha `versus`.

**Qué cuesta de más:** tres rigs en vez de uno (brazos, ~9 bocas y 2-3 cejas por personaje) — **coste único,
~15-25 créditos de fal, no por episodio**. Y tres voces de ElevenLabs en vez de una: **no aumenta el costo**,
porque ElevenLabs cobra por carácter generado y no por voz. 20 minutos repartidos entre tres son los mismos
20 minutos. George (`JBFqnCBsd6RMkjVDRZzb`) queda para A; B y C piden dos voces nuevas.

**Lo que NO cambia:** el catálogo de ocho fichas (§3) y el alcance de `escena.py`. El panel izquierdo sólo
elige qué rig carga. Es un `if`, no un motor nuevo.

Candidatos en `presentador/` (Flux 2 Pro, hoja en `presentador/_hoja_presentadores.jpg`).
Nota de rig: **B tiene los codos pegados al torso** y hay que regenerarlo con los brazos más despegados
antes de cortarle las capas. A y C están listos para cortar.

**Cómo se recorta el fondo** (aprendido a los golpes el 2026-09-11): con **`fal-ai/bria/background/remove`
(RMBG 2.0), USD 0,018 por imagen**. Los `*_alpha.png` de `presentador/` ya están hechos.
El relleno por inundación local **no sirve** para estos personajes: la piel y la camisa son casi del color
del fondo, y la inundación se come las manos. Si el recorte se rehace, es con Bria, no a mano.

## 2bis. La voz: Piper local, no ElevenLabs

> Decision de Agustin, 2026-09-11: *"esto al principio tendria que ser gratis"*.

Medido el mismo dia, con la misma linea de guion:

| | Costo | Velocidad |
|---|---|---|
| **ElevenLabs George** (lo del canal) | 22.077 chars/dia = **USD 2,21/dia = USD 66/mes** | API |
| **Piper en el VPS** | **USD 0** | 20 min de audio en 1,5 a 11 min de CPU |

**Esto deja al formato diario en costo cero.** El Radar corre con embeddings locales, los feeds son
gratis, el render es el VPS, la subida es gratis y el LLM son los USD 10 de OpenCode que ya estaban.
La voz era la unica linea que no era cero, y con Piper lo es.

**Las tres voces, una por presentador** (`voz/piper/`, muestras en `_muestra_*.wav`):

| Presentador | Voz Piper | Velocidad |
|---|---|---|
| A · El corresponsal | `en_US-ryan-high` | 2x tiempo real (la mas cuidada) |
| B · El analista | `en_US-joe-medium` | 6x |
| C · El archivista | `en_GB-alan-medium` | 14x |

**Lo que se pierde, dicho sin vueltas:** Piper no tiene la direccion de actor de eleven-v3. Es un
locutor correcto y neutro, no un narrador con intencion. Para un informativo diario eso pesa mucho
menos que para un Dispatch —a un lector de noticias se le pide neutralidad— pero es una diferencia
real y hay que escucharla antes de decidir.

**El reparto que propongo:** el diario va con Piper (30 videos al mes, USD 0). Los Dispatch y Brief
siguen con George (2 al mes, entra de sobra en el tope de USD 4 por produccion de `COSTOS.md`).
Cuando el canal monetice, se puede reevaluar.

## 3. El catálogo de fichas (panel derecho)

Regla dura: **el guion sólo puede pedir estas ocho.** Si una noticia necesita una novena, se reescribe la
noticia o se agrega la ficha al catálogo — nunca se improvisa una composición suelta.

| Ficha | Qué muestra | Campo del Radar que la alimenta |
|---|---|---|
| `mapa` | hoja + puntos + flechas | `event.paises`, `event.actores` |
| `versus` | dos actores y sus versiones enfrentadas | `narrative` + `statement(disputed)` |
| `titular` | recorte de prensa con medio y fecha | `article` |
| `dato` | un número grande con su etiqueta | `statement(fact)` con cifra |
| `serie` | una curva en el tiempo | ECB / EIA / Federal Register |
| `cronologia` | qué pasó a qué hora | timeline del evento |
| `calendario` | fechas que vienen | bloque WHAT TO WATCH |
| `plano` | imagen generada, sólo para momentos hero | fal.ai, 1-2 por episodio |

Formato que emite el guion:

```json
{"t": 142.5, "ficha": "versus",
 "izq": {"actor": "Kremlin",  "dice": "..."},
 "der": {"actor": "Ucrania",  "dice": "..."},
 "pie": "evidencia independiente insuficiente"}
```

`versus` es la ficha insignia: es la separación HECHO / AFIRMACIÓN hecha imagen, y es lo que distingue este
formato de un repaso de titulares.

## 4. Estructura del episodio — los minutos VARIAN

> Decision de Agustin (2026-09-11): *"los tiempos... lo ideal seria que eso varie de acuerdo al dia"*
> y *"faltaria un bloque importante que incluya a Medio Oriente"*. Las dos van. La escaleta la calcula
> `videos/DAILY/escaleta.py`; el dibujo con dos dias de ejemplo, `estructura.py` -> `_estructura.jpg`.

Ocho bloques. **THE MIDDLE EAST es propio**, no un rincon de THE POWERS: Israel, Iran, el Golfo y el
Levante son su propio teatro y no se reparten parejo con el resto del mundo.

| Bloque | Minimo | Maximo | Presentador | Que cubre |
|---|---|---|---|---|
| COLD OPEN | \- | fijo 0:45 | A | El hecho del dia + "stay to the end" |
| INTRO | \- | fijo 0:15 | \- | Sello de papel, THE LEDGER, la fecha |
| **THE POWERS** | 3:00 | 9:00 | A | EEUU · Europa · China · Rusia |
| **THE MIDDLE EAST** | 1:30 | 6:00 | B | Israel · Iran · Golfo · Levante |
| **THE MONEY** | 2:00 | 6:00 | C | Mercados, comercio, bancos centrales |
| **TECH & ENERGY** | 1:00 | 4:00 | C | Chips, IA, tierras raras, ductos |
| **THE SOUTH** | 1:30 | 5:00 | B | Latinoamerica, Argentina primero |
| **THE PACIFIC** | 1:00 | 4:00 | B | Australia, NZ, Indo-Pacifico, Taiwan |
| **WHAT TO WATCH** | 1:30 | 2:30 | C | El calendario de lo que viene |
| OUTRO | \- | fijo 0:20 | \- | Like, suscripcion, el video de manana |

### Como se reparten los minutos

1. **Lo fijo primero** (cold open, intro, outro): 1:20 que no se mueven.
2. **Cada bloque se lleva su MINIMO.** Asi ninguno desaparece: Latinoamerica conserva su minuto y
   medio aunque no haya pasado nada, porque la audiencia que viene por eso vuelve manana.
3. **Lo que sobra se reparte segun el peso del dia**: la suma de importancia de los acontecimientos
   de cada bloque, con tope por acontecimiento para que uno solo no se lleve el programa.
4. **Se recorta contra el maximo** y lo que rebalsa vuelve a repartirse.

Medido con los dos dias de ejemplo de `estructura.py`:

| | dia tranquilo | dia de guerra |
|---|---|---|
| THE POWERS | 5:35 | **3:37** |
| THE MIDDLE EAST | 1:58 | **5:14** |
| THE SOUTH | 2:20 | 1:30 (su minimo) |
| **total** | 20:00 | 20:00 |

### El reparto de presentadores tiene una logica

**A la mesa de las potencias, B los teatros donde estan pasando cosas, C los numeros y el calendario.**
Por eso Oriente Medio va con B junto a Latinoamerica y el Pacifico: son los frentes, no la mesa.
Ningun presentador se lleva mas de la mitad del programa.

**WHAT TO WATCH cierra siempre y no depende del peso del dia.** Un repaso de noticias lo hace
cualquiera; el calendario de lo que viene es lo que hace volver manana.

## 5. La cadena diaria

Publica **12:00 UTC** — 08:00 Nueva York, 14:00 Berlín, 09:00 Buenos Aires.

```
04:00 UTC  cierre de ventana de noticias · ranking del Radar
04:15      selección de ~25-30 eventos repartidos por bloque
04:30      guion + lista de fichas
04:35      Telegram: orden del día y banderas rojas
04:40      voz (ElevenLabs George)
04:45      composición del panel izquierdo + render de fichas
05:00      render arranca (3 workers, nice 19)
~08:30     mezcla, miniatura, subida programada
11:00      último momento para contestar si hubo bandera roja
12:00      PUBLICA
```

**Compuerta invertida:** sin banderas rojas publica solo; con bandera roja no publica hasta que Agustín
conteste. Bandera roja = atentado o masacre de los últimos 7 días, tema donde `canal/IDEOLOGIA.md` dice
preguntar, un `fact` que quedó con una sola fuente, o una persona privada nombrada.

### 5.1 Cómo corre sin que nadie lo mire

Un solo orquestador en el VPS, `daily.py`, con **etapas idempotentes**. n8n no ejecuta las etapas: las
dispara, las cronometra y avisa. Cada etapa escribe su resultado en `run_log`, así que si una falla se
reintenta sola sin rehacer las anteriores.

| # | Etapa | Qué hace | Si falla |
|---|---|---|---|
| 1 | `recolectar` | cierra la ventana, rankea, elige 25-30 eventos | reintenta a los 10 min; si vuelve a fallar, usa el ranking de la última corrida buena |
| 2 | `guion` | Claude escribe el guion + la lista de fichas (JSON validado contra esquema) | reintenta 2 veces; si el JSON no valida, aborta y avisa |
| 3 | `voz` | ElevenLabs, un archivo por bloque | reintenta; es la etapa que cuesta plata, así que cachea por hash del texto |
| 4 | `alinear` | Rhubarb saca los visemas del audio → la pista de bocas | reintenta |
| 5 | `coreo` | fichas + visemas → ángulos por cuadro | determinista, no falla |
| 6 | `render` | PIL + ffmpeg, 3 workers, `nice -n 19` | **resumible**: los cuadros van a `_frames_<fecha>/` y al reintentar sigue desde el último cuadro escrito |
| 7 | `mezcla` | voz + cortina + intro/outro | reintenta |
| 8 | `miniatura` | cuadro elegido + texto | reintenta |
| 9 | `subir` | YouTube API, privado + programado 12:00 UTC | reintenta 3 veces con espera creciente |

**Punto importante sobre el render:** `motor.py` hoy borra `_frames` al arrancar (`feedback-no-tramos-durante-render`).
Para el diario eso hay que cambiarlo por un directorio propio por fecha y arranque desde el último cuadro:
si no, un corte de luz a las 07:00 obliga a rehacer dos horas y el video no sale.

### 5.2 La subida a YouTube

Con **YouTube Data API v3**, `videos.insert` con subida resumible. Lo que la hace desatendida:

- **OAuth una sola vez.** Se autoriza desde el navegador una vez, se guarda el *refresh token* en el VPS, y
  a partir de ahí renueva solo. No vuelve a pedir nada salvo que se revoque el permiso.
- **Se programa sola:** se sube con `status.privacyStatus = "private"` y `status.publishAt = <fecha ISO>`.
  YouTube lo publica a esa hora **sin que corra nada de nuestro lado**. O sea: el video puede terminar a las
  08:30 y hacerse público a las 12:00 aunque el VPS esté apagado.
- **Cuota:** 10.000 unidades/día. `videos.insert` cuesta 1.600, `thumbnails.set` 50, sumar a lista 50.
  Un video diario consume ~1.700 de 10.000: **sobra para 5 reintentos completos**.
- **El límite de 10 MB no aplica acá.** Ese límite es de lo que el asistente puede mover en el chat
  (`project-subida-limite-10mb`). El VPS sube directo a YouTube por la API: un episodio de 20 min a 1080p
  (~400 MB) va sin problema. **Esto es lo que hace que el diario no dependa de que Agustín suba nada a mano.**

### 5.3 El vigilante

Un único chequeo independiente a las **10:00 UTC**: ¿hay un video subido y programado para hoy?
Si no, Telegram con la etapa donde se cortó y el error. Es la red que evita el peor caso: que el día pase
sin video y sin que nadie se entere.

## 6. Reglas propias de este formato

1. **El presentador es siempre el mismo.** No rota, no cambia de ropa, no envejece.
2. **Ocho fichas, ninguna más** (§3).
3. **Un solo elemento rojo por plano**, heredado de `ESTILO.md` §2.2.
4. **Las afirmaciones van con su actor en pantalla.** Si Rusia dice algo, la ficha dice "Rusia dice". Nunca
   una afirmación presentada como hecho.
5. **Nada de material de archivo ajeno.** Todo lo visual se genera. Evita el campo minado de copyright de
   imágenes de agencia.
6. La opinión del canal sigue la línea de `canal/IDEOLOGIA.md`; el interrogatorio completo **no** se corre
   por noticia (sería inviable a diario), se corre **una vez por bloque** cuando el bloque toma postura.

## 7. Gasto de esta producción

Tope de `COSTOS.md`: **USD 4**. Llevamos **USD 0,190**.

| Qué | Modelo | Precio unitario | Coste |
|---|---|---|---|
| 5 generaciones (A, B v1, C, B v2a, B v2b) | `fal-ai/flux-2-pro` | USD 0,03/megapíxel → 0,024 a 768×1024 | 0,118 |
| 4 recortes con alfa | `fal-ai/bria/background/remove` | USD 0,018 | 0,072 |
| Hoja de contacto y cuadro de layout | PIL, local | — | 0 |

## 8. Lo aprendido en la primera pasada (2026-09-11)

Tres cosas que costaron créditos o tiempo y no hay que volver a pagar:

1. **El recorte por inundación no sirve** para estos personajes: la piel y la camisa son casi del color del
   fondo y se come las manos. Es Bria RMBG, USD 0,018.
2. **"Brazos separados" hay que pedirlo con geometría, no con adjetivos.** La primera versión de B decía
   "brazos apartados del cuerpo" y salió con los codos pegados al torso. Lo que funcionó fue describir el
   ángulo ("cuarenta y cinco grados hacia afuera"), exigir el hueco ("un hueco grande de fondo visible
   entre cada brazo y el torso a lo largo de todo el brazo") y nombrar la silueta ("que lea como una Y").
3. **Flux se va solo al registro infantil** si no se lo prohíbe explícitamente. El negativo que lo frenó:
   *no big round eyes, no white eyeball sclera, no open smiling mouth, no pink cheeks*. Sin eso salen ojos
   redondos con esclerótica y cachetes rosados, que al lado de las caricaturas de líderes desentonan.

Descartes guardados como referencia: `B_v1_descartado.jpg` (codos pegados, cara infantil) y `B_v2b.jpg`
(remaches dorados fuera de escala, cabeza despegada del cuello, cara dibujada en vez de armada en capas).

## 9. Estado real (2026-09-11, construido y probado)

**Corre de punta a punta.** 15 modulos con autotest propio, todos en verde. Una corrida real contra
las 79 fuentes: **3.850 articulos ingeridos en 13 s**, agrupados en acontecimientos coherentes.

| Modulo | Que hace | Prueba |
|---|---|---|
| `radar/ingesta.py` | 79 feeds, dedup, wire_origin, chequeo de frescura | red real |
| `radar/semantica.py` | embeddings multilingues + ancla de entidad rara | 0 fusiones falsas |
| `radar/agrupar.py` | clustering incremental de tres tramos | los 3 casos canonicos |
| `radar/extraccion.py` | hecho / afirmacion / disputado | la regla del doble conteo |
| `radar/puntajes.py` | importancia y video score | 72 pruebas |
| `radar/almacen.py` | Postgres+pgvector, SQLite para test | invariantes en la base |
| `radar/llm.py` | cascada OpenCode -> Claude, 3 formatos de API | transporte falso |
| `radar/mcp_server.py` | las 8 herramientas | registradas en FastMCP |
| `videos/DAILY/fichas.py` | los 8 renderizadores | `_fichas_prueba.jpg` |
| `presentador/rig.py` | los 3 rigs, 6 piezas c/u | 116 pruebas |
| `presentador/bocas.py` | 9 visemas dibujados | las 9 distintas |
| `videos/DAILY/escena.py` | los dos paneles a 1920x1080 | `_escena_tres.jpg` |
| `videos/DAILY/daily.py` | 9 etapas idempotentes, render resumible | idempotencia y vigilante |
| `videos/DAILY/subir.py` | YouTube programado | 44 pruebas |

**Velocidad de render medida:** 46 cuadros/s en un proceso, gracias al cache de poses (el motor viejo
hacia 7,2 redibujando todo). Aun con el VPS mas lento y 3 workers, 20 min de video entran comodos.

## 10. Pendientes reales

**Bloqueantes para la primera corrida en el VPS:**
1. `OPENCODE_API_KEY` y `ANTHROPIC_API_KEY` en el entorno. Sin eso no hay guion ni extraccion.
2. `python videos/DAILY/subir.py --autorizar` una vez en el VPS (OAuth de YouTube).
3. `pip install fastembed piper-tts` y `python videos/DAILY/voz.py --bajar` (los 3 modelos, 250 MB).
4. El swap de 8 GB (sin eso el render puede tumbar Supabase y n8n).

~~Rhubarb~~ y ~~voces de ElevenLabs para B y C~~ ya no bloquean: `voz.py` resuelve las dos cosas
gratis. Rhubarb sigue siendo opcional y mejora el lip-sync si se instala.

**Clip de verificacion (2026-09-11):** `_clip_prueba.mp4`, 19 s reales con voz Piper, lip-sync con
las 9 bocas y las fichas `titular`, `versus` y `dato`. Render a **23,5 cuadros/s** con lip-sync
activo. Costo: USD 0 (lo mismo en ElevenLabs habria sido USD 0,03).

**El reacomodo de la linea de tiempo se gano el lugar en ese clip:** el guion decia que los tres
beats duraban 9, 9 y 7 segundos. La voz real duro 6,3, 7,1 y 3,9. Sin corregirlo, la ficha habria
cambiado en mitad de cada frase y la boca se habria quedado quieta hablando.

**Defectos conocidos, anotados al verlos:**
- **El brazo de C en pose `senala` cruza el pliegue** y se mete en el panel de la ficha. Hay que
  acotar el angulo por presentador o achicar el rig de C. Visible en `_escena_tres.jpg`.
- En `abre los brazos`, a C se le ve una costura horizontal en la cintura (el hueco que dejan las
  manos al moverse sobre el chaleco).
- La ficha `mapa` dibuja un marco con puntos por proyeccion simple; falta engancharla a las hojas
  reales de `produccion/mapa_*.py` para cumplir la regla 24.
- El bloque del brief solo se reparte bien cuando corrio la extraccion (los `topics` los pone el LLM).
  Sin claves, todo cae en THE POWERS.

## 11. Pendientes de formato

1. ~~Cuadro fijo del layout~~ — **aprobado por Agustín el 2026-09-11.** `_layout.jpg` / `layout.py`.
2. ~~Regenerar B con los brazos despegados~~ — hecho, `B_v2a`. Los tres tienen ya su `*_alpha.png`.
3. ~~Las piezas del rig de A~~ — **hecho.** `rig.py` + `rig_A.json` + `piezas_A/`. 6 piezas, 5 pivotes.
   Prueba en `_rig_A_prueba.jpg`. Faltan los rigs de B y C (mismo procedimiento, otros polígonos) y
   **dibujar las ~9 bocas de Rhubarb en PIL** — generarlas con Flux daría nueve bocas distintas entre sí;
   dibujadas salen consistentes, controlables y a coste cero.

   **Lo que costó acertar en el rig de A, para no repetirlo en B y C:**
   - El corte del hombro **sigue la costura de la manga** (casi vertical), no una perpendicular al brazo.
     Los brazos están separados del torso por un hueco de fondo; un corte perpendicular cruza ese hueco y
     se lleva una astilla del saco, que después se desprende al girar.
   - **El brazo va por delante del torso** en el orden de capas. Al revés, girar hacia adentro esconde el
     brazo detrás del saco y parece que desapareció.
   - **Signo:** en el brazo derecho, positivo abre hacia afuera y negativo cierra sobre el cuerpo. En el
     izquierdo es al revés, por simetría. Medido con un barrido, no deducido.
4. **`escena.py`**: rigs + los 8 renderizadores de ficha. El trabajo grueso; no depende del Radar.
5. **Las 2 voces nuevas** de ElevenLabs para B y C (George queda para A).
6. **Intro y outro propias** del formato, distintas de las del canal.
7. **Nombre del formato.** En el cuadro está puesto THE LEDGER como marcador de posición. Lo decide Agustín.
8. El Radar que lo alimenta: `RADAR.md`.
