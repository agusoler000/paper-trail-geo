"""Pruebas de geografia, tiempo, render aleatorio y encuadre de rutas."""

import math
import unittest

from PIL import Image, ImageChops

if __package__:
    from . import acciones_mapa as A
else:
    import acciones_mapa as A

M = A.M


def mundo(puntos=None, size=(1000, 1000), meta=None):
    return M.Mundo(Image.new('RGB', size, (226, 237, 232)),
                   pts=puntos or {'A': (300, 450), 'B': (400, 450), 'C': (700, 450)},
                   meta=meta)


class RutaTest(unittest.TestCase):
    def test_extremos_y_velocidad_por_distancia(self):
        ruta = A.Ruta(mundo(), ['A', 'B', 'C'], 2, 10, 'lin')
        self.assertEqual(ruta.pos(-5), (300, 450))
        self.assertEqual(ruta.pos(4), (400, 450))
        self.assertEqual(ruta.pos(6), (500, 450))
        self.assertEqual(ruta.pos(10), (700, 450))
        self.assertEqual(ruta.pos(100), (700, 450))
        pasos = [math.dist(ruta.pos(t), ruta.pos(t + 1)) for t in range(2, 10)]
        self.assertTrue(all(abs(p - 50) < 1e-9 for p in pasos))

    def test_easing_global_no_frena_en_waypoint(self):
        ruta = A.Ruta(mundo(), ['A', 'B', 'C'], 0, 12)
        self.assertAlmostEqual(ruta.pos(6)[0], 500)
        self.assertLess(ruta.pos(1)[0] - ruta.pos(0)[0], ruta.pos(6)[0] - ruta.pos(5)[0])
        self.assertEqual(ruta.puntos_hasta(6)[-1], ruta.pos(6))
        self.assertEqual(ruta.puntos_hasta(12), ruta.puntos)

    def test_errores_no_se_ocultan(self):
        casos = [(['A'], 0, 1, 'lin'), (['A', 'X'], 0, 1, 'lin'),
                 (['A', 'A'], 0, 1, 'lin'), (['A', 'B'], 1, 1, 'lin'),
                 (['A', 'B'], 2, 1, 'lin'), (['A', 'B'], 0, math.inf, 'lin'),
                 (['A', 'B'], math.nan, 1, 'lin'), (['A', 'B'], 0, 1, 'back'),
                 (['A', 'B'], -1e308, 1e308, 'lin')]
        for nombres, t0, t1, easing in casos:
            with self.subTest(nombres=nombres, t0=t0, t1=t1, easing=easing):
                with self.assertRaises(ValueError):
                    A.Ruta(mundo(), nombres, t0, t1, easing)
        for punto in ((math.nan, 1), (-1, 100), (100, 1001)):
            with self.assertRaises(ValueError):
                A.Ruta(mundo({'A': (500, 500), 'B': punto}), ['A', 'B'], 0, 1)

    def test_rumbo_cruza_180_por_arco_corto(self):
        radio = 150
        a = (700, 400)
        b = (a[0] + radio * math.cos(math.radians(170)), a[1] + radio * math.sin(math.radians(170)))
        c = (b[0] + radio * math.cos(math.radians(-170)), b[1] + radio * math.sin(math.radians(-170)))
        ruta = A.Ruta(mundo(dict(A=a, B=b, C=c)), ['A', 'B', 'C'], 0, 10, 'lin')
        self.assertAlmostEqual(ruta.heading(0), 170)
        self.assertAlmostEqual(ruta.heading(5), 180)
        self.assertAlmostEqual(ruta.heading(10), 190)
        rumbos = [ruta.heading(i / 100) for i in range(1001)]
        self.assertLess(max(abs(b - a) for a, b in zip(rumbos, rumbos[1:])), 1)

    def test_geo_audita_original_y_reporta_ausentes(self):
        meta = {'bbox': [-10, 10, -10, 10], 'sitios': {'A': (-4, 0), 'B': (4, 0)}}
        mu = mundo({'A': (300, 500), 'B': (700, 500)}, meta=meta)
        ruta = A.Ruta(mu, ['A', 'B'], 0, 1)
        self.assertEqual(A.auditar_geo(ruta)['verificados'], 2)
        mu.pts['B'] = (710, 500)
        mala = A.Ruta(mu, ['A', 'B'], 0, 1)
        with self.assertRaises(ValueError):
            A.auditar_geo(mala)
        sin = A.Ruta(mundo(), ['A', 'B'], 0, 1)
        self.assertEqual(A.auditar_geo(sin)['sin_lonlat'], ['A', 'B'])


class ActoresTest(unittest.TestCase):
    def escena(self, formato=(320, 180), modo='marcha'):
        mu = mundo({'A': (350, 460), 'B': (430, 420), 'C': (620, 500)})
        sc = M.Scene(mu, size=formato, v4=True)
        ruta = A.Ruta(mu, ['A', 'B', 'C'], 1, 5)
        sprite = Image.new('RGBA', (24, 40), (225, 39, 32, 255))
        actores = A.desplazar(sc, sprite, ruta, 'unidad', ancho=32, unidades=3, demora=0.4, modo=modo)
        return sc, ruta, actores

    def test_retraso_ancla_y_llegada_persistente(self):
        sc, ruta, actores = self.escena()
        for i, actor in enumerate(actores):
            self.assertEqual(actor.ancla(1 + i * 0.4), ruta.puntos[0])
            self.assertEqual(actor.ancla(5 + i * 0.4), ruta.puntos[-1])
            self.assertEqual(actor.ancla(500), ruta.puntos[-1])
            self.assertEqual(actor.bbox(500), actor.bbox(50))
            self.assertEqual(sc.offset(actor, 3), (0, 0))
            self.assertEqual(actor.depth, 1)
            self.assertEqual(actor._geometria(3)[2], 0)
            self.assertAlmostEqual(actor.y(3) + actor._geometria(3)[1][1] / 2, actor.ancla(3)[1])
        self.assertIsNone(actores[2].bbox(1.7))

    def test_rumbo_y_bbox_en_cuadrantes(self):
        sc, ruta, actores = self.escena(modo='rumbo')
        actor = actores[0]
        actor.rot = M.Track(180)
        for t in (1, 2, 3, 4, 5, 8):
            b = actor.bbox(t)
            self.assertGreater(b[2] - b[0], 20)
            self.assertGreater(b[3] - b[1], 20)
            self.assertAlmostEqual(actor._geometria(t)[2], 180 + ruta.heading(t))

    def test_render_en_desorden_no_muta_estado(self):
        sc, ruta, actores = self.escena()
        trazo = A.trazar(sc, ruta)
        A.encuadrar_ruta(sc, ruta, actores, margen=12, t=0)
        estado = [(list(o.sc.k), list(o.a.k), list(o.rot.k)) for o in actores]
        eventos = list(M.EVENTS)
        primero = sc.render(3)
        for t in (8, 1, 4, 2, 0, 7):
            sc.render(t)
        self.assertIsNone(ImageChops.difference(primero.convert('RGB'), sc.render(3).convert('RGB')).getbbox())
        self.assertEqual(estado, [(o.sc.k, o.a.k, o.rot.k) for o in actores])
        self.assertEqual(eventos, M.EVENTS)
        self.assertEqual(trazo.ruta.puntos_hasta(3)[-1], actores[0].ancla(3))

    def test_bbox_contiene_pixeles_y_sombra_reales(self):
        for modo in ('marcha', 'rumbo', 'fijo'):
            sc, ruta, actores = self.escena(modo=modo)
            actor = actores[0]
            actor.rot = M.Track(192)
            for t in (1, 2.125, 3.33, 4.6, 5, 50):
                lienzo = Image.new('RGBA', (sc.WM, sc.HM))
                actor.draw(lienzo, t)
                real = lienzo.getbbox()
                b = actor.bbox(t)
                self.assertGreaterEqual(real[0], b[0])
                self.assertGreaterEqual(real[1], b[1])
                self.assertLessEqual(real[2], b[2])
                self.assertLessEqual(real[3], b[3])

    def test_encuadre_horizontal_y_vertical_con_vida(self):
        for formato in ((320, 180), (180, 320)):
            for modo in ('marcha', 'rumbo', 'fijo'):
                with self.subTest(formato=formato, modo=modo):
                    sc, ruta, actores = self.escena(formato, modo)
                    A.trazar(sc, ruta)
                    A.encuadrar_ruta(sc, ruta, actores, margen=10, t=0)
                    for t in [i / 4 for i in range(41)] + [1000]:
                        ventana = sc.window(t)
                        for actor in sc.layers:
                            b = actor.bbox(t)
                            if b is None:
                                continue
                            self.assertGreaterEqual(b[0], ventana[0])
                            self.assertGreaterEqual(b[1], ventana[1])
                            self.assertLessEqual(b[2], ventana[2])
                            self.assertLessEqual(b[3], ventana[3])
                    self.assertEqual(sc.check_framing(1, 10, step=0.13, tol=0), [])
                    self.assertEqual(sc.render(3).size, formato)

    def test_encuadre_imposible_falla_sin_mover_geografia(self):
        mu = mundo({'A': (100, 500), 'B': (900, 500)})
        sc = M.Scene(mu, size=(180, 320), v4=True)
        ruta = A.Ruta(mu, ['A', 'B'], 0, 4)
        with self.assertRaises(ValueError):
            A.encuadrar_ruta(sc, ruta, margen=0)
        self.assertEqual(ruta.pos(4), (900, 500))
        self.assertEqual(mu.P('B'), (900, 500))


if __name__ == '__main__':
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from radar.entorno import cargar

    cargar()
    unittest.main()
