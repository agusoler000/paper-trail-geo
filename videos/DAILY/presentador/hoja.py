# -*- coding: utf-8 -*-
"""Hoja de contacto de los candidatos a presentador del formato diario."""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
PAPEL = (233, 223, 203)
TINTA = (34, 32, 28)
ROJO = (184, 64, 47)

OPCIONES = [
    ("A_corresponsal.jpg", "A · EL CORRESPONSAL", "THE POWERS  ·  abre y cierra"),
    ("B_analista.jpg",     "B · EL ANALISTA",     "THE SOUTH  ·  THE PACIFIC"),
    ("C_archivista.jpg",   "C · EL ARCHIVISTA",   "THE MONEY  ·  TECH  ·  WHAT TO WATCH"),
]

CW, CH = 620, 830          # celda
MARG, GAP, CAB = 46, 30, 130


def fuente(px, bold=False):
    for n in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(n, px)
        except Exception:
            pass
    return ImageFont.load_default()


W = MARG * 2 + CW * 3 + GAP * 2
H = CAB + CH + 110 + MARG
hoja = Image.new("RGB", (W, H), PAPEL)
d = ImageDraw.Draw(hoja)

d.text((MARG, 44), "LA MESA — FORMATO DIARIO", font=fuente(52, True), fill=TINTA)
d.text((MARG, 104), "tres presentadores, puesto fijo · recorte de papel · las noticias rotan, los puestos no",
       font=fuente(26), fill=(90, 84, 74))

for i, (arch, titulo, nota) in enumerate(OPCIONES):
    x = MARG + i * (CW + GAP)
    y = CAB + 30
    im = Image.open(os.path.join(BASE, arch)).convert("RGB")
    im.thumbnail((CW, CH), Image.LANCZOS)
    ox = x + (CW - im.width) // 2
    d.rectangle([x - 3, y - 3, x + CW + 3, y + CH + 3], outline=(196, 184, 162), width=3)
    hoja.paste(im, (ox, y + (CH - im.height) // 2))
    d.text((x, y + CH + 22), titulo, font=fuente(32, True), fill=TINTA)
    d.text((x, y + CH + 62), nota, font=fuente(25), fill=ROJO)

out = os.path.join(BASE, "_hoja_presentadores.jpg")
hoja.save(out, quality=94)
print(out, hoja.size)
