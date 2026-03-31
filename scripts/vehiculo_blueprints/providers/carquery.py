"""
Proveedor de catálogo de marcas/modelos y dimensiones de vehículos.
Usa un catálogo local predefinido (marcas comunes en homologaciones España)
complementado con CarAPI.app como fuente online.
"""

import time
import requests
from .base import BlueprintProvider, BlueprintSearchResult, VehicleDimensions


# Catálogo local de marcas y modelos comunes en homologaciones
CATALOGO_MARCAS = {
    "ALFA ROMEO": ["Giulia", "Stelvio", "Giulietta", "MiTo", "159", "147"],
    "AUDI": ["A1", "A3", "A4", "A5", "A6", "A7", "A8", "Q2", "Q3", "Q5", "Q7", "Q8", "TT", "e-tron"],
    "BMW": ["Serie 1", "Serie 2", "Serie 3", "Serie 4", "Serie 5", "Serie 7", "X1", "X2", "X3", "X4", "X5", "X6", "X7", "Z4"],
    "CITROEN": ["Berlingo", "C1", "C3", "C3 Aircross", "C4", "C4 Cactus", "C5", "C5 Aircross", "Jumper", "Jumpy", "SpaceTourer", "Nemo", "C-Elysee"],
    "DACIA": ["Duster", "Sandero", "Logan", "Dokker", "Lodgy", "Spring"],
    "FIAT": ["500", "500L", "500X", "Panda", "Tipo", "Ducato", "Doblo", "Punto", "Fiorino", "Talento", "Scudo"],
    "FORD": ["Fiesta", "Focus", "Mondeo", "Kuga", "Puma", "EcoSport", "Galaxy", "S-Max", "Transit", "Transit Connect", "Transit Custom", "Ranger", "Tourneo"],
    "HONDA": ["Civic", "CR-V", "HR-V", "Jazz", "e"],
    "HYUNDAI": ["i10", "i20", "i30", "Tucson", "Kona", "Santa Fe", "IONIQ", "Bayon", "H-1"],
    "IVECO": ["Daily", "Eurocargo", "S-Way", "Stralis"],
    "JEEP": ["Renegade", "Compass", "Cherokee", "Grand Cherokee", "Wrangler", "Gladiator"],
    "KIA": ["Picanto", "Rio", "Ceed", "Sportage", "Sorento", "Stonic", "Niro", "EV6", "Soul"],
    "LAND ROVER": ["Defender", "Discovery", "Discovery Sport", "Range Rover", "Range Rover Sport", "Range Rover Evoque", "Velar"],
    "MAN": ["TGE", "TGL", "TGM", "TGS", "TGX"],
    "MAZDA": ["2", "3", "6", "CX-3", "CX-30", "CX-5", "MX-5"],
    "MERCEDES-BENZ": ["Clase A", "Clase B", "Clase C", "Clase E", "Clase S", "CLA", "CLS", "GLA", "GLB", "GLC", "GLE", "GLS", "Sprinter", "Vito", "Citan", "Marco Polo", "Actros", "Atego", "Arocs"],
    "MINI": ["Cooper", "Countryman", "Clubman", "Cabrio"],
    "MITSUBISHI": ["ASX", "Eclipse Cross", "L200", "Outlander", "Space Star", "Canter"],
    "NISSAN": ["Micra", "Juke", "Qashqai", "X-Trail", "Leaf", "NV200", "NV300", "NV400", "Navara", "Primastar"],
    "OPEL": ["Corsa", "Astra", "Insignia", "Mokka", "Crossland", "Grandland", "Zafira", "Combo", "Vivaro", "Movano"],
    "PEUGEOT": ["108", "208", "308", "408", "508", "2008", "3008", "5008", "Rifter", "Partner", "Expert", "Boxer", "Traveller"],
    "RENAULT": ["Clio", "Megane", "Captur", "Kadjar", "Koleos", "Scenic", "Talisman", "Twingo", "Kangoo", "Trafic", "Master", "ZOE"],
    "SCANIA": ["R", "S", "G", "P", "L"],
    "SEAT": ["Arona", "Ateca", "Ibiza", "Leon", "Tarraco", "Alhambra", "Mii"],
    "SKODA": ["Fabia", "Octavia", "Superb", "Kamiq", "Karoq", "Kodiaq", "Scala", "Enyaq"],
    "SSANGYONG": ["Tivoli", "Korando", "Rexton", "Musso"],
    "SUBARU": ["Impreza", "XV", "Forester", "Outback", "BRZ"],
    "SUZUKI": ["Swift", "Ignis", "Vitara", "S-Cross", "Jimny", "Across"],
    "TESLA": ["Model 3", "Model S", "Model X", "Model Y"],
    "TOYOTA": ["Yaris", "Corolla", "Camry", "C-HR", "RAV4", "Land Cruiser", "Hilux", "Proace", "Proace City", "Supra", "GR86", "Aygo"],
    "VOLKSWAGEN": ["Polo", "Golf", "Passat", "Tiguan", "T-Roc", "T-Cross", "Touareg", "ID.3", "ID.4", "Caddy", "Transporter", "Crafter", "Amarok", "California", "Multivan", "Caravelle"],
    "VOLVO": ["XC40", "XC60", "XC90", "S60", "S90", "V60", "V90", "C40"],
    # Autocaravanas / Motorhomes
    "CAPRON": ["Sunlight", "V66", "T67", "T68", "T69", "I68"],
    "SUNLIGHT": ["T67", "T68", "T69", "V66", "I68", "A70", "Cliff"],
    "KNAUS": ["BoxStar", "BoxDrive", "Van TI", "Sky TI", "Sun TI", "Live TI"],
    "BURSTNER": ["Lyseo", "Nexxo", "Ixeo", "Travel Van", "Campeo"],
    "DETHLEFFS": ["Globebus", "Trend", "Just Go", "Esprit", "Pulse"],
    "CHALLENGER": ["194", "260", "264", "288", "328", "V114"],
    "ROLLER TEAM": ["Kronos", "Zefiro", "Livingstone"],
    "BENIMAR": ["Benivan", "Tessoro", "Mileo", "Primero", "Amphitryon"],
    "RAPIDO": ["Serie 6", "Serie 8", "Serie 9", "Serie 10", "V55", "V62"],
    "CARTHAGO": ["C-Compactline", "C-Tourer", "Liner", "Chic"],
    "HYMER": ["B-Klasse", "Exsis", "DuoCar", "Free", "Grand Canyon"],
    "ADRIA": ["Matrix", "Coral", "Sonic", "Twin"],
    "ELNAGH": ["T-Loft", "Magnum", "Baron"],
    "LAIKA": ["Ecovip", "Kosmo", "Kreos"],
    "PILOTE": ["Galaxy", "Pacific", "Foxy Van"],
}


class CarQueryProvider(BlueprintProvider):
    key = "carquery"
    name = "Catálogo de Vehículos"
    is_free = True
    provides_images = False
    base_url = "https://carapi.app"

    _last_request = 0
    _min_interval = 1.0

    def get_makes(self):
        """Devuelve lista de marcas del catálogo local."""
        makes = []
        for name in sorted(CATALOGO_MARCAS.keys()):
            makes.append({
                "name": name,
                "display": name.title(),
            })
        return makes

    def get_models(self, make):
        """Devuelve modelos para una marca del catálogo local."""
        make_upper = make.upper()
        models_list = CATALOGO_MARCAS.get(make_upper, [])

        # También buscar coincidencias parciales
        if not models_list:
            for key in CATALOGO_MARCAS:
                if make_upper in key or key in make_upper:
                    models_list = CATALOGO_MARCAS[key]
                    break

        return [{"name": m, "make_id": make_upper} for m in sorted(models_list)]

    def get_dimensions(self, make, model, year=None):
        """Intenta obtener dimensiones online. Si falla, devuelve None."""
        # Intentar con CarAPI.app (free tier, no requiere auth para info básica)
        try:
            elapsed = time.time() - self._last_request
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)

            # Búsqueda en CarAPI
            params = {"make": make, "model": model}
            if year:
                params["year"] = year

            r = requests.get(
                "https://carapi.app/api/trims",
                params=params, timeout=10,
                headers={"User-Agent": "Mozilla/5.0"})
            self._last_request = time.time()

            if r.status_code == 200:
                data = r.json()
                trims = data.get("data", data) if isinstance(data, dict) else data
                if isinstance(trims, list) and trims:
                    trim = trims[0]
                    specs = trim.get("specs", {}) or {}
                    return VehicleDimensions(
                        length_mm=self._parse_int(specs.get("length_mm")),
                        width_mm=self._parse_int(specs.get("width_mm")),
                        height_mm=self._parse_int(specs.get("height_mm")),
                        wheelbase_mm=self._parse_int(specs.get("wheelbase_mm")),
                        weight_kg=self._parse_int(specs.get("curb_weight_kg")),
                    )
        except Exception:
            pass

        return None

    def get_years(self, make, model):
        """Devuelve rango de años genérico."""
        return list(range(2025, 1999, -1))

    def search(self, make, model, year=None):
        """Devuelve resultado con dimensiones si disponible."""
        dims = self.get_dimensions(make, model, year)
        if dims and any(dims.to_dict().values()):
            return [BlueprintSearchResult(
                source_key=self.key,
                source_name=self.name,
                make=make,
                model=model,
                year=year,
                description=f"Dimensiones: {dims}",
                is_free=True,
                dimensions=dims.to_dict(),
                file_format="data",
                view_type="dimensiones",
            )]
        return []

    @staticmethod
    def _parse_int(value):
        if value is None or value == "" or value == "0":
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
