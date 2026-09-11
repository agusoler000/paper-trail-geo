# CANAL — identidad y configuración en YouTube

> Creado 2026-09-07. Todo lo que hace falta para abrir el canal: nombre, handle, imágenes, descripción,
> ajustes por defecto. Las imágenes se generan con `marca.py` (0 créditos, mismo motor de papel del video).
> Cambiar el nombre = volver a correr `python marca.py "OTRO NOMBRE" "otro tagline"`.

---

## 1. Nombre: **Paper Trail** (decisión de Agustín 2026-09-07)

| Qué | Valor |
|---|---|
| Nombre | **Paper Trail** |
| Handle | **`@papertrail`** (libre, verificado por HTTP y yt-dlp el 2026-09-07). Reserva: `@papertrailgeo`. |
| Tagline | **`Follow the paper.`** (banner y primera línea de la descripción) |
| Dominio | papertrail.tv libre; papertrail.com es de SolarWinds (no comprar nada hasta facturar) |
| Marcas | Sin marca viva para video o contenido editorial. La única viva en clase 41 es de Newfangled Games (videojuego) y cubre solo juegos en línea. Detalle en `NOMBRE.md` §5. |
| Colisiones en YouTube | ThePaperTrail 10,6k subs (inactivo), arelle's paper trail 5,5k, Paper Trail Pro 1,9k. Ninguno del nicho. |

Por qué este y no otro: `NOMBRE.md` (criterios, 30 candidatos, finalistas Papercut y Paper Tigers).

### 1.1 Registro: la propuesta anterior, The Map Table (rechazada)

> Lo de abajo queda como registro del primer intento.

Es el escenario madre de `ESTILO.md` §2 y ya aparece como tarjeta de título en el cold open del video 1.
Es nombre de **publicación**, no de persona (`IDEA.md` §8): "at the map table" es donde se negocia.
Describe el look sin explicarlo y no lleva la palabra *geopolitics*, que en YouTube suena a granja.

Verificado el 2026-09-07 (HTTP directo a youtube.com y RDAP):

| Qué | Estado |
|---|---|
| Nombre "The Map Table" en YouTube | Existe un canal con ese nombre: **14 suscriptores, sin contenido**. No bloquea (los nombres no son únicos) y no compite. |
| `@themaptable` | **Ocupado** (ese canal). |
| `@atthemaptable` | **Libre** ← recomendado: se lee como frase ("at the map table"). |
| `@themaptabletv` | Libre |
| `@maptabledispatch` | Libre |
| `@themaptable_` | Libre (feo, evitar) |
| `themaptable.com` | Registrado |
| `themaptable.tv` / `themaptable.co` | **Libres** (no comprar hasta que haya ingresos; presupuesto 0) |

Alternativas si no te convence, ya verificadas:

| Nombre | Handle libre | Dominio | Comentario |
|---|---|---|---|
| **The Paper Frontier** | `@thepaperfrontier` | thepaperfrontier.com libre | Suena a marca; `@paperfrontier` está ocupado (canal vacío) |
| **The Paper Dispatch** | `@thepaperdispatch`, `@paperdispatch` | sin verificar | "Dispatch" refuerza el marco de publicación |
| **The Cutout Dispatch** | `@thecutoutdispatch`, `@cutoutdispatch` | sin verificar | Nombra la técnica; menos evocador |
| Deadpan Dispatch | ocupado (`@deadpandispatch`, canal vacío) | — | Era el nombre de la regla narrativa; descartado |
| The Folded Map | ocupado (134 subs) | ocupado | Descartado |

**Tagline:** `Geopolitics, on paper.` (va en banner y en la primera línea de la descripción).

---

## 2. Imágenes (`canal/out/`)

| Archivo | Tamaño | Dónde va | Nota |
|---|---|---|---|
| `avatar_A.png` | 800×800 | Foto de perfil | Ficha ocre con el nombre. **Recomendado**: se lee a 48 px. |
| `avatar_B.png` | 800×800 | Foto de perfil (alt.) | Mapa + monograma "MT". Más limpio, menos legible. |
| `avatar_C.png` | 800×800 | Foto de perfil (alt.) | Tarjeta de papel como las del video. |
| `banner_2560x1440.png` | 2560×1440 | Imagen de banner | Nombre y tagline dentro de la zona segura 1546×423; el Burócrata y el Militar quedan fuera de ella (se ven en escritorio y TV, no en móvil). `_banner_guia.jpg` muestra la zona segura en rojo. |
| `marca_agua_150.png` | 150×150 PNG alfa | Marca de agua de video | La ficha sola. Mostrar "todo el video". |
| `miniatura_01.png` | 1280×720 | Miniatura del video 1 | Plantilla: 2-3 tarjetas de título, última en rojo (único rojo), personaje a la derecha, mapa del tema. |

Reglas que cumplen (ESTILO §2.2 y §5): paleta de 7 colores, un solo rojo por cuadro, grano + registro
offset, ninguna bandera ni escudo como logo (regla 8), ningún personaje presentado como "el analista" (regla 1).

Para ver el avatar como lo recorta YouTube: `_avatares_circulo.jpg`.

---

## 3. Descripción del canal (pegar en *Personalización → Información básica*)

```
Geopolitics, cut from paper.

Paper Trail is an animated channel about the fights that shape the world: borders, canals, fleets, mines, sanctions. Each episode takes one dispute and follows the paper behind it — the treaty, the lease, the insurance policy, the court ruling that decides who actually wins.

No talking head. No hot takes. Maps, numbers and receipts, with the sources linked under every episode.

Subscribe if you want the next one on the table.
```

(Decisión de Agustín 2026-09-07: **nada de cadencia en textos públicos**. Ni en la descripción, ni en la outro,
ni en la plantilla de video. La cadencia es interna, `CALENDARIO.md`.)

(Versión 2, 2026-09-07: Agustín rechazó la primera por "horrible". Cambios: la primera línea es la que YouTube
muestra en búsqueda, así que va el gancho y la palabra *geopolitics*; se sacó "editorial channel", "told on
paper", "no host and no pundit" y "no predictions with dates", que sonaban a manifiesto; se agregó el pedido
de suscripción al final. La frase "the narration is a voice, not a person" se fue de la descripción; si querés
declarar la voz sintética, va en la hoja de fuentes, no acá.)

(La última línea tiene que coincidir con la cadencia de `CALENDARIO.md` §1: quincenal, decisión de Agustín 2026-09-07.)

Notas:
- "No host and no pundit / a voice, not a person" es la mitigación de mayor retorno frente al bucket de
  julio 2026 ("personas de IA presentadas como expertos en temas políticos = no monetizable", `ESTILO.md` §5).
- Si querés ir un paso más lejos en transparencia, agregá `Narration is synthetic; the writing is not.`
  Es una decisión tuya: reduce riesgo de policy, puede costar credibilidad con parte de la audiencia.
- El video es "totalmente animado": **no** hace falta marcar *contenido alterado o sintético* al subir.

**Enlaces** (sección *Enlaces*, hasta 14): solo los que existan. Por ahora: la sourcesheet pública del
video 1 (un Google Doc o página estática) y, cuando exista, el correo de contacto comercial.
**Correo de contacto**: creá uno del canal (no el personal); es lo que ven los sponsors.

**Palabras clave del canal** (*Configuración → Canal → Información básica*):
`geopolitics, explained, animation, paper cutout, maps, Latin America, Venezuela, Guyana, Essequibo, Panama Canal, lithium, Russia, sanctions, aviation`

---

## 4. Ajustes por defecto de subida (*Configuración → Valores predeterminados de subida*)

| Campo | Valor |
|---|---|
| Idioma del video | English |
| Categoría | Education |
| Licencia | Estándar de YouTube |
| Comentarios | Retener los potencialmente inapropiados para revisión |
| Contenido para niños | No |
| Contenido alterado/sintético | No (animación completa, exenta) |
| Visibilidad por defecto | Privado (se programa a mano) |

**Plantilla de descripción de video:**

```
[Una frase: la tesis del episodio.]

Sources for this episode: [link a la sourcesheet]

Chapters
0:00 [Cold open]
0:40 [Ancla geográfica]
...

Map data: Natural Earth (public domain).
Music: original cues produced for this channel.
[Si se usa Kevin MacLeod: pegar el bloque de crédito de produccion/CREDITOS_MUSICA.md]

Paper Trail is an editorial channel. No host, no pundit, no predictions with dates.
```

**Descripción del video 1, lista para pegar** (capítulos medidos sobre `produccion/01_aviacion_rusa.mp4`,
16:14, a partir de `audio/01_aviacion_rusa_eleven_george_dram.tiempos.json`):

```
Russia has 673 airliners. One in five cannot leave the ground. Nobody shot them down. This is how you ground a country the size of a continent without firing at a single plane: with a fleet nobody can repair, a drone that costs less than a used car, and eleven time zones held together by one machine.

Sources for this episode: [link a canal/sourcesheets/01_aviacion_rusa.md publicado]

Chapters
0:00 Cold open: 673 airliners
0:23 The sky over Moscow
1:09 The shape of the problem
2:19 Where the numbers come from
3:08 Act I: What did four years of sanctions do to the fleet?
5:21 Act II: How do you keep a fleet flying without parts?
8:03 Act III: How does one cheap drone close an airport a thousand kilometers away?
11:05 Act IV: What happens to a country this size when it cannot fly?
13:18 Act V: What does Siberia do when the plane stops coming?
14:57 The three parts, together
15:56 Next dispatch

Map data: Natural Earth (public domain).
Music: original cues produced for this channel.

Paper Trail is an editorial channel. No host, no pundit, no predictions with dates.
```

Título: ver §7 (el de "673 airliners" fue rechazado por Agustín; propuesta nueva:
`How Ukraine Grounded Russia's Airlines Without Firing a Shot`). Etiquetas:
`russia, ukraine, aviation, sanctions, aeroflot, geopolitics, animated, explained`.
Pantalla final (últimos 20 s = beat 11, desde 15:56): elemento "video siguiente" a la derecha del cliffhanger
y "suscribirse" chico abajo a la izquierda. El guion no lo pide en voz (regla de `ESTILO.md` §3); el elemento
visual sí va.

### 4.1 Listas y secciones de la página de inicio

| Sección | Contenido | Cuándo |
|---|---|---|
| Tráiler del canal (no suscriptores) | Video 1 entero hasta que haya un corte de 30 s con el cold open + un gag por acto | Al abrir |
| Video destacado (suscriptores) | El último dispatch | Siempre |
| Lista **Dispatches** | Todos los videos largos, en orden | Al abrir |
| Lista **Shorts** | Los cortes verticales | Cuando haya 2 |
| Lista **Latin America** | Eps. 3 en adelante | Cuando exista el ep. 3 |
| Lista **Russia** | Eps. 1 y 2 | Cuando exista el ep. 2 |

Las listas por región son las que YouTube muestra como "series" y las que un sponsor mira para saber de qué
va el canal. Un post de comunidad por dispatch, el miércoles anterior, con la miniatura y una sola pregunta.

---

## 5. Orden de tareas en YouTube Studio (una tarde)

1. Crear el canal como **cuenta de marca** (no con tu nombre): `youtube.com/create_channel`.
2. Nombre: `Paper Trail`. Handle: `@papertrail` (si al crearlo aparece ocupado, `@papertrailgeo`, también verificado libre).
3. Personalización → Marca: subir `avatar_A.png`, `banner_2560x1440.png`, `marca_agua_150.png`.
4. Personalización → Información básica: descripción (§3), enlaces, correo de contacto.
5. Configuración → Canal: país, palabras clave (§3), valores de subida (§4).
6. Configuración → Canal → Elegibilidad de funciones: **verificar el teléfono** (sin eso no hay
   miniaturas personalizadas ni videos de más de 15 min, y el video 1 dura 16:14).
7. Subir el video 1 en **privado** con `miniatura_01.png`; revisar cómo se ve en móvil y en escritorio.
8. Crear la lista "Dispatches" y ponerla como sección de inicio. Tráiler del canal: el video 1 hasta que
   haya un corte de 30 s.
9. Recién después, programar la publicación. `ESTILO.md` §6 recomendaba banco de 4 videos antes del
   primero; con uno solo, el riesgo es la cadencia, no el lanzamiento.

---

## 7. Títulos

Agustín rechazó `Russia Has 673 Airliners. One in Five Cannot Fly.` (2026-09-07). Lo que fallaba: es un dato,
no una historia; no dice quién lo hizo ni cómo; y "cannot fly" suena a nota de agencia. Los títulos que
funcionan en este nicho (RealLifeLore, Wendover, Johnny Harris) tienen **actor + acción imposible + giro**,
y prometen una explicación, no una cifra.

**Fórmula del canal (v3, decisión de Agustín 2026-09-08):** `PALABRA-EMOCIÓN: [Quién] [verbo fuerte] [a quién/qué] [giro o promesa]`.
La primera palabra es una emoción en mayúsculas con dos puntos, **en todos los videos, y cada video lleva la suya según
lo que relata** (no siempre la misma): `FEAR` · `BOMBSHELL` · `PANIC` · `SHOCK` · `WARNING` · `COLLAPSE` · `EXPOSED` ·
`BETRAYAL` · `SECRET` · `ALERT` · `HUMILIATION` · `REVENGE`.
Límites: la palabra tiene que cumplirse en el video; no "BREAKING" (promete noticia en vivo) ni fechas; sin "Nazi".
Unos 70 caracteres como máximo (la palabra come 6-10); la cifra va al título o a la miniatura, no a los dos.
Si a las 48 h el CTR está bajo el 4 %, probar el mismo título sin la palabra y comparar.


**Regla de Agustín (2026-09-08): los títulos tienen que ser más sensacionalistas** ("parece que YouTube da más visitas
por eso"). Mismo límite: cada título se apoya en algo que el video dice; el drama va en el verbo y en la promesa.

Video 1, candidatos en orden (reescritos el 2026-09-08; los sobrios quedan en `SUBIR_01.md` como respaldo):

| # | Título | Por qué |
|---|---|---|
| **1** | **BOMBSHELL: Ukraine Just Grounded Russia's Airlines Without a Single Shot** (la emoción del ep. 1 es sorpresa: el arma es una póliza) |
| 1b | Ukraine Just Grounded Russia's Airlines Without Firing a Single Shot (base sin palabra) | Actor, acción imposible, giro; "just" + "single" suben la temperatura sin inventar nada. 68 caracteres. |
| 2 | One in Five Russian Planes Can't Fly. Nobody Shot Them Down | El dato del cold open con el giro en la segunda frase. |
| 3 | Russia Stole 400 Airliners. Now It Can't Keep Them in the Air | Acto I ("it stole them first and bought them second") + acto II. |
| 4 | The Insurance Policy That Just Closed the Sky Over Moscow | El arma real del video. |
| 5 | Russia Is Too Big to Run Without Planes. Ukraine Knows It | Acto IV. |

Lista anterior (2026-09-07), por si se vuelve al tono sobrio:

| # | Título | Por qué |
|---|---|---|
| **1** | **How Ukraine Grounded Russia's Airlines Without Firing a Shot** | Actor, resultado, giro. Es la pregunta del cold open contestada. 59 caracteres. |
| 2 | How Do You Ground a Superpower Without Firing a Shot? | Es literalmente la tarjeta del cold open. Más misterio, menos búsqueda (no dice Rusia ni Ucrania). |
| 3 | Russia's Planes Are Falling Apart. Ukraine Never Shot Them. | Dos frases, contraste. Bueno para miniatura de texto corto. |
| 4 | The Insurance Policy That Grounded Russia | El giro real del video (el arma es una póliza). Más nicho, más memorable. |
| 5 | Why One in Five Russian Airliners Can't Take Off | Versión "explicador" clásica. Segura, menos curiosa. |

Video 2 (AfD), candidatos en orden. **Regla nueva de Agustín (2026-09-08): los títulos tienen que ser más
sensacionalistas**, porque YouTube premia el clic. Límite que sigue: sin inventar hechos (cada título se apoya en
algo que el video dice) y sin opinión propia; el drama va en el verbo y en la promesa, no en datos nuevos.

| # | Título | Se apoya en | Caracteres |
|---|---|---|---|
| **1** | **FEAR: Half a German State Just Voted Far Right. Nobody Saw the Real Reason** (la emoción del ep. 2 es miedo: media región vota lo que nadie quiere tocar) |
| 1b | Germany's Far Right Won 44%. The Real Reason Is Worse Than Immigration (base sin palabra; con BOMBSHELL:) | Tesis de Rallo: la causa es el estancamiento + estado de bienestar insostenible, y ninguna receta lo arregla | 70 |
| 2 | Half a German State Just Voted "Extremist". Nobody Saw the Real Reason | Clasificación oficial de la rama regional + "la razón no es la del noticiero" | 70 |
| 3 | Why 170,000 Germans Who NEVER Voted Just Voted Far Right | Dato de Rallo (170.000 abstencionistas movilizados) | 56 |
| 4 | The Vote That Should Terrify Every Government in Europe | "Wake-up call" (Memorias de Pez) + el bucle europeo de Rallo | 55 |
| 5 | Germany's Most Feared Party Just Won 44%. Every Cure Has Failed | Acto V: ni la izquierda ni la nueva derecha lo frenaron en ningún país | 63 |
| 6 | Half of East Germany Just Voted for the Party Nobody Will Touch | Versión anterior, más sobria; queda como respaldo | 63 |

Reglas para que el sensacionalismo no rompa nada: la cifra (44 %) puede ir en el título si la miniatura lleva
otra (170,000 o "HALF A STATE"); "far right" es la etiqueta que usan las dos fuentes, "Nazi" no va en el título
(el video dice explícitamente que esa palabra no aplica al conjunto); nada de fechas ni "BREAKING".

Miniaturas hechas (2026-09-08, `canal/marca.py::miniatura` con Weidel y la hoja de Alemania): `out/miniatura_02A.png`
(`44 %. / HALF A STATE. / NOBODY WILL TOUCH IT.`), `02B` (`THEY WON 44 %. / THE REASON IS / NOT WHAT YOU HEARD.`) y `02C`
(`170,000 PEOPLE / WHO NEVER VOTED / JUST VOTED.`). Con el título 1, la A o la C no repiten la frase del título; la B sí la
repite en la franja ocre. Falta el veredicto de Agustín.

**Miniatura acorde al título 1** (regenerada en `out/miniatura_01.png`): texto grande `GROUNDED.` / `WITHOUT` /
`A SHOT.` (el rojo en la última), abajo `1 IN 5 RUSSIAN PLANES CAN'T FLY`, Zelensky a la derecha, mapa de
Rusia. Título y miniatura no repiten la misma frase: el título cuenta la historia, la miniatura da la cifra.

---

## 6. Lo que queda abierto

Decisiones tuyas (sin ellas no se abre el canal):
- [x] Nombre: **Paper Trail**, `@papertrail` (decisión de Agustín 2026-09-07). Imágenes regeneradas, descripción
  y plantilla actualizadas, tarjeta del cold open cambiada en `piloto.py`/`piloto2.py` (el video 1 se re-renderiza
  con ella: `produccion/01_aviacion_rusa_v5.mp4`).
- [ ] Avatar: A, B o C (§2, `out/_avatares_circulo.jpg`).
- [x] Cadencia: **quincenal** (decisión de Agustín 2026-09-07; los 500 créditos son de este canal). Fecha de lanzamiento propuesta: jueves 17/09 (`CALENDARIO.md` §3).
- [ ] Tema del ep. 2: cumplir el cliffhanger (Rusia, regiones) o ir directo a Esequibo (`CALENDARIO.md` §3).
- [ ] Si la descripción declara la narración sintética (§3, nota).
- [ ] Título del video 1. Propuesta: `Russia Has 673 Airliners. One in Five Cannot Fly.`
  Alternativas: `How Ukraine Grounded Russia Without Shooting Down a Plane` ·
  `Russia's Airlines Are Being Eaten for Parts`.

Tareas que solo podés hacer vos (cuenta de Google):
- [ ] Crear la cuenta de marca y verificar el teléfono (§5).
- [ ] Correo de contacto del canal.
- [ ] Publicar la hoja de fuentes (`sourcesheets/01_aviacion_rusa.md`) como Google Doc público y pegar el link.

Ya listo, en este directorio: imágenes (§2), descripción del canal (§3), descripción y capítulos del video 1 (§4),
listas y secciones (§4.1), calendario y cola de 8 temas (`CALENDARIO.md`), hoja de fuentes redactada.

### Nombres propios en el gancho (decisión de Agustín, 2026-09-09)

En la **intro de preguntas y en el cold open** los mandatarios van **sin nombre**: "a minister in Jerusalem",
"a president in Buenos Aires", "the president of the United States". Se mantiene el misterio y el gancho no
envejece atado a quién gobierna. **En el cuerpo del episodio van todos con nombre y apellido** desde la primera
mención (Milei, Trump, Streeting, Ben Gvir, Ridley, Haig, Galtieri, Onslow, Vernet…), que es donde hacen falta
para la precisión y para que se pueda comprobar cada dato.
Contra-argumento que se le planteó y que él descartó: en el feed los nombres propios retienen y se buscan.

## Pedir comentarios — SIEMPRE (Agustín, 2026-09-09)

> *"en todos los shorts y todos los videos de ahora en más hay que dejar preguntas o cosas para responder en los
> comentarios."*

**Cada pieza que sale del canal —episodio largo, short, teaser, serie— tiene que dejarle al espectador algo que
responder.** No es un adorno del final: los comentarios son la señal más fuerte que una pieza le da al algoritmo, y
en temas con dos bandos son gratis.

Dónde va, en este orden:

1. **EN LA VOZ, y esto es lo primero, no lo opcional** (Agustín, 2026-09-09: *"que sea la voz la que lo pregunte
   e incentive a dejar el comentario, tanto en los videos como en los shorts"*). Cerca del cierre, el narrador
   pregunta y pide explícitamente el comentario. Una pregunta concreta, nunca "¿qué opinás?": la buena divide y se
   contesta en cinco palabras. *"British or Argentine? Put it in the comments."* Va en el guion como una línea `A:`
   más, escrita desde el principio — no se pega después.
2. **En pantalla**, en la tarjeta final, junto al SUBSCRIBE. En los shorts del ep. 4 quedó como
   `BRITISH OR ARGENTINE? / TELL US IN THE COMMENTS`.
3. **En la descripción**, en la última línea.
4. **En el comentario fijado**, con la fuente primaria del dato más discutible de la pieza: invita a discutir con
   el papel delante y deja el hilo abierto desde el minuto cero.

Y cuando la pieza opina (como el veredicto del ep. 4), la pregunta se hace **honesta**: se pide la contraria.
Un video que concluye y además pregunta "¿en qué me equivoco?" recibe el doble de comentarios que uno que solo concluye.

Video 4 (Malvinas / Falklands), candidatos en orden (2026-09-09). Estudio completo, con lo que sostiene cada uno
y los descartes, en `canal/TITULOS_04.md`. La emocion del ep. 4 es **traicion**: el plan para devolver las islas lo
escribio el Foreign Office y lo enterro su propio Parlamento.

| # | Titulo | Caracteres | Se apoya en |
|---|---|---|---|
| **1** | **BETRAYAL: Britain Planned to Give the Falklands Back. MPs Killed It** | 67 | El leaseback de Ridley (1980) y el debate de los Comunes del 2 de diciembre, donde se le grito "traicion" |
| 2 | BETRAYAL: Britain Offered the Falklands Back. Its MPs Cried Treason | 67 | El mismo compas con la palabra literal de los Comunes |
| 3 | EXPOSED: Britain Signed the Falklands Deal Already. For Other Islands | 69 | Chagos: soberania a Mauricio, Diego Garcia en arriendo 99 anos, sin referendum |
| 4 | COLLAPSE: Argentina Was Winning the Falklands. Then a Junta Invaded | 67 | Resolucion 2065 (94-0), quince anos de negociacion, y 1982 |
| 5 | WARNING: There Is Oil Under the Falklands and a Date on the Calendar | 68 | Sea Lion: FID tomada, primer petroleo marzo de 2028 |
| 1b | Britain Wrote a Plan to Give the Falklands Back. Its Own MPs Killed It | 70 | Base sin palabra, para la prueba de CTR a las 48 h |

**Aprendido en el ep. 4:** un titulo se mide antes de proponerlo. Los tres primeros que escribi para este
episodio se pasaban de 70 caracteres, y el que estaba puesto (`... Back. It Killed It`) no decia **quien** mataba
que. El giro tiene que nombrar al actor, no dejarlo en un pronombre.
