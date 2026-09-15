# S12 · THE RECEIPT — plan visual para el motor v4 (2026-09-15)

> Lo escribe el orquestador de la auditoría (`canal/AUDITORIA_MOTOR_2026-09-15.md`) y lo ejecuta el
> agente de producción. Manda sobre `escenas.py` v1 (que era "plano fijo + cartel"). La API nueva está
> en `produccion/MOTOR_V4.md`. Regla 1 (nada cortado), regla 24 (puntos exactos), regla 22 (carteles
> no se pisan) y las reglas 13/14 (sujeto = el mecanismo, nunca un colectivo) siguen vigentes.

## 0. Formato y gramática (igual en las cuatro piezas)

- **Vertical nativo 1080×1920** (`Scene(mundo, size=(1080,1920), v4=True)`). Ya no hay hoja de papel
  con el video adentro: el mundo llena la pantalla. La identidad de papel va en los OBJETOS (tarjetas,
  sellos, rigs, props) y en el grano del mapa, no en un marco.
- **El mundo es un mapa v2** (`mapa_v2.mundo(...)`), uno por pieza, con un bbox **más alto que ancho**
  (≈ 9:16 o 3:5) y ~2400-3000 px de ancho para que la cámara pueda abrir (zoom < 1) y cerrar (hasta
  1:1) sin perder nitidez. Países coloreados por ROL cuando la voz los nombra (`add_layer`), no antes.
- **Un plano = corte + UN viaje motivado** (`corte` + `viaje`) hacia lo que la voz dice. `vida` por
  defecto encendida. Cero saltos secos dentro de la misma vista.
- **MESA**: cuando la pieza habla de un documento (el decreto, la póliza, las cuentas, la sentencia) se
  corta a la MESA: mundo oscurecido (`dark` 0,55) y el documento como Obj grande centrado, o un fondo
  de mesa propio si se ve mejor (decidirlo mirando un cuadro fijo). Alternar MAPA ↔ MESA es lo que da
  "corte de contenido" en vez de "corte de encuadre".
- **HUD** (capa de pantalla): subtítulos palabra a palabra (`Scene.subtitulos`, estilo `banda`,
  fy ≈ 0,80, palabras de `resaltar` en rojo), la CIFRA grande de cada beat (tarjeta de papel, cuerpo
  ≥ 96 px, legible a 405 px), el rótulo corto del beat arriba (fy ≈ 0,09, cuerpo 40), el chip
  `PART n OF 4` (arriba a la izquierda, chico), la barra de progreso ocre (abajo, 9 px).
- **Gancho**: los primeros 3,5 s llevan la tarjeta del gancho de `serie.json` (3 líneas, la roja en
  rojo) como HUD grande sobre el mapa **ya en movimiento**; se va con fade a los 3,5 s. Después el
  gancho no vuelve (competía con el video 90 s seguidos). **Dato de Studio (15-sep, §5.5): los shorts
  que abren con una historia con giro retienen 40-59 %, los de "cifra sola" 8-18 %.** Por eso la
  línea 0 de las piezas 1-3 se reordenó (giro primero, cifra después; mismos datos) y en imagen el
  primer segundo ya tiene que contar algo: la cámara viajando, un objeto entrando, un país
  pintándose. Nunca una tarjeta quieta sobre un mapa quieto.
- **Rigs**: de pie SOBRE el mapa (peana + sombra de contacto como en `mapa_v2.componer`), a la
  altura de un país, no flotando en el mar. Un rig por pieza como mínimo, en el beat que más lo pide,
  con `gesture` en cada frase mientras está y `point_at` al sitio del que se habla.
- **Sonido**: sfx del motor + `whoosh` suave en cada viaje largo + cue Lyria `cue_04_dron` (ya paga) +
  `loudnorm` a −14 LUFS en el armado. Sin cambios de música entre piezas.
- **Cierre**: la última línea (pregunta) va con la tarjeta de pregunta grande (HUD); después el
  `cierre.py` (like + suscripción, voz corta) como hasta ahora.
- **Verificación antes de renderizar**: `check_framing` = 0 · `sync.py` VACIO = 0 y CIFRA_SIN_PANTALLA
  = 0 · hoja de sync mirada cuadro a cuadro · vista a 405 px legible. Después del render: `ritmo.py`
  quietos < 20 %, mov. mediano ≥ 4, sin plano > 6 s sin cambio.
- **Lo que se conserva de la v1**: las secuencias `tanque_n00-12`, `barra_d/g00-12`, `torre_n00-12`
  (ahora sobre el mapa o en la MESA, más grandes), los props `petrolero`, `poliza`, `hotel`, `sello_*`,
  `sentencia`, `cerca`, `gota`, `resolucion`, las banderas, `flecha_arriba`, `deposito_oil`.

## 1. PARTE 1 · THE EMPTY TANK (8 líneas, ~92 s)

**Mundo**: costa del Golfo de EE. UU. + Hormuz no cabe en una hoja → **dos mundos**: (a) `mundo_gulf`
bbox lon −100 … −86, lat 26 … 34 (Texas-Luisiana, vertical), rol EE. UU. `sujeto`; (b) para la línea 5
se reusa el `mundo_hormuz` de la pieza 2. Sitios de (a): **las cuatro localidades donde el DOE ubica
los domos de sal de la reserva** (F1.10 de `fuentes/referencia.md`): Freeport TX (Bryan Mound),
Winnie TX (Big Hill), Lake Charles LA (West Hackberry), Baton Rouge LA (Bayou Choctaw). **No se pinta
el domo en sí** (no hay coordenada citable del sitio): se marca la localidad con su nombre y el rótulo
del mapa dice `STRATEGIC PETROLEUM RESERVE · 4 SALT DOMES · TEXAS & LOUISIANA`. Coordenadas de las
localidades: Freeport 28.954 N −95.360 W · Winnie 29.820 N −94.384 W · Lake Charles 30.226 N
−93.217 W · Baton Rouge 30.451 N −91.187 W (verificar cada una contra su página de Wikipedia antes de
generar el mundo y anotar la fuente). Más Houston y New Orleans como referencia.

| Línea | Voz | Mapa / cámara | Objetos y HUD |
|---|---|---|---|
| 0 | 39 % full · Reagan | Plano abierto del Golfo con los 4 domos como pins ocre; viaje lento hacia Texas | Gancho (0-3,5 s) → CIFRA `39%` roja grande; `deposito_oil` grande (secuencia `tanque_n12` como estado inicial) a la izquierda; rótulo `THE RESERVE` |
| 1 | 285 M · week of Sept 4 · built for 727 | Cierra sobre Bryan Mound/Big Hill; los pins laten | CIFRA `285,360,000 BARRELS` (HUD) y debajo `BUILT FOR 727,000,000`; sello `EIA · WEEK OF SEPT 4` chico |
| 2 | 11 March · 172 M released | **MESA**: el decreto (`decreto`) cae grande; fecha `11 MARCH` roja | El burócrata (`01_burocrata`) al lado del decreto señalándolo (`point_at`); CIFRA `172,000,000 OUT` |
| 3 | The price went up 17 % | Vuelta al MAPA, plano medio; nada más se mueve salvo… | **La animación central**: `tanque_n` 12→0 (se vacía) a la izquierda MIENTRAS `flecha_arriba` crece a la derecha con `+17%` rojo (HUD). Sin subtítulo encima de la secuencia |
| 4 | 5 weeks · 19 M · Brent 104.61 | Viaje a lo largo de los cuatro domos (paneo) | `barril` con `$104.61` (HUD, rojo); `5 WEEKS · −19,000,000` |
| 5 | Reserve exists for one day · Hormuz | **Corte de contenido**: `mundo_hormuz`, plano abierto, Irán se pinta (rol `deudor` = rojo) mientras la voz dice "Hormuz"; viaje hacia el estrecho | Rótulo `THE STRAIT OF HORMUZ`; `petrolero` cruzando el estrecho por la ruta real (`route`) |
| 6 | 39 % · somebody is making money | Vuelta al Golfo, cierra sobre un domo | CIFRA `39%` vuelve (misma tarjeta), `deposito_oil` al 39 % (`tanque_n05`), `moneda` girando (`girar`) |
| 7 | Pregunta · Comments | Plano abierto, deriva | Tarjeta de pregunta `SHOULD A COUNTRY SPEND ITS RESERVE TO MOVE A PRICE?` + `COMMENTS` |

## 2. PARTE 2 · THE CHEAPEST WEAPON (7 líneas, ~95 s)

**Mundo**: `mundo_hormuz` bbox lon 47 … 62, lat 21 … 32 (Golfo Pérsico + Golfo de Omán, vertical si se
puede: probar lat 20 … 33). Roles: Irán `deudor` (rojo, se pinta en la línea 5), Omán/EAU `tercero`
(verde suave) desde el principio. Sitios: **Strait of Hormuz** (26,57 N 56,25 E), Bandar Abbas, Fujairah,
Ras Tanura, Kuwait City, Doha, Muscat. Ruta de los petroleros: Ras Tanura → Hormuz → Golfo de Omán
(puntos reales, `route`).

| Línea | Voz | Mapa / cámara | Objetos y HUD |
|---|---|---|---|
| 0 | −95 % · +3,600 % · nothing sunk | Plano abierto del Golfo; viaje hacia el estrecho | Gancho (0-3,5 s) → dos CIFRAS: `−95%` (rojo) y `+3,600%`; 12 `petrolero` chicos en fila sobre la ruta |
| 1 | 100+ ships a day · now 10 | Cierra sobre el estrecho | **Animación**: los 12 petroleros se apagan de izquierda a derecha hasta 1 (cada 0,3 s), CIFRA `100+ → 10` |
| 2 | Not a shortage of oil | Paneo hacia Ras Tanura (el petróleo está) | `barril` grande en Ras Tanura; tarjeta `NOT A SHORTAGE OF OIL` |
| 3 | Here is the mechanism · war-risk 7,5-10 % · $3-21 M | **MESA**: la `poliza` cae grande | El ejecutivo (`03_ejecutivo`) con la póliza en la mano (`hold`); CIFRAS `7.5% – 10% OF THE HULL` y `$3M – $21M PER VOYAGE` (rojo) |
| 4 | Owner charges for risk · fund ×36 · Brent 104 | Vuelta al MAPA, plano medio del Golfo de Omán | `flecha_arriba` creciendo con `36x SINCE JANUARY`; `barril` + `$104` |
| 5 | Iran did not have to sink the tankers · uninsurable | **Irán se pinta de rojo** mientras se nombra; cierra sobre Bandar Abbas | `bandera_ir` en Bandar Abbas; sello `UNINSURABLE` rojo cae sobre el estrecho |
| 6 | The cheapest weapon is a piece of paper · Comments | MESA: la póliza sola, grande, con `sello_no` | Tarjeta `A PIECE OF PAPER` + `COMMENTS` |

## 3. PARTE 3 · EIGHT MILLION A DAY (8 líneas, ~94 s)

**Mundo**: `mundo_uk` bbox lon −11 … 3, lat 49,5 … 59 (Islas Británicas, vertical). Rol Reino Unido
`institucion` (azul) desde el principio; Irlanda `tercero` tenue. Sitios: London (Home Office), Manchester,
Birmingham, Glasgow (donde hay hoteles de asilo: sin afirmar cuáles; los `hotel` van como props sobre
ciudades grandes, no como marcas de un hotel concreto).

| Línea | Voz | Mapa / cámara | Objetos y HUD |
|---|---|---|---|
| 0 | £8 M a day · Home Secretary said six | Plano abierto de las islas; viaje hacia Londres | Gancho (0-3,5 s) → CIFRA `£8,000,000 A DAY` (rojo); `hotel` ×3 sobre Londres/Manchester/Birmingham; tarjeta `THE DAY BEFORE: £6M` |
| 1 | It is in the Home Office's own accounts | **MESA**: `libro_mayor` cae | Rótulo `HOME OFFICE · ANNUAL ACCOUNTS`; el burócrata lo abre (`gesture`) |
| 2 | 2019: £4.5 bn → now £15.3 bn | MESA | **Animación**: `torre_n` 00→12 (la pila crece) con `2019 · £4.5bn` y `NOW · £15.3bn` (rojo) |
| 3 | Same contracts. Same ten years. | MESA | sello `SAME CONTRACT` cae con sacudida; tarjeta `MORE THAN 3× THE BILL` |
| 4 | Hotels take 76 % of cost · house 35 % | Vuelta al MAPA, plano medio de Inglaterra | **Animación**: `barra_d` (MONEY) y `barra_g` (PEOPLE) crecen a distinta longitud (HUD, grandes); CIFRA `76% vs 35%` |
| 5 | £4.2 bn year to March · £107 per person per day | Cierra sobre Londres | `factura` grande + CIFRA `£107 PER PERSON PER DAY` (rojo) |
| 6 | You can argue about how many should come. This is not that argument. | Plano abierto, la isla entera, deriva | Tarjeta `NOT THAT ARGUMENT` → `A PRICE PER NIGHT` (rojo) |
| 7 | Comments | — | Tarjeta de pregunta `WHO PAYS?` + `COMMENTS` |

## 4. PARTE 4 · THE PAPER THAT MOVED 49,000 (8 líneas, ~97 s)

**Mundo**: el del test `prueba_v4.py` (Estrecho de Gibraltar, bbox 16:9 → rehacerlo **vertical**: lon
−5,95 … −4,85, lat 35,40 … 36,45, ~2600 px de ancho). Roles: España `institucion` (azul) en "Ceuta is
Spain"; Marruecos `acreedor` (ocre) en "African mainland". Marcas de Ceuta POR ENCIMA del color
(trampa conocida). Sitios: Ceuta, Fnideq, Tarifa, Algeciras, Gibraltar, Tangier, Tetouan.

| Línea | Voz | Mapa / cámara | Objetos y HUD |
|---|---|---|---|
| 0 | 29 June ruling · 32 days later · 49,000 in 24 h | **MESA** primero (la `sentencia`, 2,5 s) → corte al MAPA abierto, viaje hacia Ceuta | Gancho (0-3,5 s); `29 · VI · 2026` rojo; `32 DAYS LATER`; CIFRA `49,000` roja enorme (HUD) |
| 1 | Ceuta is Spain, on the African mainland · fence · water at both ends | Cierra sobre Ceuta; **España azul** en "Spain", **Marruecos ocre** en "mainland" | Rótulo `CEUTA · SPAIN`; `cerca` (esquema) chica sobre el istmo con dos `gota` en los extremos |
| 2 | Returned on the spot · Supreme Court did NOT strike it down · fence vs sea | MESA: `martillo_juez` + la sentencia | Tarjetas `THE FENCE: SUMMARY RETURN` / `AT SEA: ORDINARY PROCEDURE` (rojo). El jurista (`05_jurista`) señala la segunda |
| 3 | Published · spread · around the end of the fence, through the water | MAPA cerrado sobre Ceuta | **Animación central**: `route` roja que rodea el extremo de la valla por el agua (puntos reales del istmo); `gota` que se enciende |
| 4 | 80,000 tried · capacity exceeded 2,400 % · at least 141 died | Plano medio | CIFRAS `80,000`, `+2,400%`; `sello_loss` + `AT LEAST 141 DIED` (sin gag, regla de graficidad) |
| 5 | By 3 August ~70,000 went back | Paneo hacia Fnideq/Tetouan | Tarjeta `3 AUGUST · ~70,000 WENT BACK`; multitud (`08_multitud` cutout) cruzando de vuelta |
| 6 | Nobody changed a law · nobody moved a fence · a court clarified… four days | MESA: la sentencia sola | `NO NEW LAW.` `NO NEW FENCE.` `ONE RULING.` (rojo) |
| 7 | Comments | MAPA abierto, deriva | `FOLLOW THE PAPER` + `COMMENTS` |

## 5. Costos y voz

- Imagen: 0 créditos (mapas por código, props existentes, rigs pagos).
- Voz: fal `eleven-v3` George con `timestamps: True` (≈ USD 0,43 las cuatro), dirección
  `direccion_s12.py` v2. `stability` 0,5; si sobra tiempo, la pieza 1 también a 0,0 y comparar con
  `voz/prosodia.py`.
