# -*- coding: utf-8 -*-
"""Deja la ficha de subida de las CUATRO piezas de la S12 y las copias livianas para Studio.

    python publicar.py      ->  publicar/SUBIR.md + publicar/PLAN_SUBIDA.json + publicar/_up/*.mp4

Lo que se entrega es la ficha completa: **ruta absoluta** de cada archivo (regla del 14-sep), titulo,
descripcion para copiar tal cual con TODAS las fuentes, etiquetas, miniatura, video relacionado,
la pregunta del cierre y el checklist de monetizacion. Se manda por chat cada vez que se regenera.

Las copias de `_up/` se recomprimen **por debajo de 10 MB**: es el tope del subidor del navegador.
"""
import json, os, subprocess, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(AQUI, 'shorts')
FICHA = json.load(open(os.path.join(S, 'serie.json'), encoding='utf-8'))
PUB = os.path.join(AQUI, 'publicar')
os.makedirs(os.path.join(PUB, '_up'), exist_ok=True)

FUENTES_COMUNES = """
WHERE EVERY FACT COMES FROM
- US Strategic Petroleum Reserve: 285,360,000 barrels in the week ending 4 September 2026 - the lowest level since 5 November 1982. US Energy Information Administration, weekly series (WCSSTUS1). Design capacity 727 million barrels.
- The release: 172 million barrels authorised on 11 March 2026, the US share of a 400-million-barrel collective action by IEA member countries. US Department of Energy.
- Brent closed at $104.61 and WTI at $100.05 on 11 September 2026.
- Strait of Hormuz traffic down roughly 95%, from more than 100 ships a day to an average of about 10 over ten days. Kpler.
- War-risk insurance for a Hormuz transit: 7.5% to 10% of hull value, or $3m-$21m per voyage.
- UK asylum accommodation: GBP 8 million a day on hotels, from the Home Office's own accounts. GBP 4,181 million spent on asylum support, resettlement and accommodation in the year to March 2026; GBP 107 per supported person per day.
- The contracts were costed at GBP 4.5 billion over ten years (2019-29) when signed; they are now expected to cost GBP 15.3 billion. National Audit Office and the Commons Public Accounts Committee.
- Hotels took 76% of the annual cost of asylum accommodation in 2024/25 while housing 35% of the people in it. National Audit Office.
- Ceuta: the Spanish Supreme Court ruled on 29 June 2026 that summary return does not apply to people intercepted at sea en route to Ceuta or Melilla, only to the land fence. 49,000 people entered in 24 hours on 31 July; around 80,000 attempted it; at least 141 died; about 70,000 had returned to Morocco by 3 August.

WHAT THIS VIDEO DOES NOT SAY
- It does not claim the oil release caused the price to rise. It states the sequence: the reserve was opened on 11 March and Brent rose more than 17% from the announcement. The causal claim is not made.
- The refill cost is not stated as a published budget figure. It is not stated at all in these videos.
- On the immigration pieces, the subject is a contract, a department and a court - never a group of people. Every actor named is an institution or a published decision.
- The Spanish Supreme Court did not strike down summary returns. It defined which of two procedures applies. Saying otherwise would be false.
"""

DESC = {
 1: """America's emergency oil reserve is 39% full. The last time it was this low, Ronald Reagan was in his first term - and the war in the Strait of Hormuz had not started yet.

""" + FUENTES_COMUNES,
 2: """Traffic through the Strait of Hormuz is down 95%. Almost nothing has been sunk. What closed the strait was not a weapon - it was the price of insuring a ship to cross it.

""" + FUENTES_COMUNES,
 3: """Britain spends GBP 8 million a day housing asylum seekers in hotels. Hotels take 76% of the accommodation budget and house 35% of the people in it. The contracts were costed at GBP 4.5 billion and are now expected to cost GBP 15.3 billion.

""" + FUENTES_COMUNES,
 4: """On 29 June a Spanish court published a ruling. Thirty-two days later, 49,000 people crossed into Ceuta in 24 hours. Nobody changed a law and nobody moved a fence.

""" + FUENTES_COMUNES,
}

# Etiquetas POR PIEZA: esta tanda son dos temas distintos (regla 27, la palabra medida es
# `iran war` en las dos primeras y `immigration` en las dos ultimas).
TAGS = {
 1: ('iran war, strait of hormuz, strategic petroleum reserve, spr, oil prices, oil reserve, '
     'energy security, brent crude, geopolitics, paper trail, the receipt,'),
 2: ('iran war, strait of hormuz, tanker war, war risk insurance, shipping, oil tankers, '
     'freight rates, oil prices, geopolitics, paper trail, the receipt,'),
 3: ('immigration, uk immigration, asylum hotels, home office, asylum seekers uk, '
     'public spending, procurement, national audit office, britain, geopolitics, paper trail,'),
 4: ('immigration, ceuta, spain, morocco, europe border, supreme court, migration, '
     'schengen, european union, geopolitics, paper trail, the receipt,'),
}


COMENTARIO = {
 1: ("The 17% is what Brent did after the 11 March announcement. This video does not claim the "
     "release caused it - it states the sequence. The 285,360,000 barrels is the EIA weekly series "
     "for the week ending 4 September. Every source is in the description."),
 2: ("The +3,600% is a freight ETF - what it costs to move oil by sea - not the price of oil. "
     "War-risk quotes of 7.5-10% of hull value are published ranges, and they are given as ranges. "
     "Almost nothing has been sunk, but there have been attacks: that is why it says almost."),
 3: ("The 76% / 35% split is the National Audit Office, 2024/25. The GBP 4.5bn and the GBP 15.3bn "
     "are the state's own estimates of the same contracts - not a plan versus a payment. This is "
     "about a procurement decision, not about who should come."),
 4: ("The Supreme Court did not strike down summary returns. It defined which of two procedures "
     "applies: the land fence, or interception at sea. That distinction is the whole story. "
     "It says at least 141 because 86 were confirmed as of 2 August."),
}


def pieza(n):
    """La ficha de la pieza `n` de `serie.json`.

    Faltaba: `master()` la llamaba y el modulo reventaba con NameError en cuanto se corria."""
    for Q in FICHA['shorts']:
        if Q['n'] == n: return Q
    raise SystemExit('pieza %s no existe en serie.json' % n)


def _dur(f):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                 '-of', 'csv=p=0', f], capture_output=True, text=True).stdout.strip())


def master(n):
    P = pieza(n)
    return os.path.join(S, P['dir'], 'salida', '%02d_%s.mp4' % (n, P['dir'].split('_', 1)[1]))


def copia_liviana(n):
    """Recomprime por debajo de 10 MB: tope del subidor del navegador."""
    P = pieza(n)
    src = master(n)
    dst = os.path.join(PUB, '_up', '%02d_%s.mp4' % (n, P['dir'].split('_', 1)[1]))
    if not os.path.exists(src): return None
    for crf in (25, 28, 31, 34):
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', src,
                        '-c:v', 'libx264', '-preset', 'slow', '-crf', str(crf),
                        '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', dst], check=True)
        if os.path.getsize(dst) < 10*1024*1024:
            print('  _up crf %d -> %.1f MB' % (crf, os.path.getsize(dst)/1e6)); return dst
    print('  _up NO baja de 10 MB (%.1f)' % (os.path.getsize(dst)/1e6))
    return dst


def main():
    plan = {'serie': FICHA['serie'], 'playlist': FICHA['playlist'], 'piezas': []}
    md = ['# S12 · THE RECEIPT — ficha de subida', '',
          '> Tanda de 4 shorts: **2 de `iran war` y 2 de `immigration`**, pedido de Agustin del '
          '15-sep. Las cuatro el mismo dia, ~2 h entre piezas; las dos de Iran primero.', '',
                    '| | |', '|---|---|',
          '| Playlist | **%s** (crearla y meter las cuatro) |' % FICHA['playlist'],
          '| Idioma | Ingles · categoria Education · **no es para ninos** |',
          '| Este documento | `%s` |' % os.path.join(PUB, 'SUBIR.md'),
          '| Plan en JSON | `%s` |' % os.path.join(PUB, 'PLAN_SUBIDA.json'), '',
          '## Orden de operaciones', '',
          '1. **Crear la playlist** `%s` antes de subir nada. Las CUATRO van ahi.' % FICHA['playlist'],
          '2. **Subir la PIEZA 1.** Titulo, descripcion y etiquetas de abajo. Publicar YA (no programar).',
          '3. Video relacionado de la 1 -> **el short de Suecia que ya esta arriba** '
          '(`https://www.youtube.com/watch?v=qI91Bes8T2I`). Es lo unico del catalogo con trafico vivo '
          'sobre este tema.',
          '4. Poner el **comentario fijado** de la pieza 1 (esta abajo, listo para copiar).',
          '5. **Esperar ~2 h** y repetir con la PIEZA 2. Su video relacionado es la **pieza 1**.',
          '6. **Esperar ~2 h** y repetir con la PIEZA 3. Su video relacionado es la **pieza 2**.',
          '7. **Esperar ~2 h** y repetir con la PIEZA 4. Su video relacionado es la **pieza 3**.',
          '8. En las CUATRO: idioma **ingles**, categoria **Education**, **no es para ninos**.',
          '9. Miniatura: el boton "Subir miniatura" solo aparece con el Partner Program. Si no esta, '
          'elegir el cuadro sugerido que muestre el gancho — cualquiera sirve, porque el gancho esta '
          'quemado arriba los primeros 3,5 s.', '',
          '### Trampas del formulario (comprobadas subiendo 20)', '',
          '- Al escribir la descripcion recien subida, **no pulsar `ctrl+a`**: se escribe como una "a" '
          'al principio del texto.',
          '- El cuadro de descripcion **autocompleta hashtags**: dejar los hashtags antes de la ultima '
          'linea y con un espacio final.',
          '- Si programas en vez de publicar, el selector de hora **solo acepta multiplos de 15 min**.',
          '- Limite de **10 MB por archivo** al subir por navegador: por eso los de `_up/` '
          '(< 10 MB). Los masters no entran.', '']

    for P in FICHA['shorts']:
        n = P['n']; slug = P['dir'].split('_', 1)[1]
        m = master(n)
        existe = os.path.exists(m)
        up = copia_liviana(n) if existe else None
        mini = os.path.join(PUB, 'miniaturas', '%s.jpg' % P['dir'])
        rel = ('el short de Suecia ya publicado — https://www.youtube.com/watch?v=qI91Bes8T2I'
               if n == 1 else 'la PIEZA %d de esta serie' % (n-1))
        md += ['', '---', '', '## PIEZA %d DE 4 — %s' % (n, P['subtema']), '']
        if not existe:
            md += ['> ⛔ **TODAVIA NO EXISTE EL ARCHIVO.** Esta ficha va antes que el render. '
                   'No subas nada hasta que esta linea desaparezca.', '']
        md += ['**SUBIR ESTE ARCHIVO:**', '',
               '`%s`' % (up or m), '']
        if existe:
            md += ['(master sin recomprimir: `%s` — %.1f MB, %.0f s)'
                   % (m, os.path.getsize(m)/1e6, _dur(m)), '']
        md += ['**TITULO** (copiar tal cual):', '', '```', P['titulo'], '```', '',
               '**DESCRIPCION** (copiar tal cual):', '', '```',
               DESC[n].strip() + '\n' + FUENTES_COMUNES.strip(), '',
               'Full series: %s' % FICHA['playlist'],
               '', P['pregunta_voz'], '```', '',
               '**ETIQUETAS** (una linea, con la coma final):', '', '```', TAGS[n], '```', '',
               '| Campo | Valor |', '|---|---|',
               '| Miniatura 9:16 | `%s` |' % mini,
               '| Video relacionado | %s |' % rel,
               '| Pregunta en pantalla | `%s` |' % P['pregunta_pantalla'],
               '| Playlist | %s |' % FICHA['playlist'],
               '| Duracion | %.0f s |' % P.get('duracion_real_s', 0), '',
               '**Comentario fijado** (lo tiene que poner Agustin, el asistente no puede comentar en su nombre):', '',
               '```', COMENTARIO[n],
               '```', '']
        plan['piezas'].append({
            'n': n, 'archivo': up or m, 'master': m, 'existe': existe,
            'titulo': P['titulo'], 'miniatura': mini,
            'relacionado': 'qI91Bes8T2I' if n == 1 else 'pieza %d' % (n-1),
            'duracion_s': P.get('duracion_real_s'),
        })

    md += ['', '---', '', '## Checklist de monetizacion (skill 2.10b / canal/MONETIZACION.md 3)',
           '', 'Se marca ANTES de subir. No se salta por ser una pieza corta.', '',
           '- [x] **Ningun colectivo de personas es sujeto de una frase.** Los sujetos de las '
           'cuatro piezas son: la reserva, el mecanismo del seguro, el contrato y el departamento, '
           'y el tribunal. Comprobado linea por linea en los cuatro `guion.md` (regla 13).',
           '- [x] **Ningun grupo religioso ni etnico aparece**, ni como sujeto ni como adjetivo.',
           '- [x] **La pieza 3 dice en voz** "You can argue about how many people should come. '
           'This is not that argument": es la linea editorial y la defensa de monetizacion.',
           '- [x] **La pieza 4 no acusa a Marruecos** de abrir la frontera (F4.9: lo niega y lo '
           'atribuye a redes de trafico y a malas interpretaciones de la sentencia).',
           '- [x] **La pieza 4 no dice que el Supremo derogara la devolucion en caliente**: dice '
           'que delimito a que via se aplica, que es lo que paso (F4.2).',
           '- [x] **La pieza 1 no afirma causalidad** entre la liberacion y la subida del precio: '
           'dice la secuencia (F1.8).',
           '- [x] **La pieza 2 dice "almost nothing has been sunk"**, no "nothing" (hubo ataques: '
           'F2.6/F2.7), y el +3.600 % se atribuye al ETF de fletes, no al precio del petroleo.',
           '- [x] **Los 141 muertos** van con "at least" (86 confirmados al 2-ago, F4.6) y **sin '
           'imagenes de victimas**: el plano es un sello sobre un documento.',
           '- [ ] Sin `BREAKING`, sin `invasion` para personas, sin `Nazi`, sin `fraud` en titulo, '
           'miniatura ni descripcion.',
           '- [ ] Titulo <= 100 caracteres, cifra dura delante + pregunta detras, tres hashtags.',
           '- [ ] Si YouTube lo marca con **anuncios limitados**, pedir revision humana el mismo '
           'dia.', '']

    json.dump(plan, open(os.path.join(PUB, 'PLAN_SUBIDA.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    open(os.path.join(PUB, 'SUBIR.md'), 'w', encoding='utf-8').write('\n'.join(md))
    print('  ficha ->', os.path.join(PUB, 'SUBIR.md'))
    print('  plan  ->', os.path.join(PUB, 'PLAN_SUBIDA.json'))


if __name__ == '__main__':
    main()
