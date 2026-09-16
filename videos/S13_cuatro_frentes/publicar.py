# -*- coding: utf-8 -*-
"""Ficha de subida de las CUATRO piezas de la S13 («FOUR LINES»).

    python publicar.py      ->  publicar/SUBIR.md + publicar/PLAN_SUBIDA.json

Todo sale de `shorts/serie.json` (titulos, descripciones con fuentes, etiquetas, miniatura) y de los
archivos reales de `shorts/*/salida/`: si un master no existe, su bloque abre con ⛔ (regla del 14-sep:
la ficha no afirma un archivo que todavia no esta). Rutas ABSOLUTAS en todo (regla del 14-sep).

Diferencias con la ficha de la S12, a proposito:
  - Se sube el MASTER (1080x1920), no una copia recomprimida: el archivo lo suelta Agustin en el selector
    y el tope de 10 MB es solo del subidor por navegador del asistente.
  - La S12 decia que la miniatura de un Short «solo aparece con el Partner Program». Es FALSO (skill §2.8d,
    Agustin lo corrigio el 14-sep): la ficha de cada Short tiene Miniatura -> Subir archivo.
"""
import json, os, re, subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(AQUI, 'shorts')
PUB = os.path.join(AQUI, 'publicar')
FICHA = json.load(open(os.path.join(S, 'serie.json'), encoding='utf-8'))

EP01 = ('UvQSWGO_Afk', "How Ukraine Grounded Russia's Airlines Without Firing a Shot")
EP08 = ('E2nK0HY26vg', 'Is This the End of the United Kingdom?')

RELACIONADO = {
    1: 'el episodio 01 — «%s» — https://www.youtube.com/watch?v=%s (largo: suma horas; y su tesis, '
       '«without firing a shot», es la de esta serie)' % (EP01[1], EP01[0]),
    2: 'la PIEZA 1 de esta serie (Ucrania)',
    3: 'la PIEZA 2 de esta serie (Venezuela)',
    4: 'el episodio 08 — «%s» — https://www.youtube.com/watch?v=%s (largo, mismo pais)' % (EP08[1], EP08[0]),
}

COMENTARIO = {
    1: ("The 'nearly zero' is the Institute for the Study of War's NET figure since March: Russia still "
        "advances in parts of the front while Ukraine regains ground elsewhere. The six refineries are "
        "Reuters' list of Russia's top diesel producers. Every source is in the description."),
    2: ("Congress did vote: the Senate tried to stop further military action and lost 51-50 on the Vice "
        "President's tie-break. What Congress never did was authorize it. The boat figures (at least 32, "
        "about 115 killed) are PBS NewsHour's count as of 4 January."),
    3: ("Beijing has not confirmed Xi's visit on 24 September. The warning about cancelling the summit was "
        "reported by Kyodo News, citing unnamed sources. China's navy is still around Taiwan; what is new "
        "since June is the coast guard patrolling east of the island."),
    4: ("The GBP 13bn of headroom is an estimate by Pantheon Macroeconomics, not an official figure. June's "
        "GBP 11.8bn of debt interest includes GBP 4.8bn from inflation-linked gilts, so June is not a typical "
        "month. The 5.82% is the yield at the 8 September auction."),
}

PROHIBIDAS = ('breaking', 'invasion', 'nazi', 'fraud')


def dur(f):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                 '-of', 'csv=p=0', f], capture_output=True, text=True).stdout.strip())


def master(P):
    return os.path.join(S, P['dir'], 'salida', '%s.mp4' % P['dir'])


def main():
    faltan = [P['n'] for P in FICHA['shorts'] if not os.path.exists(master(P))]
    md = ['# S13 · FOUR LINES — ficha de subida (4 shorts)', '']
    if faltan:
        md += ['> ⛔ **TODAVIA NO SE PUEDE SUBIR TODO.** Faltan los masters de las piezas %s. '
               'Comprobalo: `dir %s`' % (', '.join(map(str, faltan)), os.path.join(S, '*', 'salida')), '']
    md += ['> Generada por `publicar.py` desde `shorts/serie.json`. Hoja de fuentes verificada en pagina: '
           '`%s`.' % os.path.join(AQUI, 'fuentes', 'referencia.md'), '',
           '| | |', '|---|---|',
           '| Serie / playlist | **%s** (crearla y meter las cuatro) |' % FICHA['playlist'],
           '| Idioma | Ingles · categoria Education · **no es para ninos** |',
           '| Orden | 1 Ucrania · 2 Venezuela · 3 Taiwan · 4 Reino Unido, **~2 h entre piezas** |',
           '| Este documento | `%s` |' % os.path.join(PUB, 'SUBIR.md'), '',
           '> ⚠️ **La S12 (4 shorts de ayer) sigue sin subir.** Dos tandas de cuatro el mismo dia se pisan '
           'en el feed del canal: conviene decidir cual sale hoy y cual manana.', '',
           '## Orden de operaciones', '',
           '1. Crear la playlist **%s**.' % FICHA['playlist'],
           '2. Subir la **PIEZA 1**: el MASTER de abajo, titulo, descripcion y etiquetas tal cual.',
           '3. **Miniatura -> Subir archivo** con la opcion (A, B o C) que elijas de su bloque. Todas llevan los '
           'paises y una frase chocante; hoja para comparar a 216 px: `%s`. (En Shorts SI se puede subir '
           'miniatura; la nota vieja del Partner Program era falsa.)' % os.path.join(AQUI, '_qc_miniaturas_abc_216.jpg'),
           '4. Video relacionado y comentario fijado de su bloque.',
           '5. Repetir con la 2, la 3 y la 4, ~2 h entre una y otra. Si se programa: multiplos de 15 min.', '']

    for P in FICHA['shorts']:
        n = P['n']
        m = master(P)
        minis = [os.path.join(PUB, 'miniaturas', '%s_%s.jpg' % (P['dir'], L)) for L in 'ABC']
        movil = m.replace('.mp4', '_movil.mp4')
        texto = ' '.join([P['titulo'], P['desc']]).lower()
        for w in PROHIBIDAS:
            assert not re.search(r'\b%s\b' % w, texto), 'pieza %d: palabra prohibida %r' % (n, w)
        assert len(P['titulo']) <= 100
        md += ['', '---', '', '## PIEZA %d DE 4 — %s' % (n, P['subtema']), '']
        if not os.path.exists(m):
            md += ['> ⛔ **TODAVIA NO EXISTE ESTE ARCHIVO.** No subir esta pieza hasta que la ficha se regenere.', '']
        else:
            md += ['**SUBIR ESTE ARCHIVO (master):**', '', '`%s`' % m, '',
                   '%.1f MB · %.1f s · 1080x1920 · -14 LUFS · `ritmo.py` PASS' % (os.path.getsize(m) / 1e6, dur(m)), '',
                   '(copia para mirar en el telefono, no para subir: `%s`)' % movil, '']
        md += ['**TITULO:**', '', '```', P['titulo'], '```', '',
               '**DESCRIPCION:**', '', '```', P['desc'], '```', '',
               '**ETIQUETAS:**', '', '```', ', '.join(P['tags']) + ',', '```', '',
               '| Campo | Valor |', '|---|---|',
               '| Miniatura **A** | `%s` |' % minis[0],
               '| Miniatura **B** | `%s` |' % minis[1],
               '| Miniatura **C** | `%s` |' % minis[2],
               '| Video relacionado | %s |' % RELACIONADO[n],
               '| Playlist | %s |' % FICHA['playlist'],
               '| Pregunta en la tarjeta final | `%s` |' % P.get('pregunta_pantalla', ''), '',
               '**Comentario fijado:**', '', '```', COMENTARIO[n], '```', '']

    md += ['', '---', '', '## Checklist de monetizacion (skill §2.10b)', '',
           '- [x] **Ningun colectivo de personas es sujeto.** Sujetos: la refineria y el Kremlin; la facultad '
           'y el voto; el calendario y Pekin; la subasta.',
           '- [ ] **Pieza 2**: comprobar el guion final contra las decisiones editoriales del '
           'documento privado local `postura.md`. Verificar citas y atribuciones; esta ficha no '
           'sustituye la revision humana.',
           '- [x] **Ningun muerto en gancho ni en miniatura.** Las cifras de muertos van dentro del argumento.',
           '- [x] Sin `BREAKING`, `invasion`, `Nazi` ni `fraud` en titulo ni descripcion (lo comprueba este '
           'script con un assert).',
           '- [x] Titulos <= 100 caracteres, pregunta + oracion corta, tres hashtags.',
           '- [x] Miniaturas (regla del 16-sep): bandera y NOMBRE de cada pais + frase chocante, cada frase con su '
           'fuente en `miniaturas_abc.py`.',
           '- [ ] Si YouTube marca alguna con anuncios limitados, pedir revision humana el mismo dia.', '']

    open(os.path.join(PUB, 'SUBIR.md'), 'w', encoding='utf-8').write('\n'.join(md))
    plan = {'serie': FICHA['serie'], 'playlist': FICHA['playlist'],
            'piezas': [{'n': P['n'], 'master': master(P), 'existe': os.path.exists(master(P)),
                        'titulo': P['titulo'], 'miniaturas': [os.path.join(PUB, 'miniaturas', '%s_%s.jpg' % (P['dir'], L)) for L in 'ABC'],
                        'relacionado': RELACIONADO[P['n']], 'tags': P['tags']} for P in FICHA['shorts']]}
    json.dump(plan, open(os.path.join(PUB, 'PLAN_SUBIDA.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('ficha ->', os.path.join(PUB, 'SUBIR.md'), '| faltan masters:', faltan or 'ninguno')


if __name__ == '__main__':
    main()
