# HERRAMIENTAS DE MAPAS Y B-ROLL — análisis de lo que recomendó la otra IA

> Escrito el **2026-09-15**, a pedido de Agustín: *"analiza estas herramientas, si las podemos integrar
> bien para nuestros videos y mejorarlos"*. La lista analizada es la que le pasó otra IA: Animaps /
> Mapimator / Easymotion, Google Earth Studio, MapChart + CapCut, Flourish, After Effects + GEOlayers,
> Pexels / Storyblocks / Envato, y Kling / Hailuo / Freepik Spaces.
>
> **Todo lo que sigue es propuesta y opinión del asistente. Nada de esto es regla hasta que lo adoptes.**
> Los precios y las licencias están verificados hoy (fuentes al final); los de fal.ai están **medidos**
> con la API, no copiados de la web.

---

## 0. El resumen, en cinco líneas

1. **Las tres de mapas de pago (Animaps, Mapimator, Easymotion) no entran.** No por el precio: porque
   producen mapa de app —Mapbox/OSM, colores planos, pin rojo— y el canal se llama **Paper Trail**
   y tiene una paleta cerrada de 7 colores. Comprarías un mapa peor que el que ya tenés.
2. **Google Earth Studio sí, pero acotado y con una condición que nadie te dijo:** la atribución va
   **quemada en cada cuadro** y no se puede borrar, solo mover. Es gratis, exporta secuencia de imágenes
   (= entra directo a tu ffmpeg) y hasta exporta datos de cámara 3D para anclar etiquetas.
3. **Lo que en realidad querés de Earth Studio —"el planeta y después bajo a la región"— ya lo tenés
   gratis y sin marca de agua.** Lo probé hoy: `pruebas/look/globo.py`, 0 créditos, tu paleta,
   tu motor. Los dos cuadros fijos están en `pruebas/look/globo_europa*.png`.
4. **"Kling/Hailuo/Freepik por 10-15 USD/mes" es plata tirada: ya los tenés en fal, por uso.** Medido
   hoy: un clip de 5 s con Hailuo 02 fast sale **USD 0,085**. La suscripción más barata de esa lista
   cuesta lo mismo que **140 clips**.
5. **Nada de esto mueve la aguja del problema real.** El diagnóstico del 14-sep
   (`canal/ENFOQUE_VISTAS_SUBS_2026-09-14.md`) es conversión, no calidad de imagen: 9.117 vistas y
   12 suscriptores. Un mapa más lindo no hace que alguien vuelva mañana; la franquicia sí.

---

## 1. Contra qué se mide cualquier herramienta acá

No es "¿es buena?", es "¿entra en esta fábrica sin romper nada?". Cuatro filtros, en orden:

| # | Filtro | De dónde sale |
|---|---|---|
| 1 | **¿Respeta la paleta cerrada y el mundo de papel?** | `ESTILO.md` §2.1-2.2: recorte de papel, 7 colores, nunca blanco puro, grano + registro offset |
| 2 | **¿Mantiene los puntos 100 % exactos?** | Regla 24 de la skill (reclamo tuyo del 9-sep). Hoy el código **aborta el render** si un punto no está anclado a `mapa_pts.json` |
| 3 | **¿Cuánto cuesta por producción y es techo o cuota?** | Tope de **USD 4 por producción**, y es un techo, no un presupuesto (`canal/ASSETS.md`) |
| 4 | **¿Ataca el cuello de botella de hoy?** | `canal/ENFOQUE_VISTAS_SUBS_2026-09-14.md`: el problema es conversión y franquicia |

El filtro 2 es el que más descarta, y conviene tenerlo claro antes de seguir: **tu motor de mapas ya es
mejor que todas las herramientas de la lista en lo único que vos pediste a los gritos.** `mapa_*.py`
proyecta Natural Earth 50m con Mercator sin distorsión, escribe `mapa_pts.json` con el píxel exacto de
cada sitio, y cada prop se coloca con `G('Ciudad')`. Ninguna de las herramientas de pago te da eso:
te dan un pin que arrastrás con el mouse.

---

## 2. Mapas — veredicto herramienta por herramienta

| Herramienta | Precio real | Qué da | Veredicto |
|---|---|---|---|
| **Animaps** | free con marca de agua (12 renders/mes) · $9,90 · $19,90 /mes | zoom, resaltado de países, rutas | **No.** Look de app, y la marca de agua está justo en el plan gratis |
| **Mapimator** | free: 3 proyectos, 1 export 720p/mes con marca de agua · Pro $12/mes o $99/año | rutas animadas, "AI director" | **No.** Además su licencia free/Pro es "personal y online"; broadcast/publicidad pide Enterprise |
| **Easymotion** | $10 / $20 / $60 /mes | motion graphics por chat, mapas, gráficos | **No.** Es un generador genérico; el look no se parece en nada al tuyo |
| **MapChart + CapCut** | gratis | mapas de colores por país (alianzas, votos ONU) | **No, y ojo con la licencia:** es **CC BY-SA 4.0**. Pide atribución **y ShareAlike** — usar el mapa como base de un video te empuja a licenciar el derivado igual. Riesgo innecesario |
| **Flourish** | free (todo lo que hacés queda **público**) · pago a cotizar | gráficos de datos animados | **No por ahora.** El plan gratis publica tu trabajo; y una barra de papel animada la dibuja tu motor |
| **After Effects + GEOlayers 3** | **$329,99** el plugin + suscripción de AE | el estándar de la industria | **No.** No hay AE en el pipeline, y meterlo rompe la cadena Python→ffmpeg que hoy corre sola |
| **Google Earth Studio** | **gratis** (pide acceso, aprueban en días) | sobrevuelos satélite reales | **Sí, acotado.** Ver §3 |

### Por qué "look de app" es un problema y no un capricho

El canal vende una cosa: **los papeles del propio Estado, sobre una mesa**. El sello es de papel, el
mapa es una hoja, los personajes son recortes. Meter un mapa de Mapbox con un pin rojo en el medio del
episodio no es "mejorar el mapa": es decirle al espectador que el mapa lo hiciste en otro lado. Es el
mismo motivo por el que las personas reales entran como caricatura de papel y no como foto
(`ESTILO.md` §2.3, decisión tuya del 3-sep).

---

## 3. Google Earth Studio — el único que vale, con tres condiciones

**Lo que verifiqué hoy (fuentes al final):**

- **Gratis**, corre en Chrome de escritorio, se pide acceso con la cuenta de Google y la aprobación
  tarda días. Es gratis para uso **informativo, educativo, de investigación y sin fines de lucro**.
- **Exporta secuencia de imágenes** (ZIP de frames), no video. Esto para vos es una ventaja, no un
  problema: `produccion/motor.py:447` ya arma video con `ffmpeg -framerate 24 -i f_%06d.jpg`. Es la
  misma llamada.
- **Exporta datos de cámara 3D** junto con los frames. Con eso una etiqueta se ancla a un punto real y
  se queda pegada mientras la cámara baja: es compatible con la regla 24, no la viola.
- Resolución máxima **4096×2304**. De sobra para 1080p.
- **YouTube monetizado: permitido** mientras el video sea informativo/educativo/de entretenimiento.

**Las tres condiciones, y la primera es la que decide:**

1. **La atribución va quemada en cada cuadro y no se puede sacar.** Google la escribe sobre la imagen
   al renderizar ("Google Earth" + los proveedores de imágenes, y el texto **cambia según lo que se ve
   en el cuadro**). Lo único configurable es **dónde** aparece. No hay licencia para sacarla.
   → Para casi cualquier canal esto es una molestia. Para **Paper Trail** es casi un chiste interno:
   un canal que se llama "el rastro de papel" mostrando de dónde sacó la imagen. Si se usa, la
   atribución se abraza: se la deja abajo a la izquierda y se la trata como el pie de una foto pegada.
2. **Prohibido en material promocional o publicitario.** Si algún día hay un segmento de sponsor, ese
   segmento no puede llevar imagen de Earth Studio. Un video con un bloque patrocinado es zona gris.
   Anotarlo ahora es más barato que descubrirlo con el sponsor firmado.
3. **Rompe el look si entra crudo.** Satélite fotorrealista en medio de la mesa de papel es un
   injerto. Entra tratado: duotono a la paleta (papel/tinta), grano, y **borde de foto pegada sobre la
   mesa**, como un anexo del expediente. Con eso deja de ser "un video de Google" y pasa a ser "la foto
   que alguien imprimió y puso sobre la mesa".

**Dónde lo usaría, y en ninguna otra parte:** una sola vez por episodio, 3-6 segundos, en el momento
en que el guion aterriza en un lugar concreto y real —el puerto, la frontera, el edificio—. Es decir:
donde hoy no hay nada porque un mapa de papel no puede mostrar un edificio.

---

## 4. Lo que ya tenés gratis y probé hoy: el globo de papel

Antes de pedir acceso a nada, mirá esto. **El "descenso desde el espacio" —que es el 90 % de lo que la
gente quiere de Earth Studio— sale de tu propio motor, con tu paleta, sin marca de agua y a 0 créditos.**

```bash
python pruebas/look/globo.py
```

Salida (cuadros fijos, nada animado todavía):

- `C:\Users\agust\Desktop\agustin\canal_geopolitica\pruebas\look\globo_europa.png` — el planeta
- `C:\Users\agust\Desktop\agustin\canal_geopolitica\pruebas\look\globo_europa_zoom.png` — el final del descenso

Es lo mismo que `produccion/mapa_*.py` (Natural Earth 50m + PIL) pero en **proyección ortográfica**: la
Tierra como un disco de papel sobre la mesa de madera. Encadenando zooms crecientes con el mismo centro
sale el descenso, y el último cuadro **empalma con la hoja Mercator del episodio** que ya sabés hacer.

Lo que esto resuelve y Earth Studio no:

| | globo de papel | Earth Studio |
|---|---|---|
| Costo | 0 | 0 |
| Marca de agua | **no** | **sí, quemada, en todos los cuadros** |
| Paleta del canal | **sí** | solo con tratamiento |
| Puntos exactos | sí (mismo `pts.json`) | sí (datos de cámara 3D) |
| Muestra un edificio real | no | **sí** |
| Depende de un tercero | no | sí (acceso, términos, sponsors) |

**Complemento gratis del mismo palo:** Natural Earth publica rasters de **relieve sombreado** en
dominio público. Meter el relieve por debajo de la hoja, a baja opacidad y en tinta, le da profundidad
a los mapas sin tocar la paleta ni gastar un crédito. Es media hora de trabajo sobre `mapa_*.py`.

---

## 5. B-roll e imágenes — acá la recomendación de la otra IA tiene un agujero

### 5.1 Pexels y el contexto político

La licencia de Pexels dice que **las personas identificables no pueden aparecer "bajo mala luz ni de
forma ofensiva"**, y su propio centro de ayuda va más lejos: **contenido con personas no se usa en
contexto político**. Un canal de geopolítica es, literalmente, contexto político.

Traducido: de Pexels podés usar el puerto vacío, el oleoducto, la sala sin gente. En cuanto hay una
persona identificable —una cola en la frontera, una manifestación, un funcionario— estás fuera de la
licencia. Y eso, encima, choca con `ESTILO.md` §2.3: en este canal las personas van como caricatura de
papel. **Con lo cual el b-roll de stock con gente no te sirve ni legal ni estéticamente.**

Storyblocks y Envato: suscripción mensual. Mismo problema de look, y encima con cuota.

### 5.2 Lo que sí conviene, y es gratis

Para geopolítica hay archivo público de verdad, mejor alineado con "Paper Trail" que cualquier stock:

| Fuente | Licencia | Para qué |
|---|---|---|
| **NASA** (images.nasa.gov) | dominio público | Tierra desde el espacio, satélite |
| **Copernicus / Sentinel** (ESA) | libre, con la nota *"Copernicus Sentinel data [año]"* | imagen satelital real y reciente de una zona concreta |
| **DVIDS** (Departamento de Defensa de EE. UU.) | mayormente dominio público | material militar, despliegues |
| **Wikimedia Commons** | por archivo (mirar cada una) | edificios, actos oficiales |

Todo eso entra igual que Earth Studio: tratado a papel, como una foto pegada en la mesa. Y la nota de
atribución, otra vez, le queda bien al canal en lugar de afearlo.

### 5.3 Kling / Hailuo / Freepik: ya los tenés, y por uso

Esta es la parte donde la recomendación de la otra IA te hacía pagar de más. **Precios medidos hoy con
la API de fal**, que ya tenés conectada y prepaga:

| Modelo (fal) | Precio medido | Clip de 5 s |
|---|---|---|
| `minimax/hailuo-02-fast/image-to-video` | **$0,017 / s** | **$0,085** |
| `kling-video/v3/turbo/standard/image-to-video` | $0,112 / s | $0,56 |
| `kling-video/v3/standard/image-to-video` | $0,14 / s | $0,70 |
| `minimax/hailuo-2.3-fast/standard/image-to-video` | $0,19 por corrida | $0,19 |

Contra **$10-15 por mes** de una suscripción: el clip más barato sale 8,5 centavos, así que la cuota
más barata de la lista equivale a **~140 clips de 5 s**. Vos usás uno o dos planos hero por episodio.
**No hay ningún caso en que la suscripción gane.**

> **Corrección a `COSTOS.md` §12:** ese documento anotó el 8-sep "Kling 3.0 = $0,029/s". Hoy los
> endpoints v3 de Kling en fal miden **$0,112-0,14/s**. O subió, o la anotación era de otro endpoint.
> El número de $0,029 no debería usarse más para planificar.

Y el prompt que te pasó la otra IA (*"news documentary b-roll, no faces of real leaders, wide shot,
handheld, muted colors"*) está **bien** y es compatible con tus reglas: sin caras de líderes reales,
colores apagados. Lo único que le agregaría es el cierre de paleta: *"warm paper tones, desaturated,
grain"*, para que salga más cerca de la mesa y necesite menos tratamiento después.

---

## 6. Qué haría yo, en este orden

| # | Qué | Costo | Cuánto lleva | Por qué primero |
|---|---|---|---|---|
| 1 | **Mirar los dos PNG del globo** y decir sí o no al look | 0 | 2 min | Decide todo lo demás. Sin cuadro fijo aprobado no se anima nada |
| 2 | Si va: **globo → hoja** como apertura fija de la franquicia (*"What X Paid For"* abre siempre bajando al país) | 0 | medio día | Le da a la serie una apertura reconocible, que es justo lo que pide el diagnóstico del 14-sep |
| 3 | **Relieve sombreado** de Natural Earth debajo de las hojas | 0 | ~30 min | Profundidad sin tocar la paleta |
| 4 | **Pedir acceso a Earth Studio** (tarda días, mejor pedirlo ya aunque no se use todavía) | 0 | 5 min | No cuesta nada tenerlo disponible |
| 5 | Cuando llegue: **una prueba de 4 s tratada a papel** y comparar contra el globo | 0 | 1 h | Recién ahí se decide si aporta algo que el globo no dé |
| 6 | B-roll generativo: seguir en **fal por uso**, nunca suscripción | ~$0,09-0,56 por clip | — | Ya está conectado y entra holgado en el techo de USD 4 |

Lo que **no** haría: pagar Animaps, Mapimator, Easymotion, Storyblocks, Envato, Freepik ni GEOlayers.
Ninguna resuelve algo que el pipeline no resuelva, y todas te meten una cuota mensual en un canal que
todavía no cobra.

---

## 7. Lo que ninguna de estas herramientas arregla

Vale decirlo claro porque la otra IA arrancó con *"Mapas (aquí está el dinero)"*, y no es donde está el dinero.

- El canal tiene **9.117 vistas en 28 días y 12 suscriptores**: 1 cada ~830 vistas. Eso no es un
  problema de mapas, es la falta de una promesa repetida (`canal/ENFOQUE_VISTAS_SUBS_2026-09-14.md`).
- El paso 0 (`produccion/demanda.py`) ya mostró que lo que separa los aciertos de los fracasos es
  **de quién es el tema**, no cuán lindo quedó el mapa.
- Y el reloj de monetización (`canal/MONETIZACION_2027.md`) se mueve con **horas de reproducción de
  largos**, que dependen de retención, no de sobrevuelos.

Dicho eso: el ítem 2 de la tabla de arriba —la apertura fija del globo bajando al país— **sí** empuja
la franquicia, porque es lo que hace que dos videos distintos se reconozcan como la misma serie. Esa es
la única razón por la que vale la pena hacerlo ahora y no en dos meses.

---

## 8. Fuentes verificadas hoy (2026-09-15)

- Google Earth Studio — atribución: <https://earth.google.com/studio/docs/attribution/>
- Google Earth Studio — render y exportación: <https://earth.google.com/studio/docs/en_gb/making-animations/rendering/>
- Google Earth Studio — acceso y requisitos: <https://www.google.com/earth/studio/> · <https://earth.google.com/studio/docs/requirements/>
- Google — Geo Guidelines (usos permitidos y prohibidos): <https://about.google/brand-resource-center/products-and-services/geo-guidelines/>
- Animaps — precios: <https://animaps.ai/pricing>
- Mapimator — precios: <https://mapimator.com/pricing>
- Easymotion: <https://easymotion.io/>
- MapChart — términos (CC BY-SA 4.0): <https://www.mapchart.net/terms.html>
- Flourish — precios: <https://flourish.studio/pricing/>
- GEOlayers 3 — precio: <https://aescripts.com/geolayers/>
- Pexels — licencia: <https://www.pexels.com/license/> · reglas de uso: <https://help.pexels.com/hc/en-us/articles/360042332714>
- Copernicus Sentinel — licencia abierta: <https://open.esa.int/copernicus-sentinel-satellite-imagery-under-open-licence/>
- NASA — biblioteca de imágenes y video: <https://images.nasa.gov/>
- Precios de fal.ai: **medidos con la API** el 2026-09-15 (`mcp fal get_pricing`), no copiados de la web.

> Nota de método: la página de reglas de uso de Pexels devolvió 403 al asistente; su contenido sobre
> contexto político se leyó a través del buscador, no de la página directa. Conviene que lo mires vos
> antes de apoyarte en stock con personas.
