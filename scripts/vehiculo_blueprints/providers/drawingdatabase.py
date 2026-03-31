"""
Proveedor drawingdatabase.com - Blueprints HD gratuitos para 3D modeling.
"""

import re
import requests
from bs4 import BeautifulSoup
from .base import BlueprintProvider, BlueprintSearchResult


class DrawingDatabaseProvider(BlueprintProvider):
    key = "drawingdatabase"
    name = "Drawing Database (Gratis)"
    is_free = True
    provides_images = True
    base_url = "https://drawingdatabase.com"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36"
    }

    def search(self, make, model, year=None):
        """Busca blueprints por marca y modelo."""
        results = []
        query = f"{make} {model}"
        if year:
            query += f" {year}"

        try:
            search_url = f"{self.base_url}/?s={query.replace(' ', '+')}"
            r = requests.get(search_url, headers=self.HEADERS, timeout=15)
            if r.status_code == 200:
                results = self._parse_results(r.text, make, model)
        except Exception as e:
            print(f"[DrawingDatabase] Error: {e}")

        return results

    def _parse_results(self, html, make, model):
        """Parsea la página de resultados de búsqueda."""
        results = []
        soup = BeautifulSoup(html, "html.parser")

        # Buscar artículos/posts con blueprints
        articles = soup.find_all("article") or soup.find_all("div", class_=re.compile(r"post|entry"))

        for article in articles:
            # Buscar imagen principal
            img = article.find("img", src=True)
            if not img:
                continue

            # Título
            title_tag = article.find(["h2", "h3", "h4"])
            title = title_tag.get_text(strip=True) if title_tag else ""

            # Link al detalle
            detail_link = article.find("a", href=True)
            detail_url = detail_link["href"] if detail_link else ""

            src = img.get("data-src") or img.get("src") or ""
            if not src:
                continue

            img_url = src if src.startswith("http") else f"{self.base_url}{src}"

            # Intentar obtener la imagen de mayor resolución
            # WordPress suele tener -AxB en el nombre
            full_url = re.sub(r'-\d+x\d+\.', '.', img_url)

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
                extra_data={"detail_url": detail_url},
            ))

        return results

    @staticmethod
    def _extract_year(text):
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
