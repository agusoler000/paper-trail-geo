# -*- coding: utf-8 -*-
"""Rig del presentador: corta el PNG con alfa en piezas con pivote y las compone en cualquier pose.

    python videos/DAILY/presentador/rig.py cortar A      # corta y escribe rig_A.json + piezas/
    python videos/DAILY/presentador/rig.py piezas A      # hoja con las piezas sueltas (control)
    python videos/DAILY/presentador/rig.py prueba A      # hoja de verificacion: piezas + poses
    python videos/DAILY/presentador/rig.py --autotest    # invariantes de los tres rigs

Las piezas se cortan UNA vez. Despues, un episodio nuevo no genera nada: mueve angulos.
Los poligonos de corte son datos: si una pieza queda mal, se tocan los numeros de PIEZAS y se
vuelve a cortar. Coordenadas sobre el PNG con alfa a tamano original (768x1024), ver _grid.jpg
(_grid_B.jpg y _grid_C.jpg para los otros dos).
"""
import json, os, sys
from PIL import Image, ImageChops, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
PAPEL = (233, 223, 203)
TINTA = (34, 32, 28)
ROJO = (184, 64, 47)
GRIS = (120, 112, 98)

# ---------------------------------------------------------------------------
# A · EL CORRESPONSAL
# pivotes leidos sobre A_corresponsal_alpha.png; el remache tapa la costura del corte
RIGS = {
    "A": {
        "archivo": "A_corresponsal_alpha.png",
        "nombre": "EL CORRESPONSAL",
        "pivotes": {
            "cuello":   [390, 352],
            "hombro_i": [222, 422], "codo_i": [155, 545],
            "hombro_d": [546, 425], "codo_d": [613, 545],
        },
        "boca": [390, 296],
        # orden de composicion: el primero va al fondo
        "z": ["torso", "brazo_i", "antebrazo_i", "brazo_d", "antebrazo_d", "cabeza"],
        # El corte del hombro sigue la COSTURA de la manga (casi vertical), no una
        # perpendicular al brazo: si no, se lleva la solapa del saco.
        # El del codo si es perpendicular al eje hombro->codo.
        "piezas": {
            "cabeza": {
                "pivote": "cuello",
                "poly": [[246, 10], [552, 10], [552, 322], [470, 366], [430, 374],
                         [350, 374], [310, 366], [246, 322]],
            },
            "brazo_i": {
                "pivote": "hombro_i",
                "poly": [[158, 366], [250, 376], [248, 446], [228, 502], [200, 570],
                         [62, 478], [106, 412]],
            },
            "antebrazo_i": {
                "pivote": "codo_i",
                "poly": [[62, 478], [196, 572], [204, 690], [200, 822], [2, 826], [0, 540]],
            },
            "brazo_d": {
                "pivote": "hombro_d",
                "poly": [[518, 376], [610, 366], [662, 414], [700, 484], [566, 578],
                         [542, 502], [520, 446]],
            },
            "antebrazo_d": {
                "pivote": "codo_d",
                "poly": [[566, 578], [700, 484], [768, 556], [764, 826], [552, 824], [540, 690]],
            },
            # torso = lo que queda (se calcula solo)
            "torso": {"pivote": None, "poly": None},
        },
    },

    # -----------------------------------------------------------------------
    # B · EL ANALISTA  (mangas arrolladas, tiradores; brazos rectos, colgando)
    # Pivotes medidos sobre B_analista_alpha.png, ver _grid_B.jpg.
    # La costura del hombro es una linea CASI VERTICAL: x=254 a la izquierda y x=516 a la
    # derecha. Se midio por luminancia, no a ojo: la manga izquierda deja un realce de papel
    # en x=252-253 y la derecha una sombra en x=514-515; el hueco de fondo entre brazo y
    # torso recien abre en y=506. Cortar perpendicular al brazo cruzaria ese hueco.
    "B": {
        "archivo": "B_analista_alpha.png",
        "nombre": "EL ANALISTA",
        "pivotes": {
            "cuello":   [388, 378],
            "hombro_i": [243, 424], "codo_i": [160, 597],
            "hombro_d": [516, 425], "codo_d": [602, 597],
        },
        "boca": [390, 290],
        "z": ["torso", "brazo_i", "antebrazo_i", "brazo_d", "antebrazo_d", "cabeza"],
        "piezas": {
            # Sobre el cuello no hay nada mas que la cabeza, asi que el poligono es un
            # rectangulo con una muesca: el cuello baja hasta y=372 y el cuello de la
            # camisa (x<350 y x>420) se queda con el torso.
            "cabeza": {
                "pivote": "cuello",
                "poly": [[150, 8], [620, 8], [620, 358], [424, 358], [414, 384],
                         [358, 384], [348, 358], [150, 358]],
            },
            "brazo_i": {
                "pivote": "hombro_i",
                "poly": [[150, 390], [256, 390], [254, 508], [241, 636], [79, 558], [48, 466]],
            },
            "antebrazo_i": {
                "pivote": "codo_i",
                "poly": [[79, 558], [241, 636], [241, 1024], [0, 1024], [0, 520]],
            },
            "brazo_d": {
                "pivote": "hombro_d",
                "poly": [[610, 390], [712, 466], [687, 554], [517, 640], [513, 508], [513, 390]],
            },
            "antebrazo_d": {
                "pivote": "codo_d",
                "poly": [[687, 554], [517, 640], [517, 1024], [768, 1024], [768, 513]],
            },
            "torso": {"pivote": None, "poly": None},
        },
    },

    # -----------------------------------------------------------------------
    # C · EL ARCHIVISTA  (chaleco, mono, pluma; brazos DOBLADOS: codo afuera y antebrazo
    # de vuelta hacia adentro, con las manos apoyadas SOBRE el chaleco).
    # Dos diferencias con A y B, y las dos cambian la forma del poligono:
    #  1. El brazo es piel desnuda contra el chaleco oscuro, asi que la costura del hombro
    #     se midio separando piel de chaleco (no hay hueco de fondo hasta y=525). Los
    #     numeros de abajo son el borde real de la piel, fila por fila.
    #  2. Las manos tapan el chaleco: el antebrazo tiene que seguir el contorno de la mano
    #     dedo por dedo, o al girar deja un agujero en el chaleco.
    # El corte del codo NO es perpendicular al brazo (esta doblado 65 grados): es la
    # bisectriz del angulo hombro-codo-muneca, que es lo unico que separa las dos partes.
    "C": {
        "archivo": "C_archivista_alpha.png",
        "nombre": "EL ARCHIVISTA",
        "pivotes": {
            "cuello":   [390, 400],
            "hombro_i": [212, 478], "codo_i": [65, 607],
            "hombro_d": [555, 470], "codo_d": [690, 605],
        },
        "boca": [395, 332],
        "z": ["torso", "brazo_i", "antebrazo_i", "brazo_d", "antebrazo_d", "cabeza"],
        # El mordisco que dejan las manos en el chaleco se tapa clonando tela de la misma
        # fila: +60 px hacia adentro a la izquierda, -60 a la derecha. Medido: el microfono
        # vive entre x=335 y x=435, asi que ninguno de los dos origenes lo toca. El borde
        # del poligono ES el borde real del chaleco, para no inventar tela por fuera.
        "parche": [
            {"poly": [[217, 762], [262, 762], [262, 906], [224, 906], [230, 880],
                      [234, 840], [234, 818], [217, 812]], "desde": [60, 0]},
            {"poly": [[547, 762], [547, 812], [531, 818], [531, 840], [536, 880],
                      [540, 906], [500, 906], [500, 762]], "desde": [-60, 0]},
        ],
        "piezas": {
            "cabeza": {
                "pivote": "cuello",
                "poly": [[150, 8], [620, 8], [620, 402], [436, 402], [430, 410],
                         [344, 410], [338, 402], [150, 402]],
            },
            # brazo = costura sobre el borde del chaleco (fila por fila) + hueco + corte de
            # codo. Por el hueco y por afuera el poligono va holgado: pegarlo al contorno
            # deja pelos de 1 px del brazo cosidos al torso, que al girar se ven.
            "brazo_i": {
                "pivote": "hombro_i",
                "poly": [[140, 432], [232, 432], [230, 445], [230, 462], [232, 472],
                         [234, 484], [235, 500], [237, 514], [237, 526], [233, 534],
                         [228, 544], [215, 562], [196, 592], [178, 620], [169, 644],
                         [0, 583],
                         [0, 528], [34, 478], [70, 454]],
            },
            # el contorno de la mano, dedo por dedo: de x=515 para adentro esta sobre el
            # chaleco, y cualquier exceso se lleva un pedazo del chaleco al girar.
            "antebrazo_i": {
                "pivote": "codo_i",
                "poly": [[0, 583], [169, 644],
                         [140, 655], [153, 702], [161, 703], [173, 748], [170, 749],
                         [206, 754], [251, 783], [251, 790], [245, 797], [212, 799],
                         [216, 804], [212, 807], [219, 813], [231, 836], [227, 838],
                         [249, 874], [243, 884], [228, 886], [230, 893], [223, 900],
                         [216, 900], [162, 895], [129, 833], [119, 801], [117, 780],
                         [93, 779], [75, 738], [83, 730], [60, 692], [45, 653], [38, 622]],
            },
            "brazo_d": {
                "pivote": "hombro_d",
                "poly": [[536, 432], [539, 447], [537, 462], [534, 474], [532, 486],
                         [531, 500], [532, 516], [531, 528], [542, 542], [556, 566],
                         [572, 592], [584, 614], [590, 627],
                         [768, 588],
                         [768, 520], [730, 470], [660, 440], [560, 430]],
            },
            "antebrazo_d": {
                "pivote": "codo_d",
                "poly": [[768, 588], [590, 627],
                         [640, 618], [624, 646], [603, 702], [589, 747], [592, 748],
                         [563, 750], [548, 757], [551, 759], [515, 774], [510, 780],
                         [510, 788], [517, 795], [550, 796], [541, 818], [535, 819],
                         [534, 834], [512, 869], [515, 881], [532, 884], [530, 893],
                         [537, 899], [544, 899], [548, 896], [593, 895], [600, 888],
                         [633, 828], [641, 801], [642, 778], [666, 777], [686, 737],
                         [679, 730], [707, 677], [726, 604]],
            },
            "torso": {"pivote": None, "poly": None},
        },
    },
}


def f(px, bold=False):
    for n in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(n, px)
        except Exception:
            pass
    return ImageFont.load_default()


def mascara(size, poly):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon([tuple(p) for p in poly], fill=255)
    return m


def cortar(clave):
    r = RIGS[clave]
    src = Image.open(os.path.join(BASE, r["archivo"])).convert("RGBA")
    dest = os.path.join(BASE, "piezas_%s" % clave)
    os.makedirs(dest, exist_ok=True)

    usado = Image.new("L", src.size, 0)          # lo que ya se llevo otra pieza
    salida = {}

    for nombre, cfg in r["piezas"].items():
        if cfg["poly"] is None:
            continue
        m = mascara(src.size, cfg["poly"])
        pieza = Image.new("RGBA", src.size, (0, 0, 0, 0))
        pieza.paste(src, (0, 0), Image.composite(src.split()[3], Image.new("L", src.size, 0), m))
        usado = Image.composite(Image.new("L", src.size, 255), usado, m)
        caja = pieza.getbbox()
        if not caja:
            # Antes esto era un print y un continue: el rig quedaba sin la pieza, el JSON se
            # escribia igual y recien fallaba mas tarde, lejos de la causa.
            raise ValueError("%s/%s salio vacia: el poligono no toca dibujo opaco"
                             % (clave, nombre))
        px, py = r["pivotes"][cfg["pivote"]]
        pieza.crop(caja).save(os.path.join(dest, nombre + ".png"))
        salida[nombre] = {"caja": list(caja),
                          "pivote_local": [px - caja[0], py - caja[1]],
                          "pivote_global": [px, py]}

    # el torso es lo que no se llevo nadie
    torso = Image.new("RGBA", src.size, (0, 0, 0, 0))
    resto = Image.composite(Image.new("L", src.size, 0), src.split()[3], usado)
    torso.paste(src, (0, 0), resto)

    # Parche opcional (clave "parche", solo la declara C). Si el dibujo trae una mano
    # APOYADA sobre la ropa, el antebrazo se la lleva y deja un mordisco que se ve en
    # cuanto el brazo gira. Se clona tela de al lado, misma fila, asi el sombreado
    # vertical y el grano del papel siguen dando. Los rigs sin "parche" ni pasan por aca.
    parche_px = 0
    for pa in r.get("parche", []):
        dx, dy = pa["desde"]
        zona = mascara(src.size, pa["poly"])
        habia = Image.eval(src.split()[3], lambda v: 255 if v > 200 else 0)
        hueco = ImageChops.multiply(zona, habia)
        parche_px += sum(hueco.histogram()[129:])
        tela = Image.new("RGBA", src.size, (0, 0, 0, 0))
        tela.paste(ImageChops.offset(torso, -dx, -dy), (0, 0), hueco)
        torso.alpha_composite(tela)

    caja = torso.getbbox()
    if not caja:
        raise ValueError("%s/torso salio vacio: los poligonos se llevaron todo el dibujo" % clave)
    torso.crop(caja).save(os.path.join(dest, "torso.png"))
    salida["torso"] = {"caja": list(caja), "pivote_local": None, "pivote_global": None}

    doc = {"nombre": r["nombre"], "archivo": r["archivo"], "size": list(src.size),
           "pivotes": r["pivotes"], "boca": r["boca"], "z": r["z"], "piezas": salida,
           "parche_px": parche_px}
    with open(os.path.join(BASE, "rig_%s.json" % clave), "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)

    print("rig_%s.json  ·  %d piezas en piezas_%s/" % (clave, len(salida), clave))
    for n, v in salida.items():
        w = v["caja"][2] - v["caja"][0]
        h = v["caja"][3] - v["caja"][1]
        print("   %-13s %4dx%-4d  pivote local %s" % (n, w, h, v["pivote_local"]))
    return doc


# cadena cinematica: pieza -> (padre, pivote del padre)
CADENA = {"antebrazo_i": ("brazo_i", "hombro_i"),
          "antebrazo_d": ("brazo_d", "hombro_d")}

# Las poses con nombre que pide el guion. ESPEJO de escena.POSES: el autotest compara las dos
# listas y falla si se separan, para que no haya dos verdades.
POSES_ESCENA = {
    "reposo":   {},
    "senala":   {"brazo_d": 36, "antebrazo_d": 14, "cabeza": -3},
    "abre":     {"brazo_i": -20, "brazo_d": 20, "antebrazo_i": -10, "antebrazo_d": 10},
    "enfatiza": {"brazo_i": 24, "antebrazo_i": 18, "cabeza": 2},
    "escucha":  {"cabeza": 4},
}

# Cuanto lienzo de mas necesita la pose mas abierta para que la mano no quede cortada.
# Medido el 2026-09-11 sobre los tres rigs: A 138 px, B 253, C 135 (siempre a los costados).
# El PNG original NO tiene ese aire: con margen=0 la pose "senala" le corta la mano a los tres.
MARGEN_POSES = 256


def _doc(clave):
    with open(os.path.join(BASE, "rig_%s.json" % clave), encoding="utf-8") as fh:
        return json.load(fh)


def capa_pieza(clave, nombre, angulos=None, margen=0, doc=None):
    """Una pieza sola, ya girada, sobre un lienzo de (W+2*margen, H+2*margen) transparente.

    Vive aparte de componer() para que el autotest pueda pesar la tinta pieza por pieza: si
    una capa pierde dibujo al girar es que se salio del lienzo de trabajo, y eso mirando el
    apilado no se ve (un brazo que cruza el pecho tapa torso y baja el total igual).
    """
    doc = doc or _doc(clave)
    ang = angulos or {}
    p = doc["piezas"][nombre]
    W, H = doc["size"]
    with Image.open(os.path.join(BASE, "piezas_%s" % clave, nombre + ".png")) as _im:
        im = _im.convert("RGBA")
    propio = ang.get(nombre, 0)
    padre, piv_padre = CADENA.get(nombre, (None, None))
    heredado = ang.get(padre, 0) if padre else 0

    if p["pivote_global"] is None or (not propio and not heredado):
        fija = Image.new("RGBA", (W + 2 * margen, H + 2 * margen), (0, 0, 0, 0))
        fija.alpha_composite(im, (p["caja"][0] + margen, p["caja"][1] + margen))
        return fija

    M = max(W, H) // 2 + margen             # margen de trabajo, para que nada se corte al girar
    cap = Image.new("RGBA", (W + 2 * M, H + 2 * M), (0, 0, 0, 0))
    cap.alpha_composite(im, (p["caja"][0] + M, p["caja"][1] + M))
    if propio:
        gx, gy = p["pivote_global"]
        cap = cap.rotate(propio, resample=Image.BICUBIC, center=(gx + M, gy + M))
    if heredado:
        hx, hy = doc["pivotes"][piv_padre]
        cap = cap.rotate(heredado, resample=Image.BICUBIC, center=(hx + M, hy + M))
    return cap.crop((M - margen, M - margen, M + W + margen, M + H + margen))


def componer(clave, angulos=None, fondo=PAPEL, brads=True, margen=0):
    """angulos: {'brazo_i': -12, 'antebrazo_i': 20, 'cabeza': 2, ...} en grados.

    Cada pieza se apoya en un lienzo con margen y se gira sobre su pivote GLOBAL; si tiene
    padre, se vuelve a girar sobre el pivote del padre. Rotar el lienzo entero alrededor de un
    punto global compone bien y evita la aritmetica de desplazamientos.

    `margen` agranda el cuadro devuelto a (W+2*margen, H+2*margen) con el dibujo centrado.
    Con margen=0 (el default, que es lo que hoy consume escena.py) la pose que abre el brazo
    se sale del PNG original y la mano se RECORTA; ver MARGEN_POSES y fuera_del_cuadro().
    `fondo=None` devuelve RGBA transparente en vez de RGB sobre papel.
    """
    doc = _doc(clave)
    ang = angulos or {}
    sueltos = set(ang) - set(doc["piezas"])
    if sueltos:
        # Antes una clave mal escrita se ignoraba y la pose salia igual que el reposo.
        raise ValueError("rig %s: angulos para piezas que no existen: %s"
                         % (clave, ", ".join(sorted(sueltos))))
    W, H = doc["size"]
    lienzo = Image.new("RGBA", (W + 2 * margen, H + 2 * margen),
                       (0, 0, 0, 0) if fondo is None else fondo + (255,))

    for nombre in doc["z"]:
        lienzo.alpha_composite(capa_pieza(clave, nombre, ang, margen, doc), (0, 0))

    if brads:
        d = ImageDraw.Draw(lienzo)
        for k in ("hombro_i", "hombro_d"):
            x, y = [v + margen for v in doc["pivotes"][k]]
            d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=(196, 190, 178),
                      outline=(150, 142, 128), width=3)
    return lienzo if fondo is None else lienzo.convert("RGB")


def fuera_del_cuadro(clave, angulos, margen=None):
    """Cuanto dibujo deja la pose AFUERA del PNG original, que es lo que recorta componer()
    con margen=0. -> (px_fuera, px_totales, margen_que_haria_falta)."""
    doc = _doc(clave)
    W, H = doc["size"]
    m = MARGEN_POSES if margen is None else margen
    a = componer(clave, angulos, fondo=None, brads=False, margen=m).split()[3]
    a = Image.eval(a, lambda v: 255 if v > 40 else 0)
    total = sum(a.histogram()[129:])
    dentro = sum(a.crop((m, m, m + W, m + H)).histogram()[129:])
    bb = a.getbbox()
    falta = 0
    if bb:
        falta = max(m - bb[0], m - bb[1], bb[2] - (m + W), bb[3] - (m + H), 0)
    return total - dentro, total, falta


def prueba(clave):
    """Hoja de verificacion con las poses que pide el guion.

    Se compone con MARGEN_POSES y se dibuja el borde del PNG original encima: adentro del
    recuadro punteado es lo que devuelve componer() con margen=0 (lo que hoy pega escena.py),
    y lo que asoma afuera es dibujo que en el video NO se ve. Antes esta hoja componia con
    margen=0 y mostraba la mano cortada sin decir que estaba cortada.
    """
    doc = _doc(clave)
    # SIGNO (medido con el barrido, 2026-09-11): en el brazo DERECHO positivo abre hacia
    # afuera y negativo cierra sobre el cuerpo. En el IZQUIERDO es al reves, por simetria.
    CW = 470
    W = 60 + len(POSES_ESCENA) * (CW + 24)
    H = 856
    m = MARGEN_POSES
    hoja = Image.new("RGB", (W, H), PAPEL)
    d = ImageDraw.Draw(hoja)
    d.text((40, 26), "RIG %s · %s" % (clave, doc["nombre"]), font=f(38, True), fill=TINTA)
    d.text((40, 74), "las mismas 6 piezas, cinco poses, cero generaciones · "
                     "el recuadro punteado es el PNG original: lo de afuera se recorta",
           font=f(23), fill=GRIS)
    for i, (nombre, ang) in enumerate(POSES_ESCENA.items()):
        im = componer(clave, ang, margen=m)
        dw, dh = doc["size"]
        dd = ImageDraw.Draw(im)
        for lado in (0, 1):
            for t in range(m, m + (dw if lado == 0 else dh), 24):
                if lado == 0:
                    dd.line([(t, m), (min(t + 12, m + dw), m)], fill=ROJO, width=3)
                    dd.line([(t, m + dh), (min(t + 12, m + dw), m + dh)], fill=ROJO, width=3)
                else:
                    dd.line([(m, t), (m, min(t + 12, m + dh))], fill=ROJO, width=3)
                    dd.line([(m + dw, t), (m + dw, min(t + 12, m + dh))], fill=ROJO, width=3)
        im.thumbnail((CW, 560), Image.LANCZOS)
        x = 40 + i * (CW + 24)
        hoja.paste(im, (x, 120))
        d.rectangle([x - 2, 118, x + im.width + 2, 120 + im.height + 2],
                    outline=(200, 188, 166), width=2)
        d.text((x, 132 + im.height), nombre, font=f(27, True), fill=TINTA)
        txt = "  ".join("%s %+d°" % (k.replace("brazo_", "br ").replace("ante", "a"), v)
                        for k, v in ang.items()) or "sin rotaciones"
        d.text((x, 166 + im.height), txt, font=f(20), fill=ROJO)
        fuera, total, falta = fuera_del_cuadro(clave, ang, m)
        if fuera:
            d.text((x, 196 + im.height), "margen=0 recorta %d px (%.1f%%)"
                   % (fuera, 100.0 * fuera / total), font=f(19), fill=ROJO)
            d.text((x, 220 + im.height), "hacen falta %d px de lienzo" % falta,
                   font=f(19), fill=ROJO)
        else:
            d.text((x, 196 + im.height), "entra entera en el PNG original",
                   font=f(19), fill=GRIS)
    out = os.path.join(BASE, "_rig_%s_prueba.jpg" % clave)
    hoja.save(out, quality=93)
    print(out, hoja.size)


def hoja_piezas(clave):
    """Las piezas sueltas, separadas y sobre cuadricula: para ver si alguna se llevo un
    pedazo del cuerpo o quedo partida. Es la hoja que hay que MIRAR antes de componer."""
    doc = _doc(clave)
    ims = []
    for n in doc["z"]:
        p = os.path.join(BASE, "piezas_%s" % clave, n + ".png")
        with Image.open(p) as _im:
            ims.append((n, _im.convert("RGBA"), doc["piezas"][n]))
    CH = 470
    esc = [min(1.0, CH / im.height) for _, im, _ in ims]
    anchos = [int(im.width * e) + 30 for (_, im, _), e in zip(ims, esc)]
    alto = 110 + max(int(im.height * e) for (_, im, _), e in zip(ims, esc)) + 62
    hoja = Image.new("RGB", (40 + sum(anchos), alto), (250, 246, 238))
    d = ImageDraw.Draw(hoja)
    d.text((36, 22), "PIEZAS %s · %s" % (clave, doc["nombre"]), font=f(34, True), fill=TINTA)
    d.text((36, 64), "cuadricula cada 25 px · el pivote en rojo · fondo a cuadros = transparente",
           font=f(20), fill=GRIS)
    x = 36
    for (n, im, meta), e in zip(ims, esc):
        w, h = int(im.width * e), int(im.height * e)
        cel = Image.new("RGB", (w, h), (214, 208, 196))
        dc = ImageDraw.Draw(cel)
        for gx in range(0, w, 25):
            dc.line([(gx, 0), (gx, h)], fill=(232, 228, 218))
        for gy in range(0, h, 25):
            dc.line([(0, gy), (w, gy)], fill=(232, 228, 218))
        chico = im.resize((w, h), Image.LANCZOS)
        cel.paste(chico, (0, 0), chico)
        if meta["pivote_local"]:
            px, py = [int(v * e) for v in meta["pivote_local"]]
            dc.line([(px - 10, py), (px + 10, py)], fill=ROJO, width=2)
            dc.line([(px, py - 10), (px, py + 10)], fill=ROJO, width=2)
        hoja.paste(cel, (x, 110))
        d.rectangle([x - 1, 109, x + w, 110 + h], outline=(180, 172, 158))
        d.text((x, 120 + h), n, font=f(23, True), fill=TINTA)
        d.text((x, 150 + h), "%dx%d" % (im.width, im.height), font=f(19), fill=GRIS)
        x += w + 30
    out = os.path.join(BASE, "_piezas_%s.jpg" % clave)
    hoja.save(out, quality=93)
    print(out, hoja.size)


# ---------------------------------------------------------------------------
# autotest

def _alfa(im):
    """Pixeles OPACOS. El umbral es alto a proposito: al pegar con mascara, PIL multiplica
    el alfa por si mismo, asi que los pixeles del borde antialiasado no se conservan y no
    sirven para contar. Los opacos si: 255*255/255 sigue siendo 255."""
    return sum(im.split()[3].histogram()[250:])


def autotest():
    ok = [0, 0]

    def chk(cond, texto):
        ok[0 if cond else 1] += 1
        print(("OK   " if cond else "FALLA") + "  " + texto)

    for clave, r in RIGS.items():
        ruta = os.path.join(BASE, r["archivo"])
        # Antes un PNG que faltaba se saltaba con un print y el autotest salia 0 igual.
        chk(os.path.exists(ruta), "%s: %s esta en el disco" % (clave, r["archivo"]))
        if not os.path.exists(ruta):
            continue
        with Image.open(ruta) as _s:
            src = _s.convert("RGBA")
        W, H = src.size
        chk(set(r["pivotes"]) == {"cuello", "hombro_i", "codo_i", "hombro_d", "codo_d"},
            "%s: los cinco pivotes con el nombre esperado" % clave)
        chk(r["z"] == ["torso", "brazo_i", "antebrazo_i", "brazo_d", "antebrazo_d", "cabeza"],
            "%s: z-order torso < brazos < cabeza" % clave)
        chk(set(r["piezas"]) == set(r["z"]), "%s: una pieza por capa del z-order" % clave)

        # pivotes sobre el dibujo, no en el aire
        dentro = all(0 <= x < W and 0 <= y < H for x, y in r["pivotes"].values())
        chk(dentro, "%s: pivotes dentro del lienzo %dx%d" % (clave, W, H))
        opacos = all(src.getpixel((x, y))[3] > 40 for x, y in r["pivotes"].values())
        chk(opacos, "%s: los cinco pivotes caen sobre pixel opaco" % clave)
        bx, by = r["boca"]
        chk(src.getpixel((bx, by))[3] > 40, "%s: la boca cae sobre pixel opaco" % clave)

        # cada poligono cerrado, con al menos un triangulo y dentro del lienzo
        for n, cfg in r["piezas"].items():
            if cfg["poly"] is None:
                continue
            poly = cfg["poly"]
            chk(len(poly) >= 3, "%s/%s: el poligono tiene %d vertices" % (clave, n, len(poly)))
            chk(all(0 <= x <= W and 0 <= y <= H for x, y in poly),
                "%s/%s: todos los vertices dentro del lienzo" % (clave, n))

        try:
            doc = cortar(clave)
        except ValueError as e:
            chk(False, "%s: cortar() levanto %s" % (clave, e))
            continue

        # ninguna pieza vacia y todas con pivote util
        for n in r["z"]:
            chk(n in doc["piezas"], "%s/%s: la pieza salio del corte" % (clave, n))
            caja = doc["piezas"][n]["caja"]
            chk((caja[2] - caja[0]) > 20 and (caja[3] - caja[1]) > 20,
                "%s/%s: la pieza mide %dx%d" % (clave, n, caja[2] - caja[0], caja[3] - caja[1]))

        # el pivote de cada pieza tiene que caer DENTRO de su propio poligono: si no, la
        # pieza gira alrededor de un punto que no le pertenece y se desprende.
        for n, cfg in r["piezas"].items():
            if cfg["poly"] is None:
                continue
            m = mascara(src.size, cfg["poly"])
            px, py = r["pivotes"][cfg["pivote"]]
            cerca = any(m.getpixel((px + dx, py + dy)) > 0
                        for dx in (-3, 0, 3) for dy in (-3, 0, 3))
            chk(cerca, "%s/%s: el pivote %s cae dentro del poligono" % (clave, n, cfg["pivote"]))

        # conservacion: las seis piezas tienen que cubrir TODO el dibujo (si un poligono se
        # olvida un pedazo, ese pedazo desaparece del cuadro) y casi no pisarse entre si
        # (dos piezas con el mismo pixel = una se despega y la otra deja fantasma).
        union = Image.new("L", src.size, 0)
        suma = 0
        for n in r["z"]:
            p = Image.open(os.path.join(BASE, "piezas_%s" % clave, n + ".png")).convert("RGBA")
            cj = doc["piezas"][n]["caja"]
            capa = Image.new("L", src.size, 0)
            capa.paste(p.split()[3], (cj[0], cj[1]))
            union = ImageChops.lighter(union, capa)
            suma += sum(capa.histogram()[201:])
        total = _alfa(src)
        cubierto = Image.eval(union, lambda v: 255 if v > 40 else 0)
        falta = ImageChops.multiply(Image.eval(src.split()[3], lambda v: 255 if v >= 250 else 0),
                                    Image.eval(cubierto, lambda v: 255 - v))
        n_falta = sum(falta.histogram()[129:])
        chk(n_falta < 0.002 * total,
            "%s: las piezas cubren el dibujo (%d px sin dueno de %d)" % (clave, n_falta, total))
        solape = suma - sum(union.histogram()[201:])
        chk(solape < 0.015 * total,
            "%s: solape entre piezas %d px (%0.2f%%)" % (clave, solape, 100.0 * solape / total))

        # si el rig declara parche, la ropa tiene que quedar ENTERA: ni un agujero adentro
        # de la zona parchada, que es lo que se ve en cuanto el brazo gira.
        torso_im = Image.open(os.path.join(BASE, "piezas_%s" % clave, "torso.png")).convert("RGBA")
        cj = doc["piezas"]["torso"]["caja"]
        entero = Image.new("RGBA", src.size, (0, 0, 0, 0))
        entero.paste(torso_im, (cj[0], cj[1]))
        for i, pa in enumerate(r.get("parche", [])):
            zona = mascara(src.size, pa["poly"])
            habia = Image.eval(src.split()[3], lambda v: 255 if v > 200 else 0)
            falta = Image.eval(entero.split()[3], lambda v: 0 if v > 200 else 255)
            h = ImageChops.multiply(ImageChops.multiply(zona, habia), falta)
            n_h = sum(h.histogram()[129:])
            chk(n_h == 0, "%s: parche %d tapa el mordisco (quedan %d px de agujero)"
                % (clave, i, n_h))

        # el torso tiene que seguir siendo la pieza grande
        torso = Image.open(os.path.join(BASE, "piezas_%s" % clave, "torso.png")).convert("RGBA")
        chk(_alfa(torso) > 0.25 * total,
            "%s: al torso le queda el %d%% del dibujo" % (clave, 100 * _alfa(torso) // total))

        # -------------------------------------------------------------- componer
        # Antes aca solo se miraba que componer() devolviera un RGB del tamano correcto, que
        # es lo mismo que no mirar nada: un componer que ignorara los angulos pasaba igual.

        im = componer(clave, {})
        chk(im.size == (W, H) and im.mode == "RGB",
            "%s: componer(reposo) devuelve %dx%d RGB" % (clave, im.size[0], im.size[1]))

        # (a) EL invariante: en reposo las piezas tienen que RECONSTRUIR el dibujo original.
        # Si una caja, un pivote o el z-order estan mal, el reposo ya sale distinto. Se
        # perdonan las zonas de parche, que a proposito reemplazan tela.
        ref = Image.new("RGBA", src.size, PAPEL + (255,))
        ref.alpha_composite(src)
        dif = ImageChops.difference(ref.convert("RGB"),
                                    componer(clave, {}, brads=False)).convert("L")
        peor = max(i for i, v in enumerate(dif.histogram()) if v)
        zonas = Image.new("L", src.size, 0)
        for pa in r.get("parche", []):
            zonas = ImageChops.lighter(zonas, mascara(src.size, pa["poly"]))
        sucio = ImageChops.multiply(Image.eval(dif, lambda v: 255 if v > 60 else 0),
                                    Image.eval(zonas, lambda v: 255 - v))
        n_sucio = sum(sucio.histogram()[129:])
        chk(n_sucio == 0, "%s: componer(reposo) reconstruye el original "
                          "(dif maxima %d, %d px feos fuera del parche)" % (clave, peor, n_sucio))

        # (b) girar tiene que MOVER el dibujo
        quieto = componer(clave, {}, fondo=None, brads=False, margen=MARGEN_POSES)
        for solo in ({"brazo_d": 20}, {"brazo_i": -20}, {"cabeza": 6}):
            movido = componer(clave, solo, fondo=None, brads=False, margen=MARGEN_POSES)
            n = sum(ImageChops.difference(quieto, movido).convert("L").histogram()[40:])
            chk(n > 2000, "%s: %+d grados en %s mueven el dibujo (%d px cambian)"
                % (clave, list(solo.values())[0], list(solo)[0], n))

        # (c) una clave de angulo que no es una pieza tiene que gritar, no salir en reposo
        try:
            componer(clave, {"brazo_derecho": 10})
            chk(False, "%s: componer acepta en silencio una pieza inexistente" % clave)
        except ValueError:
            chk(True, "%s: componer rechaza una pieza inexistente" % clave)

        # (d) conservacion PIEZA POR PIEZA: girar no puede perder dibujo. No sirve pesar el
        # apilado, porque un brazo que cruza el pecho tapa torso y baja el total sin que se
        # haya perdido nada; hay que pesar cada capa por separado.
        def _op(ima):
            a = Image.eval(ima.split()[3], lambda v: 255 if v > 200 else 0)
            return sum(a.histogram()[129:])
        for nom, ang in POSES_ESCENA.items():
            peor_n, peor_d = None, 0.0
            for n in doc["z"]:
                q = _op(capa_pieza(clave, n, {}, MARGEN_POSES, doc))
                m = _op(capa_pieza(clave, n, ang, MARGEN_POSES, doc))
                d = abs(m - q) / float(q)
                if d > peor_d:
                    peor_n, peor_d = n, d
            chk(peor_d < 0.02, "%s/%s: cada pieza conserva su dibujo al girar "
                               "(la que mas cambia es %s, %.2f%%)"
                % (clave, nom, peor_n or "ninguna", 100.0 * peor_d))

        # (e) y tiene que ENTRAR: MARGEN_POSES declara cuanto lienzo hace falta. Si manana
        # alguien agrega una pose mas abierta, esto se pone en rojo en vez de comerse la mano.
        for nom, ang in POSES_ESCENA.items():
            fuera, total, falta = fuera_del_cuadro(clave, ang)
            chk(falta < MARGEN_POSES,
                "%s/%s: entra en el cuadro + MARGEN_POSES (necesita %d de %d)"
                % (clave, nom, falta, MARGEN_POSES))
            if fuera:
                print("        AVISO  %s/%s deja %d px (%.1f%%) fuera del PNG original: "
                      "componer(margen=0), que es lo que hoy pide escena.py, se los come"
                      % (clave, nom, fuera, 100.0 * fuera / total))

    # Las poses viven en escena.py; aca hay una copia para poder probar el rig solo. Si las
    # dos listas se separan, el rig verifica una cosa y el video arma otra.
    try:
        sys.path.insert(0, os.path.dirname(BASE))
        import escena
        chk(escena.POSES == POSES_ESCENA, "POSES_ESCENA coincide con escena.POSES")
    except ImportError:
        chk(False, "no se pudo importar escena.py para comparar las poses")

    print("\n%d OK / %d FALLA" % tuple(ok))
    return 0 if ok[1] == 0 else 1


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "cortar"
    clave = sys.argv[2] if len(sys.argv) > 2 else "A"
    if cmd == "--autotest":
        sys.exit(autotest())
    elif cmd == "cortar":
        cortar(clave)
    elif cmd == "piezas":
        hoja_piezas(clave)
    elif cmd == "prueba":
        prueba(clave)
    else:
        print(__doc__)
