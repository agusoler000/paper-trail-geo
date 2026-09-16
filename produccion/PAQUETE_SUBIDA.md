# Paquete De Subida

`paquete_subida.py` valida una entrega y genera su `SUBIR.md`. No inventa textos,
no genera miniaturas y nunca sube, publica ni programa videos. El director prepara
el contenido; Agustin decide la variante y autoriza cualquier publicacion.

## Entrega Completa

Cada largo y cada short terminado incluye:

- Master real con audio, SHA-256, duracion, dimensiones y fps comprobados.
- Tres titulos distintos, tres miniaturas reales distintas y recomendacion A/B/C.
- Descripcion completa lista para pegar, fuentes publicas, tres hashtags,
  etiquetas de Studio y comentario fijado con pregunta concreta.
- Capitulos del montaje final para largos; son opcionales en shorts.
- Ajustes de Studio, declaracion de contenido sintetico justificada y QC humano.
- Notas sobre subtitulos, derechos/musica, pantalla final, tarjetas y orden de subida.

Titulos: aplicar `canal/CANAL.md` 7.1, pregunta + oracion breve + tres hashtags,
sin prefijo emocional y hasta 100 caracteres. La pregunta de la miniatura y el
primer segundo deben sostener la misma promesa. Las tres opciones deben cambiar
el concepto o la composicion de verdad, no solamente un color o el nombre del
archivo. Revisarlas a 320 px y escuchar los primeros dos segundos del master.

## Manifiesto Version 1

Crear `publicar/paquete_subida.json` dentro de la produccion. Rutas relativas a
la produccion, no al directorio `publicar` ni a la raiz del repositorio.

| Campo | Contenido |
|---|---|
| `schema_version`, `format` | `1`; `largo` o `short` |
| `master` | `path`, `sha256`, `duration_s`, `width`, `height`, `fps` reales |
| `candidates` | Tres objetos con `id` A/B/C, `title`, `thumbnail_path`, `angle`, `why` |
| `recommended` | A, B o C; propuesta editorial, no ganador demostrado |
| `description` | Texto definitivo, hasta 5000 caracteres; incluye capitulos y fuentes |
| `tags` | Lista de etiquetas; hasta 500 caracteres contando separadores y comillas |
| `pinned_comment` | Texto definitivo con una pregunta concreta |
| `chapters` | Objetos `time` y `title`; mismas lineas en la descripcion |
| `settings` | Visibilidad privada, Education, en, made_for_kids=false, publish_at=null |
| `settings.altered_content` | `decision`: yes/no/review; `reason`: justificacion, incluida musica IA |
| `sources` | Lista de objetos `label` y `url` publica |
| `policy` | `no_auto_publish=true`, `manual_schedule=true` |
| `qc` | `status`: pending/approved/rejected; `notes`: lista; nunca inventar aprobacion |
| `extras` | Subtitulos, musica, pantalla final, tarjetas, playlist y pasos de subida |

El perfil del proyecto exige master horizontal de al menos 1920x1080 o vertical
de al menos 1080x1920; la resolucion declarada no demuestra render nativo.
Miniaturas JPG/PNG: 16:9 desde 1280x720 para largos, 9:16 desde 1080x1920 para
shorts. Admite 4K. El limite local es 2 MiB por imagen para compatibilidad movil.
Capitulos: al menos tres, inicio 00:00, orden ascendente y tramos de al menos
10 segundos, incluido el ultimo. No usar tiempos del cuerpo antes del montaje.

## Comandos

Desde la raiz del proyecto, reemplazar `10_tema` por la produccion real:

```powershell
python produccion/paquete_subida.py videos/10_tema/publicar/paquete_subida.json --base videos/10_tema --validar
python produccion/paquete_subida.py videos/10_tema/publicar/paquete_subida.json --base videos/10_tema --salida SUBIR.md
```

Para regenerar una guia existente, agregar `--actualizar`: primero se conserva
una copia verificada en `.versiones_subida/`. Los errores impiden generar la guia.
No editar el Markdown a mano si se usa `encargo.py`: debe corresponder al manifiesto.

El paquete editorial enlaza cada pieza mediante `upload_kit_path` y
`upload_guide_path`. El QC tecnico valida tambien el master comun y conserva
las huellas de todos los archivos. `publish_allowed` siempre es false: aprobar
la estructura de la ficha no aprueba su veracidad ni autoriza una subida.

Requiere Pillow y `ffprobe` disponible en PATH. Pruebas locales sin servicios:

```powershell
python -m unittest produccion.test_paquete_subida produccion.test_encargo
```

La ficha y sus medios son material privado de produccion, no contenido para Git.
Al cambiar de ordenador, regenerar la guia desde el manifiesto: los enlaces
absolutos apuntan al equipo anterior. Registrar de nuevo el QC si cambia su hash.
