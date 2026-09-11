# INTRO y OUTRO del canal (genéricas, para todos los videos)

> **Decisión de Agustín (2026-09-07):** todos los videos llevan una intro corta que presenta el canal y una
> outro que motiva a suscribirse. **Son del canal, no del episodio**: no llevan mapa del tema ni cliffhanger.
> Se rinden UNA vez y se pegan por delante y por detrás de cada episodio.
> Deroga la regla "nunca *suscribite*" de `ESTILO.md` §3 (la había escrito el asistente).
>
> **Decisión de Agustín (2026-09-11):** *"hay que arreglar la intro y la outro: 1) tienen que incentivar a
> suscribirse y a darle likes; 2) tienen que ser más emotivas y altísima calidad."* → **v2**, este documento.

## Archivos

| Qué | Dónde |
|---|---|
| Clips terminados (voz + efectos + música) | `produccion/intro_canal.mp4` (13,96 s) · `produccion/outro_canal.mp4` (19,79 s) |
| Generador (imagen + mezcla; frames en carpeta propia `_frames_canal`, nunca en `_frames`) | `produccion/intro_outro.py` |
| Piezas de papel exclusivas del canal (pulgar, expediente, luz, sombra de contacto) | `produccion/props_canal.py` |
| Voz George (eleven-v3 por fal, con timestamps por carácter) | `audio/canal/intro_v2.mp3` + `.json` · `outro_v2.mp3` + `.json` |
| Textos de la voz (con dirección de actor) | `audio/canal/intro_v2.txt` · `outro_v2.txt` |
| Toma larga de la intro que se descartó (14,6 s) | `audio/canal/intro_v2_largo.*` |
| Mapa del mundo genérico (Natural Earth) | `produccion/assets/mapa_mundo.png` (`produccion/mapa_mundo.py`) |
| Chequeo sin renderizar (encuadre + ritmo + hoja de contacto) | `python produccion/intro_outro.py check` |
| Pegado a un episodio | `python produccion/pegar_intro_outro.py 01_aviacion_rusa_v5.mp4` → `..._canal.mp4` |

## Qué cambió en la v2 y por qué

La v1 fallaba en tres cosas concretas, visibles en `_intro_grid.jpg` / `_outro_grid.jpg` de entonces:

1. **La hoja no llenaba el cuadro.** Ocupaba dos tercios: quedaba un bloque de madera marrón a la derecha y
   dos franjas de pared arriba y abajo. Es la misma lección que la del ep. 05 (skill v1.8.0). Ahora la hoja
   del mundo va a `SHEET_S = 1.36` y **sangra por los cuatro lados**: el borde no se ve nunca.
2. **No había luz.** Todo estaba iluminado igual, así que nada llamaba la atención y la mesa se veía plana.
   Ahora hay un charco de luz cálido + viñeta (`props_canal.luz`), y en la intro un **segundo foco** que se
   cierra sobre el expediente elegido. Va sobre la clase `Overlay`, que **reescala la capa a la ventana de
   cámara en cada cuadro**: si no, al hacer zoom la viñeta quedaría descentrada.
3. **Era una secuencia de tarjetas, no un relato.** Ahora cada pieza tiene un arco (abajo).

Y lo que pidió Agustín: **se pide LIKE además de SUBSCRIBE**, en las dos piezas, con un pulgar recortado en
papel (`props_canal.pulgar`) en vez de pegar el icono de YouTube encima.

## Intro (13,96 s)

Voz: `Every border. Every war. Every deal. [pause] Somewhere, a piece of paper decided it. This is Paper Trail. Like it, subscribe, and follow the paper.`

Arco, anclado a la voz:

| t | Voz | Imagen |
|---|---|---|
| 0,0 | — | la mesa vacía: hoja del mundo, cerco de café, luz baja |
| 0,7 · 1,4 · 2,9 | *Every border / war / deal* | tres expedientes grandes CAEN uno sobre otro (RATIFIED · DECLARED · firmado), golpe de cámara en cada uno |
| 3,4 → 5,3 | (la pausa) | los tres se achican y se acomodan mientras **caen doce más**: la mesa entera del mundo |
| 5,5 | *Somewhere, a piece of paper decided it* | uno se levanta, el foco se cierra sobre él, el resto se apaga |
| 7,0 → 8,8 | (silencio) | cinco expedientes vecinos se levantan y **convergen** hacia el elegido |
| 9,0 | *This is Paper Trail* | el sello ocre cae y golpea; sello **PAPER TRAIL** |
| 10,0 · 11,1 | *Like it, subscribe* | pulgar de papel + **LIKE** abajo a la izquierda, **SUBSCRIBE** abajo a la derecha |
| 12,1 | *and follow the paper* | **Follow the paper.** |

Va **al principio del video**, después de la intro propia del episodio (ver abajo).

> **Duración:** la v1 medía 8,2 s; la v2 mide 13,96 s. El arco no entra en menos. Hay una toma más larga
> grabada (`intro_v2_largo.mp3`, 14,6 s de voz → clip de ~16 s) con la tripleta más pausada, y se puede
> recortar a ~10 s sacando la tripleta del principio. **Lo decide Agustín** (regla: el formato y la duración
> son suyos).

## Outro (19,79 s)

Voz: `That's the file closed. [pause] If it was worth your time, leave a like. That is the one thing that puts this table in front of somebody else. And if you want the next dispute on it — subscribe. Follow the paper.`

| t | Voz | Imagen |
|---|---|---|
| 0,0 | — | el Burócrata entra por la izquierda con la carpeta atada |
| 1,3 | *That's the file closed* | apoya la carpeta (golpe + sacudida) y le estampa **CLOSED** |
| 4,2 | *If it was worth your time* | señala el lugar donde va a caer el pulgar |
| 5,6 | *leave a like* | el **pulgar de papel grande** cae con golpe; tarjeta **LIKE** |
| 8,0 → 9,1 | *puts this table in front of somebody else* | tres expedientes se levantan y **salen de la mesa** hacia la derecha |
| 10,4 | (la pausa) | **entra uno nuevo** desde la derecha: el expediente del próximo |
| 12,3 · 13,8 | *the next dispute — subscribe* | el pulgar se achica al rincón, sello **SUBSCRIBE** grande |
| 15,9 | *Follow the paper* | **PAPER TRAIL** + **Follow the paper.**, y 3,2 s de cola |

**Todo lo permanente queda en la mitad izquierda** (x < 1100): la mitad derecha es para el elemento "video
siguiente" de la pantalla final de YouTube, y el botón real de suscripción va abajo al centro. La cola de
3,2 s es a propósito: los últimos ~20 s del archivo final son la outro, que es justo la ventana donde
YouTube permite poner la pantalla final.

## Sonido (decisiones del 2026-09-07, vigentes)

- **Cortina propia del canal:** `produccion/musica/tema_canal.mp3` (Lyria 3, 31 s, prompt propio: bajo
  pulsante, pizzicato, tic de reloj, piano apagado). Sin derechos de terceros. Va a −11 dB con ducking de
  −6 dB bajo la voz y fundido de salida de 2,5 s. **La outro arranca la pista en el segundo 9** (`mus_off`)
  para que no suene igual que la intro en el mismo video.
- **v2: la cortina respira.** `_mezcla(..., swell=[(t, ganancia), ...])` le pone una curva: baja en el
  susurro del principio, crece en la revelación y en el sello. Sin eso la música era una alfombra plana.
- **Efecto "slide" reemplazado:** el deslizamiento de papel original (ruido 800-4000 Hz) sonaba agudo y
  molesto; en estos clips todo deslizamiento usa `sfx_paper` (soplo grave < 900 Hz + golpecito a 140 Hz).

## Para cambiar algo

- **Texto de voz:** editar `audio/canal/intro_v2.txt` (o `outro_v2.txt`) y regenerar con
  `python voz/voz_fal_ts.py audio/canal/intro_v2.txt audio/canal/intro_v2.mp3` (George eleven-v3,
  voz `JBFqnCBsd6RMkjVDRZzb`, ~USD 0,02 por pieza). **Genera también el `.json` de timestamps, que es
  obligatorio**: la coreografía se acomoda sola a la voz nueva. Si se cambia una frase clave, actualizar
  `CLAVES_INTRO` / `CLAVES_OUTRO` en `intro_outro.py` (el script aborta si no encuentra la frase).
- **Tarjetas, tiempos o posiciones:** `build_intro()` / `build_outro()` en `intro_outro.py`.
- **Luz:** las tres constantes `LUZ_ANCHA` / `LUZ_FOCO` / `LUZ_OUTRO` arriba del archivo. `r` chico = viñeta
  más cerrada; `vin` = cuánto oscurece el borde; `a` = cuánto ilumina el centro.
- **Siempre antes de renderizar:** `python produccion/intro_outro.py check` → tiene que decir
  `violaciones de encuadre: 0` y `huecos: []` en las dos piezas (regla 1 y regla 3 de Agustín).

## Intro propia por video (decisión de Agustín, 2026-09-08)

**Todos los videos llevan, ANTES de la intro general, una intro exclusiva del episodio**: una serie de preguntas bien cortas
(gancho y retención), un objeto de papel por pregunta sobre la mesa, y el cierre: *"If you want the answers, stay with this video
until the end, and check them for yourself."* + tarjeta `STAY TO THE END.` Orden final de cada video:
**intro de preguntas (≈30 s) → intro general (14 s) → el episodio completo (con su cold open) → outro (20 s).**
Reemplaza al orden "cold open → intro" de `entregar.py --intro_at`. Plantilla: `produccion/intro03.py` (voz por fal.ai con
timestamps por carácter → `tiempos()` ubica cada pregunta; render en `_frames_canal`; armado en `produccion/_final03.sh`).
`intro03.py`, `intro04.py` e `intro05.py` usan `IO._card` y `IO._mezcla` de `intro_outro.py`: **las dos firmas se
mantuvieron iguales en la v2**, así que siguen funcionando sin tocarlas.
