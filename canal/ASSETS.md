# ASSETS — reusar antes de generar

> **Reglas de Agustín (2026-09-08, literales):**
> 1. *"Es MUY importante armar un index y ordenar bien todos los assets que generamos con IA para que si se pueden
>    reutilizar en el futuro, se reutilicen Y NO GASTEMOS CRÉDITOS INNECESARIAMENTE."*
> 2. *"QUE EL TOPE SEA 4 USD NO SIGNIFICA QUE PUEDAS GASTARLO ASÍ LIBREMENTE AL TOPE. QUE QUEDE MUY CLARO ESO."*
>
> El tope de USD 4 por producción es un **techo que no se puede cruzar**, no un presupuesto que haya que agotar.
> Lo normal es gastar **mucho menos**: los eps. 1-3 se hicieron con 49 créditos de assets en total (~USD 1,42) y
> todo eso ya está pago y disponible. Si una producción no necesita nada nuevo, **gasta 0 en assets**.

---

## 1. Antes de generar cualquier cosa con IA

```bash
python produccion/indice_assets.py buscar <lo que necesitás>     # ej: buscar putin · buscar hangar · buscar frio
```

Si aparece algo, **se usa eso**. Si de verdad no existe, se genera **y se anota** (§3). El índice completo está en
[`canal/INDICE_ASSETS.md`](INDICE_ASSETS.md) — se regenera con `python produccion/indice_assets.py`, no se edita a mano.

Orden de decisión, de gratis a caro:

| # | Antes de… | Preguntarse | Costo si se genera igual |
|---|---|---|---|
| 1 | dibujar un prop | ¿está entre los 253 de `assets/prop_*.png`? | 0 cr, pero es tiempo |
| 2 | hacer una hoja de mapa | ¿la región ya tiene hoja (`mapa`, `mapa02`, `mapa03`, `mapa04`)? Si sí, se le **agregan puntos a su `pts.json`** | 0 cr, pero son horas |
| 3 | pedir un rig nuevo | ¿el personaje ya está en los 11? ¿sirve uno genérico (burócrata, militar, vecino) en vez de una cara real? | **1 cr** |
| 4 | pedir una cue de música | ¿sirve una de las 6 del ep. 1 o la cortina? Las cues **se reusan entre episodios** | **3 cr** |
| 5 | pedir un plano hero | ¿hay uno parecido en `produccion/hero/`? ¿el momento lo justifica? | **11-21 cr** (still + i2v) |

Regla corta: **una cara real merece rig propio; todo lo demás casi nunca lo merece.**

---

## 2. Qué hay hoy (resumen; el detalle está en el índice)

| Familia | Cuántos | Créditos ya pagados | Reusable |
|---|---|---|---|
| Rigs de personaje | 11 | 11 | siempre, en todos los episodios |
| Recortes sin fondo | 13 | 0 (fuente de los rigs) | sí |
| Hojas de expresiones | 1 | 1 | sí, cuando se corten las 6 caras |
| Planos hero | 1 (`hangar`) | 11 | el clip es del ep. 1, pero el método y el prompt sirven |
| Sets / fondos | 3 | 3 | sí, como pared con post (salieron dioramas 3D, no planos) |
| Cues de música propias | 7 | 21 | **sí, entre episodios** |
| Hojas de mapa | 4 regiones | 0 (código) | sí, agregando puntos |
| Props de papel | 253 | 0 (código) | sí |
| Intro / outro del canal | 3 | 0 | se pegan tal cual, **nunca se regeneran** |

**49 créditos ≈ USD 1,42** es todo lo que costó el catálogo entero de tres episodios. Cada episodio nuevo debería
sumarle poco: uno o dos rigs si aparece una cara nueva, y nada más.

---

## 3. Al generar algo nuevo: dejarlo anotado (obligatorio)

Sin ficha, el asset existe pero nadie lo encuentra y en tres semanas se vuelve a pagar. Dos formas, las dos válidas:

**a) Ficha `.json` al lado del archivo** — la buena para lo caro. El modelo es `produccion/hero/hangar.json`:
nombre, episodio, momento, fecha, y por cada pieza el modelo, los créditos, la referencia, el **prompt completo**, la
URL del resultado y **qué se descartó y por qué**. Esa última línea es la que evita repetir el error caro.

**b) Entrada en `canal/assets_catalogo.json`** — para lo que ya existía o no justifica ficha propia:
`{"clave": {"quien": …, "modelo": …, "creditos": N, "usado_en": [...], "notas": …}}`.

Después, `python produccion/indice_assets.py` y el índice queda al día.

**`usado_en` se completa al usarlo**, no al generarlo. Un asset generado que nunca se usó es un crédito tirado, y el
índice tiene que dejarlo ver.

---

## 4. Dónde vive cada cosa

Los assets **compartidos** (rigs, cues, props base, texturas, intro/outro) quedan fuera de las carpetas de producción,
porque son del canal y los usan todos los videos — `canal/ESTRUCTURA.md` §3. Lo que es **de un video** (su hoja de
mapa, sus props nuevos, su hero, su voz) vive en `videos/<dir>/arte/` y se indexa igual.

Un asset que nació para un episodio y sirve para todos (un rig, una cue) **se promueve** a compartido: se mueve a la
carpeta común y se anota en el catálogo. Es la única razón legítima para sacar algo de la carpeta de una producción.

---

## 5. Lo que no se hace

- Generar "por las dudas" o "para tener variantes". Cada generación se pide **para un plano concreto**.
- Regenerar algo porque no se encuentra: primero `buscar`.
- Gastar hasta el tope porque queda margen. El tope es un techo (§0), y lo que sobra sobra.
- Pedir un hero sin haber mirado si el momento se resuelve con el motor a 0 créditos (`canal/CREATIVO.md`).
- Tirar un intento fallido sin anotarlo: el descarte documentado vale casi tanto como el acierto.
