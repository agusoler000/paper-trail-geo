# -*- coding: utf-8 -*-
"""Deja la ficha de subida del short S03 y la copia liviana que se arrastra a Studio.

    python publicar.py          ->  publicar/SUBIR.md + publicar/PLAN_SUBIDA.json + publicar/_up/01_aviso.mp4

**Sube y programa Agustin**, no el asistente (decision del 2026-09-11). Lo que se entrega es la ficha
completa: ruta exacta del archivo, titulo, descripcion para copiar tal cual, etiquetas en una linea
con la coma final, miniatura, pregunta del cierre y el checklist de monetizacion. Y se le manda por
chat cada vez que se regenera.

La copia de `_up/` se recomprime para quedar **por debajo de 10 MB**: es el tope del subidor del
navegador sumando los archivos de una llamada, y ademas es lo que entra comodo por el chat.
"""
import json, os, subprocess, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(AQUI, 'shorts')
FICHA = json.load(open(os.path.join(S, 'serie.json'), encoding='utf-8'))
P = FICHA['shorts'][0]
D = os.path.join(S, P['dir'])
PUB = os.path.join(AQUI, 'publicar'); os.makedirs(os.path.join(PUB, '_up'), exist_ok=True)
MASTER = os.path.join(D, 'salida', '%02d_%s.mp4' % (P['n'], P['dir'].split('_', 1)[1]))
UP = os.path.join(PUB, '_up', '%02d_%s.mp4' % (P['n'], P['dir'].split('_', 1)[1]))
MINI = os.path.join(PUB, 'miniaturas', '01_%s.jpg' % P['dir'].split('_', 1)[1])

DESC = """Europe is not just getting old. The numbers tell a different story: 4.9 percent Muslim in 2016, and 7.4 percent by 2050 even with zero migration - 14 percent if current flows continue. This is the record, with sources.

WHERE EVERY FACT COMES FROM
- Demographics: Pew Research Center, "Europe's Growing Muslim Population" (2017). 25.8 million Muslims (4.9 percent) in 2016; 2050 projections of 7.4 percent (zero migration), 11.2 percent (medium) and 14 percent (high).
- The Muslim Brotherhood: Dokumentationsstelle Politischer Islam (Austria), "The Muslim Brotherhood's Pan-European Structure" (Vidino and Altuna, 2021), mapping over 600 organisations and mosques.
- Diyanet (Turkey): 900 mosques in Germany, about 270 in France, 146 of 475 in the Netherlands. Austria closed 7 mosques and deported 40 Turkish-paid imams (2018).
- Rotherham: the Jay report (2014), around 1,400 children exploited between the late 1980s and 2013.
- Sweden: 162 bombings in 2018, 317 in 2024.
- Malmö: Jewish community of about 700 in 2010, shrinking 5 percent a year.

WHAT THIS VIDEO DOES NOT SAY
It does not blame Muslims as people. It names political Islam - organisations, the governments that fund them, and the policies that failed. Every number is a source, not an opinion.

PAPER TRAIL - the mechanism behind the story. Follow the paper.

Demographic drift or political project? Tell me in the comments.

#europe #islam #demographics"""

TAGS = ("europe, islam, demographics, immigration, muslim brotherhood, diyanet, turkey, "
        "sweden, rotherham, geopolitics, paper trail,")


def _dur(f):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                 '-of', 'csv=p=0', f], capture_output=True, text=True).stdout.strip())


def copia_liviana():
    """Recomprime hasta quedar bajo 10 MB. Empieza en crf 24 y sube de a 3."""
    dur = _dur(MASTER)
    for crf in (24, 27, 30, 33):
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', MASTER,
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', str(crf),
                        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
                        '-movflags', '+faststart', UP], check=True)
        mb = os.path.getsize(UP)/1e6
        if mb < 9.6:
            print('  _up/%s  crf=%d  %.1f MB  %.0f s' % (os.path.basename(UP), crf, mb, dur))
            return mb, dur
    raise SystemExit('no baja de 10 MB ni con crf 33')


def main():
    if not os.path.exists(MASTER): raise SystemExit('falta el master: ' + MASTER)
    mb, dur = copia_liviana()
    assert dur < 180, 'se pasa del techo de Shorts (180 s): %.1f s' % dur
    plan = {
        'produccion': FICHA['produccion'], 'modo': 'C · short suelto',
        'piezas': [{
            'n': 1, 'archivo': UP, 'master': MASTER, 'mb': round(mb, 1), 'duracion_s': round(dur, 1),
            'titulo': P['titulo'], 'descripcion': DESC, 'etiquetas': TAGS,
            'miniatura': MINI if os.path.exists(MINI) else None,
            'hook': P['hook'], 'pregunta': P['pregunta_pantalla'],
            'playlist': None, 'video_relacionado': None,
            'cuando': 'cuando lo decida Agustin (short suelto de prueba, sin urgencia)',
        }],
    }
    json.dump(plan, open(os.path.join(PUB, 'PLAN_SUBIDA.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    md = []
    A = md.append
    A('# LA ISLAMIZACION DE EUROPA — ficha para subir (un short suelto)\n')
    A('> Generado por `publicar.py`. No editar a mano: se regenera.')
    A('> **Sube y programa Agustin.** Esto es todo lo que hace falta, copiado tal cual.')
    A('> Hechos y enlaces: `fuentes/referencia.md`. Postura: `postura.md`.\n')
    A('---\n')
    A('## Rutas\n')
    A('| Que | Ruta |')
    A('|---|---|')
    A('| **El archivo que se sube** (%.1f MB) | `%s` |' % (mb, UP))
    A('| Master (calidad plena) | `%s` |' % MASTER)
    A('| Miniatura 9:16 | `%s` |' % MINI)
    A('| Este documento | `%s` |' % os.path.join(PUB, 'SUBIR.md'))
    A('| Plan en JSON | `%s` |' % os.path.join(PUB, 'PLAN_SUBIDA.json'))
    A('| Guion | `%s` |' % os.path.join(D, 'guion.md'))
    A('')
    A('---\n')
    A('## La pieza\n')
    A('**SUBIR ESTE ARCHIVO:**\n')
    A('```')
    A(UP)
    A('```\n')
    A('- **Peso:** %.1f MB  ·  **Duracion:** %.0f s (%d:%02d) — el techo de Shorts es 180 s'
      % (mb, dur, int(dur)//60, int(dur) % 60))
    A('- **Cuando:** %s' % plan['piezas'][0]['cuando'])
    A('- **Titulo (copiar tal cual):** `%s`' % P['titulo'])
    A('- **Gancho quemado en el video:** %s' % ' / '.join(P['hook']))
    A('- **Pregunta del cierre:** %s' % P['pregunta_pantalla'])
    A('- **Miniatura:** `%s`' % MINI)
    A('- **Playlist:** ninguna (no es una serie)  ·  **Video relacionado:** ninguno todavia')
    A('- **Idioma:** ingles  ·  **Categoria:** News & Politics  ·  **No es para ninos**  ·  '
      '**Contenido alterado o sintetico: No**')
    A('')
    A('**Descripcion (copiar tal cual):**\n')
    A('```')
    A(DESC)
    A('```\n')
    A('**Etiquetas** (Detalles -> "Mostrar mas" -> campo Etiquetas, **ANTES** del primer "Siguiente"). '
      'Pegar la linea entera, con la coma final:\n')
    A('```')
    A(TAGS)
    A('```\n')
    A('**Comentario fijado (copiar tal cual):**\n')
    A('```')
    A('Every fact in this video has a source, and they are all listed in the description. '
      'This is not about blaming a religion - it names political Islam, the governments that fund it, '
      'and the numbers. So: demographic drift, or a political project? Put it in the comments.')
    A('```\n')
    A('---\n')
    A(open(os.path.join(AQUI, '_monetizacion.md'), encoding='utf-8').read()
      if os.path.exists(os.path.join(AQUI, '_monetizacion.md')) else '')
    open(os.path.join(PUB, 'SUBIR.md'), 'w', encoding='utf-8').write('\n'.join(md))
    print('  ficha ->', os.path.join(PUB, 'SUBIR.md'))


if __name__ == '__main__':
    main()
