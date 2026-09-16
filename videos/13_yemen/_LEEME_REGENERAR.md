# Ep. 13 Yemen — regenerar el video en otra maquina

Este paquete trae **todo**: codigo, guion, fuentes, la voz ya generada y el arte ya renderizado.
No hay que gastar un solo credito ni volver a correr whisper.

Lo unico que **no** viene son los 22.412 cuadros sueltos (7,3 GB) y los masters (1,5 GB): son el
**resultado** del render, no su entrada.

---

## 0. Preparar

Descomprimir **sobre la raiz del repo**, respetando rutas: todo cuelga de `videos/13_yemen/`.

Hace falta, ya en el repo:
- Los assets del canal desempaquetados: `pruebas/elenco/`, `produccion/assets/`,
  `produccion/musica/`, `produccion/intro_v3/intro_canal_v3.mp4`, `produccion/outro_canal.mp4`.
- **ffmpeg** en el PATH.
- El codigo del episodio ya esta en git (commit `64e76fd`), pero viene aqui tambien por si acaso.

Dependencias (un venv aparte vale):

    pip install numpy pillow shapely soundfile faster-whisper

**Georgia Pro** es de pago. Si no esta, `produccion/props.py` cae solo a Georgia normal y lo avisa
por consola. Donde Georgia Pro si esta, no cambia nada.

---

## 1. Chequeos (los tres tienen que dar 0)

Se puede ir directo al render, pero esto tarda 2 minutos y es lo que evita un render tirado:

    python videos/13_yemen/coreo13.py check     # encuadre 0 · cortes flojos 0 · anclas 0
    python videos/13_yemen/coreo13.py sync      # VACIO = 0
    python videos/13_yemen/coreo13.py hoja      # 12 cuadros reales -> _hoja.jpg: MIRARLOS (regla 10)

## 2. Render (~25 min)

    python videos/13_yemen/coreo13.py render

**`coreo13.WORKERS = 5` esta puesto a proposito.** El automatico del motor (nucleos - 2 = 14) pide
~19 GB con este mundo de 9000x7697 y el render muere con MemoryError a mitad. Si la otra maquina
tiene mas RAM, se puede subir; si tiene menos de 16 GB, bajarlo.

Sale `salida/cuerpo.mp4` (15:33) con la voz ya pegada.

## 3. Entrega final

    python produccion/entregar.py videos/13_yemen/salida/cuerpo.mp4 ^
        videos/13_yemen/salida/PaperTrail_13_Yemen_1080p.mp4 ^
        --intro_at 19.9 --audio videos/13_yemen/audio/13_yemen_mezcla.wav

Da el 1080p y un 720p. Resultado esperado: **16:06** = intro v3 (12,5 s) + cuerpo (15:33) + outro (20 s),
con la intro metida a los 19,9 s, justo entre las preguntas y el cold open (regla 4).

---

## Si hiciera falta rehacer algo

**El arte** (viene hecho; solo si se pierde):

    python videos/13_yemen/arte/mapa.py --force      # mundo 9000x7697 + 4 capas + pins
    python videos/13_yemen/arte/props13.py --force   # los 8 props propios del episodio

**El audio** (viene hecho; `alinear13.py` corre whisper y tarda ~10 min, los demas son instantaneos):

    python videos/13_yemen/audio/alinear13.py        # mp3 -> wav + tiempos + palabras  (SOLO si se pierden)
    python videos/13_yemen/audio/actos13.py          # mete los 5 bloques de acto y desplaza tiempos
    python videos/13_yemen/coreo13.py eventos        # _eventos.json para la mezcla
    python produccion/mezcla2.py videos/13_yemen/audio/13_yemen_cuerpo.wav ^
        videos/13_yemen/_eventos.json ^
        videos/13_yemen/audio/13_yemen_cuerpo.tiempos.json ^
        videos/13_yemen/audio/13_yemen_mezcla.wav

**Las miniaturas** (vienen hechas):

    python videos/13_yemen/publicar/miniaturas13.py

Ojo: `canal/marca.py` abre `pruebas/look/mapa_hoja.png` al importarse. Si falta, se reconstruye
copiando `produccion/assets/mapa_base.png` a esa ruta (es una textura de fondo, no contenido).

---

## Lo que quedo pendiente

- **`ritmo.py` da 2 de 3**: un tramo de 6,75 s sin cambio en t=496-503 (entrada del ACT III) contra
  un limite de 6,0. Medido cuadro a cuadro, el corte **si** existe; lo que pasa es que el zoom se
  mueve tan parejo alrededor (diferencias de 10-11 sobre un umbral de 12) que la medicion no lo
  separa del movimiento de fondo. Las otras dos pasan con holgura. **Agustin decidio dejarlo asi**
  el 16-sep.
- **En 4:41 la cifra "4.9" se solapa con el grafico de barriles** y tapa el 9.3. Se arregla moviendo
  el `fx` de esa `d.cifra` en `partitura13.py::b05`.
- Los **4 shorts** tienen guion (`shorts/GUIONES.md`) pero **no estan producidos**: falta voz,
  coreografia vertical 1080x1920 y miniatura propia de cada pieza.

Las dos primeras se arreglan en una sola pasada de render (~25 min).

---

## Las tres trampas que costaron esta produccion

Estan comentadas en el codigo donde ocurren, pero conviene tenerlas a mano:

1. **Props del catalogo con texto de otros episodios.** `expediente` dice "MALVINAS FALKLANDS",
   `isla_recorte` es la silueta de las Malvinas, `diario_1` habla de aerolineas rusas y `factura`
   lleva el simbolo euro. Por eso existe `arte/props13.py`: 8 props propios por codigo, 0 creditos.
2. **Los pines del mapa se dimensionan contra el MUNDO, no contra la ventana.** Con 9000 px de ancho
   el automatico da r=37 y texto de 130, que en plano cerrado son discos de 190 px en pantalla.
   Y `pins_opciones` es **por sitio** (`{nombre: {...}}`), no global: un `{'r': 13}` suelto se lee
   como un sitio llamado "r" y se ignora en silencio.
3. **Un plano por grupo de lineas deja el video muerto.** 51 planos para 934 s daban FAIL en las tres
   pruebas de `ritmo.py`. `Dir.plano()` trocea en tramos de 4,4 s; los planos de MESA tambien llevan
   camara (si no, la pantalla se congela mientras el documento esta quieto); y en planos abiertos,
   donde el mundo ya llena el cuadro y la camara se sujeta contra el borde, **el corte se hace con
   la ESCALA**, no con el desplazamiento.

Todo el detalle editorial esta en `README.md`, `postura.md` y `publicar/SUBIR_13.md`.
