# -*- coding: utf-8 -*-
"""Miniatura del diario. 1280x720, coste cero, sin creditos.

    python videos/DAILY/miniatura.py 2026-09-14

REGLA DE AGUSTIN (feedback-titulos-y-miniaturas, 2026-09-13): fondo oscuro, cara grande y cifra
en rojo, disenada para el clic. La cifra tiene que ser la misma que promete el titulo, y tiene que
cumplirse en el video.

Lo que NO lleva, por la evidencia de `canal/_anexo_evidencia_titulos_2026-09-13.md` §4: sello de
marca grande, bandas de texto chico, ni mas de tres elementos.

TRES VARIANTES POR EPISODIO, siempre (practica del canal: `canal/out/_miniatura_02A/B/C_chica.jpg`).
Cada una va con SU titulo: la miniatura y el titulo son una sola prueba, no dos. La configuracion de
cada dia vive en `_dias/<fecha>/miniatura.json`:

    {"variantes": [
        {"clave": "A", "cifra": "$101", "pie": "OIL", "linea": "AND THE FED DECIDES WEDNESDAY",
         "presentador": "A", "titulo": "..."},
        ...]}

Salida: `miniatura_A.jpg`, `miniatura_B.jpg`, `miniatura_C.jpg` a 1280x720, mas `_miniaturas.jpg`,
la hoja de comparacion a tamano de feed (320 px de ancho, que es como se ven de verdad).
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "presentador"))
from PIL import Image, ImageDraw, ImageFilter, ImageFont   # noqa: E402

W, H = 1280, 720
FONDO = (26, 28, 34)          # tinta muy oscura, no negro puro: sigue siendo papel
FONDO2 = (44, 48, 58)
ROJO = (206, 62, 45)
PAPEL = (238, 231, 214)
GRIS = (150, 148, 142)
ALPHA = {"A": "A_corresponsal_alpha.png", "B": "B_analista_alpha.png",
         "C": "C_archivista_alpha.png"}


def _f(px, bold=True):
    for n in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(n, px)
        except Exception:
            pass
    return ImageFont.load_default()


def _encaja(dr, txt, maxw, px0, bold=True, pxmin=40):
    """Baja el cuerpo hasta que la linea entra en maxw. Un titulo largo no puede salirse del cuadro."""
    px = px0
    while px > pxmin and dr.textlength(txt, font=_f(px, bold)) > maxw:
        px -= 4
    return _f(px, bold)


def _cabeza(clave):
    """Recorta la cabeza del rig: la banda superior del alfa, que es donde esta la cara."""
    ruta = os.path.join(BASE, "presentador", ALPHA.get(clave, ALPHA["A"]))
    im = Image.open(ruta).convert("RGBA")
    caja = im.split()[3].point(lambda v: 255 if v > 40 else 0).getbbox() or (0, 0, *im.size)
    x0, y0, x1, y1 = caja
    alto = int((y1 - y0) * 0.46)                 # cabeza + hombros
    return im.crop((x0, y0, x1, y0 + alto))


def construir(cifra, pie, linea, presentador="A"):
    im = Image.new("RGB", (W, H), FONDO)
    d = ImageDraw.Draw(im)
    # degradado diagonal suave, para que el fondo oscuro no sea una plancha plana
    grad = Image.new("L", (W, H))
    ImageDraw.Draw(grad).polygon([(0, H), (W, 0), (W, H)], fill=90)
    im.paste(Image.new("RGB", (W, H), FONDO2), (0, 0), grad.filter(ImageFilter.GaussianBlur(180)))

    # la cara, grande y a la derecha
    cab = _cabeza(presentador)
    alto = int(H * 0.94)
    cab = cab.resize((int(cab.width * alto / cab.height), alto), Image.LANCZOS)
    sombra = Image.new("RGBA", cab.size, (0, 0, 0, 0))
    sombra.paste((0, 0, 0, 150), (0, 0), cab.split()[3])
    sombra = sombra.filter(ImageFilter.GaussianBlur(18))
    x = W - cab.width + int(cab.width * 0.10)
    im.paste(sombra, (x - 10, H - alto + 16), sombra)
    im.paste(cab, (x, H - alto), cab)

    # la cifra en rojo: el unico rojo del cuadro
    # la cifra no puede tocar la cara: se corta antes de donde empieza el rig
    maxw = int(W * 0.47)
    fc = _encaja(d, cifra, maxw, 260, pxmin=110)
    d.text((58, 92), cifra, font=fc, fill=ROJO)
    ycif = 92 + int(fc.size * 1.06)

    # Las dos lineas de texto van GRANDES o no van. La prueba no es a 1280 px: es a 320, que es
    # como se ve una miniatura en el feed. En la primera tanda del 14-sep la tercera linea entraba
    # a 34 px y a tamano real no se leia nada. Regla del canal: cara grande, cifra, <=3 palabras.
    if pie:
        fp = _encaja(d, pie, maxw, 104, pxmin=64)
        d.text((64, ycif), pie, font=fp, fill=PAPEL)
        ycif += int(fp.size * 1.22)

    if linea:
        if len(linea.split()) > 4:
            raise SystemExit("miniatura: '%s' tiene %d palabras. El maximo es 4: a 320 px del "
                             "feed una linea mas larga no se lee." % (linea, len(linea.split())))
        fl = _encaja(d, linea, maxw, 78, pxmin=50)
        d.text((64, ycif), linea, font=fl, fill=ROJO if not pie else PAPEL)

    # regla roja fina bajo la cifra: cierra el bloque de texto sin sumar un cuarto elemento
    d.rectangle([58, 76, 58 + 148, 86], fill=ROJO)
    return im


def _partir(d, txt, fnt, maxw):
    lineas, act = [], ""
    for p in txt.split():
        prueba = (act + " " + p).strip()
        if d.textlength(prueba, font=fnt) > maxw and act:
            lineas.append(act)
            act = p
        else:
            act = prueba
    if act:
        lineas.append(act)
    return lineas[:2]


def hoja(variantes, imgs, destino, ancho=320):
    """Las tres una al lado de la otra al tamano REAL del feed. Una miniatura se elige a 320 px,
       no a 1280: lo que no se lee ahi, no existe."""
    alto = int(ancho * 9 / 16)
    MAR, PIE = 18, 40
    hoja = Image.new("RGB", (len(imgs) * ancho + MAR * (len(imgs) + 1), alto + PIE + MAR * 2),
                     (243, 238, 228))
    d = ImageDraw.Draw(hoja)
    for i, (v, im) in enumerate(zip(variantes, imgs)):
        x = MAR + i * (ancho + MAR)
        hoja.paste(im.resize((ancho, alto), Image.LANCZOS), (x, MAR))
        d.text((x, MAR + alto + 8), v.get("clave", "?"), font=_f(20, True), fill=(40, 38, 34))
        d.text((x + 26, MAR + alto + 10), (v.get("cifra", "") + " " + v.get("pie", "")).strip(),
               font=_f(16, False), fill=(110, 104, 96))
    hoja.save(destino, quality=92)
    return destino


if __name__ == "__main__":
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    if not fecha:
        raise SystemExit("uso: python videos/DAILY/miniatura.py <fecha>")
    d = os.path.join(BASE, "_dias", fecha)
    cfg = json.load(open(os.path.join(d, "miniatura.json"), encoding="utf-8"))
    variantes = cfg.get("variantes") or [cfg]
    imgs = []
    for v in variantes:
        im = construir(v.get("cifra", ""), v.get("pie", ""), v.get("linea", ""),
                       v.get("presentador", "A"))
        dest = os.path.join(d, "miniatura_%s.jpg" % v.get("clave", "A"))
        im.save(dest, quality=94)
        imgs.append(im)
        print(dest)
    if len(imgs) > 1:
        print(hoja(variantes, imgs, os.path.join(d, "_miniaturas.jpg")))
