"""Actores y recorridos exactos sobre Mundo, sin modificar el motor compartido.

La ruta, el trazo y los actores usan la misma distancia acumulada. Las posiciones
son puntos de Mundo.P, nunca fracciones de pantalla. Los tramos son rectos sobre
la proyeccion: la coreografia debe aportar los pasos intermedios de cada ruta.

    ruta = Ruta(mundo, ['Port', 'Strait', 'Destination'], 2, 8)
    trazar(sc, ruta, off=11)
    barcos = desplazar(sc, barco_png, ruta, 'convoy', modo='rumbo', off=11)
    encuadrar_ruta(sc, ruta, barcos, t=2)

El arte de vehiculos debe apuntar a la derecha; actor.rot permite corregirlo.
En modo marcha el pie queda sobre el sitio, con el personaje siempre erguido.
Los seguidores salen y llegan con el mismo retraso; al llegar quedan en destino.
"""

import bisect
import math

from PIL import Image, ImageDraw

if __package__:
    from . import motor as M
else:
    import motor as M


def _numero(valor, nombre, minimo=None):
    try:
        n = float(valor)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError('%s debe ser un numero finito' % nombre) from exc
    if not math.isfinite(n) or (minimo is not None and n < minimo):
        raise ValueError('%s debe ser finito y >= %s' % (nombre, minimo))
    return n


class Ruta:
    """Recorrido inmutable por distancia, con easing global y rumbo continuo.

    `lin` mantiene velocidad constante tambien entre tramos de distinto largo.
    `soft` acelera y frena una vez en todo el trayecto, no en cada waypoint.
    `heading` usa grados horarios y suaviza los giros sin modificar la posicion.
    """

    def __init__(self, mundo, nombres, t0, t1, easing='soft'):
        self.mundo = mundo
        self.t0 = _numero(t0, 't0')
        self.t1 = _numero(t1, 't1')
        if self.t1 <= self.t0 or not math.isfinite(self.t1 - self.t0):
            raise ValueError('La ruta necesita una duracion positiva y finita')
        if easing not in ('lin', 'soft', 'io', 'in', 'out'):
            raise ValueError('Easing de ruta no monotono o desconocido: %s' % easing)
        self.easing = easing
        if isinstance(nombres, str):
            raise ValueError('La ruta necesita una secuencia de nombres')
        self.nombres = tuple(nombres)
        if len(self.nombres) < 2:
            raise ValueError('La ruta necesita al menos dos puntos')
        puntos = []
        for nombre in self.nombres:
            try:
                x, y = mundo.P(nombre)
            except (KeyError, TypeError, IndexError) as exc:
                raise ValueError('Punto de mapa desconocido: %s' % nombre) from exc
            x, y = _numero(x, nombre), _numero(y, nombre)
            if not (0 <= x <= mundo.w and 0 <= y <= mundo.h):
                raise ValueError('Punto fuera del mundo: %s' % nombre)
            puntos.append((x, y))
        self.puntos = tuple(puntos)
        acumulada, rumbos = [0.0], []
        for a, b in zip(self.puntos, self.puntos[1:]):
            largo = math.dist(a, b)
            if largo <= 1e-9:
                raise ValueError('Una ruta no puede tener tramos de largo cero')
            acumulada.append(acumulada[-1] + largo)
            angulo = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
            if rumbos:
                angulo = rumbos[-1] + (angulo - rumbos[-1] + 180) % 360 - 180
            rumbos.append(angulo)
        self.acumulada = tuple(acumulada)
        self.longitud = acumulada[-1]
        self.rumbos = tuple(rumbos)

    def progreso(self, t):
        u = max(0.0, min(1.0, (_numero(t, 't') - self.t0) / (self.t1 - self.t0)))
        return M.EAS[self.easing](u)

    def _tramo(self, distancia):
        return min(len(self.puntos) - 2, bisect.bisect_right(self.acumulada, distancia) - 1)

    def pos(self, t):
        distancia = self.longitud * self.progreso(t)
        if distancia <= 0:
            return self.puntos[0]
        if distancia >= self.longitud:
            return self.puntos[-1]
        i = self._tramo(distancia)
        a, b = self.puntos[i:i + 2]
        u = (distancia - self.acumulada[i]) / (self.acumulada[i + 1] - self.acumulada[i])
        return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)

    def heading(self, t):
        distancia = self.longitud * self.progreso(t)
        for i in range(1, len(self.puntos) - 1):
            ancho = 0.15 * min(self.acumulada[i] - self.acumulada[i - 1],
                               self.acumulada[i + 1] - self.acumulada[i])
            delta = distancia - self.acumulada[i]
            if abs(delta) <= ancho:
                u = M.ease_io((delta + ancho) / (2 * ancho))
                return self.rumbos[i - 1] + (self.rumbos[i] - self.rumbos[i - 1]) * u
        return self.rumbos[self._tramo(distancia)]

    def puntos_hasta(self, t):
        """Vertices revelados y punta exacta; comparte progreso con pos(t)."""
        distancia = self.longitud * self.progreso(t)
        if distancia <= 0:
            return (self.puntos[0],)
        if distancia >= self.longitud:
            return self.puntos
        i = self._tramo(distancia)
        return self.puntos[:i + 1] + (self.pos(t),)


class ActorRuta(M.Obj):
    """Prop determinista: ni la camara ni la vida automatica alteran su geografia.

    `ancla(t)` es el punto geografico. `x(t), y(t)` son el centro del dibujo para
    compatibilidad con las auditorias; en marcha el centro queda sobre los pies.
    La ruta gobierna x/y: usar otra Ruta para cambiar el recorrido, no Obj.move.
    """

    def __init__(self, imagen, ruta, nombre, ancho, demora, modo, on, off):
        super().__init__(imagen, z=35, on=on, off=off)
        self.ruta = ruta
        self.demora = demora
        self.modo = modo
        self.name = nombre
        self.salida = ruta.t0 + demora
        self.llegada = ruta.t1 + demora
        self.sc = M.Track(ancho / self.img.width)
        self.depth = 1.0
        self.vida = 0.0
        self.geografico = True
        self.x = lambda t: self._geometria(t)[0][0]
        self.y = lambda t: self._geometria(t)[0][1]

    def ancla(self, t):
        return self.ruta.pos(t - self.demora)

    def _geometria(self, t):
        s, sy = self.sc(t), self.sy(t)
        if self.modo == 'marcha' and self.salida < t < self.llegada:
            u = self.ruta.progreso(t - self.demora)
            sy *= 1 + 0.016 * math.sin((t - self.salida) * math.tau * 3.5) * math.sin(math.pi * u)
        w = max(1, int(round(self.img.width * max(0.0, s))))
        h = max(1, int(round(self.img.height * max(0.0, s * sy))))
        x, y = self.ancla(t)
        r = self.rot(t)
        if self.modo == 'rumbo':
            r += self.ruta.heading(t - self.demora)
        elif self.modo == 'marcha':
            y -= h / 2
            r = 0.0
        return (x, y), (w, h), r

    def _visible(self, t):
        return self.on <= t < self.off and self.a(t) > 0.01 and self.sc(t) > 0.01 and self.sy(t) > 0.01

    def bbox(self, t):
        if not self._visible(t):
            return None
        (x, y), (w, h), r = self._geometria(t)
        a = math.radians(r)
        rw = abs(w * math.cos(a)) + abs(h * math.sin(a))
        rh = abs(w * math.sin(a)) + abs(h * math.cos(a))
        dx, dy = (int(4 + 14 * self.lift(t)), int(6 + 18 * self.lift(t))) if self.shadow else (0, 0)
        # PIL puede expandir un pixel extra al rotar; incluir sombra y redondeo.
        return (x - rw / 2 - 2 + min(0, dx), y - rh / 2 - 2 + min(0, dy),
                x + rw / 2 + 2 + max(0, dx), y + rh / 2 + 2 + max(0, dy))

    def draw(self, canvas, t, off=(0, 0)):
        if not self._visible(t):
            return
        (x, y), size, r = self._geometria(t)
        im = self.img.convert('RGBA')
        if im.size != size:
            im = im.resize(size, Image.Resampling.BILINEAR)
        if abs(r % 360) > 0.05:
            im = im.rotate(-r, resample=Image.Resampling.BICUBIC, expand=True)
        alpha = max(0.0, min(1.0, self.a(t)))
        if alpha < 0.995:
            im = im.copy()
            im.putalpha(im.getchannel('A').point(lambda p: int(p * alpha)))
        px, py = int(round(x - im.width / 2 + off[0])), int(round(y - im.height / 2 + off[1]))
        if self.shadow:
            lift = self.lift(t)
            sombra = Image.new('RGBA', im.size, (30, 24, 18, 0))
            sombra.putalpha(im.getchannel('A').point(lambda p: int(p * max(0, 0.32 - 0.12 * lift))))
            canvas.alpha_composite(sombra, (px + int(4 + 14 * lift), py + int(6 + 18 * lift)))
        canvas.alpha_composite(im, (px, py))

    def limites_recorrido(self):
        """Cota conservadora de todo el recorrido, incluidos giros y sombra."""
        escala = max(abs(k[1]) for k in self.sc.k)
        sy = max(abs(k[1]) for k in self.sy.k)
        if any(k[2] == 'back' for k in self.sc.k + self.sy.k):
            escala *= 1.12
        w, h = self.img.width * escala, self.img.height * escala * sy
        sombra = max(0.0, max(k[1] for k in self.lift.k)) if self.shadow else 0.0
        dx, dy = (4 + 14 * sombra, 6 + 18 * sombra) if self.shadow else (0, 0)
        if self.modo == 'marcha':
            izq, arriba, der, abajo = w / 2, h * 1.016, w / 2 + dx, dy
        else:
            radio = math.hypot(w, h) / 2
            izq, arriba, der, abajo = radio, radio, radio + dx, radio + dy
        xs, ys = zip(*self.ruta.puntos)
        return (min(xs) - izq - 3, min(ys) - arriba - 3,
                max(xs) + der + 3, max(ys) + abajo + 3)


def desplazar(sc, imagen, ruta, nombre, ancho=90, unidades=1, demora=0.35,
              modo='marcha', on=None, off=None):
    """Agrega unidades con salida escalonada y devuelve la lista de actores.

    ancho esta en px de mundo. off=None conserva los actores en destino.
    on=None hace aparecer cada unidad al salir; on explicito permite esperar.
    """
    if modo not in ('marcha', 'rumbo', 'fijo'):
        raise ValueError('Modo desconocido: %s' % modo)
    if isinstance(unidades, bool) or not isinstance(unidades, int) or unidades < 1:
        raise ValueError('unidades debe ser un entero positivo')
    ancho = _numero(ancho, 'ancho', 0.001)
    demora = _numero(demora, 'demora', 0)
    final = 1e9 if off is None else _numero(off, 'off')
    inicial = None if on is None else _numero(on, 'on')
    if final <= (ruta.t0 + (unidades - 1) * demora if inicial is None else inicial):
        raise ValueError('off debe ser posterior a la aparicion de las unidades')
    if sc.mundo is not ruta.mundo:
        raise ValueError('La ruta y la escena deben compartir el mismo Mundo')
    imagen = imagen if isinstance(imagen, Image.Image) else Image.open(imagen).convert('RGBA')
    actores = []
    for i in range(unidades):
        inicio = ruta.t0 + i * demora if inicial is None else inicial
        actor = ActorRuta(imagen, ruta, '%s:%d' % (nombre, i + 1), ancho,
                          i * demora, modo, inicio, final)
        sc.add(actor)
        actores.append(actor)
    return actores


class TrazoRuta:
    """Trazo y punta anclados al mismo progreso del primer actor."""

    def __init__(self, ruta, nombre, color, ancho, on, off):
        self.ruta, self.name, self.color, self.ancho = ruta, nombre, tuple(color), ancho
        self.on, self.off = on, off
        self.z, self.depth, self.bg = 25, 1.0, False
        self.transit, self.scene = [], None
        self.geografico = True

    def bbox(self, t):
        if not self.on <= t < self.off or self.ruta.progreso(t) <= 0:
            return None
        xs, ys = zip(*self.ruta.puntos_hasta(t))
        r = max(26, self.ancho * 3)
        return min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r

    def draw(self, canvas, t, off=(0, 0)):
        if self.bbox(t) is None:
            return
        puntos = [(x + off[0], y + off[1]) for x, y in self.ruta.puntos_hasta(t)]
        d = ImageDraw.Draw(canvas)
        color = self.color[:3] + ((self.color[3] if len(self.color) > 3 else 255),)
        d.line(puntos, fill=color, width=self.ancho, joint='curve')
        x, y = puntos[-1]
        ang = math.radians(self.ruta.heading(t))
        largo = self.ancho * 2.7
        d.polygon([(x, y),
                   (x - largo * math.cos(ang - 0.5), y - largo * math.sin(ang - 0.5)),
                   (x - largo * math.cos(ang + 0.5), y - largo * math.sin(ang + 0.5))], fill=color)
        if self.ruta.t1 <= t < self.ruta.t1 + 1.2:
            u = (t - self.ruta.t1) / 1.2
            r = 6 + 19 * u
            # Color atenuado, sin escribir pixeles semitransparentes en el lienzo opaco.
            pulso = tuple(int(c * (1 - u) + 238 * u) for c in color[:3]) + (255,)
            d.ellipse((x - r, y - r, x + r, y + r), outline=pulso, width=max(1, self.ancho // 2))


def trazar(sc, ruta, nombre='ruta', color=(188, 57, 46), ancho=6, on=None, off=None):
    """Agrega la trayectoria revelada; no usar Mundo.route en paralelo."""
    if sc.mundo is not ruta.mundo:
        raise ValueError('La ruta y la escena deben compartir el mismo Mundo')
    ancho = int(_numero(ancho, 'ancho', 1))
    inicio = ruta.t0 if on is None else _numero(on, 'on')
    final = 1e9 if off is None else _numero(off, 'off')
    if final <= inicio:
        raise ValueError('off debe ser posterior a on')
    return sc.add(TrazoRuta(ruta, nombre, color, ancho, inicio, final))


def encuadrar_ruta(sc, ruta, actores=(), margen=45, t=None):
    """Devuelve (centro, zoom) que contiene ruta y actores en cualquier formato.

    Con t aplica un corte. Reserva sitio para el push/deriva automaticos de v4.
    Si el mundo no permite ese encuadre, aborta: nunca corre sitios hacia tierra
    ni mueve soldados para esconder un recorte. Ampliar el mapa o separar planos.
    Recalcular despues de cambiar escala/lift de los actores.
    """
    if sc.mundo is not ruta.mundo:
        raise ValueError('La ruta y la escena deben compartir el mismo Mundo')
    margen = _numero(margen, 'margen', 0)
    xs, ys = zip(*ruta.puntos)
    cajas = [(min(xs) - 26, min(ys) - 26, max(xs) + 26, max(ys) + 26)]
    for actor in actores:
        if actor.ruta is not ruta:
            raise ValueError('El actor pertenece a otra ruta')
        cajas.append(actor.limites_recorrido())
    for capa in sc.layers:
        if isinstance(capa, TrazoRuta) and capa.ruta is ruta:
            r = max(26, capa.ancho * 3)
            cajas.append((min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r))
    x0 = min(b[0] for b in cajas) - margen
    y0 = min(b[1] for b in cajas) - margen
    x1 = max(b[2] for b in cajas) + margen
    y1 = max(b[3] for b in cajas) + margen
    if x0 < 0 or y0 < 0 or x1 > sc.WM or y1 > sc.HM:
        raise ValueError('La ruta y sus sprites necesitan mas margen dentro del mapa')
    vida = sc.vida if sc.v4 and sc.vida else {}
    push = 1 + max(0, vida.get('push_max', 0))
    deriva = abs(vida.get('deriva', 0))
    zoom = min((sc.W - 2 * deriva) / (x1 - x0),
               (sc.H - 0.64 * deriva) / (y1 - y0)) / push
    minimo = max(sc.W / sc.WM, sc.H / sc.HM)
    if zoom < minimo or zoom <= 0:
        raise ValueError('La ruta completa no cabe en este formato; ampliar mapa o dividir planos')
    centro = ((x0 + x1) / 2, (y0 + y1) / 2)
    if t is not None:
        sc.corte(_numero(t, 't'), centro, zoom)
    return centro, zoom


def auditar_geo(ruta, tolerancia=1.0, estricto=True):
    """Contrasta puntos con lon/lat originales de mapa_v2 cuando estan disponibles.

    No confirma transitabilidad terrestre/maritima: eso depende de los waypoints
    elegidos por la coreografia. Sin lon/lat informa sitios no verificados.
    """
    tolerancia = _numero(tolerancia, 'tolerancia', 0)
    meta = ruta.mundo.meta
    sitios = meta.get('sitios', {})
    errores, sin_datos, verificados = [], [], 0
    for nombre, punto in zip(ruta.nombres, ruta.puntos):
        if nombre not in sitios or 'bbox' not in meta:
            sin_datos.append(nombre)
            continue
        lon0, lon1, lat0, lat1 = meta['bbox']
        lon, lat = sitios[nombre]
        merc = lambda valor: math.log(math.tan(math.pi / 4 + math.radians(valor) / 2))
        esperado = ((lon - lon0) / (lon1 - lon0) * ruta.mundo.w,
                    (merc(lat1) - merc(lat)) / (merc(lat1) - merc(lat0)) * ruta.mundo.h)
        error = math.dist(punto, esperado)
        verificados += 1
        if error > tolerancia:
            errores.append({'nombre': nombre, 'error_px': error})
    if errores and estricto:
        raise ValueError('Geografia desalineada: %s' % errores)
    return {'verificados': verificados, 'sin_lonlat': sin_datos, 'errores': errores}
