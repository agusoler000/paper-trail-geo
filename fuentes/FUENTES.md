# FUENTES — de dónde salen los temas y la información

> Creado 2026-09-03. Complementa `IDEA.md` (estrategia) y `ESTILO.md` §3 (guion).

## 1. Guiones de YouTube (para temas y estructura, NO para copiar)

`fuentes/yt_guiones.py` — mismo motor que el scraper de Skool (`../scrape-skool/scraper/fetch_lesson.py`):
`yt-dlp` descubre videos sin descargarlos, `youtube-transcript-api` baja la transcripción.

```
python fuentes/yt_guiones.py buscar "Essequibo Guyana Venezuela explained" --n 6
python fuentes/yt_guiones.py canal https://www.youtube.com/@CaspianReport --n 10
python fuentes/yt_guiones.py ids zaqTvSlgexk Q-C4tosjBk8
```
Salida en `fuentes/yt/`: un `.md` por video (guion por minuto + texto corrido) y `indice.md`.
Probado 2026-09-03 con 4 videos del Esequibo: los 4 con transcripción en inglés, 1-2 min en total.

**Para qué sirve:** ver qué ángulos ya están cubiertos, cómo estructuran el hook y los giros los
canales que funcionan, y qué datos repiten todos (esos hay que verificar en fuente primaria).
**Decisión de Agustín (2026-09-03):** los datos de youtubers con reputación (Fonseca, CaspianReport,
etc.) **se usan directamente en el guion, sin verificación en fuente primaria.** El riesgo, dicho una vez:
si el youtuber se equivoca, el error se hereda con su nombre y el nuestro. Las transcripciones automáticas
sí traen errores de nombres ("Guana", "esbo"): esos se corrigen al escribir.

Canales candidatos para el modo `canal`: CaspianReport, RealLifeLore, Johnny Harris, TLDR News Global,
Wendover, Kraut, Geopolitics Explained, Warographics. (Verificar handles con yt-dlp antes.)

## 2. Reuters MCP — no es para nosotros (verificado 2026-09-03)

Reuters lanzó el 2026-07-08 un servidor MCP para que agentes de IA busquen y bajen contenido de
Reuters. **Está disponible solo para clientes de Reuters News Agency**, es decir, medios con licencia
B2B de agencia. No hay plan individual ni gratuito, y el sitio de Reuters bloquea el fetch. Para un
canal sin presupuesto no es una opción hoy. Fuentes: Editor & Publisher, anuncio de @ReutersPR.

Además, aunque tuviéramos acceso, el contenido de agencia se licencia para redistribución bajo contrato;
usarlo como base de un video monetizado requeriría esa licencia.

## 3. Alternativas gratuitas y legítimas para información

| Fuente | Qué da | Cómo |
|---|---|---|
| **Búsqueda web del asistente** | Noticias recientes con cita de medio | Ya disponible en sesión |
| **GDELT** (gdeltproject.org) | Eventos y cobertura mundial, gratis, API abierta | `api.gdeltproject.org/api/v2/doc/doc?query=...&format=json` |
| **Google News RSS** | Titulares por tema/región (incluye titulares de Reuters/AP con link) | `news.google.com/rss/search?q=...&hl=en-US&gl=US&ceid=US:en` |
| **Wikipedia + Current events** | Cronologías con referencias | Portal:Current_events, historial de artículos |
| **Fuentes primarias** | CIJ (icj-cij.org), ONU, cancillerías, bancos centrales, EIA, USGS | Son las que van citadas en el guion |
| **Natural Earth** | Mapas (ya en uso) | `pruebas/look/mapa.py` |

Las fuentes primarias quedan como opción para cuando un dato no aparezca en ningún video de referencia.
