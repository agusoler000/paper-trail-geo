# -*- coding: utf-8 -*-
"""Props de papel de la serie S10 («What Sweden Paid For»). 0 creditos: todo dibujado por codigo.

    cd videos/S10_suecia/arte && python props_s10.py [--hoja]

Regla 19 (reusar antes de generar). Del indice se reusan TAL CUAL, sin redibujar:
  `bandera_tr` (S05), `escuela` (S01), `billete` (ep. 05), `libro_mayor` y `papeleta`
  (produccion/assets), y toda la familia `sello_*`.
Aca se dibuja solo lo que no existia: la **bandera sueca**, el **libro quemado**, el **encuadre de
transmision en vivo**, el **cheque**, el **pupitre**, la **mesa de cocina** y tres sellos.

**El libro va sin una sola marca religiosa** — tapa lisa, cantos chamuscados, un señalador. La pieza
habla de un libro quemado; dibujarle escritura sagrada encima seria ilustrar la profanacion, que no
es lo que cuenta el guion y es exactamente lo que convierte una pieza periodistica en otra cosa.

Dibujadas para verse a media pantalla (leccion 4 del S03): ningun trazo por debajo de ~10 px sobre
el ancho nominal.
"""
import os, sys, math, random
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', '..', '..', 'produccion'))
from PIL import Image, ImageDraw, ImageFilter
from props import (papel, texto, card, sello, FONT, FONTC,
                   TINTA, PAPEL, OCRE, AZUL, ROJO, MAPA)

BLANCO = (245, 241, 230)
GRIS = (120, 115, 105)
OUT = os.path.join(AQUI, 'assets'); os.makedirs(OUT, exist_ok=True)

AZUL_SE = (0, 82, 147)          # azul de la bandera sueca
AMAR_SE = (247, 191, 0)         # amarillo de la cruz
CARBON = (48, 44, 40)           # el chamuscado
BRASA = (176, 74, 38)


def _bandera(w, h, pintar, etiqueta):
    """Molde del S05: la ficha ENTERA es de papel, etiqueta incluida."""
    H = h + 58
    def f(d): d.rounded_rectangle([1, 1, w-2, H-2], radius=10, fill=255)
    p = papel((w, H), f, PAPEL); d = ImageDraw.Draw(p)
    d.rectangle([10, 12, w-11, h-6], fill=BLANCO+(255,))
    pintar(d)
    d.rectangle([10, 12, w-11, h-6], outline=TINTA+(255,), width=3)
    texto(p, etiqueta, int(w*0.115), (w/2, h+22), color=TINTA, font=FONTC)
    return p


def bandera_se(w=300, h=188):
    """Bandera sueca: cruz nordica amarilla sobre azul, brazo vertical corrido al asta."""
    def pintar(d):
        x0, y0, x1, y1 = 10, 12, w-11, h-6
        d.rectangle([x0, y0, x1, y1], fill=AZUL_SE+(255,))
        W, H = x1-x0, y1-y0
        br = max(10, int(H*0.20))                 # ancho de los brazos
        cx = x0 + int(W*0.375)                    # vertical corrida al asta
        cy = y0 + H/2
        d.rectangle([x0, cy-br/2, x1, cy+br/2], fill=AMAR_SE+(255,))
        d.rectangle([cx-br/2, y0, cx+br/2, y1], fill=AMAR_SE+(255,))
    return _bandera(w, h, pintar, 'SWEDEN')


TAPA = (138, 106, 66)           # marron de la tapa: tiene que separarse del papel
LOMO = (104, 78, 48)


def libro_quemado(w=210):
    """Libro cerrado en perspectiva de tres cuartos, con la esquina superior comida por el fuego.

    Primera version: tapa del mismo tono que el papel y quemado en TODO el borde superior. En la
    hoja de contacto no se leia como libro sino como una hoja en blanco chamuscada. Arreglado con
    tres cosas: tapa marron (contraste contra el papel), bloque de hojas dibujado al canto, y el
    fuego comiendo UNA esquina en diagonal en vez del borde entero — asi la silueta del libro
    sobrevive, que es lo unico que tiene que leerse en 1080x1920 a media pantalla.
    """
    h = int(w*1.24)
    def f(d): d.rounded_rectangle([6, 4, w-7, h-5], radius=9, fill=255)
    p = papel((w, h), f, PAPEL); d = ImageDraw.Draw(p)
    L, R, T, B = 18, w-19, 16, h-18
    lomo_w = int(w*0.16)
    # bloque de hojas, corrido a la derecha y abajo (da el volumen)
    d.polygon([(L+lomo_w, T+10), (R+6, T+10), (R+6, B+6), (L+lomo_w, B+6)],
              fill=BLANCO+(255,), outline=TINTA+(255,))
    for i in range(9):
        y = T+18 + i*((B-T-20)/9.0)
        d.line([(R-2, y), (R+5, y)], fill=TINTA+(110,), width=2)
    # tapa
    d.polygon([(L, T), (R, T), (R, B), (L, B)], fill=TAPA+(255,), outline=TINTA+(255,))
    d.line([(L, T), (R, T), (R, B), (L, B), (L, T)], fill=TINTA+(255,), width=4)
    # lomo
    d.polygon([(L, T), (L+lomo_w, T), (L+lomo_w, B), (L, B)], fill=LOMO+(255,))
    d.line([(L+lomo_w, T), (L+lomo_w, B)], fill=TINTA+(255,), width=3)
    for yy in (T+int((B-T)*0.22), B-int((B-T)*0.22)):
        d.line([(L+5, yy), (L+lomo_w-5, yy)], fill=(70, 52, 32, 255), width=3)
    # el fuego come la esquina superior derecha, en diagonal
    rnd = random.Random(7)
    cx, cy = R-int(w*0.46), T                      # de aca
    ex, ey = R, T+int(h*0.40)                      # hasta aca
    borde = [(cx, cy)]
    pasos = 16
    for i in range(1, pasos+1):
        t = i/pasos
        bx = cx + (ex-cx)*t + (rnd.random()-0.5)*16
        by = cy + (ey-cy)*t + (rnd.random()-0.5)*16
        borde.append((bx, by))
    d.polygon(borde + [(R, T)], fill=PAPEL+(0,))   # hueco: se recorta abajo
    quem = Image.new('RGBA', p.size, (0, 0, 0, 0)); dq = ImageDraw.Draw(quem)
    dq.polygon(borde + [(R, T)], fill=CARBON+(255,))
    p.alpha_composite(quem)
    for (bx, by) in borde[::2]:                    # brasa sobre el filo del quemado
        d.ellipse([bx-5, by-5, bx+5, by+5], fill=BRASA+(225,))
    # humo saliendo de la esquina
    hu = Image.new('RGBA', p.size, (0, 0, 0, 0)); dh = ImageDraw.Draw(hu)
    for i in range(6):
        dh.ellipse([R-70+i*12, T-8-i*2, R-34+i*12, T+18-i*2], fill=(200, 196, 188, 70))
    p.alpha_composite(hu.filter(ImageFilter.GaussianBlur(6)))
    return p


def camara_vivo(w=300):
    """Encuadre de transmision en vivo: marco, esquinas y el punto LIVE."""
    h = int(w*0.72)
    def f(d): d.rounded_rectangle([1, 1, w-2, h-2], radius=10, fill=255)
    p = papel((w, h), f, PAPEL); d = ImageDraw.Draw(p)
    d.rectangle([14, 16, w-15, h-17], fill=(212, 204, 186, 255), outline=TINTA+(255,), width=3)
    c = 30
    for (ex, ey, dx, dy) in ((22, 24, 1, 1), (w-23, 24, -1, 1), (22, h-25, 1, -1), (w-23, h-25, -1, -1)):
        d.line([(ex, ey), (ex+dx*c, ey)], fill=TINTA+(255,), width=5)
        d.line([(ex, ey), (ex, ey+dy*c)], fill=TINTA+(255,), width=5)
    d.ellipse([w-74, 30, w-52, 52], fill=ROJO+(255,))
    texto(p, 'LIVE', int(w*0.072), (w-96, 41), color=ROJO, font=FONTC, anchor='rm')
    return p


def cheque(w=360, importe='29 000 000', concepto='STATE GRANT'):
    """Cheque de papel. El importe se pasa por parametro: sirve para los 29 M y para el corte."""
    h = int(w*0.46)
    def f(d): d.rounded_rectangle([1, 1, w-2, h-2], radius=8, fill=255)
    p = papel((w, h), f, BLANCO); d = ImageDraw.Draw(p)
    d.rectangle([12, 10, w-13, h-11], outline=TINTA+(255,), width=3)
    texto(p, concepto, int(w*0.058), (26, 30), color=GRIS, font=FONTC, anchor='lm')
    d.line([(26, 46), (w-26, 46)], fill=TINTA+(90,), width=2)
    texto(p, importe, int(w*0.125), (26, int(h*0.52)), color=TINTA, font=FONT, anchor='lm')
    texto(p, 'SEK', int(w*0.058), (w-30, int(h*0.52)), color=GRIS, font=FONTC, anchor='rm')
    d.line([(26, h-34), (int(w*0.52), h-34)], fill=TINTA+(150,), width=2)
    texto(p, 'SWEDEN', int(w*0.050), (26, h-22), color=GRIS, font=FONTC, anchor='lm')
    return p


def pupitre(w=250):
    """Pupitre con su silla, de perfil, con un libro encima.

    Primera version: un amasijo de palos finos que no se leia como pupitre. Arreglado dandole a
    cada pieza cuerpo (patas de 14 px, tapa de 18 px de canto) y poniendo la silla DETRAS con
    respaldo alto: la silueta pupitre+silla es lo que hace reconocible el objeto, no la mesa sola.
    """
    h = int(w*0.92)
    def f(d): d.rounded_rectangle([2, 2, w-3, h-3], radius=8, fill=255)
    p = papel((w, h), f, PAPEL); d = ImageDraw.Draw(p)
    MADERA = (198, 174, 132); MAD_OSC = (162, 138, 98)
    piso = h-22
    # silla, detras
    d.rectangle([int(w*0.62), int(h*0.22), int(w*0.62)+15, piso], fill=MAD_OSC+(255,),
                outline=TINTA+(255,), width=3)
    d.rectangle([int(w*0.50), int(h*0.56), int(w*0.84), int(h*0.56)+16], fill=MADERA+(255,),
                outline=TINTA+(255,), width=3)
    d.rectangle([int(w*0.80), int(h*0.60), int(w*0.80)+13, piso], fill=MAD_OSC+(255,),
                outline=TINTA+(255,), width=3)
    # tapa inclinada, con canto
    tapa = [(int(w*0.10), int(h*0.44)), (int(w*0.66), int(h*0.33)),
            (int(w*0.66), int(h*0.33)+18), (int(w*0.10), int(h*0.44)+18)]
    d.polygon(tapa, fill=MADERA+(255,)); d.line(tapa+[tapa[0]], fill=TINTA+(255,), width=4)
    # patas del pupitre
    d.rectangle([int(w*0.14), int(h*0.47), int(w*0.14)+14, piso], fill=MAD_OSC+(255,),
                outline=TINTA+(255,), width=3)
    d.rectangle([int(w*0.56), int(h*0.38), int(w*0.56)+14, piso], fill=MAD_OSC+(255,),
                outline=TINTA+(255,), width=3)
    d.line([(int(w*0.16), int(h*0.72)), (int(w*0.60), int(h*0.66))], fill=TINTA+(255,), width=5)
    # libro sobre la tapa
    d.polygon([(int(w*0.24), int(h*0.395)), (int(w*0.48), int(h*0.347)),
               (int(w*0.48), int(h*0.347)+11), (int(w*0.24), int(h*0.395)+11)],
              fill=BLANCO+(255,), outline=TINTA+(255,))
    d.line([(14, piso), (w-15, piso)], fill=TINTA+(255,), width=5)
    return p


def mesa_cocina(w=330):
    """Mesa de cocina: dos platos y dos sillas. Es la imagen del cierre de la pieza 3."""
    h = int(w*0.66)
    def f(d): d.rounded_rectangle([2, 2, w-3, h-3], radius=8, fill=255)
    p = papel((w, h), f, PAPEL); d = ImageDraw.Draw(p)
    d.ellipse([20, int(h*0.30), w-21, int(h*0.66)], fill=MAPA+(255,), outline=TINTA+(255,), width=4)
    for cx in (int(w*0.36), int(w*0.64)):
        d.ellipse([cx-30, int(h*0.38), cx+30, int(h*0.52)], fill=BLANCO+(255,), outline=TINTA+(255,), width=3)
    d.rectangle([int(w*0.46), int(h*0.62), int(w*0.54), h-20], fill=(198, 184, 156, 255),
                outline=TINTA+(255,), width=3)
    d.line([(int(w*0.30), h-20), (int(w*0.70), h-20)], fill=TINTA+(255,), width=4)
    # SIN SILLAS, a proposito. Se probaron dos veces: postes sueltos (flotaban) y sillas de
    # perfil (chocaban con la mesa, que esta vista desde arriba, y parecian morsas). La mesa
    # redonda con dos platos ya dice «mesa de cocina» sola, y encima va la linea del cierre.
    # Regla del canal: si un elemento no se lee en la hoja de contacto, se saca, no se insiste.
    # Tampoco migas: cayeron dentro de los platos y la mesa quedo con dos ojos y pupilas. Con dos
    # circulos y una elipse el ojo humano ve una cara antes que una mesa. Los platos van vacios.
    return p


# ------------------------------------------------------------------ cosas de Suecia
# Agregados el 2026-09-14 a pedido de Agustin ("pon mas mapas y cosas de Suecia"). Los tres son
# signos de Suecia que se reconocen sin texto: la casa roja de Falun, la corona y el Riksdag.
FALU = (150, 58, 44)            # el rojo de Falun, el color de las casas suecas
FALU_OSC = (118, 44, 34)


def casa_falu(w=250):
    """La casa roja de madera con marcos blancos. Es el signo visual de Suecia mas reconocible."""
    h = int(w*0.88)
    def f(d): d.rounded_rectangle([2, 2, w-3, h-3], radius=8, fill=255)
    p = papel((w, h), f, PAPEL); d = ImageDraw.Draw(p)
    x0, x1 = int(w*0.14), int(w*0.86)
    ybase, ytecho, ycumbre = h-26, int(h*0.42), int(h*0.14)
    d.polygon([(x0, ybase), (x0, ytecho), (w/2, ycumbre), (x1, ytecho), (x1, ybase)],
              fill=FALU+(255,), outline=TINTA+(255,))
    d.line([(x0, ytecho), (w/2, ycumbre), (x1, ytecho)], fill=TINTA+(255,), width=5)
    d.line([(x0, ybase), (x0, ytecho)], fill=TINTA+(255,), width=4)
    d.line([(x1, ybase), (x1, ytecho)], fill=TINTA+(255,), width=4)
    d.line([(x0, ybase), (x1, ybase)], fill=TINTA+(255,), width=5)
    # alero blanco
    d.line([(x0-12, ytecho+4), (w/2, ycumbre-6)], fill=BLANCO+(255,), width=9)
    d.line([(w/2, ycumbre-6), (x1+12, ytecho+4)], fill=BLANCO+(255,), width=9)
    # dos ventanas con cruz y una puerta
    for cx in (int(w*0.32), int(w*0.68)):
        d.rectangle([cx-24, ytecho+30, cx+24, ytecho+78], fill=BLANCO+(255,),
                    outline=TINTA+(255,), width=4)
        d.line([(cx, ytecho+30), (cx, ytecho+78)], fill=TINTA+(255,), width=3)
        d.line([(cx-24, ytecho+54), (cx+24, ytecho+54)], fill=TINTA+(255,), width=3)
    d.rectangle([int(w/2)-20, ybase-58, int(w/2)+20, ybase], fill=FALU_OSC+(255,),
                outline=TINTA+(255,), width=4)
    return p


def krona(w=190):
    """Moneda de una corona sueca: canto, corona estilizada y el 1 KR."""
    h = w
    def f(d): d.ellipse([2, 2, w-3, h-3], fill=255)
    p = papel((w, h), f, OCRE); d = ImageDraw.Draw(p)
    d.ellipse([2, 2, w-3, h-3], outline=TINTA+(255,), width=5)
    d.ellipse([int(w*0.10), int(h*0.10), int(w*0.90), int(h*0.90)], outline=TINTA+(170,), width=3)
    cx, cy = w/2, h*0.40
    d.polygon([(cx-38, cy+14), (cx-30, cy-16), (cx-14, cy+2), (cx, cy-24),
               (cx+14, cy+2), (cx+30, cy-16), (cx+38, cy+14)], fill=TINTA+(255,))
    d.rectangle([cx-40, cy+14, cx+40, cy+24], fill=TINTA+(255,))
    texto(p, '1 KR', int(w*0.20), (cx, h*0.74), color=TINTA, font=FONTC)
    return p


def riksdag(w=300):
    """El Riksdag: frontis con columnas. Es «el Estado sueco» en un objeto."""
    h = int(w*0.70)
    def f(d): d.rounded_rectangle([2, 2, w-3, h-3], radius=8, fill=255)
    p = papel((w, h), f, PAPEL); d = ImageDraw.Draw(p)
    base_y = h-24
    d.polygon([(int(w*0.10), int(h*0.40)), (w/2, int(h*0.14)), (int(w*0.90), int(h*0.40))],
              fill=MAPA+(255,), outline=TINTA+(255,))
    d.line([(int(w*0.10), int(h*0.40)), (w/2, int(h*0.14)), (int(w*0.90), int(h*0.40)),
            (int(w*0.10), int(h*0.40))], fill=TINTA+(255,), width=5)
    d.rectangle([int(w*0.10), int(h*0.40), int(w*0.90), int(h*0.46)], fill=(206, 193, 166, 255),
                outline=TINTA+(255,), width=4)
    for i in range(5):
        cx = int(w*0.18) + i*int(w*0.16)
        d.rectangle([cx-11, int(h*0.46), cx+11, base_y], fill=BLANCO+(255,),
                    outline=TINTA+(255,), width=4)
    d.line([(int(w*0.06), base_y), (int(w*0.94), base_y)], fill=TINTA+(255,), width=6)
    return p


PROPS = {
    'bandera_se':    bandera_se,
    'libro_quemado': libro_quemado,
    'camara_vivo':   camara_vivo,
    'cheque':        cheque,
    'pupitre':       pupitre,
    'mesa_cocina':   mesa_cocina,
    'casa_falu':     casa_falu,
    'krona':         krona,
    'riksdag':       riksdag,
}
SELLOS = {
    'sello_cut':     ('CUT OFF', ROJO),
    'sello_closed':  ('CLOSED 2025', TINTA),
    'sello_revoked': ('REVOKED', ROJO),
    'sello_unsolved':('NO CONVICTION', TINTA),
}


def main():
    hechos = []
    for n, fn in PROPS.items():
        p = fn(); p.save(os.path.join(OUT, 'prop_%s.png' % n)); hechos.append((n, p.size))
    for n, (txt, col) in SELLOS.items():
        p = sello(txt, color=col); p.save(os.path.join(OUT, 'prop_%s.png' % n)); hechos.append((n, p.size))
    for n, s in hechos:
        print('  %-16s %dx%d' % (n, s[0], s[1]))
    print('%d props, 0 creditos' % len(hechos))
    if '--hoja' in sys.argv:
        cols, cw, ch = 4, 380, 330
        filas = (len(hechos)+cols-1)//cols
        hoja = Image.new('RGB', (cols*cw, filas*ch), (26, 24, 22))
        for i, (n, _) in enumerate(hechos):
            im = Image.open(os.path.join(OUT, 'prop_%s.png' % n)).convert('RGBA')
            im.thumbnail((cw-40, ch-70))
            x = (i % cols)*cw + (cw-im.width)//2
            y = (i//cols)*ch + (ch-40-im.height)//2
            hoja.paste(im, (x, y), im)
            ImageDraw.Draw(hoja).text(((i % cols)*cw+cw//2, (i//cols)*ch+ch-26), n,
                                      fill=(220, 214, 200), anchor='mm', font=FONTC(20))
        hoja.save(os.path.join(AQUI, '..', '_hoja_props.jpg'), quality=90)
        print('hoja de contacto -> videos/S10_suecia/_hoja_props.jpg')


if __name__ == '__main__':
    main()
