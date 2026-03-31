"""
Módulo de integración de plantillas de vehículos.
Busca, descarga y almacena blueprints/plantillas técnicas de vehículos
desde múltiples fuentes (gratuitas y de suscripción).
"""

from .db import init_db, get_makes, get_models, get_cached_blueprints, find_blueprint
from .downloader import DownloadManager

__all__ = [
    "init_db",
    "get_makes",
    "get_models",
    "get_cached_blueprints",
    "find_blueprint",
    "DownloadManager",
]
