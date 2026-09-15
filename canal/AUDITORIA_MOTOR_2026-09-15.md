# AUDITORÍA DEL MOTOR DE VIDEO — diagnóstico, benchmark y plan de mejora (2026-09-15)

> Escrito el **2026-09-15** por el orquestador (Fable) a pedido de Agustín: auditoría completa del
> motor, comparación con GeoGlobeTales, mejoras estructurales, y después rehacer la tanda S12 y el
> ep. 09 con el motor mejorado. **Este documento es el diagnóstico y la especificación**; lo que se
> implementó y cómo quedó está en `canal/AUDITORIA_MOTOR_RESULTADO_2026-09-15.md` (se escribe al final).
>
> Todo lo medido acá se midió con las herramientas del repo (`produccion/ritmo.py`, `ffmpeg`,
> `ffprobe`) sobre archivos reales, y la referencia se bajó y midió hoy (`yt-dlp`, 608×1080, 30 fps,
> 100,9 s, 11,9 M de vistas). Las opiniones están marcadas como tales.

---

## 0. La respuesta corta

1. **El motor no es el problema. El USO del motor sí.** `produccion/motor.py` ya tiene keyframes con
   easing, física de papel, rigs articulados, capas de mapa que se pintan, rutas que se dibujan,
   cámara con zoom/paneo/sacudida/parallax y un chequeo de encuadre que aborta el render. Casi nada
   de eso se ve en los videos, porque la gramática de las coreografías es **"corte a un plano fijo +
   un cartel"** sobre un fondo de papel vacío. El ep. 09 rechazado es el caso límite: 11 de 16
   cuadros son papel cuadriculado con un cartelito.
2. **Tres carencias sí son del motor y son estructurales**: (a) el mundo es un lienzo de 1920×1080 y
   la cámara solo puede acercarse (zoom ≥ 1), así que un mapa grande se ve borroso al cerrar el plano y
   nunca "se recorre"; (b) no hay capa de pantalla (HUD): subtítulos, cifras y rótulos viven en
   coordenadas del mundo y se cortan, se achican y no pueden cruzar un corte; (c) nada verifica que lo
   que se ve corresponda a lo que se dice — el chequeo cuenta objetos, no sentido, y un rótulo de
   20 px "llena" un cuadro vacío.
3. **La referencia gana por densidad y por continuidad, no por dibujo.** Medido con la misma vara:
   10,7 % de cuadros quietos contra 53-63 % nuestros; movimiento medio 9,2 contra 0,55-0,74; el mapa
   ocupa el 100 % del cuadro en los 24 cuadros muestreados; un cambio visible cada 0,2 s de mediana.
4. **La voz no está mal; está dirigida a ser plana.** George tiene rango (VOZ.md lo midió), pero la
   dirección de actor del ep. 09 pide `[flat]`, `[measured]`, `[quiet]`, `[very quiet]` en 60 de 62
   etiquetas, y la de los shorts S12 abre con `[flat, reading an inventory — no emotion]`. La
   referencia narra a **189 wpm**, conversacional, con humor ("Yeah, slavery.") y frases largas que
   corren (18,7 palabras de media). Nosotros: 158 wpm, 10,5 palabras por frase, todo "golpe seco".
5. **Lo que hay que construir es una jornada de motor, no un motor nuevo**: mundo grande + cámara
   libre + HUD + vida por defecto + auditoría guion→imagen + mapa v2 como biblioteca. Todo a 0 créditos.

---

## 1. Cómo funciona hoy el sistema (arquitectura leída, no supuesta)

```
guion.md (A:/V: por beat)
   │
   ├─ voz_ep.py / voz_corta.py: dirección de actor (direccion.py) → eleven-v3 George (fal o PicsArt)
   │      → beats mp3 → alinear: concat + bloques de acto 4,4 s + whisper small.en (35 min CPU)
   │      → audio/voz.wav + audio/tiempos.json (línea → inicio/fin) + audio/_palabras.json (palabra → t)
   │
   ├─ arte/: mapa.py (Natural Earth 50m → hoja Mercator PNG + pts.json), props_NN.py (PIL), rigs pagos
   │
   ├─ coreo.py (por producción, 400-1.300 líneas): build() → Scene
   │      · SH = diccionario de PLANOS (centro, zoom) sobre un lienzo fijo de 1920×1080
   │      · cut(t, plano) + push 5 % por plano; cards/props/rigs colocados por fracción de la ventana
   │      · pasadas automáticas: insertos de ritmo, rellenar_huecos, post-pass de encuadre,
   │        solape (regla 22), rótulos de plano, "rellenar vacíos" (etiqueta de región)
   │      · check: check_framing (aborta), check_geo (aborta), report (huecos/cortes), hoja de contacto
   │
   ├─ motor.py: Track / Obj / Rig / MapSheet / Scene → render(t) por cuadro con PIL, pool de 20 procesos
   │      → _frames/f_%06d.jpg → ffmpeg h264 crf 19 + mezcla2.py (voz + cues Lyria + sfx sintetizados)
   │
   ├─ shorts: armar.py mete el cuerpo 16:9 (1000×563) en una hoja vertical 1080×1920 con gancho fijo
   │      arriba, subtítulos por línea (tiempo repartido por caracteres), barra ocre, cierre.py
   │
   └─ entregar.py: intro v3 (12,5 s) + cuerpo + outro (20 s); master 1440p para subir
```

**Dónde se decide qué aparece en cada momento:** a mano, en `coreo.py`, línea por línea del guion
(`L(b,i)`, `E(b,i)`), con un `V:` del guion como guía no verificada. No hay ningún paso que compruebe
que la línea "Japan holds one point one three trillion" tenga en pantalla Japón y 1,13 T.

**Dónde se decide el ritmo:** en `finalize_cam()` (push por plano) y en las pasadas de relleno, que
miran **eventos sonoros** y **cantidad de objetos**, no lo que se ve.

---

## 2. Qué está mal, con evidencia

### 2.1 Del motor (`produccion/motor.py`)

| # | Carencia | Evidencia | Efecto |
|---|---|---|---|
| M1 | **El mundo mide 1920×1080 y el zoom solo cierra** (`Scene.window` devuelve el cuadro entero si `zoom ≤ 1,005` y `render` recorta del lienzo del cuadro) | `motor.py:375-388, 413-423` | Un mapa a pantalla completa se ve borroso al cerrar (upscale ×2-4); no se puede "abrir" más que el cuadro; la cámara no recorre nada. La prueba de vida de la S12 tuvo que meter la hoja de 3000 px en 1920 y perder la mitad de la resolución. |
| M2 | **`MapSheet` se dibuja entera cada cuadro y se rota entera** (`_sheet` + `resize` + `rotate` por frame) | `RETOMAR.md` del ep. 09: 65 % del tiempo de render es `MapSheet.draw`, 61 % de eso es `rotate` | Render de 16 min = ~97 min de máquina. Y todo lo demás se dibuja sobre el lienzo completo aunque la cámara mire un cuarto. |
| M3 | **No hay capa de pantalla (HUD)** | `prueba_vida.py::encamara/sub` tuvo que emular subtítulos anclados a cámara con un keyframe cada 0,1 s y partirlos en cada corte | Subtítulos, cifras, rótulos y tarjetas de acto viven en coordenadas del mundo: se cortan al cambiar de plano (post-pass los apaga), se achican con el zoom (`size/zz()`), no pueden cruzar un corte. |
| M4 | **Cámara quieta por defecto** | push = % por plano (`z → z·1,05` repartido en todo el plano): 0,13 px/cuadro en un plano de 30 s; `Scene.offset` (parallax) solo actúa si la cámara se mueve | 53-63 % de cuadros congelados en los eps. 03/04/06; el cold open del ep. 04 (30 s) es una foto. |
| M5 | **La vida de los rigs es imperceptible y los props no tienen ninguna** | `Rig.pose`: cabeza ±1,4°, brazos ±1,6°, respiración ±1,2 % (1,5 px en pantalla, 0,3 px en un teléfono); `Obj.wobble = 0` por defecto; `phase` casi igual entre rigs (todos respiran a la vez) | Los recortes se leen como calcomanías. |
| M6 | **Resolución y formato clavados** (`W,H=1920,1080` globales usados en `Rig.enter/exit`, `Obj.slide_off`, `Scene`) | `motor.py:21` | No se puede renderizar vertical nativo. Los shorts nacen 16:9 y se meten en una hoja: el video ocupa **1000×563 de 1080×1920 = 27 % del área** de la pantalla del teléfono. |
| M7 | **`Track` no admite un keyframe en t = 0** (gana siempre el valor inicial) | lección del ep. 05, repetida en el 07 | Cada coreo lo parchea a mano (`M.Track(v)` en vez de `set(0, v)`). Es una trampa de motor, no un rasgo. |

### 2.2 De la gramática de las coreografías (todas las producciones)

| # | Decisión heredada | Evidencia | Efecto |
|---|---|---|---|
| C1 | **El fondo es papel/mesa vacía; el mapa es una hoja que aparece a veces** | `fondo_piloto.png` (grilla + madera), `mp.reveal` solo en `MAPA_PLANOS`; ep. 06: mediana de ocupación 34 %; ep. 09: 11/16 cuadros son grilla + cartel | Agustín, 15-sep: *"el fondo es horrible, una cosa blanca con líneas, super aburrida, 0 animación, 0 mapas"* |
| C2 | **Plano fijo + cartel** como unidad narrativa | ep. 09 `coreo.py`: 140 `card()` y 41 `cut()` para 222 líneas; 3 rigs en 16 min | Un "PowerPoint con sombras". |
| C3 | **Los cortes no cambian el contenido, cambian el encuadre de lo mismo** (WIDE→WALL→WIDE) | `insertos()`/`rellenar_huecos()` cortan al plano contenedor y vuelven | La métrica de cortes/min da verde (10-12) y el ojo ve la misma imagen. |
| C4 | **Las cifras van en tarjetas chicas medidas para un monitor** | `pruebas/ritmo/ep06_12m30_como_se_ve_en_telefono.png`: ilegible a 405 px | El argumento (el número) no se lee donde se mira (teléfono/TV lejos). |
| C5 | **El rojo no se usa**; la paleta es marrón y crema | `POR_QUE_SON_SOSOS` §4 | Nada está "en disputa" visualmente. |
| C6 | **Shorts: gancho fijo arriba durante toda la pieza + cuerpo 16:9 chico** | `shorts.py::fondo` | El gancho compite con el video 90 s seguidos; el video es un cuarto de la pantalla. |

### 2.3 De la sincronía guion → imagen (el problema CRÍTICO)

| # | Hallazgo | Evidencia |
|---|---|---|
| S1 | **Nadie verifica la correspondencia.** `check` verifica: nada cortado, puntos del mapa exactos, huecos sin evento, cortes/min. **No verifica** que lo que se ve sea lo que se dice. | `coreo.py::check`, `Scene.report` |
| S2 | **El detector de vacío cuenta el rótulo de plano y la etiqueta de región como contenido.** | ep. 09: *"rellenos contra pantalla vacía: 3 · tramos que quedan: 0"* con 24 s vacíos en el acto II |
| S3 | **Los `V:` del guion no se usan.** Son prosa libre; la coreo los interpreta a mano y nadie compara. | `guion.md` beat 3: `V: [CARD] $120,000 per person` — la cifra se cambió en el guion v2 (74.000 $/s) y el `V:` quedó viejo |
| S4 | **La alineación línea↔tiempo es buena** (mediana de anclajes, red de seguridad) pero el subtítulo de los shorts reparte el tiempo por caracteres, no por la palabra real. | `shorts.py::cues` |
| S5 | **Las cifras habladas no se cruzan contra las cifras en pantalla.** El ep. 09 v1 dijo "22 cents" con "AND 78 CENTS" en pantalla. | `ERRORES_EP09` §1.a |

### 2.4 De la voz

| # | Hallazgo | Evidencia |
|---|---|---|
| V1 | **La dirección pide monotonía.** Etiquetas del ep. 09 (`direccion.py`): 62 etiquetas, de las cuales `flat/measured/quiet/very quiet/low/clipped/dry/same tone` = 54. La S12 abre las cuatro piezas con `[flat…]`, `[low…]`, `[dry…]`, `[low…]`. | `direccion.py`, `voz_corta.py::APERTURA` |
| V2 | **Ritmo**: George a 158 wpm en el ep. 09 (medido en `tiempos.json`), frases de 10,5 palabras, máximo 22. Referencia: **189 wpm**, 18,7 palabras/frase, mínimo 2 y máximo 39: corre y frena. | `geoglobe.en.vtt` |
| V3 | **Sin humor ni conversación.** La referencia: "But let's start from the beginning", "Yeah, slavery.", "Funny enough". Nosotros: registro de "recibo leído en voz alta". | transcripciones |
| V4 | **Nivel**: ep. 06 a −29 dBFS medio; la referencia integra **−14,5 LUFS, LRA 2,1** (muy comprimida). YouTube baja lo fuerte pero **no sube lo flojo**: nuestros largos suenan más bajos que los vecinos del feed. `entregar.py` no normaliza. | `POR_QUE_SON_SOSOS` §7, `ffmpeg ebur128` |
| V5 | **`stability 0.5`** siempre. eleven-v3 tiene tres modos (creative/natural/robust); nunca se probó el creativo para shorts. | `voz_ep.py::pedir` |
| V6 | Lo que sí funciona y se conserva: George (rango medido), etiquetas entre corchetes, pausa antes de cada revelación, segunda voz para los actos, bloques de acto fijos. | `VOZ.md` |

### 2.5 De la producción y el proceso

- **Render lento** (97 min para 16 min) → menos iteraciones → se entrega lo primero que sale.
- **La hoja de contacto de `check` engaña** (usa `sc.render` de la previsualización; ya está anotado).
- **Cada coreo copia 600-1.300 líneas** de la anterior; las lecciones se pierden (el ep. 07 nació sin
  tres correcciones del 06, el 08 sin tres del 07). Lo que sea regla debe vivir en el motor.
- **`ritmo.py` no está en el checklist** (existe desde hoy).

---

## 3. La referencia, desmontada (GeoGlobeTales · «How America Bought Louisiana» · 101 s · 11,9 M)

Medido hoy sobre el archivo (`scratchpad/ref/geoglobe.mp4`, `contacto24.png`, `geoglobe.en.vtt`):

| Área | Qué hace, exactamente |
|---|---|
| **Hook** | La primera frase ES el giro completo: *"offered to buy just one city, but somehow ended up buying the entire Louisiana territory for almost the same price"*. Después: *"But let's start from the beginning."* Cero preámbulo, cero nombre de canal. |
| **Primeros segundos** | Mapa a sangre desde el cuadro 0 con un barco cruzando el Atlántico y los dos diplomáticos arriba; la cámara ya se mueve. |
| **Ritmo de edición** | 66,5 cambios/min por el detector; **mediana 0,2 s entre cambios**, p90 2,5 s, máximo 4,8 s. No son 66 cortes: es que **siempre** cambia algo (cámara, color, subtítulo, objeto). |
| **Duración de escena** | Escenas de contenido de 1,5-4 s; dentro de cada una la cámara viaja. |
| **Cámara** | Zoom y paneo **continuos**, easing suave; el corte cambia de CONTENIDO (mapa Europa → mapa Caribe → satélite → foto real → mapa), no de encuadre del mismo contenido. Nunca un salto seco dentro de la misma vista. |
| **Mapas** | **Es el fondo el 100 % del tiempo.** Océano teal saturado, tierra kaki con relieve, países pintados de color plano por ROL (Britain rojo, France azul, Spain naranja, USA cian, Haití verde), rotulados **sobre** el territorio. El cambio de color narra (Louisiana pasa de azul a cian = la compra). |
| **Transiciones** | Sin efectos: corte seco entre contenidos distintos, o viaje de cámara. Un globo de pensamiento como inserto. |
| **Composición** | Personajes chibi de pie **sobre el mapa**, en grupos, haciendo algo (barco, pizarra, playa); props que cargan el dato (barriles bajando el Misisipi, maletín `$15M`, cartel `FOR SALE`). |
| **Tipografía / texto** | Subtítulo palabra a palabra (grupos de 2-4), sans blanca con borde oscuro, ~55 % de altura, cambia cada ~0,3-0,6 s. Rótulos de países en el mapa. Cifras grandes como prop (`$15M`, `$10M`). |
| **Jerarquía** | Una idea por cuadro: el color, o el personaje, o la cifra. El subtítulo siempre. |
| **Imagen / video** | Mezcla deliberada: mapa ilustrado + satélite real + foto real (playa, plantación). Chiste visual de choque. |
| **Motion graphics** | Ruta del Misisipi que se dibuja con barriles; barcos que cruzan; soldados que aparecen; banner `BIG LAND. BIG DISCOUNTS`. |
| **Sonido** | −14,5 LUFS integrados, LRA 2,1 (comprimido, parejo), música de fondo continua, marcas `[music]` en el subtítulo automático. |
| **Sincronía** | Cada frase tiene SU imagen: "one city" → el punto rojo en Nueva Orleans; "the same price" → Luisiana entera se pinta; "Saint-Domingue" → la cámara baja a Haití; "yellow fever" → soldados amarillos. |
| **Densidad** | 24 de 24 cuadros muestreados con mapa + al menos un elemento encima. Cero cuadros de "solo texto". |
| **Tensión / storytelling** | Estructura: giro → "empecemos por el principio" → causa (Haití) → consecuencia (Luisiana no sirve) → jugada (10 M por una ciudad) → sorpresa (15 M por todo) → remate (4 cents an acre). |
| **Voz** | 189 wpm, conversacional, frases largas encadenadas con "and/but/so", remates cortos ("Yeah, slavery."). |

**Lo que NO copiamos** (identidad Paper Trail, decisión previa de Agustín): personajes chibi (tenemos
18 rigs pagos), fotos reales mezcladas (rompen la paleta de papel), el tono de historieta. **Contamos
una cuenta, no un cuento**: el objeto central sigue siendo el documento.

---

## 4. Benchmark (nuestro sistema vs. referencia)

| Área | Nuestro sistema (medido) | Referencia (medido) | Gap | Prioridad |
|---|---|---|---|---|
| **Hook** | Intro de preguntas 30 s + intro general 12,5 s antes del cuerpo (largos); shorts abren con la cifra | El giro completo en la frase 1; mapa en movimiento desde t=0 | Medio (largos), bajo (shorts) | 3 |
| **Animación** | Mecanismos existen; uso: cartel que cae, rig que gesticula ocasional | Todo se mueve todo el tiempo: mov. medio 9,2 vs **0,55-0,74** | **×12** | 1 |
| **Mapas** | Hoja sobre la mesa, aparece a veces (34 % ocupación mediana en el 06; 3/16 cuadros en el 09) | Fondo el 100 % del tiempo, coloreado por rol, rotulado | **Enorme** | 1 |
| **Ritmo** | 10-12 cortes/min entre imágenes fijas; 53-63 % quietos | 66 cambios/min; 10,7 % quietos; mediana 0,2 s | **×6** | 1 |
| **Densidad visual** | 1 objeto + 1 cartel por plano sobre vacío | Mapa + personajes + prop + subtítulo | Grande | 1 |
| **Transiciones** | Corte + push 5 %; whip ocasional; velo de acto | Corte de contenido; viaje continuo | Grande | 2 |
| **Narración** | 158 wpm, "golpe seco", dirigida a plano | 189 wpm, conversacional, humor, contraste | Grande | 2 |
| **Sincronía voz/imagen** | Alineación buena; correspondencia no verificada; subtítulos por línea | Cada frase con su imagen; subtítulo por palabra | Grande | 1 (crítico) |
| **Motion graphics** | Cartas de papel, sellos, `secuencia()` de cuadros | Rutas, barriles, banners, cifras-prop | Medio | 2 |
| **Storytelling** | Actos fijos, 11 beats, cliffhangers; tesis fuerte | Giro → causa → jugada → remate | Bajo (es nuestra fuerza) | — |
| **Sonido** | Cues Lyria + sfx sintetizados; nivel bajo (−29 dBFS) y sin normalizar | −14,5 LUFS, LRA 2,1, música continua | Medio | 3 |
| **Packaging** | CTR 0,9-2,5 %; miniaturas con 5-6 elementos | (no medible desde el archivo) | Grande, fuera de este alcance | ver Studio |

---

## 5. Principios que se trasladan (no una copia)

1. **El mapa es el mundo y la cámara vive dentro.** Siempre hay un suelo con información (mapa
   coloreado por rol, o una superficie con sentido); nunca papel vacío.
2. **Cada frase tiene su imagen, y la imagen cambia con la frase.** Corte de contenido, no de encuadre.
3. **La cámara nunca está quieta; cada movimiento va hacia lo que se está diciendo.**
4. **El color narra**: pintar un país cuando la voz lo nombra es decir sin palabras.
5. **La cifra es un objeto grande y legible a 405 px**, no una etiqueta.
6. **Subtítulo palabra a palabra** con la palabra clave en rojo (ya tenemos los tiempos de whisper).
7. **Los personajes están de pie sobre el mapa haciendo algo** (nuestros rigs, no chibi).
8. **La voz corre, frena y respira**: contraste, no llanura.
9. **Todo se verifica por código antes de renderizar**, incluida la correspondencia guion→imagen.

---

## 6. Plan de mejora — ESPECIFICACIÓN para el motor v4 (lo implementa un agente Opus 5)

Regla de no regresión: las producciones existentes (`videos/0*/coreo.py`, `videos/S0*/coreo.py`)
tienen que seguir importando `motor` y construyendo sin cambios de resultado (mismo `check`). Todo lo
nuevo es opt-in salvo donde se indica "por defecto".

### 6.1 `produccion/motor.py` v4

**A. Formato por escena, no global.**
- `M.W, M.H` siguen existiendo (compatibilidad), pero `Scene.__init__(fondo, size=None)` toma el
  tamaño del cuadro de `size` o de `M.W, M.H`. Todo lo que hoy usa `W`/`H` del módulo dentro de
  `Rig.enter/exit`, `Obj.slide_off`, `Scene.window/offset/render` pasa a leer `self.W/self.H` de la
  escena (a `Rig`/`Obj` se les inyecta la referencia al añadirse con `Scene.add`, o reciben `W,H` por
  parámetro con default al módulo). `M.set_formato(w, h)` cambia los globales para las coreos que
  los usan como constantes. `render()` toma el tamaño del primer cuadro.

**B. Mundo grande + cámara libre.**
- Nueva clase `Mundo`: superficie de fondo **más grande que el cuadro**. `Mundo(base_png,
  pts_json=None, meta=None)`; atributos: `base` (RGB), `w,h`, `pts` (px de mundo), `layers=[(RGBA,
  Track alpha, modo)]` (capas de país: `add_layer(png, t_on, dur, mode='fade'|'wipe', t_off)`),
  `routes` (como `MapSheet.route`, dibujadas solo dentro de la ventana), `dark` (Track).
  Método `crop(t, box) -> RGBA` que recorta `base` a `box` y compone SOLO el recorte de cada capa
  activa (nunca la capa entera). `P(name)` devuelve px de mundo. `Mundo.from_v2(...)` construye una
  hoja con `produccion/mapa_v2.py` (ver 6.3) y guarda el `pts.json` con la proyección.
- `Scene(fondo | Mundo, size=...)`: si recibe un `Mundo`, `self.WM, self.HM = mundo.w, mundo.h`;
  si recibe un PNG, `WM,HM` = su tamaño (puede ser mayor que el cuadro). Lo viejo (1920×1080) queda igual.
- `Scene.window(t)`: ventana en coordenadas de mundo. `zoom` = ancho del cuadro / ancho de ventana
  medido en px de mundo **del cuadro**: `w = W/zoom`. Se permite `zoom < 1` hasta
  `zmin = max(W/WM, H/HM)`. Se sujeta el centro dentro del mundo. El caso `zoom ≤ 1,005` con mundo
  = cuadro sigue devolviendo el cuadro entero (compatibilidad).
- `Scene.render(t)`: **recorta el fondo a la ventana y dibuja solo lo que interseca la ventana**
  (`bbox` contra la ventana con margen), con el offset `(-x0, -y0)` sumado al de parallax; después
  `resize((W,H), LANCZOS)`. Para mundo = cuadro y zoom = 1 el resultado tiene que ser idéntico al de hoy
  (verificar con un cuadro del ep. 06 o de la S12: diferencia media < 1/255).
- Regla de nitidez: un mundo de 4000 px de ancho a zoom 2,08 se ve a 1:1; la coreo decide cuánto abre.

**C. HUD (capa de pantalla).**
- `Scene.hud = []`; `Scene.add_hud(*objs)`. Se dibujan DESPUÉS del recorte/resize, en px de cuadro,
  sin parallax ni deriva. `check_framing` los verifica contra `(0,0,W,H)`. Sirven para: subtítulos,
  cifras grandes, rótulos de plano, tarjetas de acto, chip `PART n OF N`, barra de progreso.
- `Scene.subtitulos(palabras, grupos=(2,4), estilo=...)`: helper que arma objetos HUD a partir de la
  lista `[(palabra, t0, t1)]` (formato de `_palabras.json`), agrupando 2-4 palabras por corte natural
  (puntuación, pausas > 0,25 s), sin dejar palabras débiles al final (reusar `shorts.py::DEBILES`),
  con `resaltar` (palabras en rojo) y dos estilos: `'banda'` (banda oscura translúcida + crema, como
  `prueba_vida.sub`) y `'papel'` (tarjeta de papel, como `shorts.py::banda_sub`). Posición por
  fracción de alto (`fy`), tamaño por fracción de ancho.

**D. Cámara viva por defecto.**
- `Scene.vida = {'push': 0.010, 'push_max': 0.14, 'deriva': 9.0}` (velocidad de zoom por segundo,
  tope y deriva lateral en px de cuadro). Se aplica en `window(t)` **desde el último keyframe de
  cámara** (hold) hasta el siguiente, alternando el sentido por índice de keyframe. `Scene.vida=None`
  la apaga. Si una coreo ya calcula su propio push (S12), da lo mismo: manda el keyframe explícito
  (el vida-push se aplica solo en tramos `hold`).
- `Scene.viaje(t0, t1, xy, z, e='io')` (alias de `cam`) y `Scene.corte(t, xy, z)` (hold en t-0,001
  + valor en t). Documentar: "un plano = corte + UN viaje motivado".
- `Track`: arreglar M7: `set(0, v)` reemplaza el keyframe inicial en vez de convivir con él.

**E. Vida en rigs y objetos (por defecto, calibrado para verse a 405 px).**
- `Rig.pose`: cabeza `4,0°`, brazos `4,5°`, respiración `±3 %`, **fase por rig** (`hash(nombre)`),
  y un micro-cabeceo cada 3-6 s. `Rig.vida = 1.0` multiplica todo (0 = quieto).
- `Obj`: `wobble = 0.35` (grados) y `bob = 1.0` (px) por defecto en objetos no-bg, fase aleatoria
  por objeto; `bg=True` → 0. `depth`: props 1,03 (como hoy), tarjetas HUD sin parallax.
- Comprobación de aceptación: dos cuadros separados 1 s de un rig quieto tienen que diferir a simple
  vista en la hoja a 405 px.

**F. Detector de vacío honesto.**
- `Scene.visible(t, ignorar=('rotulo:', 'region:', 'sub:'))` → objetos no-bg visibles en la ventana
  cuyo nombre no empiece por los prefijos ignorados. El relleno de región/rótulo **no cuenta como
  contenido**.

### 6.2 `produccion/sync.py` — auditoría guion → imagen (NUEVO, obligatoria)

`python produccion/sync.py <coreo_module> <tiempos.json> [--pts pts.json] [--out _qc/]`
(o llamado desde `coreo.py check` con la escena ya construida):

1. Para cada línea `A:` de `tiempos.json`: muestrea en `inicio+0,3`, centro y `fin-0,3`; registra
   ventana de cámara, objetos visibles (nombres), textos en pantalla (`card:`, `sello:`, `sub:`,
   HUD), capas de mapa activas, si hay mapa visible.
2. Escribe `_qc/sync.md`: tabla `t | línea | plano | qué se ve | textos | banderas` y una hoja
   `_qc/sync_%02d.jpg` con **un cuadro real (`sc.render`) por línea** (6 por fila, con el texto de
   la línea impreso debajo) — es lo que se mira antes de renderizar.
3. Banderas automáticas (cuenta y lista):
   - `VACIO`: > 0,8 s dentro de una línea sin ningún objeto visible que cuente (6.1.F).
   - `CIFRA_SIN_PANTALLA`: la línea contiene una cantidad (dígitos o números en letras: reusar el
     parser de `guiones/checklist.py`) y ninguna tarjeta/prop/HUD visible en `[inicio-1,5, fin+1,5]`
     contiene esos dígitos (normalizados: `1.13T` ≡ `1,13 trillion` ≡ `1130000000000` por magnitud).
   - `LUGAR_SIN_MAPA`: la línea nombra un sitio de `pts.json` (o una lista extra de topónimos) y el
     punto no está dentro de la ventana durante la línea (si hay mapa).
   - `TEXTO_VIEJO`: un texto en pantalla nacido hace > 12 s sigue visible (salvo HUD permanentes).
   - `PROP_HUERFANO`: un objeto aparece en una línea cuyo texto no lo menciona ni el `V:` del beat lo
     pide (aviso, no aborta).
4. Umbral: `VACIO = 0` obligatorio para renderizar; las demás se listan y el operador decide.
   `coreo.py` de las producciones nuevas aborta si `VACIO > 0`.

### 6.3 `produccion/mapa_v2.py` — el mapa como biblioteca (NUEVO, sale de `videos/09_deuda_eeuu/arte/mapa_v2.py`)

- `hoja_v2(lon0, lon1, lat0, lat1, w, roles={ISO: rol}, agua=[...], etiquetas=True, sitios={nombre: (lon,lat)},
  ss=2, seed=9, rotulos_pos={}) -> (img RGB, meta)` con `meta = {bbox, w, h, px_por_grado, pts: {nombre: [x,y]}}`.
  Lo mismo que hoy (océano teal + orilla + relieve procedural + rótulos sobre el territorio + grano)
  y además: `pins(sitios)` opcional (punto + etiqueta) y `capa_pais(iso_o_nombre, color, alpha) -> RGBA`
  para pintar países después (mismo polígono, encaja al píxel).
- Paleta V2 (del mismo archivo): `OCEANO (70,142,152)`, `ORILLA`, `TIERRA (190,178,136)`, roles
  `deudor` rojo, `acreedor` ocre, `institucion` azul, `sujeto` celeste, `tercero` verde. **Se conserva
  la regla del rojo: un rojo por plano.** Papel, tinta y grano: los de `props.py`.
- `mundo(bbox, w, ...) -> Mundo` que guarda `assets/mundo_<nombre>.png` + `_pts.json` + `_meta.json`.
- Comprobación obligatoria heredada: cada sitio cae a < 3 px de su proyección (regla 24) y se imprime.

### 6.4 `produccion/shorts.py` / armado vertical

- **Formato vertical nativo** para las producciones nuevas: el motor renderiza 1080×1920 (6.1.A) con
  el mundo y el HUD; `armar.py` deja de meter el cuerpo en una hoja: solo pega gancho (HUD, primeros
  3-4 s, grande, con la línea roja), chip `PART n OF N`, barra de progreso, subtítulos palabra a
  palabra (HUD), música + `loudnorm`, y el `cierre.py`. Lo viejo (`--marco`) queda para reproducir
  entregas anteriores.
- `cues()` de `shorts.py`: si existe `_palabras.json`, los tiempos salen de las palabras reales, no
  del reparto por caracteres.

### 6.5 Voz

- `voz/prosodia.py` (NUEVO): mide sobre un wav + tiempos.json: f0 mediana y rango p10-p90 en
  semitonos (autocorrelación numpy, como VOZ.md), wpm por línea y su desvío, pausas ≥ 0,25 s (cantidad,
  media, sd), energía RMS por línea y su rango. Imprime por beat y global, con un **índice de
  contraste** (0-100) = combinación normalizada de rango tonal, sd de wpm y sd de pausas. Sirve para
  comparar la voz vieja del ep. 09 (existe en `audio/voz.wav`) con la nueva.
- **Dirección**: regla nueva de contraste (propuesta del orquestador, no de Agustín): en cada beat,
  **no más de dos líneas seguidas con la misma familia de etiqueta**; cada beat tiene un arco
  (sube → aterriza → suelta); las revelaciones siguen bajando la voz (regla del canal), pero lo que
  las rodea sube: `[curious]`, `[amused]`, `[leaning in, faster]`, `[excited]`, `[surprised]`,
  `[wry]`, `[emphasis]`, y mayúsculas para una palabra clave. Interjecciones conversacionales cortas
  permitidas en el guion ("Yes, that one.", "Look at it again.") sin cambiar los datos.
- **Timestamps de fal**: `voz_ep.py::generar` y `voz_corta.py` piden `timestamps: True` y guardan
  `beat_XX.json`; `alinear` usa esos tiempos (carácter → palabra) si existen y **no corre whisper**
  (35 min menos por episodio y tiempos exactos). Whisper queda de respaldo (PicsArt).
- **Nivel**: `entregar.py` y `armar.py` terminan con `loudnorm=I=-14:TP=-1.5:LRA=9` sobre el master;
  `mezcla2.py` aplica un compresor suave a la voz (`acompressor` 3:1 sobre −18 dB) antes de mezclar.
- `stability`: 0,5 en largos (natural); probar 0,0 (creative) en un short y medir con `prosodia.py`.

### 6.6 Ritmo en el checklist

- `produccion/ritmo.py --json` y una función `veredicto(path)`; `coreo.py` de las producciones nuevas
  lo corre sobre el cuerpo recién renderizado e imprime PASS/FAIL: **quietos < 20 %, movimiento
  mediano ≥ 2,5, sin plano > 6 s sin cambio**. La "ocupación" no aplica al mundo de mapa (mide papel).

### 6.7 Lo que NO se toca

Guion (salvo interjecciones de dirección), fuentes, postura, intro v3 y outro, paleta de papel/tinta
para los objetos, reglas 1-28 de Agustín, formato Dispatch/Brief, el radar y THE LEDGER.

---

## 7. Orden de ejecución

1. Motor v4 (6.1-6.6) por un agente Opus 5 + prueba de regresión (ep. 06/S12 `check` igual) +
   prueba de 25 s (la Ceuta de `prueba_vida.py`) reescrita sobre el motor nuevo, medida con `ritmo.py`.
   **Auditoría del orquestador** antes de seguir.
2. Tanda **S12** (4 shorts) con el motor v4, vertical nativo, mundo de mapa por pieza: voz fal con
   timestamps (~USD 0,43), coreografía nueva, `sync.py` con 0 VACIO, render, armado, cierre, ficha.
   Auditoría pieza por pieza (hoja de sync, ritmo, cuadros reales a 405 px).
3. **Ep. 09** con el motor v4: dirección de voz reescrita (contraste), voz nueva (~USD 1,6),
   coreografía nueva (mundo EE. UU. + acreedores + mundo), `sync.py`, render, entrega con `loudnorm`.
   Auditoría completa.
4. Resultado, pendientes y evaluación honesta contra el benchmark en
   `canal/AUDITORIA_MOTOR_RESULTADO_2026-09-15.md`; skill `paper-trail-video` actualizada.

Costo total previsto: **≈ USD 2,1** en voz (dos producciones, cada una muy por debajo del tope de 4).
Imágenes: 0 créditos (todo dibujado o ya pagado).
