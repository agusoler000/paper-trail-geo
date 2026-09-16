# Puesta en escena narrativa (opt-in)

`narrativa.py` es una capa aditiva para dirigir escenas de Paper Trail. No cambia
los valores por defecto de `motor.py`, `compo.py`, Radar ni THE LEDGER. Los episodios
anteriores siguen usando sus coreografias originales.

## Contrato

Cada escena define `kind`, `title`, `beat`, `first`, `last`, `labels`, `reveals` y
`cues`. `reveals` y `cues` apuntan a indices de linea dentro del beat de la voz
aprobada. El montador agrega `start`, `end`, `frame0` y `frame1` a 24 fps.

- Una linea pertenece a una sola escena; el montaje valida cobertura y continuidad.
- `values` contiene cantidades editoriales explicitas, nunca magnitudes inventadas
  para llenar un grafico. Las comparaciones cualitativas no tienen ejes numericos.
- `places` usa coordenadas reales. `routes` es explicito: mencionar dos paises no
  significa que exista una ruta entre ellos. Las relaciones financieras no son
  desplazamientos fisicos ni despliegues militares.
- El movimiento responde a una accion: entregar, pagar, acumular, limitar, comparar
  o perder poder de compra. Un paneo por si solo no resuelve esa accion.
- Los subtitulos conservan las palabras y tiempos de la voz existente.
- Los personajes y props se reutilizan. Esta version no necesita generar imagenes
  ni volver a generar voz con servicios de pago.

Ejemplo completo: `videos/09_deuda_eeuu/direccion_v5.py` y `coreo5.py`.

## Produccion del Episodio 09

Desde la raiz del proyecto:

```powershell
python videos/09_deuda_eeuu/coreo5.py cuadros
python videos/09_deuda_eeuu/coreo5.py render --workers 3 --width 1920
python videos/09_deuda_eeuu/intro_v5.py render
python videos/09_deuda_eeuu/entrega_v5.py
python videos/09_deuda_eeuu/verificar_v5.py
```

Los nuevos archivos quedan en `videos/09_deuda_eeuu/salida/v5/`; los originales
no se sobrescriben. Las hojas de contacto y el plan quedan en `_qc/v5/` dentro
del episodio. Revisar las escenas completas, no solo una muestra por tipo:
dos escenas pueden compartir plantilla y explicar mecanismos distintos.

Usar `entrega_v5.py` para la entrega: monta el gancho nuevo y normaliza el rango
de color de cada entrada antes de concatenar. El subcomando `coreo5.py entregar`
conserva el montador inicial con apertura anterior y no incluye esa correccion;
no usarlo como ruta de entrega de esta version.

Los clips se renderizan por separado, sin escribir en `produccion/_frames`.
La reanudacion verifica firma de codigo, direccion, tiempos y resolucion; no
reutiliza un clip simplemente porque exista. No editar el codigo durante un render.
Mantener un unico trabajo de render, incluso cuando use varios workers.

## Movimiento Geografico

`acciones_mapa.py` complementa el motor existente: rutas de longitud de arco,
trayectorias de tropas o vehiculos, llegada escalonada, orientacion y encuadre.
Ver `ACCIONES_MAPA.md` y la demostracion `videos/09_deuda_eeuu/demo_mapa_v5.py`.
La demostracion esta rotulada como movimiento ilustrativo y no forma parte del
relato factual del episodio de deuda.

## Versiones y Recuperacion

```powershell
python produccion/versiones_animacion.py create --label nombre_de_version
python produccion/versiones_animacion.py verify RUTA_DEL_BACKUP
python produccion/versiones_animacion.py restore RUTA_DEL_BACKUP
```

La copia incluye archivos ignorados por git y los medios del episodio 09.
El manifiesto registra SHA-256; se excluyen secretos, caches y frames intermedios.
`restore` recupera a una carpeta nueva y no borra ni sustituye el proyecto actual.
Los videos, audio y documentos editoriales no deben incorporarse a git.

La entrega local no publica ni sube el video: esa decision requiere QC humano.
