# -*- coding: utf-8 -*-
"""Props de papel de la serie S12 («THE RECEIPT», tanda del 2026-09-15). 0 creditos: todo por codigo.

    cd videos/S12_recibos/arte && python props_s12.py [--hoja]

Regla 19 (reusar antes de generar). **Del indice se reusan TAL CUAL**, sin redibujar:
`bandera_us`, `bandera_uk`, `bandera_es`, `barril`, `deposito_oil`, `torre_petroleo`, `cerca`,
`barrera`, `resolucion`, `poliza`, `flecha_arriba`, `grafico_caida`, `lingote`, `moneda`, `cheque`
y toda la familia `sello_*`.

Aca se dibuja **solo lo que no existia**:

  - `bandera_ir`  — Iran. Sin el emblema central: a 300 px de ancho el emblema es una mancha, y una
                    mancha mal dibujada sobre una bandera nacional es peor que no ponerla. Tres
                    franjas y la etiqueta, igual que el resto de la familia.
  - `hotel`       — el objeto de la pieza 3. Un bloque con ventanas, no un hotel de lujo: lo que
                    dice el recibo es «alojamiento», no «vacaciones».
  - `petrolero`   — silueta de buque cisterna para la pieza 2.
  - `sello_same`  — SAME CONTRACT, para caer sobre la torre que crece.

Y **las secuencias de animacion**, que son lo nuevo de esta tanda (pedido de Agustin del 15-sep:
*«meterle alguna animacion en el medio»*). No hay motor de animacion nuevo: se generan N cuadros de
un mismo objeto y la coreografia los enciende en orden con `on`/`off`. Es determinista, no toca
`produccion/motor.py` —que hoy esta renderizando el ep. 09 y no se puede tocar— y se puede mirar
cuadro a cuadro antes de renderizar nada.

  - `tanque_nNN`      13 cuadros · el deposito de crudo vaciandose de 100 % a 39 %  (pieza 1)
  - `barra_dNN`       13 cuadros · barra de DINERO creciendo hasta el 76 %          (pieza 3)
  - `barra_gNN`       13 cuadros · barra de GENTE creciendo hasta el 35 %           (pieza 3)
  - `torre_nNN`       13 cuadros · la pila de libras de 4,5bn a 15,3bn              (pieza 3)

Dibujadas para verse a media pantalla (leccion 4 del S03): ningun trazo por debajo de ~10 px sobre
el ancho nominal.
"""
import os, sys
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', '..', '..', 'produccion'))
from PIL import Image, ImageDraw
from props import (papel, texto, card, sello, rect, FONT, FONTC,
                   TINTA, PAPEL, OCRE, AZUL, ROJO, MAPA)

BLANCO = (245, 241, 230)
GRIS = (120, 115, 105)
CRUDO = (46, 40, 34)            # el crudo: casi negro, pero no negro puro
CRUDO_L = (72, 62, 50)          # la lamina de arriba, para que se lea el nivel
VERDE_IR = (35, 159, 64)
ROJO_IR = (218, 0, 0)

OUT = os.path.join(AQUI, 'assets'); os.makedirs(OUT, exist_ok=True)
PASOS = 13                      # cuadros por secuencia


# ------------------------------------------------------------------ banderas
def _bandera(w, h, pintar, etiqueta):
    """Molde del S05/S10: la ficha ENTERA es de papel, etiqueta incluida."""
    H = h + 58
    def f(d): d.rounded_rectangle([1, 1, w-2, H-2], radius=10, fill=255)
    p = papel((w, H), f, PAPEL); d = ImageDraw.Draw(p)
    d.rectangle([10, 12, w-11, h-6], fill=BLANCO+(255,))
    pintar(d)
    d.rectangle([10, 12, w-11, h-6], outline=TINTA+(255,), width=3)
    texto(p, etiqueta, int(w*0.115), (w/2, h+22), color=TINTA, font=FONTC)
    return p


def bandera_ir(w=300, h=188):
    """Iran: verde, blanco y rojo en franjas horizontales iguales.

    **Sin el emblema ni la escritura del borde.** A este tamano el emblema es una mancha de 20 px, y
    una mancha mal dibujada sobre una bandera nacional se lee como desprecio, no como sintesis. La
    etiqueta dice de que pais es, que es para lo que esta el prop.
    """
    def pintar(d):
        x0, y0, x1, y1 = 10, 12, w-11, h-6
        t = (y1-y0)/3.0
        d.rectangle([x0, y0,       x1, y0+t],   fill=VERDE_IR+(255,))
        d.rectangle([x0, y0+t,     x1, y0+2*t], fill=BLANCO+(255,))
        d.rectangle([x0, y0+2*t,   x1, y1],     fill=ROJO_IR+(255,))
    return _bandera(w, h, pintar, 'IRAN')


# ------------------------------------------------------------------ objetos
def hotel(w=260):
    """Bloque de alojamiento: seis plantas, ventanas en rejilla, marquesina y cartel HOTEL.

    Deliberadamente sobrio. La pieza 3 habla de una factura de alojamiento; un hotel con palmeras
    seria un chiste visual sobre las personas alojadas, que es justo lo que la pieza no hace.
    """
    h = int(w*1.15)
    def f(d):
        d.rectangle([0, h*0.16, w, h], fill=255)          # cuerpo
        d.rectangle([w*0.06, h*0.10, w*0.94, h*0.17], fill=255)   # cornisa
        d.rectangle([w*0.22, h*0.90, w*0.78, h], fill=255)        # marquesina
    p = papel((w+2, h+2), f, PAPEL); d = ImageDraw.Draw(p)
    d.rectangle([0, h*0.16, w, h], outline=TINTA+(255,), width=4)
    filas, cols = 5, 4
    mx, my = w*0.10, h*0.24
    aw = (w - 2*mx - (cols-1)*w*0.045) / cols
    ah = (h*0.62 - (filas-1)*h*0.035) / filas
    for r in range(filas):
        for c in range(cols):
            x = mx + c*(aw + w*0.045); y = my + r*(ah + h*0.035)
            col = AZUL if (r + c) % 3 else GRIS
            d.rectangle([x, y, x+aw, y+ah], fill=col+(255,), outline=TINTA+(255,), width=3)
    d.rectangle([w*0.42, h*0.90, w*0.58, h], fill=TINTA+(255,))    # puerta
    d.rectangle([w*0.19, h*0.085, w*0.81, h*0.175], fill=TINTA+(255,))
    texto(p, 'HOTEL', int(w*0.15), (w/2, h*0.132), color=PAPEL, font=FONTC)
    return p


def petrolero(w=420):
    """Buque cisterna de perfil: casco largo, castillo a popa, cuatro domos de carga en cubierta."""
    h = int(w*0.40)
    def f(d):
        d.polygon([(0, h*0.52), (w, h*0.52), (w*0.95, h*0.86), (w*0.07, h*0.86)], fill=255)  # casco
        d.rectangle([w*0.74, h*0.24, w*0.93, h*0.52], fill=255)                              # castillo
        d.rectangle([w*0.80, h*0.06, w*0.85, h*0.24], fill=255)                              # chimenea
    p = papel((w+2, h+2), f, PAPEL); d = ImageDraw.Draw(p)
    d.polygon([(0, h*0.52), (w, h*0.52), (w*0.95, h*0.86), (w*0.07, h*0.86)],
              outline=TINTA+(255,), width=4)
    for i in range(4):                                     # domos de carga
        cx = w*(0.13 + i*0.145)
        d.ellipse([cx-w*0.042, h*0.40, cx+w*0.042, h*0.56], fill=OCRE+(255,),
                  outline=TINTA+(255,), width=3)
    d.rectangle([w*0.74, h*0.24, w*0.93, h*0.52], outline=TINTA+(255,), width=3)
    for i in range(3):                                     # ojos de buey del castillo
        d.rectangle([w*(0.765+i*0.05), h*0.31, w*(0.795+i*0.05), h*0.38],
                    fill=BLANCO+(255,), outline=TINTA+(255,), width=2)
    d.line([(w*0.07, h*0.86), (w*0.95, h*0.86)], fill=TINTA+(255,), width=4)
    return p


def sentencia(w=420):
    """El fallo del Tribunal Supremo del 29-jun-2026: el papel de la pieza 4.

    Se dibuja en vez de reusar `resolucion` (produccion/assets) porque ese prop lleva impreso
    **UNITED NATIONS 2065**: es la resolucion de otro episodio y en la miniatura se leia entera.
    Un prop que dice literalmente otra cosa no es reuso, es un error de continuidad.

    Dice TRIBUNAL SUPREMO y la fecha en numeros romanos porque asi es como se lee en un cabecero
    espanol, y porque la fecha ES el dato: los 32 dias se cuentan desde ahi.
    """
    h = int(w*1.30)
    def f(d): d.rounded_rectangle([1, 1, w-2, h-2], radius=8, fill=255)
    p = papel((w, h), f, BLANCO); d = ImageDraw.Draw(p)
    d.rounded_rectangle([10, 10, w-11, h-11], radius=6, outline=TINTA+(255,), width=4)
    texto(p, 'TRIBUNAL', int(w*0.125), (w/2, h*0.115), color=TINTA, font=FONTC)
    texto(p, 'SUPREMO', int(w*0.125), (w/2, h*0.195), color=TINTA, font=FONTC)
    d.line([(w*0.14, h*0.255), (w*0.86, h*0.255)], fill=TINTA+(255,), width=5)
    texto(p, '29 · VI · 2026', int(w*0.115), (w/2, h*0.335), color=ROJO, font=FONTC)
    for i, y in enumerate(range(int(h*0.43), int(h*0.80), int(h*0.062))):
        d.line([(w*0.13, y), (w*0.87 - (i % 3)*w*0.16, y)], fill=(150, 145, 130, 255), width=5)
    d.rounded_rectangle([w*0.58, h*0.845, w*0.90, h*0.945], radius=6,
                        outline=ROJO+(255,), width=5)
    texto(p, 'FIRME', int(w*0.072), (w*0.74, h*0.895), color=ROJO, font=FONTC)
    return p


def sello_same():
    return sello('SAME' + chr(10) + 'CONTRACT', color=ROJO, size=44)


# ------------------------------------------------------------------ secuencias
def _tanque(pct, w=300):
    """Deposito de almacenamiento visto de frente, con el crudo a `pct` de altura.

    Dos correcciones sobre la primera version, que en la hoja de contacto no se leia:
      1. **Mas alto que ancho** (1,45 en vez de 1,06). Un deposito cuadrado con el crudo al 60 %
         parece lleno; uno alto muestra el hueco, que es el dato de la pieza.
      2. **Linea roja de nivel + regla graduada a la derecha con el 100 y el 39 marcados.** El ojo
         necesita una referencia fija contra la que ver bajar el liquido; sin ella, trece cuadros
         de un bloque oscuro parecen el mismo cuadro.
    """
    h = int(w*1.45)
    LW = int(w*1.34)            # lienzo: cilindro + regla + numeros. Sin esto la regla sangra.
    cw = w*0.88
    def f(d):
        d.rounded_rectangle([0, h*0.08, cw, h], radius=12, fill=255)
        d.ellipse([0, h*0.02, cw, h*0.14], fill=255)                   # tapa
    p = papel((LW, h+2), f, PAPEL); d = ImageDraw.Draw(p)
    y0, y1 = h*0.14, h*0.965                                            # interior util
    lleno = (y1-y0) * max(0.0, min(1.0, pct/100.0))
    yt = y1 - lleno
    if lleno > 6:
        d.rounded_rectangle([cw*0.055, yt, cw*0.945, y1], radius=9, fill=CRUDO+(255,))
        d.rectangle([cw*0.055, yt, cw*0.945, yt + min(14, lleno*0.35)], fill=CRUDO_L+(255,))
        d.line([(cw*0.055, yt), (cw*0.945, yt)], fill=ROJO+(255,), width=5)   # el nivel, en rojo
    d.rounded_rectangle([0, h*0.08, cw, h], radius=12, outline=TINTA+(255,), width=5)
    d.ellipse([0, h*0.02, cw, h*0.14], outline=TINTA+(255,), width=5)
    for i in range(1, 6):                                               # aros del deposito
        y = h*0.08 + (h*0.92)*i/6.0
        d.line([(cw*0.02, y), (cw*0.98, y)], fill=TINTA+(110,), width=3)
    # regla graduada a la derecha: la referencia fija contra la que se ve bajar el nivel
    rx = cw + 6
    d.line([(rx, y0), (rx, y1)], fill=TINTA+(255,), width=4)
    for m, etq in ((100, '100'), (75, None), (50, None), (39, '39'), (25, None), (0, '0')):
        y = y1 - (y1-y0)*m/100.0
        largo = w*0.10 if etq else w*0.05
        col = ROJO if etq == '39' else TINTA
        d.line([(rx, y), (rx+largo, y)], fill=col+(255,), width=4)
        if etq:
            texto(p, etq, 26, (rx+largo+2, y), color=col, font=FONTC, anchor='lm')
    return p


def _barra(pct, color, etiqueta, w=620):
    """Barra horizontal de papel. `pct` es cuanto del ancho util esta pintado.

    **La etiqueta va centrada en la barra ENTERA y en tinta, no dentro del relleno.** En la primera
    version iba centrada en la parte pintada y con la barra corta se salia del papel: en los cuadros
    00-05 se leia «NEY», «ONEY 7», «OPLE 35». Eso es la regla 1 incumplida en el propio prop, antes
    de que la coreografia lo coloque en ninguna parte.
    """
    h = 118
    def f(d): d.rounded_rectangle([1, 1, w-2, h-2], radius=10, fill=255)
    p = papel((w, h), f, PAPEL); d = ImageDraw.Draw(p)
    x0, x1 = 16, w-16
    largo = (x1-x0) * max(0.0, min(1.0, pct/100.0))
    if largo > 4:
        d.rounded_rectangle([x0, 16, x0+largo, h-16], radius=8, fill=color+(255,))
    d.rounded_rectangle([x0, 16, x1, h-16], radius=8, outline=TINTA+(255,), width=4)
    texto(p, etiqueta, 46, ((x0+x1)/2, h/2), color=TINTA, font=FONTC)
    return p


def _torre(pct, w=250):
    """Pila de fajos de billetes. `pct` 0 -> 4 fajos (4,5bn); 100 -> 14 fajos (15,3bn)."""
    n = int(round(4 + 10*max(0.0, min(1.0, pct/100.0))))
    fh, gap = 26, 5
    h = 14*(fh+gap) + 20
    def f(d):
        for i in range(n):
            y = h - 16 - (i+1)*(fh+gap)
            d.rounded_rectangle([18, y, w-18, y+fh], radius=5, fill=255)
    p = papel((w+2, h+2), f, PAPEL); d = ImageDraw.Draw(p)
    for i in range(n):
        y = h - 16 - (i+1)*(fh+gap)
        d.rounded_rectangle([18, y, w-18, y+fh], radius=5,
                            fill=(OCRE if i % 2 else PAPEL)+(255,), outline=TINTA+(255,), width=3)
        d.line([(w*0.42, y+fh/2), (w*0.58, y+fh/2)], fill=TINTA+(200,), width=3)
    return p


# ------------------------------------------------------------------ main

# ---------------------------------------------------------------- documentos CON NOMBRE
# REGLA 14 DEL CANAL, aplicada a los props: ningun prop con texto horneado entra si su texto no
# esta en el guion o en `fuentes/referencia.md`. La tanda de prueba entro con dos que lo rompian y
# se colaron hasta el master:
#   · `contrato99` decia «LEASE / 99 YEARS» mientras la voz decia «Same contracts. Same TEN years»
#     (F3.5: los contratos son 2019-2029, diez anos). Un dato inventado en pantalla.
#   · `resolucion` decia «UNITED NATIONS / 2065», que no aparece en ningun guion de esta serie.
# Y tres mas eran sellos genericos sin nombre («REPORT», «DECREE», «POLICY»): un documento sin
# nombre no cuenta nada, el espectador no sabe que esta mirando.
#
# Cada linea de aqui abajo sale de la hoja de fuentes, con su F al lado.
DOCS = {
 # pieza 1
 'doc_eia':      ('U.S. ENERGY INFORMATION ADMINISTRATION',
                  ['WEEKLY PETROLEUM STATUS REPORT',
                   'STRATEGIC PETROLEUM RESERVE',
                   'WEEK OF SEPTEMBER 4, 2026'], 'F1.1'),
 'doc_doe':      ('U.S. DEPARTMENT OF ENERGY',
                  ['NOTICE OF SALE',
                   '11 MARCH 2026',
                   '172,000,000 BARRELS'], 'F1.6'),
 # pieza 2
 'doc_poliza':   ('WAR-RISK INSURANCE',
                  ['HORMUZ TRANSIT',
                   'PREMIUM: 7.5% - 10% OF HULL',
                   'PER VOYAGE'], 'F2.3'),
 # pieza 3
 'doc_contrato': ('ASYLUM ACCOMMODATION CONTRACTS',
                  ['SIGNED 2019  ·  TERM 2019-2029',
                   'TEN YEARS',
                   'COSTED AT £4.5 BILLION'], 'F3.5'),
 'doc_cuentas':  ('HOME OFFICE',
                  ['ANNUAL REPORT AND ACCOUNTS',
                   'ASYLUM SUPPORT AND ACCOMMODATION',
                   'YEAR TO MARCH 2026'], 'F3.1 / F3.3'),
}


def documento(titulo, lineas, w=520):
    """Un documento de papel CON NOMBRE: cabecera, regla y dos o tres lineas de contenido.

    Se lee a 405 px porque el titulo va grande y en dos renglones si hace falta; el cuerpo son
    lineas cortas, no parrafos: en un short nadie lee un parrafo."""
    h = int(w * 1.34)
    q = papel((w, h), lambda d: d.rounded_rectangle([1, 1, w-2, h-2], radius=int(w*0.035), fill=255),
              BLANCO)
    d = ImageDraw.Draw(q)
    d.rounded_rectangle([int(w*0.045), int(h*0.035), w-int(w*0.045), h-int(h*0.035)],
                        radius=int(w*0.022), outline=TINTA+(70,), width=3)
    # cabecera
    y = int(h*0.105)
    f = FONTC(int(w*0.062))
    pal = titulo.split(); ren = []; cur = ''
    for t in pal:
        pr = (cur + ' ' + t).strip()
        if d.textlength(pr, font=f) > w*0.84 and cur: ren.append(cur); cur = t
        else: cur = pr
    ren.append(cur)
    for r in ren:
        d.text((w/2, y), r, fill=TINTA+(255,), font=f, anchor='ma'); y += int(w*0.072)
    y += int(h*0.012)
    d.line([(int(w*0.10), y), (int(w*0.90), y)], fill=TINTA+(190,), width=4); y += int(h*0.045)
    # cuerpo
    f2 = FONTC(int(w*0.049))
    for i, L in enumerate(lineas):
        col = ROJO if i == len(lineas)-1 else TINTA
        ff = f2
        while d.textlength(L, font=ff) > w*0.84 and ff.size > 14: ff = FONTC(ff.size-2)
        d.text((w/2, y), L, fill=col+(255,), font=ff, anchor='ma'); y += int(w*0.070)
    # renglones de relleno, para que parezca un documento y no una tarjeta
    yy = y + int(h*0.02)
    while yy < h - int(h*0.10):
        d.line([(int(w*0.14), yy), (int(w*(0.86 - 0.12*((yy//7) % 3)))), yy],
               fill=TINTA+(55,), width=3)
        yy += int(h*0.045)
    return q


def guardar(im, nombre):
    im.save(os.path.join(OUT, 'prop_%s.png' % nombre))
    return nombre


def main():
    hechos = []
    hechos.append(guardar(bandera_ir(), 'bandera_ir'))
    hechos.append(guardar(hotel(), 'hotel'))
    hechos.append(guardar(petrolero(), 'petrolero'))
    hechos.append(guardar(sello_same(), 'sello_same'))
    hechos.append(guardar(sentencia(), 'sentencia'))

    # secuencias: N cuadros que la coreografia enciende en orden
    for i in range(PASOS):
        k = i/(PASOS-1.0)
        hechos.append(guardar(_tanque(100 - 61*k),                      'tanque_n%02d' % i))
        hechos.append(guardar(_barra(76*k, OCRE,  'MONEY'),        'barra_d%02d' % i))
        hechos.append(guardar(_barra(35*k, AZUL,  'PEOPLE'),       'barra_g%02d' % i))
        hechos.append(guardar(_torre(100*k),                            'torre_n%02d' % i))

    for nom, (tit, lin, fte) in DOCS.items():
        hechos.append(guardar(documento(tit, lin), nom))
        print('   %-14s %s   [%s]' % (nom, tit, fte))

    print('%d props en %s' % (len(hechos), OUT))
    if '--hoja' in sys.argv:
        base = [n for n in hechos if not n[-3:-2].isdigit()] + \
               ['tanque_n00', 'tanque_n06', 'tanque_n12', 'barra_d12', 'barra_g12',
                'torre_n00', 'torre_n12']
        ims = [Image.open(os.path.join(OUT, 'prop_%s.png' % n)).convert('RGBA') for n in base]
        cols = 4; fil = (len(ims)+cols-1)//cols
        cw = max(i.width for i in ims)+30; ch = max(i.height for i in ims)+30
        hoja = Image.new('RGBA', (cols*cw, fil*ch), (24, 22, 20, 255))
        for i, im in enumerate(ims):
            hoja.alpha_composite(im, ((i % cols)*cw + (cw-im.width)//2,
                                      (i//cols)*ch + (ch-im.height)//2))
        f = os.path.join(OUT, '_hoja_props.png'); hoja.convert('RGB').save(f, quality=92)
        print('hoja ->', f)


if __name__ == '__main__':
    main()
