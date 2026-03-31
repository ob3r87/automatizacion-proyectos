"""
Stubs para proveedores de pago: the-blueprints.com y ccvision.
Muestran información de suscripción sin intentar descargar.
"""

from .base import BlueprintProvider, BlueprintSearchResult


class TheBlueprintsProvider(BlueprintProvider):
    key = "the_blueprints"
    name = "The-Blueprints.com (Pago)"
    is_free = False
    provides_images = True
    requires_auth = True
    base_url = "https://www.the-blueprints.com"

    def search(self, make, model, year=None):
        return [BlueprintSearchResult(
            source_key=self.key,
            source_name=self.name,
            make=make,
            model=model,
            year=year,
            description=(
                f"31.000+ plantillas vectoriales. "
                f"Pago por descarga individual. "
                f"Buscar en: {self.base_url}/blueprints/cars/{make.lower()}/"
            ),
            is_free=False,
            download_url=f"{self.base_url}/blueprints/cars/{make.lower()}/",
            file_format="vector",
            view_type="mixed",
            extra_data={
                "type": "subscription_info",
                "search_url": f"{self.base_url}/blueprints/cars/{make.lower()}/",
            },
        )]

    def download(self, result, dest_path, progress_cb=None):
        raise RuntimeError(
            f"The-Blueprints.com requiere pago por descarga.\n"
            f"Visita: {result.download_url}"
        )


class CcvisionProvider(BlueprintProvider):
    key = "ccvision"
    name = "ccvision CAR-SPECIAL (Suscripción)"
    is_free = False
    provides_images = True
    requires_auth = True
    base_url = "https://www.ccvision.de"

    def search(self, make, model, year=None):
        return [BlueprintSearchResult(
            source_key=self.key,
            source_name=self.name,
            make=make,
            model=model,
            year=year,
            description=(
                f"13.900+ vehículos, 5 vistas (AI/EPS/CDR/DXF), escala exacta. "
                f"Suscripción: 299€ primer año, 159€/año después. "
                f"Visita: {self.base_url}/en/car-special/"
            ),
            is_free=False,
            download_url=f"{self.base_url}/en/car-special/",
            file_format="vector",
            view_type="5 vistas",
            extra_data={
                "type": "subscription_info",
                "price_first_year": "299€",
                "price_renewal": "159€/año",
            },
        )]

    def download(self, result, dest_path, progress_cb=None):
        raise RuntimeError(
            f"ccvision CAR-SPECIAL requiere suscripción.\n"
            f"299€ primer año, 159€/año renovación.\n"
            f"Visita: {self.base_url}/en/car-special/"
        )
