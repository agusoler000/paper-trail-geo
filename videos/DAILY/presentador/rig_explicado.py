# -*- coding: utf-8 -*-
"""Diagrama: que es el rig. Izquierda, donde se corta y donde van los pivotes.
Derecha, que compra ese corte: el mismo brazo en muchas poses sin volver a generar nada.
    python videos/DAILY/presentador/rig_explicado.py
"""
import math, os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
PAPEL = (233, 223, 203)
TINTA = (34, 32, 28)
ROJO = (184, 64, 47)
AZUL = (43, 76, 111)
OCRE = (217, 164, 65)
PIEL = (240, 224, 196)
GRIS = (120, 112, 98)

# pivotes leidos sobre A_corresponsal_alpha.png (768x1024), ver _grid.jpg
PIV = {
    "cuello":   (390, 352),
    "hombro_i": (222, 422), "hombro_d": (546, 425),
    "codo_i":   (155, 545), "codo_d":   (613, 545),
    "muneca_i": (112, 652), "muneca_d": (655, 652),
}
BOCA = (390, 296)


def f(px, bold=False):
    for n in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(n, px)
        except Exception:
            pass
    return ImageFont.load_default()


def punteado(d, a, b, color, dash=11, hueco=8, w=3):
    (x0, y0), (x1, y1) = a, b
    L = math.hypot(x1 - x0, y1 - y0)
    if L == 0:
        return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    t = 0.0
    while t < L:
        t2 = min(t + dash, L)
        d.line([(x0 + ux * t, y0 + uy * t), (x0 + ux * t2, y0 + uy * t2)], fill=color, width=w)
        t += dash + hueco


def pivote(d, xy, r=17, etiqueta=None, fnt=None, lado="der"):
    x, y = xy
    d.ellipse([x - r, y - r, x + r, y + r], outline=ROJO, width=4)
    d.line([(x - r + 5, y), (x + r - 5, y)], fill=ROJO, width=2)
    d.line([(x, y - r + 5), (x, y + r - 5)], fill=ROJO, width=2)
    if etiqueta:
        tw = d.textlength(etiqueta, font=fnt)
        tx = x + r + 10 if lado == "der" else x - r - 10 - tw
        d.text((tx, y - 12), etiqueta, font=fnt, fill=ROJO)


# ---------------------------------------------------------------- lienzo
CW, CH = 900, 1150          # panel izquierdo (el presentador anotado)
RW = 880                    # panel derecho (la demostracion)
MARG, CAB = 56, 150
W, H = MARG * 3 + CW + RW, CAB + CH + MARG

hoja = Image.new("RGB", (W, H), PAPEL)
d = ImageDraw.Draw(hoja)

d.text((MARG, 40), "QUE ES EL RIG", font=f(58, True), fill=TINTA)
d.text((MARG, 106), "cortar el dibujo en piezas con pivote, para que se mueva sin volver a generarlo",
       font=f(28), fill=GRIS)

# ---------------------------------------------------------------- izquierda
im = Image.open(os.path.join(BASE, "A_corresponsal_alpha.png")).convert("RGBA")
esc = CH / im.height
im = im.resize((int(im.width * esc), CH), Image.LANCZOS)
ox, oy = MARG, CAB
hoja.paste(im, (ox, oy), im)

fp = f(24, True)


def P(k):
    x, y = PIV[k]
    return (ox + x * esc, oy + y * esc)


# lineas de corte
for a, b in [("cuello", "hombro_i"), ("cuello", "hombro_d"),
             ("hombro_i", "codo_i"), ("codo_i", "muneca_i"),
             ("hombro_d", "codo_d"), ("codo_d", "muneca_d")]:
    punteado(d, P(a), P(b), (60, 90, 130))

# la boca, su propia pieza
bx, by = ox + BOCA[0] * esc, oy + BOCA[1] * esc
d.rectangle([bx - 62, by - 26, bx + 62, by + 26], outline=OCRE, width=4)
d.text((bx + 74, by - 14), "la boca: 9 formas", font=fp, fill=OCRE)

for k, et, lado in [("cuello", "cuello", "der"),
                    ("hombro_i", "hombro", "izq"), ("codo_i", "codo", "izq"),
                    ("muneca_i", "muneca", "izq"),
                    ("hombro_d", "hombro", "der"), ("codo_d", "codo", "der"),
                    ("muneca_d", "muneca", "der")]:
    pivote(d, P(k), etiqueta=et, fnt=fp, lado=lado)

d.text((ox, oy + CH + 14), "7 pivotes  ·  9 piezas  ·  se corta UNA vez",
       font=f(30, True), fill=TINTA)

# ---------------------------------------------------------------- derecha
rx = MARG * 2 + CW
d.text((rx, CAB - 4), "QUE COMPRA ESE CORTE", font=f(34, True), fill=TINTA)

y = CAB + 62
d.text((rx, y), "Un brazo cortado en dos piezas con pivote en el hombro",
       font=f(26), fill=GRIS)
d.text((rx, y + 34), "y en el codo da cualquier pose, girando numeros:",
       font=f(26), fill=GRIS)

# demostracion: el mismo brazo a distintos angulos, dibujado con formas exactas
POSES = [(-28, -18, "reposo"), (12, -40, "senala"), (48, -75, "levanta"), (-8, 34, "baja")]
cx0, cy0 = rx + 118, y + 190
SEP = 205
for i, (a1, a2, nombre) in enumerate(POSES):
    cx = cx0 + (i % 2) * SEP * 1.75
    cy = cy0 + (i // 2) * 280
    # torso de referencia
    d.rectangle([cx - 34, cy - 30, cx + 34, cy + 120], fill=AZUL)
    # brazo: hombro -> codo
    L1, L2 = 96, 92
    r1 = math.radians(90 + a1)
    ex, ey = cx + 34 + L1 * math.cos(r1) * 0.55, cy + L1 * math.sin(r1) * 0.92
    d.line([(cx + 30, cy - 6), (ex, ey)], fill=AZUL, width=27)
    r2 = math.radians(90 + a1 + a2)
    hx, hy = ex + L2 * math.cos(r2) * 0.75, ey + L2 * math.sin(r2) * 0.92
    d.line([(ex, ey), (hx, hy)], fill=PIEL, width=23)
    d.ellipse([hx - 16, hy - 16, hx + 16, hy + 16], fill=PIEL)
    # remaches
    for px, py in ((cx + 30, cy - 6), (ex, ey)):
        d.ellipse([px - 9, py - 9, px + 9, py + 9], fill=(196, 190, 178), outline=(140, 132, 118), width=2)
    d.text((cx - 40, cy + 138), nombre, font=f(25, True), fill=TINTA)
    d.text((cx - 40, cy + 168), "hombro %+d°  codo %+d°" % (a1, a2), font=f(22), fill=GRIS)

# el cierre
cy = y + 690
d.line([(rx, cy), (rx + RW - 20, cy)], fill=(196, 184, 162), width=3)
for i, ln in enumerate([
    "Sin rig, el presentador es una foto: para moverlo hay",
    "que generar otra imagen, y sale distinta cada vez.",
    "",
    "Con rig, un episodio nuevo no genera NADA: mueve",
    "numeros. Y el lip-sync es cambiar la pieza de la boca",
    "24 veces por segundo.",
]):
    d.text((rx, cy + 26 + i * 38), ln, font=f(27, True) if i >= 3 else f(27),
           fill=TINTA if i >= 3 else GRIS)

out = os.path.join(BASE, "_rig_explicado.jpg")
hoja.save(out, quality=94)
print(out, hoja.size)
