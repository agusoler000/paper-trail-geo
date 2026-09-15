# -*- coding: utf-8 -*-
"""Las voces del canal, por nombre. Regla de Agustin (2026-09-15): **al empezar cada video se le
pregunta que voz quiere**, antes de gastar un credito. Le gusta alternarlas entre videos.

    from voces import elegir
    VOZ_ID = elegir('brian')          # o 'george'; acepta tambien un ID de ElevenLabs tal cual

Medido el 2026-09-15 sobre la misma pieza (Ceuta, 75-80 s), ventanas de 1 s:

    george  movimiento tonal 3,15 st/s · f0 134 Hz · el de todos los videos hasta hoy
    brian   movimiento tonal 3,85 st/s · f0  96 Hz · un 22 % mas de movimiento, mas grave
    (la referencia GeoGlobeTales: 4,81 st/s)

Los titulos de acto los lee la SEGUNDA voz (`actos`), distinta del narrador (regla 25).
"""
VOCES = {
    'george': 'JBFqnCBsd6RMkjVDRZzb',
    'brian':  'nPczCjzI2devNBz1zQrb',
    'actos':  '21m00Tcm4TlvDq8ikWAM',      # la voz de los titulos de acto
}


def elegir(nombre_o_id):
    """'george' | 'brian' | 'actos' | un ID de ElevenLabs. Falla claro si no se reconoce."""
    if not nombre_o_id: raise SystemExit('falta la voz: george | brian (regla: se pregunta al empezar cada video)')
    k = str(nombre_o_id).strip().lower()
    if k in VOCES: return VOCES[k]
    if len(k) >= 18 and k.isalnum(): return str(nombre_o_id).strip()
    raise SystemExit('voz desconocida: %r (opciones: %s)' % (nombre_o_id, ', '.join(VOCES)))


def nombre(voice_id):
    for k, v in VOCES.items():
        if v == voice_id: return k
    return voice_id
