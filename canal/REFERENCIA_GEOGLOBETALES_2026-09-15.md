# La referencia que pasó Agustín — GeoGlobeTales, y qué se puede copiar

> Agustín, 15-sep-2026: *"¿crees que la animación se pueda acercar un poco a cómo están estos
> videos? dime si podemos hacer una prueba con estos shorts para hacer algo así, obviamente
> manteniendo nuestro estilo del canal pero más animado como aquí"*.
>
> Video: **«How America Bought Louisiana — Napoleon's $15M Deal»**, canal **GeoGlobeTales**,
> 9-jul-2026, 1080×1920, 30 fps, **1:41**, **11.947.156 vistas**.
>
> Medido con `produccion/ritmo.py`, la misma herramienta con la que medimos los nuestros.

---

## 1. El número, y es brutal

| Métrica | **GeoGlobeTales** | **RealLifeLore** (ref. anterior) | **Paper Trail** (eps. 03/04/06) |
|---|---|---|---|
| **quietos** | **10,7 %** | 10,3 % | **53-63 %** |
| **movimiento medio** | **9,25** /255 | 7,18 | **0,55-0,74** |
| **cortes/min** | **66,5** | — | 10,5-11,8 |
| hueco entre cortes (mediana) | **0,2 s** | — | ~5 s |
| hueco máximo | **4,8 s** | — | >10 s |

**Doce veces más movimiento que nosotros, y seis veces más cambios de imagen por minuto.** Y no es
un caso raro: es el mismo rango que RealLifeLore, o sea que es **el estándar del nicho**, no el
estilo de un canal.

El dato que más explica la diferencia: **la mediana entre cambios de imagen es de 0,2 segundos.**
No son cortes de plano cada 0,2 s — es que en ese video **nunca hay un instante en que la pantalla
no esté cambiando**. En los nuestros, seis de cada diez cuadros son idénticos al anterior.

> **Nota sobre la ocupación:** `ritmo.py` le da 1,3 % y a nosotros 34 %. Ese número **no significa
> nada aquí**: la métrica cuenta píxeles claros (luminancia > 150) porque está calibrada para
> nuestro papel sobre mesa oscura. GeoGlobeTales usa mapas de tonos medios, así que puntúa bajo
> ocupando el 100 % del cuadro. Es un límite de la herramienta, no un defecto de ellos.

---

## 2. Qué hace, exactamente

De la hoja de contacto de 12 cuadros:

1. **El mapa es el fondo, siempre, a sangre completa.** No hay una «hoja de mapa» apoyada en una
   mesa: la cámara vive **dentro** del mapa. En los 12 cuadros, el mapa ocupa el 100 %.
2. **La cámara viaja por el mapa sin parar** — Europa, el Caribe, Norteamérica, vuelta a Europa —
   con zoom y paneo continuos. El mapa es un espacio navegable, no una ilustración.
3. **Los países son colores planos que cambian.** Gran Bretaña roja, Francia azul, España naranja,
   EE. UU. cian. **El cambio de color ES la narración**: cuando Luisiana pasa de azul a cian, la
   compra está contada sin una palabra.
4. **Personajes «chibi»** (cabezones de juguete) recortados sobre el mapa: Jefferson, Napoleón.
5. **Fotos reales mezcladas** con el dibujo (el Napoleón de museo asomándose por el borde, la playa,
   el satélite del Caribe). El choque es deliberado y es medio chiste.
6. **Subtítulo palabra a palabra**, grande, centrado, en la mitad baja. Cambia cada ~0,3 s.
7. **Props-gag**: la etiqueta de precio `$10M`, el cartel `SOLD`, el banner
   `BIG LAND. BIG DISCOUNTS. www.BuyLouisiana1803`.

---

## 3. Qué copiamos y qué no

### Sí, y ya tenemos el mecanismo para casi todo

| Qué | Con qué se hace | Cuesta |
|---|---|---|
| **El mapa a pantalla completa, con la cámara dentro** | `MapSheet` ya proyecta con Mercator real y `Scene.cx/cy/zoom` ya son pistas animables. Hoy el mapa entra como *hoja sobre la mesa* en un plano y se va. El cambio es de **uso**, no de motor | 0 |
| **Países que se pintan y cambian de color** | `MapSheet.add_layer(..., mode='wipe')` — ya existe y hace exactamente eso | 0 |
| **Cámara en viaje continuo** entre puntos reales | El paso 1 ya está puesto en la S12; falta encadenar movimientos punto a punto en vez de un push por plano | 0 |
| **Subtítulo palabra a palabra** | **`whisper` ya nos deja `_palabras.json` con el tiempo de cada palabra** y hoy no lo usamos para nada | 0 |
| **Props-gag con humor seco** | Ya los dibujamos por código | 0 |

**El subtítulo palabra a palabra es el cambio más barato y el que más sube el número**, porque mete
un cambio de imagen cada ~0,3 s por sí solo. Los archivos ya están generados; solo hay que pintarlos.

### No

- **Los personajes chibi.** No son nuestro estilo, y son 1 crédito de generación cada uno. Nuestro
  equivalente ya existe y está pagado: los 15 rigs del elenco.
- **Las fotos reales mezcladas.** Rompen la paleta de papel, que es lo que hace reconocible al canal
  en un feed.
- **Y una cosa de fondo:** ellos cuentan **una historia** (Napoleón vende, Jefferson compra).
  Nosotros contamos **una cuenta**. Nuestro objeto central es un documento, no un personaje. El
  ritmo se copia; el sujeto no.

---

## 4. La prueba que propongo

**Pieza 4 (Ceuta), los primeros 25 segundos.** Es la candidata porque ya lleva hoja de mapa y porque
su argumento es geográfico: dónde se acaba la valla.

Qué cambia en esos 25 s:

1. El mapa del Estrecho **a sangre completa** desde el primer cuadro, en vez de como hoja.
2. La cámara **entra** desde el Estrecho entero hasta Ceuta, en movimiento continuo.
3. **España en azul y Marruecos en ocre**, pintados con `add_layer` mientras la voz los nombra.
4. **Subtítulo palabra a palabra** con `_palabras.json`.
5. La línea roja rodeando el extremo de la valla, ya con `route`.

Y después se mide con `ritmo.py` contra estos mismos números. **Meta de la prueba: quietos < 25 % y
movimiento > 4.** No se apunta al 9,25 de GeoGlobeTales en el primer intento; se apunta a salir del
0,7 y estar en la misma liga.

**Orden (regla tuya):** primero **un cuadro fijo**, después el clip de 25 s, y solo si convence se
aplica a las cuatro piezas. Cero créditos en toda la prueba: es render local.

**Bloqueante:** los pasos que tocan `produccion/motor.py` (idle, wobble, `depth` en props) siguen
esperando a que termine el render del ep. 09. El mapa a pantalla completa, el color de los países y
los subtítulos **no** tocan el motor y se pueden hacer ya.

---

## 5. Lo que esto confirma del diagnóstico del 15-sep

`canal/POR_QUE_SON_SOSOS_2026-09-15.md` decía que el problema era la fórmula del push y la
calibración del idle. **Esta referencia dice que eso se queda corto.** El push arreglado lleva de
0,7 a ~2,5 de movimiento; GeoGlobeTales está en 9,25. La diferencia que falta no está en la
calibración: está en **qué ocupa el cuadro**. Ellos ponen un mundo que se recorre; nosotros ponemos
una mesa que se mira.

El mapa a pantalla completa es el cambio grande, y es el único que cierra esa brecha.

---

## 6. RESULTADO DE LA PRUEBA · 25 s de Ceuta

`videos/S12_recibos/prueba_vida.py` · render local, **0 créditos** · medido con `ritmo.py`.

| Métrica | **Antes** (eps. 03/04/06) | **Prueba, 1ª pasada** | **Prueba, 2ª pasada** | GeoGlobeTales |
|---|---|---|---|---|
| **quietos** | 53-63 % | 6,1 % | **14,1 %** ✓ | 10,7 % |
| **movimiento** | 0,55-0,74 | 3,05 | **4,58** | 9,25 |
| **cortes/min** | 10,5-11,8 | 4,8 | **21,6** ✓ | 66,5 |
| **ocupación** | 34 % | 90,9 % | **89,7 %** ✓ | — |

**De 0,7 a 4,58 de movimiento: seis veces y media más.** Las tres metas del plan, cumplidas.

### Lo que enseñó la primera pasada

Con **solo el vuelo de cámara** salían 6,1 % de quietos —mejor que la referencia— pero el
movimiento se quedaba en 3,05 y los cortes en **4,8/min contra 66,5**. Ahí estaba lo que faltaba:

> **GeoGlobeTales no solo vuela: además corta todo el rato.** El vuelo continuo saca la imagen de la
> congelación; **el corte seco es lo que sube el movimiento medio**, porque cambia el cuadro entero
> de golpe. Hacen falta las dos cosas.

La segunda pasada alterna tramos de vuelo con **diez saltos duros** en 25 s, y el movimiento sube de
3,05 a 4,58 con los quietos todavía en 14,1 %.

### Los cuatro cambios, confirmados

1. **El mapa es el suelo del plano**, no una hoja sobre la mesa → la ocupación pasa de 34 % a 89,7 %.
2. **La cámara vive dentro del mapa**, alternando vuelo y salto seco.
3. **Los países se pintan** cuando la voz los nombra.
4. **Subtítulo palabra a palabra** (grupos de 2-4), con nuestra tarjeta de papel en vez del texto
   blanco de ellos.

Y **nuestro personaje**, no los chibi: el jurista del elenco, que ya está pagado.

### Dos cosas que se arreglaron por el camino

- **El bbox del mapa era casi cuadrado** (3000×3086). Metido en un plano 16:9, sobresalía 450 px por
  arriba y por abajo, y como `Scene.window()` limita la cámara al lienzo, **España quedaba
  permanentemente fuera de cuadro**: solo se veía la costa marroquí. La hoja se rehízo a 16:9
  (3000×1688) ensanchando la longitud a 2,19 grados.
- **Al pintarse Marruecos, Ceuta quedaba ocre** — el mapa afirmaba justo lo contrario del guion.
  Natural Earth 50m no separa el enclave, así que las marcas se sacaron a una capa propia
  (`mapa12_marcas.png`) que va **por encima** del color.

### Lo que falta para acercarse más al 9,25

- Más saltos (ellos están en 66,5/min; vamos por 21,6).
- Los pasos 2 y 4 de `PLAN_PASADA_DE_VIDA.md` —idle ×3, wobble en props, `depth`— que tocan
  `produccion/motor.py`. **Ya se pueden hacer: el ep. 09 terminó de renderizar a las 13:57.**
