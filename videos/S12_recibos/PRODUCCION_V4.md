# S12 · THE RECEIPT — registro de producción sobre el motor v4 (2026-09-15)

> Lo que hay que saber para la próxima tanda. Decisiones que no eran obvias y trampas que costaron
> tiempo. Para la skill `paper-trail-video`.
>
> Archivos nuevos de esta producción: `mundos4.py` (los cuatro mundos), `coreo4.py` (el motor de
> coreografía), `escenas4.py` (las cuatro partituras), `_vacios.py` (dos verificadores).
> `coreo.py` y `escenas.py` (v1) **no se tocaron**: quedan de referencia.

---

## 1. Las tres correcciones de la auditoría, cómo quedaron

1. **MESA sin hoja rayada.** `coreo4.Pieza.mesa()` = mundo oscurecido (`dark` 0,58) + el
   **documento grande** (40-52 % del alto) + dos o tres props de escritorio chicos de fondo. El
   documento **es** el papel: no hace falta una hoja debajo, y así el mapa oscurecido se sigue
   viendo alrededor y recuerda dónde estamos. En la prueba v4, 5 de 12 cuadros eran una hoja con
   renglones tapando el mapa; en la pieza 4 terminada no hay ninguno.
   · El documento **se mueve** (crece 5,5 % y gira 1,1° a lo largo del plano). Sin eso, `dark`
   congela el mapa y el plano entero es una foto: de ahí salía el 27 % de quietos de `prueba_vida`.
2. **Ceuta con el color de España por encima de Marruecos.** Se bajó Natural Earth **10m**
   `admin_0_map_subunits` y se recortó a los dos enclaves en
   `fuentes/mapas/ne_10m_ceuta_melilla.geojson` (1,5 KB, dominio público). `mapa_v2.capa_geojson()`
   es nueva y `mundo()` acepta `capas_geojson`. La coreografía enciende `ceuta` **después** de
   `mar`, así que gana. Medido: la capa pinta 29.798 px y el **98,7 % cae sobre tierra dibujada**
   (el 1,3 % es el antialias de la costa). Si el geojson faltara, `pieza_4` **no pinta Marruecos** y
   lo avisa: antes un mapa sin color que un mapa que diga que Ceuta es Marruecos.
3. **El gancho va sobre el mapa en movimiento.** El primer plano de las cuatro es MAPA con viaje y
   dura más que los 3,5 s del gancho. `Pieza.cerrar()` **aborta** si una partitura pone MESA antes.

---

## 2. Trampas nuevas, que es lo que de verdad sirve para la próxima

### 2.1 eleven-v3 **lee en voz alta** las etiquetas de dirección largas
La pieza 1 gastó **4,96 s** y la 3 **4,60 s** de audio a nivel de habla (−18/−20 dBFS) diciendo su
etiqueta de apertura antes de la primera palabra del guion. Las piezas 2 y 4, con la misma
estructura, salieron limpias: **no es determinista**, así que no vale "probar y ya".

- Fundir las dos etiquetas de apertura en un solo corchete **no lo arregla** (se probó y la 3
  empeoró): lo que lo dispara es la **longitud**, no el número de corchetes.
- Las etiquetas de **dentro** del texto sí se interpretan bien en las cuatro piezas. Se comprobó
  midiendo la energía en cada intervalo de etiqueta: las de dentro duran 0,6-0,9 s, que es **menos
  de lo que se tardaría en pronunciarlas**, y 7 de 11 están en silencio digital (−68/−87 dBFS).
- **El arreglo no cuesta un crédito**: los propios timestamps dicen dónde empieza la primera palabra
  del guion, así que `voz_corta.py::alinear` corta ahí y deja 0,18 s de aire. Recortó 5,08 s en la
  pieza 1 y 4,51 s en la 3.

### 2.2 `_palabras.json` guardaba las palabras NORMALIZADAS
Y eso rompía tres cosas a la vez, ninguna evidente:
- el subtítulo decía `TWENTYFOUR` en vez de `TWENTY-FOUR`;
- `motor.agrupar` corta los grupos **por puntuación**, y sin puntuación no cortaba nunca: salían
  grupos a caballo de dos frases (`NARROWER IT SAID SUMMARY`);
- `resaltar` compara quitando la puntuación, así que contra una palabra ya normalizada **no casaba
  nunca** y no había una sola palabra en rojo en el subtítulo de ninguna pieza.

Con fal se puede guardar la palabra tal cual (el texto es el del guion); con whisper no, que es por
lo que estaba normalizado. El emparejamiento sí va normalizado en los dos lados.

### 2.3 Un corte que sólo cambia el ZOOM no se ve
`ritmo.py` da por detectado un corte cuando dos cuadros seguidos difieren más de **12/255 en gris**.
Dos planos de mapa seguidos con zoom parecido enseñan casi lo mismo: la cámara salta pero la
pantalla no cambia. El primer montaje de la pieza 4 tenía así un tramo de **20 s sin un solo corte**
formado por cinco planos. Medido, cuesta creerlo hasta que se ve:

| corte | cambio de gris |
|---|---|
| zoom **out** fuerte (×0,30) | 29,0 |
| zoom **in** (×1,95) | **11,0** ← no se lee |
| mapa → mesa | 49,3 |

Tres cosas lo arreglan, y las tres son mejores decisiones de montaje, no trucos:
1. **Alternar abierto y cerrado** en planos consecutivos de mapa.
2. **Cambiar de tono, no de tamaño.** Tierra kaki ≈ 176 de gris, mar teal ≈ 127. Un corte de un
   encuadre de tierra a uno de mar se ve; uno de tierra a más tierra, no. En la pieza 1 (mapa del
   Golfo, muy uniforme) fue **lo único** que funcionó.
3. **Un cartel que cruza el corte AMORTIGUA el corte.** Es la otra cara de la ventaja del v4: como
   el HUD vive en px de cuadro, los mismos píxeles están a los dos lados. El mapa solo cambiaba 17
   y con los carteles encima bajaba a 11. Los carteles cruzan el corte **sólo cuando la frase
   sigue**; si la frase ya terminó, se van con el corte.

`coreo4.Pieza._cortes_flojos()` lo avisa al construir, y `_vacios.py::cortes(n)` lo **mide de
verdad** cuadro a cuadro sin renderizar (10 min menos por intento).

**Ojo con el umbral del predictor.** `cortes()` mide sobre el render de PIL y `ritmo.py` sobre el
mp4 ya codificado: el h264 y el reescalado por área del `ffmpeg` suavizan, y lo medido sobre el
vídeo sale **un 25-30 % más bajo**. Comprobado en la pieza 1: donde el predictor decía 13,7 / 15,9 /
14,7 el vídeo daba 10,9 / 11,0 / 10,6, o sea por debajo del umbral. **El predictor hay que leerlo
con umbral 17, no 12.** Es el número que usa `cortes(n, umbral=17.0)`.

### 2.3b MESA sin documento
Cuando lo que tiene que leerse son las **barras** o las tarjetas, un documento compite con ellas.
`mesa(..., doc=None)` oscurece el mundo y pone los props de escritorio, sin papel. Sirve para dos
cosas: el fondo neutro hace las barras más legibles, y **da un corte de verdad** donde dos planos de
mapa seguidos no lo darían — que es como se partieron los tramos de 8-14 s de las piezas 1, 2 y 3
sin tener que separar las dos barras, que necesitan verse juntas porque la comparación *es* la
pieza.

### 2.4 Dos planos de MESA seguidos con el MISMO documento tampoco se leen
El documento es HUD: no se mueve con la cámara, así que a los dos lados del corte hay el mismo
papel. Se resuelve cambiando de documento (pieza 2: `poliza` → `factura`; pieza 3: `contrato99` →
`libro_mayor`; pieza 1: `petrolero` → `deposito_oil`), que además suele contar mejor el beat.

### 2.4b El rol `sujeto` es CELESTE y el océano es TEAL: no se distinguen
Pintar EE. UU. de `sujeto` (72,178,190) sobre el mar (70,142,152) dejaba la pieza 1 con **el cuadro
entero del mismo color**: los cuatro domos flotando sin costa, el mapa sin narrar nada, y —de paso—
el movimiento medido por los suelos, porque sin contraste no hay diferencia de píxeles que medir.
Se ve de un vistazo en la primera hoja de contacto de la pieza 1 y **no lo caza ningún check**.

Va `institucion` (azul, 52,88,170), que además es lo correcto por la regla del color: el sujeto de
la pieza es **la reserva**, un organismo del Estado (`ESTADO.md` §3), no «el país del que habla el
vídeo».

Lo que choca aquí es el **TONO, no la luminancia**: medidos contra el océano (gris 122), `sujeto` da
148 (+26) y parecería aceptable, pero celeste y teal son la misma familia de color y a tamaño de
teléfono el ojo no los separa. El que sí choca por luminancia es `tercero` (verde, 124: **+2**), que
en esta tanda pinta Omán/EAU en la pieza 2 e Irlanda en la 3 — ahí se distingue por tono, no por
claro-oscuro, y por eso se deja. Regla práctica: **un rol sobre agua tiene que diferenciarse en tono
Y en luminancia**; los seguros contra este océano son `institucion` (azul, 87), `deudor` (rojo, 92)
y `acreedor` (ocre, 155).

### 2.4c La caché de `mundo()` no miraba los COLORES de las capas
La firma llevaba sólo los alias (`['usa']`), así que cambiar el rol de un país no invalidaba nada y
el mundo seguía saliendo del PNG viejo **sin decir una palabra**. Arreglado: la firma lleva ahora el
color y el alpha de cada capa. Si algo del mapa «no cambia aunque lo cambies», es esto.

### 2.4d Los veinte workers generan el mundo A LA VEZ y se pisan escribiendo
`build()` corre en cada worker del pool, así que si la caché del mundo está fría —o se invalida,
que es justo lo que provocó el arreglo de §2.4c— **los veinte generan el mismo PNG a la vez**.
Resultado medido: `mundo_hormuz_marcas.png` y `mundo_uk_marcas.png` de **0 bytes** y el render
abortando con `SyntaxError: broken PNG file`. `mapa_v2` escribe ahora a un temporal con el PID y
**renombra** (el rename sí es atómico), y el `_meta.json` —que es lo que mira la caché— se escribe
**el último**, así que ningún proceso da por bueno un mundo hasta que todos sus PNG están enteros.
Regla de operación igualmente: **`python mundos4.py` antes de renderizar**, para que el pool
encuentre la caché caliente. (Ojo al escribir a un `.tmp`: PIL deduce el formato de la extensión y
hay que pasarle `format='PNG'`.)

### 2.5 Los rótulos del mapa se miden contra la VENTANA, y `etiquetas=True` los duplica
`hoja_v2` rotula cada país con el `LABEL_X/Y` de Natural Earth **además** de lo que pida
`rotulos_extra`: salían los dos, «Iran» en cursiva encima de «IRAN». Se apagan con
`etiquetas=False` y se controlan a mano, con la posición calculada contra la ventana a `zmin`.

### 2.6 El `alto_rel` del HUD escala por ALTO y el ancho sale solo
`regla` mide 234×52: un `alto_rel` de 0,070 daba una barra de **603 px** cruzando la pantalla. Se
vio en la hoja de contacto, no en ningún check.

### 2.7 `p.prop(cual, ...)` y no `p.prop(nombre, ...)`
Con doce petroleros o tres hoteles hace falta un `nombre` distinto por copia, y si el parámetro
posicional se llama igual Python se queja de *multiple values for argument*.

### 2.8 Natural Earth 50m **no resuelve** la bahía de Ceuta
`shapely` dice «tierra» en todo el istmo, así que no se puede verificar contra el polígono.
`coreo4.Pieza.ruta(verificar='agua')` comprueba contra el **PNG del mundo**, que es lo que se ve.
Cazó las dos rutas que escribí a ojo: la de Ceuta iba 56 % por agua y la de los petroleros 40 %
(cruzaba Qatar y los EAU por tierra). Con los puntos sacados de la máscara: 100 % y 94 %.
Los segmentos de los extremos no cuentan: el origen y el destino son ciudades y están en tierra.

### 2.9 Compactar las pausas (paso obligatorio desde el 15-sep)
`voz/compactar.py` acorta las pausas por su cola sin tocar la voz y reescribe los tiempos. No es
sólo ritmo: **mejora la alineación**, porque las palabras dejan de caer en silencio.

| pieza | antes | después | palabras sobre voz |
|---|---|---|---|
| 1 · tanque | 78,2 s | **71,9 s** | 174/187 → **182/187** |
| 2 · hormuz | 69,0 s | **62,8 s** | 177/183 → **181/183** |
| 3 · hoteles | 73,4 s | **67,9 s** | 164/174 → **170/174** |
| 4 · ceuta | 80,0 s | **73,1 s** | 177/188 → **185/188** |

Los originales quedan como `audio/*_sin_compactar.*`. El cierre no se compacta.

### 2.10 Los tiempos de la partitura van por ANCLAJE, no por número
Todas las piezas se escribieron dos veces porque la primera tenía los cortes en segundos absolutos
y compactar la voz los dejó descolgados. Ahora cada corte es `t_ruling + 0.60` o `p.L(2)[0] - 0.06`,
y regenerar o recompactar la voz mueve la coreografía con ella. **Es la diferencia entre rehacer una
partitura y volver a correr `check`.**

---

## 3. Decisiones que no son técnicas y que Agustín puede querer cambiar

1. **El agua de la pieza 1 no lleva rótulo.** El nombre de ese golfo está en disputa política desde
   2025 y **el guion no lo nombra ni una vez**: la pieza habla de cuatro domos de sal en Texas y
   Luisiana. Poner un nombre —cualquiera de los dos— sería que el mapa tome una postura que Agustín
   no tomó y que el guion no necesita. Se rotulan TEXAS y LOUISIANA. Si lo quiere, es una línea en
   `mundos4.py`.
2. **La línea 5 de la pieza 1 no se va al mundo de Hormuz**, como pedía `PLAN_VISUAL_V4.md` §1. Una
   `Scene` tiene UN mundo: hacerlo obligaría a dos escenas, dos renders y un pegado por pieza. Se
   resuelve con un plano de MESA —el mapa oscurecido no afirma ninguna geografía— y el petrolero
   grande.
3. **Las coordenadas de F1.10 se cambiaron por las verificadas.** Las de `PLAN_VISUAL_V4.md` estaban
   cerca pero no eran las del infobox de Wikipedia: Lake Charles se iba 0,029° de latitud = 3,2 km =
   9 px a la escala de ese mundo. Igual el Estrecho de Hormuz (26,6 N 56,5 E, no 26,57/56,25).

---

## 4. Costo

| | |
|---|---|
| Voz de los cuerpos | 6 llamadas a fal (4 piezas + 2 regeneradas por §2.1) |
| Voz de los cierres | 5 llamadas (la 4 se generó dos veces) |
| Imagen | **0 créditos** — mapas por código, props existentes, rigs ya pagados |
| Tope de la producción | USD 4 |
