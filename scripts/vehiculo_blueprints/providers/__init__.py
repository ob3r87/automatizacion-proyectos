"""Registro de proveedores de plantillas de vehículos."""

from .carquery import CarQueryProvider
from .carblueprints import CarBlueprintsProvider
from .drawingdatabase import DrawingDatabaseProvider
from .getoutlines import GetOutlinesProvider
from .mr_clipart import MRClipartProvider
from .paid_stub import TheBlueprintsProvider, CcvisionProvider

ALL_PROVIDERS = [
    CarQueryProvider(),
    CarBlueprintsProvider(),
    DrawingDatabaseProvider(),
    GetOutlinesProvider(),
    MRClipartProvider(),
    TheBlueprintsProvider(),
    CcvisionProvider(),
]

FREE_PROVIDERS = [p for p in ALL_PROVIDERS if p.is_free]
PAID_PROVIDERS = [p for p in ALL_PROVIDERS if not p.is_free]


def get_provider(key):
    """Obtiene un proveedor por su clave."""
    return next((p for p in ALL_PROVIDERS if p.key == key), None)


def get_image_providers():
    """Proveedores que proporcionan imágenes (no solo dimensiones)."""
    return [p for p in ALL_PROVIDERS if p.provides_images]
