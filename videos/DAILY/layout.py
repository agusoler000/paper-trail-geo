# -*- coding: utf-8 -*-
"""Cuadro fijo del layout del formato diario. Para aprobar ANTES de animar nada.
Presentador a la izquierda, ficha `versus` a la derecha. Sin creditos: todo dibujado.
    python videos/DAILY/layout.py
"""
import os, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080

TINTA = (34, 32, 28)
MAPA = (220, 207, 180)
ROJO = (184, 64, 47)       # UN SOLO elemento rojo por plano
AZUL = (43, 76, 111)
OCRE = (217, 164, 65)
GRIS = (140, 130, 114)

CREASE = 952               # el pliegue entre paneles
HDR = 96


def f(px, bold=False):
    for n in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(n, px)
        except Exception:
            pass
    return ImageFont.load_default()


def wrap(d, txt, font, maxw):
    out, linea = [], ""
    for p in txt.split():
        t = (linea + " " + p).strip()
        if d.textlength(t, font=font) <= maxw:
            linea = t
        else:
            if linea:
                out.append(linea)
            linea = p
    if linea:
        out.append(linea)
    return out


def grano(im, fuerza=7):
    r = random.Random(7)
    n = Image.new("L", (im.width // 2, im.height // 2))
    n.putdata([r.randint(128 - fuerza, 128 + fuerza) for _ in range(n.width * n.height)])
    n = n.resize(im.size, Image.BILINEAR).filter(ImageFilter.GaussianBlur(0.4))
    return Image.blend(im, Image.merge("RGB", (n, n, n)), 0.10)


def tarjeta(im, box, fill, rot=0.0):
    """Tarjeta de papel con sombra proyectada y un grado de rotacion."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    pad = 50
    sh = Image.new("L", (w + pad * 2, h + pad * 2), 0)
    ImageDraw.Draw(sh).rectangle([pad + 5, pad + 9, pad + w + 5, pad + h + 9], fill=95)
    sh = sh.filter(ImageFilter.GaussianBlur(11))
    cap = Image.new("RGBA", sh.size, (0, 0, 0, 0))
    cap.paste(Image.new("RGB", sh.size, (60, 52, 40)), (0, 0), sh)
    ImageDraw.Draw(cap).rectangle([pad, pad, pad + w, pad + h], fill=fill + (255,))
    if rot:
        cap = cap.rotate(rot, resample=Image.BICUBIC, expand=False)
    im.paste(cap, (x0 - pad, y0 - pad), cap)


def sello(im, xy, lineas, color, ancho, alto, rot=-1.4):
    st = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    ds = ImageDraw.Draw(st)
    ds.rectangle([3, 3, ancho - 4, alto - 4], outline=color, width=5)
    for (txt, px, bold, dy) in lineas:
        ds.text((28, dy), txt, font=f(px, bold), fill=color)
    st = st.rotate(rot, resample=Image.BICUBIC, expand=False)
    im.paste(st, xy, st)


# ---------------------------------------------------------------- lienzo
# el presentador viene con alfa (Bria RMBG 2.0): sin rectangulo de fondo
pres = Image.open(os.path.join(BASE, "presentador", "A_corresponsal_alpha.png")).convert("RGBA")
pres = pres.crop(pres.getbbox())
PAPEL = (233, 223, 203)
FONDO_IZQ = (240, 232, 214)                # panel del presentador, un punto mas claro

im = Image.new("RGB", (W, H), PAPEL)
d = ImageDraw.Draw(im)
d.rectangle([0, HDR, CREASE, H], fill=FONDO_IZQ)

# el pliegue: sombra suave, como una hoja doblada
pl = Image.new("L", (W, H), 0)
dp = ImageDraw.Draw(pl)
for i in range(26):
    dp.line([(CREASE - 13 + i, HDR), (CREASE - 13 + i, H)], fill=int(64 * (1 - abs(i - 13) / 13.0)))
im.paste(Image.new("RGB", (W, H), TINTA), (0, 0), pl.filter(ImageFilter.GaussianBlur(6)))

# ---------------------------------------------------------------- cabecera
d.rectangle([0, 0, W, HDR], fill=PAPEL)
d.line([(0, HDR), (W, HDR)], fill=(196, 184, 162), width=3)
x = 54
d.text((x, 30), "THE LEDGER", font=f(40, True), fill=TINTA)
x += d.textlength("THE LEDGER", font=f(40, True)) + 22
d.text((x, 41), "· daily", font=f(27), fill=GRIS)
fecha = "11 SEPTEMBER 2026"
d.text((W - 54 - d.textlength(fecha, font=f(27)), 42), fecha, font=f(27), fill=GRIS)

# ---------------------------------------------------------------- panel izq: presentador
alto = 846
pres = pres.resize((int(pres.width * alto / pres.height), alto), Image.LANCZOS)
im.paste(pres, ((CREASE - pres.width) // 2, H - alto), pres)

# sello del bloque, arriba a la izquierda (chyron) — ya no pisa el titular
sello(im, (54, 136), [("THE POWERS", 38, True, 20)], AZUL, 330, 76, rot=-1.2)

# lower third del presentador
d.rectangle([0, 966, 548, 1046], fill=AZUL)
d.text((54, 980), "THE CORRESPONDENT", font=f(33, True), fill=PAPEL)
d.text((54, 1016), "washington · brussels · moscow desk", font=f(21), fill=(196, 208, 222))

# ---------------------------------------------------------------- panel der: ficha VERSUS
RX, RW = CREASE + 62, W - CREASE - 124

d.text((RX, 146), "EVENT 04  ·  06:12 UTC  ·  IMPORTANCE 71", font=f(23, True), fill=GRIS)
y = 182
for ln in wrap(d, "DRONE STRIKE ON BELGOROD", f(56, True), RW):
    d.text((RX, y), ln, font=f(56, True), fill=TINTA)
    y += 62
d.line([(RX, y + 16), (RX + 116, y + 16)], fill=TINTA, width=5)

CAJA_H = 228
for idx, (actor, color, texto, fuentes) in enumerate([
    ("RUSSIA  ·  claims", AZUL,
     "Air defences shot down 20 Ukrainian drones over the region. No damage on the ground.",
     "MoD statement · TASS · RT"),
    ("UKRAINE  ·  claims", OCRE,
     "The strike reached its target: the Belgorod refinery is out of service.",
     "General Staff · Ukrinform"),
]):
    cy = 342 + idx * (CAJA_H + 32)
    tarjeta(im, (RX, cy, RX + RW, cy + CAJA_H), MAPA, rot=(-0.4 if idx == 0 else 0.35))
    d.rectangle([RX, cy, RX + 13, cy + CAJA_H], fill=color)
    d.text((RX + 40, cy + 24), actor, font=f(30, True), fill=color)
    for i, ln in enumerate(wrap(d, texto, f(33), RW - 92)):
        d.text((RX + 40, cy + 74 + i * 44), ln, font=f(33), fill=TINTA)
    d.text((RX + 40, cy + CAJA_H - 42), fuentes, font=f(22), fill=GRIS)

# el UNICO rojo del cuadro: el sello de evidencia. Ancho acotado para no pisar los contadores.
sy = 342 + 2 * (CAJA_H + 32) + 10
sello(im, (RX, sy), [("INDEPENDENT EVIDENCE", 25, True, 18),
                     ("INSUFFICIENT", 40, True, 50)], ROJO, 566, 102, rot=-1.5)
d.text((RX + 612, sy + 26), "0  primary sources", font=f(24), fill=GRIS)
d.text((RX + 612, sy + 58), "2  blocs covering", font=f(24), fill=GRIS)

im = grano(im)
out = os.path.join(BASE, "_layout.jpg")
im.save(out, quality=95)
print(out, im.size, "fondo panel izq:", FONDO_IZQ)
