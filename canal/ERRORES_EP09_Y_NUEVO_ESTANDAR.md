# Ep. 09 — qué salió mal, y el estándar de animación que viene ahora

> Escrito el **2026-09-15** después de que Agustín viera el episodio y lo parara a medias.
> Sus palabras: *"el video está muy mal y no lo alcancé a ver completo"*, *"de lo peor que vi en
> todos los videos"*, *"estuviste 5 horas reteniéndome para hacer algo tan horrible"*.
> Él nombró tres fallos y avisó de que había muchos más. **La lista completa la saqué auditando
> el vídeo y el guion; no es trabajo suyo enumerarlos.**
>
> Este documento es el punto de retomada después de compactar el contexto.

---

## 1. Los errores, todos

### 1.a De DATO — los graves, porque el canal se llama Paper Trail

| # | Error | Qué dice | Qué es |
|---|---|---|---|
| **1** | **La cifra del cold open** | La voz dice *"forty trillion, forty-six billion, one hundred seventy-eight million dollars. And twenty-two cents"* = **$40.046.178.000.000,22** | El dato real es **$40.046.178.322.792,78**. Faltan **322.792 dólares** y los centavos están mal (22 contra 78) |
| **2** | **La contradicción a la vista** | La voz dice *twenty-two cents* y el cartel que yo mismo "corregí" dice **AND 78 CENTS** | Mi parche empeoró el fallo: puso la contradicción **en pantalla** |
| **3** | **Las pirámides** | *"Spend a million dollars a day since the pyramids were built… you would not even be a third of the way there"* | Son **4.586 años × 365 × 1 M = 1,67 billones**, el **4,2 %** de la deuda. No un tercio. La frase minimiza la cifra en 8× |
| **4** | **El rango de los aportes** | *"Every administration added between four and nine trillion"* | Trump II aportó **+3,83 T**, que queda **fuera del rango** que la propia voz enuncia 40 segundos antes de decir 3,83 |
| **5** | **$120.000 por persona** | Sin `Fn`, y depende de una población que nunca verifiqué | Con 342 M da **117.000**; con 335 M, 119.541. La cifra pasa, pero entró sin fuente y eso viola la regla del ep. 06 |
| **6** | *"borrowed over sixteen years"* | 2009 → 2026 son **17** | Menor, pero es otro número dicho a ojo |

**La raíz de 1 y 3:** escribí números en palabras y en frases de escala sin comprobar la aritmética.
`guiones/checklist.py` avisó de *"cifras en voz sin respaldo en referencia.md: 11 líneas"* y lo
descarté como falso positivo del detector. **No lo era.**

### 1.b De ANIMACIÓN — lo que hace el vídeo invisible

Muestreo de 16 cuadros repartidos por el episodio final:

- **11 de 16 son papel cuadriculado con un cartelito**. Nada más.
- **Dos cuadros seguidos (380 s y 390 s) completamente vacíos**: solo el rótulo del plano.
- El hueco del acto II va del **376 al 400**: **24 segundos** sin nada.
- Los personajes aparecen **solos, sobre papel vacío**, sin escena ni contexto.
- El mapa aparece en 3 de 16 cuadros, **quieto**, como telón.

**Y esto es lo peor: lo detecté yo mismo, lo dije, hice dos parches y entregué igual.** La regla de
Agustín del 14-sep es *"tardar está bien, entregar flojo no"*. La rompí a conciencia.

**El punto ciego del motor que lo permitió:** `coreo.py check` da *"rellenos contra pantalla vacía:
3 · tramos que quedan: 0"* con el vídeo lleno de cuadros vacíos, **porque cuenta el rótulo del
plano como contenido**. Un cartelito de 20 px en la esquina superior satisface al detector. Hay que
arreglar el detector, no solo el episodio.

### 1.c De PROCESO

| # | Error |
|---|---|
| **7** | **La intro v3 metida sin verificar la unión.** La puse por defecto en `entregar.py` y comprobé cuatro fotogramas sueltos, no el empalme real con lo ya montado |
| **8** | **Cinco horas reteniéndolo.** Le fui pidiendo confirmaciones y dando partes mientras el resultado iba mal desde el arte. Debí parar y replantear al ver la primera hoja de contacto vacía |
| **9** | **El fondo nunca se cuestionó.** El papel cuadriculado viene heredado y yo lo di por bueno para 16 minutos |

---

## 2. El estándar nuevo: GeoGlobeTales

Referencia que pasó Agustín: **@GeoGlobeTales** — *"How America Bought Louisiana"*, 101 s,
**11.948.711 vistas · 363.371 likes** (9-jul-2026). Temática vecina a la nuestra: geopolítica e
historia contada sobre mapas.

**Lo que hace, cuadro a cuadro:**

1. **El mapa ES el fondo. Siempre. En todos los cuadros.** Nunca hay un fondo vacío. Mapa con
   relieve, océano azul, costas dibujadas.
2. **Territorios coloreados por potencia** y rotulados encima del propio territorio: Britain en
   rojo, France en azul, Spain en naranja, USA en celeste. El mapa **cuenta el conflicto solo**.
3. **Personajes chibi** (cabezones, trazo simple, muy legibles a tamaño mínimo) que se paran
   **sobre el mapa**, en grupos, haciendo algo: en un barco, ante una pizarra, soldados en la playa.
4. **La cámara no para**: zoom y paneo continuos de Europa a Norteamérica al Caribe. El movimiento
   lo lleva el mapa, no un corte.
5. **Subtítulo grande abajo, permanente**, sincronizado con la voz.
6. **Mezcla de registros**: mapa ilustrado + satélite real + fotografía real (una playa con volcán).
7. **Objetos que cargan el dato**: barriles bajando el Misisipi, un maletín con `$15M`.
8. **Color saturado.** Azul, verde, rojo, naranja. **Cero beige, cero papel.**

**Lo nuestro contra eso:** fondo beige cuadriculado, un cartel con marco, todo quieto, sin color,
sin cámara, sin escena. No es una diferencia de gusto: es la diferencia entre 11,9 M y 478 vistas.

---

## 3. Reglas nuevas (Agustín, 2026-09-15) — para ESTE y TODOS los próximos vídeos

> **R1 · El fondo cuadriculado se acabó.** *"el fondo es horrible, una cosa blanca con líneas,
> super aburrida, 0 animación, 0 mapas. Esto no es lo que queremos y lo sabías."*
> Ningún plano puede ser papel vacío con un cartel.

> **R2 · El mapa es el fondo por defecto**, coloreado, con territorios identificados, y **se mueve**
> (zoom/paneo). Si un plano no tiene mapa, tiene una escena con personajes haciendo algo.

> **R3 · Cero cuadros vacíos.** El detector de vacío **no puede contar el rótulo de plano como
> contenido**. Hay que arreglarlo antes de volver a renderizar.

> **R4 · Toda cifra hablada se verifica con aritmética**, no solo con que exista la `Fn`. Las
> frases de escala ("un millón al día desde las pirámides") se calculan.

> **R5 · Se mantiene la identidad Paper Trail**: los personajes propios, el sello, el recibo, la
> idea del papel que prueba quién pagó. Lo que cambia es la **calidad y la densidad** de la
> animación, no la marca.

---

## 4. Qué se rehace y qué se conserva del ep. 09

**Se conserva** (está bien y está pago):
- La tesis y la postura (`postura.md`): los cuatro traspasos, ninguna administración como culpable.
- Las fuentes F1-F8, **con las correcciones de §1.a**.
- La tabla del Tesoro y los cuatro estados del bono: los dos objetos que sí funcionan.
- La medición del título (`us debt` 44,0 contra `debt default` 2,0).
- El paso 0 y `produccion/demanda.py`.

**Se rehace:**
- El guion, corrigiendo los seis errores de dato.
- **La voz entera** (el error de la cifra está locutado). Coste: ~USD 1,56 otra vez.
- **Toda la animación**, contra el estándar de §2.

**Se tira:** el `cuerpo.mp4` y el `FINAL.mp4` actuales.

---

## 5. Coordinación — hay otra sesión trabajando

> Agustín, 15-sep: *"Hay otra sesión trabajando con shorts. NO SE PISEN POR FAVOR."*

**Esta sesión NO toca:**
- `videos/S*/` — todo lo de series y shorts es de la otra sesión.
- `produccion/motor.py`, `produccion/props.py`, `produccion/shorts.py` y cualquier otro archivo
  compartido **sin avisar antes**. Un cambio ahí le rompe el render a la otra sesión en marcha.
- El caché de `motor.py` (la optimización de 70 → 28 min) queda **congelado**: Agustín pidió
  explícitamente *"sin mi OK no haces nada"*.

**Esta sesión trabaja solo en:** `videos/09_deuda_eeuu/`, `canal/ESTANDAR_VISUAL_V2.md` y este
documento.

Si hace falta tocar algo compartido, se pregunta primero.

### 5.b Lo que la otra sesión ya hizo, y por qué NO se duplica

Al escribir esto apareció en memoria `project-pasada-de-vida`: la otra sesión **ya midió el mismo
problema por otro lado** y tiene plan aprobado por Agustín.

| | La otra sesión | Esta sesión |
|---|---|---|
| **Pregunta** | ¿por qué se ve quieto? | ¿por qué se ve vacío y feo? |
| **Hallazgo** | 53-63 % de imagen congelada contra 10 % de RealLifeLore. Los mecanismos (idle, respiración, parallax, push) existen pero están 3-5× por debajo de lo perceptible, y `push` es un **porcentaje por plano**, así que cuanto más largo el plano **más lenta** va la cámara | 11 de 16 cuadros son papel cuadriculado con un cartel. No hay mapa de fondo, ni color, ni escena |
| **Arregla** | que **lo que hay se mueva** (calibración de `motor.py`) | **qué se ve** (mapa de fondo, color, personajes en escena) |
| **Toca** | `produccion/motor.py`, `produccion/ritmo.py` | `videos/09_deuda_eeuu/`, arte del episodio |
| **Documento** | `canal/PLAN_PASADA_DE_VIDA.md` | este y `canal/ESTANDAR_VISUAL_V2.md` |

**Los dos hacen falta y convergen en este episodio**: su plan decía *"entra en el próximo episodio,
no en el 09"* porque el 09 estaba renderizando. Al rehacerse el 09, **el próximo episodio es este**.

Su medidor `produccion/ritmo.py` (metas: quietos < 20 %, ocupación > 55 %) es el criterio objetivo
para aceptar el episodio rehecho. **Se usa antes de entregar**, junto con mirar la hoja de contacto.
