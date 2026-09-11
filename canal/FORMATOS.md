# FORMATOS — reportaje y noticia

> Pedido de Agustín (2026-09-08): "una categorización tipo reportaje o noticia, porque voy a hacer videos de reportaje o de
> noticias". Definido por el asistente con valores por defecto; los números los ajusta Agustín cuando quiera.
> **Regla de Agustín (2026-09-08): los dos formatos tienen que estar MUY bien hechos; las noticias también traen suscriptores.**
> Lo único que cambia entre los dos es el largo y la urgencia. La calidad (mapa preciso, ritmo, física, chequeos, miniatura) es la misma.
> Cada video declara su formato en la primera línea del guion: `formato: reportaje` o `formato: noticia`, y es la
> **pregunta 0 del interrogatorio** de `IDEOLOGIA.md` §2.

| | **REPORTAJE** (en pantalla: *DISPATCH*) | **NOTICIA** (en pantalla: *BRIEF*) |
|---|---|---|
| Qué es | El mecanismo detrás de un tema de fondo. Sigue valiendo dentro de un año. | Un hecho de la semana, explicado por su mecanismo. Vale 2-3 semanas. |
| Ejemplos hechos | Ep. 1 (aviación rusa), ep. 2 (AfD 44 %) | — |
| Duración | 10-12 min (mientras la retención sea baja); 15-17 min cuando suba | **4-7 min** |
| Guion | 11 beats (`ESTILO.md` §3), 1.500-2.300 palabras | **5 beats**: cold open (15 s) · qué pasó (60 s) · por qué importa (90 s) · quién gana y quién pierde (90 s) · qué mirar ahora (30 s) + NEXT. 600-900 palabras |
| Fuentes | 2+ videos de YouTube (los elige Agustín) + hoja de referencia | 2+ videos o notas de agencia; misma hoja de referencia, más corta |
| Tiempo desde el hecho | Da igual | **Publicar en ≤ 72 h** del hecho; si no, es reportaje |
| Mapa | Hoja propia del episodio (`mapa_<ep>.py`) | Hoja propia si el hecho ocurre en una región nueva; si es una región que ya tenemos, se reusa la hoja y se agregan los sitios del hecho a `pts.json`. **Misma precisión** |
| Rigs y props | Nuevos si hacen falta (1 cr c/u) | Nuevos si hacen falta (1 cr c/u); el protagonista del hecho merece su caricatura |
| Planos hero | 2 (con el tope de USD 3) | 1 en el gancho (la imagen del hecho); 2 si el tope lo permite |
| Intro / outro | Cold open → intro 8 s → cuerpo → outro 15 s | Igual |
| Shorts | **3-5, con guion exclusivo** (modelo nuevo 2026-09-08, `SHORTS.md`) | **3-4, con guion exclusivo**; si el hecho no da para 3, se hacen los que den |
| Miniatura | Cara grande + ≤ 3 palabras + un objeto | Igual, más un **sello rojo `BRIEF`** en una esquina para distinguirlo en el feed |
| Título | `PALABRA-EMOCIÓN: quién verbo qué giro` | Igual (sin fechas, tu regla) |
| Créditos / costo | 60-180 cr · USD 2,75-3,00 en fal | 30-60 cr · USD 1-1,5 en fal |
| Horas de producción | 4-5 días | 1-2 días: mismo cuidado por minuto, menos minutos |
| Publicación | Jueves 13:00 ART, quincenal | **Cuando ocurre**, martes o viernes 13:00 ART; no desplaza al reportaje |
| Lista de YouTube | Dispatches | Briefs |
| Monetización | Checklist `MONETIZACION.md` §3 | Igual **y además** la zona "eventos sensibles": nada de víctimas como gancho, el hecho se cuenta por su mecanismo; si el hecho es un atentado o una masacre de los últimos 7 días, se pregunta a Agustín antes de escribir |
| Postura | Interrogatorio completo | Interrogatorio completo (5 preguntas, no se acorta) |

## Antes del formato: qué se produce (2026-09-08)
El formato (Dispatch/Brief) es la pregunta 0 **de un episodio**. Antes va la **pregunta 00**: qué se produce —
**episodio + shorts**, **serie de shorts** (un tema, una subtemática por pieza) o **short suelto**. Lo define cómo
arranca la conversación, y cada una vive en su propio directorio: `canal/ESTRUCTURA.md`. Las series y los shorts
sueltos no llevan formato Dispatch/Brief; llevan el suyo, en `canal/SHORTS.md`.

## Cómo se marca en la pieza
- Tarjeta del cold open: el sello de papel dice `DISPATCH` o `BRIEF` debajo de PAPER TRAIL (`acto()`/tarjeta de título en la coreografía).
- Descripción de YouTube: primera línea `Dispatch ·` o `Brief ·` antes del gancho.
- Carpeta y archivos iguales para los dos (`guiones/<NN_tema>/`, `produccion/ep<NN>.py`); el formato va en el guion y en `postura.md`.

## Qué cambia en el pipeline para una noticia
**Nada de los chequeos**: 0 cortado, lugares anclados, 0 huecos > 6 s, ≥ 10 cortes/min, cuadro fijo aprobado, hoja de contacto, checklist de monetización. Lo que cambia:
1. Fase 1 igual (fuentes + interrogatorio), en 2 horas.
2. Guion de 5 beats con `checklist.py --formato noticia` (pendiente: el checklist acepta el formato y relaja el mínimo de palabras).
3. Voz: 600-900 palabras ≈ 6.000 caracteres ≈ 20 cr o USD 0,60.
4. Mapa reusado o nuevo según la región; coreografía con la plantilla corta (`ep_brief.py`, pendiente: se hace con el primer brief) y el mismo motor v3.
5. Render ~15 min; entrega con `--intro_at`; 3-4 shorts con guion propio; subida el mismo día.
