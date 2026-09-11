# Música del video (estado 2026-09-07)

**Decisión de Agustín:** cortina dramática, "sin copyright y todos esos problemas". Por eso la cortina final
NO usa las pistas de Kevin MacLeod (que exigen crédito), sino **cues generadas a medida con Lyria 3 Pro**
vía PicsArt, 3 créditos cada una, sin atribución obligatoria a terceros. Están en `produccion/musica/cue_*.mp3`:

| Cue | Actos | Carácter pedido |
|---|---|---|
| cue_01_intro | título, cold open, promesa, ancla, prensa | drone grave, piano lejano, reloj, inquietud |
| cue_02_flota | acto I | cellos fríos, tic metódico, hangar de noche |
| cue_03_partes | acto II | (copia de cue_02: Lyria bloqueó 3 fraseos "industriales" por política no especificada) |
| cue_04_dron | acto III | latido grave a 76 bpm, cuerdas que suben, peligro desde el cielo |
| cue_05_pais | acto IV | metales y cuerdas graves, espacio enorme, algo que se rompe despacio |
| cue_06_siberia | acto V, cierre, cliffhanger | viento sobre hielo, cuerdas dolientes, final sin resolver |

Además: **pulso grave sintetizado** (numpy, sin derechos) que acelera en los actos III, IV y el cierre, y
**silencio de 0,7 s** antes de cada golpe de acto. Mezcla en `mezcla2.py`: cortina 12 dB bajo la voz, ducking −5 dB.

Nota sobre derechos: el output de Lyria vía PicsArt se rige por los términos de PicsArt (mismo hueco legal ya
anotado en `ANIMACION.md` §0 para todo insumo pago). Es el mismo riesgo que el resto del material generado.

---

# (Archivo) Pistas de Kevin MacLeod, CC BY 4.0 — solo si se usan, crédito obligatorio

Las cortinas son de **Kevin MacLeod (incompetech.com)**, licencia **Creative Commons: By Attribution 4.0**
(https://creativecommons.org/licenses/by/4.0/). Es gratis para uso comercial y monetizado en YouTube a cambio
del crédito. Sin el crédito, es infracción.

Texto para pegar en la descripción del video 1:

```
Music by Kevin MacLeod (incompetech.com)
"Lost Frontier", "Deliberate Thought", "Crypto"
Licensed under Creative Commons: By Attribution 4.0
https://creativecommons.org/licenses/by/4.0/
```

Pistas descargadas en `produccion/musica/` (2026-09-07) y su perfil medido:

| Pista | Dur | Carácter medido | Uso |
|---|---|---|---|
| Lost_Frontier | 4,6 min | documental, lenta | cortina base |
| Deliberate_Thought | 3,0 min | muy calma, grave, sin brillo | cortina base |
| Crypto | 3,4 min | tensión sorda | acto del dron |
| Anguish | 4,0 min | oscura, baja | reserva |
| Dark_Times | 3,1 min | oscura, algo de brillo | reserva |
| Cold_Sober | 3,4 min | jazz, brillante, fuerte | no para cortina |
| Long_Note_Two | larga | drone | reserva |
| Heavy_Interlude | corta | golpe | stinger alternativo |

Mezcla: cortina a −23 dB respecto de la voz, con ducking de −9 dB mientras habla (`mezcla.py`).
Efectos de sonido: sintetizados en `mezcla.py`, sin derechos de terceros.
