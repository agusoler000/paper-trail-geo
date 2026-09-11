# ESTILO — narrativa y dirección de arte

> Biblia de estilo del canal de geopolítica en inglés. Todo guion, plano e imagen se valida contra este archivo.
> Idioma del canal: **inglés**. Idioma de trabajo: español.
> Creado: 2026-08-31, tras investigación con 14 agentes + verificación adversarial + prueba de render real.
> Complemento técnico: `ANIMACION.md`. Estrategia y negocio: `IDEA.md`.

---

## 0. Lo que cambió respecto de IDEA.md

`IDEA.md` §7 recomendaba **ilustración editorial animada con parallax** y descartaba la caricatura
("costo alto, baja la cadencia a 1-2 videos/mes"). El requisito nuevo es innegociable: **caricatura
animada con movimiento real, nada de Ken Burns ni parallax como recurso principal**.

Ese requisito **es viable**, pero obliga a romper otra cosa. La investigación lo dejó sin ambigüedad
(§6 de este documento). La decisión tomada acá: **se conserva la caricatura y se rompe la cadencia
semanal de 8-12 min.**

---

## 1. La regla madre: *Deadpan Dispatch* — REVISADA 2026-09-07

> **Decisión de Agustín:** el relato tiene que provocar preocupación y ganas de saber más. El guion sigue sin
> chistes verbales (el dibujo hace el humor), pero la NARRACIÓN es dramática: voz baja, pausas antes de cada
> revelación, ganchos al final de cada acto, música de tensión con arco por acto. "Cero emoción" queda derogado.


> **El guion es 100 % serio. El dibujo hace todos los chistes.**

El narrador nunca guiña el ojo, nunca comenta que algo es absurdo, nunca hace un remate hablado.
Dice el hecho en tono plano. El humor, la ironía y el golpe emocional viven **enteros en la imagen**.

**Por qué, razón comercial.** La tensión "caricatura vs. sponsors serios" es falsa y hay evidencia
dura: el socio creador más seguido de NordVPN es OverSimplified, que dibuja monigotes de palito;
Kurzgesagt hace pájaros de dibujo animado sobre temas de vida y muerte y sostiene Brilliant y Ground
News. Lo que compra un sponsor de ese tier no es el estilo de dibujo: es el **tono de la narración**
y la **trazabilidad de las fuentes**.

**Por qué, razón técnica — y es la que decide.** Kokoro y Chatterbox no pueden clavar timing cómico.
Un chiste hablado depende de una pausa de 300 ms y de una inflexión que el TTS no controla. Meter
humor en el guion es apostar a lo único que la fábrica no sabe hacer. Un remate visual, en cambio,
es timing de corte: se controla al frame.

**Consecuencia operativa:** el checklist de aceptación rechaza cualquier guion con un chiste marcado
en la columna AUDIO, y rechaza cualquier guion con menos de 8 gags marcados en la columna VIDEO.

---

## 2. El mundo visual: **La mesa de mapas**

Un único escenario madre del que se derivan todos los demás: **una mesa de negociación vista de
frente, con un mapa encima**. Sobre esa mesa pasa la geopolítica: manos que mueven fichas, funcionarios
que señalan, objetos que entran, se deslizan y se vuelcan.

### 2.1 La técnica: recorte de papel (cutout)

Marionetas planas de papel recortado, articuladas por pivotes rígidos. Linaje explícito:
**Terry Gilliam (Monty Python)** y **Lotte Reiniger**. Es animación limitada, y esa es la clave:
la rigidez del recorte **se lee como estilo deliberado, no como pobreza**. Un personaje de trazo suave
que se mueve poco parece barato; un recorte de papel que gira sobre su hombro parece un lenguaje.

Es además exactamente lo que el motor de render hace nativamente y gratis (`ANIMACION.md` §2).

### 2.2 Paleta cerrada — 7 colores, nunca más

| Rol | Hex | Uso |
|---|---|---|
| Papel | `#E9DFCB` | Fondo, siempre. Nunca blanco puro. |
| Tinta | `#22201C` | Contornos, tipografía, sombras. Nunca negro puro. |
| Madera | `#6B4A33` | La mesa. |
| Mapa | `#DCCFB4` | Superficie de cartas y documentos. |
| Rojo señal | `#B8402F` | **Solo** lo que está en disputa. Un rojo por plano, máximo. |
| Azul institución | `#2B4C6F` | Estados, burocracia, tratados. |
| Ocre recurso | `#D9A441` | Petróleo, litio, cobre, dinero. El objeto del deseo. |

El rojo es el recurso más escaso de la paleta: si todo es rojo, nada está en disputa. Regla dura:
**un solo elemento rojo por plano**.

Textura encima de todo: grano de papel + un ligero registro desalineado tipo impresión offset.
Cumple dos funciones — identidad de marca, y disimula las costuras entre elementos vectoriales.

### 2.3 Las naciones son objetos; los líderes son caricaturas (revisado 2026-09-03)

**Decisión de Agustín (2026-09-03):** la prohibición anterior de dibujar políticos reales era una regla
que propuso el asistente, no él, y queda **derogada**. Cuando el guion habla de Trump, Putin, Maduro,
Milei o cualquier figura pública, **sale su caricatura de recorte de papel**, en el mismo estilo y con
los mismos remaches que el elenco base.

Lo que sí se mantiene:

- **Las naciones como entidades siguen siendo objetos** (fichas, sellos, banderas sobre asta, expedientes,
  válvulas). El líder es un personaje; el país es una ficha que el líder mueve.
- ❌ Nunca countryballs canónicos ni rasgos étnicos nacionales. La caricatura es de **una persona
  concreta y pública**, nunca de "un ruso" o "un venezolano".
- Los **8 arquetipos** de §2.4 siguen siendo el elenco base y cubren todo lo que no es una figura pública
  con nombre propio.

**Cómo se producen.** PicsArt (Flux 2 Pro) **rechaza por moderación cualquier prompt con el nombre de una
persona real** y no cobra el intento. Se describen **por atributos**, como hace un caricaturista: para
Trump alcanza con peinado ocre hacia adelante, corbata roja larguísima y boca fruncida; para Putin, frente
enorme, pelo ralo rubio-gris peinado hacia atrás, ojos chicos y separados, boca mínima. Cada figura cuesta
1 crédito por intento, y suele hacer falta más de uno. Los prompts que funcionaron quedan en
`pruebas/elenco/prompts_lideres.md`.

**Riesgo asumido, para no olvidarlo:** YouTube expandió en 2026 su *likeness detection* a políticos y
funcionarios; aunque la parodia esté protegida en EE. UU. (*Hustler v. Falwell*), una disputa consume
tiempo del único operador, y hay precedente de bloqueo regional (el video de Hitler de OverSimplified en
partes de Europa). Es un costo aceptado a cambio de que el video hable de quien habla el guion.

### 2.4 El elenco fijo — 8 arquetipos, cero excepciones

Este es el punto donde el proyecto se salva o se muere. La "lección South Park" (el video 20 cuesta
un tercio del video 1 porque se reusa todo) **no aplica automáticamente** a un canal de geopolítica:
Esequibo, Panamá y Sáhara tienen elencos disjuntos. La única forma de que aplique es **decidir por
diseño que el elenco no cambia**.

| # | Arquetipo | Función narrativa |
|---|---|---|
| 1 | El Burócrata (sombrero, saco azul) | Estado, tratado, trámite |
| 2 | El Militar | Fuerza, frontera, amenaza |
| 3 | El Ejecutivo (maletín) | Capital extranjero, concesión |
| 4 | El Trabajador (casco) | Mina, puerto, pozo |
| 5 | La Jurista (carpeta) | Corte internacional, arbitraje |
| 6 | El Vecino | El país de al lado, el tercero interesado |
| 7 | Las Manos (sin cuerpo) | El actor anónimo que mueve las fichas |
| 8 | La Multitud (silueta repetida) | Población, protesta, migración |

Ninguno tiene nacionalidad. La nacionalidad la da **la ficha que sostiene**, y esa se cambia por
color y sello. El guion **solo puede pedir estos ocho**. Si una escena necesita un noveno, se reescribe.

Cada uno con **6 poses canónicas** y nada más: `idle`, `señalar`, `caminar`, `sorpresa`,
`entregar/recibir`, `salir de cuadro`.

### 2.5 Los 8 escenarios fijos

1. La mesa de mapas (madre) · 2. La sala de negociación · 3. El puerto/terminal ·
4. La mina o el pozo · 5. El muro de gráficos · 6. La calle con multitud ·
7. El directorio corporativo · 8. El plano de datos sobre papel

El guion no puede inventar escenarios. **Esta única regla es la diferencia entre un video cada dos
semanas y un video cada dos meses.**

### 2.6 Los mapas

Son el segundo pilar visual y el más barato: se dibujan solos con `trim` de trazo, se pintan por
regiones, las flechas avanzan. Datos de **Natural Earth** (dominio público, sin atribución obligatoria).

> ⚠️ **GADM está prohibido** — su licencia excluye uso comercial, y es la primera fuente que aparece
> al buscar shapefiles de provincias latinoamericanas. OSM solo si hace falta detalle fino, con
> `© OpenStreetMap contributors` fijo en la plantilla de descripción.
>
> ⚠️ Las fronteras en disputa que trae Natural Earth son **una decisión editorial de un tercero**.
> Para Esequibo y Sáhara Occidental hay que auditarlas a mano antes de publicar.

---

## 3. Estructura de guion (formato 15-17 min, decisión de Agustín 2026-09-03: mínimo 15:30)

~2.250-2.500 palabras a ~145 wpm. La tabla de tramos de abajo era la del formato de 7-8 min; para 16 min se
duplica el cuerpo: 5 actos de ~150 s en lugar de 3 de ~90 s. El resto (cold open, promesa, ancla, cierre,
cliffhanger) mantiene sus duraciones.

| Tramo | Contenido |
|---|---|
| 0:00-0:15 | **COLD OPEN**: un objeto físico + un número + lo que está en juego |
| 0:15-0:40 | **PROMESA**: escalada + "y casi todo el mundo entiende mal por qué" |
| 0:40-1:15 | **ANCLA GEOGRÁFICA**: el mapa se dibuja solo |
| 1:15-1:55 | **SPONSOR** como escena in-universe (§4) |
| 1:55-6:30 | **3 ACTOS de ~90 s**: encabezado-pregunta → escena concreta → un número → giro → línea-gancho |
| 6:30-7:30 | **CIERRE**: el principio estructural que enseña el caso. Sin predicciones con fecha |
| 7:30-7:50 | **CLIFFHANGER** hacia el próximo video de la serie. ~~Nunca "suscribite"~~ → **Decisión de Agustín (2026-09-07): todos los videos llevan intro fija tras el cold open y outro fija con pedido de suscripción** (`canal/INTRO_OUTRO.md`) |

**Optimizá la unidad de 30 segundos, no la de 3.** YouTube reporta *intro* como el % de audiencia que
queda tras los primeros 30 s y lo lee como "¿el contenido cumplió lo que prometía el título?".
Prohibido antes de 0:60: nombre del canal, *"in this video we'll look at"*, *"have you ever wondered"*,
pedido de suscripción, y cualquier resumen de lo que vas a hacer.

### 3.1 Las 5 plantillas de hook

1. **OBJETO** — `This is a rock from the Atacama. Chile will not sell it to you.`
2. **ANOMALÍA DE MAPA** — `Two countries agree on where this border is. Neither of their armies does.`
3. **NÚMERO INVERTIDO** — `Guyana has 800,000 people. In 2019 it had no oil. Today it pumps more per person than Saudi Arabia.`
4. **CONTRAFÁCTICO** — `If this canal closed on Monday, by Friday your supermarket would notice.`
5. **ESCENA FECHADA** — `On a Tuesday in 2023, a ship stopped moving. Nobody in the port could say why.`

Todas: sujeto concreto, verbo físico, dato verificable, cero adjetivos de hype.

### 3.2 Reglas de escritura

- **Una oración por línea.** Kokoro parte el texto por saltos de línea (`split_pattern=r'\n+'`):
  el salto de línea **es** la respiración. Coma = micro-pausa. Línea en blanco = pausa de acto.
  No uses puntos suspensivos ni rayas como pausas — el G2P no las interpreta de forma fiable.
- **Longitud de frase**: media 10-14 palabras, máximo duro 22. Y **rompé el patrón a propósito**:
  después de dos frases largas, una de 3-5 (`It did not work.`). La uniformidad de longitud es lo que
  hace que un TTS suene a máquina.
- **Preguntas retóricas**: máximo 4-5 en todo el video, solo como encabezado de acto, nunca dos
  seguidas, nunca en el hook. El TTS aplana la entonación interrogativa y una pila de preguntas es la
  firma acústica número uno del contenido de granja.
- **Densidad de datos**: 1 número duro cada ~30 s, y **cada número viene con una comparación
  dibujable**. No `exports 5.2 million tonnes` sino `5.2 million tonnes — one of every four tonnes of
  copper on the planet`, y en pantalla cuatro lingotes, uno se pinta.
- **Voz institucional**: cero `I`. `We` solo en sentido de sourcing (`we read the port authority's own
  filings`). Tercera persona **con tesis** — la tesis es lo que evita el tono de Wikipedia leída.
- **Regla de escritura visual**: cada fila de la columna VIDEO tiene que ser **sujeto + verbo físico**.
  Si no se puede escribir así, la línea es un dato (va a gráfico) o se corta.

### 3.3 Normalización para TTS (capa separada, obligatoria)

Dos versiones de cada línea: la de pantalla (`Esequibo`, `$4.3B`, `1823`, `OPEC`) y la de TTS
(`Esse-KEE-bo`, `four point three billion dollars`, `eighteen twenty-three`, `O-PEC`). Un script de
Python con un diccionario de excepciones que crece video a video: Chuquicamata, Antofagasta,
Bir Lehlou, Tindouf, Kourou, Esequibo.

> **Riesgo #1 de credibilidad, y no es el dibujo.** Una pronunciación errada de `Esequibo` en el
> minuto 1 destruye más autoridad que cualquier monigote. Escucha manual de los primeros 45 segundos
> antes de publicar, siempre.

---

## 4. El sponsor como escena, no como corte

Se escribe como la entrada del **Personaje-Sponsor** al escenario del acto en curso, con una línea que
conecta el producto con el tema. Ground News encaja perfecto con *"este conflicto se cubre distinto en
Caracas, en Georgetown y en Nueva York"*.

Precedente duro: el "NordVPN Guy" de OverSimplified es un personaje recurrente in-universe, y
OverSimplified es el partner de creadores más seguido de NordVPN. Va en el media kit:
**"tu integración se anima como una escena, no se lee a cámara"**.

---

## 5. Blindaje de plataforma (verificado en fuente primaria)

La caricatura no es un riesgo: **es una ventaja regulatoria neta** frente al formato Ken Burns.

| Hecho verificado | Consecuencia |
|---|---|
| La política de divulgación de contenido sintético de YouTube **exime al contenido "totalmente animado"** y no realista | No hay que marcar la casilla de *altered or synthetic content* |
| Las advertiser guidelines pagan **revenue completo** por *"non-graphic educational coverage or discussion of war and/or conflict"* | Con dibujo animado controlás la graficidad al 100 % — no hay footage que te limite el ad |
| La actualización de enero 2026 relajó temas controvertidos cuando el tratamiento es *non-graphic and dramatized* | El formato juega a favor |
| La política de *inauthentic content* (15/07/2025) es un gate de **monetización del YPP**, no de strikes | Con modelo de sponsors el impacto directo es menor — pero ver abajo |
| Bucket de julio 2026: **personas de IA presentadas como expertos en temas políticos** = no monetizable | **Bala directa a un canal de geopolítica sin cara** |

**Reglas duras que salen de eso:**

1. **Marca-publicación, jamás analista.** Nada de un personaje animado recurrente con nombre propio
   que "explica" geopolítica. Nada de credenciales implícitas. Nada de "nuestro analista". Voz en off
   sin identidad personal. Sección *about* que declare que es un canal editorial con guiones
   investigados. **Es la mitigación de mayor retorno de todo el frente legal.**
2. **Regla de graficidad**: sin sangre, sin cuerpos, sin heridas, sin ejecuciones, y jamás violencia
   en miniatura ni en los primeros 7 segundos. El conflicto se representa con símbolos.
3. **Prohibido el gag visual en cualquier beat que mencione víctimas.** No es estética: es cortafuegos
   reputacional. Esequibo, Sáhara y litio involucran despojo y muertos reales; aplicarles la ligereza
   de OverSimplified (que trabaja sobre guerras de hace 200 años) es veneno para el brand safety.
4. **Sourcesheet pública por video** (link en descripción). Es la movida más barata que existe para
   convertir un canal de dibujitos en "publicación", y es el criterio que hace aplicable el programa
   de partners de Ground News.
5. **Nunca clonar la voz de una figura pública real**, ni para una cita.
6. **Modelos**: SDXL/Juggernaut (RAIL++-M) y FLUX.1-**schnell** (Apache 2.0) sí.
   **FLUX.1-dev NO** — licencia de modelo no comercial. Decidirlo hoy, antes de que la identidad
   visual dependa de pesos que no se pueden monetizar.
7. **Música**: solo YouTube Audio Library o Kevin MacLeod (CC-BY, monetizable con crédito).
   **Nunca música de PicsArt** — sus Terms prohíben expresamente percibir ingresos por publicidad en
   obras que la incluyan.
8. **Bandera o escudo nacional jamás como logo, avatar o favicon** (Art. 6ter + política de
   impersonation). Dentro de mapas y escenas, sin problema.

**Anti-plantilla.** El riesgo real no es el dibujo: es el **patrón de fábrica**. Con 8 personajes y 8
escenarios fijos, la señal de "producido en masa" sube. Marcadores de originalidad obligatorios por
video: una tesis propia en una frase, al menos dos datos de documento primario (memoria anual, filing,
tratado, boletín de aduana), un mapa hecho por vos, y la sourcesheet. Y **rotar la estructura
narrativa** (cronológica / por actores / contrafáctica), no solo el tema.

---

## 6. El presupuesto de densidad de animación (la decisión más importante)

La investigación verificó contra los feeds RSS oficiales, no contra agregadores:

| Canal | Equipo | Cadencia real (2026) |
|---|---|---|
| OverSimplified | Equipo + animadores externos | **2,3 videos/año** — 19 meses sin publicar |
| Suibhne (one-man-show confirmado por el autor) | 1 persona | **4 videos/año** |
| History Matters (el estilo más barato del nicho) | Equipo | 18,6/año ≈ **65 min animados/año** |
| Armchair Historian | LLC con animadores | 20/año |
| Kurzgesagt | 72-77 personas | ~1.200 h por video |

**No existe un solo caso verificable de canal de historia o geopolítica animado con cadencia semanal
sostenida.** El techo observado del nicho entero es ~65-75 minutos animados terminados por año.

Pero todos esos números asumen **cobertura animada del 100 %**, y ninguno de los referentes la tiene.
History Matters usa narrador en off con gags puntuales; Bill Wurtz encadena imágenes casi estáticas;
Sam O'Nella sostiene poses. **La palanca no es la herramienta: es la densidad.**

### Presupuesto fijo por video de 7-8 minutos

| Capa | Metraje | Qué es |
|---|---|---|
| **A — Actuación de personaje** | **90-120 s** | Personajes que gesticulan, señalan, entran, entregan. La capa cara. |
| **B — Mundo animado sin personaje** | ~180 s | Mapas que se dibujan, fichas que se mueven, gráficos que crecen, objetos que caen. Barata y es donde vive el 60 % de los gags. |
| **C — Tipografía y datos en movimiento** | ~90 s | Cifras, citas, cronologías. Casi gratis. |
| **D — Planos "hero"** | 12-20 s | Los únicos que gastan créditos (`ANIMACION.md` §4). |

Suma ≈ 7 min. La Capa A —lo que de verdad cuesta— son **~100 segundos por video**, no 480.
Con eso el requisito de caricatura animada deja de ser incompatible con producir de forma sostenida.

### Cadencia: la decisión pendiente

Con este presupuesto, la recomendación es:

- **Lanzamiento**: 1 video de 7-8 min **cada dos semanas**, + 2 shorts semanales.
- **Banco previo**: 4 videos terminados antes de publicar el primero. La causa número uno de muerte
  de canales animados en solitario no es la calidad — es que la cadencia consume al operador antes de
  que llegue el dinero.
- Subir a semanal solo después de medir el video 5 de punta a punta.

> ⚠️ **El guion también hay que presupuestarlo.** 1.050-1.200 palabras semanales de geopolítica
> investigada y escrita en un segundo idioma es plausiblemente el cuello de botella real, por encima
> de la animación. La investigación costeó minuciosamente los días-persona por minuto animado y no
> dedicó una línea a esto. Medilo en el video 1.

---

## 7. Checklist de aceptación (correlo como script)

- [ ] Media de palabras por oración entre 10 y 14; ninguna >22
- [ ] ≤5 signos de interrogación en todo el guion
- [ ] 0 apariciones de `I`
- [ ] ≥1 número cada 90 palabras y ≤1 cada 60
- [ ] **0 chistes marcados en la columna AUDIO**
- [ ] **≥8 gags marcados en la columna VIDEO**
- [ ] 0 escenarios fuera de la lista de 8; 0 personajes fuera de la lista de 8
- [ ] Personas reales solo como caricatura de papel del elenco (§2.3, decisión de Agustín 2026-09-03)
- [ ] Capa A entre 90 y 120 s; Capa D ≤20 s
- [ ] Sourcesheet publicada con los videos de referencia de donde salen los datos (decisión de Agustín 2026-09-03: sin verificación en primaria)
- [ ] Estructura narrativa distinta a la del video anterior
- [ ] Escucha manual de los primeros 45 s (pronunciación)

---

## 8. Decisiones pendientes

- [ ] **La más grave: ¿voz TTS, voz clonada o voz propia?** → investigado a fondo, ver **`VOZ.md`**.
      Resumen: el **acento no es el problema** (Sabine Hossenfelder tiene los tres sponsors objetivo
      con acento alemán marcado; Caspian Report 42 deals con acento azerbaiyano). Lo que sigue sin
      precedente es la **narración sintética** con ese tier de sponsor. El test que decide está en
      `VOZ.md` §8 y cuesta una tarde y cero instalaciones.
- [x] Nombre editorial del canal → **Paper Trail** (decisión de Agustín 2026-09-07, análisis en `canal/NOMBRE.md`). Antes: propuesta The Map Table con handle y alternativas verificadas en
      `canal/CANAL.md` §1 (2026-09-07). Falta el veredicto de Agustín.
- [ ] Validar que existe demanda en inglés para geopolítica de LatAm/España más allá del dato suelto
      de los videos de Suibhne sobre México y España.
- [ ] Miniaturas y títulos: no aparecieron en toda la investigación y para un canal financiado por
      sponsors el CTR es el juego entero.
- [ ] Confirmar cadencia definitiva después de medir el video 1 completo.
