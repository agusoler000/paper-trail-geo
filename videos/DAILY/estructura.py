# -*- coding: utf-8 -*-
"""La escaleta del diario, dibujada, con DOS dias distintos para ver que los tiempos varian.

    python videos/DAILY/estructura.py

Los minutos NO son fijos: los calcula escaleta.repartir() con el peso real del dia.
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from PIL import Image, ImageDraw, ImageFont       # noqa: E402
import escaleta                                    # noqa: E402

PAPEL = (233, 223, 203)
TINTA = (34, 32, 28)
GRIS = (128, 120, 106)
ROJO = (184, 64, 47)
AZUL = (43, 76, 111)
OCRE = (217, 164, 65)
VERDE = (78, 102, 74)
VINO = (122, 58, 62)
MADERA = (107, 74, 51)

COLOR = {"COLD OPEN": ROJO, "INTRO": MADERA, "OUTRO": MADERA,
         "THE POWERS": AZUL, "THE MIDDLE EAST": VINO, "THE MONEY": VERDE,
         "TECH & ENERGY": VERDE, "THE SOUTH": OCRE, "THE PACIFIC": OCRE,
         "WHAT TO WATCH": MADERA}
QUE = {
    "COLD OPEN": "El hecho del dia en una frase. 'Stay to the end'.",
    "INTRO": "Sello de papel, THE LEDGER, la fecha. Fija.",
    "THE POWERS": "EEUU · Europa · China · Rusia. La mesa grande.",
    "THE MIDDLE EAST": "Israel · Iran · Golfo · Levante. Su propio teatro.",
    "THE MONEY": "Mercados, comercio, bancos centrales.",
    "TECH & ENERGY": "Chips, IA, tierras raras, ductos.",
    "THE SOUTH": "Latinoamerica, Argentina primero.",
    "THE PACIFIC": "Australia, NZ, Indo-Pacifico, Taiwan.",
    "WHAT TO WATCH": "El calendario de lo que viene. LA FIRMA.",
    "OUTRO": "Like, suscripcion, el video de manana. Fija.",
}
FICHAS = {"THE POWERS": "versus · mapa · cronologia", "THE MIDDLE EAST": "mapa · versus · cronologia",
          "THE MONEY": "serie · dato · titular", "TECH & ENERGY": "dato · serie · plano",
          "THE SOUTH": "dato · titular · mapa", "THE PACIFIC": "mapa · titular",
          "WHAT TO WATCH": "calendario", "COLD OPEN": "titular", "INTRO": "", "OUTRO": ""}
CARAS = {"A": "A_corresponsal_alpha.png", "B": "B_analista_alpha.png", "C": "C_archivista_alpha.png"}
NOMBRE = {"A": "EL CORRESPONSAL", "B": "EL ANALISTA", "C": "EL ARCHIVISTA"}
RECORTE = {"A": (250, 20, 560, 380), "B": (240, 20, 540, 400), "C": (190, 20, 590, 420)}


def f(px, bold=False):
    for n in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(n, px)
        except Exception:
            pass
    return ImageFont.load_default()


def _cara(clave, alto):
    im = Image.open(os.path.join(BASE, "presentador", CARAS[clave])).convert("RGBA")
    im = im.crop(RECORTE[clave])
    e = alto / float(im.height)
    return im.resize((int(im.width * e), alto), Image.LANCZOS)


def _ev(paises, topics, imp):
    return {"paises": paises, "topics": topics, "importancia": imp}


DIA_TRANQUILO = ([_ev(["US", "CN"], ["diplomacy"], 71), _ev(["RU", "UA"], ["military"], 64),
                  _ev(["DE", "EU"], ["elections"], 52)]
                 + [_ev(["IL"], ["diplomacy"], 34)]
                 + [_ev([], ["finance"], 58), _ev([], ["trade"], 47)]
                 + [_ev([], ["tech"], 44)]
                 + [_ev(["AR"], ["elections"], 61), _ev(["BR"], ["trade"], 42)]
                 + [_ev(["AU"], ["diplomacy"], 46)])
DIA_DE_GUERRA = ([_ev(["US", "CN"], ["diplomacy"], 52)]
                 + [_ev(["IL", "IR"], ["military"], 94), _ev(["IL", "LB"], ["military"], 88),
                    _ev(["YE", "SA"], ["military"], 81), _ev(["IR"], ["energy"], 76),
                    _ev(["EG", "PS"], ["diplomacy"], 67)]
                 + [_ev([], ["finance"], 55)]
                 + [_ev(["AR"], ["finance"], 39)]
                 + [_ev(["TW", "CN"], ["military"], 72)])


def _barra(d, im, x0, y, ancho, alto, rep, etiquetas=True):
    fijos = escaleta.FIJOS
    total = rep["total_min"]
    x = x0
    for nombre in escaleta.ORDEN:
        mins = fijos.get(nombre) or rep["bloques"].get(nombre, {}).get("minutos", 0)
        if not mins:
            continue
        w = ancho * mins / total
        d.rectangle([x, y, x + max(2, w - 3), y + alto], fill=COLOR[nombre])
        if etiquetas and w > 118:
            d.text((x + 12, y + 12), nombre, font=f(18, True), fill=PAPEL)
            d.text((x + 12, y + 38), "%d:%02d" % (int(mins), round((mins % 1) * 60)),
                   font=f(18), fill=(234, 228, 216))
        x += w
    return total


def dibujar():
    rep_t = escaleta.repartir(DIA_TRANQUILO)
    rep_g = escaleta.repartir(DIA_DE_GUERRA)

    W, MARG = 2160, 60
    FILA = 106
    CAB = 208
    BLOQUES_N = len(escaleta.ORDEN)
    H = CAB + 2 * 108 + 36 + BLOQUES_N * FILA + 200

    im = Image.new("RGB", (W, H), PAPEL)
    d = ImageDraw.Draw(im)
    d.text((MARG, 40), "THE LEDGER — ESCALETA DEL DIARIO", font=f(54, True), fill=TINTA)
    d.text((MARG, 106), "los minutos NO son fijos: se reparten cada dia segun el peso real de las noticias",
           font=f(29), fill=TINTA)
    d.text((MARG, 146), "publica 12:00 UTC · 08:00 Nueva York · 14:00 Berlin · 09:00 Buenos Aires",
           font=f(25), fill=GRIS)

    # ---- las dos barras, mismo ancho = mismo programa, distinto reparto
    y = CAB
    for titulo, rep, nota in (("UN DIA TRANQUILO", rep_t, "Oriente Medio flojo · las potencias se llevan el aire"),
                              ("UN DIA DE GUERRA", rep_g, "Oriente Medio se lleva 5:17 y se lo saca a las potencias")):
        d.text((MARG, y), titulo, font=f(27, True), fill=TINTA)
        d.text((MARG + 265, y + 4), "· %.1f min · %s" % (rep["total_min"], nota),
               font=f(23), fill=GRIS)
        _barra(d, im, MARG, y + 34, W - 2 * MARG, 64, rep)
        y += 108

    # ---- filas
    y += 32
    for nombre in escaleta.ORDEN:
        fijo = nombre in escaleta.FIJOS
        pres = escaleta.PRESENTADOR.get(nombre)
        col = COLOR[nombre]
        d.rectangle([MARG, y, MARG + 9, y + FILA - 18], fill=col)
        if pres:
            cara = _cara(pres, FILA - 32)
            im.paste(cara, (MARG + 26, y + 2), cara)
        cx = MARG + 26 + 96
        d.text((cx, y), nombre, font=f(30, True), fill=TINTA)
        wn = d.textlength(nombre, font=f(30, True))
        if fijo:
            mins = escaleta.FIJOS[nombre]
            d.text((cx + wn + 18, y + 8), "%d:%02d  fijo" % (int(mins), round((mins % 1) * 60)),
                   font=f(23, True), fill=GRIS)
        else:
            a = rep_t["bloques"][nombre]["minutos"]
            b = rep_g["bloques"][nombre]["minutos"]
            lo, hi = escaleta.BLOQUES[nombre][0], escaleta.BLOQUES[nombre][1]
            d.text((cx + wn + 18, y + 8),
                   "%d:%02d  ↔  %d:%02d" % (int(a), round((a % 1) * 60), int(b), round((b % 1) * 60)),
                   font=f(23, True), fill=col)
            d.text((cx + wn + 170, y + 10),
                   "(entre %d:%02d y %d:%02d)" % (int(lo), round((lo % 1) * 60),
                                                  int(hi), round((hi % 1) * 60)),
                   font=f(20), fill=GRIS)
        if pres:
            d.text((cx + wn + 340, y + 9), "· %s" % NOMBRE[pres], font=f(20), fill=GRIS)
        d.text((cx, y + 40), QUE[nombre], font=f(24), fill=(72, 66, 56))
        if FICHAS.get(nombre):
            d.text((cx, y + 70), "fichas:  " + FICHAS[nombre], font=f(21), fill=ROJO)
        y += FILA

    y += 14
    d.line([(MARG, y), (W - MARG, y)], fill=(196, 184, 162), width=3)
    y += 22
    for i, ln in enumerate([
        "COMO SE REPARTEN LOS MINUTOS",
        "1.  Lo fijo primero (cold open, intro, outro). Despues cada bloque se lleva su MINIMO: asi ninguno desaparece nunca.",
        "2.  Lo que sobra se reparte segun el peso del dia — la suma de importancia de sus acontecimientos, con tope por acontecimiento.",
        "3.  Latinoamerica conserva su minuto y medio aunque no haya pasado nada: la audiencia que viene por eso vuelve manana.",
        "4.  WHAT TO WATCH no depende del peso: es el calendario, y cierra siempre.",
    ]):
        d.text((MARG, y + i * 34), ln, font=f(25, True) if i == 0 else f(24),
               fill=TINTA if i == 0 else (72, 66, 56))

    out = os.path.join(BASE, "_estructura.jpg")
    im.save(out, quality=94)
    print(out, im.size)
    print("  tranquilo %.1f min · guerra %.1f min" % (rep_t["total_min"], rep_g["total_min"]))
    return out


if __name__ == "__main__":
    dibujar()
