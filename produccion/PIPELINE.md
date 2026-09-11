# Pipeline de producción del video (2026-09-03)

Todo corre en esta PC, en CPU, a 0 créditos salvo los personajes nuevos (1 crédito c/u en Flux).

```
guiones/<video>/guion.md          ← guion en dos columnas (A: audio, V: video), ESTILO.md §3
      │  python guiones/checklist.py guiones/<video>/guion.md
      ▼
voz/voz.py --voz am_onyx          ← Kokoro CPU, ~1 s de proceso por segundo de audio
      │  produccion/audio/<video>_am_onyx.wav + .tiempos.json (inicio/fin de cada frase)
      ▼
produccion/mapa_rusia.py          ← hoja de mapa por capas (Natural Earth 50m)
produccion/props.py               ← objetos de papel (49 PNG con alpha, texto con Georgia Pro)
pruebas/elenco/cortador.py        ← rigs (cabeza, torso, 2 brazos × 2 segmentos) por personaje
      ▼
produccion/motor.py               ← motor: Track/Obj/Rig/MapSheet/Scene + render paralelo (22 CPU)
produccion/piloto.py              ← coreografía del piloto: cada fila V: del guion → acciones en el tiempo
                                     de su frase (L(beat,linea) / E(beat,linea))
      │  python piloto.py  →  produccion/01_aviacion_rusa.mp4  (1080p, 24 fps, audio AAC)
      │  python piloto.py 120 150  → solo un tramo, para revisar
      ▼
```

Medidas (2026-09-03): build de la escena 3,4 s; ~0,9 s por frame en un núcleo; 20 workers.
Con tiempos estimados (`audio/_tiempos_estimado.json`, `TIEMPOS=...`) se puede probar la coreografía
antes de tener la voz.

Pendiente para el video 2: `escena.py`, el traductor que lea las filas `V:` y genere la coreografía
sin escribirla a mano (hoy `piloto.py` es la traducción manual del guion 1; sirve de corpus).

## Paso final obligatorio (regla de Agustín 2026-09-07): intro + cuerpo + outro
Todo episodio se entrega con la intro del canal al principio y la outro al final, sin excepción:

    python produccion/entregar.py <cuerpo.mp4> <salida.mp4> [--audio mezcla.wav] [--head tramo.mp4 --head_dur 8]

Genera `<salida>.mp4` (1080p) y `<salida>_720p.mp4` (<30 MB). `--audio` reemplaza la pista del cuerpo por una mezcla
nueva (remezclar no exige re-render); `--head` reemplaza los primeros N segundos por un tramo re-renderizado
(`python piloto3.py 0 8`). Antes de renderizar: `python piloto3.py check` debe dar 0 violaciones de encuadre.
