# Paquete editorial

Contrato local para preparar una promesa coherente antes del guion y comprobar
su apertura en el export final. No genera voz, imagen ni video, no elige una
frecuencia y no sube nada. El flujo por etapas vive en `ENCARGO.md`.

## API

```python
from produccion.paquete_editorial import (
    plantilla, validar_empaque, validar, capturar_evidencia,
)

paquete = plantilla('10', 'El tema elegido', formato='largo')
# Completar sources, packaging, policy y human_qc antes de escribir el guion.
antes_del_guion = validar_empaque(paquete, base_dir=produccion)
# Completar long_video y los shorts originales antes de producir sus medios.
borrador = validar(paquete, base_dir=produccion, exigir_evidencia=False)
# Solo despues de exportar el master definitivo, no desde una intro de muestra:
evidencia = capturar_evidencia('salida/master.mp4', produccion, '_qc/apertura')
paquete['packaging']['hook']['evidence'] = evidencia
final = validar(paquete, base_dir=produccion, exigir_evidencia=True)
```

`produccion` es el directorio del episodio, no la raiz del repositorio. Las rutas
de archivos se resuelven dentro de ese directorio; no se permiten escapes.
Cada short lleva su propio `packaging.hook.evidence` y su propio `media_path`.
La plantilla esta incompleta a proposito: no aprueba fuentes, guiones o medios
vacios, ni adapta silenciosamente paquetes legados.

Los tres validadores devuelven `ok`, `errores`, `advertencias`,
`ready_for_human_qc`, `human_qc_status` y **`publish_allowed: false` siempre**.
`ok` en modo borrador significa contrato de texto completo, no video terminado.
La evidencia completa solo habilita la revision humana final. Una aprobacion
humana se registra aparte con revisor y fecha; este modulo nunca publica.

## Contrato

- `schema_version: 1`, `episode: {id, topic, format, language: 'en'}`.
- `sources`: lista de `{id, claim, status, url}` o `evidence_path` local. Cada
  referencia debe existir y tener `status: 'verified'`. Ese estado es una
  declaracion auditable del investigador, no una verificacion web automatica.
- `packaging.promise`: `{id, question, answer, source_ids}`. La respuesta guia
  el episodio; no obliga a revelarla entera durante la apertura.
- `packaging.title`: `{text, promise_id, source_ids}`. Pregunta + frase corta,
  hasta 100 caracteres y tres hashtags, segun la regla vigente de `CANAL.md`.
  La advertencia a partir de 71 es orientativa. Si se incluye
  `packaging.description: {text, source_ids}`, debe llevar los mismos tres tags.
- `packaging.thumbnail`: `{text, promise_id, source_ids, country_flags, brief,
  image_path}`. La pregunta debe corresponder a la promesa. Una abreviacion
  explicita usa `question_ref` y `coherence_note`; no demuestra equivalencia.
  Un tema sin paises puede justificar `country_flags_no_aplica`.
- `packaging.hook`: misma promesa/fuentes; `visual: {start_s: 0, action,
  response_by_s: 0..1, response}` y `audio: {start_s: 0..<2, text, kind}`.
  La accion concreta del cuadro cero reconoce la promesa y sus datos. No basta
  una nota que diga "hacer atractivo"; el director debe mostrarla realmente.
- `long_video`: `script_text` o `script_path`, `media_path`, `published`,
  `visibility` y `public_url`. No atribuir a un nuevo master el estado publicado
  de una version anterior.
- `shorts`: cada elemento tiene `id`, `content_mode: 'original_script'`,
  `standalone: true`, guion completo, `duration_estimate_s`, `source_ids`,
  `twist: {text, at_s, source_ids}`, `cta`, `packaging` y `media_path`.
  Giro y CTA tienen que aparecer literalmente en el guion, no solo en notas.
  `engagement.comment_question` declara una pregunta concreta para comentarios
  que tambien debe pronunciarse en el guion, con un cierre propio de la historia.
  Se bloquean guiones duplicados y recortes literales con CTA agregado.
- `cta`: `{text, related_episode_id, availability, related_url,
  advanced_features_enabled}`. Mientras el principal esta pendiente no se puede
  afirmar que ya esta disponible. Para video relacionado se exige principal
  publico/no listado, URL real coincidente y funciones avanzadas verificadas.
  No prometer un enlace clicable en la descripcion del Short.
- `policy`: `manual_schedule: true`, `no_auto_publish: true`. El rango por
  defecto `shorts_min: 3`, `shorts_max: 5` es una referencia ajustable mediante
  `shorts_override_reason`. El formato vigente exige al menos 50 segundos por
  short; se comprueban estimacion y duracion real por separado. El export del
  short debe tener orientacion vertical (ancho menor que alto).
- `human_qc`: `{status: 'pending'|'approved'|'rejected', reviewer, reviewed_at}`.
  Una aprobacion requiere revisor `Agustin` y fecha ISO-8601 UTC aware no futura;
  son declaraciones documentadas, no autenticacion ni permiso de subida.
  `goals.guaranteed` debe ser `false`: las metas no son pronosticos.

## Evidencia real

`hook.evidence` contiene `video_path`, `video_sha256`, tres `frames` de los
segundos 0, 1 y 2 con `path` y `sha256`, y `audio` con `path`, `sha256`,
`first_audible_s` y `method`. El audio debe corresponder al mismo export final,
no a un WAV correcto que luego no quedo en el montaje. Un cambio del archivo
invalida sus hashes y obliga a recapturar.

Con `exigir_evidencia=True` se usa ffprobe/ffmpeg local para verificar pistas,
duracion, cuadros no uniformes y similitud de cada captura con el segundo real.
Se permite una captura reducida de al menos 320x180. La medida de sonido usa
PCM mono a 16 kHz, ventanas de 10 ms y umbral RMS cercano a -45 dBFS. No se
renderizan videos ni se realizan llamadas pagas.

## Limites

La igualdad de IDs, coincidencias de palabras, una imagen no vacia y un pico
audible **no prueban equivalencia semantica, verdad factual, originalidad,
legibilidad, emocion ni calidad de la animacion**. La prueba RMS tampoco sabe
si esta oyendo voz, musica o ruido. Una pista musical temprana no demuestra
que la pregunta narrada se oiga a tiempo. El QC humano debe mirar y escuchar
los segundos 0/1/2, comprobar que la voz comienza antes de 2 s, cotejar fuentes
y cifras, y revisar la apertura a tamano de telefono. Este modulo no sustituye
los controles de geografia, sincronizacion, cifras y composicion del renderer.

## Comandos

```powershell
python produccion/paquete_editorial.py videos/09_deuda_eeuu/publicar_v5/paquete_editorial.json --base videos/09_deuda_eeuu --solo-empaque
python produccion/paquete_editorial.py videos/09_deuda_eeuu/publicar_v5/paquete_editorial.json --base videos/09_deuda_eeuu --sin-evidencia
python produccion/paquete_editorial.py videos/09_deuda_eeuu/publicar_v5/paquete_editorial.json --base videos/09_deuda_eeuu
python -m unittest produccion.test_paquete_editorial produccion.test_encargo
```

Sin `--sin-evidencia`, el paquete 09 permanece bloqueado hasta incorporar los
exports y pruebas reales de sus cuatro shorts y el master definitivo. Brian es
la voz elegida para los nuevos shorts; no se ha generado audio desde este modulo.

Referencias de plataforma: [titulos y miniaturas](https://support.google.com/youtube/answer/12340300),
[video relacionado en Shorts](https://support.google.com/youtube/answer/14075157).
