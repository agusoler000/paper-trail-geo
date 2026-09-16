# AUDITORÍA DEL MOTOR — RESULTADO (2026-09-15) · borrador en curso

> Cierra `canal/AUDITORIA_MOTOR_2026-09-15.md` (diagnóstico + especificación). Este documento se va
> completando a medida que se verifican las piezas. **Lo que dice "verificado" lo comprobó el
> orquestador con sus propias herramientas (cuadros reales, `ritmo.py`, diff de regresión), no lo que
> informó el agente.** Lo que no se verificó está marcado.

---

## 1. Motor v4 — qué se hizo y qué se comprobó

Implementado por un agente Opus 5 sobre la especificación §6 de la auditoría. Informe del agente:
`produccion/_MOTOR_V4_INFORME.md`; manual de la API: `produccion/MOTOR_V4.md`.

| Cambio | Archivo | Verificado por el orquestador |
|---|---|---|
| `Mundo` (fondo más grande que el cuadro, capas de país, rutas, oscurecido; compone solo el recorte) | `produccion/motor.py` | ✅ código leído entero; prueba de Ceuta rendida a 1080×1920 sobre un mundo de 4000 px |
| `Scene(fondo, size, v4)`: formato por escena, `zoom < 1`, render por recorte, capa **HUD**, `subtitulos()`, `corte/viaje`, `vida` de cámara, `visible()` honesto | `produccion/motor.py` | ✅ leído; `python coreo.py check` del ep. 09 **byte a byte idéntico** antes/después (diff vacío en `produccion/_qc_regresion/`); imports OK |
| Vida de rigs y objetos (cabeza 4°, brazos 4,5°, respiración 3 %, wobble/bob por defecto solo en `v4=True`) | `produccion/motor.py` | ✅ opt-in confirmado en el código; se ve en los cuadros del jurista |
| `Track.set(0, v)` reemplaza el keyframe inicial (bug M7) | `produccion/motor.py` | ✅ |
| **Hallazgo colateral**: el motor v3 no era determinista (`Obj.phase` salía de `id()`, distinto en cada proceso del pool → salto de wobble en cada juntura de tramo, en las 12 producciones). v4: 0,000000 de diferencia entre corridas | `produccion/motor.py` | ✅ explicación coherente con el código; medición del agente (0,48/255 v3 vs 0 v4) no repetida |
| `produccion/mapa_v2.py` (biblioteca del mapa rico: `hoja_v2`, `capa_pais`, `pins`, `mundo` con caché y chequeo de la regla 24) | nuevo | ✅ mundo del Estrecho generado, error de proyección 0,006 px |
| `produccion/sync.py` (auditoría guion→imagen: VACIO, CIFRA_SIN_PANTALLA, LUGAR_SIN_MAPA, TEXTO_VIEJO, PROP_HUERFANO + hojas con un cuadro real por línea) | nuevo | ✅ leído entero; sobre el ep. 09 v1 caza **60 líneas VACIO** y el "22 cents / AND 78 CENTS"; hoja `videos/09_deuda_eeuu/_qc/sync_v1/sync_03.jpg` mirada: marca en rojo justo los cuadros de papel vacío que Agustín vio |
| `ritmo.py --json` + `veredicto()` (quietos < 20 %, mov. mediano ≥ 2,5, ningún plano > 6 s) | `produccion/ritmo.py` | ✅ |
| `shorts.py`: `cues()` con palabras reales, **`armar_vertical()`** (gancho 3,5 s, chip PART n OF N, barra, loudnorm) | `produccion/shorts.py` | ✅ cuadros reales de `_prueba_v4_armado.mp4` mirados; −15,2 LUFS |
| `voz/prosodia.py` (índice de contraste), `voz/timestamps.py` (fal → palabras, sin whisper), `voz_ep.py`/`voz_corta.py` con `timestamps: True`, `entregar.py` con `loudnorm`, `mezcla2.py` con compresor | varios | ⚠️ timestamps probados solo con JSON sintético (15/15); la primera llamada real la hace la S12 |

### Prueba de aceptación · Ceuta 25 s (vertical nativo, `videos/S12_recibos/prueba_v4.py`)

Medido por el orquestador con `ritmo.py` sobre `shorts/04_ceuta/salida/_prueba_v4.mp4`:

| | v3 (`prueba_vida.py`) | **v4** | GeoGlobeTales |
|---|---|---|---|
| quietos | 27,3 % | **11,1 %** | 10,7 % |
| movimiento medio | 6,97 | **8,89** | 9,22 |
| movimiento mediano | 2,03 | **4,57** | 6,92 |
| plano más largo sin cambio | 6,0 s | **4,75 s** | 4,8 s |
| `check_framing` | — | 0 | — |
| `sync.py` VACIO | — | 0 | — |

**En ritmo, la prueba está en la liga de la referencia.** Cuadros reales: `shorts/04_ceuta/salida/_aud/hoja_real.jpg`.

### Lo que el orquestador rechazó de la prueba (corregido en la producción, no en el motor)

1. **Planos de "mesa" = hoja rayada a pantalla completa** (5 de 12 cuadros): es el look que Agustín
   rechazó el 15-sep. Regla para la producción: MESA = mundo oscurecido + el documento grande + dos o
   tres props de escritorio; el documento es el papel, no hace falta una hoja debajo.
2. **Al pintar Marruecos, la península de Ceuta quedaba verde** (Natural Earth 50m no separa el
   enclave): el mapa afirmaba lo contrario que el guion. Regla: Ceuta con el color de España por
   encima (NE 10m subunits) o Marruecos sin pintar.
3. El gancho de 3,5 s no puede caer sobre un documento: va sobre el mapa en movimiento.

### Pendiente de motor (anotado por el agente, aceptado)

- `CIFRA_SIN_PANTALLA` lee el nombre del objeto, no sus píxeles: una cifra dibujada dentro de un prop
  da falso positivo (se resuelve nombrando el objeto `cifra:<valor>`).
- `MapSheet` no se tocó: las producciones viejas siguen redibujando la hoja entera; la ganancia de
  rendimiento solo la ve quien usa `Mundo`.
- `set_v4(True)` deja el flag de módulo encendido en el proceso; solo importa si en el mismo proceso
  se construye después una escena vieja.

## 2. Voz — línea de base medida (`voz/prosodia.py` sobre la voz vieja del ep. 09)

Tono mediana 131,8 Hz; rango global 8,81 st pero **entre frases 0,99 st**; energía con **3,5 dB** de
rango; 158,7 wpm; 10,5 palabras por línea. Contraste 68,1/100. Es decir: George tiene rango dentro de
la frase, pero todas las frases arrancan y terminan a la misma altura y al mismo volumen. Eso es la
monotonía, y es consecuencia de la dirección (54 de 62 etiquetas `flat/measured/quiet/low/dry`).
La dirección v2 (`videos/09_deuda_eeuu/direccion.py`, `videos/S12_recibos/direccion_s12.py`) aplica la
regla de contraste.

### 2.1 Lo que se midió con la voz nueva (S12) — y lo que cambia el plan

Medición justa, por ventanas de 1 s (`scratchpad/prosodia_cmp.py`: mediana de f0 por segundo en
semitonos, movimiento tonal = media de |Δ| entre segundos, energía por segundo, pausas ≥ 0,25 s por
minuto detectadas en el audio), sobre la misma pieza (Ceuta, 75-80 s):

| clip | mov. tonal st/s | p10-p90 tono st | rango energía dB | pausas/min |
|---|---|---|---|---|
| ep. 09 v1 (voz vieja, George) | 2,5-2,8 | 5,0-5,6 | 5,1-6,8 | 21-22 |
| S12 nueva, George 0,5, dirección v2 | 2,7-3,2 | 5,0-6,1 | 5,3-6,5 | 18-21 |
| S12 Ceuta, George **creative (0,0)** | 2,5 | 4,6 | 5,9 | 19,5 |
| S12 Ceuta, **Brian** 0,5 | **3,85** | **7,1** | 4,8 | 20,6 |
| **Referencia GeoGlobeTales** (voz + música) | **4,81** | **10,1** | 3,6 | **3,0** |

Conclusiones, en orden de importancia:

1. **Las etiquetas de dirección no mueven la aguja.** La voz nueva con dirección de contraste se mueve
   igual que la vieja. La v3 de ElevenLabs las toma como sugerencia, no como instrucción.
2. **La diferencia con la referencia está en las pausas y en la voz, no en la dirección.** Ellos: 3
   pausas por minuto. Nosotros: 20, de 0,8 s de media — **el 25 % del clip es silencio**. Eso es el
   metrónomo que se oye como monotonía.
3. **`stability 0,0` (creative) no ayuda de forma fiable** (en esta muestra salió peor). Se descarta
   para producción: más riesgo de alucinación por nada.
4. **Brian se mueve un 22 % más que George** (3,85 contra 3,15 st/s) y es más grave (96 Hz contra
   134). Es la única palanca de generación que acerca a la referencia. **Cambiar la voz es identidad
   del canal: lo decide Agustín**; se le mandaron las cuatro muestras al móvil (A George, B creative,
   C Brian, D George compactada).
5. **Trampa nueva y grave: eleven-v3 LEE EN VOZ ALTA las etiquetas de apertura largas.** Medido por
   el agente de la S12: la de la pieza 1 se llevó 4,96 s de audio hablado. Solución en `voz_corta.py`
   (se corta hasta la primera palabra del guion con los timestamps) y regla: apertura ≤ 3 palabras,
   inline ≤ 6. `direccion.py` del ep. 09 ya está acortada.
6. **Herramienta nueva: `voz/compactar.py`** — acorta las pausas por su cola (normales a 0,45 s,
   dramáticas ≥ 1 s a 0,80 s, tramos protegidos para los bloques de acto) y reescribe `_palabras.json`
   y `tiempos.json` con la misma función. Ceuta: 80 → 72 s; las palabras siguen sobre voz (184/188
   contra 175/188 antes). Es la vía de post-proceso que pedía la auditoría y **va en la S12 y en el
   ep. 09**. No sustituye la decisión sobre la voz.

## 3. YouTube Studio (15-sep) — lo que cambia en la producción

Informe completo: `canal/ANALISIS_STUDIO_2026-09-15.md` (agente Sonnet, lectura directa de Studio).

- **La caída fuerte de retención de los largos está entre el segundo 10 y el 25** (AfD −27 pp, 11-S
  −19 pp, IA −28,5 pp, Malvinas −29 pp): la ventana de la intro de preguntas + intro general. → La
  intro de preguntas del ep. 09 pasa a ≤ 12 s, con el mundo en movimiento desde el cuadro 0
  (`videos/09_deuda_eeuu/PLAN_VISUAL_V4.md` §3.b). El orden alternativo "cold open primero" queda
  anotado como A/B para Agustín.
- **Shorts: historia con giro retiene 40-59 %, cifra sola 8-18 %.** → Las líneas 0 de las piezas 1-3
  de la S12 se reordenaron (giro primero, mismos datos y fuentes).
- CTR sigue en ~1,2 % en 5 de 7 largos: el empaquetado (título + miniatura) sigue siendo el techo
  de entrada y no lo resuelve el motor; los largos convierten a suscriptor ~9× mejor que los shorts
  por vista.

## 4. Shorts S12 — auditoría pieza por pieza (el orquestador, sobre el mp4 final)

### Pieza 4 · THE PAPER THAT MOVED 49,000 (Ceuta) — ✅ aceptada con dos correcciones menores

`videos/S12_recibos/shorts/04_ceuta/salida/04_ceuta.mp4` · 75,5 s · 1080×1920 · 32 MB · copia móvil
`04_ceuta_movil.mp4` (8,9 MB, enviada a Agustín a las 18:55).

| Medido por el orquestador | Valor |
|---|---|
| `ritmo.py` quietos / mov. medio / mov. mediano / plano más largo | **2,7 %** / **7,02** / 4,26 / 4,5 s → PASS |
| loudness | −15,0 LUFS, LRA 2,0 |
| sync (agente, verificado en la hoja) | VACIO 0 · CIFRA 0 · LUGAR 0 · TEXTO_VIEJO 0 |
| voz | George 0,5, timestamps de fal, pausas compactadas 80,0 → 73,1 s |
| cuadros reales mirados | 16 (`salida/_aud/final_hoja.jpg`) + lado a lado con la referencia (`_aud/lado_a_lado.jpg`) |

Lo que se ve bien: mapa a sangre todo el tiempo; Ceuta en azul sobre Marruecos naranja (NE 10m
subunits, la corrección pedida); el documento sobre el mapa oscurecido con props de escritorio (sin
hoja rayada); la ruta roja rodeando el extremo de la valla; cifras grandes; gancho 3,5 s sobre el
mapa en movimiento; chip PART 4 OF 4; cierre con like/suscripción.

Lo que NO pasa la auditoría y va a la pasada de corrección:
1. **Regla 22**: a los 37 s la tarjeta `THE ORDINARY PROCEDURE` tapa la fecha del documento.
2. **Falta el rig**: el plan pedía el jurista de pie sobre el mapa señalando; no aparece en ningún
   cuadro. Sin personaje, el corte de 24-37 s (documento + tarjetas) es el tramo más "cartel" de la pieza.
3. Rojo: hay hasta tres rojos por cuadro (pin, ruta, cifra). Se anota; no bloquea.

### Piezas 1-3 · primera pasada (20:12-20:23) — auditadas sobre los mp4 finales, 16 cuadros reales cada una

| Pieza | `ritmo.py` | Veredicto del orquestador | Por qué |
|---|---|---|---|
| 1 · El tanque (75 s) | quietos 4,0 % · mov. 5,41 · PASS | **NO pasa** | 9 de 16 cuadros son mar vacío con un pin (el bbox del Golfo es casi todo agua y la costa corre por el borde superior); documentos placeholder (`REPORT`, `DECREE`); el depósito gris viejo; el burócrata no aparece en ningún cuadro muestreado |
| 2 · Hormuz (66 s) | quietos 5,3 % · mov. 8,03 · 31,6 cortes/min · PASS | ✅ con retoques | Irán se pinta de rojo al decir "uninsurable", los 12 petroleros, el ejecutivo de pie sobre Omán; sobra un `REPORT` genérico y el barril se lee como mancha |
| 3 · Hoteles (71 s) | quietos 5,3 % · mov. 5,76 · **FAIL** (un plano de 6,2 s) | **NO pasa** | **`LEASE 99 YEARS` en pantalla mientras la voz dice "same ten years"** (prop inventado: los contratos son de 10 años, F3.5) — el error guion→imagen que esta auditoría existe para impedir; `£8M A DAY` tapa el título del libro mayor; las barras 76/35 casi no se ven; la torre es chica en medio del mar |

### Piezas 1-4 · segunda pasada (23:05-23:19) — ✅ las cuatro aceptadas y enviadas a Agustín (23:15)

| Pieza | Duración | `ritmo.py` (medido por el orquestador) | sync | Qué se corrigió |
|---|---|---|---|---|
| 1 · El tanque | 71,9 s | quietos **0,3 %** · mov. 6,18 · PASS | VACIO 0 · CIFRA 0 | bbox con tierra en el cuadro; documentos con nombre (EIA · Weekly Petroleum Status Report · 4-sep); el tanque dibujado con escala; el burócrata sobre Texas |
| 2 · Hormuz | 66,5 s | quietos 4,9 % · mov. **8,21** · 32,5 cortes/min · PASS | VACIO 0 · CIFRA 0 | póliza con su título real (War-risk insurance · Hormuz transit · 7,5-10 % of hull); barril con etiqueta CRUDE |
| 3 · Hoteles | 71,5 s | quietos 4,9 % · mov. 6,01 · PASS | VACIO 0 · CIFRA 0 | **`LEASE 99 YEARS` eliminado**: contrato `2019-2029 · TEN YEARS · £4.5bn` + sello SAME CONTRACT; `£8M A DAY` fuera del libro mayor; torre y barras 76/35 grandes |
| 4 · Ceuta | 75,5 s | quietos 2,7 % · mov. 7,02 · PASS | VACIO 0 · CIFRA 0 | tarjetas separadas de la sentencia; el jurista visible (chico) |

Lo que queda para la pasada del compositor, no bloqueante: en la 1 la tarjeta `11 MARCH` roza al
burócrata (35 s); en la 4 `THE ORDINARY PROCEDURE` toca el borde inferior de la sentencia (36-38 s) y
el jurista es pequeño; los rótulos de países en el mapa son bg y a veces quedan cortados por el borde
(normal en un mapa). Copias para móvil (`*_movil.mp4`, 8,5-9,6 MB) enviadas.

**Lo que esto enseña, y ya está pedido al compositor** (`produccion/compo.py`, en construcción): (a) `sync.py`
no lee el texto horneado en un prop — hace falta `TEXTO_NO_DICHO`: todo texto en pantalla se declara y
se cruza contra el guion y la hoja de fuentes; (b) `TIERRA_EN_CUADRO`: un plano de mapa tiene que
tener ≥ 40 % de tierra o contenido en la ventana, y el compositor elige centro y zoom para cumplirlo;
(c) `PERSONAJE` visible ≥ 6 s de pie sobre tierra, medido. La lista de correcciones (15 puntos) se
mandó al agente de la S12 a las 20:35; las piezas se re-renderizan y se vuelven a auditar.

## 5. Ep. 09 — (pendiente, después de los shorts)

## 6. Pendientes y evaluación contra el benchmark — (al final)
