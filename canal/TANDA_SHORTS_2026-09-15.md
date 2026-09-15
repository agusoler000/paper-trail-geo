# Tanda de 3 shorts para hoy — 15-sep-2026

> Pedido de Agustín: *"busca el google trends cuál es la tendencia número 1, la 2 y la 3 en YouTube
> que aplique a la temática de nuestro canal y dame la idea para generar 3 shorts para publicar hoy.
> Objetivo: 5 suscriptores nuevos gracias a esta tanda"*.
>
> Todo lo que sigue está **medido**, no intuido: Google Trends con la propiedad *YouTube Search*
> (`gprop='youtube'`), el RSS oficial de Trending Now, y `produccion/demanda.py` (señales A-D) sobre
> cada candidato. Los datos de la reserva son de la serie semanal de la EIA leída hoy.
>
> **Las ideas son propuesta del asistente.** El tema lo elegís vos (regla 13).

---

## 1. Lo que dice Google Trends hoy

### 1.1 Trending Now del día (RSS oficial, 15-sep 12:55)

Lo que subió hoy y **aplica al canal** (el resto era MLB, Harry Styles, Below Deck, el clima):

| Geo | Puesto | Término | Tráfico | La noticia detrás |
|---|---|---|---|---|
| US | **5** | `iran war hormuz` | **5.000+** | 54 ataques aéreos saudíes sobre los hutíes; combates en Yemen |
| US | **10** | `immigration` | **5.000+** | Estados demandan para frenar la regla de green cards |
| US | 4 | `petroleum` | 100+ | **La reserva estratégica al nivel más bajo desde 1982**; el DOE dice que la va a rellenar |
| GB | 8 | `space force` | 200+ | **EE. UU. confirma por primera vez que tiene armas desplegadas en el espacio** |

### 1.2 El ranking que importa: interés DENTRO de YouTube, en US **y** en UK

Trending Now mide el buscador web. Lo que nos paga es lo que la gente busca **dentro de YouTube**.

> **Corrección sobre la primera versión de este documento.** La primera tabla que escribí daba
> `space weapons` 41,2 y `strategic petroleum reserve` 37,8 contra `iran war` 8,8. **Esos números no
> eran comparables entre sí**: salían de consultas separadas, y Google Trends normaliza cada serie
> contra *su propio* pico, no contra las demás. Medidos en un mismo grupo, el cuadro es otro y la
> decisión cambia.

**Los tres, en el mismo grupo** (`gprop='youtube'`, 4 semanas):

| Término | **US** | **UK** | Mundial |
|---|---|---|---|
| **iran war** | **8,8** | **8,0** | **5,2** |
| space weapons | 0,0 | 0,0 | 0,0 |
| strategic petroleum reserve | 0,0 | 0,0 | 0,0 |

Los dos últimos dan cero **porque `iran war` los aplasta**. Escalonando la medición para ordenarlos
entre ellos (grupo sin el ancla grande, luego encadenado):

| Término | US (escala `iran war` = 8,8) | UK (escala `iran war` = 8,0) |
|---|---|---|
| **iran war** | **8,8** | **8,0** |
| immigration | 3,5 | **5,8** |
| world war 3 | 1,0 | 1,0 |
| space weapons | ≈ 0,2 | ≈ 0,0 |
| space force | 1,0 | 0,0 |
| strategic petroleum reserve | ≈ 0,01 | 0,0 |
| oil prices / petrol prices | 0,0 | 0,0 |

**Irán tiene entre 40 y 50 veces más búsqueda dentro de YouTube que los otros dos, en los dos
países.** `space weapons` fue trending hoy en UK, pero es una noticia de un día, no una búsqueda:
en YouTube el volumen es residual. `strategic petroleum reserve` es directamente un nicho.

### 1.2.b La palabra del título, medida (regla 27)

| Término | **US** | **UK** |
|---|---|---|
| **iran war** | **37,0** | **49,5** |
| gas prices | 4,2 | 1,8 |
| strait of hormuz | 1,0 | 1,8 |
| oil crisis | 0,2 | 0,8 |
| petrol prices | 0,0 | 0,5 |

**`IRAN WAR` es la palabra, y en UK pega más fuerte todavía que en US.** Va adelante en los tres
títulos. `gas prices` es el segundo término útil, sólo en US.

### 1.2.c Lo que esto cambia

El tema no cambia — **el recibo del petróleo sigue siendo el ángulo**, porque la señal D dice que la
noticia de Irán es de los medios y el recibo no lo está dando nadie. Lo que cambia es **la puerta de
entrada**: estas piezas no se titulan «strategic petroleum reserve» (que nadie busca en ninguno de
los dos países). Se titulan **`IRAN WAR` + la cifra**, y por dentro entregan el recibo.

### 1.3 Y lo que decide si se produce o no: **de quién es el tema** (señal D)

`produccion/demanda.py` sobre los tres:

| Tema | Mejor creador | Mejor medio | Dueño | Veredicto |
|---|---|---|---|---|
| **space weapons** | Veritasium **15.848.670** | Firstpost 8.393 | **creadores ×1888** | 🟢 **LUZ VERDE — EVERGREEN** |
| **strategic petroleum reserve** | Zeihan **826.169** | WSJ 434.670 | **creadores ×1,9** | 🟢 **LUZ VERDE — EVERGREEN** |
| **iran war / hormuz** | Max Afterburner 272.065 | **CNN 1.300.046** | **medios ×4,8** | 🔴 **NO — ES DE LOS MEDIOS** |

**Esto es lo más importante del informe.** El tema que trae el tráfico (Irán, 5.000+ búsquedas hoy,
la ola abierta y caliente) es exactamente el caso del video de diesel del 14-sep: **4 vistas con la
ola abierta**, porque la audiencia de esa búsqueda quiere la noticia y la va a buscar a CNN.

Y hay un hallazgo mejor:

> **`strategic petroleum reserve` tiene 37,8 de demanda y NADIE publicó en 7 días.**
> Demanda alta, oferta cero, y el interés saltó de 2,9 a 37,8 en cuatro semanas. Es un hueco abierto.

---

## 2. La jugada: colgarse de la ola de Irán sin competir por la noticia de Irán

Los medios tienen el hecho (barcos atacados, precios, Yemen). Nosotros tenemos **el recibo**, que es
literalmente lo que se llama el canal.

El recibo existe, está en papeles del propio Estado y es demoledor:

| Dato | Valor | Fuente |
|---|---|---|
| Reserva estratégica de EE. UU. | **285.360.000 barriles** (4-sep-2026) | serie semanal EIA |
| Nivel anterior comparable | **5 de noviembre de 1982** | EIA / DOE |
| Capacidad de diseño | 727.000.000 barriles → **está al 39,3 %** | DOE |
| Lo que perdió en 5 semanas | 19,4 M barriles (304,8 M el 31-jul) | EIA |
| Lo que se liberó | **172 M barriles**, autorizados el 11-mar-2026 | DOE |
| Dentro de | acción colectiva de la AIE de **400 M barriles** | AIE |
| Qué pasó con el precio | **subió más de 17 %** desde el anuncio | — |
| Brent / WTI hoy | **104,61 / 100,05 USD** (11-sep) | — |
| Tráfico en Hormuz | **cayó 95 %**: de 100+ barcos/día a 5-12 | Kpler |
| Seguro de guerra por viaje | 7,5-10 % del casco = **3 a 21 M USD** | — |

Y el contraste que convierte esto en una historia y no en una noticia:

| | **2022** | **2026** |
|---|---|---|
| Vendió | 180 M barriles a **95 USD** de media | 172 M barriles con el barril a **100+** |
| Recompró | 59 M a menos de **76 USD**, 140 M a ~74 USD | pendiente, con el barril a **104,61** |
| Resultado | **ganó ~3.500 M USD** | el hueco son **441,6 M barriles** |
| | | a 104,61 = **≈46.200 M USD** |
| | | presupuesto pedido: **20.000 M USD** |

**En 2022 la reserva ganó plata haciendo esto. En 2026 la misma maniobra sale al revés.** Ése es el
video, y no lo está dando nadie.

El plan del secretario de Energía Chris Wright para rellenarla —canjear crudo pesado venezolano por
crudo estadounidense— cierra el arco solo.

---

## 3. LA PROPUESTA · una serie de 3 partes, no 3 temas sueltos

### Por qué serie y no tres temas

El objetivo que pusiste no es vistas, son **5 suscriptores**. El diagnóstico de
`ENFOQUE_VISTAS_SUBS_2026-09-14.md` dice que el canal convierte **1 sub cada ~830 vistas**. A esa
tasa, 5 subs necesitan **~4.150 vistas**. Tres shorts sueltos pueden hacer esas vistas y aun así
dejar 1 o 2 subs, porque el que llega no tiene ninguna razón para volver.

Lo que cambia la **tasa** —no el volumen— es que las tres piezas sean una sola historia partida en
tres, donde la 1 no se entiende sin la 2 y la 3 es el remate. Ahí suscribirse deja de ser un pedido y
pasa a ser la forma de no perderse el final.

### La serie

> **THE EMPTY TANK** — *What America Paid For* · 3 partes, hoy.
> Misma franquicia que *What Sweden Paid For*, mismo molde, mismo arte, mismo sello.

---

### PARTE 1 · «El tanque»

**Gancho (primeros 3 s, la cifra dura primero):**
> *"Two hundred eighty-five million barrels. That's everything America has left underground for an
> emergency. The last time it was this low, Ronald Reagan was in his first term."*

**Cuerpo (~55 s):** qué es la reserva, dónde está (cuatro domos de sal en Texas y Luisiana), para qué
se construyó (el embargo de 1973), y el gráfico que baja: 304,8 M el 31 de julio → 285,4 M el 4 de
septiembre. Cinco semanas, 19,4 millones de barriles. El 39 % del tanque.

**Cierre que entrega:**
> *"But the empty tank isn't the bill. The bill is what it costs to fill it back up — and four years
> ago, the exact same move made America three and a half billion dollars. Part two, tonight."*

**Título:** `285 million barrels: why is America's emergency oil at a 1982 low? #oil #geopolitics #energy`
**Miniatura:** bandera de EE. UU. + tanque + la misma pregunta.
**Duración:** 60-70 s.

---

### PARTE 2 · «La jugada que funcionó»

**Gancho:**
> *"In 2022, America sold 180 million barrels of emergency oil at ninety-five dollars. Then it bought
> them back at seventy-four. That's not a mistake. That's a trade — and it cleared three and a half
> billion dollars."*

**Cuerpo (~55 s):** cómo funciona el mecanismo. Vender caro en la crisis, recomprar barato cuando
pasa. El manual dice que la reserva no es sólo un seguro: es una palanca de precio. Con los números
del DOE: 180 M a 95, recompra de 59 M por debajo de 76 y 140 M a ~74.

**Cierre que entrega:**
> *"So the playbook works. Which raises the only question that matters this week: what happens when
> you run the same play — and the price goes the other way? Part three, tonight."*

**Título:** `Who made $3.5 billion selling America's oil? The same tank, four years ago. #oil #energy #geopolitics`

---

### PARTE 3 · «La jugada al revés» — el remate

**Gancho:**
> *"March eleventh. America opens the reserve to push the price down. The price goes up seventeen
> percent."*

**Cuerpo (~65 s):** la aritmética del recibo. El hueco hasta capacidad son 441,6 millones de
barriles. Al precio de hoy, 104,61, son unos 46.000 millones de dólares. El presupuesto pedido eran
20.000. Y la propuesta sobre la mesa para taparlo es canjear crudo pesado **venezolano**. Hormuz
cerrado al 95 %, el seguro de guerra entre 3 y 21 millones por viaje.

**Cierre:**
> *"The oil went out at a hundred. It has to come back at a hundred and four. That's the receipt —
> and somebody signs it."*
> Outro que **nombra lo que viene**: `SPACE. TOMORROW.` + `SUBSCRIBE`

**Título:** `What does it cost to refill? 441 million barrels at $104. #oil #venezuela #geopolitics`

---

### Cómo se publican

| Pieza | Hora (propuesta) | Por qué |
|---|---|---|
| Parte 1 | **~15:00 ET** | antes del pico de tarde en EE. UU. |
| Parte 2 | **~18:30 ET** | el que vio la 1 la encuentra fresca |
| Parte 3 | **~21:00 ET** | prime time; es el remate y el que pide el sub |

Las tres con **video relacionado apuntando a la anterior** (los 12 shorts del 11-S no lo tenían) y la
1 enlazando a la 2 en cuanto exista.

### Costo

**0 créditos de fal.ai en imagen.** `prop_deposito_oil.png` ya está pagado, y los rigs que hacen falta
—burócrata, ejecutivo, trabajador— también. Sólo voz: **≈0,46 USD** por las tres piezas. Muy por
debajo del techo de 4 USD (regla 15).

---

## 4. Si preferís 3 temas sueltos en vez de la serie

Opción B, más techo de vistas, menos conversión:

| # | Short | Demanda YT | Dueño | Costo extra |
|---|---|---|---|---|
| 1 | **«America just admitted it has guns in orbit»** — Troy Meink lo confirmó el 14-sep; el Tratado de 1967 prohíbe armas nucleares en órbita, **no convencionales**. 59 años de hueco en el papel. | **41,2** | creadores ×1888 | 1 cr (satélite) |
| 2 | **«El tanque vacío»** — la Parte 1 de arriba, como pieza cerrada. | 37,8 | creadores ×1,9 | 0 cr |
| 3 | **«Por qué abrir la reserva no bajó el precio»** — la Parte 3 de arriba, como pieza cerrada. | 37,8 | creadores ×1,9 | 0 cr |

El de las armas en órbita es, sobre el papel, **el tema con más techo de los tres** (Veritasium hizo
15,8 M con esto; Wendover 1,9 M) y hoy los que publican son creadores chicos de 16-22k, no los
medios. Pero su demanda viene **bajando** (64,2 → 41,2) y pide un asset nuevo.

---

## 5. Dos cosas que hay que decidir antes de arrancar

1. **Hay 3 shorts de Suecia (`videos/S10_suecia/`) terminados y sin subir**, con `SUBIR.md` y
   `PLAN_SUBIDA.json` hechos. Si el objetivo es suscriptores **hoy**, publicar una serie que ya
   existe cuesta 0 y sale en minutos. Producir esta tanda nueva son horas. No es excluyente —pero es
   tu llamada cuál sale primero.
2. **Postura** (regla 13): el sujeto de esta serie **no es un presidente**. Es la reserva y la
   política de reservas, que cruza dos administraciones —2022 vendió y recompró con ganancia, 2026
   liberó con el precio subiendo—. Ése es el encuadre que propongo: más honesto, más fuerte, y sin
   riesgo de monetización por tema partidario. Si querés otro, se cambia antes del guion.

---

## Fuentes

- Google Trends — Trending Now RSS (US, GB) y *YouTube Search* vía `pytrends`, 15-sep-2026.
- [EIA — Weekly U.S. Crude Oil Stocks in the SPR](https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=pet&s=wcsstus1&f=w) · 285.360 mil barriles al 4-sep-2026.
- [DOE — United States to Release 172 Million Barrels of Oil From the SPR](https://www.energy.gov/articles/united-states-release-172-million-barrels-oil-strategic-petroleum-reserve)
- [DOE — Final purchase for the SPR: 200 million barrels at a good deal for the taxpayer](https://www.energy.gov/articles/biden-harris-administration-makes-final-purchase-strategic-petroleum-reserve-secures-200)
- [S&P Global — Biden administration completes 'final' SPR refill purchase](https://www.spglobal.com/energy/en/news-research/latest-news/crude-oil/110824-biden-administration-completes-final-strategic-petroleum-reserve-refill-purchase)
- [CNBC — Oil in SPR falls below 300 million barrels](https://www.cnbc.com/2026/08/10/oil-in-strategic-petroleum-reserve-falls-below-300-million-barrels-lowest-since-1983.html)
- [Washington Examiner — Wright says DOE will refill SPR in next months as prices soar](http://www.washingtonexaminer.com/policy/energy-and-environment/4725701/chris-wright-energy-department-refill-strategic-petroleum-reserve-prices-soar/)
- [Washington Examiner — Wright explains how Venezuelan crude will 'fill' the SPR](http://www.washingtonexaminer.com/policy/energy-and-environment/4712733/chris-wright-venezuelan-crude-fill-strategic-petroleum-reserve/)
- [CNBC — Iran war oil prices, freight, tankers, shipping](https://www.cnbc.com/2026/09/13/iran-war-oil-prices-freight-tankers-shipping.html)
- [Al Jazeera — Oil prices surge as US-Iran strikes intensify in Strait of Hormuz](https://www.aljazeera.com/economy/2026/9/7/oil-prices-surge-as-us-iran-strikes-intensify-in-strait-of-hormuz)
- [DefenseScoop — Meink: Space Force has deployed space control weapons to orbit](https://defensescoop.com/2026/09/14/meink-space-force-has-deployed-space-control-weapons-to-orbit/)
- [CNN — US military confirms it has deployed weapons in space](https://www.cnn.com/2026/09/15/science/us-space-force-weapons-capabilities-hnk)
- [NASA — Outer Space Treaty, 1967 (texto, Art. IV)](https://www.nasa.gov/history/SP-4225/documentation/cooperation/treaty.htm)
- [EJIL — Legality of the Deployment of Conventional Weapons in Earth Orbit](https://academic.oup.com/ejil/article/18/5/873/398694)

Salidas crudas de `demanda.py`: `d_iran.txt`, `d_spr.txt`, `d_space.txt` en el scratchpad de la sesión.
