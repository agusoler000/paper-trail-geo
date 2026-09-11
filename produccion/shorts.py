# -*- coding: utf-8 -*-
"""
Shorts verticales (1080x1920) cortados de un episodio ya renderizado. 0 creditos.

No genera voz ni imagen nueva: reusa el master, la narracion ya pagada y los tiempos alineados.
Cada short se define por un rango de LINEAS del guion (indices de <ep>.tiempos.json -> "lineas"),
un gancho de 2-3 palabras y el texto de publicacion.

Uso:
    python shorts.py 01_aviacion_rusa --check       # hoja de contacto, no renderiza
    python shorts.py 01_aviacion_rusa               # renderiza todos
    python shorts.py 01_aviacion_rusa 01 04         # renderiza solo esos ids
    python shorts.py 01_aviacion_rusa --plan 4,3,3  # prepara _up/ + PLAN_SUBIDA.json para publicar

Salida: produccion/shorts/<ep>/<id>_<slug>.mp4  +  _hoja.jpg
"""
import sys, os, json, math, subprocess, shutil
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import numpy as np
import props as PR
from props import TINTA, PAPEL, OCRE, ROJO, MADERA, FONT, FONTC

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
ASSETS = os.path.join(AQUI, 'assets')

W, H = 1080, 1920                 # lienzo vertical
HX, HY = 40, 120                  # hoja de papel: el soporte de todo
HW, HH = 1000, 1680
VW, VH = 1000, 563                # bloque de video (16:9 completo: nada cortado)
VX, VY = 40, 700                  # posicion del bloque de video
CTA_DUR = 2.2                     # tarjeta final
FPS = 24
SUB_Y = 1400                      # centro de la banda de subtitulos (encima de la UI de Shorts)
SUB_W = 900                       # ancho maximo del subtitulo

madera_tx = Image.open(os.path.join(ASSETS, 'madera_1920.png')).convert('RGBA')
papel_tx = Image.open(os.path.join(ASSETS, 'papel_1920.png')).convert('RGBA')


# ---------------------------------------------------------------- utilidades de imagen
def tile(tx, size):
    out = Image.new('RGBA', size)
    for y in range(0, size[1], tx.height):
        for x in range(0, size[0], tx.width):
            out.paste(tx, (x, y))
    return out


def vineta(im, fuerza=0.75, blur=160, margen=180):
    w, h = im.size
    vig = Image.new('L', (w, h), 0)
    ImageDraw.Draw(vig).ellipse([-margen, -margen, w + margen, h + margen], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(blur))
    osc = Image.new('RGBA', (w, h), (20, 12, 6, 255))
    osc.putalpha(vig.point(lambda v: int((255 - v) * fuerza)))
    im.alpha_composite(osc)


def sombra(base, pieza, xy, blur=14, alpha=140, off=(9, 13)):
    s = Image.new('RGBA', pieza.size, (0, 0, 0, 0))
    s.putalpha(pieza.split()[3].point(lambda v: min(v, alpha)).filter(ImageFilter.GaussianBlur(blur)))
    base.alpha_composite(s, (xy[0] + off[0], xy[1] + off[1]))
    base.alpha_composite(pieza, xy)


def grano(im, fuerza=0.28):
    g = np.asarray(tile(papel_tx, im.size).convert('L')).astype(np.float32) - 215
    rgb = np.asarray(im.convert('RGB')).astype(np.float32) + g[..., None] * fuerza
    out = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert('RGBA')
    out.putalpha(im.split()[3])
    return out


def hoja_papel(w, h, color=PAPEL, radio=14, borde=True, alpha=255):
    def f(d):
        d.rounded_rectangle([1, 1, w - 2, h - 2], radius=radio, fill=255)
    p = PR.papel((w, h), f, color, sombra=False)
    if borde:
        d = ImageDraw.Draw(p)
        d.rounded_rectangle([9, 9, w - 10, h - 10], radius=max(4, radio - 5), outline=TINTA + (255,), width=3)
    if alpha < 255:
        p.putalpha(p.split()[3].point(lambda v: int(v * alpha / 255)))
    return p


def medir(txt, fnt):
    bb = ImageDraw.Draw(Image.new('L', (8, 8))).textbbox((0, 0), txt, font=fnt)
    return bb[2] - bb[0], bb[3] - bb[1]


# ---------------------------------------------------------------- piezas del lienzo
def ficha_marca(r=52):
    def f(d):
        d.ellipse([2, 2, 2 * r - 2, 2 * r - 2], fill=255)
    p = PR.papel((2 * r + 2, 2 * r + 2), f, OCRE, sombra=False)
    d = ImageDraw.Draw(p)
    d.ellipse([int(r * .17), int(r * .17), int(2 * r - r * .17), int(2 * r - r * .17)], outline=TINTA + (255,), width=3)
    d.ellipse([int(r * .24), int(r * .24), int(2 * r - r * .24), int(2 * r - r * .24)], outline=TINTA + (255,), width=2)
    d.text((r + 1, r + 1), 'PT', fill=TINTA + (255,), font=FONTC(int(r * .78)), anchor='mm')
    return p


def tarjeta_hook(lineas, rojo=None, size=98, ancho_max=940):
    """Tarjeta de papel con el gancho. `rojo` = indice de la linea que va en rojo."""
    fnt = FONTC(size)
    while max(medir(t, fnt)[0] for t in lineas) > ancho_max and size > 52:
        size -= 3
        fnt = FONTC(size)
    anchos = [medir(t, fnt)[0] for t in lineas]
    lh = int(size * 1.14)
    w = max(anchos) + 96
    h = lh * len(lineas) + 78
    p = hoja_papel(w, h, PAPEL, radio=16)
    d = ImageDraw.Draw(p)
    y0 = h / 2 - (len(lineas) - 1) * lh / 2
    for i, t in enumerate(lineas):
        col = ROJO if (rojo is not None and i == rojo) else TINTA
        d.text((w / 2, y0 + i * lh), t, fill=col + (255,), font=fnt, anchor='mm')
    return p


def tarjeta_cta():
    lineas = ['FULL EPISODE', 'ON THE CHANNEL']
    fnt = FONTC(84)
    w = max(medir(t, fnt)[0] for t in lineas) + 110
    h = 84 * 2 + 190
    p = hoja_papel(w, h, PAPEL, radio=16)
    d = ImageDraw.Draw(p)
    d.text((w / 2, 88), lineas[0], fill=TINTA + (255,), font=fnt, anchor='mm')
    d.text((w / 2, 88 + 96), lineas[1], fill=TINTA + (255,), font=fnt, anchor='mm')
    d.text((w / 2, h - 74), 'PAPER TRAIL', fill=ROJO + (255,), font=FONTC(58), anchor='mm')
    return p


def fondo(hook, rojo):
    """Todo lo que va DEBAJO del video: mesa, hoja de papel, marca, gancho, pie."""
    im = tile(madera_tx, (W, H))
    vineta(im)
    hoja = hoja_papel(HW, HH, PAPEL, radio=6, borde=False)
    sombra(im, hoja, (HX, HY), blur=26, alpha=165, off=(12, 20))
    d = ImageDraw.Draw(im)

    # marca, dentro de la hoja
    fi = ficha_marca(38)
    nom = 'PAPER TRAIL'
    fnt = FONTC(50)
    tw, _ = medir(nom, fnt)
    ancho = fi.width + 20 + tw
    x0 = (W - ancho) // 2
    sombra(im, fi, (x0, HY + 62), blur=8, alpha=110, off=(5, 7))
    d.text((x0 + fi.width + 20, HY + 62 + fi.height / 2), nom, fill=TINTA + (255,), font=fnt, anchor='lm')
    d.line([(HX + 70, HY + 172), (HX + HW - 70, HY + 172)], fill=TINTA + (90,), width=2)

    # gancho: texto grande directo sobre el papel (se lee a un pulgar de distancia)
    size = 96
    fnt = FONTC(size)
    while max(medir(t, fnt)[0] for t in hook) > HW - 96 and size > 54:
        size -= 3
        fnt = FONTC(size)
    lh = int(size * 1.14)
    cy = (HY + 200 + VY) / 2
    y0 = cy - (len(hook) - 1) * lh / 2
    for i, t in enumerate(hook):
        col = ROJO if (rojo is not None and i == rojo) else TINTA
        d.text((W / 2, y0 + i * lh), t, fill=col + (255,), font=fnt, anchor='mm')

    # pie de la hoja
    d.line([(HX + 70, SUB_Y + 190), (HX + HW - 70, SUB_Y + 190)], fill=TINTA + (70,), width=2)
    d.text((W / 2, SUB_Y + 246), 'FOLLOW THE PAPER.', fill=OCRE + (255,), font=FONTC(46), anchor='mm')

    # sombra del bloque de video
    sh = Image.new('RGBA', (VW, VH), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([0, 0, VW, VH], fill=(0, 0, 0, 160))
    sh = sh.filter(ImageFilter.GaussianBlur(16))
    im.alpha_composite(sh, (VX + 4, VY + 12))
    return grano(im), None


def frente():
    """Lo que va ENCIMA del video: linea de tinta del bloque."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([VX, VY, VX + VW - 1, VY + VH - 1], outline=(24, 22, 19, 215), width=4)
    return im


def banda_sub(texto_lineas, resaltar):
    """Subtitulo en tinta sobre el papel. Palabras en `resaltar` van en rojo."""
    size = 58
    fnt = FONT(size)
    lh = int(size * 1.30)
    anchos = [sum(medir(p + ' ', fnt)[0] for p in ln.split()) for ln in texto_lineas]
    w = min(SUB_W, int(max(anchos)) + 40)
    h = lh * len(texto_lineas) + 26
    p = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(p)
    y0 = h / 2 - (len(texto_lineas) - 1) * lh / 2
    for i, ln in enumerate(texto_lineas):
        partes = ln.split()
        anchura = sum(medir(x + ' ', fnt)[0] for x in partes) - medir(' ', fnt)[0]
        x = (w - anchura) / 2
        for pal in partes:
            limpio = pal.strip('.,;:!?"').lower()
            col = ROJO if limpio in resaltar else TINTA
            d.text((x, y0 + i * lh), pal, fill=col + (255,), font=fnt, anchor='lm')
            x += medir(pal + ' ', fnt)[0]
    # halo claro: despega el texto del grano del papel sin ensuciar
    halo = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    halo.putalpha(p.split()[3].filter(ImageFilter.GaussianBlur(7)).point(lambda v: min(255, int(v * 2.2))))
    halo = Image.composite(Image.new('RGBA', (w, h), PAPEL + (255,)), halo, halo.split()[3])
    halo.putalpha(p.split()[3].filter(ImageFilter.GaussianBlur(7)).point(lambda v: min(255, int(v * 2.2))))
    halo.alpha_composite(p)
    return halo


# ---------------------------------------------------------------- subtitulos
# palabras que no pueden quedar al final de un subtitulo (rompen la lectura)
DEBILES = {'and', 'the', 'of', 'in', 'to', 'a', 'an', 'or', 'that', 'with', 'for', 'is', 'are',
           'it', 'on', 'at', 'as', 'but', 'by', 'from', 'was', 'were', 'not', 'its', 'their',
           'his', 'her', 'you', 'we', 'they', 'this', 'these', 'those', 'no', 'so', 'if', 'when',
           'without', 'into', 'over', 'about', 'than', 'because', 'while', 'after', 'before'}


def trocear(texto, max_chars=50):
    """Parte una linea del guion en trozos de <=max_chars sin dejar palabras debiles al final."""
    out, cur = [], []
    for w in texto.split():
        cur.append(w)
        if len(' '.join(cur)) >= max_chars:
            resto = []
            while len(cur) > 3 and cur[-1].strip('.,;:!?"').lower() in DEBILES:
                resto.insert(0, cur.pop())
            out.append(' '.join(cur))
            cur = resto
    if cur:
        if out and len(' '.join(cur)) < 16:
            out[-1] += ' ' + ' '.join(cur)
        else:
            out.append(' '.join(cur))
    return out


def partir(texto, fnt, ancho_max):
    """Parte un trozo en lineas que caben SIEMPRE en ancho_max; 2 lineas de ancho parecido si se puede."""
    if medir(texto, fnt)[0] <= ancho_max:
        return [texto]
    pal = texto.split()
    mejor, dif = None, 1e9
    for i in range(1, len(pal)):
        a, b = ' '.join(pal[:i]), ' '.join(pal[i:])
        wa, wb = medir(a, fnt)[0], medir(b, fnt)[0]
        if max(wa, wb) <= ancho_max and abs(wa - wb) < dif:
            mejor, dif = [a, b], abs(wa - wb)
    if mejor:
        return mejor
    out, cur = [], ''
    for w in pal:                                  # greedy: nunca deja una linea mas ancha que el cuadro
        prueba = (cur + ' ' + w).strip()
        if cur and medir(prueba, fnt)[0] > ancho_max:
            out.append(cur)
            cur = w
        else:
            cur = prueba
    if cur:
        out.append(cur)
    return out


def cues(lineas, t0):
    """Convierte lineas del guion en cues de subtitulo de <=2 lineas, con tiempos relativos."""
    fnt = FONT(58)
    ancho = SUB_W - 40
    out = []
    for L in lineas:
        trozos = trocear(L['texto'])
        chars = [len(x) for x in trozos]
        total = sum(chars) or 1
        dur = L['fin'] - L['inicio']
        t = L['inicio'] - t0
        for tr, c in zip(trozos, chars):
            d = dur * c / total
            out.append({'t0': t, 't1': t + d, 'lineas': partir(tr, fnt, ancho)})
            t += d
    # cerrar huecos cortos para que no parpadee
    for i in range(len(out) - 1):
        if out[i + 1]['t0'] - out[i]['t1'] < 0.5:
            out[i]['t1'] = out[i + 1]['t0']
    return out


# ---------------------------------------------------------------- render
def ffmpeg(args):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y'] + args,
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-3000:])
        raise SystemExit('ffmpeg fallo')


def construir(ep, cfg, S, tmp, out_dir, solo_frame=False):
    """Arma un short. Devuelve la ruta de salida."""
    master = os.path.join(AQUI, cfg['master'])
    T = json.load(open(os.path.join(AQUI, cfg['tiempos']), encoding='utf-8'))
    L = T['lineas']
    tramo = L[S['l0']:S['l1'] + 1]
    # el aire de entrada y salida nunca puede comerse la voz vecina (hay beats sin silencio entre lineas)
    hueco_ini = tramo[0]['inicio'] - (L[S['l0'] - 1]['fin'] if S['l0'] > 0 else 0.0)
    hueco_fin = (L[S['l1'] + 1]['inicio'] if S['l1'] + 1 < len(L) else 1e9) - tramo[-1]['fin']
    pre = S.get('pre', max(0.0, min(0.45, hueco_ini * 0.6)))
    post = S.get('post', max(0.05, min(0.65, hueco_fin * 0.6)))
    t0 = tramo[0]['inicio'] - pre
    t1 = tramo[-1]['fin'] + post
    dur = t1 - t0
    total = dur + CTA_DUR
    resaltar = set(x.lower() for x in S.get('resaltar', []))

    base = f"{S['id']}_{S['slug']}"
    d_tmp = os.path.join(tmp, base)
    os.makedirs(d_tmp, exist_ok=True)

    fondo_im, _ = fondo(S['hook'], S.get('rojo'))
    fondo_im.convert('RGB').save(os.path.join(d_tmp, 'fondo.png'))
    frente().save(os.path.join(d_tmp, 'frente.png'))

    cs = cues(tramo, t0)
    ent = ['-loop', '1', '-framerate', str(FPS), '-i', os.path.join(d_tmp, 'fondo.png'),
           '-ss', f'{t0:.3f}', '-t', f'{dur:.3f}', '-i', master,
           '-i', os.path.join(d_tmp, 'frente.png')]
    filtros = []
    # video del master: escalado, con el ultimo frame congelado para la tarjeta final
    filtros.append(f'[1:v]scale={VW}:{VH}:flags=lanczos,'
                   f'tpad=stop_mode=clone:stop_duration={CTA_DUR},setsar=1[vid]')
    filtros.append(f'[0:v][vid]overlay={VX}:{VY}[c0]')
    filtros.append(f'[c0][2:v]overlay=0:0[c1]')
    idx = 3
    prev = 'c1'
    for i, c in enumerate(cs):
        p = banda_sub(c['lineas'], resaltar)
        f = os.path.join(d_tmp, f'sub_{i:03d}.png')
        p.save(f)
        ent += ['-i', f]
        x = (W - p.width) // 2
        y = SUB_Y - p.height // 2
        filtros.append(f"[{prev}][{idx}:v]overlay={x}:{y}:"
                       f"enable='between(t,{c['t0']:.3f},{c['t1']:.3f})'[s{i}]")
        prev = f's{i}'
        idx += 1
    # tarjeta final con pop
    cta = tarjeta_cta()
    pops = [(0.86, 0.10), (1.06, 0.10), (1.0, CTA_DUR)]
    tacc = dur
    for j, (esc, d_) in enumerate(pops):
        pc = cta.resize((int(cta.width * esc), int(cta.height * esc)), Image.LANCZOS)
        f = os.path.join(d_tmp, f'cta_{j}.png')
        pc.save(f)
        ent += ['-i', f]
        x = VX + (VW - pc.width) // 2
        y = VY + (VH - pc.height) // 2
        fin = min(total, tacc + d_)
        filtros.append(f"[{prev}][{idx}:v]overlay={x}:{y}:"
                       f"enable='between(t,{tacc:.3f},{fin:.3f})'[k{j}]")
        prev = f'k{j}'
        idx += 1
        tacc = fin
    # barra de progreso (siempre algo vivo en pantalla)
    filtros.append(f"[{prev}]drawbox=x={VX}:y={VY + VH}:w='{VW}*t/{total:.3f}':h=9:"
                   f"color=0x{OCRE[0]:02x}{OCRE[1]:02x}{OCRE[2]:02x}@0.95:t=fill[vout]")
    # audio
    fade_in = min(0.30, max(0.06, pre))
    filtros.append(f'[1:a]afade=t=in:st=0:d={fade_in:.2f},apad=pad_dur={CTA_DUR},'
                   f'afade=t=out:st={total - 1.1:.3f}:d=1.1,'
                   f'loudnorm=I=-14:TP=-1.5:LRA=11[aout]')

    if solo_frame:
        # un frame de control a 1/3 del recorrido (verificacion de encuadre antes de renderizar)
        tf = dur * 0.33
        cfil = [f_ for f_ in filtros if not f_.startswith('[1:a]')]
        out = os.path.join(out_dir, f'_frame_{base}.jpg')
        ffmpeg(ent + ['-filter_complex', ';'.join(cfil), '-map', '[vout]',
                      '-ss', f'{tf:.3f}', '-frames:v', '1', '-q:v', '3', out])
        return out

    out = os.path.join(out_dir, f'{base}.mp4')
    ffmpeg(ent + ['-filter_complex', ';'.join(filtros),
                  '-map', '[vout]', '-map', '[aout]',
                  '-t', f'{total:.3f}', '-r', str(FPS),
                  '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
                  '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out])
    return out


def publicar_md(ep, cfg, out_dir):
    """Fichas listas para pegar en YouTube Studio, en el orden de publicacion."""
    T = json.load(open(os.path.join(AQUI, cfg['tiempos']), encoding='utf-8'))
    L = T['lineas']
    shorts = sorted(cfg['shorts'], key=lambda s: s.get('orden', 99))
    out = [f"# Shorts de `{ep}` — fichas para subir\n",
           f"> Generado por `produccion/shorts.py {ep} --md`. No editar a mano: se regenera.",
           f"> Episodio: **{cfg['titulo_episodio']}**. Estrategia y metodo en `canal/SHORTS.md`.\n"]
    for i, S in enumerate(shorts, 1):
        tr = L[S['l0']:S['l1'] + 1]
        dur = tr[-1]['fin'] - tr[0]['inicio'] + 1.1 + CTA_DUR
        mm = lambda t: f"{int(t // 60)}:{t % 60:04.1f}"
        tags = ' '.join('#' + t.replace(' ', '') for t in S['tags'][:3])
        out += [f"## {i}. `{S['id']}_{S['slug']}.mp4` — {dur:.0f} s",
                f"*Del episodio {mm(tr[0]['inicio'])}–{mm(tr[-1]['fin'])} (lineas {S['l0']}–{S['l1']}).* {S['por_que']}\n",
                "**Titulo**", "```", S['titulo'], "```",
                "**Descripcion**", "```", S['desc'] + '\n\n' + tags, "```",
                f"**En pantalla:** {' / '.join(S['hook'])}\n"]
    p = os.path.join(out_dir, 'PUBLICAR.md')
    open(p, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('fichas:', p)


# ---------------------------------------------------------------- plan de subida
SALTO = chr(10)
MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sept', 'oct', 'nov', 'dic']
FRANJAS = ['13:00', '18:00', '21:00', '15:00', '19:30', '11:00', '16:30', '20:00']


def _hora_ui(hhmm):
    """'13:00' -> '1:00 p.m.' (formato exacto del selector de YouTube, multiplos de 15 min)."""
    h, m = (int(x) for x in hhmm.split(':'))
    m = (m // 15) * 15
    suf = 'a.m.' if h < 12 else 'p.m.'
    h12 = h % 12 or 12
    return f'{h12}:{m:02d} {suf}'


def _fecha_ui(d):
    return f'{d.day} {MESES[d.month - 1]} {d.year}'


def plan_subida(ep, cfg, out_dir, reparto, desde, horas, url_ep, ahora):
    """Prepara _up/ (<10 MB) y PLAN_SUBIDA.json con fecha y hora ya resueltas para el formulario."""
    import datetime, subprocess
    up = os.path.join(out_dir, '_up')
    os.makedirs(up, exist_ok=True)
    shorts = sorted(cfg['shorts'], key=lambda s: s.get('orden', 99))
    reparto = [int(x) for x in reparto.split(',')] if reparto else [len(shorts)]
    horas = horas.split(',') if horas else FRANJAS
    if sum(reparto) != len(shorts):
        raise SystemExit(f'el reparto suma {sum(reparto)} y hay {len(shorts)} shorts')

    plan, i = [], 0
    for dia, n in enumerate(reparto):
        if n > len(horas):
            raise SystemExit(f'{n} shorts en un dia pero solo {len(horas)} franjas horarias')
        fecha = desde + datetime.timedelta(days=dia)
        hoy = sorted(horas[:n], key=lambda h: (int(h.split(':')[0]), int(h.split(':')[1])))
        for k in range(n):
            S = shorts[i]; i += 1
            hh, mm = (int(x) for x in hoy[k].split(':'))
            cuando = datetime.datetime.combine(fecha, datetime.time(hh, (mm // 15) * 15))
            src = os.path.join(out_dir, f"{S['id']}_{S['slug']}.mp4")
            dst = os.path.join(up, os.path.basename(src))
            if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
                if os.path.getsize(src) > 9_000_000:   # el navegador no sube mas de 10 MB por archivo
                    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', src,
                                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '25', '-pix_fmt', 'yuv420p',
                                    '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', dst], check=True)
                else:
                    shutil.copyfile(src, dst)
            tags = ' '.join('#' + t.replace(' ', '') for t in S['tags'][:3])
            plan.append({
                'id': S['id'], 'slug': S['slug'], 'archivo': dst,
                'mb': round(os.path.getsize(dst) / 1048576, 1),
                'titulo': S['titulo'],
                'descripcion': S['desc'] + (SALTO + SALTO + url_ep if url_ep else '') + SALTO + SALTO + tags,
                'fecha_ui': _fecha_ui(cuando), 'hora_ui': _hora_ui(hoy[k]),
                'publicar_ya': cuando <= ahora,
            })
    p = os.path.join(out_dir, 'PLAN_SUBIDA.json')
    json.dump({'episodio': ep, 'titulo_episodio': cfg['titulo_episodio'], 'url_episodio': url_ep,
               'generado': ahora.isoformat(timespec='minutes'), 'shorts': plan},
              open(p, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    for x in plan:
        marca = 'PUBLICAR YA' if x['publicar_ya'] else f"{x['fecha_ui']} {x['hora_ui']}"
        print(f"  {x['id']} {x['slug']:<14} {x['mb']:4.1f} MB  {marca:<24} {x['titulo'][:44]}")
    print('plan:', p)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    ep = sys.argv[1]
    ids = [a for a in sys.argv[2:] if not a.startswith('--')]
    check = '--check' in sys.argv
    solo_md = '--md' in sys.argv
    arg = lambda n, d=None: (sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d)
    cfg = json.load(open(os.path.join(RAIZ, 'guiones', ep, 'shorts.json'), encoding='utf-8'))
    out_dir = os.path.join(AQUI, 'shorts', ep)
    os.makedirs(out_dir, exist_ok=True)
    tmp = os.path.join(AQUI, '_shorts_tmp')
    os.makedirs(tmp, exist_ok=True)

    if solo_md:
        publicar_md(ep, cfg, out_dir)
        return

    if '--plan' in sys.argv:
        import datetime
        ahora = datetime.datetime.now()
        d = arg('--desde')
        desde = datetime.date.fromisoformat(d) if d else ahora.date()
        plan_subida(ep, cfg, out_dir, arg('--plan'), desde, arg('--horas'),
                    arg('--ep-url', cfg.get('url_episodio')), ahora)
        return

    lista = [s for s in cfg['shorts'] if not ids or s['id'] in ids]
    hechos = []
    for S in lista:
        T = json.load(open(os.path.join(AQUI, cfg['tiempos']), encoding='utf-8'))
        tr = T['lineas'][S['l0']:S['l1'] + 1]
        d = tr[-1]['fin'] - tr[0]['inicio'] + 1.1 + CTA_DUR
        print(f"  {S['id']} {S['slug']:<16} {d:5.1f}s  {' / '.join(S['hook'])}")
        hechos.append(construir(ep, cfg, S, tmp, out_dir, solo_frame=check))

    if check:
        n = len(hechos)
        cols = min(5, n)
        filas = math.ceil(n / cols)
        tw, th = 300, 533
        g = Image.new('RGB', (cols * tw, filas * th), (18, 14, 10))
        for i, f in enumerate(hechos):
            g.paste(Image.open(f).resize((tw, th), Image.LANCZOS), ((i % cols) * tw, (i // cols) * th))
        hoja = os.path.join(out_dir, '_hoja.jpg')
        g.save(hoja, quality=90)
        print('hoja:', hoja)
    else:
        shutil.rmtree(tmp, ignore_errors=True)
        publicar_md(ep, cfg, out_dir)
        print('listos en', out_dir)


if __name__ == '__main__':
    main()
