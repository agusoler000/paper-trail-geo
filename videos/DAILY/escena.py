# -*- coding: utf-8 -*-
"""Escena del formato diario: de un guion en JSON a cuadros de 1920x1080.

    python videos/DAILY/escena.py --autotest
    python videos/DAILY/escena.py --muestra guion.json 12.5    # un cuadro suelto a los 12,5 s

Compone los dos paneles: presentador a la izquierda (rig + lip-sync), ficha a la derecha.
El lenguaje visual es el del cuadro aprobado el 2026-09-11 (videos/DAILY/_layout.jpg).

POR QUE ESTO PUEDE CORRER EN 6 vCPU
El panel izquierdo NO se redibuja cuadro a cuadro. El cuerpo del presentador solo cambia cuando
cambia la pose (unas pocas veces por beat), asi que se cachea la pose compuesta y por cuadro solo
se pega la boca encima. De 28.800 composiciones completas se pasa a unas 200, y el resto es un
alpha_composite de 120x60 px. Es la diferencia entre 4 horas de render y muchas mas.
"""
import json
import os
import sys
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(BASE))
for p in (RAIZ, BASE, os.path.join(BASE, "presentador")):
    if p not in sys.path:
        sys.path.insert(0, p)

from PIL import Image, ImageDraw, ImageFont       # noqa: E402

W, H, FPS = 1920, 1080, 24
CREASE = 952
HDR = 96
ANCHO_BOCA = 120      # ancho de la boca en coordenadas del rig (768x1024)

PAPEL = (233, 223, 203)
PAPEL_IZQ = (240, 232, 214)
TINTA = (34, 32, 28)
AZUL = (43, 76, 111)
GRIS = (140, 130, 114)

# Pose de reposo y las pocas poses nombradas que el guion puede pedir.
# Signo medido con el barrido del 2026-09-11: en el brazo derecho positivo abre, negativo cierra;
# en el izquierdo al reves.
POSES = {
    "reposo":   {},
    "senala":   {"brazo_d": 36, "antebrazo_d": 14, "cabeza": -3},
    "abre":     {"brazo_i": -20, "brazo_d": 20, "antebrazo_i": -10, "antebrazo_d": 10},
    "enfatiza": {"brazo_i": 24, "antebrazo_i": 18, "cabeza": 2},
    "escucha":  {"cabeza": 4},
}

# Reparto con una logica: A la mesa de las potencias, B los teatros donde estan pasando cosas,
# C los numeros y el calendario. Definido en escaleta.py, espejado aca para no importar de mas.
PRESENTADOR_DE_BLOQUE = {
    "COLD OPEN": "A", "THE POWERS": "A",
    "THE MIDDLE EAST": "B", "THE SOUTH": "B", "THE PACIFIC": "B",
    "THE MONEY": "C", "TECH & ENERGY": "C", "WHAT TO WATCH": "C",
}
ROTULO = {
    "A": ("THE CORRESPONDENT", "washington · brussels · moscow desk"),
    "B": ("THE ANALYST", "jerusalem · buenos aires · sydney desk"),
    "C": ("THE ARCHIVIST", "money · energy · what to watch"),
}

ESQUEMA_GUION = {
    "type": "object",
    "properties": {
        "fecha": {"type": "string"},
        "titulo": {"type": "string"},
        "bloques": {
            "type": "array", "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "enum": list(PRESENTADOR_DE_BLOQUE.keys())},
                    "presentador": {"type": "string", "enum": ["A", "B", "C"]},
                    "beats": {
                        "type": "array", "minItems": 1,
                        "items": {
                            "type": "object",
                            "properties": {
                                "t": {"type": "number", "minimum": 0},
                                "dur": {"type": "number", "exclusiveMinimum": 0},
                                "texto": {"type": "string"},
                                "ficha": {"type": "string"},
                                "datos": {"type": "object"},
                                "pose": {"type": "string", "enum": list(POSES.keys())},
                            },
                            "required": ["t", "dur", "texto", "ficha", "datos"],
                        },
                    },
                },
                "required": ["nombre", "presentador", "beats"],
            },
        },
    },
    "required": ["fecha", "bloques"],
}


def _f(px, bold=False):
    for n in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(n, px)
        except Exception:
            pass
    return ImageFont.load_default()


def cargar_guion(path):
    """Carga y VALIDA. Un guion que no valida aborta la etapa: mejor no salir que salir roto."""
    with open(path, encoding="utf-8") as fh:
        g = json.load(fh)
    try:
        import jsonschema
        jsonschema.validate(g, ESQUEMA_GUION)
    except ImportError:
        pass
    # Coherencia temporal: los beats no se pisan ni dejan huecos dentro de un bloque.
    for b in g["bloques"]:
        beats = sorted(b["beats"], key=lambda x: x["t"])
        for i in range(len(beats) - 1):
            fin = beats[i]["t"] + beats[i]["dur"]
            if fin > beats[i + 1]["t"] + 0.05:
                raise ValueError("beats superpuestos en %s: %.2f pisa a %.2f"
                                 % (b["nombre"], fin, beats[i + 1]["t"]))
        b["beats"] = beats
    return g


class Escena:
    """Compone cuadros. Cachea lo caro: las poses del presentador y las fichas estaticas."""

    def __init__(self, guion, presentadores=None, pista_visemas=None, fecha=None):
        self.guion = guion
        self.fecha = fecha or guion.get("fecha") or str(datetime.now(timezone.utc).date())
        self.visemas = pista_visemas or []
        self._cache_pose = {}
        self._cache_ficha = {}
        self._docs = {}
        self._rig = None
        self._bocas = None

        self.beats = []
        for b in guion["bloques"]:
            pres = b.get("presentador") or PRESENTADOR_DE_BLOQUE.get(b["nombre"], "A")
            for beat in b["beats"]:
                self.beats.append({**beat, "bloque": b["nombre"], "presentador": pres})
        self.beats.sort(key=lambda x: x["t"])
        self.dur = max((b["t"] + b["dur"] for b in self.beats), default=0.0)

    # ---------------------------------------------------------------- piezas

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
            except ImportError:
                self._bocas = False
        return self._bocas

    def beat_en(self, t):
        activo = None
        for b in self.beats:
            if b["t"] <= t < b["t"] + b["dur"]:
                return b
            if b["t"] <= t:
                activo = b
        return activo or (self.beats[0] if self.beats else None)

    def _rig_doc(self, clave):
        """rig_<clave>.json: de ahi sale la posicion de la boca, distinta en cada presentador."""
        if clave not in self._docs:
            p = os.path.join(BASE, "presentador", "rig_%s.json" % clave)
            try:
                with open(p, encoding="utf-8") as fh:
                    self._docs[clave] = json.load(fh)
            except Exception:
                self._docs[clave] = {}
        return self._docs[clave]

    def _panel_presentador(self, clave, pose, letra_boca):
        """Panel izquierdo. La pose se cachea; la boca se pega encima, que es lo barato.

        La boca se coloca con EXACTAMENTE la misma transformacion con la que se pego el cuerpo
        (offset y escala guardados junto a la pose). Calcularla aparte es como termino la primera
        version: la boca de B y C usaba la coordenada de A, y encima 42 px mas arriba de donde iba.
        """
        ck = (clave, pose)
        guardado = self._cache_pose.get(ck)
        if guardado is None:
            rig = self._mod_rig()
            try:
                cuerpo = rig.componer(clave, POSES.get(pose, {}), fondo=PAPEL_IZQ, brads=True)
            except Exception:
                cuerpo = Image.new("RGB", (768, 1024), PAPEL_IZQ)
            w0, h0 = cuerpo.size
            alto = H - HDR - 42
            esc = alto / float(h0)
            cuerpo = cuerpo.resize((int(w0 * esc), alto), Image.LANCZOS)
            ox, oy = (CREASE - cuerpo.width) // 2, (H - HDR) - alto
            base = Image.new("RGB", (CREASE, H - HDR), PAPEL_IZQ)
            base.paste(cuerpo, (ox, oy))
            guardado = (base, ox, oy, esc)
            self._cache_pose[ck] = guardado

        base, ox, oy, esc = guardado
        bocas = self._mod_bocas()
        if not bocas or not letra_boca:
            return base
        try:
            bx, by = self._rig_doc(clave).get("boca") or [390, 296]
            b = bocas.dibujar_boca(letra_boca, ancho=max(24, int(ANCHO_BOCA * esc)))
            panel = base.copy()
            panel.paste(b, (int(ox + bx * esc - b.width / 2.0),
                            int(oy + by * esc - b.height / 2.0)), b)
            return panel
        except Exception:
            return base

    def _panel_ficha(self, beat, t_local):
        ck = (beat["ficha"], json.dumps(beat["datos"], sort_keys=True, default=str),
              round(min(t_local, 0.6), 1))
        im = self._cache_ficha.get(ck)
        if im is None:
            try:
                import fichas
                im = fichas.render_ficha(beat["ficha"], beat["datos"],
                                         size=(W - CREASE, H - HDR), t=t_local)
            except Exception as e:
                im = Image.new("RGB", (W - CREASE, H - HDR), PAPEL)
                ImageDraw.Draw(im).text((60, 60), "ficha %s\n%s" % (beat["ficha"], e),
                                        font=_f(26), fill=(184, 64, 47))
            if len(self._cache_ficha) > 60:
                self._cache_ficha.clear()
            self._cache_ficha[ck] = im
        return im

    # ---------------------------------------------------------------- cuadro

    def cuadro(self, t):
        beat = self.beat_en(t)
        im = Image.new("RGB", (W, H), PAPEL)
        if beat is None:
            return im
        d = ImageDraw.Draw(im)

        letra = "X"
        if self.visemas:
            bocas = self._mod_bocas()
            if bocas:
                try:
                    letra = bocas.boca_en(self.visemas, t)
                except Exception:
                    letra = "X"

        im.paste(self._panel_presentador(beat["presentador"], beat.get("pose", "reposo"), letra),
                 (0, HDR))
        im.paste(self._panel_ficha(beat, t - beat["t"]), (CREASE, HDR))

        # pliegue entre paneles
        d.rectangle([CREASE - 2, HDR, CREASE + 2, H], fill=(214, 203, 182))

        # cabecera
        d.rectangle([0, 0, W, HDR], fill=PAPEL)
        d.line([(0, HDR), (W, HDR)], fill=(196, 184, 162), width=3)
        x = 54
        d.text((x, 30), "THE LEDGER", font=_f(40, True), fill=TINTA)
        x += d.textlength("THE LEDGER", font=_f(40, True)) + 22
        d.text((x, 41), "· daily", font=_f(27), fill=GRIS)
        fecha = self.fecha.upper()
        d.text((W - 54 - d.textlength(fecha, font=_f(27)), 42), fecha, font=_f(27), fill=GRIS)

        # sello del bloque
        sello = Image.new("RGBA", (400, 76), (0, 0, 0, 0))
        ds = ImageDraw.Draw(sello)
        ancho = int(ds.textlength(beat["bloque"], font=_f(34, True))) + 56
        sello = sello.crop((0, 0, ancho, 76))
        ds = ImageDraw.Draw(sello)
        ds.rectangle([3, 3, ancho - 4, 72], outline=AZUL, width=5)
        ds.text((28, 20), beat["bloque"], font=_f(34, True), fill=AZUL)
        sello = sello.rotate(-1.2, resample=Image.BICUBIC, expand=False)
        im.paste(sello, (54, 136), sello)

        # rotulo del presentador
        nombre, mesa = ROTULO.get(beat["presentador"], ("", ""))
        ancho = int(d.textlength(nombre, font=_f(33, True))) + 108
        d.rectangle([0, 966, ancho, 1046], fill=AZUL)
        d.text((54, 980), nombre, font=_f(33, True), fill=PAPEL)
        d.text((54, 1016), mesa, font=_f(21), fill=(196, 208, 222))
        return im


def construir(guion, presentadores=None, pista_visemas=None):
    return Escena(guion, presentadores, pista_visemas)


# --------------------------------------------------------------------------- autotest

def _guion_ejemplo():
    return {
        "fecha": "2026-09-11",
        "titulo": "THE LEDGER — 11 September",
        "bloques": [
            {"nombre": "THE POWERS", "presentador": "A", "beats": [
                {"t": 0.0, "dur": 6.0, "pose": "reposo", "ficha": "titular",
                 "texto": "Washington announced a new package of sanctions this morning.",
                 "datos": {"medio": "Reuters", "fecha": "11 Sep 2026",
                           "titular": "US announces new sanctions on Russia",
                           "bajada": "Measures target energy and shipping."}},
                {"t": 6.0, "dur": 7.0, "pose": "senala", "ficha": "versus",
                 "texto": "Moscow and Kyiv tell different stories about last night.",
                 "datos": {"titulo": "DRONE STRIKE ON BELGOROD",
                           "izq": {"actor": "RUSSIA", "dice": "Air defences shot down 20 drones.",
                                   "fuentes": "MoD · TASS"},
                           "der": {"actor": "UKRAINE", "dice": "The refinery is out of service.",
                                   "fuentes": "General Staff · Ukrinform"},
                           "pie": "Independent evidence: insufficient"}},
            ]},
            {"nombre": "THE SOUTH", "presentador": "B", "beats": [
                {"t": 13.0, "dur": 5.0, "pose": "enfatiza", "ficha": "dato",
                 "texto": "Argentine inflation slowed for a third month.",
                 "datos": {"numero": "1.9", "unidad": "%", "etiqueta": "monthly CPI",
                           "contexto": "third consecutive slowdown"}},
            ]},
        ],
    }


def _autotest():
    fallos = []

    def chequeo(nombre, cond, extra=""):
        print(("OK   " if cond else "FALLA") + " " + nombre + ((" | " + extra) if extra else ""))
        if not cond:
            fallos.append(nombre)

    print("--- validacion del guion ---")
    tmp = os.path.join(BASE, "_guion_test.json")
    json.dump(_guion_ejemplo(), open(tmp, "w", encoding="utf-8"))
    try:
        g = cargar_guion(tmp)
        chequeo("un guion bien formado carga", len(g["bloques"]) == 2)
    except Exception as e:
        chequeo("un guion bien formado carga", False, str(e))
        g = _guion_ejemplo()

    malo = _guion_ejemplo()
    malo["bloques"][0]["beats"][1]["t"] = 3.0        # pisa al anterior
    json.dump(malo, open(tmp, "w", encoding="utf-8"))
    try:
        cargar_guion(tmp)
        chequeo("beats superpuestos son rechazados", False)
    except ValueError:
        chequeo("beats superpuestos son rechazados", True)
    except Exception as e:
        chequeo("beats superpuestos son rechazados", False, type(e).__name__)

    try:
        import jsonschema
        jsonschema.Draft202012Validator.check_schema(ESQUEMA_GUION)
        chequeo("ESQUEMA_GUION es JSON Schema valido", True)
        malo2 = _guion_ejemplo()
        malo2["bloques"][0]["nombre"] = "UN BLOQUE INVENTADO"
        try:
            jsonschema.validate(malo2, ESQUEMA_GUION)
            chequeo("un bloque inventado es rechazado", False)
        except jsonschema.ValidationError:
            chequeo("un bloque inventado es rechazado", True)
    except ImportError:
        print("SALTEA: jsonschema")
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

    print("--- linea de tiempo ---")
    esc = construir(_guion_ejemplo())
    chequeo("duracion total correcta", abs(esc.dur - 18.0) < 0.01, "dur=%.1f" % esc.dur)
    chequeo("a los 2 s manda el primer beat", esc.beat_en(2.0)["ficha"] == "titular")
    chequeo("a los 8 s manda el versus", esc.beat_en(8.0)["ficha"] == "versus")
    chequeo("a los 15 s cambia de bloque y de presentador",
            esc.beat_en(15.0)["bloque"] == "THE SOUTH" and esc.beat_en(15.0)["presentador"] == "B")
    chequeo("fuera de rango no explota", esc.beat_en(999.0) is not None)

    print("--- cuadros ---")
    try:
        im = esc.cuadro(7.0)
        chequeo("cuadro de 1920x1080", im.size == (W, H), str(im.size))
        colores = im.getcolors(maxcolors=200000)
        chequeo("el cuadro no es de un solo color", colores is None or len(colores) > 200,
                "colores=%s" % (len(colores) if colores else ">200k"))
        muestra = os.path.join(BASE, "_escena_prueba.jpg")
        tira = Image.new("RGB", (W // 2 * 3 + 40, H // 2 + 20), PAPEL)
        for i, t in enumerate((2.0, 8.0, 15.0)):
            c = esc.cuadro(t).resize((W // 2, H // 2), Image.LANCZOS)
            tira.paste(c, (10 + i * (W // 2 + 10), 10))
        tira.save(muestra, quality=90)
        print("      muestra en %s" % muestra)
        chequeo("se escribio la tira de muestra", os.path.exists(muestra))
    except Exception as e:
        chequeo("cuadro se compone", False, "%s: %s" % (type(e).__name__, e))

    print("--- cache (lo que hace viable el render) ---")
    try:
        esc2 = construir(_guion_ejemplo())
        esc2.cuadro(7.0)
        n1 = len(esc2._cache_pose)
        for k in range(10):
            esc2.cuadro(7.0 + k * 0.04)
        chequeo("10 cuadros del mismo beat no recomponen la pose",
                len(esc2._cache_pose) == n1, "poses cacheadas=%d" % len(esc2._cache_pose))
    except Exception as e:
        chequeo("cache de poses", False, str(e))

    print()
    print("FALLOS: %d" % len(fallos) + (" -> " + ", ".join(fallos) if fallos else ""))
    return 1 if fallos else 0


if __name__ == "__main__":
    if "--autotest" in sys.argv:
        sys.exit(_autotest())
    if "--muestra" in sys.argv:
        i = sys.argv.index("--muestra")
        g = cargar_guion(sys.argv[i + 1])
        t = float(sys.argv[i + 2]) if len(sys.argv) > i + 2 else 0.0
        out = os.path.join(BASE, "_cuadro_%.1f.jpg" % t)
        construir(g).cuadro(t).save(out, quality=93)
        print(out)
        sys.exit(0)
    print(__doc__)
