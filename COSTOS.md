# Costos y proveedores · qué reemplaza a PicsArt cuando se acaban los créditos

> Investigado el **2026-09-08**, con el saldo en 54 créditos y el reset el 14/09.
> Lo que dice "medido" se midió contra la API real ese día (dry-run, sin gastar).

> ## REGLA INQUEBRANTABLE (Agustín, 2026-09-08; solo él puede cambiarla)
> **EXCEPCIÓN AUTORIZADA POR AGUSTÍN (2026-09-09), solo para la producción 04 (Malvinas): el tope sube a USD 5.**
> Literal: *"en este caso tenés un poco más de margen porque es un video muy largo y con shorts. Pero es una
> excepción. No te pases más de los 5 dólares."* Motivo: 32 min de episodio + 5 shorts con voz propia.
> Reparto real: voz del episodio 2,92 + voz de la intro 0,08 + 4 imágenes de rig y 2 remove-bg 0,27 + voz de los
> 5 shorts 0,65 = **3,92**, con 1,08 de margen para reintentos. **Para las demás producciones sigue el tope de USD 4.**

> **Gasto máximo por producción en fal.ai: USD 4** (Agustín, 2026-09-08; antes eran USD 3 por video y los subió al
> redefinir los shorts, que ahora llevan guion y voz propios). Un solo tope para el episodio **y sus shorts**.
> **Es un techo, no un presupuesto** (Agustín, 2026-09-08): que quede margen no es motivo para usarlo, y una
> producción que reusa assets gasta solo la voz. **Antes de generar nada, buscar en el índice**:
> `python produccion/indice_assets.py buscar <lo que haga falta>` (`canal/ASSETS.md`, `canal/INDICE_ASSETS.md`;
> hay 49 créditos de assets ya pagados y reusables).
> Equivale a ~138 créditos de PicsArt (1 cr ≈ $0,029). Reparto que entra en los $4: **voz de los shorts $0,46-1,15**
> (`canal/SHORTS.md` §6) · voz George 17.400 chars $1,74 · imágenes 6 × Flux Pro $0,30 · 2 planos hero de 5 s
> (Wan 2.5 720p $0,50 o Kling 2.5 Turbo $0,35) con un solo reintento $0,70-1,00 · música reusada $0. Total $2,75-3,00.
> Lo que NO entra: 3 hero con dos intentos (plan de `CREATIVO.md` §3 en PicsArt), renarración completa, Veo. Si un
> episodio necesita más, se le pregunta a Agustín antes de gastar el primer centavo por encima.

> **Conexión hecha (2026-09-08):** clave de fal.ai guardada por Agustín como variable de entorno de usuario `FAL_KEY_GEO`
> (espejada en `FAL_KEY` para `fal_client` de Python). Servidor MCP registrado a nivel usuario:
> `claude mcp add --transport http -s user fal https://mcp.fal.ai/mcp --header 'Authorization: Key ${FAL_KEY_GEO}'`.
> Las variables se leen al arrancar: reiniciar la app de Claude después de crearlas. Prueba pendiente: un beat del ep. 2 con George ($0,16).

---

## 0. El diagnóstico en una línea

**PicsArt no es el motor del canal. Es el surtidor de la voz.** El render, el chequeo de encuadre, la
mezcla, los shorts y la entrega ya corren a 0 créditos en esta máquina (`motor.py` + ffmpeg). Lo único
que se paga de verdad, episodio tras episodio, es **la narración de George**.

| Pieza | Qué cuesta hoy en PicsArt | Peso real en el ciclo |
|---|---|---|
| **Voz ElevenLabs v3 (George)** | 3,4 cr / 1.000 caracteres → **~60 cr/episodio** | **~95 % del gasto** |
| Imágenes Flux 2 Pro (rigs, props) | 1 cr por imagen | 4-10 cr/episodio |
| Cues de música Lyria | 3 cr por cue | 0-15 cr, reutilizables |
| Remove Background | **0 cr, ilimitado** | 0 |
| MP Scene (compositor) | **0 cr** | 0 — además ya no se usa: el render es local |

Ep. 1: ~90 cr de voz. Ep. 2: 17.400 caracteres → ~63 cr. Con 2 episodios por mes, la voz sola pide
**~120 cr/mes** de una cuota de 500 que además **se evapora el día 14**.

---

## 1. El número que ordena todo lo demás

Medido con `estimate_only` contra la cuenta de ElevenLabs conectada por MCP:

```
977 caracteres · voz George (JBFqnCBsd6RMkjVDRZzb) · eleven_v3 → 977 créditos = 9,77 ¢
977 caracteres · voz George                        · eleven_v4 → 977 créditos = 9,77 ¢
```

**ElevenLabs cobra 1 crédito por carácter = $0,10 por 1.000 caracteres**, y v4 (el modelo nuevo) sale
exactamente lo mismo que v3.

Con eso se despeja cuánto vale un crédito de PicsArt:

> PicsArt cobra **3,4 créditos** por lo que ElevenLabs cobra **$0,10**
> → **1 crédito de PicsArt ≈ $0,029**
> → los 500 cr/ciclo valen **≈ $14,50**, que es el plan **Pro de PicsArt ($15/mes)**.

**PicsArt no te cobra caro: te revende ElevenLabs casi al precio de lista.** Un episodio te sale $1,77
ahí y $1,74 en cualquier otro lado. **El problema no es el precio unitario. Es la forma del contrato:**
pagás $15 fijos por mes, tenés techo de 500, y lo que no gastás se quema el día 14.

---

## 2. La corrección: **no tomes un plan mensual, pagá por uso**

En la primera versión de esta hoja recomendé el plan Creator de ElevenLabs a $11/mes. **Está mal: son
$11 el primer mes y $22 a partir del segundo.** Con eso los números se dan vuelta.

Tu consumo real son ~35.000 caracteres al mes (2 episodios). Comparado:

| Ruta | Fijo mensual | Costo por episodio | Qué pasa si un mes no producís |
|---|---|---|---|
| PicsArt Pro | $15 | $7,50 | perdés $15 |
| ElevenLabs Creator | $22 | **$11** | perdés $22 |
| ElevenLabs Starter | $6 | $3 | perdés $6 — y 30.000 chars **no alcanzan** para 2 episodios |
| **Pago por uso (fal.ai / ElevenLabs PAYG)** | **$0** | **$1,74** | **$0** |

**Los planes mensuales están pensados para quien consume 5-10× lo que consumís vos.** A cadencia
quincenal, cualquier suscripción es tirar plata. La forma correcta de comprar esto es prepago por uso.

---

## 3. La respuesta a "¿hay una plataforma tipo PicsArt pero barata?": **fal.ai**

Sí, y es casi un clon de PicsArt en la forma: catálogo enorme (600+ modelos), una sola cuenta, y
**MCP oficial en `https://mcp.fal.ai/mcp`** que se enchufa a Claude Code igual que el de PicsArt —
buscás el modelo, consultás el precio, lo corrés desde acá.

La diferencia está en el modelo de negocio:

| | PicsArt | fal.ai |
|---|---|---|
| Cuota mensual | **$15 fijos** | **$0** |
| Cómo se paga | suscripción | cargás saldo y lo gastás |
| Vencimiento | **el día 14, todos los meses** | **365 días** |
| Techo | 500 cr/ciclo | ninguno |
| Si un mes no producís | perdés $15 | perdés $0 |

**Y tiene exactamente lo que usás.** Confirmado en la ficha del modelo: `fal-ai/elevenlabs/tts/eleven-v3`,
**$0,10 por 1.000 caracteres**, y el parámetro `voice` acepta nombre o ID — **"George" está en la lista
de voces**. O sea: misma voz, mismo modelo, mismos tags de actor, mismo precio, sin cuota.

### Cuánto cuesta un video en fal.ai, en dólares

Tarifas de lista de fal, verificadas modelo por modelo:

| Modelo | Precio |
|---|---|
| `elevenlabs/tts/eleven-v3` (voz George) | **$0,10 / 1.000 caracteres** |
| Seedream V4 · FLUX schnell · FLUX Pro (imagen) | **$0,03 · $0,025 · $0,05** por imagen |
| `birefnet/v2` (quitar fondo) | **$0,0008 por segundo de cómputo** → ~$0,002 por imagen |
| Lyria 3 · Lyria 3 Pro (música) | **$0,04 · $0,08** por cue |

Aplicado a tus episodios reales:

| | Episodio típico (como el ep. 2) | Episodio pesado (como el ep. 1) | Peor caso |
|---|---|---|---|
| Voz — 17.400 chars | $1,74 | $1,74 | $1,74 |
| Muestras de dirección | $0 (plan Free de ElevenLabs) | $0 | $0 |
| Imágenes nuevas | 1 rig → $0,04 | 10 rigs y props → $0,40 | $0,40 |
| Quitar fondo | $0,002 | $0,02 | $0,02 |
| Música | $0 (se reusan las cues) | 5 cues Lyria 3 Pro → $0,40 | $0,40 |
| Renarración completa | — | — | +$1,74 |
| Render · coreografía · mezcla · 8-10 shorts | **$0** | **$0** | **$0** |
| **Total** | **$1,78** | **$2,56** | **$4,30** |

**Un video te sale entre $1,80 y $4,30. Lo normal son $1,80.**

Referencias para dimensionarlo:

- **Dos episodios al mes ≈ $3,60.** Contra $15/mes fijos de PicsArt: **ahorrás ~$11 por mes, $137 por
  año** — y si un mes no producís, pagás $0 en vez de $15.
- **$10 de saldo = ~5 episodios completos** (dos meses y medio de cadencia quincenal). El saldo dura
  365 días.
- Un año entero de canal (24 episodios) ≈ **$45**. Hoy ese mismo año te cuesta **$180** en PicsArt.

El unitario es casi idéntico al de PicsArt ($1,77 el episodio allá). **Todo el ahorro viene de sacarte
la cuota fija de encima, no de que el modelo sea más barato.**

### ¿La voz de George cambia en fal? No — pero hay que llamarla bien

George no es un modelo ni una copia: es **un asset de ElevenLabs con un ID fijo**
(`JBFqnCBsd6RMkjVDRZzb`). fal no re-sintetiza nada, le pasa la petición a la misma API de ElevenLabs con
el mismo modelo. **Mismo ID + mismo modelo = misma voz, exactamente.** PicsArt hace lo mismo; los dos
son intermediarios del mismo motor.

Lo que sí puede sonar distinto si no lo controlás:

| Riesgo | Por qué | Cómo se evita |
|---|---|---|
| **Agarrar otro George** | En la librería de ElevenLabs hay **~15 voces llamadas "George"** (*Warm Explainer*, *Calm and Simple*, *perpetually exasperated*, *King George*…). El parámetro `voice` de fal acepta nombre **o** ID. | **Pasar siempre el ID `JBFqnCBsd6RMkjVDRZzb`, nunca la cadena `"George"`.** |
| Modelo distinto | `eleven_multilingual_v2` actúa distinto que `eleven_v3` e **ignora los tags** `[whisper]`, `[dry]`… | Fijar `eleven-v3` (o v4 si lo aprobás en el A/B). |
| `stability` | fal lo expone con default 0,5 (= "Natural"). Cambia la intensidad de la actuación, no la identidad. | Dejarlo en 0,5 y no tocarlo entre episodios. |
| `apply_text_normalization` | Default `auto`. Decide si "1991" se lee *nineteen ninety-one* o *one thousand nine hundred ninety-one*. **El canal está lleno de fechas y cifras.** | Fijarlo explícito y verificarlo en el primer beat con números. |

Y una aclaración honesta que vale para cualquier proveedor: **dos generaciones del mismo texto nunca son
idénticas.** La síntesis es estocástica — por eso el ep. 1 narrado dos veces sonó distinto *dentro de
PicsArt*. Lo que se conserva es el timbre, el acento y el carácter del hablante, no la toma exacta.

**Cómo comprobarlo por $0,16:** regenerar en fal un beat ya publicado del ep. 2 (~1.600 caracteres) con
el ID y `eleven-v3`, y escucharlo pegado al original. Si suena como el mismo narrador, la migración está
validada y no hace falta discutirlo más.

### Si alguna vez querés bajar todavía más el costo de la voz
En fal conviven modelos más baratos con el mismo formato de llamada: **Chatterbox $0,025/1k**
(→ $0,44 el episodio) y **Kokoro $0,02/1k** (→ $0,35, pero Kokoro ya lo rechazaste: "sin alma").
No los recomiendo para el narrador del canal — sí como voces secundarias si algún día hacés citas o
personajes que hablan.

---

## 4. Las otras candidatas que miré

| Plataforma | Formato | ¿Voz George v3? | Imágenes | MCP | Veredicto |
|---|---|---|---|---|---|
| **fal.ai** ⭐ | prepago, 365 días | **Sí, $0,10/1k** | $0,025-0,05 | **oficial** | **el reemplazo más parecido a PicsArt** |
| **ElevenLabs PAYG** | pago por uso en USD, sin plan | Sí, $0,10/1k | no | **ya conectado** | solo voz, pero es la fuente original y ya está enchufado |
| Replicate | pago por uso | no confirmado | **desde $0,003** | sí | catálogo enorme; el más barato en imagen |
| WaveSpeedAI | prepago | Sí, $0,10/1k | sí | no | mismo precio, ninguna ventaja sobre fal |
| kie.ai | prepago | sí | sí | no | agregador barato (Nano Banana, Veo, Suno); bonus por cargas grandes |
| Runware | prepago | no | **$0,0006** | no | solo imagen; imbatible en volumen, irrelevante para vos |
| Higgsfield | créditos/plan | no | sí | **ya conectado** | hoy tenés 10 cr en plan free; no reemplaza la voz |

**Ningún revendedor baja de $0,10 por 1.000 caracteres en eleven v3.** Es el precio de lista de
ElevenLabs y todos lo respetan. Si aparece uno más barato, o está reempaquetando otro modelo o está
violando los términos — no es una ruta para un canal que quiere monetizar.

---

## 5. Voz — el cuadro completo

| Ruta | Costo por episodio | ¿Sigue siendo George? | Nota |
|---|---|---|---|
| **fal.ai (eleven-v3)** ⭐ | **$1,74** | **Sí** | sin cuota, saldo 365 días, MCP oficial |
| **ElevenLabs PAYG** | **$1,74** | **Sí** | sin plan; verificar la licencia comercial en PAYG |
| PicsArt (hoy) | $1,77 | Sí | pero con $15/mes fijos, techo y vencimiento |
| ElevenLabs Starter $6 | $3 | Sí | 30.000 chars: no alcanza para 2 episodios |
| ElevenLabs Creator $22 | $11 | Sí | 6× más caro que pagar por uso, para tu volumen |
| Gemini 3.1 Flash TTS | ~$0,54 (gratis en AI Studio) | **No** | #2 en calidad, por encima de v3; acepta tags inline |
| Inworld TTS 1.5 | $0,17-0,44 | **No** | #1 en calidad en el ranking 2026 |
| OpenAI TTS | ~$0,26 | **No** | el mejor ratio calidad/precio |
| Chatterbox en fal | $0,44 | **No** | open source alojado |
| Local (Kokoro/Chatterbox) | $0 | **No** | esta laptop es Intel Arc sin CUDA: horas de CPU por episodio |

**El punto que decide:** ya tenés 2 episodios publicados con George. Cambiar de narrador en el ep. 3 es
un costo de identidad, no de dinero — y como pagando por uso la voz sale **$1,74**, no hay ninguna
razón económica para cambiarla. Gemini es el plan B si algún día querés costo cero absoluto.

**Un experimento gratis:** `eleven_v4` cuesta exactamente lo mismo que v3 (medido). Vale un A/B de un
beat: si actúa mejor, es un upgrade de calidad a costo cero.

### El plan Free de ElevenLabs: para qué sirve y para qué no

**No sirve para narrar episodios**, por dos razones independientes:

1. **No alcanza.** 10.000 créditos/mes contra 17.400 de un episodio: te quedás sin voz **en el minuto
   10 de 18**, con un solo episodio por mes. La cadencia quincenal pide 34.800 — el 29 % de lo necesario.
2. **No tiene licencia comercial y exige atribución a ElevenLabs** en todo lo que publiques. El canal
   existe para monetizar (partner program, sponsors, `ESTILO.md` §"legal"). Narrar con el plan Free y
   después monetizar es violar los términos del único insumo pago del proyecto.

(Abrir varias cuentas gratis para juntar los caracteres viola los términos, hace que te cierren la
cuenta, y **tampoco resuelve el punto 2**: la restricción es sobre el uso comercial, no sobre el volumen.)

**Para qué sí sirve, y vale la pena:** para **todas las muestras y pruebas de dirección**. En el libro
mayor del ciclo gastaste 6 cr en "muestras de voz" (09-04) + 3 cr en la "muestra dramática" (09-07) —
~9 cr por episodio en tomas de prueba que nunca se publican. Eso entra holgado en los 10.000 gratis.

**La regla que sale de esto:** *probar en Free, publicar pagando por uso.* Ajustás los tags de actor,
comparás v3 contra v4, elegís el registro — todo gratis — y recién cuando el beat está decidido lo
generás en fal.ai por $0,10 cada 1.000 caracteres.

Si lo que buscás es un episodio entero a **costo cero real y legal**, la ruta no es ElevenLabs Free:
es **Gemini 3.1 Flash TTS en AI Studio** (§5). El precio ahí es cero de verdad, pero es otra voz.

---

## 6. Imágenes (rigs y props · 1 cr c/u en PicsArt)

| Ruta | Costo | Nota |
|---|---|---|
| **Google AI Studio (Gemini image)** | **$0** | ~50 req/día a 2K sin marca de agua |
| fal.ai (Seedream / FLUX) | $0,025-0,05 | misma cuenta que la voz |
| Replicate | desde $0,003 | el más barato por unidad |
| SDXL local | $0 | **solo en la PC de la 3070**; esta laptop es Intel Arc |

Con 4-10 imágenes por episodio esto es ruido presupuestario. Dos avisos que ya están en tus docs:
PicsArt rechaza por moderación cualquier nombre de persona real (`prompts_lideres.md`) — Gemini también,
así que la técnica de describir por atributos se mantiene; y `ESTILO.md` §6 prohíbe **FLUX.1-dev** por
licencia no comercial: si alguna vez vas a local, **schnell (Apache 2.0)**, nunca dev.

---

## 7. Fondo transparente (hoy 0 cr, ilimitado)

Si te vas de PicsArt perdés un servicio que era gratis. Se reemplaza con **`rembg` local**
(`pip install rembg`), modelos U2Net/BiRefNet, offline, sin límite, sin cuenta. Un par de segundos por
imagen en CPU y el volumen es de unas pocas por episodio. **Costo: 0, para siempre.**

---

## 8. Música — acá hay un conflicto abierto en tus propios documentos

- `ESTILO.md` §7: *"**Nunca música de PicsArt** — sus Terms prohíben expresamente percibir ingresos por
  publicidad en obras que la incluyan."*
- `produccion/CREDITOS_MUSICA.md`: las cues de los actos **son Lyria vía PicsArt**, 3 cr cada una.

Las dos cosas no pueden ser verdad a la vez sin poner en riesgo la monetización de los episodios ya
publicados. **Esto no es un tema de créditos, es un tema de si el canal puede cobrar.** Se resuelve de
una de dos formas: releer los Terms y anotar la conclusión, o reemplazar las cues por **YouTube Audio
Library** o **Kevin MacLeod (CC-BY, monetizable con crédito)** — que es, textualmente, lo que tu propio
`ESTILO.md` §7 manda hacer. Costo: $0 en las dos rutas.

Nota al margen: salir de PicsArt también **tapa un agujero legal que vos mismo dejaste anotado** en
`ANIMACION.md` §0 — *"los Terms de PicsArt no dicen nada explícito sobre derechos comerciales del output
de IA"*. Comprando por uso en un proveedor de API los términos de salida son explícitos.

---

## 9. MP Scene (el compositor)

`ANIMACION.md` §1 lo trata como el motor y avisa: *"si cambian los límites de render gratis, se pierde
el motor de un día para el otro"*. **Ese riesgo ya lo desactivaste sin darte cuenta**: los episodios 1
y 2 se renderizaron con `motor.py` local (PIL + ffmpeg, 20 workers, ~40 min). Salir de PicsArt no te
cuesta el motor. Conviene bajar MP Scene de "motor" a "backend alternativo" en la doc.

---

## 10. Los totales

| | PicsArt hoy | **fal.ai (recomendado)** | Ruta $0 |
|---|---|---|---|
| Voz | 3,4 cr/1k, techo 500 | **eleven-v3 George, $1,74/ep** | Gemini TTS gratis (voz nueva) |
| Imágenes | Flux 1 cr | Seedream/FLUX $0,03 · o AI Studio $0 | Google AI Studio $0 |
| Quitar fondo | 0 cr | `rembg` local $0 | `rembg` local $0 |
| Música | Lyria 3 cr ⚠️ | YouTube Audio Library / Kevin MacLeod $0 | ídem |
| Render | local $0 | local $0 | local $0 |
| **Fijo mensual** | **$15** | **$0** | **$0** |
| **2 episodios/mes** | **$15** | **≈ $3,60** | **$0** |
| **Un año (24 episodios)** | **$180** | **≈ $45** | **$0** |

---

## 11. Escalar a 1 video por día (o cada dos) — el cálculo que cambia todo

> Pedido de Agustín, 2026-09-08: *"Tengo ganas de generar un video por día o cada dos días mínimo, más
> los shorts."*

A cadencia quincenal el costo era irrelevante ($3,60/mes). **A 1 video por día, la voz pasa a ser el
presupuesto entero** y conviene elegirla con la calculadora en la mano.

Un episodio de 15-17 min = **17.400 caracteres ≈ 18 minutos de audio**.
30 episodios/mes = **522.000 caracteres**. 15 episodios/mes = **261.000**.

### Precio de la voz, por modelo

| Modelo | Tarifa | $/episodio | **$/mes a 15 ep** | **$/mes a 30 ep** |
|---|---|---|---|---|
| **ElevenLabs v3 — George, la voz actual** | $0,10/1k chars | $1,74 | **$26,10** | **$52,20** |
| ElevenLabs Flash v2.5 — George, **sin tags de actor** | $0,05/1k | $0,87 | $13,05 | $26,10 |
| Chatterbox (en fal) | $0,025/1k | $0,44 | $6,60 | $13,20 |
| **Gemini 3.1 Flash TTS** | $20/1M tokens de audio | $0,54 | **$8,10** | **$16,20** |
| Azure Neural HD | $22/1M chars | $0,38 | $5,74 | $11,48 |
| Kokoro (en fal) — *ya rechazado* | $0,02/1k | $0,35 | $5,25 | $10,50 |
| Azure Neural estándar | $16/1M chars | $0,28 | $4,18 | $8,35 |
| **OpenAI `gpt-4o-mini-tts`** | $0,015/min de audio | **$0,27** | **$4,05** | **$8,10** |
| Gemini 3.1 Flash TTS en **modo batch** | mitad de precio | $0,27 | $4,05 | $8,10 |
| **Azure — tier gratis F0** | **500.000 chars/mes, no vence** | **$0** | **$0** | **$0** hasta 28 ep, después $16/1M |

Lo demás sigue siendo calderilla incluso a 30 episodios: imágenes ~$2,70/mes (3 nuevas por episodio),
música ~$0,40/mes (las cues se reusan), y **render, coreografía, mezcla y los 300 shorts siguen en $0**.

### Lo que dicen los números

**Mantener a George cuesta $52/mes a cadencia diaria.** Es 6 veces lo que cuesta la alternativa más
barata creíble. A quincenal la diferencia eran $2 al mes y no valía ni pensarlo; a diaria son **$44 al
mes, $528 al año**, y ahí sí es una decisión.

**Y acá está el dato que decide:** en el ranking de calidad de TTS de 2026, **Gemini 3.1 Flash TTS
queda #2, por encima de ElevenLabs v3** (Inworld 1.5 Max es #1). Acepta dirección en lenguaje natural
y tags inline (`[whispers]`), que es exactamente el modelo mental de `dirigir.py`. **Cambiar de George
a Gemini no es bajar de categoría: es pagar $16 en vez de $52 por una voz que rankea igual o mejor.**

**El momento de cambiar es ahora.** Tenés 2 episodios publicados. Con 200 episodios encima, cambiar de
narrador es impensable; con 2, no lo nota nadie. Cada mes que pasa el cambio se encarece.

### La palanca más grande no es el proveedor: es la duración

El guion de 15-17 min es una decisión de la etapa quincenal. **A cadencia diaria, casi ningún canal de
geopolítica hace 16 minutos** — el formato diario vive en 6-10 min. Si el episodio baja a ~8 minutos
(≈1.150 palabras ≈ 8.000 caracteres):

| | 17.400 chars (16 min) | 8.000 chars (8 min) |
|---|---|---|
| ElevenLabs v3, 30 ep/mes | $52,20 | **$24,00** |
| Gemini, 30 ep/mes | $16,20 | **$7,50** |
| Gemini batch, 30 ep/mes | $8,10 | **$3,75** |

**Acortar el episodio ahorra más que cambiar de proveedor, y además es lo que hace viable la cadencia.**
Con las dos palancas juntas: **de $52/mes a $7,50/mes.**

### El límite real no es la plata

Hay que decirlo con todas las letras: **a 1 video por día el cuello de botella no son los dólares, son
las horas** — y eso ya está escrito en `RETOMAR.md` ("el límite pasa a ser horas"). Hoy un episodio
pide guion + dirección + alineación (10 min de whisper) + **un archivo de coreografía de ~600 líneas
escrito a mano** + chequeo de encuadre + 40 min de render + mezcla + 8-10 shorts.

El render sí escala (40 min × 30 = 20 h/mes, corre solo de noche). **Lo que no escala es la coreografía
a mano.** El pendiente #4 de la skill — `escena.py`, el motor genérico para que un episodio nuevo no
copie 600 líneas de `piloto3.py` — deja de ser una mejora y pasa a ser **el requisito para que la
cadencia diaria exista**. Sin eso, el presupuesto de voz da igual: no vas a llegar a 30 episodios.

### Recomendación para cadencia diaria

1. **Episodios de 8-10 min**, no de 16. Es la palanca de mayor retorno, en costo y en horas.
2. **Voz: Gemini 3.1 Flash TTS**, en batch si aplica. **$3,75-7,50/mes** a 30 episodios de 8 min.
   Portar los tags de `dirigir.py` es casi 1:1.
3. **Prueba antes de decidir:** narrar un beat ya publicado del ep. 2 con Gemini y con George, y
   escucharlos en fila. Si la diferencia se nota, George a 8 min sale $24/mes y sigue siendo asumible.
4. **`escena.py` primero.** Es el que decide si la cadencia diaria es real.
5. Azure F0 (500.000 chars gratis al mes, no vence) queda como red de emergencia a costo cero, con la
   advertencia de que su actuación está por debajo de todo lo demás de esta tabla.

---

## 12. ¿Higgsfield o fal para animación generativa?

> Pregunta de Agustín, 2026-09-08: *"si metemos más animaciones con IA y todo, ¿qué nos conviene más?"*

**Depende del volumen, y el punto de quiebre es nítido: ~13 clips generativos de 5 s por episodio.**

### Los dos modelos de negocio

| | **fal.ai** | **Higgsfield** |
|---|---|---|
| Formato | pago por segundo, sin cuota | **Plus $59/mes** (1.200 cr) · **Ultra $129/mes** (3.000 cr) |
| Créditos | saldo prepago, 365 días | **no acumulan**, resetean cada mes |
| Kling 3.0 | **$0,029/segundo** | incluido en **365-day Unlimited** |
| Hailuo 02 | $0,045/s | ídem |
| Seedance 2.0 | $0,092/s | ídem |
| Veo 3.1 Fast | $0,15/s | — |
| **Voz George (eleven-v3)** | **sí, $0,10/1k** | **no** |
| Extras propios | ninguno (API cruda) | presets de cámara, Genjutsu (transferencia de movimiento), lipsync, Clipper, Marketing Studio |

**El dato que decide:** los planes Plus y Ultra de Higgsfield incluyen **acceso Unlimited de 365 días a
20+ modelos** — entre ellos **Kling 3.0, Seedance 2.0, Nano Banana Pro y GPT Image 2**. Esas
generaciones **no descuentan créditos**: generás todo lo que quieras.

### El punto de quiebre, con números

Un clip hero de 5 s con Kling 3.0 en fal = **$0,15**.

$59 (Plus) ÷ $0,029 por segundo = **2.034 segundos de video generativo al mes** para empatar.
Repartido en 30 episodios: **68 segundos por episodio ≈ 13-14 clips de 5 s.**

| Uso generativo | 30 ep/mes en **fal** | 30 ep/mes en **Higgsfield Plus** | Gana |
|---|---|---|---|
| 1 plano hero por episodio | **$4,50** | $59 | **fal, por 13×** |
| 3 planos hero por episodio | **$13,50** | $59 | **fal, por 4×** |
| 8 planos por episodio | **$36** | $59 | **fal** |
| **13-14 planos por episodio** | **~$59** | $59 | empate |
| 25 planos por episodio | $112 | **$59** | **Higgsfield** |
| Animación generativa como cuerpo del video | $300+ | **$59** | **Higgsfield, sin discusión** |

A cadencia de un video cada dos días (15/mes) el empate se corre a **27 clips por episodio**: todavía
más difícil de justificar.

### Lo que recomiendo

**fal como base, Higgsfield solo si la animación generativa pasa a ser el cuerpo del video.**

Tres razones:

1. **fal te resuelve la voz también.** George en `eleven-v3` vive en fal. Higgsfield no tiene la voz:
   si vas por ahí, igual necesitás fal o ElevenLabs aparte, y terminás pagando dos cosas.
2. **Tu uso declarado es "planos hero"** (`RETOMAR.md`: *"planos hero generativos con los créditos
   sobrantes"*). Eso son 1-3 clips por episodio → **$4,50-13,50 al mes en fal contra $59 fijos.**
3. **Higgsfield repite la trampa de PicsArt**, agravada: cuota fija de $59, créditos que no acumulan,
   y un Unlimited cuyos términos se mueven — la propia doc dice que los modelos nuevos traen ventanas
   de 7 u 11 días, no de 365. Atar el pipeline a una promoción que puede cambiar de mes a mes es el
   mismo error que atarlo al reset del día 14.

**Cuándo sí conviene Higgsfield:** si decidís que el 30-50 % del metraje pasa a ser generativo, o si
querés sus herramientas propias (Genjutsu para transferir movimiento, presets de cámara, lipsync para
los líderes que hablan). Ahí el Unlimited de Kling 3.0 + Seedance 2.0 + Nano Banana Pro por $59 es
imbatible y no hay forma de igualarlo pagando por segundo.

### La advertencia creativa, que pesa más que el precio

**El video generativo no hace animación de papel recortado.** Kling, Seedance y Veo producen imagen
fotorreal o cinematográfica. Todo `ESTILO.md` — la caricatura de recorte de papel de linaje Terry
Gilliam, la mesa de mapas, la paleta de 7 colores — es *el* diferenciador del canal. Meter planos
fotorrealistas en el medio no suma producción: **rompe la identidad y hace que el video parezca dos
canales pegados.**

El uso que sí funciona es **image-to-video sobre tus propios recortes**: partís de un cuadro de papel
ya generado con Flux y lo animás con `start_image` (Kling, Hailuo y Seedance lo soportan). Mantiene el
look y cuesta lo mismo. Cualquier otra cosa es pagar por romper el estilo.

### Y un dato del ep. 1 que conviene mirar antes de gastar en animación

Del análisis del primer día (`canal/ANALISIS_DIA1_EP01.md`): **CTR 1,2 %**, 697 impresiones, 15 vistas,
**promedio 2:18 de 16 minutos**. El diagnóstico que salió de ahí fue miniatura, título y **16 segundos
hasta la primera palabra** — no la calidad de la animación. Nadie abandonó el video en el minuto 2
porque faltaran planos generativos.

**Gastar $59/mes en animación IA mientras el CTR es 1,2 % es optimizar la parte que nadie llegó a ver.**
Las tres correcciones del análisis (miniatura, cold open antes de la intro, `place()` + lint de lugares)
cuestan $0 y mueven más la aguja. La animación generativa es la mejora que viene *después* de que la
gente entre y se quede.

---

## 13. Qué hacer esta semana (quedan 54 créditos y 6 días)

1. **Crear cuenta en fal.ai y cargar $10.** Cubre ~5 episodios y el saldo dura 365 días.
2. **Enchufar el MCP** — endpoint `https://mcp.fal.ai/mcp`, con tu API key de fal:
   ```bash
   claude mcp add --transport http fal https://mcp.fal.ai/mcp
   ```
   (verificá cómo pide la key: algunos endpoints la toman por header `Authorization`.)
3. **Narrar el ep. 3 en fal** con `eleven-v3` + `voice: "George"` y los mismos tags de `dirigir.py`.
   Comparar un beat contra el ep. 2 para confirmar que suena idéntico.
4. **Prueba A/B `eleven_v3` vs `eleven_v4`.** Mismo precio; si v4 actúa mejor, es upgrade gratis.
5. **No dejar morir los 54 créditos del 14/09.** Rinden bien en imágenes (54 rigs/props de Flux 2 Pro),
   no en voz. Gastalos todos en assets reutilizables antes del reset.
6. **Después del 14, decidir si PicsArt se cancela.** Si dos ciclos seguidos no lo tocás, son $15/mes
   que no compran nada.
7. **Resolver el conflicto de música del §8** antes de monetizar. Es el único punto de esta hoja que
   puede costar dinero de verdad.
8. Portar `voz/dirigir.py` para que emita contra fal además de PicsArt: los tags de actor son idénticos,
   es cambiar la función que hace la llamada.

---

## Fuentes

Precios de la voz medidos contra la API (dry-run, 2026-09-08). Lo demás:

- [fal · ElevenLabs eleven-v3 (precio y parámetro `voice`)](https://fal.ai/models/fal-ai/elevenlabs/tts/eleven-v3) · [docs de la API](https://fal.ai/models/fal-ai/elevenlabs/tts/eleven-v3/api) · [precios de fal](https://fal.ai/pricing) · [free credits y vencimiento del saldo](https://costbench.com/software/ai-ml-platforms/fal/free-plan/)
- [MCP oficial de fal + MCP de Replicate](https://mcpservers.md/fal-mcp) · [servidor MCP de fal para Claude Code](https://github.com/wynandw87/claude-code-fal_ai-mcp)
- [ElevenLabs · precios de API y pay-as-you-go](https://elevenlabs.io/pricing/api) · [planes](https://elevenlabs.io/pricing) · [rollover de créditos](https://elevenlabs.io/docs/help-center/account/general/how-does-credit-rollover-work) · [Creator $22 / $11 el primer mes](https://ocdevel.com/blog/20250720-tts)
- [Comparativa de plataformas de inferencia 2026 (fal vs Replicate vs Runware vs Novita)](https://www.teamday.ai/blog/fal-ai-vs-replicate-comparison) · [precios de imagen](https://pricepertoken.com/fal-ai-pricing)
- [WaveSpeedAI · eleven-v3 a $0,10/1k](https://wavespeed.ai/models/elevenlabs/eleven-v3) · [kie.ai](https://kie.ai/elevenlabs/text-to-dialogue-v3)
- [Gemini 3.1 Flash TTS — precio y límites](https://invideo.io/blog/gemini-tts-ai-voice/) · [ranking TTS 2026 por calidad y precio](https://gradium.ai/content/best-ai-voice-generators-2026)
- [Tier gratis de Google AI Studio para imagen](https://www.aifreeapi.com/en/posts/gemini-image-generation-free-api) · [Picsart · planes y precio por crédito](https://aisotools.com/picsart-pricing)
