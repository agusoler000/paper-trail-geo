# -*- coding: utf-8 -*-
"""Direccion de actor de la S13 («FOUR LINES», 2026-09-16).

Hereda las dos lecciones medidas en la S12 (15-sep):
  1. eleven-v3 LEE EN VOZ ALTA las etiquetas de apertura largas (4,96 s y 4,60 s de audio a nivel
     de habla en las piezas 1 y 3). Lo dispara la LONGITUD. Regla de la skill §2.14: apertura
     <= 3 palabras, en linea <= 6.
  2. «Las etiquetas no mueven el tono» (memoria `reference-voz-medida-2026-09-15`): lo que si hacen
     es poner pausas y cambiar el ritmo. Por eso se usan sobre todo para [pause] y velocidad, no
     para pedir emociones finas.

El registro de la serie: **alguien que se dio cuenta de donde esta la accion de verdad y te lo
muestra sin levantar la voz.** Rapido en la cronologia, frio en la cifra, bajo en la conclusion
(regla del canal: tension = bajar la voz, no subirla). Nunca dos lineas seguidas con la misma
familia de etiqueta.

Registro por pieza:
  - 01 · La refineria. Un parte que se da vuelta. Brisk en los ataques, FRIO en «half», bajo en
    «one refinery at a time».
  - 02 · El voto. Registro mesurado y preciso; las citas se leen como citas, neutras.
    Consultar las decisiones editoriales en el documento privado local `postura.md`.
  - 03 · La fecha. Un ajedrecista explicando una jugada. Socarron en «grey ships instead of grey
    hulls».
  - 04 · La subasta. Un auditor. Seco, y la division de las dos cifras (linea 6) lenta.

`voz_corta.py` importa de aca: `from direccion_s13 import APERTURA, TAGS`.
Indices = lineas `**A:**` de cada `guion.md` v2 (17, 16, 13 y 14 lineas). `tests()` lo comprueba.
"""

APERTURA = {
 0: "[curious, leaning in]",
 1: "[measured, precise]",
 2: "[quiet, intriguing]",
 3: "[dry, wry]",
}

TAGS = {
 0: {                                   # 01 · Three of the six (17 lineas)
   1: "[pause] [flat, let it land]",
   2: "[faster, the turn]",
   3: "[pause] [quiet]",
   4: "[brisk, reporting]",
   5: "[measured]",
   6: "[leaning in, explaining]",
   7: "[faster, a list]",
   8: "[pause] [slower, cold]",
   9: "[explaining, brisk]",
   10: "[flat, precise]",
   11: "[pause] [dry]",
   12: "[measured]",
   13: "[pause] [low, certain]",
   14: "[slower, each word landing]",
   15: "[quiet, final]",
   16: "[warm, direct, asking]",
 },
 1: {                                   # 02 · One vote (16 lineas)
   1: "[flat, stating numbers]",
   2: "[firm, matter of fact]",
   3: "[pause] [quiet]",
   4: "[faster, a chain of events]",
   5: "[slower, careful]",
   6: "[pause] [low, each word landing]",
   7: "[neutral, citing]",
   8: "[precise, quoting]",
   9: "[pause] [leaning in]",
   10: "[slower, dry]",
   11: "[pause] [calm, direct]",
   12: "[deliberate]",
   13: "[quiet]",
   14: "[low, final]",
   15: "[warm, asking]",
 },
 2: {                                   # 03 · A date instead of a landing (13 lineas)
   1: "[wry]",
   2: "[explaining, brisk]",
   3: "[slower, precise]",
   4: "[flat]",
   5: "[leaning in]",
   6: "[measured]",
   7: "[faster, reporting]",
   8: "[pause] [dry, amused]",
   9: "[pause] [curious, then certain]",
   10: "[slower, precise]",
   11: "[quiet, final]",
   12: "[direct, asking]",
 },
 3: {                                   # 04 · Britain lost an auction (14 lineas)
   1: "[brisk, citing a document]",
   2: "[pause] [slower, cold]",
   3: "[measured]",
   4: "[faster]",
   5: "[pause] [explaining]",
   6: "[measured]",
   7: "[flat, precise]",
   8: "[pause] [slower, each word landing]",
   9: "[measured]",
   10: "[pause] [low, certain]",
   11: "[slower]",
   12: "[quiet, final]",
   13: "[warm, asking]",
 },
}

LINEAS = {0: 17, 1: 16, 2: 13, 3: 14}


def tests():
    import re
    for n, ap in APERTURA.items():
        pal = len(re.findall(r"[a-zA-Z']+", ap))
        assert pal <= 3, 'apertura %d tiene %d palabras (max 3): %s' % (n, pal, ap)
    for n, d in TAGS.items():
        assert max(d) < LINEAS[n], 'pieza %d: etiqueta en linea %d y solo hay %d' % (n, max(d), LINEAS[n])
        for i, t in d.items():
            for grupo in re.findall(r'\[([^\]]+)\]', t):
                pal = len(re.findall(r"[a-zA-Z']+", grupo))
                assert pal <= 6, 'pieza %d linea %d: %d palabras (max 6): %s' % (n, i, pal, grupo)
        claves = sorted(d)
        for a, b in zip(claves, claves[1:]):
            fa = d[a].split(']')[-2].split('[')[-1].split(',')[0].strip()
            fb = d[b].split(']')[-2].split('[')[-1].split(',')[0].strip()
            assert not (b == a + 1 and fa == fb), \
                'pieza %d: lineas %d y %d con la misma familia "%s"' % (n, a, b, fa)
    print('direccion_s13: OK (aperturas <= 3 palabras, en linea <= 6, sin familias repetidas seguidas)')


if __name__ == '__main__':
    tests()
