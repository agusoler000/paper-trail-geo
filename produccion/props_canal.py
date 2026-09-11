# -*- coding: utf-8 -*-
"""Piezas de papel EXCLUSIVAS de la intro y la outro del canal (no del episodio). 0 creditos: todo dibujado.

Pedido de Agustin (2026-09-11): la intro y la outro tienen que pedir suscripcion Y like, y ser mas emotivas
y de altisima calidad. De aca salen las tres cosas que faltaban:

  pulgar()     el "me gusta" como recorte de papel (no un icono de YouTube pegado encima)
  documento()  un expediente generico con banda de color y renglones: es el objeto que llena la mesa
  luz()        charco de luz calido + vineta en UNA capa; es lo que convierte la mesa plana en un set

`luz()` se usa con la clase Overlay de intro_outro.py, que la reescala a la ventana de camara en cada cuadro
(si no, al hacer zoom la vineta quedaria descentrada).
"""
import numpy as np
from PIL import Image, ImageDraw
from props import (papel, rect, texto, TINTA, PAPEL, OCRE, AZUL, ROJO, BLANCO, GRIS, MADERA, FONT)

_RNG = np.random.default_rng(11)


def pulgar(w=190, color=OCRE, giro=-7):
    """Pulgar arriba recortado en papel (el 'me gusta' del canal, no el icono de YouTube pegado encima)."""
    h = int(w * 1.30)

    def f(d):
        d.rounded_rectangle([w * 0.26, h * 0.40, w * 0.97, h * 0.94], radius=int(w * 0.14), fill=255)   # puno
        d.rounded_rectangle([w * 0.28, h * 0.06, w * 0.56, h * 0.50], radius=int(w * 0.13), fill=255)   # pulgar
        d.rounded_rectangle([w * 0.24, h * 0.31, w * 0.66, h * 0.56], radius=int(w * 0.11), fill=255)   # nudillo
        d.rounded_rectangle([w * 0.00, h * 0.52, w * 0.40, h * 0.97], radius=int(w * 0.09), fill=255)   # muneca

    p = papel((w + 2, h + 2), f, color)
    d = ImageDraw.Draw(p)
    for k in range(3):                                   # pliegues de los dedos cerrados
        y = h * (0.57 + k * 0.115)
        d.line([(w * 0.47, y), (w * 0.90, y)], fill=TINTA + (190,), width=3)
    d.line([(w * 0.40, h * 0.58), (w * 0.40, h * 0.92)], fill=TINTA + (130,), width=3)       # canto de la mano
    d.line([(w * 0.06, h * 0.88), (w * 0.34, h * 0.88)], fill=TINTA + (110,), width=3)       # puno de la camisa
    return p.rotate(giro, resample=Image.BICUBIC, expand=True)


def documento(w=250, h=320, banda=AZUL, renglones=8, seed=0, sello_txt=None, sello_color=ROJO, firma=False):
    """Expediente de papel: banda de color arriba, renglones desparejos, sello o firma opcionales."""
    p = rect(w, h, BLANCO, r=6)
    d = ImageDraw.Draw(p)
    d.rectangle([10, 10, w - 11, int(h * 0.15)], fill=banda + (255,))
    d.rectangle([10, int(h * 0.15), w - 11, int(h * 0.16)], fill=TINTA + (120,))
    r = np.random.default_rng(1000 + seed)
    y = h * 0.25
    k = 0
    while y < h * (0.80 if firma else 0.90) and k < renglones:
        x2 = w - 24 - int(r.integers(0, max(1, int(w * 0.38))))
        d.line([(22, y), (x2, y)], fill=GRIS + (185,), width=3)
        y += h * 0.077
        k += 1
    if firma:
        d.line([(28, h * 0.87), (w * 0.55, h * 0.87)], fill=TINTA + (200,), width=3)
        pts = [(34 + i * (w * 0.42 / 12), h * 0.87 - 16 * np.sin(i * 1.1) * (1 - i / 14)) for i in range(13)]
        d.line([(float(a), float(b)) for a, b in pts], fill=AZUL + (255,), width=4, joint='curve')
    if sello_txt:
        # el sello se mide a partir del texto: si no, una palabra larga se corta contra su propio lienzo
        med = ImageDraw.Draw(Image.new('L', (10, 10)))
        fs = int(h * 0.125)
        f = FONT(fs); bb = med.textbbox((0, 0), sello_txt, font=f)
        pad = int(fs * 0.42); sw = bb[2] - bb[0] + 2 * pad
        if sw > w * 0.88:                                    # achica hasta que entre en el documento
            fs = max(11, int(fs * (w * 0.88) / sw)); f = FONT(fs)
            bb = med.textbbox((0, 0), sello_txt, font=f); pad = int(fs * 0.42); sw = bb[2] - bb[0] + 2 * pad
        sh = bb[3] - bb[1] + 2 * pad
        s = Image.new('RGBA', (sw, sh), (0, 0, 0, 0)); ds = ImageDraw.Draw(s)
        ds.rounded_rectangle([2, 2, sw - 3, sh - 3], radius=8, outline=sello_color + (215,), width=max(3, fs // 9))
        ds.text((sw / 2, sh / 2), sello_txt, fill=sello_color + (225,), font=f, anchor='mm')
        s = s.rotate(11, resample=Image.BICUBIC, expand=True)
        p.alpha_composite(s, (max(0, int((w - s.width) / 2)), max(0, int(h * 0.55 - s.height / 2))))
    return p


def clip(w=54, color=(150, 148, 140)):
    """Clip metalico: da escala y desorden creible a una pila."""
    h = int(w * 2.3)
    p = Image.new('RGBA', (w + 6, h + 6), (0, 0, 0, 0))
    d = ImageDraw.Draw(p)
    for off, col, wd in ((3, (20, 18, 14, 70), 9), (0, color + (255,), 8)):
        d.rounded_rectangle([6 + off, 5 + off, w - 4 + off, h - 10 + off], radius=w // 2, outline=col, width=wd)
        d.rounded_rectangle([14 + off, 16 + off, w - 12 + off, h - 2 + off], radius=w // 3, outline=col, width=wd)
    return p


def mancha(r=90, color=(120, 84, 48)):
    """Cerco de cafe sobre la mesa: la mancha que dice que alguien trabaja aca."""
    p = Image.new('RGBA', (2 * r, 2 * r), (0, 0, 0, 0))
    d = ImageDraw.Draw(p)
    d.ellipse([6, 6, 2 * r - 6, 2 * r - 6], outline=color + (92,), width=9)
    d.ellipse([16, 16, 2 * r - 16, 2 * r - 16], outline=color + (40,), width=16)
    return p


def luz(w=1920, h=1080, cx=0.44, cy=0.36, r=0.86, calido=(255, 216, 152), a=62, vin=168):
    """Charco de luz calido + vineta, en una sola capa RGBA.

    a   = cuanto ilumina el centro (0-255)      vin = cuanto oscurece el borde (0-255)
    El color se premultiplica y se divide por el alfa final para que las dos capas convivan sin bandas.
    """
    yy, xx = np.mgrid[0:h, 0:w]
    dx = (xx - cx * w) / (r * w * 0.62)
    dy = (yy - cy * h) / (r * h * 0.62)
    dist = np.sqrt(dx * dx + dy * dy).astype(np.float32)
    warm = np.clip(1.0 - dist, 0, 1) ** 1.7
    dark = np.clip((dist - 0.62) / 1.05, 0, 1) ** 1.25
    wa = warm * (a / 255.0)
    da = dark * (vin / 255.0)
    al = np.clip(wa + da, 0, 1)
    col = (np.array(calido, np.float32)[None, None, :] * wa[..., None]
           + np.array((24, 19, 13), np.float32)[None, None, :] * da[..., None]) / np.maximum(al[..., None], 1e-6)
    out = np.dstack([np.clip(col, 0, 255).astype(np.uint8), (al * 255).astype(np.uint8)])
    return Image.fromarray(out, 'RGBA')


def sombra_pie(w=320, h=76, a=88):
    """Sombra de contacto bajo un rig: sin esto el personaje flota sobre la hoja."""
    from PIL import ImageFilter
    p = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(p)
    d.ellipse([w * 0.06, h * 0.12, w * 0.94, h * 0.88], fill=(26, 20, 14, a))
    return p.filter(ImageFilter.GaussianBlur(h * 0.22))


if __name__ == '__main__':
    import os
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_qc_canal')
    os.makedirs(d, exist_ok=True)
    pulgar().save(os.path.join(d, 'pulgar.png'))
    documento(sello_txt='SETTLED').save(os.path.join(d, 'doc_sello.png'))
    documento(banda=ROJO, firma=True, seed=3).save(os.path.join(d, 'doc_firma.png'))
    clip().save(os.path.join(d, 'clip.png'))
    luz().save(os.path.join(d, 'luz.png'))
    print('ok ->', d)
