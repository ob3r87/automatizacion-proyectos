"""
Escanea proyectos_generados/ para descubrir proyectos existentes.
"""
import json
import re
import time
from pathlib import Path

PROJECT_RE = re.compile(r"PH\.(\d+)-(\d{4})$")
REVISION_RE = re.compile(r"Rev(\d+)$")

_cache = {"data": None, "ts": 0}
CACHE_TTL = 60  # segundos


def _load_config():
    config_path = Path(__file__).parent.parent / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _get_output_dir():
    cfg = _load_config()
    output = cfg.get("OUTPUT_PATH", "")
    if output and Path(output).is_dir():
        return Path(output)
    return Path(__file__).parent.parent / "proyectos_generados"


def scan_projects(force=False):
    now = time.time()
    if not force and _cache["data"] is not None and (now - _cache["ts"]) < CACHE_TTL:
        return _cache["data"]

    output_dir = _get_output_dir()
    projects = []

    if not output_dir.is_dir():
        return projects

    for folder in sorted(output_dir.iterdir(), reverse=True):
        if not folder.is_dir():
            continue
        m = PROJECT_RE.match(folder.name)
        if not m:
            continue

        revisions = []
        client = ""
        matricula = ""
        marca = ""
        modelo = ""
        reformas = []

        for rev_folder in sorted(folder.iterdir(), reverse=True):
            if not rev_folder.is_dir():
                continue
            rm = REVISION_RE.match(rev_folder.name)
            if not rm:
                continue
            revisions.append(rev_folder.name)

            datos_path = rev_folder / "datos.json"
            if datos_path.exists() and not client:
                try:
                    with open(datos_path, "r", encoding="utf-8") as f:
                        datos = json.load(f)
                    nombre = datos.get("PETICIONARIO_NOMBRE", "")
                    apellidos = datos.get("PETICIONARIO_APELLIDOS", "")
                    client = f"{nombre} {apellidos}".strip()
                    matricula = datos.get("MATRICULA", "")
                    marca = datos.get("MARCA", "")
                    modelo = datos.get("MODELO", "")
                    for ref in datos.get("REFORMAS", []):
                        code = ref.get("CODIGO", "")
                        if code:
                            reformas.append(code)
                except (json.JSONDecodeError, OSError):
                    pass

        if revisions:
            projects.append({
                "ref": folder.name,
                "revisions": revisions,
                "client": client,
                "matricula": matricula,
                "marca": marca,
                "modelo": modelo,
                "reformas": reformas,
                "path": str(folder),
            })

    _cache["data"] = projects
    _cache["ts"] = now
    return projects


def get_project_files(ref, revision=None):
    output_dir = _get_output_dir()
    project_dir = output_dir / ref
    if not project_dir.is_dir():
        return []

    files = []
    search_dirs = []

    if revision:
        rev_dir = project_dir / revision
        if rev_dir.is_dir():
            search_dirs.append(rev_dir)
    else:
        for d in sorted(project_dir.iterdir(), reverse=True):
            if d.is_dir() and REVISION_RE.match(d.name):
                search_dirs.append(d)

    for d in search_dirs:
        for f in sorted(d.iterdir()):
            if f.is_file():
                files.append({
                    "name": f.name,
                    "path": str(f),
                    "revision": d.name,
                    "size": f.stat().st_size,
                    "ext": f.suffix.lower(),
                })
    return files


def get_project_datos(ref, revision=None):
    output_dir = _get_output_dir()
    project_dir = output_dir / ref

    if revision:
        datos_path = project_dir / revision / "datos.json"
    else:
        for d in sorted(project_dir.iterdir(), reverse=True):
            if d.is_dir() and REVISION_RE.match(d.name):
                datos_path = d / "datos.json"
                if datos_path.exists():
                    break
        else:
            return None

    if datos_path.exists():
        with open(datos_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None
