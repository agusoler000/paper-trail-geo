# -*- coding: utf-8 -*-
"""Produce los shorts verticales de un dia: voz -> cuadros -> mp4.

    python videos/DAILY/hacer_cortos.py _dias/2026-09-14/shorts

Cada subcarpeta con un `guion.json` sale como `short.mp4` a 1080x1920.
Sin intro de canal y con la outro hablada dentro de la pieza (`SHORTS.md` regla 8).
La cortina es la misma del episodio, al mismo nivel, para que suene al mismo programa.
"""
import json
import multiprocessing as mp
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(BASE))
for p in (RAIZ, BASE, os.path.join(BASE, "presentador")):
    if p not in sys.path:
        sys.path.insert(0, p)

FPS = 24


def _tramo(args):
    d, i0, i1 = args
    import corto as CO
    g = CO.cargar(os.path.join(d, "guion.json"))
    vis = os.path.join(d, "visemas.json")
    pista = ([(float(t), f) for t, f in json.load(open(vis, encoding="utf-8"))]
             if os.path.exists(vis) else [])
    c = CO.construir(g, pista_visemas=pista)
    frames = os.path.join(d, "_frames")
    n = 0
    for i in range(i0, i1):
        dest = os.path.join(frames, "f_%06d.jpg" % i)
        if os.path.exists(dest):
            continue
        c.cuadro(i / FPS).save(dest, quality=92)
        n += 1
    return n


def uno(d, workers=8):
    import voz as _v
    import corto as CO
    import mezclar as MZ

    nombre = os.path.basename(d)
    g = json.load(open(os.path.join(d, "guion.json"), encoding="utf-8"))

    # --- voz (reacomoda la linea de tiempo con la duracion real)
    wav = os.path.join(d, "voz.wav")
    g2, pista, inf = _v.generar(g, wav)
    json.dump(g2, open(os.path.join(d, "guion.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    json.dump(pista, open(os.path.join(d, "visemas.json"), "w", encoding="utf-8"), indent=1)
    dur = max(b["t"] + b["dur"] for bl in g2["bloques"] for b in bl["beats"])
    print("  %-12s voz %.1f s (%d chars, USD %.2f)" % (nombre, dur, inf["chars"], inf["costo_usd"]),
          flush=True)
    if dur < 50:
        print("  %-12s AVISO: %.0f s, por debajo del minimo de 50 s de SHORTS.md" % (nombre, dur),
              flush=True)

    # --- cuadros
    frames = os.path.join(d, "_frames")
    os.makedirs(frames, exist_ok=True)
    total = int(dur * FPS)
    t0 = time.time()
    tareas = [(d, i, min(i + 48, total)) for i in range(0, total, 48)]
    with mp.Pool(workers) as pool:
        escritos = sum(pool.imap_unordered(_tramo, tareas))
    print("  %-12s %d cuadros en %.0f s" % (nombre, escritos, time.time() - t0), flush=True)

    # --- audio: voz + cortina, misma receta del episodio
    bed = MZ.cama(os.path.join(d, "_cortina.wav"), dur)
    audio = os.path.join(d, "_audio.m4a")
    fc = ("[1:a]volume=%.1fdB[m];"
          "[m][0:a]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=700:"
          "makeup=1:detection=rms[mduck];"
          "[0:a][mduck]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
          "alimiter=limit=0.97[a]" % MZ.BAJO_VOZ_DB)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-i", bed,
                    "-filter_complex", fc, "-map", "[a]",
                    "-c:a", "aac", "-b:a", "192k", audio], check=True)

    salida = os.path.join(d, "short.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS),
                    "-i", os.path.join(frames, "f_%06d.jpg"), "-i", audio,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", salida], check=True)
    mb = os.path.getsize(salida) / 1e6
    print("  %-12s LISTO %s (%.1f s, %.1f MB)" % (nombre, salida, MZ._dur(salida), mb), flush=True)
    return salida


if __name__ == "__main__":
    mp.freeze_support()
    raiz = sys.argv[1] if len(sys.argv) > 1 else None
    if not raiz:
        raise SystemExit("uso: python videos/DAILY/hacer_cortos.py <carpeta de shorts>")
    raiz = raiz if os.path.isabs(raiz) else os.path.join(BASE, raiz)
    dirs = sorted(os.path.join(raiz, n) for n in os.listdir(raiz)
                  if os.path.isdir(os.path.join(raiz, n))
                  and os.path.exists(os.path.join(raiz, n, "guion.json")))
    print("%d shorts en %s" % (len(dirs), raiz), flush=True)
    for d in dirs:
        uno(d)
