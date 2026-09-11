# INDICE DE ASSETS — generado por `produccion/indice_assets.py`

> **No editar a mano.** Se regenera con `python produccion/indice_assets.py`.
> Regla y criterios en `canal/ASSETS.md`. Los metadatos que el disco no sabe (modelo, prompt, quien es,
> en que episodio se uso) salen de `canal/assets_catalogo.json` y de las fichas `.json` al lado del archivo.

Generado: **2026-09-11** · assets con costo acumulado: **55 creditos** (~USD 1.59 a $0,029/cr).

## rigs — 16 creditos

Personajes de papel recortados en piezas (cabeza, torso, 2 brazos x 2 segmentos). REUSABLES SIEMPRE: el ep. 5 usa los del 1 al 4.

| Clave | Que es | Modelo | Cr | Usado en | Ruta |
|---|---|---|---|---|---|
| `01_burocrata` | El Burocrata | flux | 1 | 01_aviacion_rusa | `pruebas/elenco/rig/01_burocrata` |
| `02_militar` | El Militar | flux | 1 | 01_aviacion_rusa | `pruebas/elenco/rig/02_militar` |
| `03_ejecutivo` | El Ejecutivo (aerolinea, negocios) | flux | 1 | 01_aviacion_rusa | `pruebas/elenco/rig/03_ejecutivo` |
| `04_trabajador` | El Trabajador / mecanico (overol azul, casco naranja) | flux | 1 | 01_aviacion_rusa | `pruebas/elenco/rig/04_trabajador` |
| `05_jurista` | El Jurista | flux | 1 | 01_aviacion_rusa | `pruebas/elenco/rig/05_jurista` |
| `06_vecino` | El Vecino / ciudadano de a pie | flux | 1 | 01_aviacion_rusa | `pruebas/elenco/rig/06_vecino` |
| `09_lider_a` | Trump | flux | 1 | — | `pruebas/elenco/rig/09_lider_a` |
| `10_lider_b_v2` | Putin (v2) | flux | 1 | 03_kiev_belarus | `pruebas/elenco/rig/10_lider_b_v2` |
| `11_zelensky` | Zelensky | flux | 1 | 03_kiev_belarus | `pruebas/elenco/rig/11_zelensky` |
| `12_weidel` | Alice Weidel (AfD) | flux-2-pro | 1 | 02_afd_alemania | `pruebas/elenco/rig/12_weidel` |
| `13_lukashenko` | Lukashenko | flux-2-pro | 1 | 03_kiev_belarus | `pruebas/elenco/rig/13_lukashenko` |
| `14_milei` | — | flux (sin ficha) | 1 | — | `pruebas/elenco/rig/14_milei` |
| `15_islander` | — | flux (sin ficha) | 1 | — | `pruebas/elenco/rig/15_islander` |
| `16_vdl` | — | flux (sin ficha) | 1 | — | `pruebas/elenco/rig/16_vdl` |
| `17_xi` | — | flux (sin ficha) | 1 | — | `pruebas/elenco/rig/17_xi` |
| `18_rama` | — | flux (sin ficha) | 1 | — | `pruebas/elenco/rig/18_rama` |

## recortes — 18 creditos

PNG sin fondo de cada personaje. Para los que ya tienen rig es el paso previo al mismo asset (0 cr aparte); los que no lo tienen (manos, multitud) se usan enteros con cutout().

| Clave | Que es | Modelo | Cr | Usado en | Ruta |
|---|---|---|---|---|---|
| `01_burocrata` | El Burocrata — fuente del rig, no cuesta aparte | flux | 0 | 01_aviacion_rusa | `pruebas/elenco/cut/01_burocrata.png` |
| `02_militar` | El Militar — fuente del rig, no cuesta aparte | flux | 0 | 01_aviacion_rusa | `pruebas/elenco/cut/02_militar.png` |
| `03_ejecutivo` | El Ejecutivo (aerolinea, negocios) — fuente del rig, no cuesta aparte | flux | 0 | 01_aviacion_rusa | `pruebas/elenco/cut/03_ejecutivo.png` |
| `04_trabajador` | El Trabajador / mecanico (overol azul, casco naranja) — fuente del rig, no cuest | flux | 0 | 01_aviacion_rusa | `pruebas/elenco/cut/04_trabajador.png` |
| `05_jurista` | El Jurista — fuente del rig, no cuesta aparte | flux | 0 | 01_aviacion_rusa | `pruebas/elenco/cut/05_jurista.png` |
| `06_vecino` | El Vecino / ciudadano de a pie — fuente del rig, no cuesta aparte | flux | 0 | 01_aviacion_rusa | `pruebas/elenco/cut/06_vecino.png` |
| `07_manos` | Par de manos (sostienen tarjetas y fotos) | flux | 1 | 01_aviacion_rusa, 03_kiev_belarus | `pruebas/elenco/cut/07_manos.png` |
| `08_multitud` | Multitud de papel | flux | 1 | 02_afd_alemania | `pruebas/elenco/cut/08_multitud.png` |
| `09_lider_a` | Trump — fuente del rig, no cuesta aparte | flux | 0 | — | `pruebas/elenco/cut/09_lider_a.png` |
| `10_lider_b_v2` | Putin (v2) — fuente del rig, no cuesta aparte | flux | 0 | 03_kiev_belarus | `pruebas/elenco/cut/10_lider_b_v2.png` |
| `11_zelensky` | Zelensky — fuente del rig, no cuesta aparte | flux | 0 | 03_kiev_belarus | `pruebas/elenco/cut/11_zelensky.png` |
| `12_weidel` | Alice Weidel (AfD) — fuente del rig, no cuesta aparte | flux-2-pro | 0 | 02_afd_alemania | `pruebas/elenco/cut/12_weidel.png` |
| `13_lukashenko` | Lukashenko — fuente del rig, no cuesta aparte | flux-2-pro | 0 | 03_kiev_belarus | `pruebas/elenco/cut/13_lukashenko.png` |
| `14_milei` | fuente del rig, no cuesta aparte | flux (sin ficha) | 0 | — | `pruebas/elenco/cut/14_milei.png` |
| `15_islander` | fuente del rig, no cuesta aparte | flux (sin ficha) | 0 | — | `pruebas/elenco/cut/15_islander.png` |
| `16_vdl` | fuente del rig, no cuesta aparte | flux (sin ficha) | 0 | — | `pruebas/elenco/cut/16_vdl.png` |
| `17_xi` | fuente del rig, no cuesta aparte | flux (sin ficha) | 0 | — | `pruebas/elenco/cut/17_xi.png` |
| `18_rama` | fuente del rig, no cuesta aparte | flux (sin ficha) | 0 | — | `pruebas/elenco/cut/18_rama.png` |

## expresiones — 1 creditos

Hojas de caras por personaje. Se cortan una vez y sirven para todos los episodios.

| Clave | Que es | Modelo | Cr | Usado en | Ruta |
|---|---|---|---|---|---|
| `01_burocrata_hoja_v1` | Hoja de 6 expresiones del Burocrata | flux | 1 | — | `pruebas/elenco/expresiones/01_burocrata_hoja_v1.png` |

## hero — 1 creditos

Planos generativos (still + image-to-video). Lo MAS caro que generamos: 10-20 cr por clip. Cada uno con su ficha .json (modelo, prompt, creditos, que se descarto y por que).

| Clave | Que es | Modelo | Cr | Usado en | Ruta |
|---|---|---|---|---|---|
| `hangar` | Act II · Cannibals: el Boeing desarmado | flux-2-pro | 11 | — | `produccion/hero/hangar.json` |

## sets — 3 creditos

Fondos de pared generados. Reusables como telon en cualquier episodio.

| Clave | Que es | Modelo | Cr | Usado en | Ruta |
|---|---|---|---|---|---|
| `set_hangar_v1` | Fondo de hangar | flux | 1 | — | `produccion/assets/sets/set_hangar_v1.png` |
| `set_negociacion_v1` | Fondo de sala de negociacion | flux | 1 | — | `produccion/assets/sets/set_negociacion_v1.png` |
| `set_torre_v1` | Fondo de torre de control | flux | 1 | — | `produccion/assets/sets/set_torre_v1.png` |

## musica — 29 creditos

Cues propias (Lyria, 3 cr) y pistas de biblioteca. Las cues se REUSAN entre episodios: antes de generar una nueva, escuchar estas.

| Clave | Que es | Modelo | Cr | Usado en | Ruta |
|---|---|---|---|---|---|
| `Anguish` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/Anguish.mp3` |
| `Chase_Pulse` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/Chase_Pulse.mp3` |
| `Cold_Sober` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/Cold_Sober.mp3` |
| `Controlled_Chaos` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/Controlled_Chaos.mp3` |
| `Crypto` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/Crypto.mp3` |
| `Dark_Times` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/Dark_Times.mp3` |
| `Dark_Walk` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/Dark_Walk.mp3` |
| `Darkest_Child` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/Darkest_Child.mp3` |
| `Deliberate_Thought` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/Deliberate_Thought.mp3` |
| `Echoes_of_Time` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/Echoes_of_Time.mp3` |
| `Gathering_Darkness` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/Gathering_Darkness.mp3` |
| `Heavy_Interlude` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/Heavy_Interlude.mp3` |
| `Intrepid` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/Intrepid.mp3` |
| `Killers` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/Killers.mp3` |
| `Long_Note_Two` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/Long_Note_Two.mp3` |
| `Lost_Frontier` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/Lost_Frontier.mp3` |
| `Ossuary_6_-_Air` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/Ossuary_6_-_Air.mp3` |
| `Redletter` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/Redletter.mp3` |
| `Tempting_Secrets` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/Tempting_Secrets.mp3` |
| `The_Complex` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/The_Complex.mp3` |
| `Unseen_Horrors` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/Unseen_Horrors.mp3` |
| `Volatile_Reaction` | de terceros, ver CREDITOS_MUSICA.md | biblioteca libre | 0 | — | `produccion/musica/Volatile_Reaction.mp3` |
| `cue_01_intro` | Cue de apertura | lyria-3-pro | 3 | 01_aviacion_rusa | `produccion/musica/cue_01_intro.mp3` |
| `cue_02_flota` | Cue de la flota | lyria-3-pro | 3 | 01_aviacion_rusa | `produccion/musica/cue_02_flota.mp3` |
| `cue_03_partes` | Cue de repuestos / canibalismo | lyria-3-pro | 3 | 01_aviacion_rusa | `produccion/musica/cue_03_partes.mp3` |
| `cue_04_dron` | Cue de tension / drones | lyria-3-pro | 3 | 01_aviacion_rusa | `produccion/musica/cue_04_dron.mp3` |
| `cue_05_pais` | Cue amplia / pais | lyria-3-pro | 3 | 01_aviacion_rusa | `produccion/musica/cue_05_pais.mp3` |
| `cue_06_siberia` | Cue fria / Siberia | lyria-3-pro | 3 | 01_aviacion_rusa | `produccion/musica/cue_06_siberia.mp3` |
| `tema_canal` | Cortina del canal (Paper Trail) | lyria-3-pro | 3 | 01_aviacion_rusa, 02_afd_alemania, 03_kiev_belarus | `produccion/musica/tema_canal.mp3` |

## mapas — 8 (0 cr)

Hojas de mapa por region. 0 creditos pero HORAS de trabajo: si el tema cae en una region que ya tenemos, se reusa la hoja y solo se agregan puntos a su pts.json.

| Clave | Que es | Modelo | Cr | Usado en | Ruta |
|---|---|---|---|---|---|
| `mapa` | Rusia / Asia norte (Mercator, LON 18-200, LAT 38-78) | 0 cr (Natural Earth + codigo) | 0 | 01_aviacion_rusa | `produccion/assets` |
| `mapa02` | Alemania | 0 cr (Natural Earth + codigo) | 0 | 02_afd_alemania | `produccion/assets` |
| `mapa03` | Ucrania / Bielorrusia | 0 cr (Natural Earth + codigo) | 0 | 03_kiev_belarus | `produccion/assets` |
| `mapa04` | Malvinas / Atlantico sur | 0 cr (Natural Earth + codigo) | 0 | 04_malvinas | `produccion/assets` |
| `mapa05` | — | 0 cr (Natural Earth + codigo) | 0 | — | `videos/05_11s/arte/assets` |
| `mapa06` | — | 0 cr (Natural Earth + codigo) | 0 | — | `videos/06_ia_economia_politica/arte/assets` |
| `mapa11` | — | 0 cr (Natural Earth + codigo) | 0 | — | `videos/S01_11s/arte/assets` |
| `mapame` | — | 0 cr (Natural Earth + codigo) | 0 | — | `videos/S01_11s/arte/assets` |

## props — 408 (0 cr)

Objetos de papel dibujados por codigo (props*.py). 0 creditos. Antes de dibujar uno nuevo, buscar aca: hay 408.

`acorazado` · `alfombra` · `anillo_ue` · `antena` · `arbol` · `avion` · `avion_chico` · `avion_gris` · `avion_papel` · `balanza` · `balanza_men_walls` · `bandera_ar` · `bandera_es` · `bandera_fr` · `bandera_rusa` · `bandera_rusa_doblada` · `bandera_uk` · `bandera_us` · `barco_vela` · `barrera` · `barril` · `base_militar` · `bateria` · `blindado` · `blindado_fantasma` · `bocadillo_july` · `bocadillo_sept` · `boleta_electoral` · `bota` · `botas` · `bundestag` · `buque_guerra` · `caballero` · `caja` · `caja_arena` · `cajas_municion` · `cajas_municion_fantasma` · `cal20` · `cal3` · `cal_jul22` · `cal_sep20` · `calamar` · `carbon` · `carpa` · `carpa_fantasma` · `carpeta_atada` · `carta_reclutamiento` · `cartel_protesta` · `cartel_sky` · `casa` · `casa_colono` · `casa_pisos_1` · `casa_pisos_2` · `cerca` · `cheque` · `chip_aero` · `chip_aeroflot` · `chip_azul` · `chip_belarus` · `chip_cdu` · `chip_gris` · `chip_moscu` · `chip_ocre` · `chip_pokrovsk` · `chip_rojo_chico` · `chip_verde` · `circulo_rojo` · `clavo` · `cohete` · `colectivo` · `collar` · `columna_azul` · `columna_cdu` · `contrato99` · `corazon` · `corona` · `cuaderno` · `cuartel` · `decreto` · `deposito_ammo` · `deposito_fuel` · `deposito_oil` · `despertador` · `diamante` · `diana` · `diario_1` · `diario_2` · `diario_3` · `diario_afd` · `diario_inm` · `diario_rec` · `diccionario` · `dron` · `dron_fpv` · `dron_grande` · `ejercito_papel` · `escanos` · `escoba` · `escritorio` · `escudo` · `eslabon` · `eslabon_rojo` · `estrella` · `etiqueta` · `etiqueta_rublo` · `expediente` · `fabrica` · `factura` · `flecha_abajo` · `flecha_arriba` · `flecha_punteada` · `flecha_punteada_gris` · `foca` · `formulario` · `foto_apreton` · `franja_drones` · `fuego` · `fusil` · `globo` · `gota` · `graf_gasto` · `graf_inm` · `graf_voto` · `grafico_caida` · `hielo` · `humo` · `iman` · `informe` · `isla_recorte` · `lampara` · `lanzacohetes` · `libro_mayor` · `linea_piso` · `lingote` · `llave` · `luna` · `lupa` · `mano_abierta` · `mano_con_carta` · `mano_senala` · `manual` · `mapa_ardenas` · `martillo` · `martillo_juez` · `mazo` · `medalla` · `medidor_combustible` · `megafono` · `memorial` · `mesa_negociacion` · `microfono` · `moneda` · `moneda_euro` · `moneda_rublo` · `moto` · `naipe` · `orden_donbas` · `orden_kyiv` · `orden_vacia` · `oveja` · `pagina_feb22` · `palabra_donbas` · `palabra_kyiv` · `palabra_plan` · `papeleta` · `papeleta_no` · `papeleta_si` · `paraguas` · `pasaporte` · `pergamino` · `pergamino_sa` · `pinguino` · `placa` · `plano` · `politico_azul` · `politico_rojo` · `poliza` · `portada_economist` · `portada_wsj` · `puerta_con_mano` · `pupitre` · `rampa_1` · `rampa_2` · `recluta` · `red_pesca` · `regla` · `regla_40` · `regla_90` · `reloj_arena` · `resolucion` · `rueda` · `rusia_encogida` · `saco_arena` · `sacos_fila` · `sello_2` · `sello_again` · `sello_aggressor` · `sello_convicted` · `sello_evenso` · `sello_extremist` · `sello_failed` · `sello_loss` · `sello_madness` · `sello_mostly` · `sello_no` · `sello_nobody` · `sello_noprice` · `sello_notin` · `sello_rehearsal` · `sello_settled` · `sello_x` · `senal_radiacion` · `silla` · `sobre` · `sofa` · `soga` · `sol` · `soldado` · `soldado_chico` · `soldado_grande` · `tab_country` · `tab_drone` · `tab_fleet` · `tab_men` · `tab_road` · `tab_target` · `tablero` · `tablero_c` · `tanque` · `tanque_arena` · `tanque_t72` · `tanque_t72_fantasma` · `tarta` · `telefono` · `termometro` · `terrones_azucar` · `tijera` · `tornillo` · `torre_petroleo` · `tratado` · `tren` · `tren_militar` · `tren_militar_fantasma` · `trinchera` · `tv` · `tv_msg` · `urna` · `vaca` · `valija` · `via_tren` · `votante` · `votante_azul` · `votante_rojo` · `bandeja` · `barra_cn_01` · `barra_cn_24` · `barra_us_01` · `barra_us_24` · `billete` · `calendario` · `carpa` · `chip` · `contenedor` · `documento` · `escritorio` · `flecha` · `foco` · `hoja_cuentas` · `ladrillo` · `misil` · `motas` · `muro` · `pasaje` · `pila_memos` · `puerta` · `reloj_0759` · `reloj_0814` · `reloj_0820` · `reloj_0842` · `reloj_0846` · `reloj_0903` · `reloj_0924` · `reloj_0937` · `reloj_1007` · `silla` · `trono` · `auto_t` · `bandeja_cog` · `bandeja_otros` · `bandera_al` · `bandera_cn` · `bandera_dk` · `bandera_hu` · `bandera_ro` · `bandera_ue` · `berlaymont` · `billete_45_55` · `billete_60_40` · `billete_entero` · `boleta_luz` · `caballo` · `caballo_corbata` · `calendario_2027` · `canario` · `carpeta_licitacion` · `chip_h200` · `cronometro` · `dial_max` · `dial_med` · `dial_min` · `escalera_ok` · `escalera_roto` · `hucha_pension` · `impresora` · `medidor_luz` · `medidor_luz_alto` · `panel_diales` · `panel_diales_max` · `parlamento_hu` · `pila_dolares` · `pila_euros` · `rulebook` · `sello_after_2027` · `sello_both_true` · `sello_hiring` · `sello_it_lost` · `sello_licensed` · `sello_no_precedent` · `sello_not_forecast` · `sello_pick_one` · `sello_unconst` · `silla_pantalla` · `sobre_paga` · `titulo_accion` · `torre_refrig` · `vapor` · `alfombra_rezo` · `bandera_negra` · `bandera_otan` · `bandera_taliban` · `bl_busto` · `bl_entero` · `bolsa_liq` · `botella` · `caja_wmd` · `capitolio` · `caza` · `caza_chico` · `cinta` · `escaleras` · `escaleras_ok` · `escuela` · `estadio` · `estrella_sov` · `ficha_bl` · `ficha_ksm` · `ficha_yousef` · `fila_asientos` · `grua` · `iglesia` · `jet` · `jet_chico` · `jet_gris` · `memo_phoenix` · `orden_derribo` · `oreja` · `panel_int` · `patriot` · `pdb` · `pentagono` · `plan_vuelo` · `plano_normal` · `plano_wtc` · `puerta_abierta` · `puerta_blindada` · `radar` · `radar_chico` · `receta` · `sello_arrested` · `sello_borrowed` · `sello_door_closed` · `sello_door_open` · `sello_due_east` · `sello_failed` · `sello_filed` · `sello_first_time` · `sello_fuel` · `sello_imagination` · `sello_land_now` · `sello_lost` · `sello_lower_first` · `sello_ml100` · `sello_no_bomb` · `sello_no_way_down` · `sello_nobody_asked` · `sello_one_stopped` · `sello_overreaction` · `sello_same_minute` · `sello_terrorism` · `sello_too_late` · `sello_vote` · `torre` · `torre_n` · `torre_s` · `transponder` · `transponder_off` · `yate` · `zapato`

## marca — 3 (0 cr)

Piezas fijas del canal ya renderizadas. Se pegan tal cual: NO se vuelven a generar.

| Clave | Que es | Modelo | Cr | Usado en | Ruta |
|---|---|---|---|---|---|
| `intro_canal` | Intro general del canal v2 (2026-09-11), 14 s: pide like y suscripcion | render local + voz pagada | 0 | 01_aviacion_rusa, 02_afd_alemania, 03_kiev_belarus | `produccion/intro_canal.mp4` |
| `outro_canal` | Outro del canal v2 (2026-09-11), 20 s: pide like y suscripcion (pantalla final d | render local + voz pagada | 0 | 01_aviacion_rusa, 02_afd_alemania, 03_kiev_belarus | `produccion/outro_canal.mp4` |
| `intro03_canal` | Intro de preguntas del ep. 3, 33 s | render local + voz pagada | 0 | 03_kiev_belarus | `produccion/intro03_canal.mp4` |

## produccion — 1 creditos

Assets con costo generados dentro de una produccion (`videos/<dir>/arte/assets/`). Se pueden reusar en otras: buscar aca antes de volver a generar.

| Clave | Que es | Modelo | Cr | Usado en | Ruta |
|---|---|---|---|---|---|
| `bl_busto` | Caricatura de papel de bin Laden (busto y figura entera) | flux-pro/v1.1-ultra via fal | 1 | S01_11s (miniaturas de las 12 piezas) | `videos/S01_11s/arte/assets/prop_bl_busto.png` |

