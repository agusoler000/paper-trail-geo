# -*- coding: utf-8 -*-
"""Junta las cuatro fichas de la tanda de EE. UU. (S06-S09) en UN solo SUBIR.md.

    python subir_tanda.py

Lee cada `videos/<pieza>/publicar/SUBIR.md` y `shorts/serie.json` y arma
`canal/SUBIR_TANDA_US.md`: un documento, cuatro bloques, en orden de caducidad.
Se regenera; no editar a mano.
"""
import json, os, re, subprocess, pathlib

RAIZ = pathlib.Path(r'C:\Users\agust\Desktop\agustin\canal_geopolitica')
V = RAIZ / 'videos'

# En orden de CADUCIDAD, que es el orden en que conviene subirlos.
ORDEN = [
    ('S06_fed_inflacion', '01_fed', '01_fed',
     'PRIMERO — la Fed decide el martes 15 y el miercoles 16. Despues del martes la pieza pierde el filo.'),
    ('S08_presupuesto', '01_presupuesto', '01_presupuesto',
     'SEGUNDO — vale hasta la eleccion del 3 de noviembre, pero el dato de la prorroga es del 1 de septiembre y cuanto mas fresco mejor.'),
    ('S07_vivienda', '01_vivienda', '01_vivienda',
     'TERCERO — cifras del segundo trimestre y de la semana del 10-sep. Aguanta la semana entera.'),
    ('S09_midterms', '01_midterms', '01_midterms',
     'CUARTO — la aritmetica no envejece hasta el 3 de noviembre.'),
]


def dur(f):
    return float(subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f],
        capture_output=True, text=True).stdout.strip())


def constantes(py):
    """Lee `DESC`, `TAGS` y `FIJADO` del publicar.py de la pieza, con `ast`.

    La primera version raspaba el SUBIR.md ya generado con una expresion regular, y **las
    etiquetas salieron vacias**: la linea de encabezado lleva un `**ANTES**` en el medio, asi
    que `\\*\\*Etiquetas[^\\n]*\\*\\*` se comia hasta ese segundo par de asteriscos y despues no
    encontraba el salto de linea doble. Raspar un documento generado es fragil por definicion.
    Leer la constante del fuente es exacto y no se puede desincronizar.

    Se usa `ast` y **no** `import`: `publicar.py` llama a `main()` a nivel de modulo, asi que
    importarlo volveria a recomprimir el MP4 con ffmpeg."""
    import ast
    arbol = ast.parse(pathlib.Path(py).read_text(encoding='utf-8'))
    out = {}
    for nodo in arbol.body:
        if isinstance(nodo, ast.Assign) and len(nodo.targets) == 1:
            nombre = getattr(nodo.targets[0], 'id', None)
            if nombre in ('DESC', 'TAGS', 'FIJADO'):
                out[nombre] = ast.literal_eval(nodo.value)
    faltan = {'DESC', 'TAGS', 'FIJADO'} - set(out)
    if faltan:
        raise SystemExit('%s: no se pudieron leer %s' % (py, ', '.join(sorted(faltan))))
    return out


out = []
A = out.append

A('# SUBIR — tanda de EE. UU. (S06 → S09)')
A('')
A('> Generado por `produccion/subir_tanda.py`. **No editar a mano: se regenera.**')
A('> Cuatro shorts, un solo documento, **en el orden en que conviene subirlos**.')
A('> Los dos de Irán (S04 «THE RECEIPT» y S05 «THE MAP») ya están subidos y no están acá.')
A('')
A('## Lo que es igual en los cuatro')
A('')
A('| Campo | Valor |')
A('|---|---|')
A('| Idioma | inglés |')
A('| Categoría | News & Politics |')
A('| Público | **No es para niños** |')
A('| Contenido alterado o sintético | **No** |')
A('| Playlist | ninguna (no son una serie) |')
A('| Miniatura | la que va con cada pieza, 9:16, < 2 MB |')
A('')
A('**Tres cosas que sólo podés hacer vos:**')
A('')
A('1. **El comentario fijado.** Está en cada bloque, listo para copiar. Es lo que abre el hilo.')
A('2. **Video relacionado.** Apuntá cada uno al que ya tenga más vistas del canal. Sin eso el')
A('   short es un callejón sin salida: es el único enlace clicable dentro del feed de Shorts.')
A('3. **Separalos.** Unas horas entre uno y otro. Cuatro piezas del mismo canal en la misma hora')
A('   compiten entre sí en el feed.')
A('')
A('**Trampas del formulario** (comprobadas subiendo 20): el selector de hora sólo acepta')
A('múltiplos de 15 min · al escribir la descripción recién subida **no pulses `ctrl+a`** (se')
A('escribe como una «a» al principio) · las etiquetas van en Detalles → «Mostrar más», **antes**')
A('del primer «Siguiente».')
A('')
A('---')
A('')

for i, (slug, dirp, base, cuando) in enumerate(ORDEN, 1):
    d = V / slug
    ficha = json.loads((d / 'shorts' / 'serie.json').read_text(encoding='utf-8'))
    P = ficha['shorts'][0]
    C = constantes(d / 'publicar.py')
    mp4 = d / 'publicar' / '_up' / ('01_%s.mp4' % base.split('_', 1)[1])
    mini = d / 'publicar' / 'miniaturas' / ('01_%s.jpg' % base.split('_', 1)[1])
    seg = dur(str(mp4))
    mb = os.path.getsize(mp4) / 1e6

    A('# %d · %s' % (i, ficha['serie']))
    A('')
    A('**%s**' % cuando)
    A('')
    A('| | |')
    A('|---|---|')
    A('| **Archivo a subir** | `%s` |' % mp4)
    A('| **Miniatura** | `%s` |' % mini)
    A('| Duración · peso | **%d s** · %.1f MB |' % (round(seg), mb))
    A('| Gancho quemado | %s |' % ' / '.join(P['hook']))
    A('| Pregunta del cierre | %s |' % P['pregunta_pantalla'])
    A('| Master (calidad plena) | `%s` |' % (d / 'shorts' / dirp / 'salida' / ('01_%s.mp4' % base.split('_', 1)[1])))
    A('| Fuentes | `%s` |' % (d / 'fuentes' / 'referencia.md'))
    A('')
    A('**Título** (copiar tal cual):')
    A('')
    A('```')
    A(P['titulo'])
    A('```')
    A('')
    A('**Descripción** (copiar tal cual):')
    A('')
    A('```')
    A(C['DESC'])
    A('```')
    A('')
    A('**Etiquetas** (Detalles → «Mostrar más» → Etiquetas, ANTES del primer «Siguiente»). Pegá la')
    A('línea entera, con la coma final:')
    A('')
    A('```')
    A(C['TAGS'])
    A('```')
    A('')
    A('**Comentario fijado** (lo tenés que poner vos; copiar tal cual):')
    A('')
    A('```')
    A(C['FIJADO'])
    A('```')
    A('')
    A('---')
    A('')

dst = RAIZ / 'canal' / 'SUBIR_TANDA_US.md'
dst.write_text('\n'.join(out), encoding='utf-8')
print(dst, '%.1f KB' % (os.path.getsize(dst) / 1024))
