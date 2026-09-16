tipo: **A · episodio + shorts** · tema: **Yemen / Bab el-Mandeb** · 1 Dispatch + 4 shorts · abierta el 2026-09-15

# Ep. 13 — Yemen / Bab el-Mandeb

**El angulo:** no es el parte de guerra, es **la tenaza**. El petroleo del Golfo tiene dos salidas —Ormuz
y el Mar Rojo— y en 2026 se cerraron las dos. El **11 de septiembre**, el mismo dia, unos drones apagaron
el oleoducto saudi que existia para esquivar Ormuz **y** los huties tomaron la isla que parte el Bab
el-Mandeb. Y el dato que nadie pone: el trafico por ese estrecho **ya estaba a la mitad desde 2024**.

**Postura (Agustin, 15-sep):** concluye **contra Ansar Allah y Teheran** —tomar un estrecho por la fuerza
y decidir que banderas pasan es agresion— **y contra Riad y Washington**: once anos, dos coaliciones y
cientos de miles de muertos para entregar justo lo que la guerra decia proteger. Las dos, en ese orden.

---

## Estado — **TERMINADO** (2026-09-16)

**Master:** `salida/PaperTrail_13_Yemen_1080p.mp4` · 16:06 · 661 MB. Ficha de subida en
`publicar/SUBIR_13.md`. **Sin subir: es decision de Agustin.**

| Etapa | Estado |
|---|---|
| §2.0 Paso 0 — demanda (regla 26) | ✅ **LUZ VERDE - EVERGREEN** · `postura.md` §1 |
| §2.1 Fuentes | ✅ 27 fichas `F0-F26` verificadas |
| Interrogatorio de postura (regla 13) | ✅ `postura.md` §2 |
| §2.2 Guion | ✅ 11 beats, 2.346 palabras |
| §2.3 Voz | ✅ Brian + 5 titulos de acto con la segunda voz (regla 25) |
| §2.4 Mapa y props | ✅ mundo regional + 8 props propios |
| §2.5 Coreografia (motor v4) | ✅ 236 planos |
| §2.6 Encuadre / cortes / sync | ✅ 0 / 0 / VACIO=0 |
| §2.7 Mezcla | ✅ voz -18 dB + 5 cues + 740 efectos |
| §2.8 Render y entrega | ✅ cuerpo 15:33 + intro v3 + outro |
| `ritmo.py` | ⚠️ 2 de 3 — **se deja asi por decision suya**, detalle en `SUBIR_13.md` |
| Titulos y miniaturas (3 + 3, A/B) | ✅ `publicar/` |
| **Shorts** | ⛔ guiones escritos, **sin producir** |

## Lo que costo montar esto en esta maquina (para la proxima)

El clon del repo trae el codigo y los datos de mapa, pero **no** los assets ni el entorno. Lo que
hubo que resolver, ya resuelto y anotado para no repetirlo:

- **Dependencias:** `numpy`, `pillow`, `shapely`, `faster-whisper`, `soundfile` se instalan sin
  problema en un venv aparte. `motor.py` solo necesita PIL.
- **Assets:** llegaron en cinco zips (`assets_1..5`) y estan **desempaquetados en su sitio**:
  289 props/mapas, 18 rigs, 7 cues, hero, intro v3 y outro.
- **Tipografia:** falta **Georgia Pro** (es de pago). `produccion/props.py` lleva ahora un respaldo
  a Georgia normal que **no cambia nada** donde Georgia Pro si esta.
- **`pruebas/look/mapa_hoja.png`** no venia en los zips y `canal/marca.py` lo abre al importarse,
  asi que sin el no arrancaban las miniaturas. Reconstruido desde `mapa_base.png` (es una textura).
- **Workers del render:** el automatico (14) **no cabe en memoria** con un mundo de 9000x7697.
  `coreo13.WORKERS = 5`.

## Las tres trampas de la coreografia (medidas, no supuestas)

Estan comentadas en el codigo donde ocurren, pero conviene tenerlas juntas:

1. **Props del catalogo con texto de otros episodios.** `expediente` dice "MALVINAS FALKLANDS",
   `isla_recorte` es la silueta de las Malvinas, `factura` lleva el simbolo euro. Por eso existe
   `arte/props13.py` (8 props propios, 0 creditos).
2. **Los pines del mapa se dimensionan contra el MUNDO, no contra la ventana.** Con 9000 px de
   ancho salian discos de 190 px en pantalla. `pins_opciones` es **por sitio**, no global.
3. **Un plano por grupo de lineas deja el video muerto.** 51 planos para 934 s daban FAIL en las
   tres pruebas de `ritmo.py`. `Dir.plano()` trocea solo en tramos de 4,4 s; y en planos abiertos,
   donde la camara se sujeta contra el borde del mundo, **el corte se hace con la escala**.

## Proximo paso

1. **Revalidar F11, F15 y F17** antes de subir (§5 de `fuentes/referencia.md`) — el tema esta vivo.
2. Subir cuando Agustin lo decida, con la ficha `publicar/SUBIR_13.md` (3 titulos + 3 miniaturas).
3. **Producir los 4 shorts**: el guion esta en `shorts/GUIONES.md`; falta voz, coreografia vertical
   (`shorts.armar_vertical`, 1080x1920 nativo) y miniatura propia de cada pieza (§2.8d).

## Coste

**~60 creditos** de los 500 del ciclo: voz del episodio con Brian + los 5 titulos de acto con la
segunda voz. Mapa, props, miniaturas, mezcla y render: **0**. Los shorts estan estimados en 15-25 cr
mas. Muy por debajo del techo de USD 4 (regla 15), que es techo y no presupuesto.
