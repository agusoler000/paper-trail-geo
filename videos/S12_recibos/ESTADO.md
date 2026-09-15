# S12 · THE RECEIPT — estado y traspaso

> **2026-09-15.** Todo lo que sigue está en `videos/S12_recibos/`.
> Pedido de Agustín: 4 shorts, **2 de `iran war` y 2 de `immigration`**, como prueba.

---

## 1. Qué está hecho

| | Estado |
|---|---|
| **Paso 0 · demanda validada** (regla 26) | ✅ US **y** UK, con `produccion/demanda.py` |
| **Hoja de fuentes** con cada cifra verificada hoy | ✅ `fuentes/referencia.md` (F1-F4 + erratas) |
| **4 guiones** | ✅ 168-188 palabras · **89, 95, 91 y 100 s** (mínimo 50 s, regla 17) |
| **`shorts/serie.json`** con títulos, miniaturas y ficha | ✅ |
| **Props nuevos** dibujados por código | ✅ `bandera_ir`, `hotel`, `petrolero`, `sello_same`, `sentencia` + 52 cuadros de animación |
| **Hoja de mapa** del Estrecho, 16:9, puntos comprobados | ✅ `arte/mapa.py` → `mapa12_*` |
| **Partitura** de las 4 piezas | ✅ `escenas.py` (con el verbo `seq`) |
| **Coreografía** | ✅ `coreo.py` (con `secuencia()` y el paso 1 del plan de vida) |
| **Textos de voz dirigidos** | ✅ `shorts/*/audio/texto.txt` |
| **Miniaturas** | ✅ `publicar/miniaturas/*.jpg` |
| **`armar.py` / `publicar.py`** adaptados a esta serie | ✅ (ya no quedan referencias a la S10) |

---

## 2. Qué falta, en orden

```bash
# 1 · VOZ — la llamada a PicsArt la hace el asistente por MCP (eleven-v3, George).
#     ~22 créditos de los 500 ya pagados. 0 USD contra el tope de fal.
python voz_corta.py bajar 1 <url>      # y 2, 3, 4

# 2 · ALINEAR — whisper local repone los timestamps que PicsArt no da
python voz_corta.py alinear 1          # y 2, 3, 4  -> audio/tiempos.json

# 3 · ENCUADRE — regla 1: tiene que dar 0
python coreo.py check 1                # y 2, 3, 4

# 4 · RENDER del cuerpo
python coreo.py render 1               # y 2, 3, 4

# 5 · ARMADO vertical + sello PART n OF 4 + outro
python armar.py

# 6 · RITMO (paso 5 del plan de vida)
python ../../produccion/ritmo.py shorts/01_tanque/salida/01_tanque.mp4

# 7 · FICHA DE SUBIDA + copias < 10 MB
python publicar.py                     # -> publicar/SUBIR.md + PLAN_SUBIDA.json + _up/
```

**El `SUBIR.md` se le pasa a Agustín por chat en cuanto exista el archivo**, y de nuevo cada vez que
se regenere. Nunca antes de que el vídeo exista; si va antes, lleva ⛔ arriba.

---

## 3. Lo que necesita decisión de Agustín, y no la tiene

1. **El interrogatorio de postura (regla 13) no se hizo.** Los cuatro guiones se escribieron
   directamente porque el pedido vino con el tema ya elegido y con prisa. El encuadre que usan, y
   que hay que confirmar o cambiar **antes de gastar la voz**:
   - **Piezas 1 y 2 (Irán):** el sujeto es *la reserva* y *el mecanismo del seguro*, no una
     administración. No hay juicio sobre quién abrió la reserva.
   - **Piezas 3 y 4 (inmigración):** el sujeto es **un contrato, un departamento y un tribunal**.
     Ni una frase tiene un colectivo de personas como sujeto. La pieza 3 dice en voz *«You can argue
     about how many people should come. This is not that argument»*, que es a la vez la línea
     editorial y la defensa de monetización.
2. **El orden y el horario de publicación.** La propuesta está en `serie.json`: las cuatro el mismo
   día, ~2 h entre piezas, las dos de Irán primero porque `iran war` es la búsqueda con volumen en
   los dos países.

---

## 4. Para la otra sesión: la mejora de animación

**Está fuera de esta producción a propósito** (decisión de Agustín, 15-sep: *«olvídate de esto, deja
todo listo para los shorts y otra sesión se encargará de esta mejora»*).

- **Análisis y medidas:** `canal/REFERENCIA_GEOGLOBETALES_2026-09-15.md`
- **Prueba funcionando:** `videos/S12_recibos/prueba_vida.py` (25 s de la pieza 4, render local,
  0 créditos). `python prueba_vida.py cuadro | hoja | render | medir`

Dónde quedó, medido con `produccion/ritmo.py`:

| | Nuestros eps. | **La prueba** | GeoGlobeTales (11,9 M vistas) |
|---|---|---|---|
| movimiento | 0,55-0,74 | **6,97** | 9,25 |
| cortes/min | 10,5-11,8 | **16,8** | 66,5 |
| ocupación | 34 % | **72,5 %** | — |
| quietos | 53-63 % | 27,3 % | 10,7 % |
| regla 1 | — | **0 violaciones** | — |

**Lo que funcionó:**
1. El mapa deja de ser una hoja sobre la mesa y pasa a ser **el suelo del plano**; la cámara vive
   dentro (ocupación 34 % → 72 %).
2. **Cortes de contenido, no de encuadre:** la pieza alterna dos escenarios, MAPA y MESA. Saltar la
   cámara dentro del mismo plano sube la métrica y **queda grotesco** — eso fue la v2 y se descartó.
3. **El color narra:** cada país se pinta cuando la voz lo nombra.
4. Subtítulo palabra a palabra, limpio (banda translúcida), no la tarjeta de papel con marco.
5. El mapa se rehízo con **bajío, sombra proyectada y grano de papel**: antes eran dos planchas de
   color liso con una línea negra encima.

**Lo que falta, y es lo único que queda para cerrar la brecha:**

> **Los quietos siguen en 27,3 % contra una meta de 20 %, y todo viene de los planos de mesa.** El
> papel es tan liso que un push de cámara sobre él no cambia nada medible — ni se nota. Dar deriva
> propia a los objetos bajó de 31,3 % a 27,3 %, y ahí se acaba lo que se puede hacer desde la
> coreografía.
>
> Lo que lo arregla es el **paso 2 del plan** (`canal/PLAN_PASADA_DE_VIDA.md`): subir el idle de los
> rigs (cabeza 1,4° → 4°, brazos 1,6° → 4,5°, respiración ±1,2 % → ±3 %), desfasarlo por personaje y
> meter wobble de reposo en props y tarjetas. Más el **paso 4**: `depth` a props y tarjetas para que
> el parallax funcione. **Los dos tocan `produccion/motor.py`**, que estaba bloqueado por el render
> del ep. 09 — **ese render terminó el 15-sep a las 13:57, así que ya se puede.**

**Trampas encontradas por el camino, para no repetirlas:**
- `motor.Rig` se ancla por la **esquina superior izquierda**, no por los pies. Colocarlo a ojo dio 14
  violaciones seguidas de la regla 1. En la prueba se coloca midiendo su `bbox()` real contra la
  ventana.
- Un subtítulo anclado a la cámara **no puede cruzar un corte**: en el instante del corte la ventana
  salta y queda colocado con las coordenadas del plano viejo. Hay que partirlo en los límites.
- El bbox del mapa tiene que ser **16:9**. Con la hoja casi cuadrada, España quedaba permanentemente
  fuera de cámara porque `Scene.window()` limita la cámara al lienzo.
- Al pintar un país, **la marca de Ceuta tiene que ir por encima del color**: Natural Earth 50m no
  separa el enclave y el mapa acababa afirmando que Ceuta es Marruecos.
- `Scene.window()` devuelve el cuadro entero si `zoom <= 1,005`: un plano a 1,0 no tiene por dónde
  derivar.
