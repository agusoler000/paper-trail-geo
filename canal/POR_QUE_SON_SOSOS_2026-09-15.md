# POR QUÉ SE VEN SOSOS — medido, no opinado

> Escrito el **2026-09-15**. Pregunta de Agustín: *"me da la sensación que la gente se va porque son
> sosos o aburridos. ¿Me equivoco?"*
>
> **No te equivocás. Y ahora hay número.** Lo que sigue está medido sobre los archivos finales con una
> herramienta nueva (`produccion/ritmo.py`, 0 créditos), no sacado de una impresión. Las propuestas de
> §7 en adelante son del asistente y no son regla hasta que las adoptes.

---

## 1. La respuesta, en una línea

**Dos tercios de cada episodio largo son una imagen congelada, y en la mitad del video el 66 % del
cuadro es mesa de madera vacía.** Los cortes están bien (10-11 por minuto, la meta se cumple), pero
entre corte y corte no pasa nada. Un corte cada 4 segundos entre dos imágenes fijas no es ritmo: es un
pase de diapositivas.

Y la prueba de que no es el estilo ni el motor: **tus propios shorts, hechos con el mismo motor y el
mismo arte, dan 85-94 % de ocupación de cuadro contra 34 % de los largos.** Lo vertical te obliga a
cerrar el plano; en horizontal el plano se abre y el contenido queda chico y perdido.

---

## 2. Cómo se midió (reproducible)

```bash
python produccion/ritmo.py <video.mp4> [--contacto]
```

Tres métricas, todas sobre el archivo final:

| Métrica | Qué es | Meta propuesta |
|---|---|---|
| **quietos** | % de muestras (a 4 fps) cuya diferencia con la anterior es < 0,8/255 — imagen congelada | < 20 % |
| **cortes/min** | cambios de plano detectados por salto de imagen | 10-15 |
| **ocupación** | % del cuadro con papel/documento (el resto es mesa) | > 55 % |

El detector de cortes es conservador: encuentra 194 en el ep. 06 y el archivo de eventos tiene 266
`clack` (el sonido del corte). O sea, **subestima** los cortes, lo que hace el hallazgo más fuerte, no
más débil.

---

## 3. Los números

### 3.1 Largos

| Ep. | Duración | quietos | cortes/min | ocupación (mediana) |
|---|---|---|---|---|
| 03 Kiev/Bielorrusia | 16:00 | **53,1 %** | 11,8 ✓ | 65 % |
| 04 Malvinas | 33:12 | **62,8 %** | 11,3 ✓ | — |
| 06 IA economía | 18:26 | **62,2 %** | 10,5 ✓ | **34 %** |

Lo consistente en los tres es **quietos: 53-63 %**. La ocupación varía por episodio (el 03 encuadra
bastante mejor que el 06), y con tres datos no alcanza para cruzarla contra la retención.

Detalle del ep. 06: movimiento **mediano** entre cuadros = 0,55 sobre 255. Es un cambio del **0,2 %**
de la imagen. El plano más largo sin corte: **51 segundos**. En el ep. 04, **62 segundos**.

Y el ep. 04 abre con **30 segundos sin un solo corte** y movimiento 0,73 — el cold open del video más
exitoso del canal es, literalmente, una imagen fija.

### 3.2 La referencia del nicho, con la misma vara

Medido el 15-sep sobre 100 segundos del medio de *Why The Taliban Are Begging The US To Come Back*
(RealLifeLore, 38:51). Es **una sola muestra de un solo canal**, así que vale como orden de magnitud,
no como norma:

| | movimiento mediano | quietos |
|---|---|---|
| **RealLifeLore** | **7,18** /255 | **10,3 %** |
| Ep. 03 | 0,74 | 53,1 % |
| Ep. 04 | 0,61 | 62,8 % |
| Ep. 06 | 0,55 | 62,2 % |

**La imagen de referencia se mueve unas doce veces más que la nuestra**, y tiene cambio perceptible el
90 % del tiempo contra el 38-47 % nuestro. Ésa es, medida, la distancia entre "esto está pasando" y
"esto es una lámina".

Dos advertencias de método: el conteo de cortes no es comparable (ahí da 76,8/min porque el detector
también dispara con zooms y mapas animados, no solo con cortes), y **la ocupación tampoco** (mide
píxeles claros = papel; en un video de paleta oscura da bajo por construcción, no por vacío).

### 3.3 Shorts (mismo motor, mismo arte, mismas manos)

| Pieza | quietos | cortes/min | ocupación |
|---|---|---|---|
| Ep. 06 · `03_2027` | **5,5 %** | 13,7 | **85 %** |
| Malvinas · `03_1833` | 43,3 % | 12,2 | **94 %** |
| Suecia · `01_momika` | 33,1 % | 10,6 | **92 %** |

**La ocupación del cuadro es el corte más limpio del análisis:** 85-94 % en vertical contra 34 % en
horizontal. No es una diferencia de grado, es otra cosa.

Y no es casualidad que los shorts sean lo único que funciona: traen el 88 % de las vistas y los mejores
retienen 24-33 % (`canal/ANALISIS_ITERACION_2026-09-13.md` §1.4).

---

## 4. La prueba que no necesita números

Tres archivos en `pruebas/ritmo/`:

| Archivo | Qué muestra |
|---|---|
| `ep06_4m_tres_cuadros_seguidos.png` | Tres cuadros del minuto 4, separados por 6 segundos. Cambia una tarjetita. El resto es idéntico |
| `ep06_12m30_como_se_ve_en_telefono.png` | El cuadro del minuto 12:30 al tamaño real de un teléfono. El 60 % inferior es madera vacía y el texto casi no se lee |
| `ep06_contacto.png` | 12 cuadros repartidos por el episodio. Siete de doce tienen más de la mitad del encuadre en mesa vacía, el horizonte siempre a la misma altura y los objetos siempre del mismo tamaño |
| `encuadre_antes_despues.png` | El **mismo** cuadro con la cámara cerrada. Sin generar nada nuevo: solo acercándose, se lee y tiene peso |

Cuatro cosas que se ven y ningún número dice:

1. **El horizonte está a la misma altura en los 12 cuadros.** No hay variedad de encuadre: ni un primer
   plano, ni un ángulo, ni profundidad.
2. **Todo tiene el mismo tamaño.** Los personajes, las tarjetas y los objetos ocupan siempre la misma
   fracción del cuadro.
3. **El rojo no aparece nunca.** `ESTILO.md` §2.2 dice que el rojo es el recurso más escaso de la
   paleta — hoy directamente no se usa, y el episodio entero es marrón y crema.
4. **Las tarjetas de texto son chicas.** En el cuadro a tamaño de teléfono, *"AND WHERE IT GOES MISSING"*
   es casi ilegible. Y esas tarjetas son el argumento.

---

## 5. Por qué el checklist no lo vio

Porque mide **cortes por minuto** y los cortes están bien: 10,4 medido por el propio pipeline, 10,5-11,3
medido acá. Verde.

Lo que nadie mide es qué pasa **dentro** del plano. El checklist tampoco mide cuánto del cuadro está
ocupado: la "pasada anti-pantalla-vacía" del ep. 05 cuenta **eventos** (sonidos) y luego "lo visible",
pero visible = hay algún objeto, no = el cuadro está lleno. Un plano con una tarjetita de 200 px en una
mesa de 1920 pasa el chequeo.

**Ése es el agujero: el sistema mide el ritmo del montaje y nadie mide el ritmo de la imagen.**

---

## 6. Dónde coincide con la curva de retención

Cruzando el perfil de movimiento con las curvas leídas el 13-sep (`ANALISIS_ITERACION` §1.3.b):

| Ep. | Dónde se va la gente | Qué mide el ritmo ahí |
|---|---|---|
| 06 | de 2:00 a 3:00 cae de ~70 % a ~40 % | el bloque 2:30-3:00 tiene movimiento **1,22** y **2 cortes** — el más flojo de los primeros cuatro minutos |
| 06 | escalón en ~9:40 | bloque 9:30: movimiento **1,22**, **1 corte** |
| 04 | caída fuerte de 0:34 a 1:10 | el bloque 0:00-0:30 tiene **0 cortes** y movimiento **0,73** |

Con 11 a 163 espectadores únicos por video esto no prueba causalidad — cada espectador pesa 5-10 puntos
de la curva. Pero **las tres caídas conocidas caen sobre los tres tramos más muertos**, y eso ya no
parece casualidad.

---

## 7. Lo que NO es el problema (también medido, para no gastar pólvora)

- **El audio no es.** Ep. 06: nivel medio −29 dBFS, solo **3,2 %** del video tiene huecos de silencio
  real ≥ 0,5 s, y el más largo es de 1,7 s. Hay lecho sonoro y está bien puesto.
- **El largo no es.** El % visto es plano (~28-29 %) con 18 o con 33 minutos (§1.3 del 13-sep).
- **El guion no es** — al menos no es lo primero. El del 11-S tenía el mejor cold open del corpus y
  murió por CTR (0,9 %) y por competir con la BBC el día del aniversario.
- **La voz no es.** George con dirección de actor; nadie se quejó de la voz, y los shorts con la misma
  voz retienen 24-33 %.

---

## 8. La idea: **la pasada de vida**

Cuatro cambios, todos en `produccion/motor.py` y en la coreografía, **todos 0 créditos**, ninguno toca
el guion ni el arte ni la voz. Es render local: lo único que cuesta es tiempo de máquina.

### 8.1 Que nada quede quieto — *deriva permanente de cámara*

Hoy la cámara se mueve solo cuando la coreografía lo pide. Propuesta: **todo plano tiene una deriva
lenta por defecto** (push-in o pull-out de 0,5-1,5 % por segundo, más un paneo mínimo), y la coreografía
solo la sobrescribe cuando quiere otra cosa. Es un valor por defecto en `finalize_cam`, no un rediseño.

Efecto esperado en la métrica: **quietos de 62 % a ~0 %**.

> Nota honesta: `ESTILO.md` §0 descartó "Ken Burns como recurso principal". Esto no es el recurso
> principal, es el **piso**: la animación de recorte sigue siendo la que cuenta la historia. Pero un
> recorte de papel inmóvil sobre una mesa inmóvil, durante 12 segundos, es una foto.

### 8.2 Parallax — **ya está construido y no se está usando**

`Scene.offset()` (motor.py:391) ya desplaza cada capa según su `depth` cuando la cámara se mueve, y
`Rig` nace con `depth=1.06`. O sea: el parallax existe y funciona — **pero solo actúa mientras la
cámara se mueve**, y la cámara está quieta casi todo el video. Arreglado §8.1, esto se enciende solo.
Lo único que queda por hacer es dar `depth` a las capas que hoy no lo tienen (props de primer plano,
tarjetas) para que la profundidad se note.

### 8.3 Que los rigs respiren **más fuerte**

> Corrección a lo que escribí primero en este documento: dije que los personajes estaban congelados
> porque `self.bob` solo se usa al caminar. Eso último es cierto, pero **el idle existe por otro
> lado** y hay que decirlo bien. En `Rig.pose()` (motor.py:230-245):
> la cabeza oscila `1,4°`, cada brazo `1,6°`, y hay respiración de escala `±1,2 %` cada 2,8 s.

El problema no es que falte, es que **es imperceptible**: 1,4° sobre una cabeza de ~60 px son 1,5 px,
y ±1,2 % de un personaje de 300 px son ±1,8 px. En un teléfono, donde el cuadro entra en 405 px de
ancho, eso son **0,3 px**: no existe.

Propuesta: **subir el idle hasta que se vea** — tres a cuatro veces la amplitud actual, desfasado por
personaje para que no respiren todos al mismo tiempo, más un parpadeo cada 3-6 s — y **extenderlo a lo
que hoy no tiene nada**: las tarjetas, los props sobre la mesa y las sombras están 100 % inmóviles, y
ocupan más cuadro que los personajes. Es tocar constantes, no escribir un sistema nuevo.

### 8.4 Cerrar el plano — *la mesa no es el tema*

El dato de §3.2 dice que en vertical ya lo hacés bien sin proponértelo. En horizontal hay que forzarlo:

- **ningún plano por debajo de 55 % de ocupación**; los planos de mesa se cierran hasta que el
  documento mande en el cuadro;
- **tarjetas al doble**, medidas para leerse en un teléfono, no en el monitor;
- **variar la altura del horizonte y la escala** entre planos — hoy son idénticos los 12 cuadros;
- **usar el rojo**: una cifra, una zona, un sello. Hoy es cero.

Esta es la lección que ya aprendieron en el ep. 05 (*"la hoja de mapa tiene que llenar el ancho del
cuadro"*) y que se aplicó **solo al mapa**. Falta aplicarla a los planos de mesa.

### 8.5 Y medirlo

`produccion/ritmo.py` corre en un minuto sobre el archivo final. Propuesta: que sea parte del checklist
de entrega, con las tres metas de §2, igual que el chequeo de precisión del mapa aborta el render.

---

## 9. En qué orden, y qué cuesta

| # | Qué | Costo | Trabajo | Efecto esperado |
|---|---|---|---|---|
| 1 | **Deriva de cámara por defecto** (§8.1) | 0 | ~2 h | `quietos` de 62 % a casi 0, y enciende el parallax que ya existe |
| 2 | **Subir el idle y extenderlo a props y tarjetas** (§8.3) | 0 | ~2 h | Que los recortes dejen de parecer calcomanías |
| 3 | **Cerrar planos + tarjetas grandes + rojo** (§8.4) | 0 | 1 jornada (toca la coreografía) | `ocupación` de 34 % a >55 % |
| 4 | **`depth` a props y tarjetas** (§8.2) | 0 | ~1 h | Profundidad; es lo que hace que parezca caro |
| 5 | **`ritmo.py` en el checklist** (§8.5) | 0 | 20 min | Que no vuelva a pasar sin que nadie lo note |

Todo junto es **una jornada de código, cero créditos**, y aplica a todos los episodios futuros sin
tocar el guion. Salió más barato de lo que parecía porque **casi todo el mecanismo ya está en el motor**
(idle, respiración, parallax, `shake`, `whip`): lo que falta es usarlo y subir las amplitudes.

El plan de ejecución, paso por paso y con los criterios de aceptación, está en
[`canal/PLAN_PASADA_DE_VIDA.md`](PLAN_PASADA_DE_VIDA.md).

---

## 10. Lo que no puedo saber desde acá

- **Si esto es lo que hace que se vayan.** Las tres caídas conocidas coinciden con los tres tramos más
  muertos, pero con 11-163 espectadores la curva es gruesa. Se confirma o se cae con el próximo
  episodio, comparando la curva contra estas métricas.
- **Cuánto vale la referencia.** El dato de §3.2 es **un** fragmento de **un** canal. Sirve para el
  orden de magnitud (12× de movimiento), no para fijar una meta. Con `yt-dlp` ya actualizado, medir
  tres o cuatro canales más son veinte minutos.
- **El CTR sigue siendo el problema de entrada** (0,9-2,5 %). Esto arregla lo que pasa **después** del
  clic. Las dos cosas son independientes y las dos hacen falta.
