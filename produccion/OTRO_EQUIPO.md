# Continuar En Otro Equipo

Estado del traspaso: codigo preparado para Git; pruebas locales pasan. No se ha
verificado un clon limpio en otra maquina. No asumir que `git pull` copia toda
la produccion ni que una instalacion del VPS configura un escritorio Windows.

## Que Viaja Por Git

Motor, acciones de mapas, narrativa, encargos, validadores, tests, documentacion
tecnica y codigo de las producciones usadas como plantillas. Los cambios siguen
siendo opt-in; no activar timers, publicar ni gastar al comprobar la instalacion.

## Que Requiere Transferencia Privada

- Directorio completo de la produccion que se quiera continuar. El episodio 09
  esta excluido, incluidos `SUBIR.md`, `CONTINUAR_SHORTS_CON_CLAUDE.md`, sus scripts,
  guiones, JSON, miniaturas, voces y masters. No forzar su entrada a Git.
- `produccion/assets/`, `pruebas/elenco/`, musica, intro/outro y demas medios que
  use la produccion. Preservar las rutas relativas, no solo copiar el MP4.
- Configuracion local y credenciales mediante un medio privado; nunca commitearlas
  ni pegarlas en logs. El programa carga el entorno con `radar/entorno.py`.
- Las skills locales no viajan con este repositorio. Comprobar su instalacion en
  el otro equipo; no editar memorias personales para completar el traspaso.

El backup inicial es anterior a los ultimos cambios de produccion. Para trasladar
el estado nuevo se necesita una copia actual, no asumir que aquel backup lo tiene.
`versiones_animacion.py` incluye especificamente el motor y el episodio 09; leer
su seleccion y exclusiones antes de usarlo para otra produccion. Restaura siempre
en una carpeta nueva y verificar hashes antes de sustituir archivos existentes.

## Dependencias A Comprobar

Python 3.12, Pillow, numpy y shapely para la animacion; ffmpeg y ffprobe en PATH.
`shapely` no esta en el instalador actual del VPS. Para consultas de demanda,
comprobar tambien pytrends y yt-dlp; son opcionales y no se instalan solos.
Estas dependencias de escritorio no reemplazan las del Radar o THE LEDGER.

Hay tipografias con rutas fijas de Windows en `narrativa.py` y `props.py`:
Arial Bold y Georgia Pro Bold. Otro SO o un Windows sin esas fuentes requiere
resolver las fuentes antes de renderizar. No se incluyen fuentes comerciales
en Git ni se promete el mismo aspecto con sustituciones.

## Verificacion Inicial

Desde la raiz, sin renders ni llamadas pagadas:

```powershell
python -m unittest produccion.test_acciones_mapa produccion.test_narrativa produccion.test_encargo produccion.test_paquete_editorial produccion.test_paquete_subida produccion.test_metricas_produccion
python produccion/versiones_animacion.py --autotest
ffmpeg -version
ffprobe -version
```

En el equipo original, las seis suites suman 103 pruebas correctas. Esto no
sustituye comprobar assets, fuentes y un cuadro real en el equipo destino.
Para el episodio 09, continuar desde la guia privada para Claude, no desde un
guion antiguo. Los shorts aun requieren produccion; no afirmar que ya estan hechos.

Los enlaces absolutos de `SUBIR.md` cambian con el equipo. Regenerarlo con
`paquete_subida.py --actualizar` desde el manifiesto y directorio local correctos;
no modificar el master aprobado. Ver [PAQUETE_SUBIDA.md](PAQUETE_SUBIDA.md).
