# CREATIVO — qué le falta a la animación y cómo se mejora muchísimo gastando poco

> 2026-09-08. Pedido de Agustín: análisis de la creación creativa partiendo de lo que hay, TODO lo que hay que mejorar,
> qué mejora muchísimo con mínimo gasto, invertir un poco más de créditos, y cuando se acaben seguir en fal.ai
> **manteniendo siempre el estilo**. "Me gustarían más animaciones atractivas."
> Base: hojas de contacto de los eps. 1 y 2 (68 + 75 cuadros), `motor.py` v2, `ESTILO.md` §2 y §6, `ANIMACION.md` §4,
> precios medidos hoy en PicsArt (`picsart_preflight`) y precios de lista de fal.ai.

---

## 0. Punto de partida: qué tenemos y qué se ve

**Lo que ya funciona** (no se toca): el look de papel sobre la mesa, la paleta de 7 colores, el elenco, los mapas reales,
la voz de George, el sonido sincronizado, el sistema de planos con chequeo de encuadre, el render a 0 créditos.

**Lo que se ve plano**, en orden de lo que más se nota en pantalla:

| # | Qué pasa hoy | Por qué aburre |
|---|---|---|
| 1 | Los personajes aparecen siempre en los mismos dos lugares, a la misma escala, con la misma pose (manos en la cintura), y solo "presentan": no tocan el mapa, no reaccionan, no se miran. Sin boca, sin parpadeo, sin giro de cabeza. | Son muñecos parados al lado de una pizarra. El espectador deja de mirarlos a los 10 s. |
| 2 | Las cosas **aparecen** (pop) y **desaparecen**; nada cae, se desliza, rebota, se pliega o se rompe. | El papel no se comporta como papel. La "física" es lo que hace creíble un recorte. |
| 3 | La cámara solo hace push-in lento y corte duro. No hay barridos, no hay zoom-through, no hay temblor en el golpe. | Cada corte parece un cambio de diapositiva. |
| 4 | Planos de pared: una tarjeta de texto en un vacío crema durante 10-20 s. | Es la pantalla más pobre del video y aparece 6-8 veces por episodio. |
| 5 | Mapa desnudo durante 30-60 s con un pin o una tarjeta. | El mapa es el activo más caro del canal y está muerto la mitad del tiempo. |
| 6 | 112 tarjetas de texto por episodio, todas el mismo rectángulo con la misma entrada. | Monotonía tipográfica; la cifra fuerte y la frase menor pesan igual. |
| 7 | Sin profundidad: mesa, hoja, props y personajes están en el mismo plano; las sombras no se mueven. | Se lee como una imagen plana, no como objetos sobre una mesa. |
| 8 | Los gags son chicos (`fold`, `shake`): 8 en el ep. 1, 23 en el ep. 2. Ninguno "grande". | Nada que se recuerde ni que sirva de miniatura o de primer cuadro de un short. |

Nada de esto es el estilo: Gilliam es rígido **y** se mueve todo el tiempo. Es densidad y física, no técnica nueva.

---

## 1. Nivel 0 · Motor, 0 créditos: es el 70 % de la mejora

Todo esto es trabajo en `motor.py` y en los helpers de coreografía. Ordenado por impacto por hora de trabajo.

### 1.1 Física de papel (un día)
- **Caída y asentamiento**: todo lo que entra cae desde 30-60 px arriba con un rebote (0,35 s) y una rotación residual de ±2° que se estabiliza. Reemplaza al `pop` como entrada por defecto.
- **Salidas con sentido**: deslizar fuera de la hoja, levantar (escala 1,05 + sombra grande + fade), o **arrugar** (escala en X a 0 con giro). Nunca "desaparecer".
- **Flip-in**: tarjetas que entran girando sobre su eje horizontal (escala Y 0→1 con overshoot). Para cifras.
- **Wobble al aterrizar** y **temblor** de la hoja entera en cada stinger (2 px, 0,2 s).

### 1.2 Profundidad (medio día)
- **Cuatro capas con paralaje**: mesa (0,92), hoja (1,0), props (1,04), personajes y tarjetas (1,08). En cada push-in, cada capa se mueve distinto. Es lo que convierte la imagen plana en una mesa.
- **Sombras proyectadas** con offset proporcional a la "altura" de la capa, y que crecen cuando algo se levanta. Hoy la sombra está pintada en el PNG y no cambia.

### 1.3 Cámara (medio día)
- **Barrido** (`whip`) entre regiones del mapa en 0,4 s con desenfoque direccional simulado (3 frames duplicados con offset), en vez de corte cuando el destino está en la misma hoja.
- **Zoom-through**: acercarse a un prop hasta que llena el cuadro y cortar desde ahí al plano siguiente (transición gratis y con energía).
- **Golpe de cámara** (2-4 px, 4 frames) en sellos, dominós y stingers.
- **Encuadres nuevos** con el mismo chequeo: personaje a 0,85 de escala en primer plano medio (`CHR2`), plano contrapicado de la mesa para la apertura de acto.

### 1.4 Personajes vivos (un día en el motor + 2-4 cr en imágenes, §2)
- **Parpadeo** automático cada 3-5 s (párpado = pieza recortada de la misma cabeza, 2 frames).
- **Boca de 2 posiciones** cuando se cita a un líder, movida por la amplitud de la voz (ya tenemos la alineación).
- **Señalar de verdad**: `point(rig, 'Moscow')` resuelve el ángulo de los dos segmentos del brazo hacia `G('Moscow')`. Hoy el gesto es genérico.
- **Reacciones** como curvas reutilizables: retroceder (lean 6°), encogerse de hombros, asentir doble, golpe en la mesa con temblor, mirar al otro personaje.
- **Entrada caminando** (bob vertical 4 px a 2 Hz + inclinación 3°) y **salida** por el borde con `flyout`.
- **Dos personajes que interactúan**: uno entrega un papel al otro (ya existe `hand_card`), uno señala y el otro mira.
- **Escala variable**: 0,62 (hoy), 0,85 (medio cuerpo) y 1,2 (cabeza que asoma desde el borde para un comentario).

### 1.5 Mapa vivo (medio día)
- **Pines que caen** con sombra y rebote; **regiones que se rayan** (hatch) a mano en 0,6 s en vez de aparecer pintadas; **rutas a lápiz** con la punta visible.
- **Barrido día/noche** o de escarcha sobre Rusia como ambiente continuo.
- **Alfileres con hilo rojo** entre dos sitios (el cliché del tablero de detective, encaja con "Follow the paper").
- Regla nueva: **ningún plano de mapa dura más de 6 s sin un evento**; `check` lo reporta.

### 1.6 Tipografía con jerarquía (medio día)
- Tres clases de tarjeta: **cifra hero** (grande, cuenta desde 0 con tick, sello rojo), **frase** (tarjeta actual), **etiqueta** (chica, ocre, sin sombra).
- **Sello que cae** (`stamp`, ya existe) para veredictos; **tira de papel arrancada** para citas; **teletipo** para fechas.
- Máximo 60 tarjetas por episodio (hoy 112): las demás se vuelven objeto o gesto.

### 1.7 Transiciones y sets (medio día)
- **Pasar de página** entre actos (la hoja se levanta por una esquina y debajo está el set siguiente).
- **La pared deja de estar vacía**: cada plano de pared tiene un fondo de set (§2.3) y al menos dos objetos.
- **Las Manos** (recorte que ya existe) colocan objetos en el mapa en los momentos clave: es la firma visual más barata que tenemos y casi no se usa.

**Total nivel 0: 4-5 días de motor.** Es la inversión con retorno compuesto: vale para todos los episodios.

---

## 2. Nivel 1 · Imágenes, 1 crédito cada una (Flux 2 Pro, medido hoy): 15-25 cr una sola vez

| Activo | Cantidad | Créditos | Para qué |
|---|---|---|---|
| **Hojas de expresión** por personaje: cabeza neutra, sorpresa, enojo, sonrisa, ojos cerrados, boca abierta | 6 por personaje × 4 personajes principales (Burócrata, Militar, Ejecutivo, Trabajador) | 4-8 (una imagen por hoja con el workflow `character-sheet`) | Reacciones y boca. Hoy hay una sola cara. |
| **Cabeza de tres cuartos** por personaje | 4 | 4 | Giro de cabeza hacia el mapa o hacia el otro personaje. |
| **Manos**: señalar, sostener, puño, palma abierta | 1 hoja | 1-2 | Señalar de verdad; gestos. |
| **Fondos de set** en papel recortado (los 8 escenarios de `ESTILO.md` §2.5: hangar, torre, sala de negociación, puerto, mina, muro de gráficos, calle, directorio) | 8 | 8 | La pared deja de estar vacía. Reutilizables en todos los episodios. |
| **Props con partes** (avión con ala/motor/tren separables, edificio por pisos, barco por secciones) | 3 | 3 | Gags grandes: desarmar, apilar, hundir. |
| Líderes citados con boca y 3 expresiones (Putin, Zelensky, Trump, Weidel) | 4 | 4 | Vida en las citas. |

Regla de consistencia: cada imagen se genera **con la imagen actual del personaje como referencia** y el bloque de prompt fijo
del estilo (`pruebas/elenco/prompts_lideres.md`), fondo quitado gratis, cortada con `cortador.py`. Un personaje nuevo sigue
costando 1-2 cr.

---

## 3. Nivel 2 · Video generativo, planos "hero": 60-100 cr por episodio

Precios medidos hoy en PicsArt (`picsart_preflight`, sin gastar):

| Modelo | Clip | Créditos | ≈ USD |
|---|---|---|---|
| **Kling V2.6** (t2v/i2v, 16:9) | 5 s | **10** | $0,29 |
| **Seedance 2.0 Fast** (720p, start/end frame) | 5 s | **20** | $0,58 |
| Flux 2 Pro (imagen) | 1 | 1 | $0,03 |
| Hailuo 2.3 Fast, Kling Motion Control V3 | requieren imagen de entrada; cotizar con el primer test | — | — |

Cómo se hace para que **no rompa el estilo** (esto es lo que decide si sirve o no):

1. **Nunca texto → video directo.** Primero un cuadro fijo en nuestro estilo (Flux, 1 cr) construido a partir de nuestros
   propios activos: el rig, el prop, la hoja de mapa. Ese cuadro es el `startFrame`. Si se quiere una acción concreta,
   segundo cuadro = `endFrame` (Seedance) y el modelo **interpola**, no inventa (`ANIMACION.md` §4).
2. **Bloque de prompt fijo** en todos los clips: *stop-motion paper cutout, layered cardboard with visible paper grain and
   cut edges, flat muted palette (cream, ochre, ink, brick red, slate blue), on a wooden map table, soft top light, no
   photorealism, no 3D render, no text.*
3. **Post en el motor, 0 cr**: LUT a la paleta de 7 colores, grano de papel, viñeta, y **borde de papel**: el clip se
   incrusta como una "foto" o "recorte" pegado sobre la mesa, con sombra y una esquina levantada. Así, aunque el modelo se
   desvíe un poco, se lee como un objeto más del mundo, no como otro video.
4. **Tres clips por episodio, 5 s cada uno**, en los tres momentos que más venden: el gancho (segundo 1-6), el giro del
   acto central, el remate. Dos intentos por clip. Presupuesto: 3 × 2 × 10 = **60 cr con Kling**, hasta 100 con Seedance
   donde haga falta control de inicio/fin.
5. **Reusar**: un ciclo bueno (el avión que se pliega, la alfombra roja que se desenrolla, el sello gigante que cae) se
   guarda en `produccion/hero/` y se reutiliza en shorts, miniaturas y próximos episodios.

Qué se prueba primero (con los 54 cr que quedan hasta el 14/09, propuesta): **un solo clip hero** del ep. 1 (el Boeing
canibalizado en el hangar, Kling 2.6, 10 cr, 2 intentos = 20 cr) + hoja de expresiones del Burócrata (2 cr) + 3 fondos
de set (3 cr). Si el clip hero pasa el post de estilo, el pipeline queda validado por 25 cr.

---

## 4. Continuidad en fal.ai cuando se acaben los créditos (mismo estilo, mismo pipeline)

`COSTOS.md` ya validó voz (George, mismo ID), imagen (Flux Pro $0,05) y música en fal.ai. Para video, precios de lista de
fal en 2026: Wan 2.5 desde $0,05/s (480p; $0,10 a 720p), Kling 2.5 Turbo Pro $0,07/s, Kling 3.0 Pro $0,112/s, Veo 3.1
Fast $0,10/s. Un plano hero de 5 s sale **$0,35-0,60**; los tres del episodio con dos intentos, **$2-4**.

Reglas para que el estilo no se mueva al cambiar de proveedor:
- **Mismos activos de entrada** (nuestros cuadros fijos), **mismo bloque de prompt**, **mismo post en el motor**. El proveedor
  solo interpola; el estilo lo ponen la imagen de entrada y el post.
- **Un modelo por tipo de plano** y no cambiarlo: Kling para movimiento de objetos y cámara, Seedance/Wan con start+end para
  gestos de personaje. Se elige en el test de §3 y se anota en la skill.
- Cada clip aprobado guarda `prompt`, `modelo`, `seed`, `startFrame` en `produccion/hero/<nombre>.json`: se puede regenerar
  igual en cualquier proveedor.
- Lo que NO se migra: el render, el chequeo, la mezcla, los shorts. Siguen a $0 en esta máquina.

**Tope inquebrantable de Agustín (2026-09-08): USD 3 por video en fal.ai.** Reparto que entra: voz $1,74 + 6 imágenes $0,30 +
**2 planos hero** de 5 s con un solo reintento (Wan 2.5 720p $0,50 c/u o Kling 2.5 Turbo $0,35 c/u) $0,70-1,00 = **$2,75-3,00**.
El tercer hero y el segundo reintento quedan para PicsArt mientras haya créditos. Si hace falta más, se le pregunta antes.

---

## 5. Presupuesto por episodio con el nivel 2 incluido

| Rubro | Créditos PicsArt | Notas |
|---|---|---|
| Voz George | 60-65 | Guion de 2.200-2.300 palabras |
| Imágenes nuevas (rigs, sets, props) | 5-15 | Los sets y hojas de expresión se hacen una vez |
| Planos hero (3 × 2 intentos) | 60-100 | Kling 10 / Seedance 20 por clip |
| Música nueva (0-2 cues) | 0-6 | Banco reutilizable |
| **Total** | **125-185** | Dos episodios por ciclo = 250-370 de 500. Sobran 130+ para pruebas. |

---

## 6. Orden de trabajo propuesto (antes del ep. 3)

1. **Motor, nivel 0** (4-5 días): 1.1 física → 1.2 profundidad → 1.4 personajes → 1.3 cámara → 1.5 mapa → 1.6 tipografía → 1.7 sets.
   Cada punto se valida con un tramo de 20 s del ep. 1 re-renderizado (`piloto3.py 330 350`), no con un episodio entero.
2. **Imágenes, nivel 1** (un día, 15-25 cr): hojas de expresión de los 4 principales, 8 sets, 3 props con partes.
3. **Test hero** (25 cr, una tarde) con el post de estilo. Si pasa, entra en el ep. 3; si no, se queda en nivel 0 + 1, que ya
   es un salto grande.
4. Recién entonces, ep. 3: guion con `[HERO]` marcado en tres líneas, el resto con el vocabulario nuevo (`drop`, `point`, `whip`,
   `page_turn`, `hatch`, `pin`).

Lo que este plan no cambia: el estilo, la paleta, el elenco, la voz, el render local y el chequeo de encuadre. Cambia la
cantidad de vida por segundo.
