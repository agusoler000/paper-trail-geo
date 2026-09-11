# VOZ — decisión pendiente y evidencia verificada

> **2026-09-07: registro DRAMÁTICO** (decisión de Agustín: "más emoción, preocupación, ganas de saber más").
> `voz/dirigir.py` reescrito con etiquetas [low, ominous], [hushed], [whisper], [slower, each word landing]; regla:
> tensión = bajar la voz, no subirla. Ganchos al final de cada acto en el guion. Costo: 66 créditos. Saldo 216 → 198 tras
> 6 cues de Lyria. La regla "deadpan cero emoción" de ESTILO.md era del asistente, no de Agustín: derogada.
>
> **DECIDIDO 2026-09-04: ElevenLabs v3 (vía PicsArt `eleven-v3`), voz George (`JBFqnCBsd6RMkjVDRZzb`), con
> dirección de actor entre corchetes.** Agustín delegó la elección ("no puedes hacer tú la investigación?").
> Criterio medido sobre el mismo cold open: George tuvo el rango de tono más amplio (p10-p90 95-167 Hz) y el
> fraseo más variado (21 pausas de longitud distinta vs. 11 idénticas de Kokoro). Kokoro descartado.
> Pipeline: `voz/dirigir.py` (guion → 11 textos por beat con etiquetas) → 11 llamadas a `eleven-v3` →
> `voz/alinear.py` (une beats con 1,5 s, 8 s de pre/post-roll, y recupera tiempos por frase con faster-whisper
> small.en en CPU). Costo real del piloto: **57 créditos** por 2.211 palabras (14.210 caracteres).
> Verificado: las etiquetas no se leen en voz alta. Alineación: 198/200 frases limpias.
>
> Estado anterior: **sin decidir**. Es la decisión abierta más grave del canal (`ESTILO.md` §8).
> **2026-09-03:** Kokoro instalado en ESTA PC (CPU): `pip kokoro-onnx soundfile`, modelo en `C:\ia\kokoro`
> (mismas rutas que la PC de la 3070). `voz/voz.py` narra un guion completo y deja tiempos por línea.
> Marlowe tampoco eligió voz: sus candidatas eran `am_onyx`, `bm_george`, `am_michael`, `am_fenrir`, `bm_lewis`.
> Agustín pidió oír "la de Marlowe" sobre el guion del piloto: se generaron las tres primeras en
> `produccion/audio/01_aviacion_rusa_<voz>.wav`. **Veredicto de Agustín sobre Kokoro (am_onyx, video entero):
> "más aburrido que chupar un clavo, tiene que tener alma".** Kokoro queda descartado como voz final: lee, no actúa.
>
> **Alternativa probada (2026-09-03): ElevenLabs v3 vía PicsArt** (`eleven-v3`, param `prompt`, `voiceId`).
> Acepta dirección de actor entre corchetes ([pause], [wry], [quiet, intense]). Costo medido: **3 créditos por
> ~95 palabras → ~70 créditos por video de 2.200 palabras.** Muestras del cold open en
> `produccion/audio/muestra_eleven_brian.mp3` (nPczCjzI2devNBz1zQrb) y `muestra_eleven_george.mp3`
> (JBFqnCBsd6RMkjVDRZzb). El conector de ElevenLabs directo (creative_generate_speech) exige plan creator para
> las voces de biblioteca: descartado. Higgsfield tiene 10 créditos gratis: irrelevante.
> Investigado el 2026-08-31: 5 frentes + 2 verificadores adversariales.
> Pregunta original del usuario: *"¿Podemos generar una voz a partir de la mía (yo hablo español)
> en inglés y darle algún retoque?"*

---

## 1. Respuesta corta

**Generar, sí. Retocar el acento, no.** El acento y el timbre son el mismo vector en estos modelos
(*entanglement*), documentado desde Zhang et al. 2019 y escrito textualmente en la model card de
Chatterbox:

> *"Ensure that the reference clip matches the specified language tag. Otherwise, language transfer
> outputs may inherit the accent of the reference clip's language."*

No hay perilla, plugin ni EQ que lo separe en post. Y dos papers de 2026 miden que el clonado
**homogeneiza**: los oyentes califican los clones de hablantes con acento como *menos* parecidos al
original. El resultado no es "tu voz con tu acento" — es una voz aplanada.

---

## 2. El giro: el acento NO es el problema de negocio

Verificado con datos de mercado:

| Canal | Acento | Sponsors |
|---|---|---|
| Sabine Hossenfelder (1,8M) | Alemán marcado | **Brilliant ×20, Ground News ×16, NordVPN ×11** |
| Caspian Report (1,9M) | Azerbaiyano marcado | 42 deals de 21 marcas, Ground News ×14 |
| Perun (640K) | Australiano | Ground News ×43 |
| Binkov (935K) | Esloveno marcado | Ground News ×10 |

**El tier compra audiencia, no fonética.**

Lo que sí es un hueco de evidencia: **cero canales verificables con narración TTS o voz clonada
tienen ese tier de sponsor**. No prueba imposibilidad, pero implica ser el caso de prueba.

---

## 3. Política de YouTube (fuente primaria)

- ✅ Clonar **tu propia** voz para voiceovers o dubs está listado **explícitamente** entre los casos
  que **NO** requieren divulgación. Y divulgar no penaliza:
  *"Disclosing AI content won't limit a video's audience or impact its eligibility to earn money."*
- ⛔ La actualización de julio 2026 prohíbe monetizar *"AI-generated personas to deliver information
  on sensitive topics… health, legal issues, finances, or **politics**"*. Geopolítica es *politics*.

**La línea roja no es la voz sintética: es inventar un host humano ficticio que se presente como
experto.** El formato de marca-publicación ya deja del lado correcto. Reforzarlo poniendo el
**nombre real del editor** en el About del canal.

---

## 4. Licencias — verificadas una por una

**Descartados sin ambigüedad:**

| Modelo | Motivo |
|---|---|
| **XTTS-v2** | CPML: *"Use for revenue-generating activity… is not a non-commercial purpose."* Y Coqui cerró en enero 2024 → la licencia comercial ya no se puede comprar de nadie. Es el más descargado y el más recomendado en tutoriales. |
| F5-TTS | pesos `cc-by-nc-4.0` |
| Fish / OpenAudio S1-mini | `cc-by-nc-sa-4.0` |
| Higgs Audio v3 | *"Production / hosted / revenue-generating use"* restringido (era Apache 2.0 en v2 — **las licencias se mueven**) |
| Diff-HierVC | CC BY-NC |
| so-vits-svc | cláusulas extra que prohíben "entornos de producción", contradiciendo su propia AGPL |
| Applio | agrega Terms of Use sobre el MIT pidiendo contacto para uso comercial → usar el upstream **RVC-Project** (MIT puro) |

**Limpios:** Chatterbox MIT · OpenVoice v2 MIT · MeloTTS MIT · Kokoro Apache 2.0 ·
CosyVoice2 **apache-2.0 también en los pesos** (verificado en el front-matter del model card, con
`es` y `en`) · RVC-Project MIT · seed-vc GPL-3.0 · VibeVoice MIT.

> ⚠️ **Copyleft en el árbol de las tres opciones "limpias"**: `pykakasi` (GPL-3.0-or-later) es
> dependencia dura de MeloTTS **y** de `chatterbox-tts` 0.1.7; `phonemizer-fork` (GPL-3.0+) está en
> la ruta de G2P inglés de Kokoro. Hoy no genera ninguna obligación (ejecutás local, no distribuís
> software) y la GNU FAQ es explícita en que la licencia del código no alcanza a la salida. **El
> riesgo aparece solo si algún día empaquetás y distribuís el pipeline.**

---

## 5. Hardware (medido, no estimado)

- **Chatterbox Multilingual entra holgado en la 3070**: pesos reales 3,21 GB en fp32
  (`t3_mtl23ls_v3` 2,14 + `s3gen_v3` 1,06 + `ve` 0,01), ~1,6 GB en fp16. El "hace falta una 4090"
  venía de un proveedor de alquiler de GPU (fuente terciaria con incentivo comercial).
- `chatterbox-tts` 0.1.7 fija **`torch==2.6.0` exacto** y `numpy<2` → coincide con el venv actual.
  **Riesgo de rotura: cero.** No hay upgrade porque 0.1.7 ya es la última versión.
- **IndexTTS-2.5 no cierra en 8 GB**: 5,49 GB de artefactos propios **más** w2v-bert (~2,4 GB),
  MaskGCT, CampPlus y BigVGAN aparte, y exige CUDA 12.8+.
- ⚠️ Todos esos son tamaños en disco, **cotas inferiores**: no incluyen activaciones, KV cache,
  fragmentación del allocator ni contexto CUDA. El único número que vale es
  `torch.cuda.max_memory_allocated()` en la máquina real con un guion real.

---

## 6. Los dos riesgos que deciden

**A — Deriva de acento entre tomas (peor que el acento en sí).**
Issues abiertos de Chatterbox: #267 *"una de cada cinco generaciones sale con acento británico"*;
#422 *"English is American"*; #311 documenta que con el mismo audio y el mismo texto el resultado
local es bastante peor que la página de demos. Un guion de 1.100 palabras se corta en decenas de
chunks → **acento aleatorio dentro del mismo video**. Un acento inconsistente es peor para la marca
que uno marcado y estable.

**B — El ritmo.** Medición propia previa: Chatterbox ~234 wpm, piso realista ~170-175 efectivos.
Llegar a 145 exigiría `atempo` ~0,62, que se escucha. Kokoro llega nativamente con `speed` 0,83-0,88.
El único modelo con control de duración real es IndexTTS-2.5, que no entra en la GPU.

> Corrección de método: la doc de Chatterbox dice *"reducing cfg helps compensate with slower, more
> deliberate pacing"* — o sea, el fabricante **sí** presenta `cfg` como perilla de ritmo. La medición
> propia (que no movió el wpm) sigue siendo la mejor evidencia para este caso, pero conviene
> re-testearla antes de darla por cerrada.

---

## 7. El camino que puede funcionar: invertir el orden

En vez de pedirle a un modelo que genere inglés con tu timbre (donde el acento entra por la
referencia), usar **conversión de voz**:

```
Kokoro genera el inglés   →   el conversor repinta el timbre
(pronunciación + ritmo nativos)      (sin tocar la pronunciación)
```

Respaldado por la definición del campo: *voice conversion* modifica el timbre preservando lo
no-tímbrico, **incluido el acento**; cambiar el acento es una tarea separada (*accent conversion*).
**El acento español nunca entra al pipeline.** Bonus: la conversión preserva el timing, así que el
ajuste `speed` 0,83-0,93 de Kokoro sobrevive intacto — no hay que re-resolver el wpm.

> 🔑 **`chatterbox-tts` 0.1.7 YA incluye `chatterbox.vc.ChatterboxVC` y un `example_vc.py`.**
> Toda esta hipótesis se prueba hoy, en la GPU, licencia MIT, **cero instalaciones y cero venvs
> nuevos**. Los frentes de investigación proponían instalar seed-vc o entrenar RVC sin haberlo visto.

**Si igual se entrena RVC**: grabar la referencia leyendo **en inglés**, no en español — la cobertura
de fonemas ingleses (/æ/, /θ/, /ð/, l oscura) importa más que el acento, porque la articulación la
dicta la fuente.
⚠️ *Lo que NO se sostiene*: la prescripción de `index_rate` 0,25-0,4. La FAQ oficial de RVC habla
**solo de fuga de timbre**, nunca de acento, y dice que con buen dataset el parámetro es irrelevante.

---

## 8. El test que decide (una tarde, costo 0)

Mismo párrafo de ~120 palabras con topónimos y cifras, **generado cortado en frases** (no una frase
suelta — es la única forma de ver la deriva entre chunks):

| | Versión |
|---|---|
| **(a)** | Kokoro puro |
| **(b)** | Kokoro → `ChatterboxVC` con referencia propia en inglés |
| **(c)** | Chatterbox multilingüe clonado, referencia en inglés |
| **(d)** | ídem, referencia en español ← control, va a ser la peor |
| **(e)** | voz real grabada |

Escuchar **a ciegas y al día siguiente** (el mismo día el oído está contaminado). Medir
`torch.cuda.max_memory_allocated()` en la misma corrida.

La decisión real es entre **(a)**, **(b)** y **(e)**. Si (b) no le gana claramente a (a), quedarse
con (a) y no volver al tema hasta el video 10.

---

## 9. Reglas que ya se pueden fijar, decida lo que se decida

1. **El ad read del sponsor se graba con voz real, siempre.** 45-60 s por video quincenal. Cubre la
   exposición a FTC 16 CFR 255 (la revisión 2023 amplió *endorser* a personas generadas por IA) y es
   donde la evidencia dice que la voz humana gana.
2. **Nombre real del editor publicado** en el About. Es la defensa más barata contra el cubo de
   *inauthentic content*: hay un humano atribuible haciendo el juicio editorial.
3. **Nunca un host con nombre propio ni credenciales.** Es la única línea roja verificada.
4. **Si se usa TTS, preferir la voz clonada propia antes que una voz stock de Kokoro** — la voz stock
   compartida con miles de canales es el marcador acústico del perfil *faceless AI channel*.
   *(Tensión no resuelta: Kokoro tiene mejor inglés y mejor control de ritmo. El A/B decide.)*
5. **Congelar la voz como artefacto binario**: `voice_v1.pt` + `referencia_master.wav` + sha256 +
   `requirements.lock` + snapshot local de los pesos. Triple backup. La sesión de grabación no sale
   igual dos veces.
6. **Golden sample de 20 s** re-renderizado antes de cada video para detectar deriva por
   actualización de torch o de driver.
7. **Plan B cuando facture**: ElevenLabs Creator ~11 USD/mes desbloquea cloning profesional con
   licencia comercial. Y el primer gasto discrecional ideal es un **locutor nativo contratado** — es
   la ruta Kurzgesagt y cuesta una fracción de un solo deal del nicho.

---

## 10. Advertencia de método

El verificador encontró que **cuatro afirmaciones del dossier estaban mal atribuidas a fuente
primaria**: la doc de Chatterbox sobre el pacing decía lo contrario de lo reportado, la licencia de
los pesos de CosyVoice sí estaba documentada, VibeVoice no estaba borrado, y el `index_rate` de RVC
no habla de acento. El patrón siempre fue el mismo: la URL correcta con una conclusión que la fuente
no contiene.

Y el punto ciego que ningún frente pudo cerrar: **no existen reportes independientes de cómo suena
concretamente el par referencia-en-español → salida-en-inglés**. Todo lo que hay es inferencia desde
arquitectura y documentación del fabricante. Por eso el test del §8 no es opcional.

> **Límite de tiempo:** una tarde y dos muestras de audio. El canal no tiene videos publicados; el
> problema de voz está resuelto-suficiente con Kokoro. Si no aparece una mejora audible, publicar con
> Kokoro y volver al tema después del video 10.

## 2026-09-07 · A/B para el guion v2 (relato)
Cold open narrado con George (JBFqnCBsd6RMkjVDRZzb) y Brian (nPczCjzI2devNBz1zQrb), 3 cr c/u. Medido con autocorrelación:
| voz | dur | f0 mediana | rango p10-p90 | pausas ≥0,25 s | sd pausas | silencio |
|---|---|---|---|---|---|---|
| George | 29,1 s | 125 Hz | 8,8 semitonos | 10 | 0,38 | 33 % |
| Brian | 26,6 s | 106 Hz | 15,7 semitonos | 9 | 0,14 | 26 % |
Decisión: George (continuidad con lo aprobado, pausas más variadas = drama; Brian corre el riesgo de quedar <15:30).
Dirección por línea en `voz/dirigir.py` (registro "narrador de historia": cinematográfico en escenas, seco en chistes).
