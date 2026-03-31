"""
Gestor de descargas de plantillas de vehículos.
Descarga, genera thumbnails, registra en base de datos, gestiona caché.
"""

import hashlib
import os
import re
import sys
from pathlib import Path

from . import db
from .providers.base import BlueprintSearchResult


# Ruta raíz de almacenamiento
if getattr(sys, 'frozen', False):
    _BASE = Path(sys.executable).parent
else:
    _BASE = Path(__file__).resolve().parent.parent.parent

STORAGE_ROOT = _BASE / "plantillas_vehiculos"


class DownloadManager:
    """Gestiona descargas, thumbnails y caché de plantillas."""

    def __init__(self, storage_root=None):
        self.storage_root = Path(storage_root) if storage_root else STORAGE_ROOT
        self.storage_root.mkdir(parents=True, exist_ok=True)

    def get_dest_folder(self, make, model):
        """Devuelve la carpeta destino: plantillas_vehiculos/MARCA/Modelo/"""
        folder = self.storage_root / self._sanitize(make.upper()) / self._sanitize(model)
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def get_dest_path(self, make, model, source_key, view_type="mixed",
                      year=None, file_format="png"):
        """Genera ruta de archivo destino."""
        folder = self.get_dest_folder(make, model)
        parts = [source_key, view_type]
        if year:
            parts.append(str(year))
        base_name = "_".join(parts)
        filename = f"{base_name}.{file_format}"

        # Evitar sobreescribir
        dest = folder / filename
        counter = 1
        while dest.exists():
            dest = folder / f"{base_name}_{counter}.{file_format}"
            counter += 1
        return str(dest)

    def download_blueprint(self, result, provider, progress_cb=None):
        """Descarga una plantilla y la registra en la BD.

        Args:
            result: BlueprintSearchResult
            provider: BlueprintProvider instance
            progress_cb: callable(float) 0.0-1.0

        Returns:
            dict con file_path, thumbnail_path, dimensions, blueprint_id
        """
        # 1. Verificar si ya existe en caché local
        cached = db.find_blueprint(result.make, result.model,
                                   year=result.year, source=result.source_key)
        if cached:
            for bp in cached:
                if os.path.exists(bp["file_path"]):
                    return {
                        "file_path": bp["file_path"],
                        "thumbnail_path": bp.get("thumbnail_path", ""),
                        "dimensions": result.dimensions,
                        "blueprint_id": bp["id"],
                        "from_cache": True,
                    }

        # 2. Determinar ruta destino
        dest_path = self.get_dest_path(
            result.make, result.model, result.source_key,
            result.view_type, result.year, result.file_format)

        # 3. Descargar
        provider.download(result, dest_path, progress_cb=progress_cb)

        # 4. Obtener info del archivo
        file_size = os.path.getsize(dest_path) if os.path.exists(dest_path) else 0
        width_px, height_px = self._get_image_size(dest_path)

        # 5. Generar thumbnail
        thumb_path = self._generate_thumbnail(dest_path)

        # 6. Registrar en BD
        blueprint_id = db.save_blueprint(
            make_name=result.make,
            model_name=result.model,
            year=result.year,
            source_key=result.source_key,
            source_url=result.download_url,
            file_path=dest_path,
            file_format=result.file_format,
            view_type=result.view_type,
            width_px=width_px,
            height_px=height_px,
            file_size=file_size,
            thumbnail_path=thumb_path or "",
        )

        return {
            "file_path": dest_path,
            "thumbnail_path": thumb_path or "",
            "dimensions": result.dimensions,
            "blueprint_id": blueprint_id,
            "from_cache": False,
        }

    def _generate_thumbnail(self, image_path, max_width=150):
        """Genera thumbnail para preview en GUI."""
        try:
            from PIL import Image
            ext = Path(image_path).suffix.lower()
            if ext not in (".png", ".jpg", ".jpeg", ".bmp", ".gif"):
                return ""

            img = Image.open(image_path)
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img.thumbnail(new_size, Image.LANCZOS)

            thumb_path = str(Path(image_path).with_suffix("")) + "_thumb.png"
            img.save(thumb_path, "PNG")
            return thumb_path
        except Exception:
            return ""

    def _get_image_size(self, image_path):
        """Obtiene dimensiones de una imagen en píxeles."""
        try:
            from PIL import Image
            ext = Path(image_path).suffix.lower()
            if ext not in (".png", ".jpg", ".jpeg", ".bmp", ".gif"):
                return 0, 0
            img = Image.open(image_path)
            return img.size
        except Exception:
            return 0, 0

    def fetch_dimensions(self, make, model, year=None):
        """Obtiene dimensiones del vehículo (primero BD, luego CarQuery)."""
        # 1. Buscar en BD
        dims = db.get_dimensions(make_name=make, model_name=model, year=year)
        if dims:
            return {
                "length_mm": dims.get("length_mm"),
                "width_mm": dims.get("width_mm"),
                "height_mm": dims.get("height_mm"),
                "wheelbase_mm": dims.get("wheelbase_mm"),
                "weight_kg": dims.get("weight_kg"),
            }

        # 2. Intentar CarQuery API
        try:
            from .providers.carquery import CarQueryProvider
            cq = CarQueryProvider()
            vd = cq.get_dimensions(make, model, year)
            if vd:
                # Guardar en BD para futuro uso
                make_id = db.save_make(make, source="carquery")
                model_id = db.save_model(make_id, model, source="carquery")
                db.save_dimensions(model_id, year, vd.to_dict(), source="carquery")
                return vd.to_dict()
        except Exception:
            pass

        return None

    def get_local_blueprints(self, make=None, model=None):
        """Devuelve plantillas almacenadas localmente."""
        return db.get_cached_blueprints(make=make, model=model)

    def check_connectivity(self):
        """Verifica si hay conexión a internet."""
        try:
            import requests
            r = requests.head("https://www.google.com", timeout=3)
            return r.status_code < 400
        except Exception:
            return False

    @staticmethod
    def _sanitize(name):
        """Sanitiza un nombre para usarlo como nombre de carpeta."""
        return re.sub(r'[<>:"/\\|?*]', '_', name).strip()
