# NOMBRE — análisis de candidatos

> 2026-09-07. Agustín rechazó "The Map Table". Este documento es el análisis completo: criterios, 30 candidatos,
> verificación real de handles (dos vías: HTTP a youtube.com y yt-dlp), colisiones con canales existentes
> (búsqueda de YouTube con filtro "canal") y dominios (RDAP).
>
> **Decisión de Agustín (2026-09-07): Paper Trail.** Handle `@papertrail`, tagline `Follow the paper.`
> Marcas registradas revisadas en §5. Imágenes regeneradas en `out/`; tarjeta del cold open del video 1
> cambiada en `produccion/piloto.py` y `piloto2.py`.

---

## 1. Qué tiene que hacer el nombre

Del propio proyecto (`IDEA.md` §2 y §8, `ESTILO.md` §1-2):

1. **Decir "poder, fronteras, mundo" sin la palabra *geopolitics*** (en YouTube suena a granja de contenido).
2. **Nombrar el papel.** El estilo es el producto entero; el recorte de papel es lo que nadie más tiene.
3. **Ser una publicación, no una persona.** Nada de "X Explains" ni nombres propios.
4. **Un doble sentido, a ser posible.** La regla narrativa es que el dibujo hace los chistes con la cara seria;
   el nombre debería hacer lo mismo: sonar serio y tener un chiste adentro.
5. **Corto.** 1-2 palabras, legible en la ficha del avatar a 48 px, handle sin sufijos ni números.
6. **Sin dueño.** Ningún canal de más de ~10k suscriptores con el mismo nombre, ninguna marca fuerte que
   se coma los resultados de Google.
7. **No encerrar el nicho.** Nada de "LatAm" en el nombre: el ep. 1 es Rusia, el ep. 7 es el Sáhara.

Por qué *The Map Table* fallaba contra esto: cumple 1, 3 y 7 pero no tiene chiste (4), son tres palabras (5),
no nombra el papel (2) y suena a mueble.

---

## 2. Los finalistas (verificados 2026-09-07)

| # | Nombre | El doble sentido | Handle | Dominio | Colisiones reales |
|---|---|---|---|---|---|
| **1** | **Paper Trail** | *Follow the paper trail*: los documentos que deciden una disputa (tratados, leasings, pólizas, fallos). Es literalmente el método del canal ("follows the objects that decide it"). Y el canal está hecho de papel. | **`@papertrail` LIBRE** (verificado dos veces) | papertrail.tv libre; papertrail.com es de Papertrail (logs de SolarWinds, producto para devs) | ThePaperTrail 10,6k subs (14 videos, inactivo), arelle's paper trail 5,5k, Paper Trail Pro 1,9k. Un videojuego indie "Paper Trail" (2024). |
| **2** | **Papercut** | El recorte de papel (*paper cut-out*) y el corte de papel: la herida chiquita que duele más de lo que debería. Una póliza de seguro que deja en tierra a una superpotencia **es** un papercut. | **`@papercut` LIBRE** (verificado dos veces); `@papercutgeo` libre | papercutgeo.com libre; papercut.com es PaperCut Software (gestión de impresión) | PaperCut Software 5,8k subs, Papercut Audio 9,6k, una banda tributo a Linkin Park (la canción "Papercut"). Google lo domina el software. |
| **3** | **Paper Tigers** | El *paper tiger* de Mao: el poder que parece feroz y no lo es. Un canal sobre potencias que se caen por un repuesto o un seguro. Y son tigres de papel de verdad. | `@papertigers` **ocupado** (20 subs, 46 videos); `@thepapertigers` ocupado; `@papertigersgeo` libre | papertigers.tv libre; papertigers.com registrado | Paper Tiger Trading Co 20,8k, la película *The Paper Tigers* (2020), Paper Tiger (estudio de diseño). |
| 4 | The Dotted Line | Las fronteras en disputa se dibujan con línea de puntos; los tratados se firman *on the dotted line*. | `@thedottedline` ocupado (12 subs); `@onthedottedline` libre | thedottedline.tv libre | Solo canales de menos de 100 subs. |
| 5 | Chokepoint | El cuello de botella: canales, estrechos, puertos. Es el tema de la mitad de la cola de episodios. | `@chokepoint` ocupado (6 subs, vacío); `@thechokepoint` libre | chokepoint.tv libre | Bandas de ~1,4k. Baggage: "Operation Choke Point" (escándalo bancario de EE. UU.) y "chokepoint capitalism". Encierra el nicho en lo marítimo y "choke" es palabra sensible para anunciantes. |

### Descartados con motivo

| Nombre | Por qué no |
|---|---|
| Fine Print | Colisión real: Fine Print, 94,5k subs. |
| Paper Tiger (singular) | `@papertiger` ocupado por un canal de 10,5k con 124 videos. |
| Paper Atlas, Paper Borders, Buffer State, Terra Nullius, Hard Borders, Lines on Paper | Handle principal ocupado por canales chicos; sin doble sentido que justifique el sufijo. |
| Paper Sovereign, Paper Statecraft, Paper Straits | Libres, pero "sovereign" suena a canal de cripto, "statecraft" a think tank, "straits" encierra el tema. Sin chiste. |
| Paperweight | Libre, pero el chiste ("pisapapeles" = cosa inútil) va en contra del canal. |
| Scissors and Maps, Folded Borders, Cut and Paste Politics | Libres, pero suenan a tutorial de manualidades. |
| The Treaty Table, The Paper Frontier, Paper Dispatch | Mismo problema que The Map Table: descriptivos, tres palabras, sin chiste. |
| Contested | Búsqueda de YouTube la tapa Eurovision Song Contest. |

---

## 3. Recomendación: **Paper Trail**, con **Papercut** como segunda

**Paper Trail** es el único que cumple los 7 criterios a la vez, y el handle limpio `@papertrail` está libre,
lo que en 2026 es casi un milagro para dos palabras comunes en inglés. Es el nombre que un sponsor entiende
en un segundo (periodismo de documentos) y el que la descripción del canal ya está escribiendo sin saberlo.
Riesgo: el término lo usan tres canales chicos y un producto de logs para programadores. Ninguno compite por
la audiencia. Tagline: **`Follow the paper.`** (o mantener `Geopolitics, on paper.`).

**Papercut** es el nombre con más carácter y el que mejor cuenta el look. Pierde por Google: buscar
"papercut" da un software de impresión y una canción de Linkin Park, y va a seguir dando eso durante años.
Si preferís carácter sobre buscabilidad, es este. Tagline: **`Small cuts. Big maps.`**

**Paper Tigers** es el más geopolítico de los tres y se descarta solo por el handle: `@papertigersgeo` es
un sufijo, y la película de 2020 ocupa la búsqueda.

Los tres se ven en la ficha en `out/nombres/_hoja_nombres.jpg` (avatar A, avatar C y banner para cada uno).

---

## 5. Marcas registradas: "Paper Trail" (verificado 2026-09-07 en el buscador oficial de la USPTO y en TSDR)

La búsqueda `paper trail` en tmsearch.uspto.gov devuelve 8.567 resultados (incluye todo lo que contiene
"trail"). Los que llevan exactamente PAPER TRAIL / PAPERTRAIL:

| Marca | Titular | Clase | Cubre | Estado |
|---|---|---|---|---|
| **PAPER TRAIL** (reg. 7933698, serial 98316744) | **Newfangled Games Ltd** (Norwich, Reino Unido) | 9, 25, **41** | Software de videojuegos; ropa; y en clase 41: *"providing on-line computer games; providing online video games; entertainment services, namely, providing online puzzle games; online multiplayer video games"* | **VIVA, registrada el 09/09/2025** |
| PAPER TRAIL (serial 78690479) | Roaring Spring Blank Book Co. | 16 | Carpetas colgantes, separadores, sobres | Viva, registrada |
| A PAPER TRAIL OF LOVELINESS... | Effective Grants LLC | 35 | Redacción de subvenciones | Viva |
| PAPER TRAIL RECORDS (87027982) y PAPER TRAIL RECORDS CERTIFIED EST 2011 | Shaw, Alonzo | 41 | Producción de contenido multimedia | **Muertas, canceladas** |
| PAPER TRAIL (Dragon Army Apps) | — | 9, 41 | Juego descargable | Muerta |
| PAPER TRAIL (Wextech, software), PAPER TRAIL (vermut), PAPER TRAIL (agendas), THE PAPER TRAIL (Domtar), PAPERTRAIL ×4 (CUSP Point, Irlanda) | — | 9, 16, 33, 38, 42 | Varios | Todas muertas |
| PAPERTRAIL PROCESSING, PAYPERTRAIL | — | 35, 36 | Consultoría, finanzas | Pendientes |

Además: Newfangled Games tiene la misma marca en el Reino Unido (UK00003525973, solicitada el 23/08/2020,
por el videojuego *Paper Trail* de 2024). Papertrail de SolarWinds (logs para programadores) **no aparece
como marca viva en EE. UU.**; funciona como marca de uso.

**Lectura.** No hay ninguna marca viva de PAPER TRAIL para series de video, canales, documentales ni
contenido editorial. La única viva en la clase 41 (la de entretenimiento) es la de Newfangled Games y su
enunciado cubre **exclusivamente juegos en línea**. Un canal de geopolítica animada no es un juego, no
compite con uno y no se confunde con uno: el riesgo de que Newfangled pueda hacer valer su marca contra el
canal es bajo. Dos consecuencias prácticas:

1. **Operar el canal con este nombre no infringe nada verificable.** YouTube no exige marca para un nombre.
2. **Si algún día querés registrar PAPER TRAIL como marca propia en clase 41** (por ejemplo, para vender
   merchandising o licenciar), el examinador de la USPTO va a citar la de Newfangled, y habrá que argumentar
   la diferencia de servicios o limitar el enunciado a "series de video sobre geopolítica". Es un trámite
   discutible, no un bloqueo. En clase 25 (ropa) sí está tomada: nada de remeras "Paper Trail" sin abogado.

No verificado: EUIPO (Unión Europea) e INPI (Argentina). Para un canal de YouTube con audiencia en EE. UU. el
registro relevante es el de la USPTO; si el canal factura en Europa, repetir la búsqueda en euipo.europa.eu.

---

## 4. Cómo se verificó (para repetirlo con otro nombre)

- Handle: `curl -s -o /dev/null -w "%{http_code}" -H "Cookie: SOCS=CAI; CONSENT=YES+1" https://www.youtube.com/@handle`
  → 404 libre, 200 ocupado. Contraste con `yt-dlp --flat-playlist --playlist-items 1 https://www.youtube.com/@handle/videos`.
- Colisiones: `https://www.youtube.com/results?search_query=NOMBRE&sp=EgIQAg%253D%253D` (filtro canal), leer
  `ytInitialData` → `channelRenderer`.
- Dominio: `curl -s -L -o /dev/null -w "%{http_code}" https://rdap.org/domain/dominio` → 404 libre. Reintentar si 429.
- Scripts: `nombres_preview.py` (imágenes) y el chequeo en el scratchpad de la sesión del 2026-09-07.
