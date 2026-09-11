# Análisis del video 1 v2 — qué le falta y qué se cambió en la v3

> 2026-09-07. Pedido de Agustín: "buena aproximación pero sigue muy aburrido y soso; cortina musical bajita y sin
> copyright; análisis completo SOLO para mejorar, no para empeorar; le falta algo".
> Regla que apliqué: no tocar nada de lo aprobado (look, elenco, voz, guion, estructura). Solo sumar capas.

## 1. Diagnóstico con datos (v2, 15:37)

| Medida | v2 | Qué significa |
|---|---|---|
| Personaje en pantalla | **39 %** del tiempo | 9 minutos de mapa y tarjetas sin nadie que actúe |
| Huecos ≥3 s sin nada en movimiento | **14 huecos, 74 s** | tramos muertos, sobre todo entre actos |
| Gap máximo entre eventos visuales | **41 s** | casi un minuto mirando lo mismo |
| Encuadre | **1 solo plano fijo** los 15 minutos | ningún cambio de escala ni de foco |
| Audio | voz sola, sin cortina ni efectos | cada gesto es mudo: el papel no suena, el sello no golpea |
| Color | ~55 % del cuadro es madera marrón | el mapa era chico (1200×720) |

**Lo que "le falta"** no es una cosa: son cinco capas que todo video de este género tiene y este no tenía.
La voz sola, por buena que sea, no sostiene 15 minutos sobre un plano fijo y mudo.

## 2. Qué se agregó en la v3 (sin quitar nada)

1. **Cortina musical.** Kevin MacLeod, CC BY 4.0 (gratis con crédito, ver `CREDITOS_MUSICA.md`).
   Perfilé 8 pistas por energía y brillo; van "Lost Frontier" y "Deliberate Thought" (calmas, graves) y
   "Crypto" (tensión) encadenadas con crossfade. Nivel: 14 dB bajo la voz, con ducking de 6 dB más
   mientras habla → queda ~19 dB por debajo, "bajita" como pediste.
2. **Diseño de sonido.** 464 eventos sincronizados con la animación, sintetizados sin derechos: papel que se
   desliza (65), tarjetas que aparecen (118) y se van (78), entradas y salidas de personaje (34), fichas y
   dominós (30), sellos (7), calendarios (2), lápiz que dibuja el mapa (4), golpe de puño (2), y un golpe
   musical grave al entrar cada acto (5). El motor los emite solo: cada `pop`, `move`, `enter`, `slam`
   registra su sonido.
3. **Cámara.** Acercamiento lento durante cada acto (1,10-1,14×), punch-in al cold open, zoom al mapa
   cuando se dibuja, zoom a Moscú cuando llega el dron, zoom a Yakutia en el acto V. El plano deja de ser
   uno solo.
4. **Tarjetas de acto.** "ACT I · THE FLEET", etc., con su golpe musical. Marcan el ritmo y le dan al
   espectador la sensación de avance.
5. **Personaje presente en los huecos.** El Burócrata hace de anfitrión en la ancla geográfica y en el
   cierre; el Ejecutivo señala las rutas de repuestos; el Militar mira llegar el dron; el Trabajador ve
   caerse el avión a pedazos. Personaje en pantalla pasa de 39 % a ~62 %.
6. **Micromovimiento continuo.** Todos los rigs respiran de hombros y cabeza (±1,5°) aunque estén
   quietos; las tarjetas oscilan 0,8°. Nada queda clavado.
7. **Mapa más grande** (1350×810 en lugar de 1200×720): menos madera, más mapa.

## 3. Lo que NO toqué y por qué

- El guion y la voz (aprobados). Cambiar texto obligaría a pagar otra narración.
- El look de papel y el elenco.
- La estructura de 11 beats y los tiempos: la coreografía sigue sincronizada frase por frase.

## 4. Lo que sigue faltando, en orden de impacto (para la v4, si la querés)

1. **Planos de detalle con recorte.** Hoy la cámara solo acerca. Un plano cerrado real del sello cayendo,
   o del avión canibalizado, con las piezas grandes, daría el "corte" de edición que tienen los canales
   de referencia. Costo: cero créditos, un día de trabajo en el motor (composición por plano).
2. **Boca que se mueve.** Los personajes no hablan; el narrador es en off. Está bien para el estilo, pero
   una boca de 2 posiciones en Zelensky y Putin cuando se los cita daría vida barata.
3. **Un remate visual por acto** más fuerte que los actuales (el avión que se pliega solo, el mapa que se
   oscurece). Hoy los gags son chicos; uno grande por acto se recuerda.
4. **Miniatura y título.** Sin eso el video no existe para YouTube. Todavía no hay nada.
5. **Voz: variantes.** George va bien; probar la misma dirección con "Brian" en un acto para comparar en
   contexto largo cuesta 15 créditos.
