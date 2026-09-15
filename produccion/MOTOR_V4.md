# MOTOR v4 — cómo se escribe una coreografía nueva

> Especificación: `canal/AUDITORIA_MOTOR_2026-09-15.md` §6. Implementado el 2026-09-15.
> Pieza de referencia, completa y funcionando: `videos/S12_recibos/prueba_v4.py` (25 s, vertical).
>
> **Todo lo de este documento es opt-in.** Una coreografía vieja (`Scene(png_de_1920x1080)`) rinde
> exactamente igual que antes: `videos/09_deuda_eeuu/coreo.py check` da una salida byte a byte
> idéntica a la del motor v3.

---

## 0. Ejemplo mínimo (30 líneas): mundo + cámara + HUD + subtítulos

```python
import sys, os, json
sys.path.insert(0, '../../produccion')
import motor as M, mapa_v2 as MV, props as PR

BBOX = (-6.447, -4.253, 35.40, 36.40)          # lon0, lon1, lat0, lat1
SITIOS = {'Ceuta': (-5.3213, 35.8894), 'Tarifa': (-5.6045, 36.0128)}

def build():
    M.EVENTS.clear()
    mu = MV.mundo('estrecho', BBOX, 4000, sitios=SITIOS, out_dir='arte/assets',
                  capas={'esp': (['ESP'], MV.ROL['institucion'])})      # se cachea en disco
    sc = M.Scene(mu, size=(1080, 1920), v4=True)                        # vertical NATIVO
    CE, TA = mu.P('Ceuta'), mu.P('Tarifa')

    mu.add_layer(mu.meta['capas']['esp'], 3.6, 1.5)        # el color narra: España se pinta a 3,6 s

    sc.corte(0.0, (TA[0], TA[1]), 0.95)                    # plano 1: abierto sobre el Estrecho
    sc.viaje(0.0, 6.0, (CE[0], CE[1]), 1.30, 'io')         #   ... y UN viaje motivado hacia Ceuta
    sc.corte(6.0, (CE[0], CE[1]), 2.10)                    # plano 2: corte de CONTENIDO
    sc.viaje(6.0, 12.0, (CE[0] + 30, CE[1]), 2.35, 'io')

    cifra = M.Obj(PR.card('49,000', size=190, tcolor=PR.ROJO))
    cifra.name = 'card:49,000'; cifra.x = M.Track(540); cifra.y = M.Track(760)
    cifra.on, cifra.off = 6.1, 11.8
    sc.add_hud(cifra)                                      # HUD: px de cuadro, cruza los cortes

    pal = json.load(open('audio/_palabras.json', encoding='utf-8'))     # [[palabra, t0, t1], ...]
    sc.subtitulos(pal, estilo='banda', fy=0.885, resaltar=['49,000', 'Ceuta'])
    sc.dur = 12.0
    return sc
```

`python -c "import coreo; sc=coreo.build(); print(sc.check_framing(0, sc.dur))"` tiene que dar `[]`,
y `sync.auditar(sc, 'audio/tiempos.json')` tiene que dar `VACIO: 0`. Después, `M.render(...)`.

---

## 1. `Mundo` — el suelo del video

El mapa deja de ser una hoja que aparece a veces y pasa a ser la superficie por la que vuela la
cámara. Es más grande que el cuadro, así que un plano cerrado se ve a 1:1 en vez de ser un upscale.

```python
mu = M.Mundo('assets/mundo_x.png', pts='assets/mundo_x_pts.json')
mu.P('Ceuta')                                   # px de MUNDO del sitio (regla 24: sale de lon/lat)
mu.add_layer(png, t_on, dur=1.4, mode='fade'|'wipe', t_off=None, dur_off=1.0, xy=(0,0))
mu.route(['Tarifa','Ceuta'], t0, t1, color=PR.ROJO, width=10, dotted=False, t_off=None)
mu.dark.set(t, 0.6, 'io')                       # oscurecer el mundo (planos de mesa, velos de acto)
mu.crop(t, (x0,y0,x1,y1))                       # lo usa Scene.render: compone SOLO el recorte
```

Las capas y las rutas se componen **únicamente dentro del recorte**, no sobre el mundo entero: es
la diferencia de rendimiento con `MapSheet`, que redibujaba la hoja completa cada cuadro.

`MapSheet` sigue existiendo y sin cambios: las 12 producciones anteriores lo usan.

## 2. `Scene(fondo, size=None, v4=False)`

- `fondo`: ruta de PNG, `Image` o `Mundo`.
- `size=(w, h)`: el formato **del cuadro**, por escena. `(1080, 1920)` para vertical nativo.
  `M.set_formato(w, h)` cambia además los globales `M.W`/`M.H` para el código que los usa como
  constantes. `M.render()` toma el formato del primer cuadro, no de los globales.
- `v4=True`: enciende la vida por defecto (cámara, objetos y rigs) y el flag de módulo `M.VIDA_V4`.
- `sc.W/sc.H` = cuadro · `sc.WM/sc.HM` = mundo.

Con `v4=False` (el valor por defecto) el motor recorre exactamente el camino de la v3.

## 3. Cámara: **un plano = un corte + UN viaje motivado**

```python
sc.corte(t, (x, y), z)                 # recolocación seca; emite un evento 'tick'
sc.viaje(t0, t1, (x, y), z, 'io')      # el movimiento del plano; va HACIA lo que dice la voz
```

- `z` es el zoom: ancho del cuadro / ancho de la ventana, medido en px de mundo. **Se permite
  `z < 1`** hasta `zmin = max(W/WM, H/HM)`, que es ver el mundo entero. La v3 no dejaba abrir.
- El centro se sujeta dentro del mundo.
- `sc.cam` y `sc.whip` siguen existiendo con el comportamiento de la v3.

**Trampa que arregla `corte` y que conviene entender.** En este motor el easing vive en el keyframe
que **termina** el tramo. Cerrar un plano con `pista.set(t-0.001, valor, 'hold')` —lo que parece
natural, y lo que hacían a mano las coreografías viejas— le dice al tramo *anterior entero* que no
se mueva: el viaje de ese plano se congela. Le pasaba a `prueba_vida.py` y no se había visto porque
los objetos sí se movían. `sc.corte()` hereda el easing del tramo en curso y borra el keyframe que
cayera justo en `t`, así que el corte es exacto y el viaje anterior se conserva.

### Vida de cámara (solo con `v4=True`)

```python
sc.vida = {'push': 0.010, 'push_max': 0.14, 'deriva': 9.0}   # por defecto
sc.vida = None                                                # apagada
```

Se aplica **solo en los tramos hold**, desde el último keyframe de cámara: si la coreo manda un
viaje, la vida no se pisa con él. El push va siempre hacia dentro (alternarlo pegaría un plano
abierto contra el tope del mundo y lo congelaría); lo que alterna por índice de keyframe es el
sentido de la deriva, para que dos planos seguidos no se vayan hacia el mismo lado.

## 4. HUD — la capa de pantalla

```python
sc.add_hud(obj)          # px de CUADRO, sin parallax, sin deriva, no la recorta la cámara
sc.hud                   # la lista
```

Es donde viven subtítulos, cifras grandes, rótulos de plano, tarjetas de acto, el chip `PART n OF N`
y la barra de progreso. `check_framing` los verifica contra `(0, 0, W, H)`.

**Un objeto de HUD puede cruzar un corte de cámara.** Eso es nuevo y cambia cómo se escribe: en la
v3 los carteles vivían en coordenadas del mundo y el post-pass los **apagaba** en cada corte para
que no quedaran cortados, lo que dejaba medio segundo de pantalla muda en cada juntura. Ahora se
solapan los tiempos y no hay juntura.

## 5. Subtítulos

```python
sc.subtitulos(palabras, grupos=(2,4), estilo='banda'|'papel', fy=0.86, resaltar=(),
              ancho=0.86, size=None, z=95, fade=0.08, pausa=0.25, t0=0.0, t1=1e9)
```

`palabras` es `[(palabra, t0, t1)]` — el formato de `audio/_palabras.json`. Agrupa de 2 a 4 palabras
cortando por puntuación y por las pausas reales de la voz (> `pausa` s), y no deja una palabra débil
al final del grupo (`M.DEBILES`, la misma lista que usa `shorts.py`). `resaltar` pinta esas palabras
en rojo. Devuelve los objetos creados, uno por grupo, ya en el HUD.

`estilo='banda'`: banda oscura translúcida con texto crema y borde — se lee sobre cualquier mapa.
`estilo='papel'`: tarjeta de papel con tinta — para planos de mesa.

## 6. Vida en objetos y rigs

Con `v4=True`, `Scene.add` le pone a cada objeto no-bg `wobble = 0.35°` y `bob = 1.0 px` **si la
coreo no los tocó**, y les reparte la fase. A los rigs les enciende `Rig.v4`: cabeza 4,0°, brazos
4,5°, respiración ±3 %, fase por rig y un micro-cabeceo cada 3-6 s. `o.vida = 0` / `rig.vida = 0`
deja quieto un objeto concreto; `bg=True` no tiene vida nunca.

Los números de la v3 (1,4° de cabeza, 1,2 % de respiración) medían 0,3 px en un teléfono: por eso
los recortes se leían como calcomanías.

**La fase ya no sale de `id()`.** Salía, y `id()` cambia de proceso a proceso: el render corre en un
pool de 20 y cada uno construye la escena, así que cada trozo de video tenía otra fase y en la
juntura se veía el salto. Medido: dos corridas del mismo cuadro del ep. 09 diferían 0,48/255 de
media y 215 en el peor píxel. Ahora sale de un contador que `Scene.__init__` pone a cero: **el
motor es determinista** (dos corridas del mismo cuadro dan 0,000000 de diferencia).

## 7. Detector de vacío honesto

```python
sc.visible(t, ignorar=('rotulo:', 'region:', 'sub:', 'mundo:'))
```

Devuelve los objetos que **cuentan como contenido**: no-bg, dentro de la ventana, y cuyo nombre no
empieza por los prefijos ignorados. El rótulo de plano y la etiqueta de región no son contenido —
contarlos es lo que dejaba pasar los 24 s de pantalla vacía del acto II del ep. 09.

Ojo: un `Mundo` es `bg`, así que **el mapa no cuenta como contenido**. Es a propósito: la regla es
que cada frase tenga su imagen *encima* del mapa.

## 8. `sync.py` — auditoría guion → imagen

```bash
python produccion/sync.py coreo.py audio/tiempos.json --out _qc [--guion guion.md] [--paso 2]
```
```python
import sync
r = sync.auditar(sc, 'audio/tiempos.json', out='_qc')
if r['VACIO']: sys.exit('hay pantalla vacia')
```

Escribe `_qc/sync.md` (tabla línea por línea) y `_qc/sync_NN.jpg` con **un cuadro real por línea** y
el texto de la línea debajo, marcado en rojo si tiene banderas. Banderas: `VACIO` (obligatorio 0),
`CIFRA_SIN_PANTALLA`, `LUGAR_SIN_MAPA`, `TEXTO_VIEJO`, `PROP_HUERFANO`.

Las cifras se comparan por **magnitud**: «one point one three trillion», «$1.13T» y
«1130000000000» son la misma cifra.

## 9. `mapa_v2.py` — el mapa como biblioteca

```python
mu = MV.mundo(nombre, bbox, w, roles=None, sitios={}, agua=[], rotulos_extra=[],
              capas={'alias': (paises, color, alpha)}, pins_opciones={}, out_dir='arte/assets')
im, meta = MV.hoja_v2(lon0, lon1, lat0, lat1, w, roles=..., sitios=..., agua=...)
cap = MV.capa_pais(meta, ['ESP'], MV.ROL['institucion'])      # encaja al píxel con la hoja
pin = MV.pins(meta, opciones={...})                            # punto exacto + etiqueta
```

`mundo()` guarda `mundo_<n>.png`, `_pts.json` y `_meta.json`, **comprueba la regla 24** (cada sitio a
menos de 3 px de una proyección Mercator calculada aparte; aborta si no) y **cachea**: `build()`
corre en cada worker del pool y una hoja de 4000 px no se puede regenerar veinte veces.

Dos cosas que hay que decidir a conciencia:

- **Los roles no van horneados en la hoja** si el color tiene que narrar. Van como `capas` que se
  encienden cuando la voz nombra el país. Si están puestos desde el cuadro 0 no cuentan nada.
- **El tamaño de los rótulos se mide contra la VENTANA, no contra el mundo.** Un mundo de 4000 px
  visto por un cuadro vertical muestra 1266 px de ancho: un rótulo de 66 px de mundo ocupa medio
  ancho de pantalla y se sale por el borde. Y un rótulo fuera de la franja que la cámara recorre no
  se ve nunca.

## 10. Armado vertical y voz

```python
shorts.armar_vertical(cuerpo_1080x1920, tiempos, out, hook=[...], rojo=1, resaltar=[...],
                      n=4, N=4, cue='produccion/musica/cue_04_dron.mp3', subs=False)
```

No mete el cuerpo en ninguna hoja: el cuerpo **es** la pantalla. Encima pega el gancho como tarjeta
grande sólo los primeros ~3,5 s, el chip `PART n OF N`, la barra de progreso ocre y —si el cuerpo no
los trae ya por HUD (`subs=False`)— los subtítulos. Termina con `loudnorm=I=-14:TP=-1.5:LRA=9`.
`construir()` (el armado viejo, con hoja y bloque 16:9) queda igual para reproducir entregas hechas.

`shorts.cues()` usa `_palabras.json` si está al lado del `tiempos.json`: tiempos reales por palabra
en vez del reparto por caracteres.

**Timestamps de fal.** `voz_ep.py generar` y `voz_corta.py generar` piden `timestamps: True` y
guardan la respuesta (`beat_XX.json` / `voz.json`). `alinear` saca las palabras de ahí con
`voz/timestamps.py` y **no corre whisper** (35 min de CPU menos por episodio, y las palabras son las
del guion en vez de las de una transcripción). Whisper sigue de respaldo para lo que venga de
PicsArt, que no devuelve tiempos. Test: `python voz/test_timestamps.py`.

`voz/prosodia.py <voz.wav> <tiempos.json>` mide si la narración está dirigida a ser plana.

## 11. Ritmo

```bash
python produccion/ritmo.py cuerpo.mp4 --json     # sale 0 si PASA, 1 si no
```
```python
d, ok = ritmo.veredicto('cuerpo.mp4')
```

Tres condiciones para una producción nueva: **quietos < 20 %**, **movimiento mediano ≥ 2,5** y
**ningún plano de más de 6 s sin un cambio**. La medición no cambió. La `ocupación` no entra en el
veredicto: sobre un mundo de mapa mide teal saturado, no mesa vacía.

---

## 12. Lo que NO cambió

`MapSheet`, `Obj`, `Rig`, `Track` (salvo el arreglo de `set(0, v)`), `Scene.cam/whip/shake/report`,
`prop()`, `M.render()`, la paleta de papel, `props.py`, las reglas 1-28, el formato Dispatch/Brief,
la intro v3 y el outro.

Una diferencia mínima en lo viejo: `Track.set(0, v)` ahora **reemplaza** el keyframe inicial en vez
de convivir con él perdiendo. Afecta sólo al instante t = 0 y sólo a las coreografías que lo usan
(`mp.reveal.set(0, 1, 'hold')` en el 04, el S01 y `ep02.py`): antes el primer cuadro salía con el
mapa sin revelar. Es un arreglo, no una regresión.
