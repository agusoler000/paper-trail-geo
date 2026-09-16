"""Valida una entrega completa y escribe SUBIR.md; nunca sube ni programa nada."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlparse

from PIL import Image


VERSION = 1
MAX_THUMB_BYTES = 2 * 1024 * 1024
DOCS = {
    "Titulos y descripcion": "https://support.google.com/youtube/answer/57404?hl=en",
    "Miniaturas": "https://support.google.com/youtube/answer/72431?hl=en",
    "Capitulos": "https://support.google.com/youtube/answer/9884579?hl=en",
    "Contenido sintetico": "https://support.google.com/youtube/answer/14328491?hl=en",
}
PLACEHOLDER = re.compile(r"\b(?:TODO|TBD|PLACEHOLDER)\b|\[(?:INSERT|ADD|LINK|URL|TITLE|DESCRIPTION)[^\]]*\]", re.I)
EMPTY = {"", "...", "pending", "pendiente", "n/a", "por definir"}
EMOTION = re.compile(r"^(?:FEAR|BOMBSHELL|PANIC|SHOCK|WARNING|COLLAPSE|EXPOSED|BETRAYAL|SECRET|ALERT|HUMILIATION|REVENGE):", re.I)


def sha256(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def local_path(base, value, must_exist=True):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Falta una ruta local relativa a la produccion.")
    base = Path(base).resolve()
    given = Path(value)
    if given.is_absolute():
        raise ValueError("Las rutas del paquete deben ser relativas a la produccion.")
    path = (base / given).resolve()
    if not path.is_relative_to(base) or path == base:
        raise ValueError("La ruta sale de la produccion.")
    if must_exist and (not path.is_file() or not path.stat().st_size):
        raise ValueError("Falta archivo no vacio: " + str(path))
    return path


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(r"(?:\d{1,3}:)?\d{2}:\d{2}", value):
        raise ValueError("Usar MM:SS o H:MM:SS.")
    parts = [int(part) for part in value.split(":")]
    if parts[-1] >= 60 or (len(parts) == 3 and parts[-2] >= 60):
        raise ValueError("Segundos/minutos fuera de rango.")
    total = 0
    for part in parts:
        total = total * 60 + part
    return total


def probe_master(path):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                            check=True, capture_output=True, text=True, encoding="utf-8", timeout=60)
    data = json.loads(result.stdout)
    video = next(stream for stream in data["streams"] if stream.get("codec_type") == "video")
    audio = any(stream.get("codec_type") == "audio" for stream in data["streams"])
    fps = float(Fraction(video["avg_frame_rate"]))
    duration = float(data.get("format", {}).get("duration") or video["duration"])
    return {"duration_s": duration, "width": int(video["width"]), "height": int(video["height"]),
            "fps": fps, "audio": audio}


def artifact_paths(manifest):
    """Referencias locales del contrato, para que el QC tambien cubra la entrega."""
    result = [manifest["master"]["path"]]
    result.extend(candidate["thumbnail_path"] for candidate in manifest["candidates"])
    return list(dict.fromkeys(result))


def validar(manifest, base_dir):
    errors, warnings = [], []
    artifacts = []

    def error(code, field, message):
        errors.append({"codigo": code, "ruta": field, "mensaje": message})

    def warning(code, field, message):
        warnings.append({"codigo": code, "ruta": field, "mensaje": message})

    def obj(value, field):
        if not isinstance(value, dict):
            error("TIPO", field, "Se esperaba un objeto.")
            return {}
        return value

    def text(value, field, limit=None):
        if not isinstance(value, str) or value.strip().casefold() in EMPTY or PLACEHOLDER.search(value):
            error("TEXTO_INCOMPLETO", field, "Falta texto definitivo; no se aceptan placeholders.")
            return False
        if limit is not None and len(value) > limit:
            error("LIMITE_TEXTO", field, f"Supera {limit} caracteres.")
            return False
        return True

    def file_record(value, field):
        try:
            path = local_path(base_dir, value)
            artifacts.append({"path": value, "sha256": sha256(path), "bytes": path.stat().st_size})
            return path
        except (ValueError, OSError) as exc:
            error("ARCHIVO", field, str(exc))
            return None

    data = obj(manifest, "paquete")
    if data.get("schema_version") != VERSION or data.get("format") not in ("largo", "short"):
        error("VERSION_FORMATO", "schema_version", "Usar schema_version=1 y format=largo o short.")
    vertical = data.get("format") == "short"
    master = obj(data.get("master"), "master")
    master_path = file_record(master.get("path"), "master.path")
    actual = None
    if master_path:
        if master.get("sha256") != artifacts[-1]["sha256"]:
            error("MASTER_HASH", "master.sha256", "El master no coincide con el SHA-256 declarado.")
        try:
            actual = probe_master(master_path)
            if not actual["audio"]:
                error("MASTER_AUDIO", "master", "El master no tiene pista de audio.")
            for key in ("width", "height"):
                if not finite(master.get(key)) or master[key] != actual[key]:
                    error("MASTER_MEDIDA", "master." + key, "No coincide con el archivo real.")
            min_w, min_h = (1080, 1920) if vertical else (1920, 1080)
            if actual["width"] < min_w or actual["height"] < min_h or actual["width"] * min_h != actual["height"] * min_w:
                error("MASTER_PERFIL", "master", f"Perfil del proyecto: proporcion {min_w}:{min_h}, al menos {min_w}x{min_h}; no prueba render nativo.")
            if not finite(master.get("fps")) or abs(master["fps"] - actual["fps"]) > .01:
                error("MASTER_FPS", "master.fps", "No coincide con la cadencia real.")
            if not finite(master.get("duration_s")) or abs(master["duration_s"] - actual["duration_s"]) > .1:
                error("MASTER_DURACION", "master.duration_s", "No coincide con la duracion real.")
            if not finite(actual["duration_s"]) or actual["duration_s"] <= 0 or not finite(actual["fps"]) or actual["fps"] <= 0:
                error("MASTER_INVALIDO", "master", "Duracion o cadencia no valida.")
        except (OSError, ValueError, KeyError, StopIteration, ZeroDivisionError, subprocess.SubprocessError) as exc:
            error("FFPROBE", "master", "No se pudo verificar el video: " + str(exc))

    description = data.get("description")
    description_ok = text(description, "description", 5000)
    desc_tags = re.findall(r"#[\w]+", description or "") if isinstance(description, str) else []
    if len(desc_tags) != 3:
        error("HASHTAGS", "description", "La descripcion lleva tres hashtags, iguales a los titulos (CANAL 7.1).")
    candidates = data.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 3:
        error("TRES_CANDIDATOS", "candidates", "Entregar exactamente tres parejas de titulo y miniatura.")
        candidates = candidates if isinstance(candidates, list) else []
    ids, titles, pixel_hashes = [], [], []
    for i, raw in enumerate(candidates):
        prefix = f"candidates[{i}]"
        candidate = obj(raw, prefix)
        identity = candidate.get("id")
        if identity not in ("A", "B", "C"):
            error("CANDIDATO_ID", prefix + ".id", "Usar A, B o C.")
        ids.append(identity)
        title = candidate.get("title")
        if text(title, prefix + ".title", 100):
            titles.append(" ".join(title.casefold().split()))
            title_tags = re.findall(r"#[\w]+", title)
            body = re.sub(r"#[\w]+", "", title).strip()
            question, separator, sentence = body.partition("?")
            if not separator or not question.strip() or not sentence.strip() or EMOTION.match(title) or "\n" in title:
                error("TITULO_FORMULA", prefix + ".title", "Pregunta + oracion breve, sin prefijo emocional; CANAL 7.1.")
            if len(title_tags) != 3 or {tag.casefold() for tag in title_tags} != {tag.casefold() for tag in desc_tags}:
                error("TITULO_HASHTAGS", prefix + ".title", "Deben ser los mismos tres hashtags de la descripcion.")
        text(candidate.get("angle"), prefix + ".angle")
        text(candidate.get("why"), prefix + ".why")
        image_path = file_record(candidate.get("thumbnail_path"), prefix + ".thumbnail_path")
        if image_path:
            if image_path.stat().st_size > MAX_THUMB_BYTES:
                error("MINIATURA_PESO", prefix, "El perfil de entrega exige <=2 MiB para compatibilidad movil.")
            try:
                with Image.open(image_path) as im:
                    im.load()
                    width, height = im.size
                    if im.format not in ("JPEG", "PNG") or image_path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
                        error("MINIATURA_FORMATO", prefix, "Entregar JPG o PNG reales.")
                    min_w, min_h = (1080, 1920) if vertical else (1280, 720)
                    if width < min_w or height < min_h or width * min_h != height * min_w:
                        error("MINIATURA_MEDIDA", prefix, f"Perfil del proyecto: proporcion {min_w}:{min_h}, al menos {min_w}x{min_h}.")
                    pixel_hashes.append(hashlib.sha256(im.convert("RGB").tobytes()).hexdigest())
            except (OSError, ValueError) as exc:
                error("MINIATURA_INVALIDA", prefix, str(exc))
    if sorted(identity for identity in ids if isinstance(identity, str)) != ["A", "B", "C"]:
        error("CANDIDATO_ID", "candidates", "A, B y C deben aparecer una sola vez.")
    if len(titles) != len(set(titles)):
        error("TITULOS_REPETIDOS", "candidates", "Los tres titulos deben ser distintos.")
    if len(pixel_hashes) != len(set(pixel_hashes)):
        error("MINIATURAS_REPETIDAS", "candidates", "No basta renombrar o cambiar metadatos: las imagenes deben ser distintas.")
    if data.get("recommended") not in ("A", "B", "C"):
        error("RECOMENDADO", "recommended", "Elegir uno de los tres candidatos.")

    tags = data.get("tags")
    if not isinstance(tags, list) or not tags or any(not isinstance(tag, str) or not tag.strip() for tag in tags):
        error("ETIQUETAS", "tags", "Faltan etiquetas concretas.")
    else:
        for i, tag in enumerate(tags):
            text(tag, f"tags[{i}]")
            if "," in tag or "\n" in tag:
                error("ETIQUETA_SEPARADOR", f"tags[{i}]", "Una etiqueta por elemento, sin comas ni saltos.")
        count = len(",".join(tags)) + sum(2 for tag in tags if " " in tag)
        if count > 500:
            error("ETIQUETAS_LIMITE", "tags", "Supera 500 caracteres contando separadores y comillas para frases.")
    if text(data.get("pinned_comment"), "pinned_comment") and "?" not in data["pinned_comment"]:
        error("COMENTARIO_PREGUNTA", "pinned_comment", "Incluir una pregunta concreta para comentarios.")

    chapters = data.get("chapters", [] if vertical else None)
    if not isinstance(chapters, list) or ((not vertical or chapters) and len(chapters) < 3):
        error("CAPITULOS_CANTIDAD", "chapters", "YouTube exige al menos tres capitulos.")
        chapters = chapters if isinstance(chapters, list) else []
    times = []
    for i, raw in enumerate(chapters):
        chapter = obj(raw, f"chapters[{i}]")
        text(chapter.get("title"), f"chapters[{i}].title")
        try:
            seconds = timestamp(chapter.get("time"))
            times.append(seconds)
            if i == 0 and chapter["time"] != "00:00":
                error("CAPITULOS_CERO", "chapters[0].time", "El primer capitulo debe ser 00:00.")
            expected = chapter["time"] + " " + str(chapter.get("title", ""))
            if description_ok and expected not in [line.strip() for line in description.splitlines()]:
                error("CAPITULOS_DESCRIPCION", f"chapters[{i}]", "Falta la misma linea de capitulo en la descripcion literal.")
        except ValueError as exc:
            error("CAPITULO_TIEMPO", f"chapters[{i}].time", str(exc))
    duration = actual["duration_s"] if actual else master.get("duration_s")
    if times:
        ends = times[1:] + ([duration] if finite(duration) else [])
        if len(ends) != len(times) or any(end - start < 10 for start, end in zip(times, ends)):
            error("CAPITULOS_TRAMOS", "chapters", "Capitulos ordenados, dentro del master y de al menos 10 s, incluido el ultimo.")

    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        error("FUENTES", "sources", "Faltan fuentes publicas para la ficha.")
    else:
        for i, raw in enumerate(sources):
            source = obj(raw, f"sources[{i}]")
            text(source.get("label"), f"sources[{i}].label")
            url = source.get("url")
            if not isinstance(url, str) or urlparse(url).scheme not in ("https", "http") or not urlparse(url).netloc:
                error("FUENTE_URL", f"sources[{i}].url", "Se necesita una URL publica real, no una ruta local.")
            elif description_ok and url not in description:
                warning("FUENTE_DESCRIPCION", f"sources[{i}]", "Verificar enlace en descripcion o sourcesheet publica.")
    settings = obj(data.get("settings"), "settings")
    for key, expected in (("visibility", "private"), ("category", "Education"), ("language", "en"), ("made_for_kids", False)):
        if settings.get(key) != expected or (key == "made_for_kids" and settings.get(key) is not False):
            error("AJUSTE", "settings." + key, f"El perfil de entrega requiere {expected!r}.")
    if settings.get("publish_at", "absent") is not None:
        error("SIN_CALENDARIO", "settings.publish_at", "Debe ser null; fecha y cantidad las decide Agustin.")
    altered = obj(settings.get("altered_content"), "settings.altered_content")
    if altered.get("decision") not in ("yes", "no", "review"):
        error("CONTENIDO_SINTETICO", "settings.altered_content.decision", "Indicar yes, no o review con justificacion.")
    text(altered.get("reason"), "settings.altered_content.reason")
    if altered.get("decision") == "review":
        warning("CONTENIDO_REVISAR", "settings.altered_content", "Resolver antes de subir. La musica sintetica requiere revision especifica.")
    policy = obj(data.get("policy"), "policy")
    if policy.get("no_auto_publish") is not True or policy.get("manual_schedule") is not True:
        error("PUBLICACION_HUMANA", "policy", "No permitir subida o calendario automaticos.")
    qc = obj(data.get("qc"), "qc")
    if qc.get("status") not in ("pending", "approved", "rejected") or not isinstance(qc.get("notes"), list):
        error("QC", "qc", "Registrar estado y notas; el validador no aprueba por Agustin.")
    warning("QC_VISUAL", "candidates", "Revisar a 320 px: legibilidad, misma promesa, bandera, contraste y tres composiciones realmente diferentes.")
    return {"ok": not errors, "errores": errors, "advertencias": warnings, "artifacts": artifacts,
            "ready_for_human_qc": not errors, "publish_allowed": False, "human_review_required": True}


def markdown(manifest, base_dir):
    """Texto de entrega determinista; no cambia ni completa contenido editorial."""
    master = manifest["master"]
    lines = ["# SUBIR - " + ("Entrega Del Short" if manifest["format"] == "short" else "Entrega Del Largo"), "", "**Estado: revision humana. No subido ni programado.**", "",
             "Agustin decide la variante, cantidad y momento. Esta ficha no autoriza una publicacion.", "",
             "## Archivo Final", "", f"- Master: `{local_path(base_dir, master['path'])}`",
             f"- SHA-256: `{master['sha256']}`",
             f"- Duracion: {master['duration_s']} s; {master['width']}x{master['height']}; {master['fps']} fps.",
             "- Recomendacion editorial: " + manifest["recommended"] + " (no es una medicion de rendimiento).", "",
             "## Tres Opciones", ""]
    for candidate in manifest["candidates"]:
        thumb = local_path(base_dir, candidate["thumbnail_path"])
        lines.extend(["### " + candidate["id"], "", "```text", candidate["title"], "```", "",
                      f"Miniatura: `{thumb}`", "", f"![Miniatura {candidate['id']}]({thumb.as_posix()})", "",
                      "Angulo: " + candidate["angle"], "", "Criterio: " + candidate["why"], ""])
    lines.extend(["## Descripcion Completa", "", "```text", manifest["description"], "```", "",
                  "## Etiquetas", "", "```text", ",".join(manifest["tags"]), "```", "",
                  "## Comentario Fijado", "", "```text", manifest["pinned_comment"], "```", "",
                  "## Ajustes De Studio", "", "```json", json.dumps(manifest["settings"], indent=2, ensure_ascii=False), "```", "",
                  "No usar un No automatico para contenido sintetico: revisar tambien musica y voz segun la politica vigente.", "",
                  "## Fuentes", ""])
    lines.extend(f"- [{source['label']}]({source['url']})" for source in manifest["sources"])
    lines.extend(["", "## QC Humano", "", "Estado declarado: " + manifest["qc"]["status"], "",
                  "- [ ] Ver y escuchar el master final, incluida apertura y ultima palabra.",
                  "- [ ] Revisar las tres miniaturas a 320 px y elegir titulo/miniatura coherentes.",
                  "- [ ] Comprobar fuentes, capitulos, cifras, subtitulos, derechos y declaracion sintetica.",
                  "- [ ] Confirmar subtitulos, pantalla final, tarjetas, playlist y moderacion en Studio.",
                  "- [ ] Agustin decide si se sube; comenzar privado, sin fecha programada por el sistema.", ""])
    lines.extend("- " + str(note) for note in manifest["qc"]["notes"])
    standard = {"schema_version", "format", "master", "candidates", "recommended", "description", "tags",
                "pinned_comment", "chapters", "settings", "sources", "policy", "qc"}
    extra = {key: value for key, value in manifest.items() if key not in standard}
    if extra:
        lines.extend(["", "## Notas Adicionales", "", "```json", json.dumps(extra, indent=2, ensure_ascii=False), "```"])
    lines.extend(["", "## Referencias Del Estandar", "", "Regla editorial: `canal/CANAL.md` 7.1.", ""])
    lines.extend(f"- [{name}]({url})" for name, url in DOCS.items())
    return "\n".join(lines) + "\n"


def renderizar(manifest_path, base_dir, salida="SUBIR.md", actualizar=False):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8-sig"))
    result = validar(manifest, base_dir)
    if not result["ok"]:
        return result
    destination = local_path(base_dir, salida, must_exist=False)
    content = markdown(manifest, base_dir).encode("utf-8")
    destination.parent.mkdir(parents=True, exist_ok=True)
    previous = destination.read_bytes() if destination.exists() else None
    if previous == content:
        return {**result, "output": str(destination), "changed": False, "backup": None}
    if previous is not None and not actualizar:
        raise ValueError("SUBIR.md ya existe. Se conserva; usar --actualizar para versionar y reemplazar explicitamente.")
    backup = None
    if previous is not None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
        folder = destination.parent / ".versiones_subida"
        if not folder.resolve().is_relative_to(Path(base_dir).resolve()):
            raise ValueError("El directorio de versiones sale de la produccion.")
        folder.mkdir(exist_ok=True)
        backup = folder / f"{destination.stem}_{stamp}_{hashlib.sha256(previous).hexdigest()[:12]}.md"
        shutil.copy2(destination, backup)
        if backup.read_bytes() != previous:
            raise ValueError("No se pudo verificar la copia anterior. Se conserva el original.")
    fd, temp = tempfile.mkstemp(prefix=".subir-", suffix=".tmp", dir=destination.parent)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(content)
        if (destination.read_bytes() if destination.exists() else None) != previous:
            raise ValueError("SUBIR.md cambio durante la escritura; no se reemplaza.")
        os.replace(temp, destination)
    finally:
        Path(temp).unlink(missing_ok=True)
    return {**result, "output": str(destination), "changed": True, "backup": str(backup) if backup else None}


def main(argv=None):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from radar.entorno import cargar
    cargar()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--salida", default="SUBIR.md")
    parser.add_argument("--actualizar", action="store_true")
    parser.add_argument("--validar", action="store_true", help="Solo validar, sin escribir SUBIR.md.")
    args = parser.parse_args(argv)
    try:
        result = (validar(json.loads(args.manifest.read_text(encoding="utf-8-sig")), args.base) if args.validar
                  else renderizar(args.manifest, args.base, args.salida, args.actualizar))
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 0 if result["ok"] else 2
    except (ValueError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc), "publish_allowed": False}, ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
