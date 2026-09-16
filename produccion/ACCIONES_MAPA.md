# Acciones Sobre Mapas

`acciones_mapa.py` agrega recorridos y actores al motor v4 sin modificar `motor.py` ni el compositor existente. Es optativo: las producciones anteriores conservan su comportamiento.

Los soldados avanzan con los pies sobre el recorrido. Los barcos y vehiculos giran siguiendo la ruta. El trazo y el primer actor comparten el mismo progreso; la camara no desplaza los objetos respecto del mapa.

## Ejemplo

```python
import motor as M
import acciones_mapa as AM

mundo = M.Mundo('mapa.png', pts='mapa_pts.json', meta='mapa_meta.json')
sc = M.Scene(mundo, size=(1920, 1080), v4=True)

ruta = AM.Ruta(mundo, ['Origin', 'Pass', 'Destination'], 2.0, 9.0)
AM.trazar(sc, ruta, color=(188, 57, 46), ancho=8, off=13.0)
actores = AM.desplazar(
    sc, 'soldado.png', ruta, 'columna',
    ancho=100, unidades=3, demora=0.8,
    modo='marcha', off=13.0,
)
AM.encuadrar_ruta(sc, ruta, actores, margen=60, t=2.0)

assert not sc.check_framing(2, 13, step=0.1, tol=0)
```

Los nombres del ejemplo deben existir en `mundo.pts`. Sus posiciones se obtienen exclusivamente de `Mundo.P`: nunca se inventan como fracciones de la pantalla. Para nuevos sitios, proyectar primero sus coordenadas originales con `mapa_v2`.

## Recorrido

`Ruta(mundo, nombres, t0, t1, easing='soft')` necesita al menos dos puntos conocidos, una duracion positiva y finita y tramos de largo mayor que cero. Rechaza puntos fuera del mundo, coordenadas no finitas y easing que pueda hacer retroceder o sobrepasar el recorrido.

| Metodo | Resultado |
| --- | --- |
| `pos(t)` | Posicion exacta en px de mundo; antes/despues devuelve origen/destino. |
| `progreso(t)` | Fraccion recorrida, entre cero y uno. |
| `heading(t)` | Grados horarios, con giros suaves y continuidad al cruzar 180 grados. |
| `puntos_hasta(t)` | Vertices revelados y punta exacta del recorrido. |

`easing='lin'` mantiene velocidad constante por distancia acumulada, incluso si los tramos tienen largos distintos. `soft`, `io`, `in` y `out` aplican su aceleracion a la ruta completa, sin frenar en cada punto intermedio. La distancia se mide sobre la proyeccion en pixeles, no en kilometros ni como velocidad militar real.

Los tramos son rectos entre puntos sobre el mapa. Para seguir costas, carreteras o pasos, aportar puntos intermedios suficientes. El modulo no calcula rutas terrestres o maritimas ni desplaza objetos a tierra automaticamente.

## Actores

`desplazar(sc, imagen, ruta, nombre, ancho=90, unidades=1, demora=0.35, modo='marcha', on=None, off=None)` devuelve una lista de `ActorRuta`.

- `ancho` esta en pixeles de mundo. El zoom decide su tamano final en pantalla.
- `marcha`: cuerpo erguido, pequeno movimiento de paso y pie sobre el ancla geografica.
- `rumbo`: centro sobre el recorrido, vehiculo orientado en el sentido de avance. El arte debe apuntar a la derecha; `actor.rot = M.Track(90)` permite corregir otra orientacion.
- `fijo`: sigue el recorrido conservando la orientacion indicada por `actor.rot`.
- `demora`: segundos entre salidas. Cada unidad tarda lo mismo y llega con igual retraso.
- `on=None`: cada unidad aparece al salir. Un `on` explicito permite mostrarla esperando en origen.
- `off=None`: permanece en destino. Un `off` explicito termina su presencia.

Cada actor expone `ancla(t)`, `salida` y `llegada`. `x(t)` e `y(t)` representan el centro del dibujo, que en marcha queda por encima del pie. El recorrido gobierna la posicion: para cambiarlo, crear otra `Ruta`; no usar `Obj.move` o `Obj.at` sobre estos actores.

Se conservan las pistas de opacidad y escala del motor. Por ejemplo, para evitar que una columna termine dibujada como varios soldados superpuestos sobre el mismo punto, se pueden retirar las primeras unidades despues de mostrar cada llegada:

```python
for actor in actores[:-1]:
    actor.fade(actor.llegada + 0.1, actor.llegada + 0.6, 1, 0)
```

No separar artificialmente los destinos para disimular el solape: si se necesita una formacion, sus puntos deben definirse expresamente en el mapa.

## Trazo Y Camara

`trazar(sc, ruta, nombre='ruta', color=(188,57,46), ancho=6, on=None, off=None)` agrega una linea revelada, flecha y pulso de llegada. No duplicar esta linea con `Mundo.route`, ya que esa funcion tiene un reloj independiente.

`encuadrar_ruta(sc, ruta, actores=(), margen=45, t=None)` devuelve `(centro, zoom)`. Si se indica `t`, aplica un corte. Considera el recorrido completo, el tamano de los actores, rotaciones, sombras, la relacion de aspecto y la vida automatica v4. Sirve para horizontal y vertical.

El encuadre aborta si el mapa no tiene superficie suficiente o una ruta demasiado ancha no cabe en vertical. Ampliar el mapa o separar planos. No se cambia la geografia para acomodarla a la camara. Recalcular despues de modificar escala o elevacion de actores, y repetir `check_framing` si se agregan viajes de camara o rotulos.

## Verificacion

`auditar_geo(ruta, tolerancia=1.0, estricto=True)` compara las posiciones con las lon/lat originales de `meta['sitios']`, usando el bbox Mercator del mapa. Sin esos datos devuelve los nombres en `sin_lonlat`; no los considera verificados. Una discrepancia superior a la tolerancia produce un error en modo estricto.

Esta auditoria no confirma que una ruta sea transitable. Para eso hay que verificar la superficie y el recorrido contra una fuente geografica adecuada. La demo comprueba tierra y mar contra Natural Earth 50m, cuya costa tiene la precision propia de esa escala.

```powershell
python -m produccion.test_acciones_mapa -v
python videos/09_deuda_eeuu/demo_mapa_v5.py cuadros
```

Las 11 pruebas cubren extremos, velocidad entre tramos desiguales, entradas invalidas, rumbo continuo, proyeccion, llegadas, orden arbitrario de render, bbox contra pixeles y sombras reales, y encuadre horizontal/vertical. La demo verifica ademas solapes de actores/rotulos y contenido tapado por el HUD.

La demo de 20 segundos esta rotulada como movimiento ilustrativo y no representa operaciones reales. Sus mapas y props se reutilizan o se dibujan localmente, con costo cero. Su comando `render` transmite cuadros directamente a ffmpeg y no utiliza `_frames`; igualmente debe respetarse el turno unico de render del proyecto.
