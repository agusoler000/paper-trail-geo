# -*- coding: utf-8 -*-
"""Short vertical de THE LEDGER: 1080x1920, presentador arriba, ficha abajo.

    python videos/DAILY/corto.py --autotest
    python videos/DAILY/corto.py <dir_del_short>        # guion.json + voz.wav -> cuadros

POR QUE EXISTE
`canal/SHORTS.md` §2 dice que un short del modo A reusa **el arte** del episodio, no el metraje:
los rigs, las fichas y las texturas, con coreografia nueva y vertical. Eso es exactamente lo que
hace este modulo: importa `presentador/rig.py`, `presentador/bocas.py` y `fichas.py` de `escena.py`
y los recompone en vertical. No hay arte nuevo ni un credito gastado.

LO QUE CAMBIA RESPECTO DEL LARGO
  - 1080x1920 en vez de 1920x1080: el presentador arriba, la ficha abajo.
  - Cabecera con un sello de ESTADO (`UPDATED`, `CORRECTION`): un short de actualizacion tiene que
    decir en el primer cuadro que es una actualizacion, o parece el episodio repetido.
  - **Sin intro de canal; outro corta que pide la suscripcion** (`SHORTS.md` regla 8 de Agustin,
    que es la excepcion explicita a la regla 4).
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(BASE))
for p in (RAIZ, BASE, os.path.join(BASE, "presentador")):
    if p not in sys.path:
        sys.path.insert(0, p)

from PIL import Image, ImageDraw, ImageFont      # noqa: E402
import escena as ESC                             # noqa: E402  paleta, POSES, ROTULO, encuadre
import fichas as FI                              # noqa: E402

W, H, FPS = 1080, 1920, 24
HDR = 132                      # cabecera: marca + sello de estado
ALTO_PRES = 700                # panel del presentador
Y_FICHA = HDR + ALTO_PRES
ALTO_FICHA = H - Y_FICHA
ANCHO_BOCA = 120

PAPEL, PAPEL_IZQ = ESC.PAPEL, ESC.PAPEL_IZQ
TINTA, AZUL, GRIS = ESC.TINTA, ESC.AZUL, ESC.GRIS
ROJO = FI.ROJO


def _f(px, bold=False):
    for n in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(n, px)
        except Exception:
            pass
    return ImageFont.load_default()


class Corto:
    """Misma firma de guion que el largo: {"fecha","bloques":[{"presentador","beats":[...]}]}."""

    def __init__(self, guion, pista_visemas=None):
        self.guion = guion
        self.visemas = pista_visemas or []
        self.sello = guion.get("sello", "UPDATED")
        self.fecha = guion.get("fecha", "")
        self._cache_pose = {}
        self._cache_ficha = {}
        self._rig = None
        self._bocas = None
        self.beats = []
        for b in guion["bloques"]:
            pres = b.get("presentador", "A")
            for beat in b["beats"]:
                self.beats.append({**beat, "presentador": pres})
        self.beats.sort(key=lambda x: x["t"])
        self.dur = max((b["t"] + b["dur"] for b in self.beats), default=0.0)

    # ------------------------------------------------------------------ piezas
    def _mod_rig(self):
        if self._rig is None:
            import rig
            self._rig = rig
        return self._rig

    def _mod_bocas(self):
        if self._bocas is None:
            try:
                import bocas
                self._bocas = bocas
            except Exception:
                self._bocas = False
        return self._bocas

    def _doc(self, clave):
        with open(os.path.join(BASE, "presentador", "rig_%s.json" % clave), encoding="utf-8") as fh:
            return json.load(fh)

    def _panel_presentador(self, clave, pose, letra):
        """Igual que en el largo pero recortado al BUSTO: en vertical el panel es mas ancho que
           alto, asi que si entrara el cuerpo entero la cara quedaria diminuta."""
        ck = (clave, pose)
        g = self._cache_pose.get(ck)
        if g is None:
            rig = self._mod_rig()
            # el encuadre comun a las cinco poses lo calcula escena.py; se reusa tal cual para que
            # el presentador no cambie de tamano entre el largo y el short
            m, caja = ESC.Escena(self.guion)._encuadre(clave)
            cuerpo = rig.componer(clave, ESC.POSES.get(pose, {}), fondo=None, brads=True, margen=m)
            cuerpo = cuerpo.crop(caja)
            # busto: la mitad superior del dibujo, que es donde estan cara, hombros y manos altas
            cuerpo = cuerpo.crop((0, 0, cuerpo.width, int(cuerpo.height * 0.62)))
            esc = min(W / float(cuerpo.width), ALTO_PRES / float(cuerpo.height))
            cuerpo = cuerpo.resize((max(1, int(cuerpo.width * esc)),
                                    max(1, int(cuerpo.height * esc))), Image.LANCZOS)
            base = Image.new("RGB", (W, ALTO_PRES), PAPEL_IZQ)
            ox = (W - cuerpo.width) // 2
            oy = ALTO_PRES - cuerpo.height
            base.paste(cuerpo, (ox, oy), cuerpo)
            g = (base, ox + (m - caja[0]) * esc, oy + (m - caja[1]) * esc, esc)
            self._cache_pose[ck] = g
        base, ox, oy, esc = g
        bocas = self._mod_bocas()
        if not bocas or not letra:
            return base
        try:
            bx, by = self._doc(clave).get("boca") or [390, 296]
            b = bocas.dibujar_boca(letra, ancho=max(24, int(ANCHO_BOCA * esc)))
            pan = base.copy()
            pan.paste(b, (int(ox + bx * esc - b.width / 2.0),
                          int(oy + by * esc - b.height / 2.0)), b)
            return pan
        except Exception:
            return base

    def _panel_ficha(self, beat, dt):
        ck = (beat["ficha"], json.dumps(beat["datos"], sort_keys=True, default=str),
              round(min(dt, 1.2), 2))
        im = self._cache_ficha.get(ck)
        if im is None:
            im = FI.render_ficha(beat["ficha"], beat["datos"], size=(W, ALTO_FICHA), t=dt)
            if len(self._cache_ficha) > 6:
                self._cache_ficha.pop(next(iter(self._cache_ficha)))
            self._cache_ficha[ck] = im
        return im.copy()

    # ------------------------------------------------------------------ cuadro
    def _beat(self, t):
        act = None
        for b in self.beats:
            if b["t"] <= t:
                act = b
            else:
                break
        return act or (self.beats[0] if self.beats else None)

    def cuadro(self, t):
        im = Image.new("RGB", (W, H), PAPEL)
        d = ImageDraw.Draw(im)
        beat = self._beat(t)
        if beat is None:
            return im

        letra = ""
        if self.visemas:
            for tt, f in self.visemas:
                if tt <= t:
                    letra = f
                else:
                    break
            if letra == "X":
                letra = "X"

        im.paste(self._panel_presentador(beat["presentador"], beat.get("pose", "reposo"), letra),
                 (0, HDR))
        im.paste(self._panel_ficha(beat, t - beat["t"]), (0, Y_FICHA))
        d.line([(0, Y_FICHA - 2), (W, Y_FICHA - 2)], fill=(214, 203, 182), width=4)

        # cabecera
        d.rectangle([0, 0, W, HDR], fill=PAPEL)
        d.line([(0, HDR), (W, HDR)], fill=(196, 184, 162), width=3)
        d.text((46, 20), "PAPER TRAIL", font=_f(26, True), fill=AZUL)
        d.text((46, 50), "THE LEDGER", font=_f(44, True), fill=TINTA)

        # sello de estado: lo primero que tiene que leerse en un short de actualizacion
        s = self.sello
        fs = _f(30, True)
        anc = int(d.textlength(s, font=fs)) + 40
        sello = Image.new("RGBA", (anc, 56), (0, 0, 0, 0))
        ds = ImageDraw.Draw(sello)
        ds.rectangle([2, 2, anc - 3, 53], fill=ROJO + (255,))
        ds.text((20, 12), s, font=fs, fill=PAPEL + (255,))
        sello = sello.rotate(-1.6, resample=Image.BICUBIC, expand=False)
        im.paste(sello, (W - anc - 46, 38), sello)

        # rotulo del presentador, abajo del panel
        nombre, _ = ESC.ROTULO.get(beat["presentador"], ("", ""))
        anc = int(d.textlength(nombre, font=_f(30, True))) + 76
        d.rectangle([0, Y_FICHA - 66, anc, Y_FICHA - 6], fill=AZUL)
        d.text((40, Y_FICHA - 56), nombre, font=_f(30, True), fill=PAPEL)
        return im


def construir(guion, pista_visemas=None):
    return Corto(guion, pista_visemas)


def cargar(path):
    with open(path, encoding="utf-8") as fh:
        g = json.load(fh)
    for b in g["bloques"]:
        beats = sorted(b["beats"], key=lambda x: x["t"])
        for i in range(len(beats) - 1):
            if beats[i]["t"] + beats[i]["dur"] > beats[i + 1]["t"] + 0.05:
                raise ValueError("beats superpuestos: %.2f pisa a %.2f"
                                 % (beats[i]["t"] + beats[i]["dur"], beats[i + 1]["t"]))
        b["beats"] = beats
    return g


def autotest():
    ok = True

    def chk(c, txt):
        nonlocal ok
        print(("OK    " if c else "FALLA ") + txt)
        ok = ok and bool(c)

    g = {"fecha": "2026-09-14", "sello": "UPDATED", "bloques": [
        {"nombre": "COLD OPEN", "presentador": "A", "beats": [
            {"t": 0.0, "dur": 4.0, "texto": "x", "ficha": "dato", "pose": "senala",
             "datos": {"numero": "104.61", "unidad": "USD / bbl", "etiqueta": "Brent, Friday",
                       "contexto": "Up 8.7% on the week."}},
            {"t": 4.0, "dur": 4.0, "texto": "y", "ficha": "titular", "pose": "reposo",
             "datos": {"medio": "Reuters", "fecha": "14 September 2026",
                       "titular": "Gulf states meet in Muscat", "bajada": "...", "pie": ""}}]}]}
    c = construir(g, pista_visemas=[(0.0, "A"), (1.0, "D"), (2.0, "X")])
    chk(abs(c.dur - 8.0) < 0.01, "duracion total | dur=%.1f" % c.dur)
    im = c.cuadro(1.0)
    chk(im.size == (W, H), "cuadro vertical 1080x1920 | %s" % (im.size,))
    chk(len(im.getcolors(1 << 20) or []) > 500, "el cuadro no es una plancha de color")
    chk(c.cuadro(6.0).size == (W, H), "el segundo beat tambien compone")
    chk(c.cuadro(99.0).size == (W, H), "fuera de rango no explota")
    n = len(c._cache_pose)
    for i in range(10):
        c.cuadro(1.0 + i * 0.04)
    chk(len(c._cache_pose) == n, "10 cuadros del mismo beat no recomponen la pose")
    dest = os.path.join(BASE, "_corto_prueba.jpg")
    c.cuadro(1.2).save(dest, quality=92)
    print("      muestra en %s" % dest)
    print("\nFALLOS: %d" % (0 if ok else 1))
    return 0 if ok else 1


if __name__ == "__main__":
    if "--autotest" in sys.argv:
        sys.exit(autotest())
    print(__doc__)
