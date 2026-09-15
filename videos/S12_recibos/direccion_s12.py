# -*- coding: utf-8 -*-
"""Direccion de actor de la S12 («THE RECEIPT») — VERSION 2 (2026-09-15, auditoria del motor).

La v1 (`voz_corta.py::APERTURA/TAGS`) abria las cuatro piezas con [flat…], [low…], [dry…], [low…] y
pedia "lo mas plano posible". Para un short de 90 s en el feed eso es letal: la referencia
(GeoGlobeTales, 11,9 M) narra a 189 wpm, conversacional y con humor. Aca el registro es
**alguien que te muestra un recibo y disfruta de que no lo sepas**: rapido en lo explicativo,
frio SOLO en la cifra, socarron en la vuelta de tuerca. Regla: nunca dos lineas seguidas con la
misma familia de etiqueta. Las revelaciones bajan la voz (regla del canal), lo demas sube.

`voz_corta.py` importa de aca: `from direccion_s12 import APERTURA, TAGS`.
Indices = lineas `A:` de cada `guion.md` (8, 7, 8 y 8 lineas).
"""

APERTURA = {
 0: "[curious, leaning in, a little amused]",          # El tanque
 1: "[wry, you are about to see how a machine works]", # Hormuz
 2: "[dry, an auditor who has found something]",       # Los hoteles
 3: "[quiet, intriguing, a chronology]",               # Ceuta
}

TAGS = {
 0: {                                    # El tanque (8 lineas)
   0: "[curious, a story that turned the other way — the twist first, then the number, cold]",
   1: "[faster, citing a document]",
   2: "[measured, explaining, brisk]",
   3: "[pause] [flat, one short sentence, let it land]",
   4: "[faster, wry]",
   5: "[slower, each word landing]",
   6: "[pause] [quiet, the turn]",
   7: "[warm, direct, faster, asking]",
 },
 1: {                                    # Hormuz (7 lineas)
   0: "[wry, emphasis on NOTHING, then faster on the two numbers]",
   1: "[measured]",
   2: "[pause] [wry, the reframe]",
   3: "[leaning in, faster, laying out a mechanism]",
   4: "[dry, amused]",
   5: "[pause] [slower, quiet, each word landing]",
   6: "[low, final, then warmer on the last word]",
 },
 2: {                                    # Los hoteles (8 lineas)
   0: "[amused, telling a small contradiction, emphasis on EIGHT at the end]",
   1: "[clipped, citing a document]",
   2: "[leaning in, curious, faster]",
   3: "[pause] [clipped, dry, cut off]",
   4: "[explaining, brisk]",
   5: "[flat, precise]",
   6: "[pause] [warm, direct, to camera, slower]",
   7: "[quiet, asking]",
 },
 3: {                                    # Ceuta (8 lineas)
   0: "[measured, then faster on the second sentence]",
   1: "[explaining, placing it on a map, brisk]",
   2: "[pause] [slower and precise — this sentence must not be rushed]",
   3: "[faster, a chain of events]",
   4: "[flat, stating numbers, then quiet on the last one]",
   5: "[measured]",
   6: "[pause] [slower, low, each word landing, wry on the last clause]",
   7: "[warm, direct, asking]",
 },
}
