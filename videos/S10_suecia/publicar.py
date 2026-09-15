# -*- coding: utf-8 -*-
"""Deja la ficha de subida de las tres piezas de la S10 y las copias livianas para Studio.

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
- Election result, 13 September 2026: Valmyndigheten (val.se) and SVT's count. PRELIMINARY at the time of writing: 95% counted. Sweden Democrats 17.5% (-3.0), 62 seats (-11) - the first time the party has shrunk in a national election. Turnout 80.3%.
- Shootings: 147 in 2025 against 390 in 2022, a 63% fall. Swedish Police (Polisen).
- Homicides: 84 in 2025, the lowest since 2012, against a peak of 124 in 2020. Bra (Swedish National Council for Crime Prevention), March 2026.
- Detonations: 189 in 2025 against 136 in 2024. Polisen press release, January 2026: "Minskat antal skjutningar men fler sprangningar under 2025".
- Reported explosives offences up from 162 in 2018 to 621 in 2025 (+289%). Bra, 4 March 2026.
- Asylum applications at their lowest since 1997, and in 2024 more people left Sweden than arrived for the first time in over 50 years. Swedish Government and Migrationsverket.

WHAT THIS VIDEO DOES NOT SAY
- It does not say Sweden is being destroyed, or that it is heading for any particular demographic future. Shootings are down 63% since 2022 and homicides are at a 13-year low. Those numbers are in this description because they are true.
- It does not treat Muslims as a group. Every actor named here is an organisation, a government, a public body or a named individual.
"""


def pieza(n):
    for s in FICHA['shorts']:
        if s['n'] == n: return s
    raise SystemExit('pieza %s no existe' % n)


DESC = {
1: """In 2023 an Iraqi refugee named Salwan Momika burned copies of the Quran in public squares in Stockholm. Sweden let him. That was the point of Sweden.

On 29 January 2025 he was live-streaming from his flat in Sodertalje when men came through the door and shot him dead, on camera. In October 2025 Swedish court documents named a suspect: a 24-year-old Syrian man living in Sweden. No one has been convicted.

Turkey had already spent months blocking Swedish entry into NATO over those burnings, demanding extraditions.

SOURCES FOR THIS ONE
- The killing of Salwan Momika, 29 January 2025, Sodertalje, during a live stream: CNN, Al Jazeera, Reuters, 30 January 2025.
- Suspect named in Swedish court documents on 16 October 2025: a 24-year-old Syrian man resident in Sweden. Named here only as "a suspect" - he has not been convicted.
- Momika's 2023 Quran burnings and Turkey citing them, alongside extradition demands, while delaying Sweden's NATO accession: contemporaneous reporting, 2023-2024.
- Easter 2022 riots after an anti-Muslim rally: 26 police officers and 14 members of the public injured, 20 police vehicles damaged or destroyed. CNN, 18 April 2022.
""",
2: """For sixteen years the Swedish state funded Ibn Rushd, a study association whose links to the Muslim Brotherhood were raised again and again.

It drew state grants from 2008 to 2024. In 2023 the funding body investigated properly and found study material incompatible with the terms of the grant. In 2024 it cut every krona for 2025-2027. Ibn Rushd shut down.

A government inquiry into banning foreign money for religious organisations reports in May 2026. One case in the file is a Shia mosque outside Stockholm, flagged over collaboration with the Iranian regime.

SOURCES FOR THIS ONE
- Ibn Rushd received state grants via Folkbildningsradet from 2008 to 2024; the order of magnitude used here is around 29 million kronor a year.
- The government-commissioned review of Ibn Rushd: Erik Amna, "Nar tilliten provas", Folkbildningsradet, 2019.
- The 2023 investigation found study material incompatible with the grant conditions; 146,900 kronor was reclaimed.
- Folkbildningsradet's 2024 decision removing state funding for 2025-2027, and Ibn Rushd winding down from 2025: Folkbildningsradet and SVT.
- Chair Inger Ashing's stated reason: that Ibn Rushd lacks the conditions to run activities in line with the state's purposes for the grant. The conclusion drawn in this video is the channel's own, not the agency's.
- The inquiry into restricting foreign funding of "anti-democratic interests", reporting by 29 May 2026, and the Shia mosque outside Stockholm flagged over the Iranian regime: Swedish Government.
""",
3: """Since 2019 Sweden has closed seventeen Islamic schools. Two of them in 2022, after the security service warned that pupils were being radicalised inside them. From 2024 religious free schools cannot open new branches or take on more students.

That is the part the state can reach.

Six thousand fifteen-year-olds in Stockholm, Gothenburg and Malmo were surveyed for their own city councils. Around 14% live under honour norms. Sweden wrote a new criminal offence for it in 2022.

And on Sunday the party that forced the crackdown lost eleven seats.

SOURCES FOR THIS ONE
- Seventeen Islamic free schools closed since 2019 by the Swedish Schools Inspectorate (Skolinspektionen). Two permits revoked in May 2022, in Uppsala and Stockholm, after Sapo warned of radicalisation risk: The Local, 5 May 2022.
- Restrictions on confessional free schools expanding or opening new branches from 2024: Swedish Government.
- The honour-norms figure is from the three big cities, NOT from Sweden as a whole: a study commissioned by the city councils of Stockholm, Gothenburg and Malmo, fieldwork 2017-2018, 6,002 fifteen-year-olds surveyed plus 235 in-depth interviews. Around 14% live under honour norms; more than one in ten girls said they were expected to be virgins when they married.
- The offence of "hedersfortryck" (honour-based oppression) entered into force 1 June 2022; 254 offences were reported through the end of 2025: Bra.
- Sapo lists violent Islamism as one of the two largest terror threats to Sweden, alongside violent right-wing extremism. Threat level raised to 4 of 5 in August 2023 and lowered to 3 of 5 on 23 May 2025.
- Citizenship residence requirement raised from five to eight years, in force 6 June 2026, with language and civics tests and a self-sufficiency requirement, and no transitional arrangements: Swedish Riksdag, decision of 29 April 2026.
""",
}

TAGS = ('sweden, sweden election, swedish politics, islamism, political islam, europe, immigration, '
        'geopolitics, salwan momika, ibn rushd, sweden democrats, stockholm, nato, paper trail,')


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
    md = ['# S10 · WHAT SWEDEN PAID FOR — ficha de subida', '',
          '> Serie de 3 shorts, **las tres el mismo dia** con ~30 min entre piezas '
          '(`canal/SHORTS.md` §3.6: es noticia).', '',
          '> ⚠️ **El escrutinio estaba al 95 %** al escribir los guiones. El definitivo sale el fin de '
          'semana del 19-20 de sep. Lo unico que dependeria de eso es una linea de la pieza 3 '
          '(las 11 bancas), y es robusta a lo que falta contar.', '',
          '| | |', '|---|---|',
          '| Playlist | **%s** (crearla y meter las tres) |' % FICHA['playlist'],
          '| Idioma | Ingles · categoria Education · **no es para ninos** |',
          '| Este documento | `%s` |' % os.path.join(PUB, 'SUBIR.md'),
          '| Plan en JSON | `%s` |' % os.path.join(PUB, 'PLAN_SUBIDA.json'), '',
          '## Orden de operaciones', '',
          '1. **Crear la playlist** `%s` antes de subir nada. Las tres van ahi.' % FICHA['playlist'],
          '2. **Subir la PIEZA 1.** Titulo, descripcion y etiquetas de abajo. Publicar YA (no programar).',
          '3. Video relacionado de la 1 -> **el short de Suecia que ya esta arriba** '
          '(`https://www.youtube.com/watch?v=qI91Bes8T2I`). Es lo unico del catalogo con trafico vivo '
          'sobre este tema.',
          '4. Poner el **comentario fijado** de la pieza 1 (esta abajo, listo para copiar).',
          '5. **Esperar ~30 min** y repetir con la PIEZA 2. Su video relacionado es la **pieza 1**.',
          '6. **Esperar ~30 min** y repetir con la PIEZA 3. Su video relacionado es la **pieza 2**.',
          '7. En las tres: idioma **ingles**, categoria **Education**, **no es para ninos**.',
          '8. Miniatura: el boton "Subir miniatura" solo aparece con el Partner Program. Si no esta, '
          'elegir el cuadro sugerido que muestre el gancho — cualquiera sirve, porque el gancho esta '
          'quemado arriba durante todo el video.', '',
          '### Trampas del formulario (comprobadas subiendo 20)', '',
          '- Al escribir la descripcion recien subida, **no pulsar `ctrl+a`**: se escribe como una "a" '
          'al principio del texto.',
          '- El cuadro de descripcion **autocompleta hashtags**: dejar los hashtags antes de la ultima '
          'linea y con un espacio final.',
          '- Si programas en vez de publicar, el selector de hora **solo acepta multiplos de 15 min**.',
          '- Limite de **10 MB por archivo** al subir por navegador: por eso los de `_up/` '
          '(6,3-6,8 MB). Los masters no entran.', '']

    for P in FICHA['shorts']:
        n = P['n']; slug = P['dir'].split('_', 1)[1]
        m = master(n)
        existe = os.path.exists(m)
        up = copia_liviana(n) if existe else None
        mini = os.path.join(PUB, 'miniaturas', '%s.jpg' % P['dir'])
        rel = ('el short de Suecia ya publicado — https://www.youtube.com/watch?v=qI91Bes8T2I'
               if n == 1 else 'la PIEZA %d de esta serie' % (n-1))
        md += ['', '---', '', '## PIEZA %d DE 3 — %s' % (n, P['subtema']), '']
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
               '**ETIQUETAS** (una linea, con la coma final):', '', '```', TAGS, '```', '',
               '| Campo | Valor |', '|---|---|',
               '| Miniatura 9:16 | `%s` |' % mini,
               '| Video relacionado | %s |' % rel,
               '| Pregunta en pantalla | `%s` |' % P['pregunta_pantalla'],
               '| Playlist | %s |' % FICHA['playlist'],
               '| Duracion | %.0f s |' % P.get('duracion_real_s', 0), '',
               '**Comentario fijado** (lo tiene que poner Agustin, el asistente no puede comentar en su nombre):', '',
               '```', {1: 'Court documents named a suspect in October 2025. Nobody has been convicted. '
                          'Sources for every number are in the description.',
                       2: 'Folkbildningsradet published the decision that removed the funding. '
                          'The 2019 review is Erik Amna, "Nar tilliten provas". Both are in the description.',
                       3: 'The 14% figure is from Stockholm, Gothenburg and Malmo - not from Sweden as a '
                          'whole. 6,002 fifteen-year-olds surveyed for the three city councils.'}[n],
               '```', '']
        plan['piezas'].append({
            'n': n, 'archivo': up or m, 'master': m, 'existe': existe,
            'titulo': P['titulo'], 'miniatura': mini,
            'relacionado': 'qI91Bes8T2I' if n == 1 else 'pieza %d' % (n-1),
            'duracion_s': P.get('duracion_real_s'),
        })

    md += ['', '---', '', '## Checklist de monetizacion (`canal/MONETIZACION.md` §3)', '',
           '- [ ] Ningun grupo religioso aparece como sujeto. Los sujetos son organizaciones, '
           'organismos del Estado y gobiernos, con nombre.',
           '- [ ] Al sospechoso de la pieza 1 **no se lo nombra**: hay identificacion judicial, no condena.',
           '- [ ] El 14 % de la pieza 3 dice **siempre** "Stockholm, Gothenburg and Malmo".',
           '- [ ] Las bajas de delito (-63 % en tiroteos) estan en la descripcion de las tres.',
           '- [ ] Sin `BREAKING`, sin `invasion` para personas, sin `Nazi` en titulo ni miniatura.',
           '- [ ] Titulo ≤ 100 caracteres, pregunta + oracion corta, tres hashtags.', '']

    json.dump(plan, open(os.path.join(PUB, 'PLAN_SUBIDA.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    open(os.path.join(PUB, 'SUBIR.md'), 'w', encoding='utf-8').write('\n'.join(md))
    print('  ficha ->', os.path.join(PUB, 'SUBIR.md'))
    print('  plan  ->', os.path.join(PUB, 'PLAN_SUBIDA.json'))


if __name__ == '__main__':
    main()
