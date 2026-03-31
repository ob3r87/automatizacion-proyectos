"""
Proveedor MR-Clipart (Car'n Truck) - 70k+ plantillas profesionales.
Requiere suscripción. Soporte para:
1. Importar plantillas descargadas manualmente desde mr-clipart.com
2. Mostrar como opción disponible con enlace a suscripción
"""

import os
import re
from pathlib import Path
from .base import BlueprintProvider, BlueprintSearchResult


class MRClipartProvider(BlueprintProvider):
    key = "mr_clipart"
    name = "MR-Clipart Car'n Truck (Suscripción)"
    is_free = False
    provides_images = True
    requires_auth = True
    base_url = "https://mr-clipart.com"

    # Carpeta donde el usuario puede colocar plantillas descargadas de MR-Clipart
    _local_folder = None

    def __init__(self, local_folder=None):
        if local_folder:
            self._local_folder = Path(local_folder)
        else:
            # Buscar en ubicación por defecto
            import sys
            if getattr(sys, 'frozen', False):
                base = Path(sys.executable).parent
            else:
                base = Path(__file__).resolve().parent.parent.parent.parent
            self._local_folder = base / "plantillas_vehiculos" / "_mr_clipart"

    def search(self, make, model, year=None):
        """Busca en la carpeta local de MR-Clipart + muestra enlace de suscripción."""
        results = []

        # 1. Buscar plantillas locales importadas
        results.extend(self._search_local(make, model, year))

        # 2. Siempre añadir una entrada informativa sobre la suscripción
        results.append(BlueprintSearchResult(
            source_key=self.key,
            source_name=self.name,
            make=make,
            model=model,
            year=year,
            description=(
                f"70.000+ plantillas profesionales SVG/AI/PDF a escala 1:20. "
                f"Suscripción: 129€/año o 599€ vitalicia. "
                f"Visita: {self.base_url}"
            ),
            is_free=False,
            download_url=self.base_url,
            file_format="svg",
            view_type="5 vistas (frontal, lateral, posterior, aérea)",
            extra_data={
                "subscription_url": self.base_url,
                "price_year": "129€ + IVA",
                "price_lifetime": "599€ + IVA",
                "type": "subscription_info",
            },
        ))

        return results

    def _search_local(self, make, model, year=None):
        """Busca plantillas descargadas localmente de MR-Clipart."""
        results = []
        if not self._local_folder or not self._local_folder.exists():
            return results

        # Buscar por nombre de archivo que contenga marca/modelo
        make_lower = make.lower()
        model_lower = model.lower()
        extensions = {".svg", ".ai", ".pdf", ".eps", ".cdr", ".png", ".jpg"}

        for root, dirs, files in os.walk(self._local_folder):
            for fname in files:
                ext = Path(fname).suffix.lower()
                if ext not in extensions:
                    continue

                fname_lower = fname.lower()
                # Buscar coincidencias (marca y/o modelo en nombre)
                if make_lower in fname_lower or model_lower in fname_lower:
                    full_path = os.path.join(root, fname)
                    file_size = os.path.getsize(full_path)

                    results.append(BlueprintSearchResult(
                        source_key=self.key,
                        source_name=f"{self.name} (Local)",
                        make=make,
                        model=model,
                        year=self._extract_year(fname),
                        preview_url="",
                        download_url=full_path,  # Ruta local
                        file_format=ext.lstrip("."),
                        view_type="mixed",
                        description=f"[Local] {fname}",
                        is_free=True,  # Ya descargado = gratis
                        extra_data={
                            "local": True,
                            "file_size": file_size,
                        },
                    ))

        return results

    def download(self, result, dest_path, progress_cb=None):
        """Para MR-Clipart: si es local, copiar. Si es suscripción, informar."""
        if result.extra_data.get("local"):
            # Copiar desde la carpeta local de MR-Clipart
            import shutil
            shutil.copy2(result.download_url, dest_path)
            if progress_cb:
                progress_cb(1.0)
            return dest_path
        else:
            raise RuntimeError(
                f"MR-Clipart requiere suscripción.\n"
                f"Precio anual: 129€ + IVA\n"
                f"Precio vitalicio: 599€ + IVA\n"
                f"Visita: {self.base_url}\n\n"
                f"Descarga las plantillas desde la web y colócalas en:\n"
                f"{self._local_folder}"
            )

    def import_folder(self, folder_path):
        """Importa una carpeta de plantillas MR-Clipart al sistema."""
        import shutil
        self._local_folder.mkdir(parents=True, exist_ok=True)
        count = 0
        extensions = {".svg", ".ai", ".pdf", ".eps", ".cdr", ".png", ".jpg"}
        for root, dirs, files in os.walk(folder_path):
            for fname in files:
                if Path(fname).suffix.lower() in extensions:
                    src = os.path.join(root, fname)
                    dst = self._local_folder / fname
                    if not dst.exists():
                        shutil.copy2(src, dst)
                        count += 1
        return count

    @staticmethod
    def _extract_year(text):
        match = re.search(r'\b(19|20)\d{2}\b', text)
        return int(match.group()) if match else None
