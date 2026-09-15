# PLAN — la pasada de vida

> Escrito el **2026-09-15**. Sale de `canal/POR_QUE_SON_SOSOS_2026-09-15.md` (el diagnóstico medido).
> Decisión de Agustín: **no se toca el episodio que se está renderizando; esto entra en el próximo.**
>
> Objetivo en una línea: **que la imagen se mueva lo suficiente como para que se note**, sin cambiar el
> guion, la voz, el arte, la paleta ni una sola regla del canal. Cero créditos.

---

## 0. Antes de tocar nada

**Regla dura (ya vigente): no se edita `produccion/motor.py` ni una coreografía mientras haya un render
corriendo.** El pool de `motor.py` levanta ~22 procesos que importan el módulo; editarlo a mitad de
camino mezcla código viejo y nuevo en el mismo video.

```bash
powershell "Get-Process python -ErrorAction SilentlyContinue | Measure-Object | Select-Object Count"
```

Más de 3-4 procesos `python` = hay render. Hoy 15-sep a las 12:20 arrancó el del **ep. 09 (deuda de
EE. UU.)**: `coreo.py` con su pool, escribiendo en `videos/09_deuda_eeuu/_frames`. **Este plan se aplica
cuando ese render termine.**

---

## 1. El hallazgo que cambia el plan (y lo abarata)

Al leer el motor para escribir esto apareció algo mejor que lo que pensaba: **los mecanismos de vida ya
existen todos**. Lo que está mal es la **calibración**, y en un caso la **fórmula**.

| Mecanismo | Dónde está | Qué hace hoy | Por qué no se ve |
|---|---|---|---|
| Push de cámara | `coreo.py` · `cut(t, name, push=0.05)` y `finalize_cam` | zoom de `z` a `z*1,05` **repartido en todo el plano** | En un plano de 30 s son **0,13 px por cuadro** |
| Idle de cabeza y brazos | `motor.py:230-245` (`Rig.pose`) | cabeza ±1,4°, brazos ±1,6° | ~1,5 px en pantalla; **0,3 px en un teléfono** |
| Respiración | `motor.py:245` | escala ±1,2 % cada 2,8 s | ±1,8 px sobre un rig de 300 px |
| Parallax | `motor.py:391` (`Scene.offset`, `depth=1.06`) | desplaza capas según profundidad | **solo actúa mientras la cámara se mueve**, y casi no se mueve |
| Props, tarjetas, sombras | — | nada | están 100 % inmóviles y ocupan más cuadro que los rigs |

### 1.1 El error de fórmula, que es la raíz

`push` es un **porcentaje por plano**, no una velocidad. El zoom va de `z` a `z*(1+push)` entre el corte
y el siguiente, sea el plano de 2 segundos o de 30. Resultado: **cuanto más largo el plano, más lento
se mueve la cámara** — exactamente al revés de lo que hace falta, porque los planos largos son los que
aburren.

Y se ve en los datos del propio ep. 06:

| Tramo | Cortes en 30 s | Duración media del plano | Movimiento medido |
|---|---|---|---|
| 11:00-11:30 | 13 | ~2,3 s | **6,58** |
| 04:00-04:30 | 0 | ~30 s | **0,58** |

Mismo push (0,05), mismo motor, mismo episodio: **once veces menos movimiento** solo por durar más.

---

## 2. Los cinco cambios

### Paso 1 · El push pasa a ser velocidad · `coreo.py` → `finalize_cam`

**Hoy:**
```python
if push and t1 > t+0.5:
    sc.zoom.set(t1, z*(1+push), 'lin')
```

**Propuesta:**
```python
PUSH_V = 0.010          # 1,0 % de zoom por segundo
PUSH_MAX = 0.14         # tope: ningun plano se acerca mas de 14 %
if t1 > t+0.4:
    k = min(PUSH_V*(t1-t), PUSH_MAX) if push is None else push
    sc.cx.set(t1, cx+DERIVA_X, 'lin'); sc.cy.set(t1, cy+DERIVA_Y, 'lin')
    sc.zoom.set(t1, z*(1+k), 'lin')
```

- La deriva lateral (`DERIVA_X/Y`, 6-10 px en el plano, alternando el sentido por corte) evita que todo
  sea siempre un acercamiento frontal.
- `push` explícito en un `cut()` sigue mandando: la coreografía puede pedir otra cosa.
- **Ojo técnico:** `Scene.window()` devuelve el cuadro entero si `zoom <= 1.005`. Los planos que hoy
  están a zoom 1,0 no tienen margen para derivar; hay que darles `z = 1.02-1.04` de base. Eso recorta un
  2-4 % del cuadro: lo detecta `check_framing()`, que ya existe y ya aborta.

**Criterio de aceptación:** `quietos < 20 %` y `movimiento mediano ≥ 2,5` en el tramo de prueba.

### Paso 2 · Subir el idle y extenderlo · `motor.py` → `Rig.pose` + `Obj`

- Cabeza `1,4° → 4°`, brazos `1,6° → 4,5°`, respiración `±1,2 % → ±3 %`.
- **Desfasar por personaje** (hoy todos usan la misma fase: respiran sincronizados, que es justo lo que
  delata que es código).
- Parpadeo cada 3-6 s si el rig tiene la pieza; si no la tiene, un micro-cabeceo.
- **Wobble de reposo en props y tarjetas**: ±0,4° y ±1 px, periodo 3-5 s, fase aleatoria por objeto.
  Son papeles sobre una mesa: que respiren como papel.

**Criterio:** en un cuadro fijo, la diferencia tiene que **verse** al comparar dos cuadros separados por
1 segundo. Si hay que buscarla, quedó corto.

### Paso 3 · Cerrar el plano · las ventanas de `win()` en la coreografía

Es el que más trabajo lleva y el que más cambia el resultado. El dato: los shorts ocupan **85-94 %** del
cuadro y los largos **34 %**.

- Ninguna ventana con menos de **55 %** de ocupación: se cierra hasta que el documento mande.
- **Tarjetas al doble.** Medida de aceptación: leerlas en el PNG reducido a **405 px de ancho** (el
  tamaño real en un teléfono). Si no se leen ahí, no existen.
- **Variar la altura del horizonte y la escala entre planos.** Hoy los 12 cuadros de la hoja de contacto
  tienen el horizonte a la misma altura.
- **Usar el rojo.** `ESTILO.md` §2.2 lo reserva para lo que está en disputa; hoy no aparece **nunca**.
  Una cifra, una zona o un sello por acto.

**Criterio:** `ocupación mediana > 55 %` y la hoja de contacto de 12 cuadros sin dos encuadres iguales.

### Paso 4 · `depth` a props y tarjetas · `motor.py`

`Scene.offset()` ya hace el parallax; solo los rigs tienen `depth` (1,06). Dar `depth` 1,02-1,10 a los
props de primer plano y a las tarjetas hace que, con la cámara en movimiento del paso 1, la mesa tenga
profundidad real. **Una hora de trabajo, y es lo que hace que parezca caro.**

### Paso 5 · Que no vuelva a pasar · el checklist

`produccion/ritmo.py` ya está escrito y probado. Agregarlo al final de la entrega con las tres metas:

| Métrica | Meta | Hoy (eps. 03/04/06) |
|---|---|---|
| quietos | < 20 % | 53-63 % |
| cortes/min | 10-15 | 10,5-11,8 ✓ |
| ocupación | > 55 % | 34-65 % |

---

## 3. Cómo se prueba antes de comprometer un episodio entero

1. Elegir **60 segundos** de un episodio ya renderizado (propuesta: ep. 06, del 2:00 al 3:00 — es donde
   la retención se cae de ~70 % a ~40 %).
2. Re-renderizar ese tramo con los pasos 1, 2 y 4 aplicados (los tres son de motor y coreografía; el
   paso 3 se hace después, sobre el episodio nuevo).
3. Correr `ritmo.py` sobre el tramo viejo y el nuevo.
4. **Primero un cuadro fijo, después el clip** (regla tuya): si el cuadro fijo no convence, no se
   renderiza nada más.
5. Mirar los dos clips seguidos. Si no se nota, se revierte y se perdió una tarde.

**Tiempo estimado:** los cinco pasos son **una jornada de código**; la prueba de 60 s, unos 20 minutos de
render en esta máquina.

---

## 4. Riesgos, y qué los cubre

| Riesgo | Cobertura |
|---|---|
| El push más rápido saca objetos del cuadro | `check_framing()` ya existe y aborta el render |
| Los planos a zoom ≥ 1,02 recortan y la hoja de mapa sangra | `caber()` y `clamp()` ya achican para que entre; revisar el primer cuadro de cada plano |
| Más movimiento = archivo más pesado | Es el mismo `crf 19`; se espera 10-30 % más de peso. No afecta la subida |
| Tocar el motor a mitad de un render | §0: comprobar procesos antes |
| Que el movimiento se note "de más" | El paso 2 es el que puede pasarse; se calibra mirando cuadros, no el número |

---

## 5. Lo que este plan **no** toca

Guion · voz · estructura de actos · intro y outro fijas · paleta de 7 colores · reglas de mapa (regla 24,
los puntos siguen siendo exactos) · el arte existente · ideología y postura · títulos y miniaturas.

Y no gasta un crédito: es render local de principio a fin.
