"""Versiones locales de animacion: copias independientes, verificadas y restaurables."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile


RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from radar.entorno import cargar


SELECCION = (
    "produccion", "videos/09_deuda_eeuu", "pruebas/elenco", "fuentes/mapas",
    "voz", ".gitignore", "AGENTS.md", "README.md",
)
DIRS_EXCLUIDOS = {"__pycache__", ".git", ".venv", "venv", "node_modules"}
EXT_MODELOS = {".onnx", ".safetensors", ".pt", ".pth", ".ckpt", ".gguf", ".bin"}
EXT_VOZ = {".py", ".json", ".toml", ".yaml", ".yml", ".ini", ".cfg", ".txt",
           ".md", ".ps1", ".sh", ".bat", ".cmd"}
POLITICA = {
    "seleccion": list(SELECCION),
    "excluye": ["_frames*", "__pycache__", ".git", ".venv", "venv", "node_modules",
                "*.log", "*.pyc", "*.pyo", "modelos binarios", "enlaces/reparse points",
                ".env*", "credenciales/tokens/secretos/cookies por nombre", "*.pem", "*.key"],
    "voz": "Solo codigo y configuracion (no audio ni modelos).",
    "copias": "Archivos independientes; sin enlaces duros. Incluye archivos no registrados en git.",
}
BLOQUE = 4 * 1024 * 1024


def utc():
    return datetime.now(timezone.utc).isoformat()


def sello():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")


def es_enlace(ruta):
    estado = ruta.lstat()
    return ruta.is_symlink() or bool(getattr(estado, "st_file_attributes", 0) & 0x400)


def excluido(ruta, relativo, directorio=False):
    nombre = ruta.name.lower()
    if nombre.startswith(".env") or re.search(
        r"(^|[_\-.])(token|tokens|credential|credentials|secret|secrets|cookie|cookies)([_\-.]|$)",
        nombre,
    ):
        return True
    if directorio:
        return nombre in DIRS_EXCLUIDOS or nombre.startswith("_frames")
    extension = ruta.suffix.lower()
    if extension in EXT_MODELOS | {".log", ".pyc", ".pyo", ".pem", ".key"}:
        return True
    return relativo.parts[0] == "voz" and extension not in EXT_VOZ


def estado_archivo(ruta):
    st = ruta.stat()
    return (st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def inventario(raiz):
    archivos = {}
    for seleccion in SELECCION:
        base = raiz / seleccion
        if not base.exists():
            continue
        if es_enlace(base):
            continue
        if base.is_file():
            archivos[base.relative_to(raiz).as_posix()] = estado_archivo(base)
            continue
        for actual, carpetas, nombres in os.walk(base, followlinks=False):
            actual = Path(actual)
            carpetas[:] = sorted(
                nombre for nombre in carpetas
                if not es_enlace(actual / nombre)
                and not excluido(actual / nombre, (actual / nombre).relative_to(raiz), True)
            )
            for nombre in sorted(nombres):
                ruta = actual / nombre
                relativo = ruta.relative_to(raiz)
                if not es_enlace(ruta) and not excluido(ruta, relativo):
                    archivos[relativo.as_posix()] = estado_archivo(ruta)
    return archivos


def sha256(ruta):
    digest = hashlib.sha256()
    with ruta.open("rb") as entrada:
        while bloque := entrada.read(BLOQUE):
            digest.update(bloque)
    return digest.hexdigest()


def copiar_verificado(origen, destino, esperado):
    destino.parent.mkdir(parents=True, exist_ok=True)
    for intento in range(3):
        antes = estado_archivo(origen)
        if antes != esperado:
            raise RuntimeError(f"El origen cambio durante la copia: {origen}")
        digest = hashlib.sha256()
        with origen.open("rb") as entrada, destino.open("wb") as salida:
            while bloque := entrada.read(BLOQUE):
                digest.update(bloque)
                salida.write(bloque)
            salida.flush()
            os.fsync(salida.fileno())
        despues = estado_archivo(origen)
        if antes != despues:
            raise RuntimeError(f"El origen cambio al copiarlo: {origen}")
        checksum = digest.hexdigest()
        if destino.stat().st_size == antes[0] and sha256(destino) == checksum:
            shutil.copystat(origen, destino)
            return checksum
    raise RuntimeError(f"No se pudo verificar la copia despues de 3 intentos: {destino}")


def dentro(ruta, contenedor):
    return ruta == contenedor or contenedor in ruta.parents


def documentar(carpeta, respaldo):
    instrucciones = f"""# Versiones locales de animacion

Esta es una copia independiente del motor y del episodio 09, incluidos sus assets,
voz de episodio, masters y la muestra aprobada. No es un clon completo del proyecto.
No se modifico ni publico el master. Las rutas se conservan dentro de `archivos/`.
`manifest.json` contiene el origen, fecha UTC, exclusiones y SHA-256 por archivo.
No incluye credenciales, modelos descargables, logs ni fotogramas intermedios.

## Verificar esta version

Desde el proyecto:

```powershell
python produccion/versiones_animacion.py verify "{respaldo}"
```

## Recuperar sin pisar tu trabajo

```powershell
python produccion/versiones_animacion.py restore "{respaldo}"
```

El comando verifica todo y recupera los archivos en una carpeta NUEVA junto a esta
version. Nunca borra ni reemplaza el proyecto actual. Tambien acepta `--destination`
con una ruta que todavia no exista. Para volver el motor atras, conserva primero
una nueva version del proyecto actual y luego recupera los archivos elegidos.

## Guardar otro punto de retorno

```powershell
python produccion/versiones_animacion.py create --label v1_aprobada
```

El directorio del backup esta fuera del repositorio; no se publica mediante git.
"""
    (carpeta / "RECUPERAR.md").write_text(instrucciones, encoding="utf-8")


def crear(raiz, carpeta, etiqueta):
    raiz = raiz.resolve()
    carpeta = carpeta.resolve()
    if dentro(carpeta, raiz):
        raise ValueError("El directorio de backups debe estar fuera del proyecto.")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", etiqueta):
        raise ValueError("La etiqueta solo acepta letras, numeros, guion, punto y guion bajo.")
    archivos = inventario(raiz)
    if not archivos:
        raise ValueError("No hay archivos seleccionados para respaldar.")
    total = sum(st[0] for st in archivos.values())
    carpeta.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(carpeta).free < total + 64 * 1024 * 1024:
        raise ValueError("No hay espacio libre suficiente para una copia independiente.")
    nombre = f"{sello()}_{etiqueta}"
    final = carpeta / nombre
    parcial = carpeta / (nombre + ".incompleto")
    parcial.mkdir()
    registros = []
    try:
        print(f"Copiando {len(archivos)} archivos ({total / 1024**3:.2f} GiB)...", flush=True)
        for relativo, estado in archivos.items():
            checksum = copiar_verificado(raiz / relativo, parcial / "archivos" / relativo, estado)
            registros.append({"path": relativo, "size": estado[0], "sha256": checksum,
                              "source_mtime_ns": estado[1]})
        if inventario(raiz) != archivos:
            raise RuntimeError("El conjunto de origen cambio durante la copia. Repetir create con el origen quieto.")
        manifiesto = {"schema": 1, "created_utc": utc(), "label": etiqueta,
                      "source_root": str(raiz), "exclusion_policy": POLITICA,
                      "file_count": len(registros), "total_bytes": total, "files": registros}
        (parcial / "manifest.json").write_text(json.dumps(manifiesto, indent=2), encoding="utf-8")
        documentar(parcial, final)
        parcial.rename(final)
        print(json.dumps({"backup": str(final), "files": len(registros), "bytes": total,
                          "sha256_verified": True}), flush=True)
        return final
    except Exception as exc:
        (parcial / "INCOMPLETO.txt").write_text(f"{utc()}\n{exc}\nNo restaurar esta copia.\n", encoding="utf-8")
        raise


def cargar_manifiesto(respaldo):
    respaldo = respaldo.resolve()
    manifiesto = json.loads((respaldo / "manifest.json").read_text(encoding="utf-8"))
    if manifiesto.get("schema") != 1:
        raise ValueError("Formato de manifiesto desconocido.")
    vistos = set()
    for registro in manifiesto["files"]:
        relativo = PurePosixPath(registro["path"])
        if relativo.is_absolute() or ".." in relativo.parts or not relativo.parts:
            raise ValueError("El manifiesto contiene una ruta no permitida.")
        if "\\" in registro["path"] or ":" in registro["path"]:
            raise ValueError("El manifiesto contiene una ruta no portatil.")
        normalizado = registro["path"].casefold()
        if normalizado in vistos:
            raise ValueError("El manifiesto contiene rutas duplicadas.")
        vistos.add(normalizado)
        archivo = (respaldo / "archivos" / registro["path"]).resolve()
        if not dentro(archivo, respaldo / "archivos"):
            raise ValueError("Una ruta sale de la carpeta del respaldo.")
    if len(vistos) != manifiesto["file_count"]:
        raise ValueError("El total del manifiesto no coincide.")
    if sum(item["size"] for item in manifiesto["files"]) != manifiesto["total_bytes"]:
        raise ValueError("El tamano total del manifiesto no coincide.")
    return manifiesto


def verificar(respaldo):
    manifiesto = cargar_manifiesto(respaldo)
    for registro in manifiesto["files"]:
        ruta = respaldo / "archivos" / registro["path"]
        if not ruta.is_file() or ruta.stat().st_size != registro["size"]:
            raise RuntimeError(f"Archivo ausente o tamano incorrecto: {registro['path']}")
        if sha256(ruta) != registro["sha256"]:
            raise RuntimeError(f"SHA-256 incorrecto: {registro['path']}")
    print(f"VERIFICADO: {manifiesto['file_count']} archivos; {manifiesto['total_bytes']} bytes.", flush=True)
    return manifiesto


def restaurar(respaldo, destino=None):
    respaldo = respaldo.resolve()
    manifiesto = verificar(respaldo)
    destino = (destino or respaldo.parent / (respaldo.name + "_recuperado_" + sello())).resolve()
    origen = Path(manifiesto["source_root"]).resolve()
    if destino.exists() or dentro(destino, origen) or dentro(destino, respaldo):
        raise ValueError("Restaurar requiere una carpeta nueva fuera del proyecto y del respaldo.")
    destino.mkdir(parents=True)
    for registro in manifiesto["files"]:
        fuente = respaldo / "archivos" / registro["path"]
        checksum = copiar_verificado(fuente, destino / registro["path"], estado_archivo(fuente))
        if checksum != registro["sha256"]:
            raise RuntimeError(f"El respaldo cambio durante la restauracion: {registro['path']}")
    print(json.dumps({"restored": str(destino), "files": manifiesto["file_count"]}), flush=True)
    return destino


def autotest():
    with tempfile.TemporaryDirectory(prefix="papertrail_versiones_") as temporal:
        base = Path(temporal)
        origen = base / "proyecto"
        (origen / "produccion" / "_frames_prueba").mkdir(parents=True)
        (origen / "produccion" / "motor.py").write_text("codigo", encoding="utf-8")
        (origen / "produccion" / "_frames_prueba" / "001.png").write_bytes(b"frame")
        (origen / "produccion" / "token.json").write_text("secreto", encoding="utf-8")
        (origen / "produccion" / ".env").write_text("secreto", encoding="utf-8")
        version = crear(origen, base / "backups", "prueba")
        assert verificar(version)["file_count"] == 1
        recuperado = restaurar(version)
        assert (recuperado / "produccion" / "motor.py").read_text() == "codigo"
        try:
            restaurar(version, recuperado)
        except ValueError:
            pass
        else:
            raise AssertionError("Debe rechazar destinos existentes")
        (version / "archivos" / "produccion" / "motor.py").write_text("roto!!", encoding="utf-8")
        try:
            verificar(version)
        except RuntimeError:
            pass
        else:
            raise AssertionError("Debe detectar corrupcion")
    print("AUTOTEST OK: copia, exclusiones, restauracion, no sobreescritura y corrupcion.")


def main():
    cargar()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--autotest", action="store_true")
    comandos = parser.add_subparsers(dest="command")
    nuevo = comandos.add_parser("create", help="Crear una copia independiente fuera del repositorio")
    nuevo.add_argument("--label", required=True)
    nuevo.add_argument("--backup-dir", type=Path, default=RAIZ.parent / (RAIZ.name + "_backups"))
    chequeo = comandos.add_parser("verify", help="Verificar todos los SHA-256 de una version")
    chequeo.add_argument("backup", type=Path)
    recuperar = comandos.add_parser("restore", help="Restaurar en una carpeta nueva; nunca sobrescribe")
    recuperar.add_argument("backup", type=Path)
    recuperar.add_argument("--destination", type=Path)
    args = parser.parse_args()
    try:
        if args.autotest:
            autotest()
        elif args.command == "create":
            crear(RAIZ, args.backup_dir, args.label)
        elif args.command == "verify":
            verificar(args.backup)
        elif args.command == "restore":
            restaurar(args.backup, args.destination)
        else:
            parser.error("Indicar create, verify, restore o --autotest")
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
