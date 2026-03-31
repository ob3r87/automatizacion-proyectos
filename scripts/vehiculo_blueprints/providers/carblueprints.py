"""
Proveedor carblueprints.info - Blueprints gratuitos sin registro.
Scraping de la web para buscar y descargar imágenes.
"""

import re
import requests
from bs4 import BeautifulSoup
from .base import BlueprintProvider, BlueprintSearchResult


class CarBlueprintsProvider(BlueprintProvider):
    key = "carblueprints"
    name = "Car Blueprints (Gratis)"
    is_free = True
    provides_images = True
    base_url = "https://carblueprints.info"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"
    }

    def search(self, make, model, year=None):
        """Busca blueprints por marca y modelo."""
        results = []
        try:
            # Intentar búsqueda directa por marca
            search_url = f"{self.base_url}/blueprints/{make.lower()}/"
            r = requests.get(search_url, headers=self.HEADERS, timeout=15)

            if r.status_code == 200:
                results.extend(self._parse_make_page(r.text, make, model))

            # Si no hay resultados, intentar búsqueda general
            if not results:
                search_url = f"{self.base_url}/search/?q={make}+{model}"
                r = requests.get(search_url, headers=self.HEADERS, timeout=15)
                if r.status_code == 200:
                    results.extend(self._parse_search_page(r.text, make, model))

        except Exception as e:
            print(f"[CarBlueprints] Error: {e}")

        return results

    def _parse_make_page(self, html, make, model):
        """Parsea la página de una marca buscando el modelo."""
        results = []
        soup = BeautifulSoup(html, "html.parser")

        # Buscar links que contengan el nombre del modelo
        model_lower = model.lower()
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True).lower()
            href = link["href"]
            if model_lower in text and (".jpg" in href or ".png" in href
                                         or "/blueprints/" in href):
                # Encontrado un link al modelo
                img_url = href if href.startswith("http") else f"{self.base_url}{href}"
                title = link.get_text(strip=True)
                year = self._extract_year(title)

                results.append(BlueprintSearchResult(
                    source_key=self.key,
                    source_name=self.name,
                    make=make,
                    model=model,
                    year=year,
                    preview_url=img_url,
                    download_url=img_url,
                    file_format=self._get_format(img_url),
                    view_type="mixed",
                    description=title,
                    is_free=True,
                ))

        # También buscar imágenes directamente
        for img in soup.find_all("img", src=True):
            alt = (img.get("alt", "") or "").lower()
            src = img["src"]
            if model_lower in alt:
                img_url = src if src.startswith("http") else f"{self.base_url}{src}"
                # Buscar versión de mayor resolución
                full_url = img_url.replace("/thumb/", "/").replace("_thumb", "")
                title = img.get("alt", f"{make} {model}")
                year = self._extract_year(title)

                results.append(BlueprintSearchResult(
                    source_key=self.key,
                    source_name=self.name,
                    make=make,
                    model=model,
                    year=year,
                    preview_url=img_url,
                    download_url=full_url,
                    file_format=self._get_format(full_url),
                    view_type="mixed",
                    description=title,
                    is_free=True,
                ))

        return results

    def _parse_search_page(self, html, make, model):
        """Parsea la página de resultados de búsqueda."""
        results = []
        soup = BeautifulSoup(html, "html.parser")

        for img in soup.find_all("img", src=True):
            alt = (img.get("alt", "") or "").lower()
            if make.lower() in alt or model.lower() in alt:
                src = img["src"]
                img_url = src if src.startswith("http") else f"{self.base_url}{src}"
                full_url = img_url.replace("/thumb/", "/").replace("_thumb", "")
                title = img.get("alt", f"{make} {model}")

                results.append(BlueprintSearchResult(
                    source_key=self.key,
                    source_name=self.name,
                    make=make,
                    model=model,
                    year=self._extract_year(title),
                    preview_url=img_url,
                    download_url=full_url,
                    file_format=self._get_format(full_url),
                    view_type="mixed",
                    description=title,
                    is_free=True,
                ))

        return results

    @staticmethod
    def _extract_year(text):
        """Extrae el año de un texto (ej: 'Seat Leon 2020')."""
        match = re.search(r'\b(19|20)\d{2}\b', text)
        return int(match.group()) if match else None

    @staticmethod
    def _get_format(url):
        url_lower = url.lower()
        if ".png" in url_lower:
            return "png"
        if ".svg" in url_lower:
            return "svg"
        return "jpg"
