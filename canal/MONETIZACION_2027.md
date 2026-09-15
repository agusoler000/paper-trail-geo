# MONETIZACIÓN 2027 — lo que cambia, qué nos toca y qué no

> Comprobado el **2026-09-15** contra las fuentes oficiales de YouTube, a pedido de Agustín, después de analizar
> la clase abierta de Máximo Bruno (6-sep-2026). Este documento **no cambia ninguna regla**: reporta lo verificado
> y separa los hechos de las propuestas. Complementa `canal/MONETIZACION.md`, que sigue siendo el documento de
> riesgo de contenido.

---

## 1. Lo que dice YouTube, textual y con fuente

### 1.a El listón sube el 1-feb-2027 — CONFIRMADO

Fuente: [blog oficial de YouTube, *New opportunities to earn and changes to the YouTube Partner Program*](https://blog.youtube/news-and-events/youtube-partner-program-updates-2027-new-opportunities-earn/)

| | Hoy (hasta el 31-ene-2027) | Desde el 1-feb-2027 |
|---|---|---|
| Suscriptores | 1.000 | 1.000 (**no cambia**) |
| **Horas de visualización** (365 días) | **4.000** | **8.000** |
| Vistas de Shorts (90 días), vía alternativa | 10 M | **20 M** |

Textual: *«8,000 qualified watch hours in the last 365 days, or 20 million qualified Shorts views in the last 90 days»*.

Y la frase que define nuestra situación: *«This update won't impact creators already in YPP»* — **el que ya está
adentro no se ve afectado**. No hay prórroga ni transición para el que no llegó: si el 1-feb-2027 no estamos
monetizados, el umbral que nos aplica es 8.000.

**Quedan 139 días** (15-sep-2026 → 1-feb-2027).

### 1.b Qué cuenta como hora de visualización — CONFIRMADO, y esto es lo importante

Fuente: [blog oficial, *What counts as qualified watch hours and views*](https://blog.youtube/news-and-events/youtube-monetization-qualified-watch-hours-shorts-views/)

Cuenta:
- tiempo de reproducción de **videos largos públicos** (y podcasts), y de directos archivados.

**NO cuenta** (textual): contenido privado, oculto o borrado · contenido visto como anuncio ·
**el tiempo de reproducción de Shorts** · directos no archivados.

> **Consecuencia directa para nosotros: los Shorts no suman ni un segundo a las 4.000 horas.**
> Las series S01 a S11 —11-S, IA, el aviso del 7-O, la tanda de EE. UU., Suecia, islamización— no acercan
> el canal a la monetización ni un minuto. Solo los 9 largos cuentan.

### 1.c La otra vía, la de Shorts, no es una vía para nosotros

Para *entrar* hacen falta 10 M de vistas de Shorts en 90 días (20 M desde febrero). Aparte, desde el 1-feb-2027
para *cobrar por Shorts* hacen falta 10 M de vistas cualificadas en 90 días; por debajo de eso el canal sigue en
el programa y cobra por los largos. Con nuestros números, esta vía no existe.

### 1.d «Contenido inauténtico» — CONFIRMADO, y NO estamos en la zona roja

Fuente: [*YouTube channel monetization policies*](https://support.google.com/youtube/answer/1311392?hl=en).
El 15-jul-2025 la política de *repetitious content* pasó a llamarse **inauthentic content**.

**Lo que queda fuera de monetización** (textual): *«similar or repetitive content with low educational value»* ·
*«image slideshows, templated storylines, or scrolling text»* con narrativa mínima ·
*«AI-generated content made with generic or unoriginal templates»* sin la perspectiva original del autor.

**Lo que está permitido, también textual:**
- *«Same intro and outro for your videos, but the bulk of your content is different»* → nuestra intro de 14 s y
  outro de 20 s fijas **no son un problema**, están descritas como caso permitido.
- Series donde cada entrega tiene *«distinct storyline, focus, or concept»* → la franquicia **What X Paid For**
  propuesta en `ENFOQUE_VISTAS_SUBS_2026-09-14.md` cae exactamente en la casilla permitida.
- IA sí, siempre que el resultado *«must still demonstrate your creative vision»*.

**Contraste con nuestro pipeline** (revisado hoy en `videos/S10_suecia/escenas.py`): los cortes caen en
0,0 · 5,0 · 9,4 · 10,8 · 13,6 s — duración variable, no el patrón de 3-4 s fijos que describe la clase como marca
de los canales purgados. Guion propio, arte propio, mapa propio verificado por código. **No hay que cambiar nada
por esta política.** Lo que sí conviene es no perder eso de vista si algún día se industrializan los shorts con un
molde único.

### 1.e Declaración de contenido sintético — lo que ya dice `MONETIZACION.md` es correcto

Fuente: [*Disclosing use of altered or synthetic content*](https://support.google.com/youtube/answer/14328491).
Se declara el contenido **realista** que pueda confundir: una persona real diciendo lo que no dijo, metraje de un
lugar real, un evento que no ocurrió. **No** se declara la animación no realista, ni *«production assistance, like
using generative AI tools to create or improve a video outline, script, thumbnail, title, or infographic»*.

Narración con voz de IA sobre animación de papel → **no requiere declaración**. Sigue valiendo la excepción ya
escrita: si entran planos generativos de personas reales, se marca **Sí**.

---

## 2. Lo que la clase dice mal

| Afirmación de la clase | Qué es verdad |
|---|---|
| «YouTube cuenta todas las vistas pero **solo paga la vista con intención**, la que pasa los 30 segundos» | **Falso para los largos.** No hay ningún umbral de 30 s publicado: la hora cualificada es tiempo de reproducción de un video público largo, y punto. El concepto de *engaged view* existe, pero es **de Shorts** (textual: *«the viewer stayed to watch past the initial seconds, and does not include any loops»*) y sirve para la **elegibilidad**, no para el pago. Lo de «te pagan por la vista con intención» no está en ninguna política. |
| «Con 200.000 vistas de un video pasás las 4.000 horas» | **Verdadero, y por debajo.** Con nuestros largos (~18 min) bastan **~53.000 visualizaciones** a un 25 % de retención. La aritmética está en §3. |
| «Las 8.000 horas son solo un video más» | Verdadero en aritmética, engañoso en la práctica: es un video más **de los que pegan**, no un video más de los que hacemos. |

---

## 3. Dónde estamos, con los números reales

Leído hoy con `yt-dlp` del canal público (`@papertrailgeo`), los 8 largos con vistas:

| Video | Duración | Vistas |
|---|---|---|
| FEAR: Half a German State Just Voted Far Right | 18:48 | 478 |
| EXPOSED: Falklands or Malvinas | 33:12 | 278 |
| COLLAPSE: AI Moves 15% of the Economy | 18:27 | 250 |
| SHOCK: 25 Years After 9/11 | 18:46 | 84 |
| Is This the End of the United Kingdom? | 21:05 | 78 |
| How Ukraine Grounded Russia's Airlines | 16:57 | 77 |
| NEWS 14-09 | 18:47 | 3 |
| $6.06 Diesel: Saudi Arabia Just Shut the Pipe | 18:15 | 2 |
| **Total** | | **1.250** |

Si **todos** hubieran visto el 100 % de cada video: 457 horas. A una retención realista del 25-30 % para un canal
nuevo: **entre 110 y 140 horas** de las 4.000. Estamos en el **3 %** del umbral, con 139 días por delante.

**Las dos formas de llegar, en números:**

- **Por goteo:** ~43.600 visualizaciones de largo en 139 días = **314 por día**. Hoy el canal hace del orden de
  60 por día contando todo. Es multiplicar por cinco y sostenerlo cuatro meses y medio.
- **De un golpe:** **un solo largo con ~53.000 vistas** cierra el asunto. Un video de 18 min visto al 25 % son
  4,5 minutos por espectador; 53.000 × 4,5 min = 4.000 horas.

La segunda es la que ocurre de verdad en canales nuevos, y es exactamente el caso Nepal de la clase: el canal
tenía videos de 200 vistas y uno hizo 2,8 M.

---

## 4. Los tres problemas, ordenados por lo que cuestan

**1. El esfuerzo está yendo a donde no cuenta.** Desde el 8-sep se produjeron once series de shorts (S01-S11).
Ninguna suma una hora cualificada. Los largos, que son lo único que cuenta, son 9 y dos de ellos tienen 2 y 3
vistas. No es que los shorts no sirvan —sirven para descubrimiento y para suscriptores— pero **el reloj de
febrero solo lo mueven los largos**.

**2. La ventana es de 139 días y el umbral se duplica después.** No hay transición: o el canal está adentro el
31-ene-2027, o el listón pasa a 8.000 horas y a 20 M de vistas de Shorts.

**3. El problema de conversión ya diagnosticado el 14-sep sigue siendo el cuello.** Un suscriptor cada 830
vistas. El caso Nepal dice lo mismo que `ENFOQUE_VISTAS_SUBS_2026-09-14.md`: el canal que pegó **repitió el
mismo tema cuatro veces** (2,8 M · 1,2 M · 500 k · 2 M) y se cayó cuando cambió la palabra clave de *Nepal* a
*Himalaya*. Saltar de tema es lo que estamos haciendo.

---

## 5. Propuestas (del asistente — ninguna es regla hasta que Agustín la adopte)

1. **Un largo por semana como mínimo, y los shorts colgando de ese largo**, no como producciones sueltas. Es la
   única palanca que mueve las 4.000 horas.
2. **Repetir la franquicia en vez de cambiar de tema**: *What Sweden Paid For* ya existe; *Britain*, *France*,
   *Belgium*, *Germany* están escritos como cola en el ENFOQUE del 14-sep. Es lo que hizo el canal de Nepal, y es
   además la casilla que la política de contenido inauténtico permite por escrito.
3. **La palabra clave exacta en el título**: el país que la gente busca, adelante. Ya es la regla de la bandera en
   la miniatura, aplicada al texto.
4. **Antes de elegir tema, mirar Google Trends**: la lección del video es que el canal de Nepal se cayó por hacer
   un video de un tema cuya demanda ya había pasado.
5. **Método gratis de tema probado** (de la clase, min 1:54-2:00): en un canal del nicho que funcione, pestaña
   *Popular* → copiar el título de su video top → pegarlo en la búsqueda de YouTube filtrando por popularidad. Si
   la misma idea hizo millones hace seis años, hace tres y hace tres meses, está probada; se hace con otro ángulo.
   Es el «outlier» que ViewStats cobra, hecho a mano.

---

## 6. Qué NO hay que cambiar

- La intro y outro fijas: permitidas por escrito.
- La declaración de contenido sintético: lo que dice `MONETIZACION.md` está bien.
- El pipeline de animación: los cortes ya tienen duración variable y el arte es propio.
- Las reglas de riesgo de contenido de `MONETIZACION.md`: nada de lo comprobado hoy las toca.

---

## Fuentes

- [YouTube Blog — New opportunities to earn and changes to the YouTube Partner Program](https://blog.youtube/news-and-events/youtube-partner-program-updates-2027-new-opportunities-earn/)
- [YouTube Blog — What counts as qualified watch hours and views](https://blog.youtube/news-and-events/youtube-monetization-qualified-watch-hours-shorts-views/)
- [YouTube Help — Channel monetization policies (inauthentic content)](https://support.google.com/youtube/answer/1311392?hl=en)
- [YouTube Help — YouTube Partner Program overview & eligibility](https://support.google.com/youtube/answer/72851?hl=en)
- [YouTube Help — Disclosing use of altered or synthetic content](https://support.google.com/youtube/answer/14328491)
