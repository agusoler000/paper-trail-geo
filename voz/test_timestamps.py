# -*- coding: utf-8 -*-
"""Test de `voz/timestamps.py` con un payload SINTETICO (0 creditos, no llama a fal).

    python voz/test_timestamps.py

Comprueba lo que de verdad puede salir mal al cambiar whisper por los tiempos del proveedor:
 1. que las palabras salgan bien de la alineacion por caracteres,
 2. que las etiquetas de direccion de actor (`[measured]`) NO entren como palabras,
 3. que el desplazamiento del beat y el recorte de silencio se apliquen,
 4. que se encuentre la alineacion este donde este dentro de la respuesta,
 5. que un payload sin alineacion devuelva vacio (y se caiga a whisper).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import timestamps as TS

FALLOS = []


def ok(cond, que):
    print(('  OK   ' if cond else '  FALLA ') + que)
    if not cond: FALLOS.append(que)


def payload(texto, dur_char=0.05, t_ini=0.0):
    """Arma una respuesta con la forma de ElevenLabs: un caracter cada `dur_char` segundos."""
    ch = list(texto)
    a = [round(t_ini + i * dur_char, 4) for i in range(len(ch))]
    b = [round(x + dur_char, 4) for x in a]
    return {'audio': {'url': 'https://example/x.mp3'},
            'timestamps': {'characters': ch,
                           'character_start_times_seconds': a,
                           'character_end_times_seconds': b}}


def main():
    # --- 1 y 2: palabras, sin las etiquetas de actor
    p = payload('[measured] On the 29th of June a Spanish court published a ruling.')
    w = TS.palabras(p)
    dichas = [x[0] for x in w]
    ok(dichas == ['on', 'the', '29th', 'of', 'june', 'a', 'spanish', 'court', 'published', 'a', 'ruling'],
       'palabras del payload: %s' % dichas)
    ok(all('measured' != x for x in dichas), 'la etiqueta [measured] no entra como palabra')

    # los tiempos crecen y el primero cae donde empieza la primera letra de "On"
    ok(all(w[i][1] <= w[i + 1][1] for i in range(len(w) - 1)), 'los tiempos van en orden')
    i_on = '[measured] On the'.index('On')
    ok(abs(w[0][1] - i_on * 0.05) < 1e-6, 'el primer tiempo es el del caracter "O" (%.3f s)' % w[0][1])
    ok(w[0][2] > w[0][1], 'cada palabra dura algo')

    # --- 3: desplazamiento del beat y recorte de silencio
    w2 = TS.palabras(p, t0=100.0, recorte=0.25)
    ok(abs((w2[0][1] - w[0][1]) - (100.0 - 0.25)) < 1e-6,
       't0 y recorte se aplican (%.3f -> %.3f)' % (w[0][1], w2[0][1]))

    # --- 4: la alineacion, venga donde venga
    al = p['timestamps']
    ok(TS.alineacion({'alignment': al}) is not None, 'la encuentra en "alignment"')
    ok(TS.alineacion({'normalized_alignment': al}) is not None, 'la encuentra en "normalized_alignment"')
    ok(TS.alineacion(al) is not None, 'la encuentra si viene suelta')
    ok(TS.alineacion({'output': {'timestamps': al}}) is not None, 'la encuentra anidada en "output"')

    # --- 5: sin alineacion -> vacio, y `hay()` dice que no
    ok(TS.palabras({'audio': {'url': 'x'}}) == [], 'un payload sin alineacion devuelve vacio')
    ok(TS.alineacion({'audio': {'url': 'x'}}) is None, 'alineacion() devuelve None sin alineacion')

    # --- extra: una sola palabra, y texto con puntuacion pegada
    u = TS.palabras(payload('Ceuta.'))
    ok(u == [('ceuta', 0.0, 0.3)] or (len(u) == 1 and u[0][0] == 'ceuta'),
       'una sola palabra con punto: %s' % u)
    ok(abs(TS.duracion(p) - (len(p['timestamps']['characters']) * 0.05)) < 1e-6,
       'duracion() = fin del ultimo caracter')

    # --- 6: LA FORMA REAL DE FAL — `timestamps` es una LISTA de bloques con tiempos continuos.
    # Es lo que rompio la primera llamada de verdad (S12 pieza 4, 2026-09-15): `hay()` daba False
    # y `alinear` se caia a whisper sin necesidad. Se parte el mismo texto en trozos y tiene que
    # dar exactamente las mismas palabras y los mismos tiempos que el bloque entero.
    texto = '[measured] On the 29th of June a Spanish court published a ruling.'
    entero = payload(texto)
    al_e = entero['timestamps']
    cortes = [0, 11, 23, 40, len(texto)]
    trozos = [{'characters': al_e['characters'][i:j],
               'character_start_times_seconds': al_e['character_start_times_seconds'][i:j],
               'character_end_times_seconds': al_e['character_end_times_seconds'][i:j]}
              for i, j in zip(cortes, cortes[1:])]
    lista = {'audio': {'url': 'x'}, 'timestamps': trozos}
    wl = TS.palabras(lista)
    ok([x[0] for x in wl] == dichas, 'lista de bloques: mismas palabras que el bloque entero')
    ok(all(abs(a[1] - b[1]) < 1e-9 and abs(a[2] - b[2]) < 1e-9 for a, b in zip(wl, w)),
       'lista de bloques: mismos tiempos que el bloque entero')
    ok(TS.hay_lista(lista) if hasattr(TS, 'hay_lista') else TS.alineacion(lista) is not None,
       'alineacion() encuentra la lista de bloques')
    ok(TS.alineacion(trozos) is not None, 'la encuentra si la lista viene suelta')
    ok(abs(TS.duracion(lista) - TS.duracion(entero)) < 1e-9,
       'duracion() da lo mismo con lista que con bloque')
    # una palabra partida JUSTO en el corte entre dos bloques tiene que salir entera
    ok('published' in [x[0] for x in wl], 'una palabra partida entre dos bloques sale entera')

    # --- desde archivo
    tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_test_ts.json')
    json.dump(p, open(tmp, 'w', encoding='utf-8'))
    ok(TS.hay(tmp), 'hay() reconoce un json en disco')
    ok([x[0] for x in TS.palabras(json.load(open(tmp, encoding='utf-8')))] == dichas,
       'leido de disco da lo mismo')
    os.remove(tmp)

    print('\n%d comprobaciones, %d fallos' % (22, len(FALLOS)))
    sys.exit(1 if FALLOS else 0)


if __name__ == '__main__':
    main()
