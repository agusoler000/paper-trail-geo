# SHORTS — modelo nuevo (2026-09-08)

> **Decisión de Agustín, 2026-09-08.** Los shorts se rediseñan enteros:
> 1. Se crean **junto con el video principal y/o solos**. Lo define **cómo arranca la conversación**.
> 2. Con episodio: **mismas imágenes** que el largo, **guion exclusivo**, y **3-5 shorts MUY bien armados** en vez de 10.
> 3. **Duración mínima 50 s**; el máximo **lo decide el tema**, sin default, hasta los 3 min que permite Shorts.
> 4. Solo shorts: se produce **igual que el video principal pero en formato short** — se genera todo y se prepara.
> 5. **Serie de shorts**: un tema, varias subtemáticas, una pieza por subtema, todas de la misma serie.
> 6. **Cada producción en su directorio** (`canal/ESTRUCTURA.md`).
> 7. **Tope de gasto: USD 4 por producción** (episodio + shorts en el mismo techo), subido de 3 por esta decisión.
> 8. **Sin intro de canal; outro corta que pida la suscripción** en cada pieza.
>
> Lo anterior es de Agustín. Los números, plantillas y criterios que no estén marcados así son **propuesta del
> asistente** y él los cambia cuando quiera.

---

## 1. Los tres modos

| | **A · Con episodio** | **B · Serie** | **C · Suelto** |
|---|---|---|---|
| Arranca con | "hacemos un video de X" | "una serie de shorts sobre X" | "un short de X" |
| Cuántos | 3-5 | los que pidan los subtemas (4-8) | 1 |
| Investigación | la del episodio | propia y completa | propia |
| Guion | **exclusivo**, no es un recorte | uno por pieza | uno |
| Voz | **nueva** (no se reusa la del largo) | nueva | nueva |
| Imágenes | **las mismas del episodio** (props, mapa, rigs, hero) | propias, hechas para la serie | propias |
| Coreografía | nueva, vertical | nueva, vertical | nueva, vertical |
| A dónde manda | al episodio | a la pieza siguiente / a la playlist | al canal |
| Carpeta | `videos/<NN>_<tema>/shorts/` | `videos/S<NN>_<tema>/shorts/<n>_<subtema>/` | igual que B |

---

## 2. Modo A — los 3-5 del episodio

**"Mismas imágenes" quiere decir el arte, no el metraje.** Se reusan `arte/props.py`, `arte/mapa.py`, los rigs, los
planos hero y las texturas — que es donde estaba el trabajo y el gasto. Lo que **no** se reusa es el video ya
renderizado: la coreografía del largo está pegada frase por frase a la narración vieja, así que pegarle una voz nueva
encima desincroniza todo. Se escribe coreografía nueva, corta, en vertical, con los mismos objetos.

**El guion exclusivo** no repite el argumento del episodio: lo **destila**. Por cada short, una idea completa que se
entiende sin haber visto nada, que **deja una pregunta abierta**, y cuyo final natural es "esto está entero en el canal".
Un short que cuenta el episodio no sirve: el que lo vio entero no hace clic.

Los 3-5 salen de tomar los momentos más fuertes del episodio y **contarlos de nuevo, mejor**, con el tiempo que en el
largo no tenían: el gag visual, la cifra invertida, el giro conceptual.

**Duración:** mínimo 50 s, **sin máximo por defecto: lo decide el tema** (Agustín, 2026-09-08). Techo real de
YouTube Shorts: 3 min. Al armar cada pieza se propone su duración y él la aprueba. Ver §7 sobre el dato del canal.


### El arco de una pieza (Agustín, 2026-09-09, mirando los shorts del ep. 4)

> *"las historias de los shorts tienen que tener una historia que inicia, se desarrolla y cierra. Si de la nada me
> salta con chao o con algo que nada que ver, ¿cómo mierda atrapo al viewer?"*

Lo que decía antes esta hoja — *"una idea completa que deja una pregunta abierta"* — se quedaba corto y produjo un
tic: en el ep. 4 **cuatro de las cinco piezas terminaron con una pregunta retórica que empieza con "So…"**, y una
(la del 1833) usó la pregunta **en lugar** del cierre. Suena a fórmula y deja al espectador colgado.

La regla completa:

1. **Inicio.** Dos o tres frases que sitúan de qué se habla. Nadie en el feed sabe nada (§ del contexto, 2026-09-09).
2. **Desarrollo.** Una sola idea, con los hechos en orden y un giro a mitad.
3. **Cierre de verdad.** La última frase **cierra la idea**: una afirmación que se puede repetir de memoria.
   *"London already owns the contract. It just has the wrong islands typed at the top."* Eso cierra.
   *"So what do you call that morning?"* no cierra: pregunta y se va.
4. **Recién después**, si abre algo, que sea **una** frase corta y **no siempre el mismo recurso**. Si las cinco
   piezas terminan con "So + pregunta", el espectador aprende la fórmula y deja de escuchar el final.
5. La pregunta abierta puede estar **en el medio** (lo que empuja a seguir mirando) y el cierre al final. No al revés.


### Cuándo se publica un short (Agustín, 2026-09-09)

> *"esa restricción tiene que quitarse. Los shorts son para atraer gente a nuestro canal y que vean nuestros videos.
> Pueden ser presentaciones para futuros videos o sobre videos que ya subimos."*

**Un short no depende de que su episodio esté publicado.** Es una pieza de captación por derecho propio y puede salir:

| Momento | Para qué sirve | A dónde manda |
|---|---|---|
| **Antes** del episodio | Presentación / teaser: instala el tema y crea expectativa | Al canal, o al video más cercano del catálogo. Cuando el episodio salga, se le edita el enlace |
| **El mismo día** | Empuja el estreno | Al episodio |
| **Después**, semanas o meses | Revive un episodio ya subido y le sigue trayendo gente | Al episodio |
| **Suelto o en serie**, sin episodio detrás | Trae suscriptores por sí mismo (modos B y C) | Al canal o a la pieza siguiente |

Lo que **no** cambia: el enlace al canal o a un video siempre se pone. Un short sin destino trae vistas y no trae a
nadie. Si sale antes del episodio, se apunta a lo que haya y **se edita después** — son dos minutos en Studio.

Lo que yo (el asistente) había escrito antes — "primero el episodio, después los shorts" — era una conclusión mía
sacada de una limitación técnica (no se puede enlazar un video que todavía no existe), no una regla de Agustín.


## Pedir comentarios — SIEMPRE (Agustín, 2026-09-09)

> *"en todos los shorts y todos los videos de ahora en más hay que dejar preguntas o cosas para responder en los
> comentarios."*

**Cada pieza que sale del canal —episodio largo, short, teaser, serie— tiene que dejarle al espectador algo que
responder.** No es un adorno del final: los comentarios son la señal más fuerte que una pieza le da al algoritmo, y
en temas con dos bandos son gratis.

Dónde va, en este orden:

1. **EN LA VOZ, y esto es lo primero, no lo opcional** (Agustín, 2026-09-09: *"que sea la voz la que lo pregunte
   e incentive a dejar el comentario, tanto en los videos como en los shorts"*). Cerca del cierre, el narrador
   pregunta y pide explícitamente el comentario. Una pregunta concreta, nunca "¿qué opinás?": la buena divide y se
   contesta en cinco palabras. *"British or Argentine? Put it in the comments."* Va en el guion como una línea `A:`
   más, escrita desde el principio — no se pega después.
2. **En pantalla**, en la tarjeta final, junto al SUBSCRIBE. En los shorts del ep. 4 quedó como
   `BRITISH OR ARGENTINE? / TELL US IN THE COMMENTS`.
3. **En la descripción**, en la última línea.
4. **En el comentario fijado**, con la fuente primaria del dato más discutible de la pieza: invita a discutir con
   el papel delante y deja el hilo abierto desde el minuto cero.

Y cuando la pieza opina (como el veredicto del ep. 4), la pregunta se hace **honesta**: se pide la contraria.
Un video que concluye y además pregunta "¿en qué me equivoco?" recibe el doble de comentarios que uno que solo concluye.

---

## 3. Modo B — la serie

Ejemplo que pidió Agustín (2026-09-08): **11-S**, con una pieza por ángulo — los hechos · cómo se planeó · el origen ·
las consecuencias en la vida cotidiana · dónde estamos hoy.

**Una investigación, una postura, un set de arte, N piezas.** El interrogatorio de `IDEOLOGIA.md` §2 se hace una vez
para la serie entera, no por pieza.

Reglas de serie:

1. **Cada pieza es un ángulo cerrado.** "Los hechos" no explica el origen; "el origen" no repite los hechos. Si dos
   piezas cuentan lo mismo con otras palabras, sobra una.
2. **Cada pieza se entiende sola.** La gente entra por la 4, no por la 1. Ninguna arranca con "como vimos en el anterior".
3. **Cada pieza cierra abriendo la siguiente**: la última frase nombra el ángulo que viene ("Nobody planned this in a
   cave. Next: who paid for it.").
4. **Sello `PART 2 OF 5`** de papel, misma esquina en todas, misma tipografía. Es lo que hace que se vea como serie
   en el feed y lo que hace que alguien busque las otras.
5. **Playlist propia** con el nombre de la serie. Las N entran ahí y el link va en las N descripciones.
6. **Una por día, en orden, a la misma hora.** Publicadas salteadas, la serie no existe.
7. **El "video relacionado"** de cada pieza apunta a la anterior. Excepción: si la serie desemboca en un episodio largo
   del mismo tema, todas apuntan al episodio — **ese es el mejor uso de una serie** y convierte la serie en el tráiler
   de un Dispatch.

---

## 4. La pieza — reglas de formato

- **1080×1920, 24 fps, audio normalizado a −14 LUFS.**
- El cuadro 16:9 entra **completo, sin recortar** (regla 1 de Agustín: nada cortado), incrustado en una hoja de papel
  sobre la mesa, que es lo que llena el alto. El bloque de video mide 1000×563 en `shorts.py`.
- **Gancho fijo arriba** en 2-3 líneas, una en rojo. Es el título visible y se lee sin sonido. Sensacionalista, con el
  drama en el verbo y en la promesa, nunca en un dato que el short no diga.
- **Subtítulos quemados** por frase, palabras clave en rojo. El 80 % del feed se mira sin audio.
- **Barra de progreso** ocre: dice cuánto falta y siempre hay algo en movimiento.
- **Nada importante por debajo de y≈1550**: ahí la app pone título, canal y botones.
- **Sin intro del canal** (los 30 s de preguntas no caben en una pieza de 60 s).
- **Outro corta que pide la suscripción** — decisión de Agustín, 2026-09-08, y es la excepción a su regla 4. 3-4 s
  al final de cada pieza: ficha PT, `SUBSCRIBE` grande y `FOLLOW THE PAPER.` debajo, sobre la hoja, con el sello
  cayendo (`stamp()`) para que haya movimiento hasta el último cuadro. Encima va la línea que corresponda al modo:
  `FULL EPISODE ON THE CHANNEL` (A) · `PART 3 TOMORROW` (B) · `MORE ON THE CHANNEL` (C). Es lo único que se agrega
  al final: nada de tarjetas no pedidas.

---

## 5. Pipeline de un short con guion propio

Con episodio (modo A), después de entregar el largo. Solo o serie (B/C), es el pipeline del episodio en chico.

| # | Paso | Costo | Salida |
|---|---|---|---|
| 1 | Fuentes e interrogatorio de postura (`IDEOLOGIA.md` §2). En modo A ya está hecho | 0 | `postura.md` |
| 2 | Guion exclusivo, una idea por pieza, cierre con pregunta abierta | 0 | `shorts/<n>/guion.md` |
| 3 | Ficha de cada pieza: gancho, palabras a resaltar, título, descripción, tags, orden | 0 | `shorts/shorts.json` |
| 4 | Voz George con dirección de actor (`voz/voz_fal.py`) | **≈ USD 0,10 / 1.000 chars** | `shorts/<n>/audio/` |
| 5 | Alineación (`voz/alinear.py`) | 0 | `.tiempos.json` |
| 6 | Coreografía vertical reusando el arte de la producción | 0 (horas) | `shorts/<n>/coreo.py` |
| 7 | `check` de encuadre: **0 cortados** antes de renderizar | 0 | hoja de contacto |
| 8 | Render + composición del lienzo vertical | 0, ~3 min/pieza | `shorts/<n>/salida/` |
| 9 | Fichas de publicación y plan de subida | 0 | `PUBLICAR.md`, `PLAN_SUBIDA.json` |
| 10 | Subida y programación: skill **`youtube-shorts-upload`** | 0 | — |
| 11 | Checklist de monetización (`MONETIZACION.md` §3) | 0 | — |

Los pasos 7 y 11 **no se saltan nunca**: son los mismos chequeos del largo (regla de Agustín en `FORMATOS.md`: la
calidad no baja porque la pieza sea corta).

---

## 6. Lo que cuesta ahora

El modelo viejo costaba **0**: recortaba el master y reusaba la voz ya pagada. El nuevo tiene guion propio, así que
**tiene voz propia**, y la voz es lo único que se paga.

George a ~140 wpm y ≈ USD 0,10 por 1.000 caracteres:

| Pieza | Palabras | Caracteres | Costo |
|---|---|---|---|
| 50 s | ~117 | ~640 | USD 0,06 |
| 90 s | ~210 | ~1.150 | USD 0,12 |
| 180 s | ~420 | ~2.300 | USD 0,23 |
| **4 piezas de 90 s** | ~840 | ~4.600 | **USD 0,46** (≈16 cr PicsArt) |
| **5 piezas de 180 s** | ~2.100 | ~11.500 | **USD 1,15** (≈39 cr) |

Render e imagen siguen a 0 (todo local, arte reusado). Lo que sí crece es el **tiempo**: 3-5 piezas de 50-180 s son
4-9 minutos de animación nueva, un tercio de la coreografía de un episodio.

**Regla 15, actualizada por Agustín el 2026-09-08 por esto mismo: el tope pasa de USD 3 por video a USD 4 por
producción**, un solo techo para el episodio **y sus shorts**. Reparto: voz del episodio 1,74 + imágenes 0,30 +
2 hero con un reintento 0,70-1,00 + **voz de los shorts 0,46-1,15** = 3,20-4,19. Con 5 piezas de 3 min el tope queda
justo: en ese caso se recorta un hero o se pregunta.

---

## 7. Lo que se gana y lo que se arriesga

**Se gana:** piezas que se sostienen solas (hoy el recorte hereda el ritmo del largo, que está pensado para otro
formato); un gancho escrito para el feed y no heredado; la posibilidad de hacer shorts sin tener un episodio detrás;
y series, que es el formato que más rinde en Shorts porque construye hábito.

**Se arriesga, y conviene medirlo:**

1. **Duración contra el dato propio.** Los shorts que rindieron en el canal miden 31-59 s (el mejor del ep. 1, 380
   vistas en 20 min, dura 55 s). En el feed la señal que manda es el **porcentaje visto**, y a 3 min es mucho más
   difícil. Propuesta: 50-90 s por defecto, estirar a 2-3 min solo cuando el tema lo aguante, y comparar en las
   primeras dos tandas. La duración la decide Agustín; esto es el dato, no una objeción.
2. **Un short largo cuenta la idea entera** y le saca la razón para hacer clic al episodio. El corte tiene que seguir
   dejando la pregunta abierta aunque dure 3 minutos.
3. **De 10 a 3-5 se corta la cobertura del calendario a la mitad**: 10 shorts tapaban cinco semanas, 3-5 tapan dos.
   Con episodios quincenales quedan huecos. Los modos B y C existen justamente para eso, pero eso los vuelve trabajo
   fijo del calendario, no algo opcional.

---

## 8. Al subir (2 min por pieza)

1. Subir el MP4. Título y descripción de `PUBLICAR.md`. **Título** (regla de Agustín): palabra-emoción en mayúsculas
   + dos puntos, distinta en cada uno — `FEAR:`, `BOMBSHELL:`, `PANIC:`, `SHOCK:`, `WARNING:`, `COLLAPSE:`, `EXPOSED:`,
   `BETRAYAL:`, `SECRET:`, `ALERT:`. Sin `BREAKING`, sin fechas, sin `Nazi`, y la palabra tiene que cumplirse en la pieza.
2. **Video relacionado** → el episodio (modo A) o la pieza anterior (modo B). Es el único enlace clicable dentro del
   feed de Shorts; sin eso el short es un callejón sin salida.
3. Comentario propio fijado (lo tiene que hacer Agustín: el asistente no puede comentar en su nombre).
4. Idioma inglés, categoría Education, "no es para niños".
5. **Miniatura (corregido el 2026-09-09).** Antes decía "sin miniatura personalizada", y eso dejó de ser
   cierto: **YouTube habilitó miniaturas propias para Shorts el 24 de julio de 2026**, aunque **solo para
   canales del YouTube Partner Program** y con despliegue gradual. Mientras el botón "Subir miniatura" no
   aparezca en Studio, lo que sí está para todos es **elegir entre tres cuadros sugeridos** (escritorio).
   Cada producción deja sus miniaturas 9:16 (< 2 MB) generadas del propio video, listas para el día que
   aparezca el botón: ver `videos/S01_11s/miniaturas.py` como plantilla.
   Ventaja del formato del canal: **el gancho va quemado arriba durante todo el video**, así que cualquier
   cuadro que elija YouTube ya trae el titular. Nunca queda una miniatura muda.
5. A la playlist que corresponda: **Shorts** (modo A y C) o la playlist de la serie (modo B).

**Trampas del formulario de YouTube** (comprobadas subiendo 20):
- El selector de hora solo acepta múltiplos de **15 minutos**. Si las franjas del día están tomadas, publicar directo.
- Al escribir la descripción recién subida, **no pulsar `ctrl+a`**: se escribe como una "a" al principio del texto.
- El `<input type=file>` está oculto; hay que exponerlo por JS para adjuntar el archivo.
- Límite de 10 MB por archivo al subir por navegador: usar las copias de `_up/` (crf 25).
- Para el video relacionado en lote: `document.querySelector('#linked-video-editor-link')`.

---

## 9. Qué medir (a las 48 h)

| Número | Umbral | Qué hacer si falla |
|---|---|---|
| Retención a los 3 s | ≥ 70 % | El gancho no funciona: cambiar las 2-3 palabras de arriba y volver a subir |
| **% visto** | ≥ 60 % | La pieza es larga para lo que cuenta: bajar la duración objetivo de la próxima tanda |
| Clics al episodio / a la pieza siguiente | ≥ 1 % de las vistas | Revisar que el video relacionado esté puesto |
| Suscriptores por pieza | — | Es la métrica real: un short que trae suscriptores vale más que uno con 10× vistas |
| **Piezas 1→N de una serie** | caída < 50 % | Si la 2 pierde más de la mitad de la 1, el encadenado no funciona |

---

## 10. Decisiones de Agustín (2026-09-08) y lo que queda abierto

**Decidido:**
- **Tope: USD 4 por producción**, episodio y shorts en el mismo techo (antes eran 3 por video). Regla 15 actualizada.
- **Sin intro de canal; outro corta pidiendo la suscripción** en cada pieza (§4). Excepción explícita a la regla 4.
- **Duración: 50 s mínimo, el máximo por tema.** Sin default: se propone por pieza y él aprueba.

**Abierto:**
- [ ] **La serie de 11-S**: cuántas piezas, y si desemboca o no en un Dispatch largo del mismo tema (si desemboca,
      las N apuntan al episodio y la serie se vuelve su tráiler).
- [ ] Cobertura del calendario con 3-5 en vez de 10 (§7.3): si las series pasan a ser trabajo fijo entre episodios.

---

## 11. Historial — cómo se hacía hasta el ep. 3 (modelo viejo, 0 créditos)

30 shorts producidos así: **10 por episodio, cortados del master ya renderizado** con `produccion/shorts.py` a partir
de `guiones/<ep>/shorts.json` (rangos de líneas del guion sobre `audio/<ep>.tiempos.json`), reusando voz, música y
animación ya pagadas. ~35 s de render por pieza, 0 créditos. Salida en `produccion/shorts/<ep>/`.

Qué dejó ese modelo, y sigue valiendo:
- Los 10 del ep. 1 y los 10 del ep. 2 subidos y programados con el episodio vinculado (2026-09-08); los del ep. 3, planificados.
- Duraciones reales 31-59 s; el mejor rendimiento, 55 s.
- Pedido de Agustín para videos de actualidad: **al menos el 75 % de los shorts salen el mismo día del episodio**.
- No publicar shorts antes del episodio (no tienen a dónde llevar), no poner cadencia en los textos, no repetir tema
  dos veces seguidas.
- El modo viejo (`shorts.py --de-master`) **se conserva**: sigue siendo la forma más barata de sacar piezas de un
  episodio ya hecho, y para los eps. 1-3 es lo único que hay.
