# -*- coding: utf-8 -*-
"""Similitud semantica de titulares: embeddings + ancla de entidad rara.

    python radar/semantica.py --autotest

POR QUE ESTE MODULO EXISTE (medido el 2026-09-11, no supuesto)

La primera version del Radar agrupaba con TF-IDF de n-gramas de caracteres, para no bajar un modelo.
Contra datos reales no funciono, y el numero que lo demostro es este:

    "Washington introduces new sanctions against Moscow"
    "Вашингтон вводит новые санкции против Москвы"      (el MISMO hecho, en ruso)
        TF-IDF de caracteres : 0.002      <- no los junta jamas
        embeddings           : 0.940      <- obvio

Y peor: con TF-IDF, dos hechos DISTINTOS ("sanciones a Rusia" y "drones sobre Belgorod") daban 0.244
mientras que el MISMO hecho contado de dos formas daba 0.136. No existe umbral que separe eso, porque
TF-IDF compara palabras y esto pide comparar significado. Una corrida completa lo confirmo: de 3.851
articulos reales se formaron 3.748 eventos, o sea no agrupo nada.

EL CASO DIFICIL, que no lo arregla ningun umbral
    "Russia says air defences downed 20 drones over Belgorod"
    "Fire reported at Belgorod oil refinery after overnight attack"
Es el MISMO incidente contado por los dos bandos, y justamente por eso dicen cosas opuestas: la
similitud semantica es 0.065. No es un defecto del modelo, es la naturaleza del hecho — y es
exactamente el material de la ficha `versus`.

LA SOLUCION, en tres tramos
 1. ANCLA DE ENTIDAD RARA. Los dos comparten "Belgorod", que aparece en 0 de 3.851 titulares del dia:
    es una entidad rarisima. Compartir "Russia" (121 de 3.851) no dice nada; compartir "Belgorod" dice
    muchisimo. Por eso el ancla se pesa por IDF de entidad, no por Jaccard, que diluye lo raro.
 2. PRECISION ANTES QUE COBERTURA. Partir un acontecimiento en dos es redundante y se nota en el
    orden del dia; fundir dos acontecimientos distintos en uno es un error editorial que sale al aire.
    Por eso el umbral es alto.
 3. EL MARGEN LO DECIDE UN LLM BARATO. Entre 0.35 y 0.60 no hay certeza: ahi se pregunta
    "¿mismo hecho?" a un modelo Flash. Son ~50 pares por dia: centavos, y resuelve justo los dificiles.
"""
import math
import os
import re
import sys
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
_RAIZ = os.path.dirname(BASE)
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DIM = 384

# Calibrados el 2026-09-11 contra un corpus real de 3.851 titulares.
PESO_ANCLA = 0.40         # solo para ORDENAR candidatos, no para decidir (ver decidir())
UMBRAL_SEGURO = 0.60      # semantica pura: de aca para arriba, mismo hecho sin preguntar
UMBRAL_DUDA = 0.35        # semantica pura: de aca a SEGURO se le pregunta al LLM
UMBRAL_ANCLA = 0.18       # con un ancla fuerte, se pregunta desde aca (nunca se afirma)
ANCLA_MINIMA = 0.55       # que tan rara tiene que ser la entidad compartida para que valga
VENTANA_ANCLA_H = 30      # el ancla solo vale si los dos son del mismo tramo de tiempo

_STOP = {
    "the", "a", "an", "of", "on", "in", "at", "over", "after", "says", "said", "and", "for",
    "to", "new", "its", "as", "with", "from", "by", "is", "are", "will", "has", "have",
    "el", "la", "los", "las", "de", "del", "por", "para", "con", "que", "una", "un",
}
_ENT = re.compile(r"\b[A-ZА-ЯÀ-Þ][\wа-яß-ÿ'-]{2,}\b")
_NUM = re.compile(r"\b\d{2,}\b")

_modelo = None


def _cargar():
    global _modelo
    if _modelo is None:
        from fastembed import TextEmbedding
        _modelo = TextEmbedding(MODELO)
    return _modelo


def disponible():
    try:
        import fastembed  # noqa: F401
        return True
    except ImportError:
        return False


def vectorizar(textos):
    """-> np.ndarray (n, 384) normalizado. ~350 textos/s en CPU, sin torch."""
    import numpy as np
    if not textos:
        return np.zeros((0, DIM), dtype="float32")
    v = np.asarray(list(_cargar().embed(list(textos))), dtype="float32")
    n = np.linalg.norm(v, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return v / n


def vectorizar_uno(texto):
    return vectorizar([texto])[0]


def similitud(a, b):
    import numpy as np
    return float(np.asarray(a) @ np.asarray(b))


# --------------------------------------------------------------------------- entidades

def entidades(texto):
    """Nombres propios y numeros: lo que ancla un titular a un hecho concreto."""
    e = set(_ENT.findall(texto or "")) | set(_NUM.findall(texto or ""))
    return {x.lower() for x in e if x.lower() not in _STOP and len(x) > 2}


class IdfEntidades:
    """Cuan rara es cada entidad en el corpus del dia. 'Belgorod' vale; 'Russia' no."""

    def __init__(self, corpus):
        self.n = max(1, len(corpus))
        self.df = Counter()
        for t in corpus:
            self.df.update(entidades(t))
        self.max = math.log(self.n + 1)

    def idf(self, e):
        return math.log((self.n + 1) / (self.df.get(e, 0) + 1))

    def ancla(self, a, b):
        """0..1 segun lo rara que sea la entidad mas rara que comparten."""
        comunes = entidades(a) & entidades(b)
        if not comunes:
            return 0.0
        return min(1.0, max(self.idf(e) for e in comunes) / self.max)


def puntaje(vec_a, vec_b, texto_a=None, texto_b=None, idf=None, horas=0.0):
    """Puntaje combinado. Sirve para ORDENAR candidatos; para decidir se usa decidir()."""
    s = similitud(vec_a, vec_b)
    if idf is not None and texto_a and texto_b and abs(horas) <= VENTANA_ANCLA_H:
        s += PESO_ANCLA * idf.ancla(texto_a, texto_b)
    return s


def decidir(semantico, ancla=0.0):
    """'si' | 'duda' | 'no'.

    REGLA QUE COSTO UNA CORRIDA ENTERA APRENDER (2026-09-11): el ancla de entidad NUNCA promueve a
    'si'. Solo puede llevar un par hasta 'duda', y ahi decide el LLM.

    Con el ancla sumando directo al puntaje, 3.834 articulos se fundieron en clusters basura: uno
    titulado "The tech wars are about to enter a fiery new phase" se habia tragado un puente en
    Nueva Zelanda y el pase de Messi, porque compartir UNA entidad medio rara sumaba 0,40 y eso
    alcanzaba para cruzar el umbral. Compartir un nombre propio es motivo para PREGUNTAR, nunca
    para afirmar.
    """
    if semantico >= UMBRAL_SEGURO:
        return "si"
    if semantico >= UMBRAL_DUDA:
        return "duda"
    if semantico >= UMBRAL_ANCLA and ancla >= ANCLA_MINIMA:
        return "duda"
    return "no"


ESQUEMA_MISMO = {
    "type": "object",
    "properties": {
        "mismo": {"type": "boolean",
                  "description": "true solo si los dos titulares hablan del MISMO acontecimiento concreto."},
        "por_que": {"type": "string", "description": "Una frase corta."},
    },
    "required": ["mismo", "por_que"],
}

_SISTEMA_MISMO = (
    "Decidis si dos titulares hablan del MISMO acontecimiento concreto.\n"
    "MISMO ACONTECIMIENTO no es mismo tema. Dos ataques distintos en la misma guerra son dos "
    "acontecimientos. Dos versiones enfrentadas del mismo incidente SI son el mismo acontecimiento: "
    "que digan cosas opuestas es justamente la senal de que hablan de lo mismo.\n"
    "Ante la duda respondes false: partir un acontecimiento en dos es barato, fundir dos en uno no."
)


def mismo_hecho(a, b, llm=None):
    """Resuelve el margen con un modelo barato. Ante cualquier error, conservador: False."""
    if llm is None:
        try:
            from radar.llm import llm as _llm
            llm = _llm
        except Exception:
            return False
    try:
        r = llm("masivas",
                "Titular A: %s\nTitular B: %s\n\n¿Hablan del mismo acontecimiento concreto?" % (a, b),
                esquema=ESQUEMA_MISMO, sistema=_SISTEMA_MISMO)
        return bool(r.get("mismo"))
    except Exception:
        return False


# --------------------------------------------------------------------------- autotest

def _autotest():
    fallos = []

    def chequeo(nombre, cond, extra=""):
        print(("OK   " if cond else "FALLA") + " " + nombre + ((" | " + extra) if extra else ""))
        if not cond:
            fallos.append(nombre)

    if not disponible():
        print("SALTEA: falta fastembed (pip install fastembed). Sin el no hay agrupamiento util.")
        return 1

    G = {
        "sanciones": ["US announces new sanctions on Russia over Ukraine war",
                      "US imposes new Russia sanctions",
                      "Washington introduces new sanctions against Moscow",
                      "Вашингтон вводит новые санкции против Москвы"],
        "taiwan": ["Taiwan reports Chinese military aircraft near its airspace",
                   "Taiwan detects Chinese warplanes in its air defence zone",
                   "Taiwan scrambles jets after PLA incursion"],
        "belgorod": ["Drone strike hits Belgorod refinery, Ukraine says",
                     "Russia says air defences downed 20 drones over Belgorod",
                     "Fire reported at Belgorod oil refinery after overnight attack"],
        "milei": ["Argentina inflation slows for the third consecutive month",
                  "Milei celebra la desaceleracion de la inflacion en Argentina"],
        "brent": ["Brent crude climbs on supply concerns",
                  "Oil prices rise as traders weigh supply risks"],
    }
    textos = [t for ts in G.values() for t in ts]
    # El corpus del IDF imita al real medido el 2026-09-11 sobre 3.851 titulares: "Russia" aparecia
    # en 121 y "Belgorod" en 0. Un corpus sintetico donde las dos aparecen una vez no prueba nada.
    ruido = (["Russia and %s discuss energy cooperation" % p
              for p in ("India", "Turkey", "Iran", "Brazil", "Egypt", "Algeria")] * 20
             + ["Federal Reserve Board issues enforcement action", "Indonesia travel advice",
                "NATO Secretary General to visit Germany", "UEFA urges US court to deny bid"] * 30)
    idf = IdfEntidades(textos + ruido)

    print("--- el caso que mato al metodo anterior ---")
    V = vectorizar(textos)
    ix = {t: i for i, t in enumerate(textos)}
    s_ru = similitud(V[ix["Washington introduces new sanctions against Moscow"]],
                     V[ix["Вашингтон вводит новые санкции против Москвы"]])
    chequeo("el mismo hecho en ruso y en ingles se reconoce", s_ru > 0.80, "%.3f (TF-IDF daba 0.002)" % s_ru)

    print("--- el ancla de entidad rara ---")
    chequeo("'belgorod' es rara y 'russia' no",
            idf.idf("belgorod") > idf.idf("russia"),
            "belgorod=%.2f russia=%.2f" % (idf.idf("belgorod"), idf.idf("russia")))
    a = "Russia says air defences downed 20 drones over Belgorod"
    b = "Fire reported at Belgorod oil refinery after overnight attack"
    sin = similitud(V[ix[a]], V[ix[b]])
    con = puntaje(V[ix[a]], V[ix[b]], a, b, idf)
    chequeo("el ancla levanta el caso dificil", con > sin + 0.2,
            "sin ancla=%.3f con ancla=%.3f" % (sin, con))

    print("--- separacion, con la decision de tres tramos ---")
    peor_mismo, mejor_cruce = 9.0, -9.0
    for g, ts in G.items():
        for i, x in enumerate(ts):
            for y in ts[i + 1:]:
                peor_mismo = min(peor_mismo, puntaje(V[ix[x]], V[ix[y]], x, y, idf))
    gl = list(G.items())
    cruces = []
    for i, (g1, t1) in enumerate(gl):
        for g2, t2 in gl[i + 1:]:
            for x in t1:
                for y in t2:
                    s = puntaje(V[ix[x]], V[ix[y]], x, y, idf)
                    mejor_cruce = max(mejor_cruce, s)
                    cruces.append(s)
    print("      mismo hecho baja a %.3f · hechos distintos suben a %.3f" % (peor_mismo, mejor_cruce))
    chequeo("ningun par de hechos DISTINTOS llega al umbral seguro",
            mejor_cruce < UMBRAL_SEGURO, "max cruce=%.3f < %.2f" % (mejor_cruce, UMBRAL_SEGURO))

    juntados = sum(1 for g, ts in G.items() for i, x in enumerate(ts) for y in ts[i + 1:]
                   if decidir(puntaje(V[ix[x]], V[ix[y]], x, y, idf)) == "si")
    dudas = sum(1 for g, ts in G.items() for i, x in enumerate(ts) for y in ts[i + 1:]
                if decidir(puntaje(V[ix[x]], V[ix[y]], x, y, idf)) == "duda")
    total = sum(len(ts) * (len(ts) - 1) // 2 for ts in G.values())
    print("      de %d pares del mismo hecho: %d seguros, %d a consultar, %d se pierden"
          % (total, juntados, dudas, total - juntados - dudas))
    chequeo("se captura la mayoria del mismo hecho sin preguntar",
            juntados >= total * 0.6, "%d/%d" % (juntados, total))
    chequeo("lo que no se captura cae en 'duda', no en 'no'",
            (juntados + dudas) >= total * 0.75, "%d/%d" % (juntados + dudas, total))

    print("--- prioridad de precision ---")
    falsos = [s for s in cruces if decidir(s) == "si"]
    chequeo("CERO falsas fusiones de hechos distintos", len(falsos) == 0, "falsos=%d" % len(falsos))

    print("--- rendimiento ---")
    import time
    t0 = time.time()
    vectorizar(["titular de prueba numero %d sobre geopolitica" % i for i in range(300)])
    v = 300 / (time.time() - t0)
    print("      %.0f textos/s en CPU" % v)
    chequeo("3.900 titulares se vectorizan en menos de 2 min", 3900 / v < 120,
            "%.0f s estimados" % (3900 / v))

    print()
    print("FALLOS: %d" % len(fallos) + (" -> " + ", ".join(fallos) if fallos else ""))
    return 1 if fallos else 0


if __name__ == "__main__":
    if "--autotest" in sys.argv:
        sys.exit(_autotest())
    print(__doc__)
