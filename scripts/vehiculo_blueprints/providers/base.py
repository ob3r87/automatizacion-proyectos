"""Clase base abstracta para proveedores de plantillas de vehículos."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BlueprintSearchResult:
    """Un resultado de búsqueda de un proveedor."""
    source_key: str
    source_name: str
    make: str
    model: str
    year: Optional[int] = None
    preview_url: str = ""
    download_url: str = ""
    file_format: str = "png"
    view_type: str = "mixed"       # lateral, frontal, posterior, planta, mixed
    description: str = ""
    is_free: bool = True
    dimensions: Optional[dict] = None
    extra_data: dict = field(default_factory=dict)


@dataclass
class VehicleDimensions:
    """Dimensiones técnicas de un vehículo."""
    length_mm: Optional[int] = None
    width_mm: Optional[int] = None
    height_mm: Optional[int] = None
    wheelbase_mm: Optional[int] = None
    weight_kg: Optional[int] = None

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def __str__(self):
        parts = []
        if self.length_mm:
            parts.append(f"L:{self.length_mm}mm")
        if self.width_mm:
            parts.append(f"A:{self.width_mm}mm")
        if self.height_mm:
            parts.append(f"H:{self.height_mm}mm")
        if self.wheelbase_mm:
            parts.append(f"Bat:{self.wheelbase_mm}mm")
        return " | ".join(parts) if parts else "Sin dimensiones"


class BlueprintProvider(ABC):
    """Clase base abstracta para proveedores de blueprints/plantillas."""

    key: str = ""
    name: str = ""
    is_free: bool = True
    requires_auth: bool = False
    provides_images: bool = True
    base_url: str = ""

    @abstractmethod
    def search(self, make, model, year=None):
        """Busca plantillas. Devuelve lista de BlueprintSearchResult."""
        ...

    def download(self, result, dest_path, progress_cb=None):
        """Descarga una plantilla a dest_path. Devuelve ruta final."""
        import requests
        try:
            r = requests.get(result.download_url, stream=True, timeout=30,
                             headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_cb and total:
                        progress_cb(downloaded / total)
            return dest_path
        except Exception as e:
            raise RuntimeError(f"Error descargando de {self.name}: {e}")

    def get_makes(self):
        """Devuelve lista de marcas disponibles."""
        return []

    def get_models(self, make):
        """Devuelve lista de modelos para una marca."""
        return []

    def get_dimensions(self, make, model, year=None):
        """Devuelve VehicleDimensions si disponible."""
        return None

    def is_available(self):
        """Comprueba si el proveedor es accesible."""
        try:
            import requests
            r = requests.head(self.base_url, timeout=5,
                              headers={"User-Agent": "Mozilla/5.0"})
            return r.status_code < 400
        except Exception:
            return False
