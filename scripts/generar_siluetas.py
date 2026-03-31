# -*- coding: utf-8 -*-
"""
Generador de siluetas SVG para plantillas de vehículos.
Crea una colección local organizada por categoría de vehículo.
"""
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SALIDA   = BASE_DIR / "plantillas_vehiculos"

# ─── Siluetas SVG por tipo ────────────────────────────────────────────────────
# viewBox: 0 0 800 300  (escala referencia, no dimensional real)
# Los paths representan vista lateral izquierda

SILUETAS = {

    # ── M1 — TURISMOS ─────────────────────────────────────────────────────────

    "M1_BERLINA": {
        "nombre": "Turismo Berlina (Sedan)",
        "categoria": "M1",
        "tipo": "Berlina",
        "descripcion": "Turismo de 3 volúmenes con maletero diferenciado",
        "vistas": {
            "lateral": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 300" width="800" height="300">
  <title>M1 Turismo Berlina — Vista Lateral</title>
  <rect width="800" height="300" fill="#f8f8f8"/>
  <!-- Carrocería principal -->
  <path d="M 80,220 L 80,180 Q 90,170 120,165 L 200,130 Q 240,108 300,105 L 480,105 Q 530,106 570,118 L 650,150 Q 690,165 710,180 L 720,220 Z"
        fill="white" stroke="#1a1a1a" stroke-width="3" stroke-linejoin="round"/>
  <!-- Techo -->
  <path d="M 200,130 Q 250,90 310,82 L 490,82 Q 540,82 570,95 L 610,120 L 570,118 Q 530,106 480,105 L 300,105 Q 240,108 200,130 Z"
        fill="white" stroke="#1a1a1a" stroke-width="3" stroke-linejoin="round"/>
  <!-- Parabrisas delantero -->
  <path d="M 300,105 L 310,82 L 380,80 L 380,105 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Luneta trasera -->
  <path d="M 490,105 L 490,82 L 560,84 L 570,105 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Ventanas laterales -->
  <path d="M 385,105 L 385,83 L 485,82 L 485,105 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Rueda delantera -->
  <circle cx="175" cy="222" r="42" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="175" cy="222" r="28" fill="#e0e0e0" stroke="#555" stroke-width="1.5"/>
  <circle cx="175" cy="222" r="10" fill="#999"/>
  <!-- Rueda trasera -->
  <circle cx="610" cy="222" r="42" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="610" cy="222" r="28" fill="#e0e0e0" stroke="#555" stroke-width="1.5"/>
  <circle cx="610" cy="222" r="10" fill="#999"/>
  <!-- Línea suelo -->
  <line x1="40" y1="264" x2="760" y2="264" stroke="#555" stroke-width="1.5" stroke-dasharray="8,6"/>
</svg>""",
        }
    },

    "M1_HATCHBACK": {
        "nombre": "Turismo Hatchback 5 puertas",
        "categoria": "M1",
        "tipo": "Hatchback",
        "descripcion": "Turismo compacto de 2 volúmenes, 5 puertas",
        "vistas": {
            "lateral": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 300" width="800" height="300">
  <title>M1 Hatchback — Vista Lateral</title>
  <rect width="800" height="300" fill="#f8f8f8"/>
  <!-- Carrocería -->
  <path d="M 90,225 L 90,185 Q 100,172 130,168 L 220,140 Q 265,112 330,108 L 560,108 Q 610,110 645,130 L 680,162 Q 700,175 710,188 L 718,225 Z"
        fill="white" stroke="#1a1a1a" stroke-width="3" stroke-linejoin="round"/>
  <!-- Techo -->
  <path d="M 220,140 Q 270,95 340,88 L 520,88 Q 570,90 610,108 L 560,108 Q 610,110 645,130 L 610,108 Q 570,90 520,88 L 340,88 Q 270,95 220,140 Z"
        fill="white" stroke="#1a1a1a" stroke-width="2"/>
  <path d="M 220,140 Q 270,95 340,88 L 520,88 Q 570,90 610,108 L 560,108 L 330,108 Q 265,112 220,140 Z"
        fill="white" stroke="#1a1a1a" stroke-width="3" stroke-linejoin="round"/>
  <!-- Parabrisas -->
  <path d="M 330,108 L 345,88 L 420,86 L 420,108 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Ventanas -->
  <path d="M 424,108 L 424,87 L 510,87 L 510,108 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Luneta (inclinada en hatchback) -->
  <path d="M 514,108 L 514,89 L 600,106 L 610,108 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Ruedas -->
  <circle cx="185" cy="226" r="43" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="185" cy="226" r="29" fill="#e0e0e0" stroke="#555" stroke-width="1.5"/>
  <circle cx="185" cy="226" r="10" fill="#999"/>
  <circle cx="615" cy="226" r="43" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="615" cy="226" r="29" fill="#e0e0e0" stroke="#555" stroke-width="1.5"/>
  <circle cx="615" cy="226" r="10" fill="#999"/>
  <!-- Suelo -->
  <line x1="40" y1="269" x2="760" y2="269" stroke="#555" stroke-width="1.5" stroke-dasharray="8,6"/>
</svg>""",
        }
    },

    "M1_SUV": {
        "nombre": "SUV / Todoterreno",
        "categoria": "M1",
        "tipo": "SUV",
        "descripcion": "Vehículo todoterreno o SUV de altura elevada",
        "vistas": {
            "lateral": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 320" width="800" height="320">
  <title>M1 SUV — Vista Lateral</title>
  <rect width="800" height="320" fill="#f8f8f8"/>
  <!-- Carrocería alta -->
  <path d="M 75,238 L 75,185 Q 85,170 115,163 L 180,145 Q 210,120 270,112 L 570,112 Q 620,115 660,135 L 700,165 Q 718,180 722,195 L 725,238 Z"
        fill="white" stroke="#1a1a1a" stroke-width="3.5" stroke-linejoin="round"/>
  <!-- Techo plano SUV -->
  <path d="M 180,145 Q 220,96 290,90 L 540,90 Q 590,92 630,108 L 570,112 L 270,112 Q 210,120 180,145 Z"
        fill="white" stroke="#1a1a1a" stroke-width="3" stroke-linejoin="round"/>
  <!-- Parabrisas más vertical -->
  <path d="M 270,112 L 292,90 L 370,88 L 370,112 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Ventanas -->
  <path d="M 374,112 L 374,89 L 470,89 L 470,112 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <path d="M 474,112 L 474,90 L 560,90 L 570,112 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Protecciones bajas -->
  <rect x="75" y="205" width="650" height="18" rx="4" fill="#ddd" stroke="#aaa" stroke-width="1"/>
  <!-- Ruedas grandes SUV -->
  <circle cx="175" cy="240" r="48" fill="white" stroke="#1a1a1a" stroke-width="3.5"/>
  <circle cx="175" cy="240" r="32" fill="#d8d8d8" stroke="#555" stroke-width="1.5"/>
  <circle cx="175" cy="240" r="12" fill="#888"/>
  <circle cx="625" cy="240" r="48" fill="white" stroke="#1a1a1a" stroke-width="3.5"/>
  <circle cx="625" cy="240" r="32" fill="#d8d8d8" stroke="#555" stroke-width="1.5"/>
  <circle cx="625" cy="240" r="12" fill="#888"/>
  <!-- Suelo -->
  <line x1="40" y1="288" x2="760" y2="288" stroke="#555" stroke-width="1.5" stroke-dasharray="8,6"/>
</svg>""",
        }
    },

    "M1_MONOVOLUMEN": {
        "nombre": "Monovolumen / MPV",
        "categoria": "M1",
        "tipo": "Monovolumen",
        "descripcion": "Vehículo familiar monovolumen o minivan",
        "vistas": {
            "lateral": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 310" width="800" height="310">
  <title>M1 Monovolumen — Vista Lateral</title>
  <rect width="800" height="310" fill="#f8f8f8"/>
  <!-- Carrocería monovolumen (silueta más alta y redondeada) -->
  <path d="M 80,230 L 80,185 Q 90,170 115,162 L 165,140 Q 195,105 260,95 L 550,95 Q 610,98 660,130 L 700,165 Q 718,182 720,200 L 722,230 Z"
        fill="white" stroke="#1a1a1a" stroke-width="3" stroke-linejoin="round"/>
  <!-- Techo redondeado -->
  <path d="M 165,140 Q 200,88 275,80 L 520,80 Q 590,82 640,115 L 660,130 L 550,95 L 260,95 Q 195,105 165,140 Z"
        fill="white" stroke="#1a1a1a" stroke-width="3" stroke-linejoin="round"/>
  <!-- Parabrisas inclinado -->
  <path d="M 260,95 L 278,80 L 370,78 L 370,95 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- 3 ventanas laterales -->
  <path d="M 374,95 L 374,79 L 445,79 L 445,95 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <path d="M 449,95 L 449,80 L 520,80 L 520,95 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Luneta trasera -->
  <path d="M 524,95 L 524,81 L 598,110 L 610,128 L 580,125 L 550,95 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Ruedas -->
  <circle cx="175" cy="232" r="45" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="175" cy="232" r="30" fill="#e0e0e0" stroke="#555" stroke-width="1.5"/>
  <circle cx="175" cy="232" r="11" fill="#999"/>
  <circle cx="620" cy="232" r="45" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="620" cy="232" r="30" fill="#e0e0e0" stroke="#555" stroke-width="1.5"/>
  <circle cx="620" cy="232" r="11" fill="#999"/>
  <!-- Suelo -->
  <line x1="40" y1="277" x2="760" y2="277" stroke="#555" stroke-width="1.5" stroke-dasharray="8,6"/>
</svg>""",
        }
    },

    "M1_CABRIO": {
        "nombre": "Descapotable / Cabrio",
        "categoria": "M1",
        "tipo": "Cabrio",
        "descripcion": "Turismo descapotable con capota baja",
        "vistas": {
            "lateral": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 280" width="800" height="280">
  <title>M1 Cabrio — Vista Lateral</title>
  <rect width="800" height="280" fill="#f8f8f8"/>
  <!-- Carrocería baja -->
  <path d="M 90,215 L 90,182 Q 100,172 130,167 L 195,150 Q 230,140 270,138 L 560,138 Q 610,140 660,155 L 700,175 Q 715,185 718,200 L 720,215 Z"
        fill="white" stroke="#1a1a1a" stroke-width="3" stroke-linejoin="round"/>
  <!-- Capota baja (cabrio con capota) -->
  <path d="M 270,138 Q 295,112 330,108 L 520,108 Q 555,110 575,125 L 560,138 L 270,138 Z"
        fill="white" stroke="#1a1a1a" stroke-width="2.5" stroke-linejoin="round"/>
  <!-- Parabrisas muy inclinado -->
  <path d="M 270,138 L 295,112 L 360,110 L 360,138 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Ventana lateral pequeña -->
  <path d="M 364,138 L 364,111 L 445,111 L 445,138 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Techo capota -->
  <path d="M 448,138 L 448,112 L 520,111 L 540,125 L 560,138 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Ruedas más pequeñas deportivo -->
  <circle cx="180" cy="217" r="40" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="180" cy="217" r="27" fill="#e0e0e0" stroke="#555" stroke-width="1.5"/>
  <circle cx="180" cy="217" r="10" fill="#999"/>
  <circle cx="620" cy="217" r="40" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="620" cy="217" r="27" fill="#e0e0e0" stroke="#555" stroke-width="1.5"/>
  <circle cx="620" cy="217" r="10" fill="#999"/>
  <!-- Suelo -->
  <line x1="40" y1="257" x2="760" y2="257" stroke="#555" stroke-width="1.5" stroke-dasharray="8,6"/>
</svg>""",
        }
    },

    # ── N1 — FURGONETAS / VEHÍCULOS COMERCIALES LIGEROS ──────────────────────

    "N1_FURGONETA_PEQUENA": {
        "nombre": "Furgoneta pequeña (tipo Transit Connect / Berlingo)",
        "categoria": "N1",
        "tipo": "Furgoneta compacta",
        "descripcion": "Vehículo comercial ligero de carrocería integral, < 3.5t",
        "vistas": {
            "lateral": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 310" width="800" height="310">
  <title>N1 Furgoneta Pequeña — Vista Lateral</title>
  <rect width="800" height="310" fill="#f8f8f8"/>
  <!-- Carrocería box furgoneta -->
  <path d="M 70,238 L 70,120 Q 80,108 110,104 L 190,90 Q 220,78 270,76 L 650,76 Q 690,78 710,100 L 718,120 L 720,238 Z"
        fill="white" stroke="#1a1a1a" stroke-width="3" stroke-linejoin="round"/>
  <!-- Cabina delantera diferenciada -->
  <path d="M 70,238 L 70,120 Q 80,108 110,104 L 190,90 Q 220,78 270,76 L 310,76 L 310,238 Z"
        fill="#f5f5f5" stroke="#1a1a1a" stroke-width="2"/>
  <!-- Parabrisas -->
  <path d="M 190,90 L 200,76 L 300,76 L 300,92 Q 280,94 190,90 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Ventanilla conductor -->
  <rect x="165" y="120" width="90" height="55" rx="3" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Ventanilla pasajero pequeña -->
  <rect x="265" y="120" width="38" height="55" rx="3" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Zona carga (sin ventanas) -->
  <rect x="318" y="100" width="394" height="138" rx="2" fill="white" stroke="#bbb" stroke-width="1"/>
  <!-- Puerta corredera carga -->
  <line x1="380" y1="100" x2="380" y2="238" stroke="#999" stroke-width="1.5" stroke-dasharray="4,3"/>
  <!-- Puertas traseras dobles -->
  <line x1="650" y1="80" x2="650" y2="238" stroke="#1a1a1a" stroke-width="2"/>
  <!-- Rueda delantera -->
  <circle cx="165" cy="240" r="46" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="165" cy="240" r="30" fill="#e0e0e0" stroke="#555" stroke-width="1.5"/>
  <circle cx="165" cy="240" r="11" fill="#999"/>
  <!-- Rueda trasera -->
  <circle cx="620" cy="240" r="46" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="620" cy="240" r="30" fill="#e0e0e0" stroke="#555" stroke-width="1.5"/>
  <circle cx="620" cy="240" r="11" fill="#999"/>
  <!-- Suelo -->
  <line x1="40" y1="286" x2="760" y2="286" stroke="#555" stroke-width="1.5" stroke-dasharray="8,6"/>
</svg>""",
        }
    },

    "N1_FURGONETA_GRANDE": {
        "nombre": "Furgoneta grande (tipo Sprinter / Crafter / Daily)",
        "categoria": "N1",
        "tipo": "Furgoneta grande",
        "descripcion": "Vehículo comercial ligero de gran capacidad, < 3.5t",
        "vistas": {
            "lateral": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 320" width="800" height="320">
  <title>N1 Furgoneta Grande — Vista Lateral</title>
  <rect width="800" height="320" fill="#f8f8f8"/>
  <!-- Caja alta -->
  <path d="M 60,250 L 60,100 Q 72,82 110,76 L 195,62 Q 230,52 285,50 L 690,50 Q 726,54 738,80 L 742,105 L 742,250 Z"
        fill="white" stroke="#1a1a1a" stroke-width="3" stroke-linejoin="round"/>
  <!-- Cabina -->
  <path d="M 60,250 L 60,100 Q 72,82 110,76 L 195,62 Q 230,52 285,50 L 330,50 L 330,250 Z"
        fill="#f5f5f5" stroke="#1a1a1a" stroke-width="2"/>
  <!-- Parabrisas grande -->
  <path d="M 195,62 L 210,50 L 320,50 L 320,66 Q 295,68 195,62 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Ventanas cabina -->
  <rect x="155" y="110" width="110" height="65" rx="3" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Cuerpo carga sin ventanas -->
  <rect x="338" y="72" width="396" height="178" rx="2" fill="white" stroke="#bbb" stroke-width="1"/>
  <!-- Puerta corredera -->
  <line x1="430" y1="72" x2="430" y2="250" stroke="#999" stroke-width="1.5" stroke-dasharray="5,3"/>
  <!-- Puertas traseras -->
  <line x1="680" y1="54" x2="680" y2="250" stroke="#1a1a1a" stroke-width="2"/>
  <line x1="710" y1="54" x2="710" y2="250" stroke="#1a1a1a" stroke-width="2"/>
  <!-- Rueda delantera -->
  <circle cx="160" cy="252" r="50" fill="white" stroke="#1a1a1a" stroke-width="3.5"/>
  <circle cx="160" cy="252" r="33" fill="#e0e0e0" stroke="#555" stroke-width="1.5"/>
  <circle cx="160" cy="252" r="12" fill="#999"/>
  <!-- Rueda trasera doble representada -->
  <circle cx="632" cy="252" r="50" fill="white" stroke="#1a1a1a" stroke-width="3.5"/>
  <circle cx="632" cy="252" r="33" fill="#e0e0e0" stroke="#555" stroke-width="1.5"/>
  <circle cx="632" cy="252" r="12" fill="#999"/>
  <!-- Suelo -->
  <line x1="30" y1="302" x2="770" y2="302" stroke="#555" stroke-width="1.5" stroke-dasharray="8,6"/>
</svg>""",
        }
    },

    "N1_PICKUP": {
        "nombre": "Pickup / Camioneta",
        "categoria": "N1",
        "tipo": "Pickup",
        "descripcion": "Vehículo comercial ligero con caja abierta de carga",
        "vistas": {
            "lateral": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 300" width="800" height="300">
  <title>N1 Pickup — Vista Lateral</title>
  <rect width="800" height="300" fill="#f8f8f8"/>
  <!-- Cabina pickup -->
  <path d="M 80,230 L 80,185 Q 90,170 120,163 L 195,145 Q 228,118 280,112 L 420,112 L 420,230 Z"
        fill="white" stroke="#1a1a1a" stroke-width="3" stroke-linejoin="round"/>
  <!-- Techo cabina -->
  <path d="M 195,145 Q 235,98 295,92 L 408,92 L 420,112 L 280,112 Q 228,118 195,145 Z"
        fill="white" stroke="#1a1a1a" stroke-width="3" stroke-linejoin="round"/>
  <!-- Parabrisas -->
  <path d="M 280,112 L 296,92 L 380,91 L 380,112 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Ventana trasera cabina -->
  <rect x="384" y="95" width="28" height="42" rx="2" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Caja de carga abierta -->
  <path d="M 425,155 L 425,230 L 720,230 L 720,155 Z" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <!-- Interior caja -->
  <rect x="430" y="160" width="285" height="65" fill="#f0f0f0" stroke="#ccc" stroke-width="1"/>
  <!-- Separador cabina-caja -->
  <line x1="424" y1="130" x2="424" y2="230" stroke="#1a1a1a" stroke-width="3"/>
  <!-- Compuerta trasera -->
  <line x1="718" y1="155" x2="718" y2="230" stroke="#1a1a1a" stroke-width="3"/>
  <!-- Rueda delantera -->
  <circle cx="175" cy="232" r="44" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="175" cy="232" r="29" fill="#e0e0e0" stroke="#555" stroke-width="1.5"/>
  <circle cx="175" cy="232" r="11" fill="#999"/>
  <!-- Rueda trasera -->
  <circle cx="618" cy="232" r="44" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="618" cy="232" r="29" fill="#e0e0e0" stroke="#555" stroke-width="1.5"/>
  <circle cx="618" cy="232" r="11" fill="#999"/>
  <!-- Suelo -->
  <line x1="40" y1="276" x2="760" y2="276" stroke="#555" stroke-width="1.5" stroke-dasharray="8,6"/>
</svg>""",
        }
    },

    # ── N2/N3 — CAMIONES ──────────────────────────────────────────────────────

    "N2_CAMION_RIGIDO": {
        "nombre": "Camion rigido (N2 - hasta 12t)",
        "categoria": "N2",
        "tipo": "Camion_rigido",
        "descripcion": "Camión de reparto / distribución hasta 12 toneladas",
        "vistas": {
            "lateral": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 320" width="900" height="320">
  <title>N2 Camión Rígido — Vista Lateral</title>
  <rect width="900" height="320" fill="#f8f8f8"/>
  <!-- Cabina camión -->
  <path d="M 50,265 L 50,145 Q 62,118 100,108 L 168,90 Q 200,72 245,68 L 310,68 L 310,265 Z"
        fill="white" stroke="#1a1a1a" stroke-width="3" stroke-linejoin="round"/>
  <!-- Techo cabina -->
  <path d="M 168,90 Q 200,60 250,55 L 305,55 L 310,68 L 245,68 Q 200,72 168,90 Z"
        fill="white" stroke="#1a1a1a" stroke-width="2.5"/>
  <!-- Parabrisas -->
  <path d="M 245,68 L 252,55 L 305,55 L 305,68 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Ventana lateral cabina -->
  <rect x="145" y="120" width="110" height="75" rx="3" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Cuerpo/caja de carga larga -->
  <rect x="315" y="68" width="548" height="197" rx="4" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <!-- Detalle estructura caja -->
  <line x1="430" y1="68" x2="430" y2="265" stroke="#ddd" stroke-width="1"/>
  <line x1="545" y1="68" x2="545" y2="265" stroke="#ddd" stroke-width="1"/>
  <line x1="660" y1="68" x2="660" y2="265" stroke="#ddd" stroke-width="1"/>
  <line x1="775" y1="68" x2="775" y2="265" stroke="#1a1a1a" stroke-width="2"/>
  <!-- Chasis bajo cabina -->
  <rect x="50" y="232" width="813" height="18" fill="#e8e8e8" stroke="#999" stroke-width="1"/>
  <!-- Rueda delantera sencilla -->
  <circle cx="155" cy="268" r="52" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="155" cy="268" r="35" fill="#d8d8d8" stroke="#555" stroke-width="1.5"/>
  <circle cx="155" cy="268" r="13" fill="#888"/>
  <!-- Rueda trasera doble -->
  <circle cx="638" cy="268" r="52" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="638" cy="268" r="35" fill="#d8d8d8" stroke="#555" stroke-width="1.5"/>
  <circle cx="638" cy="268" r="13" fill="#888"/>
  <circle cx="720" cy="268" r="52" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="720" cy="268" r="35" fill="#d8d8d8" stroke="#555" stroke-width="1.5"/>
  <circle cx="720" cy="268" r="13" fill="#888"/>
  <!-- Suelo -->
  <line x1="20" y1="308" x2="880" y2="308" stroke="#555" stroke-width="1.5" stroke-dasharray="8,6"/>
</svg>""",
        }
    },

    "N3_CAMION_ARTICULADO": {
        "nombre": "Camión articulado / Tráiler (N3)",
        "categoria": "N3",
        "tipo": "Articulado",
        "descripcion": "Tractora + semirremolque, masa total > 12t",
        "vistas": {
            "lateral": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 320" width="1100" height="320">
  <title>N3 Articulado — Vista Lateral</title>
  <rect width="1100" height="320" fill="#f8f8f8"/>
  <!-- Cabina tractora -->
  <path d="M 45,270 L 45,140 Q 58,112 100,100 L 175,82 Q 215,62 265,58 L 340,58 L 340,270 Z"
        fill="white" stroke="#1a1a1a" stroke-width="3" stroke-linejoin="round"/>
  <!-- Techo cabina con deflector aerodinámico -->
  <path d="M 175,82 Q 215,50 270,45 L 340,45 L 340,58 L 265,58 Q 215,62 175,82 Z"
        fill="white" stroke="#1a1a1a" stroke-width="2.5"/>
  <!-- Deflector techo -->
  <path d="M 340,45 Q 360,30 385,32 L 385,58 L 340,58 L 340,45 Z" fill="#eee" stroke="#aaa" stroke-width="1.5"/>
  <!-- Parabrisas tractora -->
  <path d="M 265,58 L 272,45 L 338,45 L 338,58 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Ventana cabina -->
  <rect x="145" y="115" width="125" height="80" rx="3" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Chasis tractora -->
  <rect x="45" y="240" width="350" height="20" fill="#e0e0e0" stroke="#999" stroke-width="1"/>
  <!-- Quinta rueda -->
  <rect x="320" y="228" width="60" height="16" rx="3" fill="#ccc" stroke="#888" stroke-width="1.5"/>
  <!-- Semirremolque largo -->
  <rect x="385" y="80" width="680" height="195" rx="5" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <!-- Estructura semirremolque -->
  <line x1="500" y1="80" x2="500" y2="275" stroke="#ddd" stroke-width="1"/>
  <line x1="620" y1="80" x2="620" y2="275" stroke="#ddd" stroke-width="1"/>
  <line x1="740" y1="80" x2="740" y2="275" stroke="#ddd" stroke-width="1"/>
  <line x1="860" y1="80" x2="860" y2="275" stroke="#ddd" stroke-width="1"/>
  <line x1="980" y1="80" x2="980" y2="275" stroke="#1a1a1a" stroke-width="2"/>
  <!-- Chasis remolque -->
  <rect x="385" y="248" width="680" height="16" fill="#ddd" stroke="#999" stroke-width="1"/>
  <!-- Ruedas tractora -->
  <circle cx="140" cy="272" r="52" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="140" cy="272" r="35" fill="#d8d8d8" stroke="#555" stroke-width="1.5"/>
  <circle cx="140" cy="272" r="13" fill="#888"/>
  <circle cx="248" cy="272" r="52" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="248" cy="272" r="35" fill="#d8d8d8" stroke="#555" stroke-width="1.5"/>
  <circle cx="248" cy="272" r="13" fill="#888"/>
  <circle cx="330" cy="272" r="52" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="330" cy="272" r="35" fill="#d8d8d8" stroke="#555" stroke-width="1.5"/>
  <circle cx="330" cy="272" r="13" fill="#888"/>
  <!-- Ruedas semirremolque -->
  <circle cx="820" cy="272" r="52" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="820" cy="272" r="35" fill="#d8d8d8" stroke="#555" stroke-width="1.5"/>
  <circle cx="820" cy="272" r="13" fill="#888"/>
  <circle cx="920" cy="272" r="52" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="920" cy="272" r="35" fill="#d8d8d8" stroke="#555" stroke-width="1.5"/>
  <circle cx="920" cy="272" r="13" fill="#888"/>
  <!-- Suelo -->
  <line x1="20" y1="308" x2="1080" y2="308" stroke="#555" stroke-width="1.5" stroke-dasharray="8,6"/>
</svg>""",
        }
    },

    # ── M2/M3 — AUTOBUSES ─────────────────────────────────────────────────────

    "M2_MICROBUS": {
        "nombre": "Microbús / Minibús (M2 — hasta 5t)",
        "categoria": "M2",
        "tipo": "Microbus",
        "descripcion": "Microbús para transporte de viajeros, hasta 5 toneladas",
        "vistas": {
            "lateral": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 300" width="800" height="300">
  <title>M2 Microbús — Vista Lateral</title>
  <rect width="800" height="300" fill="#f8f8f8"/>
  <!-- Carrocería microbús -->
  <path d="M 55,240 L 55,95 Q 68,75 105,68 L 180,55 L 660,55 Q 700,58 720,78 L 730,100 L 730,240 Z"
        fill="white" stroke="#1a1a1a" stroke-width="3" stroke-linejoin="round"/>
  <!-- Frente diferenciado -->
  <path d="M 55,240 L 55,95 Q 68,75 105,68 L 180,55 L 210,55 L 210,240 Z"
        fill="#f0f0f0" stroke="#1a1a1a" stroke-width="2"/>
  <!-- Parabrisas grande -->
  <path d="M 130,68 L 140,55 L 205,55 L 205,70 Q 185,72 130,68 Z" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Ventanas pasajeros (grandes) -->
  <rect x="218" y="68" width="80" height="65" rx="3" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <rect x="304" y="68" width="80" height="65" rx="3" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <rect x="390" y="68" width="80" height="65" rx="3" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <rect x="476" y="68" width="80" height="65" rx="3" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <rect x="562" y="68" width="80" height="65" rx="3" fill="#d0e8f0" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Puerta delantera viajeros -->
  <rect x="218" y="150" width="80" height="90" rx="2" fill="#f0f0f0" stroke="#888" stroke-width="1.5" stroke-dasharray="4,2"/>
  <!-- Ruedas -->
  <circle cx="155" cy="242" r="50" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="155" cy="242" r="33" fill="#d8d8d8" stroke="#555" stroke-width="1.5"/>
  <circle cx="155" cy="242" r="12" fill="#888"/>
  <circle cx="628" cy="242" r="50" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="628" cy="242" r="33" fill="#d8d8d8" stroke="#555" stroke-width="1.5"/>
  <circle cx="628" cy="242" r="12" fill="#888"/>
  <!-- Suelo -->
  <line x1="30" y1="292" x2="770" y2="292" stroke="#555" stroke-width="1.5" stroke-dasharray="8,6"/>
</svg>""",
        }
    },

    # ── L — MOTOCICLETAS ──────────────────────────────────────────────────────

    "L3E_MOTOCICLETA": {
        "nombre": "Motocicleta (L3e)",
        "categoria": "L3e",
        "tipo": "Motocicleta",
        "descripcion": "Motocicleta de 2 ruedas sin sidecar, cilindrada > 50cc",
        "vistas": {
            "lateral": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 300" width="600" height="300">
  <title>L3e Motocicleta — Vista Lateral</title>
  <rect width="600" height="300" fill="#f8f8f8"/>
  <!-- Chasis / frame (tubo central) -->
  <line x1="160" y1="165" x2="420" y2="145" stroke="#1a1a1a" stroke-width="4"/>
  <!-- Horquilla delantera -->
  <line x1="155" y1="100" x2="120" y2="205" stroke="#1a1a1a" stroke-width="5"/>
  <line x1="170" y1="100" x2="140" y2="205" stroke="#1a1a1a" stroke-width="3"/>
  <!-- Manillar -->
  <line x1="148" y1="103" x2="128" y2="93" stroke="#1a1a1a" stroke-width="4"/>
  <line x1="165" y1="100" x2="185" y2="90" stroke="#1a1a1a" stroke-width="4"/>
  <!-- Deposito -->
  <path d="M 195,118 Q 230,100 310,98 L 380,102 Q 400,108 400,130 Q 390,150 340,155 L 220,158 Q 185,150 185,135 Z"
        fill="#e8e8e8" stroke="#1a1a1a" stroke-width="2.5"/>
  <!-- Asiento -->
  <path d="M 300,145 Q 340,138 420,135 L 440,138 Q 445,145 440,150 Q 400,155 300,158 Z"
        fill="#555" stroke="#1a1a1a" stroke-width="2"/>
  <!-- Motor / bloque -->
  <rect x="230" y="168" width="140" height="55" rx="6" fill="#d0d0d0" stroke="#1a1a1a" stroke-width="2.5"/>
  <!-- Escape -->
  <path d="M 340,215 Q 380,225 440,220 Q 480,215 490,220" fill="none" stroke="#888" stroke-width="8" stroke-linecap="round"/>
  <!-- Basculante trasero -->
  <line x1="360" y1="175" x2="460" y2="200" stroke="#1a1a1a" stroke-width="4"/>
  <!-- Rueda delantera -->
  <circle cx="120" cy="210" r="62" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="120" cy="210" r="44" fill="#e8e8e8" stroke="#666" stroke-width="1.5"/>
  <circle cx="120" cy="210" r="12" fill="#888"/>
  <!-- Rueda trasera -->
  <circle cx="468" cy="208" r="62" fill="white" stroke="#1a1a1a" stroke-width="3"/>
  <circle cx="468" cy="208" r="44" fill="#e8e8e8" stroke="#666" stroke-width="1.5"/>
  <circle cx="468" cy="208" r="12" fill="#888"/>
  <!-- Suelo -->
  <line x1="20" y1="272" x2="580" y2="272" stroke="#555" stroke-width="1.5" stroke-dasharray="8,6"/>
</svg>""",
        }
    },

    "L1E_CICLOMOTOR": {
        "nombre": "Ciclomotor (L1e / L2e)",
        "categoria": "L1e",
        "tipo": "Ciclomotor",
        "descripcion": "Ciclomotor de 2 o 3 ruedas, < 50cc o < 4kW",
        "vistas": {
            "lateral": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 280" width="500" height="280">
  <title>L1e Ciclomotor — Vista Lateral</title>
  <rect width="500" height="280" fill="#f8f8f8"/>
  <!-- Chasis -->
  <path d="M 130,160 Q 180,140 250,138 L 350,140 Q 370,148 380,165" fill="none" stroke="#1a1a1a" stroke-width="4"/>
  <!-- Horquilla -->
  <line x1="128" y1="115" x2="105" y2="190" stroke="#1a1a1a" stroke-width="4"/>
  <!-- Manillar -->
  <line x1="124" y1="116" x2="108" y2="105" stroke="#1a1a1a" stroke-width="3.5"/>
  <line x1="138" y1="113" x2="155" y2="105" stroke="#1a1a1a" stroke-width="3.5"/>
  <!-- Carrocería/carenado -->
  <path d="M 155,148 Q 185,125 250,120 L 340,122 Q 365,128 375,148 Q 365,168 340,172 L 180,170 Q 155,165 155,148 Z"
        fill="#e0e0e0" stroke="#1a1a1a" stroke-width="2"/>
  <!-- Asiento pequeño -->
  <path d="M 270,120 Q 310,112 360,118 L 375,125 Q 370,130 340,132 L 270,130 Z" fill="#666" stroke="#1a1a1a" stroke-width="1.5"/>
  <!-- Motor pequeño -->
  <rect x="220" y="168" width="90" height="40" rx="5" fill="#ccc" stroke="#1a1a1a" stroke-width="2"/>
  <!-- Rueda delantera pequeña -->
  <circle cx="100" cy="196" r="50" fill="white" stroke="#1a1a1a" stroke-width="2.5"/>
  <circle cx="100" cy="196" r="36" fill="#e8e8e8" stroke="#666" stroke-width="1.5"/>
  <circle cx="100" cy="196" r="10" fill="#888"/>
  <!-- Rueda trasera -->
  <circle cx="388" cy="196" r="50" fill="white" stroke="#1a1a1a" stroke-width="2.5"/>
  <circle cx="388" cy="196" r="36" fill="#e8e8e8" stroke="#666" stroke-width="1.5"/>
  <circle cx="388" cy="196" r="10" fill="#888"/>
  <!-- Suelo -->
  <line x1="20" y1="246" x2="480" y2="246" stroke="#555" stroke-width="1.5" stroke-dasharray="8,6"/>
</svg>""",
        }
    },

}


def generar_catalogo():
    """Genera todos los SVGs y el archivo de índice."""
    SALIDA.mkdir(parents=True, exist_ok=True)
    index = []
    total = 0

    for clave, datos in SILUETAS.items():
        cat  = datos["categoria"]
        import unicodedata
        tipo_raw = datos["tipo"].replace("/", "-").replace(" ", "_")
        tipo = "".join(c for c in unicodedata.normalize("NFD", tipo_raw) if unicodedata.category(c) != "Mn")
        carpeta = SALIDA / cat / tipo
        carpeta.mkdir(parents=True, exist_ok=True)

        for vista_nombre, svg_content in datos["vistas"].items():
            filename = f"{clave}_{vista_nombre}.svg"
            filepath = carpeta / filename
            filepath.write_text(svg_content, encoding="utf-8")
            total += 1
            print(f"  OK  {cat}/{tipo}/{filename}")

            index.append({
                "clave": clave,
                "nombre": datos["nombre"],
                "categoria": cat,
                "tipo": datos["tipo"],
                "descripcion": datos["descripcion"],
                "vista": vista_nombre,
                "archivo": str(filepath.relative_to(SALIDA)),
            })

    # Guardar índice JSON
    idx_path = SALIDA / "indice.json"
    idx_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGenerados {total} SVGs en: {SALIDA}")
    print(f"Indice guardado en: {idx_path}")
    return total, index


if __name__ == "__main__":
    print("Generando coleccion de siluetas de vehiculos...\n")
    n, idx = generar_catalogo()
    print(f"\nListo. {n} plantillas disponibles en {SALIDA}")
