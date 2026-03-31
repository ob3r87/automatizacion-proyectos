# -*- coding: utf-8 -*-
"""
Configuración centralizada de la aplicación.
Lee config.json del directorio raíz del proyecto.
"""
import json
import os
from pathlib import Path

# Directorios base
TRACKER_DIR  = Path(__file__).parent          # .../tracker/
PROJECT_ROOT = TRACKER_DIR.parent              # .../AUTOMATIZACION_PROYECTOS/

CONFIG_FILE  = PROJECT_ROOT / "config.json"
DB_PATH      = TRACKER_DIR / "tracker.db"
PDF_DIR      = TRACKER_DIR / "pdfs"
CODIGOS_REFORMA_PATH = TRACKER_DIR / "codigos_reforma.json"

# Plantillas DOCX
TEMPLATE_BASE = PROJECT_ROOT / "PLANTILLA_BASE.docx"
TEMPLATE_CFO  = PROJECT_ROOT / "PLANTILLA_CFO.docx"
TEMPLATE_CT   = PROJECT_ROOT / "PLANTILLA_CT.docx"


def load_config() -> dict:
    """Carga config.json. Devuelve dict vacío si no existe."""
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def get_output_path() -> Path:
    """Ruta de salida para proyectos generados."""
    cfg = load_config()
    p = cfg.get("OUTPUT_PATH", "").strip()
    if p and Path(p).exists():
        return Path(p)
    default = PROJECT_ROOT / "proyectos_generados"
    default.mkdir(exist_ok=True)
    return default


def get_template_path(tipo: str) -> Path:
    """Ruta a una plantilla DOCX. tipo: 'base'|'cfo'|'ct'"""
    cfg = load_config()
    key_map = {"base": "TEMPLATE_PROYECTO", "cfo": "TEMPLATE_CFO", "ct": "TEMPLATE_CT"}
    key = key_map.get(tipo.lower(), "TEMPLATE_PROYECTO")
    p = cfg.get(key, "").strip()
    if p and Path(p).exists():
        return Path(p)
    defaults = {"base": TEMPLATE_BASE, "cfo": TEMPLATE_CFO, "ct": TEMPLATE_CT}
    return defaults.get(tipo.lower(), TEMPLATE_BASE)


def save_config(updates: dict) -> None:
    """Actualiza config.json con los valores dados."""
    cfg = load_config()
    cfg.update(updates)
    CONFIG_FILE.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


# Puerto del servidor Flask
FLASK_PORT = int(os.environ.get("PHICAN_PORT", 5050))
FLASK_HOST = os.environ.get("PHICAN_HOST", "127.0.0.1")
FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
