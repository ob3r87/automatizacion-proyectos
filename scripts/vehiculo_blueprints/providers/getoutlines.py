"""
Proveedor GetOutlines.com - 40k+ blueprints gratuitos (bitmap).
Bitmaps gratuitos, vectores premium.
"""

import re
import requests
from bs4 import BeautifulSoup
from .base import BlueprintProvider, BlueprintSearchResult


class GetOutlinesProvider(BlueprintProvider):
    key = "getoutlines"
    name = "GetOutlines (Gratis bitmap)"
    is_free = True
    provides_images = True
    base_url = "https://getoutlines.com"

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
            search_url = f"{self.base_url}/search?q={query.replace(' ', '+')}"
            r = requests.get(search_url, headers=self.HEADERS, timeout=15)
            if r.status_code == 200:
                results = self._parse_results(r.text, make, model)
        except Exception as e:
            print(f"[GetOutlines] Error: {e}")

        return results

    def _parse_results(self, html, make, model):
        """Parsea la página de resultados."""
        results = []
        soup = BeautifulSoup(html, "html.parser")

        # Buscar cards de resultados con imágenes
        for card in soup.find_all(["div", "a", "li"],
                                   class_=re.compile(r"card|result|item|product")):
            img = card.find("img", src=True)
            if not img:
                continue

            title = img.get("alt", "") or card.get_text(strip=True)[:80]

            # Verificar relevancia
            text_lower = (title + " " + (img.get("alt", "") or "")).lower()
            if not (make.lower() in text_lower or model.lower() in text_lower):
                continue

            src = img.get("data-src") or img.get("src") or ""
            if not src:
                continue

            img_url = src if src.startswith("http") else f"{self.base_url}{src}"

            # Link al detalle
            link = card if card.name == "a" else card.find("a", href=True)
            detail_url = ""
            if link and link.get("href"):
                href = link["href"]
                detail_url = href if href.startswith("http") else f"{self.base_url}{href}"

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
                description=title.strip(),
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
