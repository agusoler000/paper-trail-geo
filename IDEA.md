# Canal de geopolítica en inglés

**Estado (2026-09-07):** en producción. Video 1 terminado, identidad y calendario en `canal/`.
**Decisión de Agustín (2026-09-07): este canal es la apuesta máxima.** Marlowe's Alley (`../canal_youtube/`)
ya no tiene prioridad ni reserva de créditos; los 500 créditos por ciclo son de este canal.

> Lo que sigue abajo se escribió el 2026-08-31, cuando la idea estaba en pausa detrás de Marlowe. Las
> referencias a esa prioridad quedan como registro.

---

## 1. La idea en una frase

Canal de geopolítica en inglés que toma **temas e información** de canales de geopolítica en español que
el usuario ya sigue, los reescribe con estilo propio y los publica con animación propia.

---

## 2. La tesis (por qué el modelo es sólido)

**En geopolítica la información es commodity.** Nadie tiene fuentes exclusivas: Caspian Report,
RealLifeLore, Johnny Harris y TLDR leen los mismos cables de Reuters y los mismos informes de think tanks.
La diferencia entre un canal de 3M de views y uno de 3.000 no es la información — es la presentación.

**Consecuencia dura:** si la info es la misma que la de todos, el estilo no es un detalle, es el producto
completo. Ahí se gana o se pierde el canal. Todo el esfuerzo va ahí.

---

## 3. El modelo operativo

```
Canal fuente (español)  →  extraer tema + hechos  →  reescribir con estilo propio (inglés)
                                                  →  animar  →  publicar
```

---

## 4. Los dos filtros que hacen o rompen el canal

### 4.1 Trampa: el arbitraje circular

Muchos canales de geopolítica en español **son ellos mismos resúmenes de fuentes en inglés** (Reuters, FT,
The Economist, think tanks anglosajones). Copiar eso y llevarlo al inglés no arbitra nada: es devolver
contenido anglo al mercado anglo, varios días tarde y de segunda mano.

**Filtro de tema:** ¿este tema ya lo cubre bien alguien en inglés?
- Sí → saltear.
- No → adelante.

### 4.2 Dónde está el hueco real: Latinoamérica

Los canales de geopolítica en inglés cubren Rusia, China y Medio Oriente hasta el hartazgo, y
**Latinoamérica casi nada**. Ahí está el arbitraje genuino:

- Esequibo (Guyana / Venezuela)
- Canal de Panamá
- Litio argentino / triángulo del litio
- Cobre chileno
- Venezuela como actor geopolítico, no como nota policial
- México como actor geopolítico (no crónica de cárteles)
- Posición de Brasil en BRICS
- Sáhara Occidental y Marruecos desde la óptica española
- Gibraltar, rutas migratorias de Canarias

---

## 5. La línea legal (es la única que importa)

- **Los hechos NO tienen copyright.** Que Turquía controle el Bósforo y eso le dé palanca sobre el grano
  ruso es un hecho. Decirlo en inglés no es infracción.
- **La traducción SÍ está protegida.** Traducir un guion es de las cosas *más* claramente infractoras —
  más que parafrasear — porque la traducción es un derecho exclusivo enumerado del autor.
- Riesgo práctico de que un canal español detecte y accione contra un canal en inglés: muy bajo.
- **Detalle operativo real:** si copiás la información también copiás los errores. Replicar un error del
  original es la prueba forense de la copia, y la audiencia anglo de geopolítica es mucho más quisquillosa
  con los datos que la hispana.
- **Lo que da strike inmediato:** reusar su material (clips, mapas, gráficos, música). Content ID lo
  detecta solo. Cero de eso.

---

## 6. Economía del nicho

- **Ícono amarillo crónico.** Guerra, conflicto y muertes caen en "controversial issues and sensitive
  events" de las guías de anunciantes. El RPM teórico de $15 se convierte en ~$3 justo en los videos que
  más views hacen. Es el problema estructural del nicho.
- **La respuesta del nicho: se vive de sponsors, no de AdSense.** Ground News, Brilliant, NordVPN y Nebula
  patrocinan medio nicho. Un canal de 50k subs comprometidos saca más de un deal que de un año de AdSense
  amarillo. Eso cambia el cálculo: **no hace falta volumen masivo, hace falta audiencia nicho y creíble.**
- **Mitigación:** priorizar geopolítica *evergreen* (por qué esta frontera tiene esta forma, cómo funciona
  un cuello de botella marítimo, geografía de recursos) sobre noticias de conflicto activo. Es atemporal
  —sin deadline de 72 h— y mucho más segura para anunciantes.

---

## 7. Estilo visual — opciones evaluadas

> ⚠️ **SUPERADO el 2026-08-31.** Esta sección queda como registro del razonamiento original.
> La decisión vigente es **caricatura animada de recorte (cutout) con movimiento real** — ver
> `ESTILO.md` y `ANIMACION.md`. Lo que hacía inviable la caricatura en esta tabla ("costo alto,
> baja la cadencia") era el supuesto de animar el 100 % del metraje; el presupuesto de densidad de
> animación (`ESTILO.md` §6) lo resuelve. Lo que sí se rompió, a cambio, es la cadencia semanal.

| Estilo | Costo/minuto | Diferenciación | Encaje con la fábrica |
|---|---|---|---|
| Mapa-céntrico (Caspian / RealLifeLore) | Muy bajo | Baja — lo hacen todos | Perfecto: DepthFlow sobre mapas |
| **Ilustración editorial animada** | Medio | **Alta — hueco real** | Muy bueno: SDXL + LoRA de estilo |
| Infográfico-cinemático (Wendover / Polymatter) | Bajo | Media-alta | Bueno, pero exige datos duros por video |
| Caricatura / sátira | Alto | Máxima | Malo: baja la cadencia a 1-2 videos/mes |

**Recomendación: híbrido editorial + mapas.** Ilustración estilizada tipo portada de The Economist
—paleta limitada, simbólica, no literal— animada con parallax, alternando con mapas cuando el tema lo pide.

Razones: barato por minuto, el pipeline existente ya lo hace, y sobre todo **gana en miniaturas**, que en
este nicho decide más que el video mismo. La ilustración editorial destaca en un feed lleno de capturas de
Putin con flechas rojas.

**Descartado:** caricaturizar personas reales identificables. Los anunciantes lo evitan y entra en terreno
de medios manipulados.

---

## 8. El problema de la credibilidad de la voz (y su solución)

La geopolítica en inglés se sostiene en la autoridad del narrador. Con TTS eso normalmente se cae: suena a
granja de contenido y esa audiencia lo detecta en 10 segundos.

**Solución: no presentarse como persona, presentarse como publicación.** Nada de host ficticio con nombre
y "hey guys". Nombre editorial, voz de narrador institucional, tono documental. La audiencia acepta
perfectamente una voz sin cara si el marco es "medio", y rechaza una voz sintética que finge ser un tipo.
Beneficio extra: libera de mantener consistencia de personaje y hace el canal más comprable para sponsors.

---

## 9. Reglas de transformación del guion (borrador)

1. Ver el video fuente y anotar **solo hechos** — datos, fechas, cifras, actores. Nunca frases.
2. **Cerrar el video antes de escribir.** Con el video abierto se traduce sin querer.
3. **Cambiar la estructura.** El guion de geopolítica en español suele ser cronológico y de arranque lento.
   El formato que retiene en inglés es: tesis primero, gancho en 15 segundos, frases cortas, "por qué te
   importa" antes del minuto 1. Una traducción literal suena rígida y se cae en retención.
4. **Agregar una cosa que el original no tenía**: un mapa, un dato, un contraargumento. Ese es el
   diferencial y lo que convierte esto en canal propio en vez de eco.
5. (Opcional, recomendado) Verificar los datos duros contra fuente primaria — Reuters, comunicados
   oficiales, informes de think tanks, datos de IEA / FMI / Banco Mundial. ~30-40 min por video. Elimina
   errores heredados y suele revelar un ángulo mejor que el original no vio.

---

## 10. Qué se reusa de la fábrica de Marlowe (~60 %)

**Sí se reusa:** ComfyUI/SDXL, Kokoro/Chatterbox TTS, faster-whisper (subtítulos), render FFmpeg,
DepthFlow (parallax — ideal para mapas), orquestación n8n, compositor PicsArt.

**No se reusa:** LoRA de Marlowe, estética noir, voz del personaje, biblia de personaje entera.

---

## 11. Decisiones ya tomadas

- Idioma del canal: **inglés**.
- Enfoque: **evergreen** por sobre noticias de actualidad (la fábrica es lenta; las noticias mueren en 72 h).
- Monetización objetivo: **sponsors** desde el video 1, no AdSense.
- Formato de marca: **publicación**, no persona.
- Nicho de tema prioritario: **Latinoamérica y España** (el hueco desatendido en inglés).
- ~~Cadencia objetivo: semanal.~~ → **quincenal**, 7-8 min + 2 shorts/semana (2026-08-31).
- Descartado: caricatura de figuras reales; reusar material audiovisual ajeno.

### Añadidas el 2026-08-31

- Estilo visual: **caricatura animada de recorte de papel** (linaje Gilliam / Reiniger), paleta de
  7 colores, escenario madre "la mesa de mapas". Detalle en `ESTILO.md`.
- Regla narrativa: **guion 100 % serio, el dibujo hace los chistes** ("Deadpan Dispatch").
- Las naciones se representan como **objetos** (fichas, sellos, banderas), nunca como personas.
- **Elenco fijo de 8 arquetipos y 8 escenarios**, cerrados. Es lo que hace amortizable la biblioteca.
- Motor de animación: **MP Scene por JSON**, render a costo 0. Probado y funcionando (`pruebas/`).
- La IA de video queda como **condimento** (12-20 s por video), nunca como motor.

---

## 12. Decisiones pendientes

- [x] ~~Estilo visual definitivo~~ → **decidido 2026-08-31**: cutout animado, ver `ESTILO.md`.
- [ ] **Voz: ¿TTS, voz clonada o voz propia?** Sigue siendo la decisión más grave. Investigada a
      fondo el 2026-08-31 → **`VOZ.md`**. El acento quedó descartado como problema; el hueco real es
      que no hay precedente de narración sintética con sponsors de ese tier. Test decisor en `VOZ.md` §8.
- [x] Nombre editorial del canal → **Paper Trail** (decisión de Agustín 2026-09-07; análisis y marcas en `canal/NOMBRE.md`).
- [ ] Lista concreta de canales fuente en español y cuáles pasan el filtro §4.1.
- [ ] Set de reglas de guion como prompt operativo automatizable (base ya escrita: `ESTILO.md` §3).
- [ ] Miniaturas y títulos — sin resolver, y con modelo de sponsors el CTR es el juego entero.
- [ ] Validar que existe demanda en inglés para geopolítica de LatAm/España.

---

## 13. Primer paso al retomar

~~Generar 3-4 imágenes de prueba con SDXL en estilo ilustración editorial.~~

**Hecho el 2026-08-31**: el look y el motor están probados con un render real
(`pruebas/demo_mesa_de_mapas.mp4` — 7 s, 1080p, 0 créditos, sin difusión).

Próximo paso: **mirar ese demo y decidir si el cutout rígido cierra como identidad de marca.**
No tiene squash-and-stretch ni deformación de malla — es Gilliam, no Disney. Si la expectativa interna
es más alta, hay que saberlo antes de construir la biblioteca de rigs, no después.

**No arrancar producción sin haber clavado el look.** En este canal el estilo es el producto entero (§2).
