---
name: paper-trail-video
version: 1.11.0
changelog:
  - v1.13.0 (2026-09-15, noche): **auditoría completa del motor y motor v4** (`canal/AUDITORIA_MOTOR_2026-09-15.md` = diagnóstico + benchmark contra GeoGlobeTales + especificación; `canal/AUDITORIA_MOTOR_RESULTADO_2026-09-15.md` = lo verificado). Lo nuevo, en orden de importancia: (1) **`produccion/motor.py` v4** (`Mundo` = el mapa como suelo más grande que el cuadro, `Scene(fondo, size, v4=True)` con formato por escena y `zoom < 1`, capa **HUD** en px de pantalla, `Scene.subtitulos()` palabra a palabra desde `_palabras.json`, `corte`+`viaje`, vida por defecto en cámara/rigs/props, `Track.set(0,v)` arreglado, motor determinista — el v3 no lo era: la fase del wobble salía de `id()` y cambiaba por proceso del pool). TODO opt-in: las 12 producciones viejas rinden byte a byte igual. Manual: **`produccion/MOTOR_V4.md`**; plantilla completa: `videos/S12_recibos/coreo4.py` + `escenas4.py`. (2) **`produccion/sync.py`**: auditoría guion→imagen obligatoria (VACIO=0 aborta; CIFRA_SIN_PANTALLA, LUGAR_SIN_MAPA, TEXTO_VIEJO, PROP_HUERFANO; una hoja con un cuadro REAL por línea) — sobre el ep. 09 v1 cazó 60 líneas vacías y el «22 cents / AND 78 CENTS». (3) **`produccion/mapa_v2.py`**: el mapa rico (teal + relieve + países por rol + rótulos sobre el territorio) como biblioteca con caché y chequeo de la regla 24; NE 10m subunits para enclaves (Ceuta). (4) **Shorts en vertical nativo 1080×1920** (`shorts.armar_vertical`): el cuerpo es la pantalla; gancho solo 3,5 s; antes el video ocupaba el 27 % del área del teléfono. (5) `ritmo.py --json` con veredicto (quietos < 20 %, mov. mediano ≥ 2,5, ningún plano > 6 s) en el checklist. (6) **Voz, medido**: las etiquetas de dirección NO mueven el tono; **eleven-v3 lee en voz alta las etiquetas de apertura largas** (≤ 3 palabras); la referencia hace 3 pausas/min y nosotros 20 → `voz/compactar.py` (0,45/0,80 s, reescribe tiempos); timestamps de fal en vez de whisper (`voz/timestamps.py`); **Brian se mueve un 22 % más que George** → **regla 29: se pregunta la voz al empezar cada video** (`voz/voces.py`). (7) Studio 15-sep (`canal/ANALISIS_STUDIO_2026-09-15.md`): la caída fuerte de los largos está en el segundo 10-25 (la intro de preguntas pasa a ≤ 12 s en movimiento) y los shorts con giro retienen 40-59 % contra 8-18 % de los de cifra sola (giro primero en la línea 0). Reglas de producción que salen de la auditoría de las piezas: nada de hoja rayada en los planos de mesa (documento grande sobre el mundo oscurecido + props de escritorio); el enclave se pinta con el color de su país por encima; el gancho va sobre el mapa en movimiento; toda cifra hablada es un objeto grande legible a 405 px.
  - v1.12.0 (2026-09-15, tarde): **tanda S12 «THE RECEIPT» y la referencia de ritmo que paso Agustin.** Pedido: 4 shorts, 2 de `iran war` y 2 de `immigration`, con animacion. Paso 0 corrido en **US y UK** por primera vez, y una correccion importante de metodo: **los numeros de `demanda.py` no son comparables entre consultas distintas** — Trends normaliza cada serie contra su propio pico, asi que para rankear hay que pedir los terminos EN EL MISMO GRUPO y encadenar con un ancla. Medido asi: `iran war` 8,8 (US) / 8,0 (UK) contra `space weapons` ≈0,2 y `strategic petroleum reserve` ≈0,01; la palabra del titulo es `iran war` (37,0 US / **49,5 UK**). Señal D: Iran es de MEDIOS (CNN x4,8) → se entra por el recibo, nunca por el hecho; `immigration` es de CREADORES en **UK** (x2,7) y de medios en US (x2,2), por eso las dos piezas de inmigracion son UK y Europa. Herramienta nueva en el coreo local: **`secuencia()`**, que enciende N cuadros pregenerados del mismo objeto (deposito que se vacia, barras que crecen) — el motor no tiene deformacion por eje, asi que un nivel que baja no se puede hacer escalando. **Referencia externa medida** (`canal/REFERENCIA_GEOGLOBETALES_2026-09-15.md`): GeoGlobeTales, 11,9 M vistas, da **10,7 % de quietos y 9,25 de movimiento** contra nuestros 53-63 % y 0,55-0,74. La prueba (`videos/S12_recibos/prueba_vida.py`) llego a **6,97 de movimiento y 0 violaciones de la regla 1** con tres cambios: el mapa pasa a ser el SUELO del plano (ocupacion 34 % → 72 %), los cortes cambian de CONTENIDO (mapa ↔ mesa) en vez de sacudir la camara, y el color de los paises narra. **Leccion cara: perseguir el numero de `ritmo.py` produce basura** — diez saltos de camara en 25 s subieron el movimiento a 4,58 y Agustin lo rechazo por grotesco; el movimiento que sirve es el motivado. Trampas nuevas: `motor.Rig` se ancla por la **esquina superior izquierda** (14 violaciones seguidas de la regla 1 al colocarlo a ojo); un subtitulo anclado a camara **no puede cruzar un corte**; la hoja de mapa tiene que ser **16:9** o `Scene.window()` deja medio mapa fuera para siempre; y al pintar un pais, la marca del enclave va **por encima** del color o el mapa afirma lo contrario del guion.
  - v1.11.0 (2026-09-15): **por qué los episodios se ven "sosos", medido**. Pregunta de Agustín (*"la gente se va porque son sosos, ¿me equivoco?"*): no se equivoca, y hay número. Herramienta nueva `produccion/ritmo.py` (0 cr, ffmpeg + numpy) con tres métricas: **quietos** (% de muestras a 4 fps cuya diferencia con la anterior es < 0,8/255), **cortes/min** y **ocupación** (% del cuadro con papel). Medido sobre los archivos finales: eps. 03/04/06 dan **53-63 % de cuadros congelados** y movimiento mediano **0,55-0,74**/255, con los cortes en verde (10,5-11,8/min, la meta se cumple). Referencia externa con la misma vara (100 s de RealLifeLore): **10,3 % de quietos y movimiento 7,18** — doce veces más. Y el contraste interno que lo cierra: **los shorts del mismo motor ocupan 85-94 % del cuadro contra 34 % de los largos**, porque el vertical obliga a cerrar el plano. **La raíz es un error de fórmula, no falta de mecanismo**: `cut(t, name, push=0.05)` reparte el zoom en TODO el plano, así que cuanto más largo el plano más lenta la cámara (ep. 06: 6,58 de movimiento en los tramos de planos de 2,3 s contra **0,58** en uno de 30 s). El motor **ya tiene** idle de cabeza y brazos (±1,4°/±1,6°), respiración (±1,2 %) y parallax (`Scene.offset`, `depth=1.06`): están calibrados 3-5× por debajo de lo perceptible (1,5 px en pantalla = 0,3 px en un teléfono) y el parallax solo actúa si la cámara se mueve. Plan aprobado por Agustín para el **próximo** episodio (no el 09, que estaba renderizando): `canal/PLAN_PASADA_DE_VIDA.md` — push por velocidad (%/s con tope), idle ×3, wobble en props y tarjetas, `depth` a props, cerrar ventanas a ≥ 55 % de ocupación, tarjetas legibles a 405 px de ancho, usar el rojo, y `ritmo.py` en el checklist. Diagnóstico completo con las pruebas visuales en `canal/POR_QUE_SON_SOSOS_2026-09-15.md` y `pruebas/ritmo/`. Además: **`yt-dlp` estaba roto** (versión de marzo → YouTube devolvía 403 y el scraper de fuentes iba a caer): actualizado a 2026.08.19, instalado `curl-cffi` para impersonación y creado `%APPDATA%\yt-dlp\config.txt` con `--js-runtimes node` para que no falten formatos. Trampa de trabajo: **antes de tocar `motor.py` o una coreografía hay que contar procesos `python`** — el pool levanta ~22 y editar el módulo a mitad de render mezcla código viejo y nuevo.
  - v1.10.0 (2026-09-15): **paso 0 — ningún tema entra en producción sin validar la demanda** (reglas 26-28 y §2.0, herramienta `produccion/demanda.py`). Nace de analizar dos videos que pasó Agustín (el de ViewStats de MrBeast y una clase abierta de Máximo Bruno) y de comprobar lo que dicen contra las políticas de YouTube. Lo verificado: desde el **1-feb-2027** entrar al YPP pide **8.000 horas** (hoy 4.000) o 20 M de vistas de Shorts, el que ya está dentro no se ve afectado, y **el tiempo de reproducción de Shorts NO cuenta** para las horas — once series de shorts no acercaron el canal ni un segundo (`canal/MONETIZACION_2027.md`). Desmentido: no existe ningún umbral de 30 s ("vista con intención") para los largos. Lo que **no** hay que cambiar: la intro/outro fijas y la franquicia repetida están permitidas por escrito, y el pipeline no cae en *inauthentic content* (cortes de duración variable, arte y guion propios). El hallazgo del paso 0: lo que separa nuestros aciertos de nuestros fracasos no es la demanda sino **de quién es el tema** — donde el video más visto lo firma un creador funcionamos (478 · 278 · 250), donde lo firma un medio no (4 vistas con la ola abierta y caliente). La herramienta acierta en los cuatro casos conocidos. Límite conocido: el veredicto **depende de la frase**, hay que probar 2-3. La regla 5 se reescribió: la cadencia quincenal llevaba una semana siendo falsa.
  - v1.9.3 (2026-09-13, noche): **dos decisiones de Agustín para los videos futuros**: (1) *"Los prefijos, si considerás que son contraproducentes, quitalos"* → los títulos van **sin `PALABRA-EMOCIÓN:`** (la emoción dentro de la frase; `canal/CANAL.md` §7.1 es la única fuente); (2) *"Los que ya están subidos dejalos como están. Lo mismo con las miniaturas. No sigas cambiando"* → lo publicado hasta hoy no se toca. Con su permiso explícito se aplicó en Studio lo que está en `canal/STUDIO_ARREGLOS_2026-09-13.md` (descripción y palabras clave del canal, ep. 05 completo, ep. 06 correcciones, ep. 01 etiquetas, 11 de 12 shorts del 11-S con video relacionado) y el resto quedó como referencia. Método nuevo en §2.10c: miniatura del episodio con `canal/miniaturas_v2.py` y verificación de lo publicado con `yt-dlp`. Trampas de Studio aprendidas: los botones de diálogo (Continuar/Detener) responden a coordenadas o a Return, no al clic por referencia; el cuadro de descripción **autocompleta hashtags** y pega el sugerido si el hashtag queda último (dejar los hashtags antes de la última línea y con un espacio final); el selector de "video relacionado" se elige con clic por coordenadas o clic + espacio; el `Guardar` por referencia falla si el selector quedó abierto; el ancho real del cuadro cambia entre capturas (usar el factor de la última captura).
  - v1.9.2 (2026-09-13, tarde): **"arregla todo, nada de a medias"**. Hecho en el repo: `guiones/checklist.py` gana tres chequeos que salen de planes ya escritos (juicios de valor en voz, `IDEOLOGIA.md` §3; cifras en voz sin respaldo en la hoja, `--ref hoja1,hoja2`, regla 7 vigente; conteo de muletillas sin límite) y mira el CLOSE y no el NEXT para la regla 20; **miniaturas candidatas** para los eps. 01-05 (`canal/miniaturas_v2.py`, 0 cr: cara del protagonista real + mapa con la zona en rojo + 2-3 palabras, sin sello) como propuesta, no regla; la **retención se leyó por código** desde el SVG de Studio (`ANALISIS_ITERACION` §1.3.b): el segundo 30 aguanta (67-82 %), la pérdida está entre el minuto 1 y el 4, y en el ep. 04 cae sobre la intro general. En YouTube: **solo pasaron las etiquetas del ep. 01**; el clasificador de permisos del entorno bloquea cambiar títulos, descripciones y cerrar pruebas A/B desde el asistente, así que `canal/STUDIO_ARREGLOS_2026-09-13.md` queda como ficha para Agustín (o para habilitar el permiso). Descubierto: los 12 shorts del 11-S no tienen video relacionado. Trampas: `form_input` no sirve en los cuadros de Studio (son DIV editables) y las capturas de pantalla congelan el renderer de Studio; leer con `find`/`get_page_text` y JS de solo lectura.
  - v1.9.1 (2026-09-13): **reconciliación de reglas después del análisis de iteración** (`canal/ANALISIS_ITERACION_2026-09-13.md`), con la premisa de Agustín: *"No te inventes reglas que no te he dicho yo"*. Sin reglas nuevas. Lo que cambió: (1) el handle real del canal es **`@papertrailgeo`** (la skill, `CANAL.md` y la memoria decían `@papertrail`; el ep. 05 lo muestra mal en una tarjeta, `coreo.py` ya corregido para renders futuros); (2) la regla 7 quedó vieja: desde el 9-sep Agustín pide verificar los datos y desde el ep. 06 fuentes primarias con `Fn`; (3) la regla 12 concentra las cuatro instrucciones suyas sobre opinión ajena; (4) las reglas 15 y 16 estaban en orden invertido; (5) títulos: `canal/CANAL.md` §7 es la única fuente y `SHORTS.md`/`FORMATOS.md`/§2.2 remiten ahí; vale la última decisión suya (11-sep: cifra o fecha adelante, hashtags, ≤ 100), y lo que era propuesta del asistente (~70 caracteres, cifra en uno solo, sin fechas) quedó marcado como propuesta; (6) `CALENDARIO.md` está obsoleto (los temas los elige él, regla 13); (7) `ESTILO.md` lleva una tabla de vigencia con lo derogado, y su §5.7 sobre la música de PicsArt se verificó y corrigió; (8) el presentador B del diario deja de llamarse "El analista" (`ESTILO.md` §5.1, riesgo del bucket de "expertos de IA", regla 14 de Agustín); (9) las hojas de fuentes de S02, ep. 06, Malvinas, 11-S y S03 llevan sección de **erratas y cortes no declarados**; (10) `guiones/checklist.py` avisa si las últimas líneas abren con "So" (regla 23) y si falta el pedido de comentario (regla 20). Los cambios en YouTube Studio están en `canal/STUDIO_ARREGLOS_2026-09-13.md` y los hace Agustín o el asistente con su Chrome, según decida él.
  - 2026-09-11 (ep. 06, segunda vuelta): Agustin rechazo la animacion ("muy mala, mete personitas y
    cosas moviendose"). La causa: el motor ya traia gesture/point/hold/walk/slam y el primer corte no
    los usaba. Regla nueva: una persona y una cosa moviendose en cada beat. Y se hizo la intro propia
    del episodio, que faltaba (timestamps:True en fal, adelay del audio, la hoja sangra).
  - 2026-09-11 (ep. 06, IA en economia y politica): dos bugs de alineacion (el cache de whisper ya
    esta en la linea de tiempo final, y anclar por primer/ultimo token colapsa el final de cada beat);
    el mapa se revela solo en planos de mapa; nada nace dentro de un bloque de acto; los cuadros de
    aprobacion tienen que salir de sc.render(); fuentes primarias con Fn obligatorio.
  - v1.9.0 (2026-09-11): **intro y outro del canal rehechas (v2)**, pedido de Agustin: *"tienen que incentivar a suscribirse y a darle likes"* + *"mas emotivas y altisima calidad"*. Tres fallas concretas de la v1 y como se arreglan, validas para cualquier pieza: (1) **la hoja tiene que llenar el cuadro** — la v1 dejaba un tercio de madera vacia a la derecha y dos franjas de pared; es la misma leccion del ep. 05, y ahora la hoja del mundo va a `SHEET_S = 1.36` y sangra por los cuatro lados. (2) **Sin luz no hay jerarquia**: `props_canal.luz()` arma charco calido + vineta en UNA capa RGBA (premultiplicada y dividida por el alfa final, sin bandas), y va sobre la clase **`Overlay`** de `intro_outro.py`, que **reescala la capa a la ventana de camara en cada cuadro** — si se pone como Obj normal, al hacer zoom la vineta queda descentrada y se ve una esquina oscura flotando. Tres ajustes utiles: `r` chico = viñeta mas cerrada, `vin` = cuanto oscurece el borde, `a` = cuanto ilumina el centro; probarlos en una hoja de 4 variantes ANTES de renderizar. (3) **Una secuencia de tarjetas no es un relato**: cada pieza tiene arco (la intro va de tres expedientes que caen → la mesa entera del mundo → UNO bajo el foco → el sello; la outro, de cerrar el archivo → pedir el like CON EL MOTIVO → la suscripcion → la firma). Nuevo y reusable: **`produccion/props_canal.py`** (`pulgar()` el me-gusta como recorte de papel — no el icono de YouTube pegado encima —, `documento()` expediente con banda/renglones/sello/firma, `luz()`, `sombra_pie()` — sin sombra de contacto el rig FLOTA sobre la hoja —, `clip()`, `mancha()`); **coreografia anclada a la voz** por los timestamps por caracter de ElevenLabs (`_voz()` busca la frase en el texto y devuelve su segundo: si se regenera la voz, todo se reacomoda solo y el script aborta si la frase no aparece); **`_mezcla(..., swell=[(t,ganancia)])`** para que la cortina respire en vez de ser una alfombra plana, y `mus_off` para que la outro no arranque la misma pista que la intro; y **`intro_outro.py check`** (encuadre + ritmo + hoja de contacto de cuadros reales, sin renderizar). Trampas nuevas: un sello dibujado sobre un lienzo del tamaño de la caja **se corta a si mismo** si el texto es mas ancho (hay que medir el texto primero); `Rig.point(t,'L')` saca el brazo POR EL BORDE IZQUIERDO (los carteles estaban a su derecha: era `'R'`); y el `report` de huecos marca los silencios del guion — los 3 s que la voz calla se llenan con movimiento CON SENTIDO (los expedientes convergen sobre el elegido; entra el expediente del proximo), no con relleno. Duraciones: intro 8,2 s → **13,96 s**, outro 15 s → **19,79 s** (la cola larga es la ventana de pantalla final). Voz nueva: USD 0,07 en total (tres tomas).
  - v1.8.0 (2026-09-09): **primer Dispatch producido dentro de `videos/<NN>_<tema>/`** (ep. 05, 11-S por el 25 aniversario) y seis lecciones de coreografia que valen para todos los episodios. (1) **Mirar cuadros del RENDER, no la previsualizacion**: la hoja de contacto de `check` enganya; hubo que cortar el render al 16 % porque la hoja de mapa era chica en el cuadro. La hoja tiene que llenar el ancho (`MAP_S = 1920/ancho_hoja`) y el plano `MAPW` tiene que contenerla entera. (2) **`win()` devuelve la ventana al FINAL del push-in**, no la del primer cuadro. (3) **La pasada de ritmo tiene que mirar solo los cortes del guion** (`CUTS0`), no los que ella misma inserta, o el corte de vuelta aterriza en un plano abandonado (era el 70 % de los cortados). (4) **`SUP` es siempre el plano que CONTIENE al cerrado**; probar `'WIDE': 'MAPW'` dejo 113 objetos a medias. (5) **Pasada anti-pantalla-vacia**: el chequeo de huecos cuenta eventos (sonidos), no lo que se ve; midiendo lo visible aparecio que el 9,7 % del episodio era solo mapa. Se parte cada tramo por los cortes y se rellena con la etiqueta de la region (informa) o estirando la ultima tarjeta. Bajo al 6,5 %. (6) **`M.EVENTS.clear()` al empezar `build()`**: el pool reusa procesos y sin eso los cortes salen distintos entre tramos. Ademas: **la alineacion no puede emparejar palabras por cantidad** (el guion escribe los numeros con letras y whisper los pone en digitos; el desfase llego a 34 s), se empareja por texto con `difflib` y las palabras de whisper se cachean; **el post-pass puede apagar al protagonista** (borro a bin Laden en mitad del cierre), hay que revisar la lista de apagados; y las **rutas de musica van absolutas** en `eventos.json`. Herramientas nuevas reutilizables: `_tiempos_falso.py` (probar la coreografia sin esperar a whisper), `_arreglar_tiempos.py` y `_checklist_monetizacion.py`. El indice de assets ahora tambien recorre `videos/*/arte/assets/` (de 323 a 431 assets): antes, los props dibujados por codigo dentro de una produccion no se encontraban y se volvian a dibujar. **Y un fallo de motor que afectaba a todos los videos**: `Track` nace con un keyframe propio en t=0 y corta con `if t <= k[0][0]`, asi que **en el instante 0 gana siempre su valor inicial** y ningun keyframe puede fijar el primer cuadro; el video abria con la hoja sin revelar y la camara en plano general. Se arregla inicializando los Track (`mp.reveal = M.Track(1.0)`, y `sc.cx/cy/zoom` con el primer plano al empezar `finalize_cam`).
  - v1.5.0 (2026-09-08): **shorts redefinidos + una producción por directorio** (reglas 17 y 18, pedido de Agustín). Los shorts se hacen junto al video principal **y/o solos**, según cómo arranque la conversación; con episodio son **3-5 con guion exclusivo** (no 10 recortes) reusando **el arte** del largo — no el metraje —, de **50 s mínimo** y sin tope fijo (el máximo lo decide el tema, hasta los 3 min de Shorts); solos se producen como un video principal en formato short; y existen las **series** (un tema, una subtemática por pieza; ejemplo de Agustín: 11-S). Método en `canal/SHORTS.md` (reescrito), estructura de carpetas en `canal/ESTRUCTURA.md` (`videos/<NN>_<tema>/`, `videos/S<NN>_<tema>/`). Los shorts **dejan de costar 0** (voz propia, ≈USD 0,46 por 4 piezas de 90 s) y por eso Agustín **subió el tope de la regla 15 de USD 3 a USD 4 por producción** (episodio + shorts, un solo tope). Decidió también: **outro corta pidiendo suscripción** en cada pieza, sin intro de canal (excepción a la regla 4), y **duración mínima 50 s con el máximo por tema**. Señalado y no resuelto: de 10 a 3-5 se corta a la mitad la cobertura del calendario, y el dato propio dice que lo que rinde son 31-59 s. Bloqueante técnico a resolver: `motor.py:427` borra `produccion/_frames` al arrancar, así que hoy no se puede renderizar el largo y sus shorts a la vez.
  - v1.7.0 (2026-09-10): **la serie del 11-S producida entera** (`videos/S01_11s/`, 12 piezas). Herramientas nuevas y reutilizables para cualquier serie o short suelto: `coreo.py` (motor de coreografia de la serie: planos WIDE/MAPW/CORR/NYC/DC/BOS/ATL/GAN/WALL/CTR, **encaje automatico** que achica y recentra todo lo que no entra en la ventana -- la regla 1 pasa a cumplirse por construccion --, **pase de ritmo** que vuelve a cortar al mismo plano donde el guion deja mas de 5,5 s sin nada, y **post-pass de corte** que apaga lo que quedaria parcialmente visible en el plano nuevo), `escenas.py` (una partitura por pieza, tuplas ancladas a lineas del guion), `voz_serie.py` (dirigir/generar/alinear las N piezas), `armar.py` (lienzo vertical + sello PART n OF N + outro SUBSCRIBE + **cortina propia**) y `publicar.py` (PUBLICAR.md + PLAN_SUBIDA.json + copias `_up/`). **`motor.render(..., frames=<dir>)`**: cada produccion usa su propio `_frames`, asi que **ya se puede renderizar el largo y sus shorts a la vez** (era el bloqueante de `ESTRUCTURA.md` §4.1). Trampas nuevas: whisper devuelve 0.0 para la primera palabra y un keyframe en t=0 choca con el del motor (flash en 0,0) -- anclar a PRE; un tiempo negativo en un corte rompe la interpolacion de camara; el `pop` entra con `back` y se pasa ~12 % del tamano final, hay que descontarlo al encajar; y **verificar que las fuentes que pasa Agustin sean del tema** (de los 4 videos del 11-S, uno era del 11-M de Madrid).
  - v1.6.0 (2026-09-09): **primera serie de shorts (tipo B) y la regla de que no se censuran palabras**. Serie del 11-S en `videos/S01_11s/` (10 piezas: arquitectos, bin Laden, los hechos desde el suelo, una por cada uno de los cuatro vuelos, la no-respuesta militar, consecuencias geopoliticas, vida cotidiana); el interrogatorio y las fuentes se hicieron **una vez para la serie** y cada pieza cierra abriendo la siguiente. **Comprobado en el reglamento de YouTube** (`canal/MONETIZACION.md` §1.b nuevo): no hay lista de palabras prohibidas, un reportaje educativo sobre un atentado esta en **ads allowed** por escrito, y el bip pertenece a la regla de groserias, asi que censurar "terrorismo" resta (rompe el registro educativo, y la ofuscacion deliberada esta penalizada). La vuelta cuando se quiere el gesto: **sello de papel** sobre el subtitulo, audio limpio. Aprendido tambien: el scraper cae en `IpBlocked` seguido, el camino corto es yt-dlp `--write-auto-sub` + `vtt2md.py` **corriendo desde `fuentes/`** (el script escribe en `yt/` relativo al cwd); y **hay que verificar que la fuente que pasa Agustin sea del tema**: de los 4 videos del 11-S, uno era del 11-M de Madrid.
  - v1.5.1 (2026-09-08): **índice de assets** (regla 19, pedido de Agustín: reusar antes de generar para no gastar créditos al pedo). `produccion/indice_assets.py` recorre el repo y escribe `canal/INDICE_ASSETS.md` + `assets_indice.json`; metadatos en `canal/assets_catalogo.json` y en fichas `.json` al lado del archivo (modelo `produccion/hero/hangar.json`); `indice_assets.py buscar <termino>` es el paso obligatorio antes de cualquier generación. Catálogo actual: 318 assets, **49 créditos** ya pagados (11 rigs, 7 cues, 3 sets, 1 hero, 253 props, 4 hojas de mapa). Criterios en `canal/ASSETS.md`. Y aclaración de Agustín sobre la regla 15: **el tope de USD 4 es un techo, no un presupuesto para agotar**.
  - v1.4.2 (2026-09-08): **intro propia por video** (regla 4 ampliada, pedido de Agustín): preguntas cortas + "stay to the end" antes de la intro general; `produccion/intro03.py` como plantilla, voz con timestamps por fal (`voz/voz_fal_ts.py`), armado final `_final03.sh` (4 entradas). Ep. 3 final: `03_kiev_belarus_final.mp4`, 16:00.
  - v1.4.1 (2026-09-08): **ep. 3 producido en un día** (reportaje 15 min, Kiev/Bielorrusia). Nuevo: `fuentes/vtt2md.py` convierte el VTT de yt-dlp al formato de `fuentes/yt/` (la API de transcripciones sigue `IpBlocked`; yt-dlp necesita `--js-runtimes node`); `voz/voz_fal.py <dir> <beats…>` genera beats con George por fal.ai (`fal-ai/elevenlabs/tts/eleven-v3`, `voice` = ID, ~$0,10 por 1.000 chars) leyendo `FAL_KEY` de la variable de usuario vía un `.ps1` (el MCP `fal` da 401 hasta reiniciar la app). Decisiones de Agustín: **formato y duración los decide él** (no proponer Brief por créditos); **en voz se citan las fuentes de origen (The Economist, WSJ, Syrskyi), nunca los canales de YouTube**. Rig nuevo `13_lukashenko`. Hoja `mapa_kiev.py` → `assets/mapa03_*` con capas (Bielorrusia, Donbás, ejes, franja de drones). 104 props en `props03.py`. Coreografía `ep03.py` (agente): helpers nuevos reutilizables `insertos()` (cortes automáticos cerrado→contenedor→cerrado en frases largas para llegar a ≥10 cortes/min), `whip()` con tránsito y post-pass, `card()` con `clamp()` al plano, `stamp()` que calcula la escala para no salirse; planos a z 3–3,8 (a z≥4 el texto se ve borroso); `foto_manos()` compone dos rigs en un marco; segunda hoja de mapa en el mismo episodio (beat NEXT). Check: 0 cortados, 10,4 cortes/min, 0 huecos.
  - v1.4.0 (2026-09-08): **dos formatos** (pedido de Agustín): REPORTAJE / *Dispatch* (10-17 min, 11 beats, hoja propia, 2 hero, 8-10 shorts, jueves quincenal) y NOTICIA / *Brief* (4-7 min, 5 beats, ≤72 h del hecho, 4-6 shorts, se publica cuando ocurre; **misma calidad y mismos chequeos** que el reportaje). Tabla completa en `canal/FORMATOS.md`. El formato es la pregunta 0 del interrogatorio y va en la primera línea del guion.
  - v1.3.4 (2026-09-08): **cold open antes de la intro**: `entregar.py --intro_at S` inserta la intro del canal en el segundo S del cuerpo (fin del cold open); `voz/alinear.py` pre-roll 1 s (antes 8). Verificado con un cuerpo de prueba (12+8+15 = 35 s). Sin `--intro_at` se reproduce el orden viejo (eps. 1 y 2).
  - v1.3.3 (2026-09-08): **motor v3** (`produccion/motor.py`): física de papel (`drop`, `flipin`, `slide_off`, `crumple`, `raise_`/`settle`), sombra dura por objeto y rig, `sy`, `lift`, `depth` con paralaje, `Scene.shake`/`whip`, `Rig.point_at(xy)`/`shrug`/`hop`/`lean`, bob al caminar, `Scene.report()` (huecos > 6 s y cortes/min, impreso por `check`). Test hero validado: cuadro plano con Flux (referencia = rig) + Kling V2.6 i2v 10 cr, ficha en `produccion/hero/hangar.json`; el prompt de i2v debe pedir UNA acción. Sets y hojas de expresión en `assets/sets/` y `pruebas/elenco/expresiones/`.
  - v1.3.2 (2026-09-08): regla 15, tope inquebrantable de USD 3 por video en fal.ai. OK de Agustín al plan de `canal/CREATIVO.md` (motor nivel 0 + test hero de ~25 cr antes del 14/09).
  - v1.3.1 (2026-09-08): **regla 14, monetización**: `canal/MONETIZACION.md` lista las zonas de riesgo (odio por grupo, extremismo, eventos sensibles, temas controvertidos, desinformación electoral, títulos incendiarios, contenido sintético) y la vuelta de cada una; pregunta 6 del interrogatorio de postura y checklist §3 antes de subir.
  - v1.3.0 (2026-09-08): **regla 13, ideología**: Agustín definió su perfil en `canal/IDEOLOGIA.md` (liberal, atlantista, China rival con cosas buenas, inmigración controlada, simpatía Milei/Trump/Bukele/Meloni, pro Israel con crítica, juicio en voz solo ante agresión/dictadura clara o a pedido). **Antes de cada guion, siempre, interrogatorio cerrado de 3-5 preguntas** → `guiones/<ep>/postura.md`. Público: internacional anglófono, no LatAm.
  - v1.2.3 (2026-09-08): primer día del ep. 1 medido (`canal/ANALISIS_DIA1_EP01.md`): CTR 1,2 %, promedio 2:18, shorts 8-14 % de vistas interesadas. Errores nuevos en §3: intro antes del cold open (16 s sin voz); lugares del guion puestos por fracción del plano en vez de `G()`; región pintada del color del agua; 1 corte cada 11,7 s. Pendientes en §4: `place()` + lint de lugares + cortes/min en `check`, cold open antes de la intro con `entregar.py --head`, planos hero generativos.
  - v1.2.2 (2026-09-08): el paso de subida de los shorts sale a su propia skill, `youtube-shorts-upload` (§2.10 la referencia). `shorts.py` gana `--plan` para resolver archivos, textos, fechas y horas antes de tocar el navegador.
  - v1.2.1 (2026-09-08): títulos y ganchos de shorts **más sensacionalistas** (pedido de Agustín), con el límite de no inventar hechos ni opinar (§2.2). Miniaturas del ep. 2 con `marca.miniatura(pers='12_weidel.png', mapa=<hoja compuesta>)`. Shorts delegados a un agente Opus 5 para no gastar uso de Fable: funcionó en ~12 min con `shorts.py` sin cambios.
  - v1.2.0 (2026-09-07): **ep. 2 (AfD) producido con el pipeline generalizado a otro país/tema**: mapa por episodio (`mapa_alemania.py` → `assets/mapa02_*`, `MapSheet(base=,pts=)`), props por episodio (`props02.py`), dirección de voz por episodio (`guiones/<ep>/direccion.py` + `voz/dirigir.py --out`), rig nuevo (Weidel) con el mismo cortador, coreografía `ep02.py`. Regla nueva de Agustín (§0.12): cuando el video se basa en videos ajenos, se **mantiene la opinión de las fuentes y no se agrega opinión propia**. Precio real medido de la voz: ~3,4 cr por 1.000 caracteres (con tags). Transcripción bloqueada por IP → `yt-dlp --write-auto-sub` (§2.1).
  - v1.1.0 (2026-09-07): agregado el paso de **shorts** (§2.10). Agustín: "por cada video que hagamos haremos esto". 8-10 verticales por episodio, 0 créditos, cortados del master con `produccion/shorts.py` a partir de `guiones/<ep>/shorts.json`; estrategia y método en `canal/SHORTS.md`.
  - v1.0.0 (2026-09-07): primera versión, destilada de la producción del ep. 1 ("How Do You Ground a Superpower Without Firing a Shot?", v6). Cubre guion, voz, alineación, coreografía por planos, chequeo de encuadre, mezcla, render, intro/outro y entrega.
description: >
  Cómo producimos un episodio del canal Paper Trail (geopolítica animada en papel recortado, inglés, 15-17 min,
  quincenal) de punta a punta y a costo casi cero de créditos. Usar esta skill siempre que Agustín pida hacer,
  rehacer, corregir o iterar un video del canal, un episodio nuevo, "el piloto", la voz, la coreografía, el render,
  la mezcla, la intro/outro, los shorts verticales o la entrega. También cuando diga "hazlo como el ep. 1", "sigue el pipeline" o
  "mejorá el video". Todo vive en C:\Users\agust\Desktop\agustin\canal_geopolitica. Esta skill se va mejorando:
  cada iteración con feedback de Agustín agrega una entrada al changelog y, si cambia el método, al texto.
---

# Paper Trail · cómo hacemos un video

Proyecto: `C:\Users\agust\Desktop\agustin\canal_geopolitica`. Punto de entrada al retomar: `RETOMAR.md`.
Canal: **Paper Trail**, handle **`@papertrailgeo`** (el que quedó registrado; comprobado el 2026-09-13), tagline *Follow the paper.* (decisión de Agustín 2026-09-07).
Idioma del video: inglés. Idioma con Agustín: español, respuestas cortas, el detalle va a documentos.

## 0. Reglas de Agustín (no negociables; las propuestas del asistente NO son reglas suyas)

1. **Nada cortado por el borde del cuadro. Nunca.** Se verifica por código antes de renderizar (§6).
2. **Sitios reales en el mapa**: todo lo que se apoya en el mapa se ancla a coordenadas reales con etiqueta.
3. **Movimientos fluidos** (easing suave, sin saltos) y **siempre hay algo moviéndose** en pantalla.
4. **Intro del canal al principio y outro al final, en todos los videos.** **(2026-09-11) Las dos piden LIKE y SUSCRIPCION**
   (*"tienen que incentivar a suscribirse y a darle likes"*) y se rehicieron para que sean emotivas: v2 en `canal/INTRO_OUTRO.md`.** **(2026-09-08) Y antes de la intro general, una intro propia
   del episodio: preguntas bien cortas como gancho + "stay with this video until the end and check the answers for yourself"**
   (`canal/INTRO_OUTRO.md`; plantilla `produccion/intro03.py`). Orden: preguntas → intro general → episodio entero (con cold open) → outro.
4.b **Intro v3 (Agustín, 2026-09-15): `produccion/intro_v3/intro_canal_v3.mp4` es la vigente.**
   Mapa de papel → el archivo con los documentos → el sello `PAPER TRAIL` sobre un memorándum
   censurado con `LIKE` y `SUBSCRIBE`. Dura **12,5 s** (la v2 duraba 13,96). `produccion/entregar.py`
   la toma por defecto desde el 15-sep y acepta `--intro <ruta>` para reproducir entregas viejas.
   La outro sigue siendo `produccion/outro_canal.mp4` (11-sep), 20 s.
5. **Duración y cadencia (reescrita el 2026-09-15; antes decía "cadencia quincenal", que llevaba una semana
   siendo falsa).** La **duración** la manda el formato (`canal/FORMATOS.md`): Dispatch 15-17 min de cuerpo,
   mínimo **15:30**; Brief 4-7 min. La **cadencia la fija Agustín**, con dos límites que no son opinión:
   **(a) nunca dos largos el mismo día** — el 14-sep se subieron tres y el reparto fue 78 / 4 / 3 vistas,
   contra 77-478 los días de a uno; **(b) hasta el 31-ene-2027 lo que cuenta son horas de visualización, y las
   horas **solo las dan los largos** — el tiempo de reproducción de Shorts está excluido por escrito
   (`canal/MONETIZACION_2027.md`).
6. El relato tiene que enganchar: dramático, con emoción, humor seco, ganchos al final de cada acto. "El video LO TIENE
   QUE QUERER VER LA GENTE, no puede ser feo ni aburrido."
7. Fuentes, en el orden en que Agustín lo fue diciendo (vale lo último): **3-sep**: youtubers de reputación vía el scraper,
   sin verificar contra fuentes primarias. **9-sep** (`feedback-video-es-insumo`): *"verificar los datos igual, eso sí lo quiere"*.
   **11-sep** (ep. 06): *"Revisa muy bien las fuentes, busca fuentes nuevas de ser necesario… NO TE INVENTES NADA"* → la hoja de
   referencia numera cada dato `F0…Fn` con su URL y nada entra al guion sin su `Fn` (§3, lección 11 del ep. 06). **Hoy rige esto
   último**: los videos de YouTube son insumo; los datos se verifican; lo que no tiene fuente no se dice o se declara en
   "lo que el guion NO dice". (Hasta el 13-sep esta regla decía solo lo del 3-sep y por eso los guiones del 9 al 12 tenían
   ~12 afirmaciones sin fuente: `canal/ANALISIS_ITERACION_2026-09-13.md` §4.2.)
8. Líderes reales como caricaturas de papel (Trump, Putin, Zelensky) están permitidos y son parte del atractivo.
9. Música sin derechos de terceros (cues propias con Lyria vía PicsArt), nada de pistas que exijan crédito.
10. Mostrar cuadros fijos antes que animación cuando se cambia el look; mirar frames reales del render antes de entregar.
11. Presupuesto: 500 créditos PicsArt por ciclo (reset el día 14). Un episodio cuesta ~90 cr (voz). Todo lo demás es
    0 créditos (render local).
12. **Cuando el episodio se basa en videos de otros (Rallo, Memorias de Pez, Fonseca…), el guion MANTIENE la opinión de
    esos videos y no agrega la opinión del asistente** (pedido literal, 2026-09-07: "NO MODIFIQUES LA OPINIÓN. NO DES TU
    OPINIÓN"). Si las fuentes opinan distinto, van las dos, atribuidas ("our economist", "the other analyst"); lo que el
    guion no dice porque no está en las fuentes se lista en `fuentes/<tema>_referencia.md` §"Lo que el guion NO dice".
    **Las cuatro instrucciones suyas sobre opinión ajena, juntas (2026-09-13, sin agregar ninguna):** (a) 7-sep, la de arriba:
    episodio construido sobre videos ajenos → su opinión se mantiene y se atribuye; (b) 8-sep, `IDEOLOGIA.md` §2 pregunta 3: en
    el interrogatorio se le pregunta si se mantiene tal cual o se filtra por su perfil; (c) 9-sep, `feedback-video-es-insumo`:
    un video que pasa es insumo para sacar información, *"si tiene información que va contra nuestra opinión lo ajustamos"*;
    (d) 11-sep, S02: *"la conclusión de él TAL CUAL, pero la ponemos como nuestra. NO NOMBRAR A RALLO… porque la conclusión
    de él es exactamente igual que la nuestra"*. En la práctica: **lo que no compartimos se atribuye; lo que coincide con la
    postura del canal puede ir como propio y sin nombrar si él lo decide; lo que contradice, se ajusta y se le dice**. Y lo que
    una fuente opina y se deja fuera va **declarado** en "lo que el guion NO dice" (en Malvinas no se hizo con Carajo).
13. **Ideología y postura (2026-09-08)**: el canal es neutro por defecto; el perfil de Agustín está en `canal/IDEOLOGIA.md` §1 y
    **antes de cada guion, siempre, se le hace el interrogatorio de §2** (3-5 preguntas cerradas) y se guarda `guiones/<ep>/postura.md`.
    La voz solo concluye ante agresión o dictadura clara o cuando él lo pidió; temas culturales, aborto y género: preguntar siempre.
    Público objetivo: internacional de habla inglesa, no Latinoamérica. **Los temas los elige Agustín** a partir de videos de YouTube.
    Islam: postura en `IDEOLOGIA.md` §1; en voz se nombra islam político y actores concretos, nunca a los musulmanes como grupo.
14. **Monetización (2026-09-08)**: todo lo que pueda comprometer anuncios o el canal tiene que estar MUY claro y se le da una vuelta
    sin perder el rumbo: cambiar el sujeto (islam → islamismo, migrantes → política migratoria de X, Rusia → el Kremlin), atribuir,
    nombrar actores concretos. Zonas y vueltas en `canal/MONETIZACION.md`; pregunta 6 del interrogatorio; checklist §3 antes de subir.
    Si no hay vuelta, se le dice el costo a Agustín y decide él.
15. **REGLA INQUEBRANTABLE (solo Agustín la cambia): gasto máximo en fal.ai = USD 4 por PRODUCCIÓN** — el episodio
    **y sus shorts** juntos, un solo tope (≈138 cr PicsArt). Eran USD 3 por video; **él lo subió a 4 el 2026-09-08**
    al darle guion y voz propios a los shorts. Reparto en `COSTOS.md` (voz del episodio $1,74 + imágenes $0,30 +
    2 hero con un reintento + voz de los shorts $0,46-1,15). Antes de pasar el tope, preguntar.
    **Es un TECHO, no un presupuesto** (Agustín, 2026-09-08, literal: *"QUE EL TOPE SEA 4 USD NO SIGNIFICA QUE PUEDAS
    GASTARLO ASÍ LIBREMENTE AL TOPE"*). Lo normal es gastar mucho menos; si la producción no necesita nada nuevo,
    gasta 0 en assets. Que quede margen no es motivo para usarlo.
16. **Formatos (2026-09-08)**: cada video es `reportaje` (Dispatch) o `noticia` (Brief); tabla de diferencias en `canal/FORMATOS.md`.
    Es la pregunta 0 del interrogatorio; una noticia sale en ≤ 72 h del hecho, con 5 beats. **Misma calidad que el reportaje**
    (Agustín: "ambos son importantes que estén muy bien hechos, las noticias obtendrán suscriptores también"): mismos chequeos,
    misma precisión de mapa, hero y rigs nuevos si el hecho lo pide; solo cambian el largo y la urgencia.
17. **Shorts, redefinido (2026-09-08)**: se hacen **junto al video principal y/o solos**, y lo define **cómo arranca
    la conversación**. Con episodio: **las mismas imágenes** del largo (el arte: props, mapa, rigs, hero — no el
    metraje), **guion exclusivo** (no un recorte) y **3-5 piezas MUY bien armadas** en vez de 10, de **50 s mínimo**
    y sin tope fijo: **el máximo lo decide el tema** (techo de Shorts, 3 min). Sin intro del canal y con una **outro
    corta que pida la suscripción** (excepción a la regla 4 aprobada por él). Solos: se producen **igual que el video principal pero en
    formato short**, generando y preparando todo. También **series**: un tema con varias subtemáticas, una pieza por
    subtema, todas de la misma serie (ejemplo de Agustín: 11-S → los hechos · cómo se planeó · el origen · las
    consecuencias en la vida cotidiana). Método completo en `canal/SHORTS.md`.
18. **Una producción, un directorio (2026-09-08, literal)**: *"Es muy importante que cada producción final tenga su
    directorio… TODO LO REFERENTE A UN VIDEO ESTARÁ EN SU DIRECTORIO."* `videos/<NN>_<tema>/` para episodio + shorts,
    `videos/S<NN>_<tema>/` para serie o short suelto. Árbol, qué queda compartido (motor, props base, elenco, música,
    intro/outro) y plan de migración en `canal/ESTRUCTURA.md`. **El ep. 4 no se mueve** mientras haya una sesión
    trabajando en él; sus shorts sí nacen con el modelo nuevo.
19. **Índice de assets, reusar antes de generar (2026-09-08)**: *"es MUY importante armar un index y ordenar bien todos
    los assets que generamos con IA para que si se pueden reutilizar en el futuro, se reutilicen Y NO GASTEMOS CRÉDITOS
    INNECESARIAMENTE"*. **Antes de generar cualquier cosa con IA**: `python produccion/indice_assets.py buscar <lo que
    haga falta>`. Si aparece, se usa. Si no, se genera **y se anota** (ficha `.json` al lado del archivo como
    `produccion/hero/hangar.json`, o entrada en `canal/assets_catalogo.json`) y se regenera el índice. Criterios y
    orden de decisión en `canal/ASSETS.md`; índice vivo en `canal/INDICE_ASSETS.md`.

20. **Comentarios en TODO (Agustín, 2026-09-09)**: *"en todos los shorts y todos los videos de ahora en más hay
    que dejar preguntas o cosas para responder en los comentarios"*. **Lo pide LA VOZ**, no solo una tarjeta
    (Agustín, 2026-09-09): el narrador pregunta y pide el comentario cerca del cierre, y va escrito en el guion como
    una línea `A:` desde el principio, en episodios y en shorts por igual. Además: en la tarjeta final junto al
    SUBSCRIBE, en la última línea de la descripción y en el comentario fijado. La buena pregunta
    divide y se contesta en cinco palabras ("British or Argentine?"), no es "¿qué opinás?". Si la pieza opina,
    la pregunta pide la contraria. Detalle en `canal/CANAL.md` §Pedir comentarios.
21. **Los shorts NO dependen del episodio (Agustín, 2026-09-09)**: pueden salir ANTES como presentación de un
    video futuro, el mismo día, o meses después para revivir uno viejo. Si salen antes, apuntan al canal y se les
    edita el "video relacionado" cuando el episodio exista. Y **cada pieza abre situando el tema en dos frases**:
    en el feed nadie sabe de qué se habla. Detalle en `canal/SHORTS.md`.
22. **Carteles (Agustín, 2026-09-09)**: el recuadro se MIDE con `textbbox`, nunca se estima por cantidad de letras
    (en el ep. 4 se desbordaron 31 de 48), y dos carteles no se pisan salvo que sea a propósito (había 40 pares).
    Los dos chequeos van en `check`, antes de renderizar. Detalle en `ANIMACION.md` §Reglas de cartel.
23. **Arco de un short (Agustín, 2026-09-09)**: inicia, se desarrolla y **cierra**. La última frase cierra la idea;
    la pregunta abierta va después y no siempre con el mismo recurso. Cinco piezas que terminan con "So + pregunta"
    es una fórmula que el espectador aprende y deja de escuchar.
24. **Los puntos del mapa son 100 % precisos (Agustín, 2026-09-09, reclamo)**: *"cuando se señalan puntos en los
    mapas NO SON PRECISOS y te había dicho antes TENÍAN QUE SER 100 % precisos y vuelves a cometer el mismo
    error?"*. Es la regla 2 y **se incumplió tres veces en el ep. 5** sin que ningún chequeo lo viera. Causas y
    arreglo en `ANIMACION.md` §Precisión geográfica: **(a)** `MapSheet.P()` no aplicaba la inclinación de la
    hoja → 22 px de error en pantalla, **en todos los episodios del canal** (corregido en `motor.py`);
    **(b)** lo que representa un recorrido **no puede tener tamaño fijo** — la flecha de "Iraq invades Kuwait"
    se pasaba 53 px y caía sobre Qatar; va con `entre(prop, t, G('A'), G('B'))`, que se escala al largo real;
    **(c)** lo que marca un sitio lleva **tope de tamaño en grados de longitud**: 4-6 una ciudad, 8-12 un país
    (`P(..., grados=5, sitio='Mecca')`). **Obligatorio antes de renderizar:** `check_geo()` corre dentro de
    `coreo.py check` y **aborta el render**; y se mira con los ojos la hoja de `_prueba_geo.py`, que dibuja una
    cruz sobre el sitio real que la voz nombra en cada momento. Si la animación no coincide con la cruz, está mal.
25. **Transición de acto estandarizada (Agustín, 2026-09-09)**: *"pasa del III al IV se ve super rápido.
    deberíamos estandarizar eso... Eso tiene que tener un tiempo, y un 'efecto de sonido' que lo indique. Y si
    tiene un título, se tiene que leer con otra voz."* **Bloque fijo de 4,4 s metido EN EL AUDIO** (la voz
    principal se calla; no es un cartel encima de la narración): golpe (stinger + thump) y sacudón → regla de
    papel que cruza el cuadro → velo que apaga el mapa → cae `ACT N` → **el título lo lee una SEGUNDA VOZ**
    (`21m00Tcm4TlvDq8ikWAM`, ~USD 0,03 los cinco actos) mientras la tarjeta entra girando → ficha `PAPER TRAIL`
    → se levanta el velo y corta al acto. **Igual en los cinco actos y en todos los episodios.** Tabla de tiempos
    en `ANIMACION.md` §Transición de acto; lo arma `voz_ep.py` (`BEATS_ACTO`, `PAUSA_ACTO`, `ACTO_T0`) +
    `coreo.py::acto(num, txt, beat)`. Cambiar la duración **no obliga a repetir whisper**: las palabras
    cacheadas en `audio/_palabras.json` se desplazan por cálculo exacto.
26. **Ningún tema entra en producción sin pasar el paso 0 (Agustín, 2026-09-15).** Se corre
    `python produccion/demanda.py "<frase>" --geo <US|GB>` (Trends con la propiedad **Búsquedas de YouTube**) **antes** de §2.1 y se pega el veredicto en
    `postura.md`. La pregunta que decide no es si el tema es bueno: es **de quién es el tema**. Donde el video
    más visto lo firma un *creador*, nuestro formato tiene sitio; donde lo firma un *medio*, la audiencia va a
    buscar la noticia a Bloomberg y se va. Calibrado contra los ocho largos del canal: acierta en los cuatro
    casos conocidos (AfD 478 · Malvinas 278 · IA 250 · diesel 4). Detalle y límites en §2.0.
27. **La palabra que se busca va adelante, en el título y en la miniatura (Agustín, 2026-09-15).** El término
    exacto por el que la gente busca —el país, la cifra, la comparación— entre las primeras palabras del título,
    y **el mismo término en la miniatura**. Va junto con la regla de la bandera. La lección es de un canal que
    hizo 2,8 M con *Nepal* y se cayó al titular *Himalaya*: el tema era el mismo, la palabra no.
28. **Cuando un tema pega, el siguiente video es del mismo tema (Agustín, 2026-09-15).** No se salta a otra
    cosa: se repite con otro ángulo mientras la demanda aguante. El canal de referencia repitió cuatro veces
    (2,8 M · 1,2 M · 500 k · 2 M) y solo se cayó cuando cambió de tema. Es además la casilla que la política de
    *inauthentic content* permite por escrito («series with distinct storyline, focus, or concept»).
29. **La voz se pregunta al empezar CADA video (Agustín, 2026-09-15).** *"Es importante que cada vez que
    empiece un video me pregunte qué voz quiero."* Opciones medidas en `voz/voces.py`: **George**
    (`JBFqnCBsd6RMkjVDRZzb`, la de todos los videos hasta hoy) o **Brian** (`nPczCjzI2devNBz1zQrb`, más
    grave, un 22 % más de movimiento tonal). Le gusta alternarlas entre videos. Va como pregunta del
    interrogatorio, antes de generar un solo beat; los títulos de acto siguen con la segunda voz (regla 25).
30. **Motor v4 obligatorio en toda producción nueva (2026-09-15, auditoría).** Manual `produccion/MOTOR_V4.md`,
    plantilla `videos/S12_recibos/coreo4.py` + `escenas4.py`. Antes de renderizar: `check_framing` = 0,
    `sync.py` con VACIO = 0 (y las cifras habladas en pantalla), **mirar la hoja de sync cuadro a cuadro**;
    después de renderizar: `ritmo.py --json` = PASS. Pausas de la voz compactadas con `voz/compactar.py`.

## 1. Mapa del repo

| Qué | Dónde |
|---|---|
| Estrategia, estilo, animación, voz | `IDEA.md`, `ESTILO.md`, `ANIMACION.md`, `VOZ.md` |
| Identidad, intro/outro | `canal/CANAL.md` (§7 = única fuente de la regla de títulos), `canal/INTRO_OUTRO.md`, `canal/NOMBRE.md`. `canal/CALENDARIO.md` está obsoleto (solo historial) |
| Fuentes (scraper YouTube, transcripciones) | `fuentes/yt_guiones.py`, `fuentes/yt/*.md`, `fuentes/FUENTES.md` |
| Guion | `guiones/<NN_tema>/guion.md` (+ `guion_v1.md` histórico), `guiones/checklist.py` |
| Voz | `voz/dirigir.py` (dirección por línea), `voz/alinear.py` (whisper → tiempos) |
| Producción | `produccion/motor.py` (motor), `props.py` (objetos de papel), `mapa_rusia.py` (hoja de mapa), `piloto3.py` (coreografía del ep. 1, plantilla), `mezcla.py`/`mezcla2.py` (audio), `entregar.py` (intro+cuerpo+outro), `intro_outro.py` + `props_canal.py` (intro/outro del canal, v2) |
| Elenco (rigs de papel) | `pruebas/elenco/rig/<nombre>/` (01_burocrata, 02_militar, 03_ejecutivo, 04_trabajador, 05_jurista, 06_vecino, 09_lider_a=Trump, 10_lider_b_v2=Putin, 11_zelensky) + `cut/07_manos`, `cut/08_multitud` |
| Música | `produccion/musica/cue_*.mp3` (Lyria, por acto), `tema_canal.mp3`; `CREDITOS_MUSICA.md` |
| Shorts | `canal/SHORTS.md` (modelo nuevo: 3-5 con guion propio, series, solos), `produccion/shorts.py` (generador), `shorts.json` (ficha de cada pieza) |
| Assets: índice y reuso | `canal/ASSETS.md` (regla y criterios), `canal/INDICE_ASSETS.md` (índice vivo), `canal/assets_catalogo.json` (metadatos), `produccion/indice_assets.py` (`buscar <x>` antes de generar) |
| Estructura de carpetas | `canal/ESTRUCTURA.md` — una producción, un directorio (`videos/<NN>_<tema>/`, `videos/S<NN>_<tema>/`). Hasta el ep. 4 rige el reparto viejo (`guiones/` + `produccion/` planos) |

## 2. Pipeline (orden fijo)

### 2.0 Paso 0 — validar la demanda (0 cr, ~2 min) · regla 26

```bash
python produccion/demanda.py "how britain became a poor country" --geo GB
```

Cuatro señales, todas gratis y sin cuenta (comprobadas el 2026-09-15):

| | Qué mide | De dónde sale |
|---|---|---|
| **A** | Cuánto se busca el tema **dentro de YouTube**, y si sube o baja | Google Trends con la propiedad **Búsquedas de YouTube** (`pytrends`, `gprop='youtube'`) |
| **B** | Si la idea **pegó en años distintos** | `yt-dlp ytsearch` con fecha y vistas |
| **C** | Si la **ola sigue abierta** | los últimos 7 días, medido en YouTube |
| **D** | **De quién es el tema**: creadores o medios | mejor vídeo de creador ÷ mejor vídeo de medio |

**La propiedad importa** (lo señaló Agustín el 15-sep): Trends por defecto mide la búsqueda **web**, que es
gente que lee un artículo y se va; con `gprop='youtube'` mide a quien busca **un vídeo**, que es la que nos
deja horas de visualización. `demanda.py` usa siempre la de YouTube.

**Elegir la palabra del título (regla 27), medida y no intuida:**

```bash
python produccion/demanda.py "us debt" --geo US --titulo "us debt,national debt,debt crisis,debt default"
```

Devuelve el interés de cada término en YouTube a 12 meses y a 4 semanas. Ejemplo real: `us debt` **44,2** ·
`national debt` 28,5 · `debt crisis` 18,5 · `debt default` **2,0**. El instinto decía *default* (es lo que
titula el vídeo de 2,7 M) y la medición dice **us debt**: eso va adelante en el título y en la miniatura.

**D es la que decide.** Se calibró contra los ocho largos del canal y es la única que separa lo que funcionó
de lo que no:

| Tema | Mejor creador | Mejor medio | Nos dio |
|---|---|---|---|
| AfD Sajonia-Anhalt | TLDR **611 k** | BBC 221 k | **478** |
| Malvinas | OverSimplified **29,8 M** | — | **278** |
| IA y empleo | Economics Explained **1,18 M** | MS NOW 5,6 k | **250** |
| Diesel / Saudi | Steve Ram 92 k | DW **713 k** | **4** |

El video de diesel tenía la ola **abierta y caliente** el día que se subió (DW 713 k, WQAD 653 k, 7NEWS 108 k)
y aun así hizo 4 vistas. El tema no era malo: era **de los medios**.

**Los cinco veredictos:**

- `LUZ VERDE - EVERGREEN` — creadores + idea probada en ≥2 años. El mejor caso: sin reloj, y se puede repetir
  (regla 28). Es la clase de Malvinas y de IA.
- `VERDE CON RELOJ` — creadores + ola abierta pero sin historial. **La ventana son 3-5 días**: medido en Nepal,
  el pico está entre el día 1 y el 4 (549 k · 406 k · 395 k) y al día 6 ya cae a 104 k. Si no sale en esa
  ventana, no sale.
- `GRIS - SOLO CON ANGULO` — empate. Se entra solo con lo que el medio no da (el recibo, el mecanismo, el
  precedente), nunca con el vídeo del hecho.
- `NO - ES DE LOS MEDIOS` — el medio le saca ≥1,4x al mejor creador. Si aun así interesa, va al diario o al
  Brief; nunca a un Dispatch de 20 minutos.
- `NO - SIN DEMANDA` — ni idea probada ni ola.

**Dos límites que hay que conocer:**

1. **El veredicto depende de la frase.** *"britain poorer than mississippi"* da `NO - SIN DEMANDA`;
   *"how britain became a poor country"* da `LUZ VERDE` con cuatro años probados (7,6 M · 4,3 M · 2,9 M · 1,9 M).
   **Se prueban 2-3 frases** — las que escribiría el espectador en el buscador, no el título del guion.
2. **Trends necesita el término corto, no la frase.** *"the us cannot repay its national debt"* no tiene
   volumen; el script cae solo al núcleo (*"national debt"*) y lo dice en el informe. Con `--kw` se fuerza
   a mano. Si Google devuelve 429 por pedirle demasiado seguido, el informe sigue sin esa señal.
3. **El RSS de trending del día (`--hoy`) es contexto suelto, no veredicto**, y solo sirve cuando no se sabe
   qué buscar: el feed de US viene cargado de búsquedas de navegación (*"latest news"*, *"stock market
   today"*); el de GB sale más limpio (*"north sea oil"*, *"state pension amount"*). El parámetro
   `&category=` **no funciona**: devuelve el feed general.

Un aniversario **reabre la ola**: el vídeo de Nepal de un año después hizo 119 k. Vale para el calendario.

### 2.1 Tema y fuentes (0 cr)
- El tema lo pasa Agustín (regla 13: *los temas los elige él*, a partir de videos o de un hecho). `canal/CALENDARIO.md` está
  **obsoleto** desde el 8-sep: su cola de temas era del asistente y no se usa.
- `python fuentes/yt_guiones.py <url o id>` → transcripción en `fuentes/yt/`. Varias fuentes si hay.
- Si la API responde `IpBlocked`, bajar los subtítulos con yt-dlp (`--js-runtimes node`) y convertir con
  `python fuentes/vtt2md.py _sub/<id>.<lang>.vtt "<canal>" "<título>" <dur_s> <fecha> [vistas]` (hecho en el ep. 3): `python -m yt_dlp --skip-download --write-auto-sub --sub-lang es,en -o "_sub/%(id)s.%(ext)s" <url>`
  (hecho así con Rallo en el ep. 2; el bloque de conversión está en la sesión del 2026-09-07 y conviene pasarlo a `yt_guiones.py`).
- Cuando la fuente es un video de opinión, la hoja `fuentes/<tema>_referencia.md` separa: datos, opinión de cada fuente
  (tal cual), y "lo que el guion NO dice".
- Resumir hechos y números en `fuentes/<tema>_referencia.md`. No verificar (regla 7), sí cruzar entre youtubers.

### 2.2 Guion (0 cr) — formato A:/V:
- Archivo `guiones/<NN_tema>/guion.md`. Una oración por línea `A:`; planos en `V:` con etiqueta `[WIDE]/[MAP]/[CHAR]/[CARD]`
  y `[GAG]` para chistes visuales. 11 beats: COLD OPEN (25 s) · HOOK (60 s) · SHAPE OF THE PROBLEM · WHO IS LYING ·
  ACTO I…V (140-170 s c/u) · CLOSE (60 s) · NEXT (20 s).
- Escribirlo como RELATO: escenas concretas ("At six forty in the morning, the controllers hear one word…"), "you",
  frases cortas que caen como golpes, humor seco, gancho al cierre de cada acto ("The second one flies.").
- ~2.350 palabras ≈ 16 min con George. Correr `python guiones/checklist.py guiones/<NN>/guion.md`.
- Título: **la regla vive en `canal/CANAL.md` §7.1 y solo ahí**. Vigente desde el 2026-09-13 (decisión de Agustín, *"los prefijos,
  si considerás que son contraproducentes, quitalos"*): **sin `PALABRA-EMOCIÓN:` adelante**; `[cifra o fecha] [quién hizo qué, con la
  emoción dentro de la frase, aterrizado en el que mira] #tag #tag #tag`, ≤ 100 caracteres, tres hashtags iguales en la descripción,
  sin inventar hechos. Lo publicado hasta el 13-sep se queda como está (también las miniaturas).

### 2.3 Voz (≈ 90 cr) — ElevenLabs v3 vía PicsArt, voz George
- `python voz/dirigir.py guiones/<NN>/guion.md --out produccion/audio/dirigido_<NN>` → `beat_XX.txt` con tags de actor
  por línea (`[pause] [whisper] [dry] [slow, each word landing]`…). La dirección va en **`guiones/<NN>/direccion.py`**
  (dict `DIR`, índices de línea por beat; el script asserta; si no existe usa el DIR del ep. 1 que sigue en `dirigir.py`).
- Precio real: **~3,4 cr por 1.000 caracteres** incluyendo tags (ep. 2: 17.400 chars → ~60 cr). Los 11 beats se pueden
  pedir en paralelo en una sola tanda. George lee a ~138-147 wpm según el registro: 2.480 palabras dieron 17:55 de voz
  (18:25 de cuerpo con pre/post-roll), o sea que para quedar en 15-17 min el guion debe rondar **2.200-2.300 palabras**.
- Generar cada beat con `picsart_generate(model="eleven-v3", prompt=<texto del beat>, extra={"voiceId":"JBFqnCBsd6RMkjVDRZzb","language":"en"})`
  (George). ~3 cr por 560 caracteres. Descargar a `produccion/audio/dirigido/beat_XX.mp3`.
- Alternativa medida: Brian `nPczCjzI2devNBz1zQrb` (más rango tonal, menos pausas, más corto). Se eligió George.
- `python voz/alinear.py guiones/<NN>/guion.md produccion/audio/dirigido --voz eleven_george_vN` (tarda ~10 min, whisper
  small.en CPU) → `produccion/audio/<NN>_eleven_george_vN.wav` + `.tiempos.json` (beats y líneas con inicio/fin).
  Pre-roll **1 s** (v2, 2026-09-08), post-roll 8 s, 1,5 s entre beats. Comprobar que todas las líneas tengan ≥0,3 s.

### 2.4 Mapa, props y elenco (0 cr) — **primero buscar en el índice** (regla 19)
Antes de pedir un rig, una cue, un set o un hero: `python produccion/indice_assets.py buscar <lo que haga falta>`.
Hoy ya están pagos 11 rigs, 7 cues propias, 3 sets, 1 hero, 253 props y 4 regiones de mapa = 49 cr. Si la región del
tema ya tiene hoja, se reusa y solo se le agregan puntos a su `pts.json`. Lo que se genere nuevo se anota en
`canal/assets_catalogo.json` o en su ficha `.json`, y se corre `python produccion/indice_assets.py`.

- `cd produccion && python mapa_rusia.py` genera la hoja (Natural Earth 50m, Mercator, LON 18–200, LAT 38–78):
  `mapa_base.png` (con nombres de países), `mapa_rusia.png`, `mapa_husos.png`, `mapa_ciudades.png` (36 sitios con
  etiqueta), `mapa_yakutia.png`, `mapa_frost_norte/este.png`, `mapa_pts.json`.
- Para otro episodio: copiar el script, cambiar bbox y lista `P` de sitios (lon, lat). **Los sitios se etiquetan en la hoja**
  y todo prop se coloca con `G('Ciudad')`. Nada "a ojo". Ejemplo hecho: `mapa_alemania.py` (ep. 2) → `assets/mapa02_*.png` +
  `mapa02_pts.json`, con H calculado desde el bbox (sin distorsión), regiones sin dato oficial (ex RDA, Sajonia-Anhalt) como
  polígonos lon/lat a mano recortados al país real, y puntos "de borde" (`East edge`) para líneas hacia lugares fuera de la
  hoja (Moscú). `M.MapSheet(..., base='mapa02_base.png', pts='mapa02_pts.json')`. Lo que no entra en la hoja va a `WALL`.
- Props nuevos por episodio en `props<NN>.py` (importa `props.py`); el ep. 2 agregó 68 (urna, votantes, gráficos de Rallo,
  escaños, Bundestag, sellos, cadena…). Rigs nuevos: prompt en `pruebas/elenco/prompts_lideres.md`, Flux 2 Pro (1 cr),
  `picsart_remove_bg`, entrada en `juntas.json` mirando la imagen, `python cortador.py <nombre>` (Weidel = `12_weidel`).

### 2.5 Coreografía (0 cr) — `produccion/piloto3.py` es la plantilla
Segunda instancia: `produccion/ep02.py` (mismos helpers; planos propios `GER/SA/EAST/WEST/SOUTH`; helpers nuevos `stamp()`
(sello que cae), `tabimg()`, `drop_in()` (cae desde arriba con transito), `hand_card()`). Errores del ep. 2 a no repetir: todo
`stamp()`/`P()` sin `dur` ni `unpop` queda en pantalla para siempre (mirar la hoja de contacto antes de renderizar);
las tarjetas de acto necesitan que el primer corte del beat sea a un plano que contenga (960,250..330), o cortar en `L(b,1)`.
Sistema de planos (ventanas conocidas): `WIDE` (mesa), `MAPW` (hoja entera), `WEST/MOS/EAST/YAK` (detalles del mapa),
`WALL` (pared para tarjetas grandes), `CHR/CHL` (primer plano de personaje a derecha/izquierda, calculado desde el bbox
del rig con margen para brazos levantados y salto).
- `cut(t,'PLANO')` corte duro + push-in lento; `at('PLANO',fx,fy)` coloca por fracción de la ventana.
- Los rigs existen por plano: `rig(nombre,t,'R'|'L',off=<corte siguiente>)`; se apagan antes del corte. Homes:
  `HOME_R=(1320,330)`, `HOME_L=(130,330)`, escala 0,62.
- Una acción visual por frase (`L(b,i)`/`E(b,i)` = inicio/fin de la línea i del beat b). Gestos automáticos por frase
  (`Rig.gesture`), tráfico aéreo ambiente en rutas reales (`traffic()`), que se detiene con la "alfombra".
- Helpers: `card(txt,t,fx,fy,size,dur,color)`, `P(prop,t,x,y,sc_,dur)`, `img(PIL,t,x,y)`, `fly(avion,t0,t1,A,B)`,
  `fold()`, `shake()`, `acto(num,titulo,t)` (tarjeta de acto + stinger), `cutout()` (manos, multitud).
- Objetos que salen de cuadro a propósito: `flyout()` o `transit.append((t0,t1))`. Fondos/overlays: `bg=True`.
- **v3 (2026-09-08)**: entrada por defecto `o.drop(t,x,y)` (cae y se asienta) en vez de `pop`; cifras con `flipin`; salidas con `slide_off`/`crumple`;
  `rig.point_at(t,G('Moscow'))` señala de verdad; `sc.shake(t)` en sellos y stingers; `sc.whip(t,xy,z)` entre regiones de la misma hoja;
  meta de ritmo: `check` debe dar 0 huecos > 6 s y ≥ 10 cortes/min.
- Reglas de fluidez: pops 0,5 s (`back`), desplazamientos ≥0,8 s (`soft`/`io`), `on` = primer keyframe, nunca `x(0)`
  para leer una posición (usar `x(t)` con t posterior al pop).

### 2.6 Chequeo de encuadre (obligatorio antes de renderizar)
`python produccion/piloto3.py check` → recorre el video cada 0,25 s; imprime `CORTADO <objeto> t=…` y una hoja de
contacto `_hoja_v6.jpg`. **Debe dar `violaciones de encuadre: 0`.** El render aborta si no. Además hay un post-pass en
`build()` que apaga en cada corte lo que quedaría parcialmente visible en el plano nuevo.

### 2.7 Mezcla (0 cr)
`piloto3.py` exporta `eventos3.json` (efectos sintetizados por acción: pop/unpop/slide/clack/stamp/whoosh/tick/flip/
thump/draw/stinger, cues por beat, pulso grave que acelera en actos III/IV/cierre) y llama a
`mezcla2.py voz.wav eventos3.json tiempos.json salida.wav` (cortina −12 dB, ducking −5 dB, silencio 0,7 s antes de
cada stinger). Las cues son Lyria (`picsart_generate(model=lyria-3-pro…)`, 3 cr c/u, ya generadas para el ep. 1;
reutilizables). El tráfico ambiente NO emite sonidos (`fly(..., sfx=False)`).

### 2.8 Render (0 cr, ~40 min con 20 workers)
- Lanzar **desprendido** (los jobs del Bash tool mueren a los 10 min):
  ```bash
  printf '%s\n' 'cd /c/Users/agust/Desktop/agustin/canal_geopolitica/produccion' 'python piloto3.py > _render.log 2>&1' 'echo "RENDER RC=$?" >> _render.log' > _cadena.sh
  powershell.exe -NoProfile -Command 'Start-Process -FilePath "C:\Program Files\Git\bin\bash.exe" -ArgumentList "_cadena.sh" -WorkingDirectory "C:\Users\agust\Desktop\agustin\canal_geopolitica\produccion" -RedirectStandardOutput "…\_cadena.log" -RedirectStandardError "…\_cadena.err" -WindowStyle Hidden'
  ```
  y vigilar con Monitor (`grep RENDER RC=|Traceback`). Escribir los `.sh` con `printf` (sin CR) y rutas `/c/...`.
- Nunca dos renders a la vez: comparten `produccion/_frames`. Antes de relanzar, matar `python.exe` con `piloto3` en la
  línea de comandos y sus hijos `multiprocessing`.
- Mientras renderiza, mirar frames reales de `_frames` (hoja de 12) para cazar fealdades antes del final.
- Tramo de prueba: `python piloto3.py 120 150` → `_tramo_120_150.mp4`.

### 2.8b La ficha de subida NO se manda antes de que el archivo exista (2026-09-14)

`SUBIR_<NN>.md` se escribe en presente —*"El archivo: `salida/..._SUBIR_1440p.mp4`. Ese y nada
mas"*— y eso **afirma que el video esta**. El 14-sep se le mando con el cuerpo al 15 % de render;
Agustin fue a `salida/`, no habia nada, y perdio el tiempo. El mensaje de chat decia "renderizando",
pero **el documento operativo es la ficha**: si dice otra cosa, gana la ficha.

- Se manda **cuando el master existe**, comprobado con un `ls`, no de memoria.
- Si hay que mandarla antes (para que apruebe titulo o miniatura mientras renderiza), lo primero de
  la ficha es un bloque **`⛔ TODAVIA NO SE PUEDE SUBIR`** con el porcentaje real y el comando para
  que lo compruebe el mismo.
- Vale para cualquier entregable: **el tiempo verbal del documento tiene que coincidir con el estado
  real del archivo.**

### 2.8c Todo archivo se entrega con su RUTA ABSOLUTA (2026-09-14)

Agustin: *"las miniaturas donde estan ? pasame las rutas completas. Cuantas veces te lo tengo que
decir ?"*. Se le habia mandado tres veces la hoja comparativa de miniaturas y ninguna vez la ruta
del PNG. **La comparativa sirve para elegir; la ruta sirve para usar. Van las dos.**
Ruta absoluta completa (`C:/Users/agust/Desktop/agustin/canal_geopolitica/videos/<prod>/...`), en el
chat **y** en la ficha, con el dato que hace falta para saber si sirve (1280x720 PNG, 1077 MB, 21:04).

### 2.8d Los shorts SI llevan miniatura propia (2026-09-14)

La ficha de cada short en Studio tiene **Miniatura -> Subir archivo** y funciona igual que en un
video largo (`file_upload` sobre el input `file-loader`, despues **Guardar**). La nota vieja del
proyecto decia que hacia falta el Partner Program; por eso la primera tanda del ep. 08 salio sin
portada y se le dijo a Agustin que no se podia. Su respuesta: *"No mientas si se puede si yo he
subido miniaturas"*.

**La regla que sale de esto: una limitacion de la plataforma NO se afirma de memoria — se mira el
formulario antes de decir que algo no se puede.**

Formato: **1080x1920, menos de 2 MB**. Criterio: **la pregunta grande arriba y el objeto de esa
pieza abajo** — el gancho del propio video ya ocupa el tercio superior y si la portada repite ahi,
compiten. Plantilla: `videos/08_reino_unido/shorts/miniaturas_shorts.py`.

### 2.9 Entrega (regla 4)
`python produccion/entregar.py <cuerpo.mp4> <salida.mp4> --intro_at <fin del cold open, s> [--audio mezcla.wav] [--head tramo.mp4 --head_dur 8]`
→ cold open + intro (14 s desde la v2 del 2026-09-11; eran 8) + resto del cuerpo + outro (20 s; eran 15). **Desde el ep. 3 (decisión del 2026-09-08) el orden es otro: intro de preguntas
(`intro<NN>.py`, ~30 s) → intro general → cuerpo entero → outro, armado con un `ffmpeg concat` de 4 entradas (`produccion/_final03.sh`,
desprendido); `--intro_at` queda para el orden viejo**. **El archivo que se sube es SIEMPRE uno solo y de máxima calidad (Agustín, 2026-09-08): el final 1080p
escalado a 2560×1440 con `-crf 16 -preset slow` (`_master03.sh` → `<ep>_SUBIR_1440p.mp4`), porque la animación de papel comprime a ~2 Mb/s y YouTube
recomprime; a 1440p le asigna VP9 y más bitrate. En `SUBIR_<NN>.md` va ese archivo y nada más; las 720p/540p son solo para el chat y hay que decirlo.** (= `BE(0)+0.3` del tiempos.json), 1080p crf 19, y `_720p`. Para mandar por chat el límite es 30 MB: si la 720p
pasa, hacer 960x540 crf 35 audio 80k. Comprobar duración total y un frame de cada unión (intro/cuerpo/outro).
Los últimos 20 s son la outro: ahí va la pantalla final de YouTube; la mitad derecha queda libre para "video siguiente".

### 2.10 Shorts — regla 17. **Pregunta 00 de toda conversación: ¿qué se produce?**
Antes que el formato (Dispatch/Brief) va **el tipo de producción**, y lo define cómo arranca Agustín la conversación:

| Arranca con | Tipo | Qué se hace |
|---|---|---|
| "hacemos un video de X" | **A · episodio + shorts** | el largo entero + **3-5 shorts con guion exclusivo** |
| "una serie de shorts sobre X" | **B · serie** | una investigación, una pieza por subtemática, encadenadas |
| "un short de X" | **C · suelto** | el pipeline del episodio en chico, una pieza |
| "solo el video" | **A sin shorts** | el largo, `shorts/` vacío |

**Modo A.** Después de entregar el largo. **Mismas imágenes = el arte** (`arte/props.py`, `arte/mapa.py`, rigs, hero,
texturas), **no el metraje**: la coreografía del largo está pegada a la narración vieja, así que con voz nueva
desincroniza. Guion **exclusivo** que destila la idea, no la recorta; cada pieza se entiende sin haber visto nada y
**deja una pregunta abierta**; **50 s mínimo** y el máximo lo decide el tema (techo de Shorts: 3 min).

**Modos B y C.** Es el pipeline completo (§2.1 a §2.9) en formato short: fuentes, interrogatorio de postura, guion,
voz, arte, coreografía vertical, chequeo de encuadre, render, fichas, subida. En una serie el interrogatorio y las
fuentes se hacen **una vez para la serie**; cada pieza tiene su guion, su voz y su coreografía. Sello `PART n OF N`,
playlist propia, una por día en orden, y el "video relacionado" apunta a la pieza anterior (o al Dispatch del mismo
tema, si la serie desemboca en uno: es el mejor uso de una serie).

Pasos, en cualquier modo:
1. `shorts/guion.md` (o `shorts/<n>_<subtema>/guion.md` en serie) y `shorts/shorts.json`: por pieza `hook` (2-3
   líneas, `rojo` = cuál va en rojo), `resaltar`, `titulo`, `desc`, `tags`, `orden` y `por_que`.
2. Voz George con dirección (`voz/voz_fal.py`) + `voz/alinear.py`. **Ya no es 0 créditos**: ≈USD 0,10/1.000 chars,
   ~USD 0,46 por 4 piezas de 90 s. Ojo con la regla 15 (tope de USD 3): `canal/SHORTS.md` §6 y §10.
3. Coreografía vertical reusando el arte + `check` de encuadre: **0 cortados** antes de renderizar (regla 1 y 10).
4. `python produccion/shorts.py <prod> --check` → hoja de contacto; después el render (~3 min por pieza).
5. Subida y programación: skill **`youtube-shorts-upload`** (`--plan`, formulario de Studio, "Video relacionado").
6. Checklist de monetización (§2.10b). No se salta por ser una pieza corta.

La pieza: 1080×1920, cuadro 16:9 completo (nada cortado) sobre hoja de papel, gancho fijo arriba, subtítulos quemados,
barra de progreso ocre, −14 LUFS. **Sin intro del canal, y con una outro corta que pide la suscripción**
(decisión de Agustín 2026-09-08, excepción a la regla 4): 3-4 s, la ficha PT y `SUBSCRIBE · FOLLOW THE PAPER`,
más el enlace al episodio o a la pieza siguiente. Lo que convierte vistas en visitas al canal es **adjuntar el
episodio como "video relacionado"**; sin eso el short es un callejón sin salida (`canal/SHORTS.md`).

El modo viejo (10 shorts recortados del master, 0 créditos, `shorts.py --de-master`) **se conserva** para episodios ya
hechos; es lo único que hay para los eps. 1-3. Historial en `canal/SHORTS.md` §11.

### 2.10b Checklist de monetización (antes de subir, 2 min)
`canal/MONETIZACION.md` §3: sin generalizaciones por grupo en voz, todo extremista/fraude atribuido, sin víctimas recientes como
gancho, sin `Nazi`/`BREAKING`/`invasion`/`fraud` en título-miniatura-descripción, ajustes de Studio, y si sale con anuncios
limitados pedir revisión humana.

### 2.10c Miniatura del episodio (0 cr) y verificación de lo publicado
- **Miniatura**: la base para lo que venga es `canal/miniaturas_v2.py` (13-sep): la cara del protagonista real (rig del elenco), la
  hoja de mapa del episodio con la zona en disputa en rojo, dos o tres palabras en tarjetas grandes, sin sello de marca ni bandas de
  texto chico; se mira a 320 px (`_hoja_v2.jpg`). Es el método que salió de la evidencia del nicho (`canal/_anexo_evidencia_titulos_2026-09-13.md`
  §4); **Agustín aprueba cada miniatura** antes de subir, como siempre. Si el episodio no tiene un protagonista con rig, la cara se
  genera con el camino largo del elenco (`pruebas/elenco/`), no con una imagen suelta.
- **Después de subir** (método del asistente, 13-sep; sale de haber encontrado fichas que decían una cosa y YouTube otra): leer lo
  publicado con `python -m yt_dlp -J <url>` (título, descripción, etiquetas) y compararlo con la ficha `SUBIR.md`/`PUBLICAR.md`; y en
  Studio comprobar que cada short tenga **video relacionado** (los 12 del 11-S salieron sin ninguno). Lo que no coincida se corrige
  el mismo día, mientras es reciente.

### 2.11 Cierre de iteración
Actualizar `RETOMAR.md` (qué se entregó, qué falta), `VOZ.md`/`ANIMACION.md` si cambió el método, la memoria del
proyecto (`~/.claude/projects/C--Users-agust-Desktop-agustin-canal-geopolitica/memory/`) y **esta skill** (changelog +
texto). Pendientes típicos: miniatura + título, bocas para líderes citados, subir.

## 2.12 ANTES de lanzar un render largo (2026-09-14, costo: 25 min tirados)

Tres cosas, en este orden, y ninguna se salta:

1. **`check` tiene que dar 0 violaciones y precision geografica OK.** Obligatorio, aborta el render.
2. **Mirar CUADROS REALES, no la previsualizacion.** O un tramo corto, o los primeros ~600 cuadros
   del render. En el ep. 08 se tiraron 3.200 cuadros porque `check` daba **0 cortados** mientras la
   hoja del Atlantico Sur se quedaba pegada de fondo en casi todo el episodio, el grafico de barras
   estaba mal armado y el cuadro 0 salia vacio. **`check` no ve nada de eso.**
3. **El largo del guion se cierra ANTES de pedir la voz.** El ep. 08 salio en 2.668 palabras contra
   un objetivo de 2.300: 5.000 cuadros de mas, **35 minutos extra de render**. El checklist lo marca;
   con la voz ya generada, recortar cuesta otra generacion. Si el tema pide pasarse, se le dice a
   Agustin con el coste en minutos, no se descubre al final.

El inventario completo de los errores de ese dia, con su regla y donde quedo escrita cada una, esta
en `canal/ERRORES_2026-09-14.md`. **Leerlo antes de empezar una produccion nueva.**

## 2.13 Al copiar el motor de otra produccion (2026-09-14)

- **Revisar todo texto que PROMETA algo.** El cierre de los shorts del ep. 08 decia *"PART 2 IS UP
  NOW"* heredado de la serie S02: no habia parte 2. Es la misma trampa de `prop_urna` (dice "YES"
  desde el ep. 02) y `ticket` ("$418.82" del S04), ahora tambien en las tarjetas de cierre y en las
  outros. **Modo A y modo B no dicen lo mismo** (`canal/SHORTS.md`).
- **Correr UNA pieza entera antes de lanzar la cadena.** `armar.py 1 --frame` cuesta 20 segundos y
  caza los `KeyError` de fichas (en el ep. 08, el gancho estaba en `shorts.json` y el motor lo
  buscaba en `serie.json`, y murio a mitad de la primera pieza).
- **Recalcular las rutas.** El motor de la S02 vive dos niveles bajo la raiz y el de los shorts del
  ep. 08, cuatro: `RAIZ` estaba mal y no importaba `motor`.

## 2.14 Receta del motor v4 (desde el 2026-09-15) — para no redescubrir nada y gastar pocos tokens

Leer **solo** esto: `produccion/MOTOR_V4.md` (la API, 260 líneas), `videos/S12_recibos/PLAN_VISUAL_V4.md`
(cómo se planifica una pieza) y `videos/S12_recibos/coreo4.py` + `escenas4.py` (la plantilla que funciona).
No hace falta leer `motor.py` entero ni las coreografías viejas.

| Paso | Comando / archivo | Tiene que dar |
|---|---|---|
| 0 | Preguntas de arranque: formato (regla 16), **voz** (regla 29), postura (regla 13); `produccion/demanda.py` (regla 26) | respuestas en `postura.md` |
| 1 | Guion `A:` + `fuentes/referencia.md` con `Fn`; `guiones/checklist.py` | 0 cifras sin fuente; las de escala calculadas |
| 2 | **Plan visual por beat** (copiar `PLAN_VISUAL_V4.md`): mundo(s) con bbox, roles y sitios; qué se ve en cada línea; la animación central; MESA = documento grande sobre el mundo oscurecido + 2-3 props, nunca hoja rayada | un documento antes de tocar código |
| 3 | Voz: `voz_corta.py dirigir` (apertura ≤ 3 palabras, inline ≤ 6) → `generar <n>` (fal, `timestamps`, la voz elegida) → `alinear <n>` → `python voz/compactar.py audio/voz.wav ... --max 0.45 --max-largo 0.80 --palabras ... --tiempos ...` y renombrar | `tiempos.json` + `_palabras.json` compactados; `voz/prosodia.py` anotado |
| 4 | Mundos: `mapa_v2.mundo(nombre, bbox, w, sitios=..., capas=..., out_dir='arte/assets')` (bbox vertical para shorts; ~2400-3000 px); cuadro fijo a 1080×1920 en `_qc/v4_mundo_<n>.png` **y mirarlo** | regla 24 impresa (< 3 px), rótulos legibles |
| 5 | `coreo4.py`/`escenas4.py`: `Scene(mundo, size=(1080,1920), v4=True)`, `corte`+`viaje` por plano, capas cuando la voz nombra el país, HUD para subtítulos/cifras/rótulo, rig de pie sobre el mapa (`figura`), `python coreo4.py check <n>` | `check_framing` **0**, `sync` **VACIO 0**, CIFRA 0; **mirar `_qc_sync/sync_00.jpg`** |
| 6 | `python coreo4.py render <n>` (uno a la vez, `frames=` propio) → `shorts.armar_vertical(...)` → `cierre.py generar/pegar` → `python produccion/ritmo.py <final> --json` | ritmo **PASS**; hoja de 12 cuadros reales + vista a 405 px mirada |
| 7 | `publicar.py` → `publicar/SUBIR.md` + `_up/` (< 10 MB) | ficha con rutas absolutas, checklist de monetización |

Episodio largo: lo mismo con `voz_ep.py` (beats, bloques de acto protegidos en `compactar --proteger`),
`Scene(mundo, size=(1920,1080), v4=True)`, intro de preguntas ≤ 12 s en movimiento, `entregar.py`
(intro v3 + cuerpo + outro, `loudnorm`). Plan de referencia: `videos/09_deuda_eeuu/PLAN_VISUAL_V4.md`.

Lo que **no** garantiza el sistema y sigue siendo trabajo de mirar: la composición (que un cuadro se
vea bonito y no solo correcto) y el sentido de cada imagen. Por eso la hoja de sync se mira siempre.

## 3. Errores ya cometidos (no repetir)
- Intro del canal pegada ANTES del cold open + 8 s de pre-roll = 16 s sin voz (ep. 1 publicado, promedio 2:18). La decisión era intro tras el cold open.
- Tarjetas de lugares (TURKEY, BELARUS, HORMUZ, IRELAND) colocadas por fracción del plano sobre el Ártico; sobre enviado a Kazán cuando el guion decía Urales. Todo lugar va con `G()` o a la pared.
- Yakutia pintada del mismo celeste que el mar: se lee como un lago.
- Zoom continuo de cámara que recorta tarjetas/personajes en los bordes → usar cortes entre planos + chequeo.
- Puntos "a ojo" sobre el mapa, regiones vagas ("Urals"), tarjetas de lugares que no están en el mapa (Hormuz, Irlanda)
  encima del mapa → sitios reales etiquetados; lo que no está en el mapa va a la pared (`WALL`) o a la franja superior.
- Bugs de motor que hacían saltos: keyframe exacto devolvía el anterior (flash en 0,0), `unpop` saltaba a escala 1,
  `pop`+`scale` duplicaban keyframes (flash a tamaño completo). Corregidos en `motor.py` v2.
- 459 sonidos "slide" del tráfico ambiente ensuciando la mezcla → tráfico mudo.
- Yakutia como rectángulo lon/lat → polígono orgánico; escarcha como rectángulo → capa enmascarada a Rusia con degradé.
- Relato "documental serio" = aburrido → relato con escenas, "you", humor seco, ganchos.
- Presentar reglas propias (prohibir Trump/Putin, "cero emoción", verificar fuentes) como si fueran de Agustín.
- **Las fichas decían una cosa y YouTube tenía otra** (descubierto el 2026-09-13 leyendo lo publicado con `yt-dlp`): descripción
  del canal v1 rechazada, `[link a la hoja de fuentes]` publicado en el ep. 1, `SUBIR ESTE ARCHIVO:` pegado en el título de un
  short, eps. 1-5 sin etiquetas, 8-12 hashtags contra los tres de la regla, ningún comentario fijado, shorts sin URL del episodio.
  Lo publicado se puede leer sin entrar a Studio: `python -m yt_dlp -J <url>` (título, descripción, etiquetas, comentarios).
- Kokoro (voz local) rechazado: "sin alma". ElevenLabs George con dirección de actor.
- `_frames` compartida: un segundo render borró los cuadros del primero.
- Heredocs con líneas muy largas en el Bash tool → usar el Write tool; `.sh` con CRLF → `printf`.
- `entregar.py` y `shorts.py` en primer plano del Bash tool: el tool los mata a los 10 min (ep. 3: la 1080p y la 720p ya estaban hechas y se perdieron al relanzar). Lanzarlos **desprendidos** como el render (`_entregar03.sh`, `_shorts03.sh`) y vigilar el log con Monitor.

### Del ep. 05 (2026-09-09) — cuatro fallos de coreografía que valen para cualquier episodio
- **`win()` devolvía la ventana ANTES del push-in.** Cada corte empuja un 5 % durante todo el plano, así que
  la ventana buena para colocar cosas es la del FINAL, no la del primer cuadro. Con la grande, todo lo que va
  cerca del borde entra bien y se corta dos segundos después. `win()` tiene que devolver `w/(1+PUSH)`.
- **La pasada de ritmo miraba sus propios cortes.** `insertos()`/`rellenar_huecos()` calculaban el plano de
  referencia sobre TODOS los cortes, incluidos los que ellas mismas insertaban, y el corte de vuelta aterrizaba
  en un plano que el guion ya había abandonado. Hay que guardar `CUTS0 = sorted(CUTS)` antes de las pasadas y
  calcular el plano y el límite de la vuelta **sólo sobre los cortes del guion**. Era el 70 % de los cortados.
- **`SUP` tiene que ser siempre el plano que CONTIENE al cerrado.** Se probó `'WIDE': 'MAPW'` para poder partir
  los huecos que caen sobre la mesa: MAPW es más cerrado que WIDE, así que dejó a medias todo lo colocado para
  WIDE (113 cortados de golpe). Los huecos sobre el plano más abierto se llenan con **contenido**, no con un
  corte de relleno.
- **Medir un prop rotado por su alto × ancho.** Un prop a −72° ocupa su bbox rotado
  (`w·cos + h·sin`, `w·sin + h·cos`). Sin eso, el auto-encaje lo deja pasar y el chequeo lo marca.
- **Red de seguridad que sirve**: `caber(im, x, y, sc_)` **achica** el objeto hasta que entre, sin moverlo,
  porque casi todo está anclado a un sitio real del mapa (regla 2) y correrlo sería ponerlo donde no va. Los
  sellos y tarjetas de TEXTO sí se pueden mover (`clamp`), porque no están anclados a nada.
- **Probar la coreografía ANTES de que termine whisper** con un `tiempos.json` sintético
  (`_tiempos_falso.py`: reparte la duración real del WAV entre los beats en proporción a las palabras) y
  `TIEMPOS=... python coreo.py check`. Caza los `KeyError` de props y los desbordes de índice sin esperar
  media hora. De 230 violaciones a 0 sin tocar el audio.

### Mirar CUADROS DEL RENDER, no la previsualización (ep. 05, 2026-09-09)
La hoja de contacto que arma `check` usa `sc.render(t)` y engaña: se ve bien y el render real no. En el ep. 05
hubo que **cortar el render al 16 %** porque en los cuadros de verdad la hoja del mapa era chica dentro del
cuadro y sobraba mesa por todos lados. **A los ~5 minutos de render, armar una hoja con cuadros reales de
`_frames/` y mirarla** antes de dejarlo correr una hora.
- **La hoja de mapa tiene que llenar el ancho del cuadro.** Escala = 1920 / ancho_de_la_hoja (en el ep. 05,
  2400 px → `MAP_S = 0.72`, hoja de 1728×713, franja de mesa arriba y abajo). Con menos, todo se ve chico.
- **El plano `MAPW` tiene que CONTENER la hoja entera**: `zoom ≤ 1920/(ancho_hoja+margen)`. Si es más cerrado,
  recorta el mapa y todo lo anclado a los bordes queda a medias.

### Que la pantalla nunca se quede sola con el mapa (ep. 05, 2026-09-09)
Se midió: el **9,7 % del episodio** (104 s, con tramos de hasta 7 s) no tenía nada en pantalla salvo la hoja.
Pasa por dos motivos: se corta a un plano y el contenido entra un segundo después, o un prop se apaga antes de
que aparezca el siguiente. El chequeo de huecos NO lo detecta, porque cuenta **eventos** (sonidos), no lo que
se ve. Hace falta una pasada aparte que mida **lo que de verdad está dentro de la ventana**:
1. Muestrear cada 0,25 s y marcar los tramos sin ningún objeto visible.
2. **Partir cada tramo por los cortes de cámara**: un relleno sólo vale dentro del plano en el que nace.
3. En planos de mapa, meter la **etiqueta de la región** (`THE GULF`, `THE UNITED STATES`…): tapa el hueco y
   además informa. En planos de mesa o pared, **estirar la última tarjeta** (seguro: ya entraba ahí).
4. Repetir tres veces, porque cada pasada deja restos.
Bajó a 6,5 %, y lo que queda son las pausas de 1,5 s entre beats. **Sólo se estiran tarjetas**, nunca props
grandes: estirar el foco lo metía en un plano donde no entraba.

### El post-pass puede APAGAR al protagonista (ep. 05, 2026-09-09)
El post-pass apaga en cada corte todo lo que quedaría a medias. En el ep. 05 eso **borró la caricatura de bin
Laden en mitad del cierre**, justo cuando la voz cuenta que él mismo hizo la cuenta: el corte iba a `WALL` y la
figura, colocada abajo, no entraba. **Antes de renderizar, revisar la lista de `apagados en corte` y buscar ahí
los props que son el sujeto de la escena.** Si aparece uno, se sube o se achica hasta que entre también en el
plano al que se corta, o se cambia el corte.

### `M.EVENTS` es global: `build()` tiene que empezar con `M.EVENTS.clear()` (ep. 05, 2026-09-09)
El pool de render **reusa procesos**, así que un worker puede llamar a `build()` varias veces. Sin el clear, la
segunda llamada ve los eventos duplicados, la pasada de ritmo no encuentra huecos y calcula **otros cortes**:
el video sale con la cámara saltando entre tramos. Se comprueba llamando a `build()` tres veces seguidas y
verificando que den los mismos cortes y el mismo número de eventos.

### El PRIMER CUADRO del video: ningún keyframe puede fijarlo (ep. 05, 2026-09-09)
`motor.Track.__init__` crea `self.k = [(0.0, v0, 'hold')]` **y** `__call__` corta con
`if t <= k[0][0]: return k[0][1]`. Consecuencia: **en el instante 0 gana siempre el valor inicial del Track**.
Un keyframe en `t=0` no gana (lo tapa el corte), y uno negativo es peor (queda detrás del inicial y la cámara
entra interpolando). En el ep. 05 el video abría con la hoja de mapa sin revelar y la cámara en plano general;
el plano del guion entraba recién en el cuadro 2. Es un cuadro de 25.594, pero es **el que YouTube usa al pasar
el cursor por la miniatura**.
**La vuelta:** inicializar los Track, no ponerles keyframe en 0.
```python
mp.reveal = M.Track(1.0)                      # y NO mp.reveal.set(0, 1, 'hold')
if CUTS:                                      # al principio de finalize_cam()
    _x, _y, _w, _h, _z = win(CUTS[0][1])
    sc.cx = M.Track(_x+_w/2); sc.cy = M.Track(_y+_h/2); sc.zoom = M.Track(_z)
```
Y si el render ya salió sin el arreglo, no hace falta rehacerlo entero: `motor.render` borra `_frames` al
**arrancar**, no al terminar, así que se rehace el cuadro 0 y se vuelve a correr el `ffmpeg` de armado
(`videos/05_11s/_arreglar_cuadro0.py` es la plantilla).

### Rutas de música absolutas (ep. 05, 2026-09-09)
`mezcla.cargar()` resuelve el archivo de cada cue **contra el directorio actual**. Desde `videos/<prod>/` las
rutas relativas tipo `musica/cue_01_intro.mp3` no existen. En `eventos.json` van absolutas.

### Alineación: NO emparejar palabras por cantidad (ep. 05, 2026-09-09)
`voz/alinear.py` y la primera versión de `voz_ep.py` le daban a cada línea tantas palabras de whisper como
palabras tiene la línea. **Eso se rompe en cuanto el guion escribe números con letras**: "two thousand nine
hundred and seventy-seven" son 6 palabras y whisper transcribe "2,977", que es 1. El desfase se ACUMULA: en el
ep. 05 llegó a 34 s en el beat 8, y el beat del cierre quedó con sus primeros 33 s sin ninguna línea y sus
últimas ocho —el veredicto del video— apretadas en 2 s. El re-sincronizado por beat no alcanza porque sólo
avanza el puntero, nunca lo retrocede.
**La vuelta:** emparejar por TEXTO con `difflib.SequenceMatcher` entre los tokens normalizados del guion y los
de whisper, beat por beat, e interpolar las líneas sin ancla entre sus vecinas. Y **cachear las palabras de
whisper** en `audio/_palabras.json`: la transcripción de 18 min tarda ~35 min de CPU y no hay que repetirla
para cambiar el reparto. Los límites de beat son exactos (salen de sumar los MP3), así que sirven de marco duro.

### Del ep. 06 (2026-09-11) — la alineación puede mentir dos veces, y el mapa no siempre va

**1. El cache de whisper YA está en la línea de tiempo final.** `alinear` arma `voz.wav` (con los bloques de
acto metidos) y DESPUÉS transcribe, así que `audio/_palabras.json` queda en la línea de tiempo definitiva. La
corrección que desplaza las palabras por los bloques de acto sólo vale si el cache se hizo de un wav SIN los
bloques. Aplicándola igual, el video queda **detrás de su propia voz**: en el ep. 06 eran +2,8 s en el acto I
y **+14,4 s en el cierre**, y ningún chequeo lo ve porque los tiempos son internamente coherentes. Se detecta
comparando la ÚLTIMA palabra del cache con los dos finales posibles (con y sin bloques) y se salta la
corrección si ya encaja con el nuevo. **Síntoma para buscarlo:** la primera línea de cada beat empieza cada vez
más tarde respecto del inicio del beat. Un `for b in range(11): primera_linea - inicio_beat` lo muestra en
cinco segundos; tiene que dar < 1 s en todos.

**2. Anclar por el primer y último token de cada línea se rompe.** Basta que una palabra común ("the")
enganche al final del beat para que el `fin` de esa línea salte allá y las siguientes se queden sin sitio: 21
de 223 líneas cayeron en el mismo instante, **todas al final de un beat**, y entre ellas las cuatro del cierre
— el pedido de comentario duraba 0,3 s. Un puntero que avanza línea por línea es peor (42): si una línea
engancha lejos dentro de su ventana, el puntero se va de paseo. **Lo que aguanta: el centro de cada línea es
la MEDIANA de los tiempos de sus tokens anclados** (un anclaje malo no mueve una mediana), se tiran los
centros fuera de orden, y cada línea va del punto medio con la anterior al punto medio con la siguiente. Más
una **red de seguridad** que le garantiza a cada línea `0,30 + 0,050 × palabras` segundos redistribuyendo
dentro del beat. Quedó 1 de 223. El chequeo es una línea: contar líneas con `fin - inicio < 0,55`.

**3. La hoja de mapa NO es la superficie por defecto.** En el ep. 05 el mapa estaba siempre porque el episodio
entero era geográfico. En un episodio de economía, con la hoja abajo el cuadro se lee como un atlas con cosas
encima: el billete del cold open parecía flotar sobre el Atlántico. `mp.reveal` se maneja desde
`finalize_cam()` según el plano de cada corte —1 en los planos de mapa, 0 en los de mesa y pared— con un
fundido de 0,3 s. Se ve en la hoja de contacto de `check` sin renderizar.

**4. Nada NACE dentro de un bloque de transición de acto.** Si la última línea de un beat se alinea pegada a
su final, un `L(b, última)+0.8` cae ya dentro del bloque de 4,4 s: el objeto aparece sobre la tarjeta de acto,
en plano `WALL`, y por lo tanto cortado. Un `fuera(t)` que corre la creación hacia atrás y un `tope(t)` que
mata todo antes del bloque bajaron de 46 cortados a 11. **Y ningún cartel ni prop sin `dur` explícito**: el
`card()` del episodio pone 8,2 s por defecto y el `stampcard()` 5 s, porque lo que se queda para siempre
reaparece cortado en cada plano nuevo (era el error del ep. 02 y volvió).

**5. Las cifras no van sobre la hoja.** Es la regla de los lugares (ep. 01) aplicada a los números: en una
ventana regional un cartel entra justo y al cortar a `WALL` queda a medias. **El mapa dice DÓNDE, la pared
dice CUÁNTO.**

**6. `motor.Rig` posiciona por el ORIGEN del rig, no por su centro**, y los rigs nuevos miden entre 760 y 955
px de ancho (los del elenco base, 768). Un `x=1440` con escala 0,50 pone el borde derecho en 1917. El helper
`figura()` recibe el centro y convierte, y mide el margen **contra la ventana del plano**, no contra el cuadro.

**7. Cerrar los planos de mesa para llenar el cuadro rompe los rigs.** Se probó `WIDE` 1.26 y `WALL` 1.78
(todo un cuarto más grande): 344 cortados, todos rigs, porque la ventana se hace más chica que la figura. Si
alguna vez se cierran, hay que rehacer `figura()` para que escale el rig a la ventana primero.

**8. Vestir la mesa: viñeta sí, tapete no.** La mitad de abajo del cuadro queda como madera vacía en los
planos de mesa. Un `alfombra` a lo ancho es peor (un rectángulo rojo que domina todo). Lo que funciona es una
**viñeta** (un PNG de fondo con alfa que oscurece la franja baja y los lados: la madera lee como profundidad)
más tres objetos chicos y quietos. Va con `bg=True`, así que está exenta de los chequeos.

**9. Los cuadros de aprobación hechos a mano engañan más que la previsualización.** Para el ep. 06 se armaron
11 cuadros fijos a 1920×1080 componiendo con PIL sobre el fondo real, y Agustín los aprobó; el render salió
peor, porque a mano se compone centrado y la coreografía coloca por fracción de ventana y `caber()` achica.
**Los cuadros de aprobación tienen que salir de `sc.render(t)` con la coreografía puesta**, aunque sea con un
`tiempos.json` sintético.

**10. Un episodio abstracto se sostiene con OBJETOS, no con gráficos.** El ep. 06 usa tres y vuelven: el
billete que se rasga (60/40 → 45/55), el panel de cinco diales y las dos bandejas. Cada cifra cae dentro de
uno de los tres. Y dos gags cargan el juicio sin que la voz opine (el caballo de papel que al final lleva
corbata, la silla del gabinete con una pantalla).

**11. Fuentes primarias en vez de videos de YouTube.** Cuando el tema lo pide (Agustín: *"NO TE INVENTES
NADA"*), la hoja de referencia numera cada dato `F0`…`Fn` con su URL y **nada entra al guion sin su `Fn`**, más
una sección "lo que el guion NO dice y por qué". Cuesta más pero es lo que permite nombrar gente con nombre y
apellido sin riesgo. Ejemplo completo: `videos/06_ia_economia_politica/fuentes/referencia.md`.

**12. El checklist marca densidad numérica de más y es un falso positivo** en episodios de economía: cuenta
"one", "two" y los años como cifras. Medir sólo cantidades reales (`percent|billion|million|thousand|hundred`)
antes de tocar el guion: el ep. 06 daba 1 cada 29 palabras por el contador y 1 cada 89 de verdad.


### Del ep. 06, segunda vuelta (2026-09-11) — "la animación me parece muy mala"

Agustín, después de ver el primer render: *"La animacion me parece muy mala, deberia tener mas animaciones
mejores, tiene que ser atractivo. No puedes haber hecho un video tan malo. Rehaz el video. Tienes que meter
personitas y cosas moviendose... no quiero que esto vuelva a pasar."* Tenía razón y la causa fue concreta:
**el motor ya traía todo el vocabulario de animación y el primer corte no lo usaba.** No era una limitación,
era no haber leído `produccion/piloto3.py`, que sí lo usa.

**Lo que hay y hay que usar SIEMPRE** (`motor.Rig`): `enter`/`exit` (entra y sale de cuadro), `gesture(t, i)`
— **un gesto chico en CADA frase mientras la figura está en pantalla**, que es lo que hace que nada quede
quieto —, `point(t, side, hold, amp)` y `point_at(t, G('sitio'))` (señala de verdad un punto del mapa),
`hold(obj, side, t0, t1)` (**le pone un prop en la mano**: el maletín, la llave, el mazo, la factura),
`walk`, `hop`, `shrug`, `slam`, `nod`, `look`, `raise_arms`, `lean`. Más el vaivén de respiración, que es
automático. Un rig en pantalla se mueve solo; un cartel no.

**La regla práctica que salió de esto:** en cada beat tiene que haber **una persona y una cosa moviéndose**.
Personas: los dos protagonistas del episodio vuelven una y otra vez (acá el ejecutivo y el electricista), más
el burócrata para el Estado, el vecino para el votante, el jurista para el tribunal y la caricatura del líder
que toca. Cosas: la moneda que viaja de una bandeja a otra, la balanza que se inclina, los diales que giran de
uno en uno, las pilas de dinero que crecen, la multitud que avanza hacia una puerta que se cierra, el escalón
que se rompe, el vapor que sube, la papeleta que entra en la urna, el auto que cruza el cuadro.

**`enmano()` NO hace `sc.add()`.** El rig dibuja el prop en la posición de la muñeca y su `bbox` ya lo
incluye. Agregarlo además como capa suelta lo dibuja en (0,0) —la esquina— y el chequeo lo marca cortado:
**789 violaciones de golpe**, todas props en la mano.

**`motor.Rig` posiciona por el ORIGEN, y el margen se mide contra la VENTANA del plano.** Ver la lección 6 de
la vuelta anterior. El helper `figura()` del ep. 06 recibe el centro deseado, convierte, y si no entra achica.

**La hoja de contacto a 480 px miente sobre el tamaño de las figuras.** En la hoja parecían chicas y a 1920
se veían bien. Antes de cambiar escalas, **mirar UN cuadro a tamaño completo**.

### La intro propia del episodio (lo que faltaba en el ep. 06)

Agustín: *"lo que no veo es la intro del video en SI, cada video tiene una intro propia, luego se encrusta la
general y la outro."* Es la regla 4 y en el ep. 06 no se había hecho. Plantilla: `videos/05_11s/intro05.py`
→ `videos/06_ia_economia_politica/intro06.py`.

1. **La voz se pide con `timestamps: True`.** El endpoint `fal-ai/elevenlabs/tts/eleven-v3` devuelve el campo
   `timestamps` **en null** si no se pasa el flag, y sin timestamps por carácter no se puede anclar la imagen
   a cada pregunta. Costó una generación de más descubrirlo.
2. **El audio se retrasa `T_VOZ` con `adelay`.** La coreografía espera la voz a los 0,6 s pero el mp3 habla
   desde su cuadro 0: sin el `-af adelay=600|600` la imagen va medio segundo adelantada. Y **sin `-shortest`**,
   que además recortaba el final del cartel de cierre.
3. **La hoja del mundo tiene que SANGRAR** por los cuatro lados (es la lección v2 de `INTRO_OUTRO.md`): con
   escala 0,70 quedaba una banda en el medio con madera abajo y pared arriba. Con 1,50 llena el cuadro.
4. **Cada pregunta lleva su imagen a medias**, nunca la respuesta: las dos figuras enfrentadas, la silla del
   gabinete con una pantalla, nueve fichas de diez, el recibo de sueldo con una flecha hacia la jubilación.
5. **La hoja de control se muestrea DOS SEGUNDOS después** del inicio de cada pregunta: en el instante exacto
   las figuras todavía están entrando y la hoja sale vacía (pasó, y parecía que no se dibujaba nada).


### Motor de shorts: seis cosas medidas en la serie S02 y en los shorts del ep. 06 (2026-09-11)

El motor de serie (`videos/S02_ia_riesgo/coreo.py` + `escenas.py`) es hoy la plantilla para cualquier tanda
de shorts: se copia y se le cambia el arte. Estas seis correcciones ya estan dentro y **no hay que volver a
descubrirlas**.

1. **Un prop con duracion fija deja el plano vacio.** En el primer armado de la S02 la mitad de los cuadros de
   control salieron en blanco: props de 4 s en planos de 8 s. La duracion se calcula **hasta pasado el corte
   siguiente** (`escenas.correr::hasta`), y como el post-pase de encuadre ya apaga lo que no entre en el plano
   nuevo, una duracion larga no puede cortar nada.
2. **Nada nace despues del corte siguiente.** Los pasos se escriben en orden de autoria, pero un ancla con
   offset —`(5, 2.2)`— puede caer del otro lado de un corte que se declara mas abajo en la lista: el objeto se
   coloca con las coordenadas del plano VIEJO y aparece cortado en el nuevo. Lo resuelve `escenas.correr::antes`.
   Es la misma trampa que en el ep. 06 se habia parcheado con `fuera()`, aca resuelta de raiz.
3. **El post-pase de encuadre necesita DOS ventanas**: `dentro` se juzga con la del final del push-in (el objeto
   tiene que entrar durante todo el movimiento) y `fuera` con la del instante del corte. Con una sola pasaban
   objetos que asoman 3 px justo al cortar y el chequeo los marcaba despues.
4. **Post-pase de solape (regla 22).** Si algo nuevo tapa **mas del 25 %** del area de algo que ya estaba, lo
   viejo se apaga al entrar el nuevo. El 25 % deja pasar el apoyo de esquina de dos fichas —que se lee como una
   pila— y atrapa lo que de verdad molesta: una tarjeta de texto encima de otra.
5. **Una tarjeta nacida en un plano cerrado queda ilegible si el corte siguiente abre el plano.** La tarjeta se
   dibuja chica en unidades de escena, asi que sigue entrando entera pero se lee a 20 px. Ahora el post-pase
   apaga el texto que ocupe **menos del 1,2 %** del area de la ventana nueva.
6. **La caja de `rig.json` es la de REPOSO.** `enter()` y `gesture()` rotan los miembros y el bbox real llega a
   ser **1,16 veces mas alto** (medido: 1.188 px dibujados contra 1.024 de la ficha). `figura()` presupuesta
   **1,25** y mide contra la ventana del final del push-in; sin eso los rigs se pasaban ~30 px por abajo. Y un
   **prop en la mano agranda el bbox y `figura()` no lo sabe**: si es alto —una escalera—, va al lado y no en la mano.

### Mapas en shorts: una hoja muy ancha no sirve para primeros planos (2026-09-11)

La hoja del ep. 06 mide 2400x746 (3,2:1) y cubre 282 grados de longitud: **8,5 px por grado**. Consecuencias que
se midieron, no se supusieron:

- **Albania mide 21 px** en esa hoja. Un "primer plano" es una mancha.
- **Washington y Pekin estan a 193 grados**: no hay una sola posicion de la hoja en un cuadro 16:9 que permita un
  plano honesto de los dos, ni un plano mundial que no meta la pared clara en el cuadro.
- Un **sello de papel centrado en una ciudad ocupaba 33 grados** de longitud. Eso es exactamente lo que la
  regla 24 prohibe.

Las dos salidas, segun el caso: **(a) no llevar mapa** —la S02 no lo lleva, y las banderas que se ven son props
sobre la mesa, no marcas sobre un sitio, asi que no afirman un lugar—; **(b) una hoja nueva de la region**, que
cuesta 0 creditos porque es render local: `videos/06_ia_economia_politica/arte/mapa_balcanes.py` cubre 20 grados
con 2000 px (**100 px por grado**) y ahi Albania mide 250. Y en `at_map` va el parametro **`grados`**, que pone
el tope de tamano en grados de longitud (4-6 una ciudad, 8-12 un pais) por multiplicacion y no a ojo.

### Tandas de shorts: serie (B) vs. del episodio (A) — que cambia de verdad

| | Serie (B) | Del episodio (A) |
|---|---|---|
| Sello en pantalla | `PART n OF N` | ninguno |
| Tarjeta final | `SUBSCRIBE` + a que pieza va | `FULL EPISODE ON THE CHANNEL` |
| Video relacionado | la pieza anterior | el Dispatch |
| Publicacion | una por dia... **salvo que sea noticia** | con el episodio o despues |
| Playlist | propia, con el nombre de la serie | ninguna |

**La excepcion de la cadencia la fijo Agustin el 2026-09-11**: la S02 salio **entera el mismo dia** porque era
noticia de tres dias. La regla de "una por dia" vale para series que no caducan. Y el **selector de hora de
Studio solo acepta multiplos de 15 minutos**: `publicar.py` ahora lo asserta en vez de descubrirlo en el navegador.

### El cierre de like y suscripcion va PEGADO, no dentro del guion (2026-09-11)

Agustin, con las cinco piezas ya armadas: *"en todos los short haz un breve cierre pidiendo like y suscripcion"*.
Meter la linea en el guion obligaba a volver a pedir las cinco voces enteras (USD 1,18) para ganar cuatro
segundos. Se hace con `cierre.py`: **un clip de voz corto por pieza** (USD 0,04 los cinco) sobre una **tarjeta a
pantalla completa** (pulgar y campana de papel, `LIKE + SUBSCRIBE`, la pregunta de la pieza y el sello del canal),
concatenado despues del cuerpo ya armado. Cada pieza dice una frase distinta (regla 23) y **la ultima manda a la
serie completa o al episodio**, no a la siguiente.

### Un short suelto (modo C) de punta a punta: S03, «The Warning» (2026-09-11)

Primera produccion **modo C** completa: un tema, un short, pipeline entero en chico. Plantilla
reutilizable en `videos/S03_aviso_oct7/` (se copia y se le cambia el arte). Ocho cosas medidas:

1. **El primer objeto del video no puede ser un `dr` (caida).** El post-pase de encuadre muestrea
   0,10 s despues de cada corte; a esa altura la caida esta a medias sobre el borde superior —ni
   dentro ni fuera— y la apaga. Entra con `P`, que crece desde su sitio. Se detecto mirando un
   **cuadro real** a los 4 s: estaba el sello y no el periodico. La hoja de contacto no lo mostraba.
2. **Las ventanas de plano tienen que CABER en su superficie, y se comprueba con cuadros reales.**
   Heredadas de la S02, `CTR` se salia de la hoja de trabajo por la derecha (una tira de madera en
   todos los planos de mesa) y `WALL` se metia en la mesa por abajo. Se arreglo en el fondo
   (`MESA_Y` 300 -> 420, hoja 1010x820 -> 1150x648 en x=-14) y en las dos ventanas.
3. **`CRECER` 0,52 deja el cuadro vacio en un short.** Subio a 0,62. Y la regla de composicion que
   salio de mirar 36 cuadros: **nunca un objeto solo**. Cada beat abre con su objeto a la izquierda
   (fx ~0,27) y a los ~2 s entra su contraparte a la derecha (fx ~0,72); los beats de un solo
   elemento llevan un rotulo arriba (fy 0,10).
4. **Los props compartidos estan dibujados para 90 px.** En un short ocupan medio cuadro y ahi
   `prop_cohete` se lee como una casita, `prop_dron` como una pesa y `prop_moto` como una mancha
   negra. Hay que redibujarlos grandes (`cohete_p`, `dron_p`, `moto_p` en `arte/props_s03.py`).
5. **Con `CRECER` alto, dos objetos a fx 0,27 y 0,72 SI se tocan**, y el post-pase de solape apaga al
   que estaba: se comio la ficha `NETANYAHU` cuando entro el sello al lado. Si hacen falta tres
   elementos, uno va arriba del todo.
6. **Ojo con lo que dicen los props viejos.** `prop_urna` lleva escrito `YES` (viene del referendum
   del ep. 02); en una eleccion israeli decia otra cosa. Se cambio por la bandera.
7. **La familia `props` del indice de assets no consultaba el catalogo** —escribia `quien=''` fijo—,
   asi que el primer prop pagado con IA figuraba como codigo gratis y `buscar` no lo encontraba por
   su nombre. Corregido en `produccion/indice_assets.py`: ahora hereda su ficha como las demas.
8. **Recortar una imagen generada no cuesta un remove-bg.** El fondo que devuelve Flux con el prompt
   del elenco es un plano liso: un relleno por inundacion desde las cuatro esquinas con
   **tolerancia 14** alcanza (`arte/recortar_bibi.py`). Con 34 se comia el pelo blanco.

**Y lo que NO salio bien:** cinco intentos de Flux 2 Pro para la caricatura de un lider real y
ninguno es inequivocamente el. El parecido se sostiene con el contexto (la miniatura dice OCT 7), no
solo. Si el lider va a volver, conviene el camino largo del elenco
(`pruebas/elenco/prompts_lideres.md` + `juntas.json` + `cortador.py`) en vez de una imagen suelta.

### El orden del final de un short (Agustin, 2026-09-11)

*"al final que le deje a los oyentes un ¿Y tu que piensas? ... dejalo en los comentarios. Y luego como
en todos, la outro con la incitacion a suscribirse y darle like."* Son **tres tarjetas y en este
orden**: la pregunta (ultima linea del guion, dicha por la voz), el sello del canal, y recien despues
`LIKE + SUBSCRIBE` con la voz del `cierre.py`. La tarjeta del cuerpo (`tarjeta_cta`) **no** repite
SUBSCRIBE: dos carteles casi iguales seguidos se anulan y el que pierde es el que tiene voz.

### Del ep. 07 (2026-09-14) — el motor del ep. 06 venia con tres agujeros, y la mesa estaba vacia

**1. `check_geo` tenia clavados los 222 grados de la hoja del ep. 06** (`grado = base.width*sc/222`).
Cualquier episodio con otra hoja mide mal el tope de tamano: con la del 07 (44 grados) daba **cinco
veces de mas** y marcaba props correctos como si taparan medio mapa. Tiene que salir del `GRADO` del
propio episodio.

**2. `figura()` no presupuestaba el crecimiento del bbox por los gestos.** Es la leccion 6 de la S02
—la caja de `rig.json` es la de REPOSO y `enter()`/`gesture()` la agrandan hasta 1,16x— y el motor
del ep. 06 nunca la incorporo: `min(sc_, ww*0.92/ancho, hh*0.92/alto)` sin el 1,25. Los rigs se
pasaban ~30 px por arriba en los planos cerrados.

**3. El post-pase de solape de carteles (regla 22) tampoco estaba.** Nacio en la S02 y hay que
llevarlo a todo episodio nuevo: si algo NUEVO tapa mas del 25 % del area de algo que ya estaba, lo
viejo se apaga al entrar el nuevo. Apago 5 pares que se pisaban.

**4. `fondo_piloto.png` solo tiene papel en el tercio de arriba.** Es la causa concreta de lo que
Agustin marco en el ep. 06 (*"la animacion me parece muy mala"*): cualquier corte a WIDE o WALL deja
tres cuartos de madera vacia con dos objetos chicos flotando. **La vuelta es una hoja de trabajo**
—un PNG de papel de 1880x1000 con cuadricula tenue, `bg=True`, exento de los chequeos— que cubre casi
todo el cuadro. Arregla el episodio entero de una vez y no toca ninguna composicion.

**5. Los props compartidos estan dibujados para 90 px y en un cuadro de 1920 se ven como monedas.**
Hace falta un **piso de tamano en pantalla** (13,5 % del ancho de la ventana) y un techo (46 %),
aplicado en `P()` antes de `caber()`. Es la leccion del S03 al reves: en vertical habia que
achicarlos, en 16:9 hay que agrandarlos.

**6. `at(0.001, x, y)` NO fija el primer cuadro.** Ya estaba dicho para la camara (ep. 05) y vale
igual para los objetos: `Track` nace con su keyframe en t=0 y `__call__` corta con
`if t <= k[0][0]`, asi que en el instante 0 gana el valor inicial. La hoja de trabajo salia dibujada
en (0,0) y el cuadro 0 era madera. Los objetos de fondo se posicionan con `o.x = M.Track(...)`.

**7. Ojo con lo que dicen los props viejos, otra vez.** `ticket` (del S04) dice *"SINCE FEB 28 · YOU
PAID $418.82 MORE"*: es otra cifra por hogar y contradecia la verificada de este episodio (770). Y
`urna` sigue diciendo `YES` desde el ep. 02. **Antes de reusar un prop con texto, mirarlo.**

**8. Una hoja ALTA se maneja con ventanas 16:9 dentro de ella.** La geografia del 07 (Suez arriba,
Bab el-Mandeb abajo, Ormuz a la derecha) no entra en una hoja panoramica como la del ep. 06. Con
3400x2020, `MAP_S` elegido para que la hoja sea mas grande que el cuadro y **todos** los planos
siendo ventanas interiores, la hoja sangra siempre: nunca se ve mesa alrededor del mapa, y no hace
falta un plano que muestre la hoja entera.

**9. `entregar.sh` pasa rutas de git-bash a Python y ffprobe no las lee.** El paso 4 (la hoja de
uniones) hace `dur(P+'/intro_canal.mp4')` con `P=/c/Users/...`: esa forma la traduce el SHELL, no
Python, asi que desde `subprocess.run()` el archivo no existe, ffprobe devuelve vacio y el `float()`
revienta con `could not convert string to float: ''`. Solo se pierde la hoja de contacto —los cuatro
mp4 ya estan hechos—, pero conviene el helper `win()` que convierte `/c/x` en `C:/x`. Corregido en
`videos/07_petroleo_ormuz/entregar.sh`, que es de donde hay que copiarlo.

**10. El tope de subida sigue siendo el mismo y ahora importa mas.** El 14-sep Agustin pidio
*"subelo y hazlo publico inmediatamente. Usa Claude chrome"*. `file_upload` topea en **10 MB** y el
master pesa cientos de MB: **los bytes los suelta el en el selector**, y Claude hace todo lo demas
en Studio (titulo, descripcion, etiquetas, miniatura, publico, comentario fijado).

### Del ep. 08 (2026-09-14) — el motor del 07 tenia tres agujeros mas, y el cuadro se veia vacio

Dispatch armado **el mismo dia** del hecho (Agustin: *"ES PARA HOY"*), 20 min de cuerpo. Lo que se
aprendio, en orden de cuanto duele:

**1. `fuera()` mandaba SIEMPRE hacia atras, tambien a lo que nace DESPUES del bloque de acto.**
El margen `b+0.25` atrapa a la primera linea de cada acto —arranca a los 0,15 s de terminar la
transicion— y la empujaba **cinco segundos atras**, al plano del acto anterior, donde no entra. Asi
salia cortado el memorandum del acto V. Se decide por la mitad del bloque: `return a-m if t < (a+b)/2
else b+0.35`. Venia mal desde el ep. 07.

**2. La altura de caida de `drop()` puede parir el objeto FUERA del cuadro, y `caber()` no lo ve.**
Sobre un sitio que ya esta alto en la ventana —Edimburgo en el plano abierto, Tower Hamlets en el de
Londres— un `h=300` pone el nacimiento en y negativo; `caber()` calcula `dy <= 8` y **devuelve la
escala sin achicar**, asi que nadie corrige nada y el chequeo lo marca. La altura de caida se limita
al hueco que hay encima: `dh = max(6, min(dh, (y-y0-hh*0.05)*0.55))`.

**3. Una SEGUNDA geografia no puede ser un `MapSheet` —el motor dibuja una sola hoja— y hay que
apagarla a mano.** La hoja del Atlantico Sur va como capa de fondo con su propia proyeccion y sus
puntos en su `pts.json` (asi la regla 24 vale igual en las dos). Pero en los planos de mesa el
`MapSheet` se apaga solo con `mp.reveal` y **esta capa no**: se quedo de fondo en 40 de 48 cuadros
de la hoja de contacto, con "SOUTH ATLANTIC" detras de todo el episodio. Hace falta el equivalente
de `mp.reveal`: `cerrar_satl()` la apaga en el primer corte a un plano que no sea el suyo.

**4. Las escalas del ep. 07 dejan el cuadro VACIO en 16:9.** Mirando cuadros reales, un cartel o un
prop ocupaba una octava parte del cuadro y el resto era papel. No es la animacion, es la ESCALA:
props `*1.55` con piso del **18,5 %** del ancho de la ventana (era 1,28 y 13,5 %), y carteles con
piso de cuerpo **54** (era 42). Con eso hay que reajustar barras y diales, que se pasan.

**5. El rotulo de beat fijo arriba (recurso del S03) tambien vale en 16:9.** En cada plano de mesa o
pared que dure mas de 3,5 s entra el nombre del tramo arriba, atenuado. Llena el cuadro, informa, y
no toca ninguna composicion. Cien rotulos en un episodio de 20 min.

**6. `card('   ')` con espacios da una tarjeta del ancho de tres espacios.** Las doce fichas de la
votacion de los diputados escoceses salieron de 40 px. Van con texto real (`NO` / `YES`).

**7. Los sellos "vacios" no cuentan nada.** La fila de una racha electoral con recuadros en blanco
se lee como ruido; **con el anio adentro** (1999, 2003, 2007… y el ultimo con `?`) cuenta la racha y
ademas informa.

**8. Las subdivisiones del Reino Unido, dibujadas a mano, se notan.** Los poligonos lon/lat
recortados al pais (el metodo del ep. 02) dejan bordes rectos donde la frontera es sinuosa. Natural
Earth `admin_0_map_subunits` trae England/Scotland/Wales/Northern Ireland reales; recortado a esas
cuatro pesa 170 KB y queda en `fuentes/mapas/ne_10m_uk_subunits.geojson` para el proximo.

**9. Un guion de 2.700 palabras da 20 min, no 17.** El checklist avisa (objetivo 1.500-2.300) y hay
que hacerle caso ANTES de pedir la voz: con la voz hecha, recortar cuesta otra generacion. Y el
contador de oraciones largas es el que mas mejora el guion: de 18,8 palabras de media a 9,8.

**10. Dos vias para la misma voz, y solo una da timestamps.** fal.ai devuelve `timestamps` con el
flag; **PicsArt no**. Si fal se cae a mitad de produccion, la voz sale por PicsArt (mismo modelo,
misma voz por ID) y los tiempos los pone **whisper local en un minuto**
(`videos/08_reino_unido/voz_intro_tiempos.py`). Y los errores `"User is locked. Reason: TOP_UP"` y
`"Exhausted balance"` son de **fal**, no de PicsArt; tras una recarga tardan minutos en propagarse,
asi que conviene reintentar antes de dar el saldo por perdido.

**11. eleven-v3 corta por arriba de ~2.800 caracteres EN SILENCIO**: devuelve un mp3 valido con el
final faltando. `voz_ep.py::generar()` parte el beat en dos por el corte de oracion mas cercano a la
mitad y los concatena con ffmpeg; la union cae en un punto y no se oye.

**12. El interrogatorio se puede hacer EN PARALELO con la investigacion.** `AskUserQuestion` bloquea
el turno, pero en el mismo mensaje se lanzan el scraper y las primeras busquedas. En un Dispatch
"para hoy" eso son veinte minutos que no se pierden.

## 4. Ideas para mejorar (pendientes, en orden de impacto)
0. **Del análisis del día 1 (2026-09-08)**: cold open antes de la intro y pre-roll de 1 s; miniatura con ≤3 palabras y cara grande; `place(nombre)` que obliga a anclar a `mapa_pts.json` o manda a `WALL` con `OFF THE MAP →`; lint de lugares del guion en `check`; medidor de cortes/min (meta 1 cada 4-6 s) y huecos > 4 s; regiones nunca en color de agua; primer cuadro de cada short en movimiento.
1. Miniatura y título por episodio (`canal/miniatura_01.py` existe como base).
2. Bocas de 2 posiciones en Zelensky/Putin cuando se los cita; ojos que parpadean.
3. Primeros planos reales (medio cuerpo) sin violar la regla 1: recorte deliberado por diseño, a consultar con Agustín.
4. `escena.py` genérico para que el ep. 2 no copie 600 líneas de `piloto3.py`.
5. Medir horas por episodio desde el ep. 2 (el cuello de botella es tiempo, no créditos).
