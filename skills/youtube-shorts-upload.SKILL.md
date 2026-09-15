---
name: youtube-shorts-upload
version: 1.6.0
changelog:
  - v1.6.0 (2026-09-09): **no se cierran pestanas** (§4). Agustin lo pidio explicitamente; la skill decia `tabs_close_mcp` al terminar y ya no.
  - v1.5.0 (2026-09-09): **el subagente que sube ahora es Opus, no Sonnet** (decision de Agustin): Sonnet iba lento y se equivocaba en el formulario de Studio, y cada error cuesta mas tiempo que la diferencia de modelo. El reparto (§7) no cambia: el principal planifica, verifica el canal, hace el video relacionado y la verificacion final; el subagente sube uno por vez.
  - v1.4.0 (2026-09-09): **los Shorts ya aceptan miniatura propia** (YouTube la habilito el 24-jul-2026), pero **solo para canales del YouTube Partner Program** y con despliegue gradual. Si el boton "Subir miniatura" no esta en Studio, para todos queda **elegir entre tres cuadros sugeridos** (escritorio). Cada produccion deja las suyas 9:16 y < 2 MB (`miniaturas.py`), y `PLAN_SUBIDA.json` trae el campo `miniatura` con la ruta. Correccion: hasta la v1.3 la skill decia "sin miniatura personalizada", que era cierto hasta julio de 2026 y ya no lo es.
  - v1.3.0 (2026-09-10): **el plan de una SERIE lo genera su propio `publicar.py`**, no `shorts.py` (§2b). Probado con `videos/S01_11s/` (11-S, 12 piezas): una pieza por dia a la misma hora, playlist propia, video relacionado = pieza anterior, y el sello `PART n OF N` ya viene quemado en el MP4. Mismo formato de `PLAN_SUBIDA.json`, asi que el resto del flujo no cambia.
  - v1.2.0 (2026-09-08): **shorts redefinidos** (`canal/SHORTS.md`): una tanda puede ser del episodio (3-5 con guion propio), de una **serie** (playlist propia, video relacionado = pieza anterior, una por dia en orden) o de un short suelto; §0 lo distingue. Rutas nuevas por produccion (`videos/<dir>/shorts/`) desde el ep. 5.
  - v1.1.0 (2026-09-08): reparto Opus/Sonnet verificado (§7): un subagente Sonnet alcanza el navegador y hereda el seleccionado. Regla nueva: la cuenta tiene más de un canal y Studio abre otro por defecto — navegar con CHANNEL_ID y verificar antes de subir (§1).
  - v1.0.0 (2026-09-08): primera versión, destilada de subir los 10 shorts del ep. 1 de Paper Trail a mano con Claude in Chrome. Incluye el plan generado por código (`shorts.py --plan`), la receta exacta del formulario de Studio y las cinco trampas que hicieron fallar la primera tanda.
description: >
  Subir shorts verticales a YouTube y programarlos por fecha y hora, usando Claude in Chrome sobre YouTube Studio.
  Usar cuando Agustín pida "subí los shorts", "publicá los shorts", "programá los shorts", "subilos todos",
  "4 hoy, 3 mañana y 3 pasado" o cualquier reparto parecido, y también para vincular el episodio largo a shorts
  que ya están arriba. Cubre: preparar los archivos y el calendario, rellenar el formulario de Studio, programar,
  poner el "Video relacionado" y verificar. NO cubre producir los shorts (eso es la skill `paper-trail-video` §2.10).
---

# Subir y programar shorts en YouTube

Flujo probado el 2026-09-08 con 10 shorts. **Duración real: ~4 minutos por short.** Todo se hace con
`mcp__claude-in-chrome__*` sobre `studio.youtube.com`.

## 0bis. Lo que Claude NO puede subir (tope duro)

`mcp__claude-in-chrome__file_upload` acepta **10 MB como maximo sumando los archivos de una llamada**.

- **Shorts: si.** Por eso el plan deja copias en `_up/*.mp4` de 2-4 MB. Esas son las que se adjuntan,
  nunca el master del short.
- **Episodio largo: NO.** Un master de 30 min pesa 0,5-1,3 GB. **Lo sube Agustin a mano.** No se
  intenta, no se reintenta, no se busca comprimirlo: a 10 MB un video de media hora es ilegible.
  Dejarle la ficha lista para copiar en `canal/SUBIR_<NN>_AHORA.md` (archivo, miniatura, titulo,
  descripcion con capitulos, hora de programacion, comentario fijado) y pedirle **la URL del
  episodio**, que hace falta para la descripcion y el "video relacionado" de cada short.

Comprobar ademas que la extension responde antes de prometer nada: `list_connected_browsers`
devolviendo `[]` significa que no hay navegador y no hay subida posible, aunque Chrome este abierto.

## 0. Antes de tocar el navegador

0. **Qué tanda es** (modelo de shorts nuevo, 2026-09-08, `canal/SHORTS.md`):
   - **Del episodio** (3-5 piezas con guion exclusivo): igual que siempre, el "video relacionado" es el episodio.
   - **Serie** (un tema, una subtematica por pieza): no hay episodio al que apuntar. El **video relacionado de cada
     pieza es la anterior de la serie** (la 1.a no lleva, o lleva el Dispatch del mismo tema si existe), las N van a
     una **playlist propia con el nombre de la serie**, y salen **una por dia, en orden, a la misma hora**. Publicadas
     salteadas la serie no existe.
   - **Suelto**: sin video relacionado; la descripcion lleva el canal.
   Las rutas dependen de la produccion: hasta el ep. 4, `produccion/shorts/<ep>/`; desde la siguiente,
   `videos/<dir>/shorts/...` (`canal/ESTRUCTURA.md`).

1. **El video largo tiene que estar público** (tandas de episodio). El short apunta a él; si no existe, no hay a
   dónde llevar. Anotar su URL (`https://youtu.be/<id>`) y su ID.
> **Cadencia (decisión de Agustín 2026-09-08): si el episodio es de actualidad, al menos el 75 % de los shorts salen
> el MISMO día que el episodio**, uno por hora desde que el largo está público hasta las ~22:00; el resto al día
> siguiente. Ejemplo real del ep. 2: `--plan 8,2 --horas 14:30,15:30,16:30,17:30,18:30,19:30,20:30,21:30`.
> Para episodios que no caducan sigue valiendo el reparto lento de `canal/SHORTS.md` §4.

2. Generar el plan por código, que resuelve archivos, textos, fechas y horas:
   ```bash
   python produccion/shorts.py <ep> --plan 4,3,3 --desde 2026-09-10 --ep-url https://youtu.be/<id>
   ```
   - `--plan 4,3,3` = cuántos por día (el orden sale de `orden` en `guiones/<ep>/shorts.json`).
   - `--horas 13:00,18:00,21:00` para cambiar las franjas (por defecto esas tres).
   - Deja `produccion/shorts/<ep>/_up/*.mp4` (copias por debajo de 10 MB) y **`PLAN_SUBIDA.json`**, que ya trae
     `archivo`, `titulo`, `descripcion`, `fecha_ui` ("10 sept 2026"), `hora_ui` ("1:00 p.m.") y `publicar_ya`.
2b. **Si la tanda es una SERIE**, el plan no sale de `shorts.py` sino del `publicar.py` de esa produccion:
   ```bash
   python videos/S<NN>_<tema>/publicar.py 2026-09-11 13      # fecha de arranque y hora
   ```
   - Una pieza **por dia**, en orden, a la misma hora: la serie no se reparte por franjas.
   - Deja `videos/S<NN>_<tema>/publicar/PLAN_SUBIDA.json` + `PUBLICAR.md` + `_up/*.mp4` (por debajo de 10 MB),
     con el mismo formato que el de los episodios (`archivo`, `titulo`, `descripcion`, `fecha_ui`, `hora_ui`,
     `publicar_ya`) y ademas `playlist` y `video_relacionado` por pieza.
   - El sello `PART n OF N` **ya viene quemado en el video**: no hay que tocar nada en Studio por eso.
   - Hay que **crear la playlist de la serie una vez** (nombre en `serie.json`) y meter las N ahi.

3. Leer `PLAN_SUBIDA.json` y seguirlo al pie de la letra. **No inventar títulos, horas ni descripciones.**

> **Zona horaria:** YouTube programa en la zona de la cuenta, no en la del usuario. Comprobarla con
> `javascript_tool`: `new Date().toString()`. Si no coincide con lo que Agustín espera, decírselo antes de subir.

## 1. Abrir el navegador y **fijar el canal**

`tabs_context_mcp` → si pide elegir navegador, `AskUserQuestion` con la lista y luego `select_browser`
o `switch_browser`.

> **La cuenta tiene más de un canal.** `studio.youtube.com` a secas abre el que YouTube elija (el 2026-09-08
> abrió `UCjQCcEGSdIUKfurNOC65yaQ`, que no es Paper Trail). **Navegar siempre por URL con el CHANNEL_ID
> explícito** y verificar antes de subir el primer archivo:
> ```js
> location.href.match(/channel\/(UC[\w-]+)/)?.[1] + ' | ' + document.title
> ```
> Si no coincide con el CHANNEL_ID del plan, **parar y avisar**. Subir al canal equivocado es
> el único error de esta tarea que no tiene deshacer limpio.

Paper Trail: `UCYF_JLmNE14ZLEN8ANHGzZA`.

## 2. Por cada short (repetir tal cual)

### 2.1 Abrir el formulario y adjuntar el archivo
```
navigate → https://studio.youtube.com/channel/<CHANNEL_ID>/videos/upload?d=ud
wait 5
```
El `<input type=file>` está oculto y no aparece en el árbol de accesibilidad. Hacerlo visible primero:
```js
const i=[...document.querySelectorAll('*')].filter(e=>e.shadowRoot)
  .flatMap(e=>[...e.shadowRoot.querySelectorAll('input[type=file]')])
  .concat([...document.querySelectorAll('input[type=file]')]);
i.forEach(x=>{x.style.cssText='display:block;opacity:1;position:fixed;top:10px;left:10px;z-index:99999;width:300px;height:40px'});
i.length
```
Después `find "input de archivo"` → `file_upload` con la ruta de `archivo`. Esperar 10 s.
**Nunca clicar "Seleccionar archivos"**: abre el diálogo nativo de Windows, que no se puede manejar.

### 2.2 Título y descripción
`find "campo de título y campo de descripción"` y para cada uno: `left_click` → `wait 2` → escribir.

- **Título**: `ctrl+a`, `Delete`, `type` (viene con el nombre del archivo, hay que borrarlo).
- **Descripción**: está vacía → **escribir directo, sin `ctrl+a`**. Pasar el texto completo de una vez,
  con `\n\n` dentro del mismo `type` para separar link y hashtags.

Verificar SIEMPRE antes de seguir:
```js
function val(id){const e=document.querySelector('#'+id);const d=e.querySelector('div#textbox')||e.querySelector('[contenteditable]');return d?d.innerText:null;}
JSON.stringify({t:val('title-textarea'), d:val('description-textarea')})
```
Si la descripción empieza con una `a` suelta, el `ctrl+a` se escribió como texto: poner el cursor al principio
(`ctrl+Home`) y `Delete`.

### 2.3 Audiencia y pasos siguientes
`find "opción No, no es contenido creado para niños"` → `scroll_to` → `left_click`. **Comprobar en un
screenshot que quedó marcado**: si no lo está, el asistente muestra "Debes responder esta pregunta" y los
"Siguiente" no avanzan (pasa a menudo si se clica sin `scroll_to`).

Después `find "botón Siguiente"` y clicarlo **3 veces** con 2 s entre medio (Elementos de video →
Verificación → Visibilidad).

### 2.4 Programar
`find "botón para expandir la opción Programar"` → clic. Luego:

- **Fecha**: si `fecha_ui` no es la que muestra, clicar el selector y **escribir la fecha en el campo de texto
  del calendario** (`find "campo de texto editable con la fecha dentro del calendario"` → `triple_click` →
  `type "9 sept 2026"` → `Return`). Clicar celdas del calendario por coordenadas falla: el diálogo se mueve.
- **Hora**: `find "campo de hora de programación"` → `form_input` con `hora_ui` → `Return`.
  `form_input` es lo único fiable aquí; escribir con teclado en ese campo revierte a "12:00 a.m.".
  **El selector solo acepta múltiplos de 15 minutos** (el plan ya los respeta).
- Verificar que no haya error:
  ```js
  const d=document.querySelector('ytcp-uploads-dialog');
  JSON.stringify({txt:d.innerText.slice(0,200), futuro:d.innerText.includes('futuro')})
  ```
- `find "botón Programar"` → clic → esperar 10 s.

Si `publicar_ya` es `true` (la hora ya pasó), no programar: expandir "Guardar o publicar", marcar **Público**
y pulsar **Publicar**.

### 2.5 Confirmar
Screenshot. Tiene que decir "Se programó el video — se establecerá como público el …" o "Se publicó el video".
Si sale **"Tuvimos problemas para guardar tu video"**, esperar 15 s: reintenta solo. Si el diálogo sigue abierto
con el botón activo, volver a pulsarlo. Si sale "Seguimos verificando tu contenido", pulsar **Entendido**.

### 2.6 Etiquetas (se anadio el 2026-09-09)

Los shorts tambien llevan etiquetas, y hasta el ep. 4 no se estaban poniendo. Estan en
**Mostrar mas** dentro del paso Detalles, o sea **antes** del primer "Siguiente":

`find "boton Mostrar mas para expandir opciones adicionales"` -> clic -> esperar 4 s ->
`find "campo de etiquetas (tags) para escribir palabras clave"` -> `scroll_to` -> clic ->
`type` la linea entera **con coma final**. Se convierten en chips solos. 8 etiquetas por pieza
entran de sobra (100/500 caracteres).

## 2bis. Trampas del DOM de Studio (medidas el 2026-09-09, 5 shorts)

Tres cosas que cuestan reintentos si no se saben:

1. **Los clics por coordenada y por `ref` pueden no aterrizar.** El frame del screenshot (1568x606)
   no coincide con el viewport CSS (1600x619): la pagina se dibuja a ~0.78 dentro de la imagen y el
   clic cae ~60 px mas arriba. Si un `left_click` sobre un campo no escribe nada, **pasa a JS**:
   `.focus()` + `Range` para campos de texto, `.click()` sobre el elemento real para botones y radios.
   Verifica `document.activeElement` antes de cada `type`. **La unica excepcion es el campo de hora**:
   ahi `find` + `form_input` con el ref sigue siendo lo unico que funciona.
2. **Hay elementos duplicados con el mismo `id`, uno visible y otro fantasma de 0x0.**
   `document.querySelector('#title-textarea')` puede devolver el fantasma (rect 0x0, `offsetParent`
   null) aunque su `innerText` sea correcto. Pasa igual con el boton **Cerrar**. Filtrar siempre por
   `getBoundingClientRect().height > 0`.
3. **`ytcp-uploads-dialog` SIEMPRE mide altura 0**: es un wrapper, el dialogo real es un
   `tp-yt-paper-dialog`. Eso **no** es el sintoma de "renderer saturado" de la tabla §6 — ese error
   de la tabla se refiere a los campos internos midiendo 0x0. Comprobarlo con un screenshot antes de
   dar la subida por perdida.

Y una regla de oro cuando el navegador va lento: **si sale `CDP timed out`, la accion probablemente
SI se ejecuto**. Esperar 15 s y **verificar por JS**; reintentar a ciegas duplica el texto.

## 3. Video relacionado (el paso que hace que esto sirva)

Es el único enlace clicable dentro del feed de Shorts. Se pone **después**, desde la edición de cada video.
Sacar los IDs reales de la lista (no leerlos de un screenshot, se confunden `I`/`l` y mayúsculas):

```
navigate → https://studio.youtube.com/channel/<CHANNEL_ID>/videos/short
```
```js
const m=new Map();
[...document.querySelectorAll('a[href*="/video/"]')].forEach(a=>{const id=(a.getAttribute('href').match(/video\/([^\/]+)/)||[])[1];
  const t=(a.getAttribute('aria-label')||a.title||a.innerText||'').trim();
  if(id && t.length>15 && !t.includes('comentarios') && !m.has(id)) m.set(id,t.slice(0,50));});
JSON.stringify([...m.entries()])
```

Y para cada uno, `navigate → https://studio.youtube.com/video/<ID>/edit`, esperar 10 s y correr:
```js
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function deepAll(){const o=[];const w=r=>{r.querySelectorAll('*').forEach(e=>{o.push(e); if(e.shadowRoot) w(e.shadowRoot)})}; w(document); return o;}
const trig=document.querySelector('#linked-video-editor-link');
(trig.querySelector('button')||trig).click(); await sleep(4000);
const opt=deepAll().find(e=>e.children.length===0 && /<TITULO DEL EPISODIO>/.test(e.textContent||''));
if(!opt) throw new Error('no option');
(opt.closest('ytcp-video-picker-item')||opt.closest('[role=option]')||opt.parentElement).click(); await sleep(4000);
for(let i=0;i<3;i++){const s=deepAll().find(e=>e.tagName==='BUTTON'&&/^Guardar$/.test((e.innerText||'').trim())&&!e.disabled); if(s){s.click(); await sleep(6000);} else await sleep(2500);}
const b=deepAll().filter(e=>e.tagName==='BUTTON'&&/^Guardar$/.test((e.innerText||'').trim()));
JSON.stringify({rel:/<TITULO DEL EPISODIO>/.test(document.body.innerText), guardarDis:b[0]?b[0].disabled:null})
```
**Listo solo cuando devuelve `{"rel":true,"guardarDis":true}`.** `guardarDis:false` = falta guardar: repetir el
bucle de "Guardar". El botón tarda en habilitarse, por eso se intenta tres veces.

## 4. Verificación final (obligatoria)

```
navigate → https://studio.youtube.com/channel/<CHANNEL_ID>/videos/short
```
```js
JSON.stringify([...document.querySelectorAll('ytcp-video-row')].map(r=>{const t=r.innerText.split('\n').filter(x=>x.trim());
  return t.slice(0,1).concat(t.filter(x=>/Programado|Público|Publicado|sept/.test(x))).join(' | ');}))
```
Comprobar: están los N, con las fechas del plan, y ninguno quedó privado. Además leer con `get_page_text` que
ninguna descripción empiece con una `a` suelta ni tenga el link pegado a un hashtag (`...Afk#russia`).

**No cerrar la pestaña al terminar** (regla de Agustin, 2026-09-09): no se cierra ninguna pestaña ni sesion
del navegador. Si estorba, reusarla con `navigate`.

## 5. Qué reportar y qué NO hacer

Reportar: tabla de qué salió cuándo, desvíos del plan (y por qué), y lo que queda para Agustín:
- **El comentario fijado en cada short** (una línea + el título del episodio). No se publica en su nombre.
- Cambiar horas si la zona de la cuenta no era la que esperaba.

No hacer: cambiar títulos o descripciones del plan, publicar shorts si el episodio largo no está público,
tocar la miniatura (en Shorts no se usa), ni añadir tarjetas o frases que no estén en el plan.

## 6. Errores conocidos (los cinco que costaron tiempo)

| Síntoma | Causa | Salida |
|---|---|---|
| La descripción empieza con `a` | `ctrl+a` en un campo sin foco se escribe como texto | `ctrl+Home` + `Delete`; mejor, no usar `ctrl+a` en la descripción |
| El título quedó mezclado con los hashtags | El foco no cambió de campo | Verificar por JS después de escribir; reescribir el campo entero |
| La hora vuelve a "12:00 a.m." | El campo no acepta teclado | `form_input` |
| "Selecciona un momento futuro" | Hora no múltiplo de 15, o ya pasó | Otra franja, o publicar directo |
| `find` devuelve 429 / rate limit | Se agotó el modelo interno de `find` | Seguir con `read_page` (accesibilidad, sin modelo) y `javascript_tool` |
| `form_input` pone la hora en a.m. | El campo usa locale es-ES | Pasar exactamente `"5:30 p.m."` (minúsculas con puntos), no `"5:30 PM"` |
| El calendario propone el día siguiente | Default de YouTube cuando la hora de hoy ya pasó | Corregir a la fecha del plan; si escribir no toma, clicar la celda del día |
| El diálogo de subida queda con **altura 0** y `#title-textarea` mide 0x0 | Renderer saturado; el archivo **sí se subió** y queda un **borrador** con el nombre del archivo | No insistir: el borrador no reabre el diálogo al clicar la fila. Subir el archivo de nuevo desde cero y **borrar el borrador** después (fila → botón `Borrar el video` → marcar la casilla → `Eliminar borrador de video`) |
| `navigate` bloqueado por "Leave site?" | Quedó un diálogo de subida a medio llenar | `window.addEventListener('beforeunload', e=>{e.stopImmediatePropagation(); delete e.returnValue}, {capture:true})` y después `navigate` con `force:true` |

Si la pestaña empieza a dar `CDP timed out` o `Script injection timed out`, el renderer está saturado:
esperar 10-15 s y reintentar. No recargar en medio de un formulario a medio llenar.

## 7. Reparto: el principal planifica, un subagente Opus ejecuta

Verificado el 2026-09-08: **un subagente alcanza el navegador y hereda el que ya está seleccionado**, sin
preguntar nada. Así que la subida se delega y el principal se queda con lo que tiene criterio.

> **El subagente va con Opus** (decisión de Agustín, 2026-09-09). Se probó con Sonnet y no compensa: es lento
> en un formulario de ~20 pasos y se equivoca (se salta el `scroll_to` de la audiencia, escribe el `ctrl+a`
> como texto, no verifica por JS). Cada uno de esos errores cuesta reintentos y a veces un borrador que hay
> que borrar a mano, o sea más tiempo y más tokens que la diferencia de modelo.

**El principal, antes de delegar:**
1. Confirma que el episodio está público y anota su URL y el CHANNEL_ID.
2. Corre `shorts.py <ep> --plan …` y **lee el plan**: orden, títulos, franjas horarias.
3. Comprueba la zona horaria de la cuenta (`new Date().toString()`) y avisa a Agustín si no es la que espera.
4. Abre el navegador y **verifica que Studio está en el canal correcto** (§1).

**Delegado a un subagente Opus, uno por vez** (`Agent` con `model: "opus"`), con este prompt:

```
Subí y programá UN short en YouTube siguiendo la skill youtube-shorts-upload (§2), sin desviarte.
Canal: UCYF_JLmNE14ZLEN8ANHGzZA. Antes de adjuntar nada, verificá que Studio está en ESE canal;
si no lo está, pará y reportá sin subir.
Datos exactos (no los cambies, no los reescribas):
  archivo: <archivo>
  título: <titulo>
  descripción: <descripcion>
  programar: <fecha_ui> a las <hora_ui>     (o: publicar ya, si publicar_ya es true)
Verificá cada paso con los javascript_tool de la skill. Al terminar, reportá: el estado final que muestra
Studio, el título y la descripción tal como quedaron (leídos por JS), y cualquier desvío.
Si aparece algo que no está en la tabla §6 de la skill, PARÁ y reportá sin reintentar.
```

**Reglas del reparto:**
- **Nunca dos subagentes a la vez**: comparten el mismo navegador y se pisan la pestaña. Estrictamente secuencial.
- El principal **revisa el reporte de cada uno** antes de lanzar el siguiente; si un título o una descripción
  volvió distinta de la del plan, la corrige él.
- El **"Video relacionado" (§3) y la verificación final (§4) los hace el principal**, no el subagente: son un
  barrido sobre los N videos y ahí un error se propaga a todos.

Lo que no se delega nunca: elegir qué shorts salen y en qué orden, redactar títulos, decidir qué hacer si
YouTube cambió el formulario, y cualquier cosa que Agustín no haya pedido explícitamente.

## 8. La alternativa que no se usó

La YouTube Data API (`videos.insert` con `status.publishAt`) haría esto sin navegador y sin coordenadas, pero:
sube 1.600 unidades de cuota por video sobre 10.000 diarias por proyecto (≈6 videos/día, no alcanza para 10),
necesita OAuth propio, y **habría que verificar si expone el "video relacionado" de Shorts** — si no lo expone,
ese paso vuelve igual al navegador. Si algún día se sube más volumen, evaluarla; hoy no compensa.
