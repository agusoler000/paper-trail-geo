# -*- coding: utf-8 -*-
"""Props propios del ep. 13, dibujados por codigo. **0 creditos** (regla 19: primero se busca en el
catalogo; esto es lo que el catalogo NO tiene o tiene contaminado).

Por que existe este modulo. La primera hoja de contacto (16-sep) enseno que varios props del
catalogo compartido llevan **texto horneado de otros episodios** y no se pueden reusar aqui:

    expediente    -> dice "MALVINAS FALKLANDS"
    isla_recorte  -> es la silueta de las Malvinas
    diario_1      -> "Russia offers airlines reassurances"
    graf_gasto    -> "SOCIAL SPENDING PER PERSON"
    grafico_caida -> "-6%", de otro tema
    factura       -> "BILL" con el simbolo EURO, y este episodio habla de dolares
    bandera_rusa  -> es la bandera rusa (se habia usado como "bandera generica": error)
    regla_40      -> dice "40 KM", y el estrecho mide 30

Patron del catalogo (`props.py`): la FORMA se dibuja como mascara con `papel(size, fn, color)` —el
`fn` recibe un Draw en modo 'L', asi que ahi solo valen `fill=255`— y los detalles de color van
ENCIMA, con `ImageDraw.Draw(p)` y colores RGBA, o con `rect(w,h,color)` de base.

    python videos/13_yemen/arte/props13.py [--force]
"""
import os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', '..', '..', 'produccion'))
import props as PR
from PIL import Image, ImageDraw

SALIDA = os.path.join(AQUI, 'assets')
A = lambda c: tuple(c) + (255,)


def faro(w=150):
    """La torre de Perim. El catalogo solo tiene `antena`, que es una torre de telecomunicaciones."""
    h = int(w * 2.1)
    def fn(d):
        x = w / 2
        d.polygon([(x - w * 0.22, h - 2), (x + w * 0.22, h - 2), (x + w * 0.13, h * 0.30),
                   (x - w * 0.13, h * 0.30)], fill=255)
        d.rectangle([x - w * 0.19, h * 0.21, x + w * 0.19, h * 0.31], fill=255)
        d.rectangle([x - w * 0.12, h * 0.09, x + w * 0.12, h * 0.22], fill=255)
        d.polygon([(x - w * 0.17, h * 0.10), (x + w * 0.17, h * 0.10), (x, h * 0.01)], fill=255)
    p = PR.papel((w, h), fn, PR.PAPEL)
    d = ImageDraw.Draw(p)
    x = w / 2
    for i in range(3):
        y = h * (0.42 + 0.17 * i)
        d.rectangle([x - w * 0.165 + w * 0.012 * i, y, x + w * 0.165 - w * 0.012 * i,
                     y + h * 0.070], fill=A(PR.ROJO))
    d.rectangle([x - w * 0.115, h * 0.095, x + w * 0.115, h * 0.215], fill=A(PR.OCRE))
    d.rectangle([x - w * 0.19, h * 0.215, x + w * 0.19, h * 0.305], fill=A(PR.TINTA))
    return p


def tanquero(w=340):
    """Un petrolero. El catalogo tiene `barco_vela` (velero) y `buque_guerra`; ninguno sirve."""
    h = int(w * 0.44)
    def fn(d):
        d.polygon([(w * 0.03, h * 0.50), (w * 0.97, h * 0.50), (w * 0.88, h * 0.86),
                   (w * 0.12, h * 0.86)], fill=255)
        d.rectangle([w * 0.06, h * 0.38, w * 0.94, h * 0.52], fill=255)
        for i in range(4):
            cx = w * (0.17 + 0.20 * i)
            d.ellipse([cx - w * 0.058, h * 0.18, cx + w * 0.058, h * 0.40], fill=255)
        d.rectangle([w * 0.79, h * 0.10, w * 0.93, h * 0.40], fill=255)
    p = PR.papel((w, h), fn, PR.PAPEL)
    d = ImageDraw.Draw(p)
    d.polygon([(w * 0.04, h * 0.52), (w * 0.96, h * 0.52), (w * 0.88, h * 0.84),
               (w * 0.12, h * 0.84)], fill=A(PR.TINTA))
    for i in range(4):
        cx = w * (0.17 + 0.20 * i)
        d.ellipse([cx - w * 0.050, h * 0.20, cx + w * 0.050, h * 0.38], fill=A(PR.OCRE))
    return p


def tuberia(w=420):
    """El oleoducto East-West, para los planos de mesa."""
    h = int(w * 0.22)
    def fn(d):
        d.rectangle([0, h * 0.34, w - 1, h * 0.66], fill=255)
        for i in range(5):
            x = w * (0.10 + 0.20 * i)
            d.rectangle([x - w * 0.016, h * 0.20, x + w * 0.016, h * 0.80], fill=255)
    p = PR.papel((w, h), fn, PR.OCRE)
    d = ImageDraw.Draw(p)
    for i in range(5):
        x = w * (0.10 + 0.20 * i)
        d.rectangle([x - w * 0.013, h * 0.22, x + w * 0.013, h * 0.78], fill=A(PR.PAPEL))
    return p


def recibo_usd(w=330):
    """La factura del episodio, en DOLARES. `factura` del catalogo lleva el simbolo euro."""
    h = int(w * 1.32)
    p = PR.rect(w, h, PR.PAPEL, r=4)
    d = ImageDraw.Draw(p)
    PR.texto(p, 'THE RECEIPT', 38, (w / 2, h * 0.115), PR.TINTA)
    d.line([w * 0.10, h * 0.185, w * 0.90, h * 0.185], fill=A(PR.TINTA), width=3)
    for i in range(5):
        y = h * (0.29 + 0.093 * i)
        d.line([w * 0.12, y, w * (0.80 - 0.07 * (i % 3)), y], fill=(150, 145, 130, 255), width=4)
    PR.texto(p, '$', 96, (w / 2, h * 0.855), PR.ROJO)
    return p


def barriles(w=380):
    """Las dos cifras de barriles enfrentadas: 9,3 contra 4,1. Sustituye a `graf_gasto`."""
    h = int(w * 0.80)
    p = PR.rect(w, h, PR.PAPEL, r=4)
    d = ImageDraw.Draw(p)
    PR.texto(p, 'BARRELS / DAY', 28, (w / 2, h * 0.11), PR.TINTA)
    base = h * 0.84
    for i, (alt, col, et, cif) in enumerate(((0.56, PR.OCRE, '2023', '9.3'),
                                             (0.25, PR.ROJO, '2024', '4.1'))):
        cx = w * (0.30 + 0.40 * i)
        d.rectangle([cx - w * 0.115, base - h * alt, cx + w * 0.115, base], fill=A(col))
        d.rectangle([cx - w * 0.115, base - h * alt, cx + w * 0.115, base],
                    outline=A(PR.TINTA), width=3)
        PR.texto(p, et, 24, (cx, base + h * 0.075), PR.TINTA)
        PR.texto(p, cif, 34, (cx, base - h * alt - h * 0.055), PR.TINTA)
    return p


def isla(w=200):
    """La silueta de Perim. `isla_recorte` del catalogo son las Malvinas."""
    h = int(w * 0.74)
    def fn(d):
        d.polygon([(w * 0.10, h * 0.52), (w * 0.28, h * 0.24), (w * 0.62, h * 0.18),
                   (w * 0.88, h * 0.38), (w * 0.82, h * 0.70), (w * 0.46, h * 0.82),
                   (w * 0.18, h * 0.74)], fill=255)
    p = PR.papel((w, h), fn, PR.MAPA)
    d = ImageDraw.Draw(p)
    d.ellipse([w * 0.45, h * 0.41, w * 0.57, h * 0.53], fill=A(PR.ROJO))
    return p


def carro(w=210):
    """El carro del supermercado, para la cadena del ACT V."""
    h = int(w * 0.88)
    def fn(d):
        d.polygon([(w * 0.22, h * 0.22), (w * 0.94, h * 0.22), (w * 0.80, h * 0.62),
                   (w * 0.34, h * 0.62)], fill=255)
        d.line([w * 0.05, h * 0.10, w * 0.25, h * 0.10], fill=255, width=7)
        d.line([w * 0.25, h * 0.10, w * 0.31, h * 0.62], fill=255, width=7)
        for cx in (w * 0.42, w * 0.74):
            d.ellipse([cx - w * 0.058, h * 0.68, cx + w * 0.058, h * 0.80], fill=255)
    p = PR.papel((w, h), fn, PR.PAPEL)
    d = ImageDraw.Draw(p)
    for cx in (w * 0.42, w * 0.74):
        d.ellipse([cx - w * 0.050, h * 0.69, cx + w * 0.050, h * 0.79], fill=A(PR.TINTA))
    for i in range(3):
        d.line([w * (0.35 + 0.16 * i), h * 0.25, w * (0.31 + 0.16 * i), h * 0.59],
               fill=(150, 145, 130, 255), width=3)
    return p


def regla_30(w=300):
    """La regla que mide el estrecho. `regla_40` del catalogo dice 40 KM."""
    h = int(w * 0.17)
    p = PR.rect(w, h, PR.OCRE, r=3)
    d = ImageDraw.Draw(p)
    for i in range(1, 20):
        x = w * i / 20.0
        d.line([x, 0, x, h * (0.34 if i % 5 else 0.52)], fill=A(PR.TINTA), width=3)
    PR.texto(p, '30 KM', 30, (w / 2, h * 0.72), PR.TINTA)
    return p


PROPS = {'faro': faro, 'tanquero': tanquero, 'tuberia': tuberia, 'recibo_usd': recibo_usd,
         'barriles': barriles, 'isla': isla, 'carro': carro, 'regla_30': regla_30}


def build(force=False):
    os.makedirs(SALIDA, exist_ok=True)
    hechos = {}
    for n, fn in PROPS.items():
        p = os.path.join(SALIDA, 'p13_%s.png' % n)
        if force or not os.path.exists(p):
            fn().save(p)
        hechos[n] = p
    return hechos


if __name__ == '__main__':
    h = build(force='--force' in sys.argv)
    cols, s = 4, 320
    filas = (len(h) + cols - 1) // cols
    hoja = Image.new('RGB', (cols * s, filas * (s + 28)), (238, 232, 218))
    dr = ImageDraw.Draw(hoja)
    for i, (n, p) in enumerate(sorted(h.items())):
        im = Image.open(p).convert('RGBA')
        k = min((s - 20) / im.width, (s - 20) / im.height)
        im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
        x, y = (i % cols) * s, (i // cols) * (s + 28)
        hoja.paste(im, (x + (s - im.width) // 2, y + (s - im.height) // 2), im)
        dr.text((x + 10, y + s + 6), n, fill=(30, 30, 30))
        print('  %-12s ok' % n)
    hoja.save(os.path.join(AQUI, '..', '_props13.jpg'), quality=90)
    print('  hoja -> _props13.jpg')
