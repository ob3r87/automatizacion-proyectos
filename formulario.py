# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
=============================================================
  GENERADOR DE PROYECTOS DE REFORMA DE VEHICULO
  Phican Ingenieros — Interfaz gráfica con pestañas
=============================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import re
import sys
import subprocess
import threading
from datetime import datetime
from pathlib import Path

# ── Selector de planos de vehículo (opcional) ─────────────────────────────────
try:
    sys.path.insert(0, str(Path(__file__).parent / "scripts"))
    from vehiculo_blueprints.gui_selector import VehicleBlueprintSelector
    from vehiculo_blueprints.downloader import DownloadManager
    _PLANOS_OK = True
except Exception:
    _PLANOS_OK = False

# ── PIL para preview de imágenes ──────────────────────────────────────────────
try:
    from PIL import Image, ImageTk
    _PIL_OK = True
except Exception:
    _PIL_OK = False

# ── Rutas ────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
SCRIPT_PY   = BASE_DIR / "generar_proyecto.py"
SCRIPT_CFO  = BASE_DIR / "generar_cfo.py"
SCRIPT_CT   = BASE_DIR / "generar_ct.py"
OUTPUT_DIR  = BASE_DIR / "proyectos_generados"
CONFIG_PATH = BASE_DIR / "config.json"
CAMPOS_CONFIG = [
    "MARCA_PORTADA", "MARCA", "LUGAR_FIRMA",
    # Técnico firmante (fijo por empresa)
    "TECNICO_NOMBRE", "TECNICO_COLEGIO", "TECNICO_COLEGIO_ABREV", "TECNICO_NUM_COLEGIADO",
]

# ── Colores ───────────────────────────────────────────────────────────────────
VERDE   = "#2e7d32"
VERDE_H = "#1b5e20"
GRIS_BG = "#f0f2f5"
BLANCO  = "#ffffff"
AZUL    = "#1565c0"
AZUL_L  = "#e8eef7"
ROJO    = "#c62828"

# ── Meses en español ─────────────────────────────────────────────────────────
MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}
MESES_ES_UPPER = {k: v.upper() for k, v in MESES_ES.items()}

# ── Categorías de vehículos ────────────────────────────────────────────────
CATEGORIAS_VEHICULO = [
    "M1 — Turismos (hasta 8 plazas)",
    "M2 — Microbuses (>8 plazas, ≤5 000 kg)",
    "M3 — Autobuses (>8 plazas, >5 000 kg)",
    "N1 — Vehículos de carga ligeros (≤3 500 kg)",
    "N2 — Vehículos de carga medios (3 500-12 000 kg)",
    "N3 — Vehículos de carga pesados (>12 000 kg)",
    "O1 — Remolques ligeros (≤750 kg)",
    "O2 — Remolques medios (750-3 500 kg)",
    "O3 — Remolques pesados (3 500-10 000 kg)",
    "O4 — Remolques muy pesados (>10 000 kg)",
    "L1e — Ciclomotor de 2 ruedas",
    "L2e — Ciclomotor de 3 ruedas",
    "L3e — Motocicleta de 2 ruedas",
    "L4e — Motocicleta con sidecar",
    "L5e — Triciclo a motor",
    "L6e — Cuadriciclo ligero",
    "L7e — Cuadriciclo pesado",
    "T — Tractor agrícola",
    "C — Maquinaria agrícola de cadenas",
    "R — Remolque agrícola",
    "S — Maquinaria intercambiable remolcada",
]

# ── Catálogo oficial de Códigos de Reforma — Manual de Reformas de Vehículos Rev 7.2 ──────────────
# Fuente: MINCOTUR — Revisión 7ª Corrección 2ª (enero 2026), Sección I: Vehículos M, N y O
# Formato: "CODIGO": ("Grupo", "Descripción del acto reglamentario", [categorías M/N/O aplicables])
CODIGOS_REFORMA_V7 = {
    # ── Grupo 1: Identificación ─────────────────────────────────────────────────────────────────────
    "1.1": ("1", "Sustitución total o parcial del bastidor o de la estructura autoportante, cuando la parte sustituida sea la que lleva grabado el número de identificación del vehículo", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "1.2": ("1", "Retroquelado por ausencia, deterioro, desaparición, o modificación del número de identificación del vehículo (VIN)", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "1.3": ("1", "Cambio de emplazamiento de la placa de matricula", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    # ── Grupo 2: Unidad Motriz ─────────────────────────────────────────────────────────────────────
    "2.1": ("2", "Modificación de las características o sustitución de los elementos del sistema de admisión del comburente", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "2.2": ("2", "Modificación de las características o sustitución de los elementos del sistema de alimentación de combustible", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "2.3": ("2", "Modificación o sustitución de la unidad motriz por otra de distintas características", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "2.4": ("2", "Adición o desinstalación de una/s unidad/es motriz/ces para la tracción del vehículo", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "2.5": ("2", "Cambio de emplazamiento de la unidad motriz", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "2.6": ("2", "Modificación o sustitución de las características del sistema de escape: disposición, volumen total, silenciadores, catalizadores o filtros de partículas", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "2.7": ("2", "Modificación de la ubicación, sustitución, adición o reducción del número de depósitos de combustible", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "2.8": ("2", "Modificación del sistema de accionamiento del mando para la aceleración, así como de la ubicación, sustitución, adición o supresión de mandos", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "2.9": ("2", "Modificación de sistemas o de la programación de los mismos que puedan variar la potencia máxima", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "2.10": ("2", "Modificación del sistema de accionamiento para el arranque de la unidad motriz", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "2.11": ("2", "Transformación a Vehículos eléctricos o híbridos y sus modificaciones", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "2.12": ("2", "Vehículos eléctricos o híbridos: modificación, sustitución, adición o reubicación del sistema de acumulación de energía eléctrica", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "2.13": ("2", "Modificación del sistema del control de emisiones para el paso de una etapa Euro a una etapa superior", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "2.14": ("2", "Instalación de sistemas reductores de emisiones en cuanto a NOX y partículas", ['M2', 'M3', 'N1', 'N2', 'N3']),
    "2.15": ("2", "Transformación a Vehículos con uso del hidrógeno como medio de almacenamiento de energía y sus modificaciones (pila de combustible)", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "2.16": ("2", "Transformación a Vehículos con uso del hidrógeno como medio de almacenamiento de energía y sus modificaciones (motor de combustión interna)", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    # ── Grupo 3: Transmisión ─────────────────────────────────────────────────────────────────────
    "3.1": ("3", "Modificación de las características o sustitución del elemento de conexión o desconexión de la transmisión (embrague)", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "3.2": ("3", "Modificación del sistema de accionamiento del embrague, así como de la ubicación, sustitución, adición o supresión de mandos", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "3.3": ("3", "Modificación de la caja de cambios o sustitución por otra de distintas características", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "3.4": ("3", "Modificaciones de las características o sustituciones en los elementos de transmisión por otros diferentes a los del vehículo original", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "3.5": ("3", "Modificación del sistema de tracción a través de la variación del número de ejes motrices", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "3.6": ("3", "Modificación o sustitución del sistema de selección de velocidades por otro de distintas características", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    # ── Grupo 4: Ejes y Ruedas ─────────────────────────────────────────────────────────────────────
    "4.1": ("4", "Sustitución del eje por otro de distintas características o modificación de las características del mismo", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "4.2": ("4", "Modificación de la distancia entre ejes", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "4.3": ("4", "Aumento o disminución del número de ejes", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "4.4": ("4", "Modificaciones o sustituciones en ruedas o instalación/desinstalación de separadores de ruedas que impliquen modificación de la vía", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "4.5": ("4", "Sustitución de neumáticos por otros no equivalentes", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    # ── Grupo 5: Suspensión ─────────────────────────────────────────────────────────────────────
    "5.1": ("5", "Modificación de las características del sistema de suspensión o de algunos de sus componentes elásticos o amortiguadores", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    # ── Grupo 6: Dirección ─────────────────────────────────────────────────────────────────────
    "6.1": ("6", "Modificación del sistema de dirección", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "6.2": ("6", "Cambio de emplazamiento, adición o desinstalación de volante", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "6.3": ("6", "Sustitución del volante por otro de distintas características", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "6.4": ("6", "Instalación o desinstalación de ayudas en el volante", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "6.5": ("6", "Modificación del tipo y modo de mando o incorporación/desinstalación de sistemas avanzados de control del vehículo", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    # ── Grupo 7: Frenos ─────────────────────────────────────────────────────────────────────
    "7.1": ("7", "Modificación de las características del sistema de frenado o de alguno de sus componentes", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "7.2": ("7", "Incorporación/desinstalación de sistemas auxiliares de absorción de energía cinética (sistemas de frenada recuperativa)", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "7.3": ("7", "Modificación de los mandos de accionamiento del freno, así como de la ubicación, sustitución, adición o supresión de los mismos", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    # ── Grupo 8: Carrocería ─────────────────────────────────────────────────────────────────────
    "8.1": ("8", "Reducción de plazas de asiento", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "8.2": ("8", "Aumento de plazas de asiento", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "8.3": ("8", "Sustitución de plazas de asiento por plazas de pie o modificación del número de plazas de pie", ['M2', 'M3']),
    "8.4": ("8", "Acondicionamiento de espacio para la instalación de sillas de ruedas", ['M1', 'M2', 'M3']),
    "8.10": ("8", "Sustitución de asiento por otro distinto", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "8.11": ("8", "Cambio de algún cinturón de seguridad por otro de diferente tipo, número o situación de los puntos de anclaje", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "8.12": ("8", "Instalación de cinturones de seguridad", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "8.20": ("8", "Instalación o desinstalación de elementos permanentes en la zona frontal del interior del habitáculo del vehículo", ['M1']),
    "8.21": ("8", "Instalación o desinstalación de mamparas de separación entre asientos", ['M1']),
    "8.22": ("8", "Modificación, instalación o desinstalación de elementos en la zona de equipaje, o en el espacio destinado a pasajeros para convertirlo en zona de equipaje", ['M1']),
    "8.23": ("8", "Modificación de un autobús para utilizarse como: servicio médico, RTV, vivienda, taller o laboratorio ambulante u otros usos especiales", ['M2', 'M3']),
    "8.24": ("8", "Instalación de Convertidores de corriente continua a corriente alterna", ['M2', 'M3']),
    "8.30": ("8", "Instalación o desinstalación de elementos fijos del espacio destinado a carga y/o equipaje del vehículo que no afecten a la estructura", ['M2', 'M3', 'N1', 'N2', 'N3']),
    "8.31": ("8", "Instalación o desinstalación de elementos fijos que afectan a la estructura del espacio destinado a carga y/o equipaje del vehículo", ['M2', 'M3', 'N1', 'N2', 'N3']),
    "8.33": ("8", "Instalación o desinstalación arco de seguridad interior contra vuelco", ['M1', 'N1', 'N2', 'N3']),
    "8.40": ("8", "Instalación o desinstalación de rampas, elevadores, grúas, plataformas, asideros, peldaños o sistemas de acceso para personas con movilidad reducida (PMR)", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "8.50": ("8", "Transformaciones que modifiquen la longitud del voladizo delantero y/o trasero", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "8.51": ("8", "Modificaciones que afecten a la carrocería de un vehículo", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "8.52": ("8", "Modificación, incorporación o desinstalación de elementos en el exterior del vehículo", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "8.56": ("8", "Adaptación de vehículos para el transporte de mercancías peligrosas o modificación de vehículos ya adaptados para dicho transporte", ['N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "8.60": ("8", "Sustitución o modificación del carrozado de un vehículo", ['N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "8.61": ("8", "Instalación o desinstalación de grúas", ['N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "8.62": ("8", "Incorporación o desinstalación de plataformas elevadoras, así como trampillas o rampas de acceso", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "8.70": ("8", "Transformación a Ambulancias, funerarios, blindados, autocaravanas y sus modificaciones", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "8.80": ("8", "Cambio de clase en M2 y M3", ['M2', 'M3']),
    "8.81": ("8", "Variación del volumen de bodegas o compartimento para equipajes", ['M2', 'M3']),
    # ── Grupo 9: Alumbrado ─────────────────────────────────────────────────────────────────────
    "9.1": ("9", "Adición o desinstalación de cualquier elemento, dispositivo, sistema, componente o unidad técnica independiente del alumbrado", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "9.2": ("9", "Modificación o sustitución de cualquier elemento, dispositivo, sistema, componente o unidad técnica independiente del alumbrado por otro de distintas características", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    # ── Grupo 10: Uniones y Remolques ─────────────────────────────────────────────────────────────────────
    "10.1": ("10", "Instalación o modificación de dispositivos de acoplamiento en vehículos de categorías M y N", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3']),
    "10.2": ("10", "Instalación, modificación o desinstalación de dispositivos de acoplamiento en vehículos de categoría O", ['O1', 'O2', 'O3', 'O4']),
    "10.6": ("10", "Transformación de vehículo remolcado en vehículo remolcado apto para remolcar otro vehículo", ['O4']),
    # ── Grupo 11: Modificaciones Tarjeta ITV ─────────────────────────────────────────────────────────────────────
    "11.0": ("11", "Cambio de alguno de los datos de la tarjeta ITV, cuando no lleva asociada otra transformación del vehículo", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "11.1": ("11", "Cambio de clasificación", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "11.2": ("11", "Variaciones de Masas Máximas Autorizadas", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "11.3": ("11", "Variación de cualquiera de las Masas Máximas Técnicas Admisibles del vehículo", ['M1', 'M2', 'M3', 'N1', 'N2', 'N3', 'O1', 'O2', 'O3', 'O4']),
    "11.5": ("11", "Vehículos para uso exclusivo de pruebas deportivas", ['M1', 'N1', 'N2', 'N3']),
    "11.6": ("11", "Ampliación de combinaciones de vehículos modulares para el transporte especial", ['O4']),
}

# Alias para compatibilidad (el código antiguo usa CODIGOS_REFORMA)
CODIGOS_REFORMA = {k: (v[0], v[1]) for k, v in CODIGOS_REFORMA_V7.items()}


def _codigos_para_categoria(cat_codigo):
    """Devuelve los códigos de reforma aplicables a una categoría (p.ej. 'M1')."""
    if not cat_codigo:
        return list(CODIGOS_REFORMA_V7.keys())
    return [
        cod for cod, (grp, desc, cats) in CODIGOS_REFORMA_V7.items()
        if cat_codigo in cats
    ]


# Directivas por código — datos extraídos del Manual de Reformas V7.2
# Formato: [(sistema, referencia, [M1, M2, M3, N1, N2, N3, O1, O2, O3, O4])]
# Valores: "(1)" última actualización, "(2)" versión matriculación, "(-)" no aplica, "(x)" reforma no posible
DIRECTIVAS_POR_CODIGO = {
    "1.1": [
        ("Placas e inscripciones reglamentarias", "76/114/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
    ],
    "1.2": [
        ("Placas e inscripciones reglamentarias", "76/114/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
    ],
    "1.3": [
        ("Placa de matrícula posterior", "70/222/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Salientes exteriores", "74/483/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Instalación de dispositivos alumbrado y señalización", "76/756/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Salientes exteriores de las cabinas", "92/114/CEE", ["(-)", "(-)", "(-)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
    ],
    "2.1": [
        ("Nivel sonoro admisible", "70/157/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones", "70/220/CEE", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones (Euro 5/6, veh. ligeros)", "Reg. CE Nº 715/2007", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Humos diésel", "72/306/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Salientes exteriores", "74/483/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Campo de visión delantera", "77/649/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones diesel", "88/77/CEE", ["(-)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones (Euro 4/5, veh. pesados)", "Reg. CE Nº 595/2009", ["(-)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "2.2": [
        ("Nivel sonoro admisible", "70/157/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones", "70/220/CEE", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones (Euro 5/6, veh. ligeros)", "Reg. CE Nº 715/2007", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Depósitos de combustible", "70/221/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Frenado", "71/320/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones diesel", "88/77/CEE", ["(-)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones (Euro 4/5, veh. pesados)", "Reg. CE Nº 595/2009", ["(-)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Sistemas de Calefacción", "2001/56/CE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Equipos especiales para GLP", "CEPE/ONU 67R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Equipos especiales para GNC/GNL", "CEPE/ONU 110R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Adaptación a GLP o GNC (retro)", "CEPE/ONU 115R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "2.3": [
        ("Nivel sonoro admisible", "70/157/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones", "70/220/CEE", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones (Euro 5/6, veh. ligeros)", "Reg. CE Nº 715/2007", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Depósitos de combustible", "70/221/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Frenado", "71/320/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones diesel", "88/77/CEE", ["(-)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Neumáticos", "92/23/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Equipos especiales para GLP", "CEPE/ONU 67R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Equipos especiales para GNC/GNL", "CEPE/ONU 110R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Adaptación a GLP o GNC (retro)", "CEPE/ONU 115R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Retro adaptación combustible dual", "CEPE/ONU 143R", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "2.4": [
        ("Nivel sonoro admisible", "70/157/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones", "70/220/CEE", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones (Euro 5/6, veh. ligeros)", "Reg. CE Nº 715/2007", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Depósitos de combustible", "70/221/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Frenado", "71/320/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones diesel", "88/77/CEE", ["(-)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones (Euro 4/5, veh. pesados)", "Reg. CE Nº 595/2009", ["(-)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Neumáticos", "92/23/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Equipos especiales para GLP", "CEPE/ONU 67R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Equipos especiales para GNC/GNL", "CEPE/ONU 110R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Adaptación a GLP o GNC (retro)", "CEPE/ONU 115R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "2.5": [
        ("Nivel sonoro admisible", "70/157/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Frenado", "71/320/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Neumáticos", "92/23/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "2.6": [
        ("Nivel sonoro admisible", "70/157/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones", "70/220/CEE", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones (Euro 5/6, veh. ligeros)", "Reg. CE Nº 715/2007", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Salientes exteriores", "74/483/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Salientes exteriores de las cabinas", "92/114/CEE", ["(-)", "(-)", "(-)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones diesel", "88/77/CEE", ["(-)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones (Euro 4/5, veh. pesados)", "Reg. CE Nº 595/2009", ["(-)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Silenciosos de recambio", "96/20/CE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Catalizadores para recambio", "98/77/CE", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "2.7": [
        ("Depósito de combustible", "70/221/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Masas y dimensiones", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Equipos especiales para GNC/GNL", "CEPE/ONU 110R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Equipos especiales para GLP", "CEPE/ONU 67R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Adaptación a GLP o GNC (retro)", "CEPE/ONU 115R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Protecciones laterales 89/297", "CEE", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(2)", "(2)"]),
    ],
    "2.8": [
        ("Acondicionamiento interior", "74/60/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("conducción en caso de colisión", "74/297/CEE", ["(2)", "(-)", "(-)", "(2)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "2.9": [
        ("Nivel sonoro admisible", "70/157/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones", "70/220/CEE", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones (Euro 5/6, veh. ligeros)", "Reg. CE Nº 715/2007", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Humos diesel", "72/306/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Potencia del motor", "80/1269/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones diesel", "88/77/CEE", ["(-)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones (Euro 4/5, veh. pesados)", "Reg. CE Nº 595/2009", ["(-)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "2.10": [
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Acondicionamiento interior", "74/60/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Antirrobo e inmovilizador", "74/61/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("testigo e indicadores", "78/316/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "2.11": [
        ("Nivel sonoro admisible", "70/157/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones", "70/220/CEE", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones (Euro 5/6, veh. ligeros)", "Reg. CE Nº 715/2007", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Depósitos de combustible", "70/221/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Frenado", "71/320/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones diésel", "88/77/CEE", ["(-)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Neumáticos", "92/23/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones (Euro 4/5, veh. pesados)", "Reg. CE Nº 595/2009", ["(-)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "100R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Equipos especiales para GLP", "CEPE/ONU 67R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Equipos especiales para GNC/GNL", "CEPE/ONU 110R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Adaptación a GLP o GNC (retro)", "CEPE/ONU 115R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Antirrobo e inmovilizador", "74/61/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("indicadores", "78/316/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Mecanismos de dirección", "70/311/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Dispositivos antihielo y antivaho", "78/317/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Dispositivos limpiaparabrisas y lavaparabrisas", "78/318/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Sistemas de Calefacción", "2001/56/CE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "66R", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "2.12": [
        ("Nivel sonoro admisible", "70/157/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Frenado", "71/320/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "100R", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Mecanismos de dirección", "70/311/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "66R", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
    ],
    "2.13": [
    ],
    "2.14": [
    ],
    "2.15": [
        ("Nivel sonoro admisible", "70/157/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones", "70/220/CEE", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Frenado", "71/320/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones diésel", "88/77/CEE", ["(-)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Neumáticos", "92/23/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Nº", "79/2009", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "100R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Antirrobo e inmovilizador", "74/61/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("indicadores", "78/316/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Mecanismos de dirección", "70/311/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Dispositivos antihielo y antivaho", "78/317/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Dispositivos limpiaparabrisas y lavaparabrisas", "78/318/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Sistemas de Calefacción", "2001/56/CE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "66R", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "2.16": [
        ("Nivel sonoro admisible", "70/157/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones", "70/220/CEE", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Depósitos de combustible", "70/221/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Frenado", "71/320/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones diésel", "88/77/CEE", ["(-)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Neumáticos", "92/23/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Nº", "79/2009", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Antirrobo e inmovilizador", "74/61/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("indicadores", "78/316/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Mecanismos de dirección", "70/311/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Dispositivos antihielo y antivaho", "78/317/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Dispositivos limpiaparabrisas y lavaparabrisas", "78/318/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Sistemas de Calefacción", "2001/56/CE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "66R", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "3.1": [
        ("Emisiones (Euro 5/6, veh. ligeros)", "Reg. CE Nº 715/2007", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Humos diésel", "72/306/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "3.2": [
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Acondicionamiento interior", "74/60/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "3.3": [
        ("Nivel sonoro admisible", "70/157/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones", "70/220/CEE", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones (Euro 5/6, veh. ligeros)", "Reg. CE Nº 715/2007", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Frenado", "71/320/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Velocímetro y marcha atrás", "75/443/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Neumáticos", "92/23/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Limitadores de velocidad", "92/24/CEE", ["(-)", "(2)", "(2)", "(-)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "3.4": [
        ("Nivel sonoro admisible", "70/157/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones", "70/220/CEE", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones (Euro 5/6, veh. ligeros)", "Reg. CE Nº 715/2007", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Frenado", "71/320/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Velocímetro y marcha atrás", "75/443/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Neumáticos", "92/23/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Limitadores de velocidad", "92/24/CEE", ["(-)", "(2)", "(2)", "(-)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Instalación de limitadores de velocidad", "92/6/CEE", ["(-)", "(2)", "(2)", "(-)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "3.5": [
        ("Nivel sonoro admisible", "70/157/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones", "70/220/CEE", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Emisiones (Euro 5/6, veh. ligeros)", "Reg. CE Nº 715/2007", ["(2)", "(2)", "(-)", "(2)", "(2)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Mecanismos de dirección", "70/311/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Frenado", "71/320/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "3.6": [
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Acondicionamiento interior", "74/60/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "4.1": [
        ("Nivel sonoro admisible", "70/157/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Depósitos de combustible", "70/221/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Dispositivos de protección trasera", "70/221/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Placa de matrícula posterior", "70/222/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Mecanismos de dirección", "70/311/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Cerraduras y bisagras de las puertas", "70/387/CEE", ["(2)", "(-)", "(-)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Dispositivos de visión indirecta", "2003/97/CE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Frenado", "71/320/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Velocímetro y marcha atrás", "75/443/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("señalización luminosa", "76/756/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Guardabarros", "78/549/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Protección lateral", "89/297/CEE", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(2)", "(2)"]),
        ("Sistemas antiproyección", "91/226/CEE", ["(-)", "(-)", "(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Neumáticos", "92/23/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Protección delantera contra el empotramiento", "2000/40/CE", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Protección de los peatones", "2003/102/CE", ["(2)", "(-)", "(-)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Sistemas de protección delantera", "2005/66/CE", ["(2)", "(-)", "(-)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
    ],
    "4.2": [
        ("Depósitos de combustible", "70/221/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Dispositivos de protección trasera", "70/221/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Mecanismos de dirección", "70/311/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Frenado", "71/320/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("señalización luminosa", "76/756/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Guardabarros", "78/549/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Protección lateral", "89/297/CEE", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(2)", "(2)"]),
        ("Sistemas antiproyección", "91/226/CEE", ["(-)", "(-)", "(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Neumáticos", "92/23/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Protección delantera contra el empotramiento", "2000/40/CE", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Protección de los peatones", "2003/102/CE", ["(2)", "(-)", "(-)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Sistemas de protección delantera", "2005/66/CE", ["(2)", "(-)", "(-)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
    ],
    "4.3": [
        ("Nivel sonoro admisible", "70/157/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Depósitos de combustible", "70/221/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Dispositivos de protección trasera", "70/221/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Placa de matrícula posterior", "70/222/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Mecanismos de dirección", "70/311/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Frenado", "71/320/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Velocímetro y marcha atrás", "75/443/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("señalización luminosa", "76/756/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Guardabarros", "78/549/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Protección lateral", "89/297/CEE", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(2)", "(2)"]),
        ("Sistemas antiproyección", "91/226/CEE", ["(-)", "(-)", "(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Neumáticos", "92/23/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Protección delantera contra el empotramiento", "2000/40/CE", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Protección de los peatones", "2003/102/CE", ["(2)", "(-)", "(-)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Sistemas de protección delantera", "2005/66/CE", ["(2)", "(-)", "(-)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
    ],
    "4.4": [
        ("Dispositivos de protección trasera", "70/221/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Mecanismos de dirección", "70/311/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Guardabarros", "78/549/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Protección lateral", "89/297/CEE", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(2)", "(2)"]),
        ("Sistemas antiproyección", "91/226/CEE", ["(-)", "(-)", "(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Neumáticos", "92/23/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Protección delantera contra empotramiento", "2000/40/CE", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
    ],
    "4.5": [
        ("Nivel sonoro admisible", "70/157/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Dispositivos de protección trasera", "70/221/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Placa de matrícula posterior", "70/222/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Mecanismos de dirección", "70/311/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Cerraduras y bisagras de las puertas", "70/387/CEE", ["(2)", "(-)", "(-)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Dispositivos de visión indirecta", "2003/97/CE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Frenado", "71/320/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Velocímetro y marcha atrás", "75/443/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("señalización luminosa", "76/756/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Guardabarros", "78/549/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Protección lateral", "89/297/CEE", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(2)", "(2)"]),
        ("Sistemas antiproyección", "91/226/CEE", ["(-)", "(-)", "(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Neumáticos", "92/23/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Protección delantera contra el empotramiento", "2000/40/CE", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Protección de los peatones", "2003/102/CE", ["(2)", "(-)", "(-)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Sistemas de protección delantera", "2005/66/CE", ["(2)", "(-)", "(-)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
    ],
    "5.1": [
        ("Dispositivos de protección trasera", "70/221/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Placa de matrícula posterior", "70/222/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Dispositivos de visión indirecta", "2003/97/CE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Frenado", "71/320/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("señalización luminosa", "76/756/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Guardabarros", "78/549/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Protección lateral", "89/297/CEE", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(2)", "(2)"]),
        ("Sistemas antiproyección", "91/226/CEE", ["(-)", "(-)", "(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Dispositivos de acoplamiento", "94/20/CE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Protección delantera contra el empotramiento", "2000/40/CE", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Protección de los peatones", "2003/102/CE", ["(2)", "(-)", "(-)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Sistemas de protección delantera", "2005/66/CE", ["(2)", "(-)", "(-)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
    ],
    "6.1": [
        ("Mecanismos de dirección", "70/311/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
    ],
    "6.2": [
        ("Mecanismos de dirección", "70/311/CEE", ["(2)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Dispositivos de visión indirecta", "2003/97/CE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Antirrobo e inmovilizador", "74/61/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("conducción en caso de colisión", "74/297/CEE", ["(2)", "(-)", "(-)", "(2)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("señalización", "76/756/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Campo de visión delantera", "77/649/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("indicadores", "78/316/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Dispositivos antihielo y antivaho", "78/317/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Lava/limpiaparabrisas", "78/318/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Autobuses y autocares", "2001/85/CE", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "36R", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "52R", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "107R", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "6.3": [
        ("Mecanismos de dirección", "70/311/CEE", ["(2)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("conducción en caso de colisión", "74/297/CEE", ["(2)", "(-)", "(-)", "(2)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("indicadores", "78/316/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "6.4": [
        ("Mecanismos de dirección", "70/311/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Acondicionamiento interior", "74/60/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("conducción en caso de colisión", "74/297/CEE", ["(2)", "(-)", "(-)", "(2)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("indicadores", "78/316/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "6.5": [
        ("Mecanismos de dirección", "70/311/CEE", ["(1)", "(-)", "(-)", "(1)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Acondicionamiento interior", "74/60/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("conducción en caso de colisión", "74/297/CEE", ["(2)", "(-)", "(-)", "(2)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "7.1": [
        ("Mecanismos de dirección", "70/311/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Frenado", "71/320/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Acondicionamiento interior", "74/60/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
    ],
    "7.2": [
        ("Frenado", "71/320/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
    ],
    "7.3": [
        ("Frenado", "71/320/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Acondicionamiento interior", "74/60/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
    ],
    "8.1": [
        ("Resistencia de los asientos", "74/408/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Anclajes de los cinturones de seguridad", "76/115/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("retención", "77/541/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Autobuses y autocares", "2001/85/CE", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "36R", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "52R", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "107R", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "66R", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "8.2": [
        ("Resistencia de los asientos", "74/408/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Anclajes de los cinturones de seguridad", "76/115/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("retención", "77/541/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Inflamabilidad", "95/28/CE", ["(-)", "(-)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("97/27/CE", "", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Autobuses y autocares", "2001/85/CE", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "36R", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "52R", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "107R", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "66R", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "8.3": [
        ("Inflamabilidad", "95/28/CE", ["(x)", "(-)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(x)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("Autobuses y autocares", "2001/85/CE", ["(x)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "36R", ["(x)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "52R", ["(x)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "107R", ["(x)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "66R", ["(x)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "8.4": [
        ("Anexo XI", "2007/46/CE", ["(1)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("Anclajes de los cinturones de seguridad", "76/115/CEE", ["(-)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("retención", "77/541/CEE", ["(-)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("Inflamabilidad", "95/28/CE", ["(-)", "(-)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("VII)", "", ["(-)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "36R", ["(-)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "52R", ["(-)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "66R", ["(-)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "8.10": [
        ("Cerraduras y bisagras", "70/387/CEE", ["(2)", "(-)", "(-)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Dispositivos de visión indirecta", "2003/97/CE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Acondicionamiento interior", "74/60/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Resistencia de los asientos", "74/408/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Anclajes de los cinturones de seguridad", "76/115/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("retención", "77/541/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Inflamabilidad", "95/28/CE", ["(-)", "(-)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Autobuses y autocares", "2001/85/CE", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "36R", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "52R", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "107R", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "66R", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "8.11": [
        ("Resistencia de los asientos", "74/408/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Anclajes de los cinturones de seguridad", "76/115/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("retención", "77/541/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Inflamabilidad", "95/28/CE", ["(-)", "(-)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "8.12": [
        ("Resistencia de los asientos", "74/408/CEE", ["(2)", "(1)", "(1)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Anclajes de los cinturones de seguridad", "76/115/CEE", ["(2)", "(1)", "(1)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("retención", "77/541/CEE", ["(2)", "(1)", "(1)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Inflamabilidad", "95/28/CE", ["(-)", "(-)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "66R", ["(-)", "(1)", "(1)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "8.20": [
        ("Acondicionamiento interior", "74/60/CEE", ["(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("indicadores", "78/316/CEE", ["(1)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("Campo de visión delantera", "77/649/CEE", ["(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("Dispositivos de visión indirecta*", "2003/97CE", ["(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "8.21": [
        ("Acondicionamiento interior", "74/60/CEE", ["(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("Resistencia de los asientos", "74/408/CEE", ["(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("Anclajes de los cinturones de seguridad", "76/115/CEE", ["(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("retención", "77/541/CEE", ["(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "8.22": [
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("Acondicionamiento interior", "74/60/CEE", ["(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("Resistencia de los asientos", "74/408/CEE", ["(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("Anclajes de los cinturones de seguridad", "76/115/CEE", ["(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("retención", "77/541/CEE", ["(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("Apoyacabezas", "78/932/CEE", ["(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("Sistemas de Calefacción", "2001/56/CE", ["(1)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "8.23": [
        ("Limitador de velocidad", "92/6/CEE", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
    ],
    "8.24": [
        ("CEPE/ONU", "36R", ["(x)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "52R", ["(x)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "107R", ["(x)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(x)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "8.30": [
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("indicadores", "78/316/CEE", ["(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Autobuses y Autocares", "2001/85/CE", ["(x)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "36R", ["(x)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "52R", ["(x)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "107R", ["(x)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Cristales de seguridad", "92/22/CEE", ["(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Retrovisores / Dispositivos de visión indirecta", "2003/97/CE", ["(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Inflamabilidad 95/28/CE *", "*", ["(x)", "(1)", "(1)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "8.31": [
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("indicadores", "78/316/CEE", ["(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Autobuses y Autocares", "2001/85/CE", ["(x)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "36R", ["(x)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "52R", ["(x)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "107R", ["(x)", "(2)", "(2)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Sistemas de Calefacción", "2001/56/CE", ["(x)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "8.33": [
        ("Acondicionamiento interior", "74/60/CEE", ["(2)", "(x)", "(x)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(x)", "(x)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(x)", "(x)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "8.40": [
        ("Cerraduras y bisagras", "70/387/CEE", ["(2)", "(-)", "(-)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Acondicionamiento interior", "74/60/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("VII)", "", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
    ],
    "8.50": [
        ("Dispositivos de protección trasera", "70/221/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Placa de matrícula posterior", "70/222/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Mecanismos de dirección", "70/311/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Dispositivos de visión indirecta", "2003/97/CE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Salientes exteriores", "74/483/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("señalización luminosa", "76/756/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Salientes exteriores de las cabinas", "92/114/CEE", ["(-)", "(-)", "(-)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Protección delantera contra el empotramiento", "2000/40/CE", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Dispositivos de acoplamiento", "94/20/CE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Protección de los peatones", "2003/102/CE", ["(2)", "(-)", "(-)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
    ],
    "8.51": [
        ("Dispositivos de protección trasera", "70/221/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Placa de matrícula posterior", "70/222/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Cerraduras y bisagras de las puertas", "70/387/CEE", ["(2)", "(-)", "(-)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Autobuses y autocares", "2001/85/CE", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Salientes exteriores", "74/483/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Dispositivos de remolcado", "77/389/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("señalización luminosa", "76/756/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Campo de visión delantera", "77/649/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Lava/limpiaparabrisas", "78/318/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Guardabarros", "78/549/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Sistemas antiproyección", "91/226/CEE", ["(-)", "(-)", "(-)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Cristales de seguridad", "92/22/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(2)", "(2)", "(2)", "(2)"]),
        ("Salientes exteriores de las cabinas", "92/114/CEE", ["(-)", "(-)", "(-)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Colisión frontal", "96/79/CE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Protección delantera contra el empotramiento", "2000/40/CE", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Sistemas de protección delantera", "2005/66/CE", ["(2)", "(-)", "(-)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("CEPE/ONU", "66R", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Protección de los peatones", "2003/102/CE", ["(2)", "(-)", "(-)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("CEPE/ONU", "29R", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
    ],
    "8.52": [
        ("Dispositivos de protección trasera", "70/221/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Placa de matrícula posterior", "70/222/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Cerraduras y bisagras de las puertas", "70/387/CEE", ["(2)", "(-)", "(-)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Autobuses y Autocares", "2001/85/CE", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Salientes exteriores", "74/483/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("señalización luminosa", "76/756/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Protección lateral", "89/297/CEE", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(2)", "(2)"]),
        ("Dispositivos de remolcado", "77/389/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Campo de visión delantera", "77/649/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Lava/limpiaparabrisas", "78/318/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Guardabarros", "78/549/CEE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Sistemas antiproyección", "91/226/CEE", ["(-)", "(-)", "(-)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Cristales de seguridad", "92/22/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Salientes exteriores de las cabinas", "92/114/CEE", ["(-)", "(-)", "(-)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Colisión frontal", "96/79/CE", ["(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Colisión lateral", "96/27/CE", ["(2)", "(-)", "(-)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Protección delantera contra el empotramiento", "2000/40/CE", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Dispositivo de visión indirecta", "2003/97/CE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Sistemas de protección delantera", "2005/66/CE", ["(2)", "(-)", "(-)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("CEPE/ONU", "66R", ["(-)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Protección de los peatones", "2003/102/CE", ["(2)", "(-)", "(-)", "(2)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("CEPE/ONU", "29R", ["(-)", "(-)", "(-)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
    ],
    "8.56": [
        ("Dispositivos de protección trasera", "70/221/CEE", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Placa de matrícula posterior", "70/222/CEE", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Frenado", "71/320/CEE", ["(x)", "(x)", "(x)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("señalización luminosa", "76/756/CEE", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Protección lateral", "89/297/CEE", ["(x)", "(x)", "(x)", "(-)", "(2)", "(2)", "(-)", "(-)", "(2)", "(2)"]),
        ("Sistemas antiproyección", "91/226/CEE", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Dispositivos de acoplamiento", "94/20/CE", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Limitadores de velocidad", "92/24/CEE", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(x)", "(x)", "(x)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("mercancías peligrosas", "98/91/CE", ["(x)", "(x)", "(x)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("CEPE/ONU 111", "R", ["(x)", "(x)", "(x)", "(-)", "(1)", "(1)", "(-)", "(-)", "(1)", "(1)"]),
    ],
    "8.60": [
        ("Dispositivos de protección trasera", "70/221/CEE", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Placa de matrícula posterior", "70/222/CEE", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Dispositivos de visión indirecta", "2003/97/CE", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("señalización luminosa", "76/756/CEE", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Protección lateral", "89/297/CEE", ["(x)", "(x)", "(x)", "(-)", "(2)", "(2)", "(-)", "(-)", "(2)", "(2)"]),
        ("Sistemas antiproyección", "91/226/CEE", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Dispositivos de acoplamiento", "94/20/CE", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(x)", "(x)", "(x)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("CEPE/ONU", "111R", ["(x)", "(x)", "(x)", "(-)", "(2)", "(2)", "(-)", "(-)", "(2)", "(2)"]),
        ("CEPE/ONU", "29R", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
    ],
    "8.61": [
        ("Dispositivos de protección trasera", "70/221/CEE", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Placa de matrícula posterior", "70/222/CEE", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Dispositivos de visión indirecta", "2003/97/CE", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("señalización luminosa", "76/756/CEE", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Protección lateral", "89/297/CEE", ["(x)", "(x)", "(x)", "(-)", "(2)", "(2)", "(-)", "(-)", "(2)", "(2)"]),
        ("Sistemas antiproyección", "91/226/CEE", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(x)", "(x)", "(x)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("CEPE/ONU", "29R", ["(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
    ],
    "8.62": [
        ("Dispositivos de protección trasera", "70/221/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Placa de matrícula posterior", "70/222/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("señalización luminosa", "76/756/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Protección lateral", "89/297/CEE", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(2)", "(2)"]),
        ("Sistemas antiproyección", "91/226/CEE", ["(-)", "(-)", "(-)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
    ],
    "8.70": [
        ("Anexo XI", "2007/46/CE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "8.80": [
        ("Inflamabilidad", "95/28/CE", ["(x)", "(-)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(x)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("Autobuses y autocares", "2001/85/CE", ["(x)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "36R", ["(x)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "52R", ["(x)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "107R", ["(x)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "66R", ["(x)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "8.81": [
        ("Inflamabilidad", "95/28/CE", ["(x)", "(-)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(x)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("Autobuses y autocares", "2001/85/CE", ["(x)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "36R", ["(x)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "52R", ["(x)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "107R", ["(x)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "9.1": [
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("señalización luminosa", "76/756/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Catadióptricos", "76/757/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("76/758/CEE", "", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Indicadores de dirección", "76/759/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("matrícula posterior", "76/760/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("lámparas)", "76/761/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Luces antiniebla delanteras", "76/762/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Luces antiniebla traseras", "77/538/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Luces de marcha atrás", "77/539/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Luces de estacionamiento", "77/540/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("indicadores", "78/316/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("CEPE/ONU", "45R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("CEPE/ONU", "70R", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(2)", "(2)"]),
        ("CEPE/ONU", "87R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("CEPE/ONU", "91R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("CEPE/ONU", "104R", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(2)", "(2)"]),
        ("CEPE/ONU", "123R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
    ],
    "9.2": [
        ("Parásitos radioeléctricos (compat. EM)", "72/245/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("señalización luminosa", "76/756/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Catadióptricos", "76/757/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("76/758/CEE", "", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Indicadores de dirección", "76/759/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("matrícula posterior", "76/760/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Proyectores (incluidas las lámparas)", "76/761/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Luces antiniebla delanteras", "76/762/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Luces antiniebla traseras", "77/538/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Luces de marcha atrás", "77/539/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Luces de estacionamiento", "77/540/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("indicadores", "78/316/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("CEPE/ONU", "45R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("CEPE/ONU", "70R", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(2)", "(2)"]),
        ("CEPE/ONU", "87R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("CEPE/ONU", "91R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("CEPE/ONU", "104R", ["(-)", "(-)", "(-)", "(-)", "(2)", "(2)", "(-)", "(-)", "(2)", "(2)"]),
        ("CEPE/ONU", "123R", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
    ],
    "10.1": [
        ("Dispositivos de protección trasera 70/221/CEE (*)", "(*)", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Dispositivos de remolcado 77/389/CEE (*)", "(*)", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("señalización luminosa 76/756/CEE (*)", "(*)", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (automóviles) 92/21/CEE", "(*)", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
        ("Masas y dimensiones (resto vehículos) 97/27/CE", "(*)", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(x)", "(x)", "(x)", "(x)"]),
        ("Dispositivos de acoplamiento", "94/20/CE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("Instalación del dispositivo Anexo VII", "94/20/CE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(x)", "(x)", "(x)", "(x)"]),
        ("CEPE/ONU", "107R", ["(-)", "(1)", "(1)", "(-)", "(-)", "(-)", "(x)", "(x)", "(x)", "(x)"]),
    ],
    "10.2": [
        ("señalización luminosa", "76/756/CEE", ["(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(2)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(1)", "(1)", "(1)", "(1)"]),
        ("Dispositivos de acoplamiento", "94/20/CE", ["(x)", "(x)", "(x)", "(x)", "(x)", "(x)", "(2)", "(2)", "(2)", "(2)"]),
    ],
    "10.6": [
        ("Dispositivos de protección trasera", "70/221/CEE", ["(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(2)"]),
        ("Placa de matrícula posterior", "70/222/CEE", ["(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(2)"]),
        ("señalización luminosa", "76/756/CEE", ["(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(2)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(1)"]),
        ("Dispositivos de acoplamiento", "94/20/CE", ["(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(1)"]),
        ("Instalación del dispositivo Anexo VII", "94/20/CE", ["(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(1)"]),
        ("Frenado", "71/320/CEE", ["(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(1)"]),
    ],
    "11.0": [
    ],
    "11.1": [
    ],
    "11.2": [
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
    ],
    "11.3": [
        ("Dispositivos de protección trasera", "70/221/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("Mecanismos de dirección", "70/311/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Frenado", "71/320/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Dispositivos de remolcado de vehículos", "77/389/CEE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(-)", "(-)", "(-)", "(-)"]),
        ("Masas y dimensiones (automóviles)", "92/21/CEE", ["(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("Neumáticos", "92/23/CEE", ["(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Masas y dimensiones (resto vehículos)", "97/27/CE", ["(-)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)", "(1)"]),
        ("Dispositivos de acoplamiento", "94/20/CE", ["(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)", "(2)"]),
        ("CEPE/ONU", "107R", ["(-)", "(1)", "(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
        ("CEPE/ONU", "66R", ["(-)", "(1)", "(1)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)"]),
    ],
    "11.5": [
    ],
    "11.6": [
        ("Dispositivos de protección trasera", "70/221/CEE", ["(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(2)"]),
        ("Placa de matrícula posterior", "70/222/CEE", ["(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(2)"]),
        ("señalización luminosa", "76/756/CEE", ["(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(2)"]),
        ("Masas y dimensiones", "97/27/CE", ["(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(2)"]),
        ("Dispositivos de acoplamiento", "94/20/CE", ["(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(2)"]),
        ("Instalación del dispositivo Anexo VII", "94/20/CE", ["(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(2)"]),
        ("Frenado", "71/320/CEE", ["(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(2)"]),
        ("Sistemas antiproyección", "91/226/CEE", ["(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(2)"]),
        ("Cristales de seguridad", "92/22/CEE", ["(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(2)"]),
        ("Mecanismos de dirección", "70/311/CEE", ["(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(2)"]),
        ("Protección lateral", "89/297/CEE", ["(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(2)"]),
        ("Neumáticos", "92/23/CEE", ["(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(2)"]),
        ("Compatibilidad electromagnética", "72/245/CEE", ["(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(-)", "(2)"]),
    ],
}


def _get_output_dir() -> Path:
    """
    Devuelve la carpeta de salida configurada en config.json.
    Si no hay configuración o la ruta no existe aún, devuelve el valor por defecto.
    La ruta se resuelve en tiempo de ejecución para que el cambio en
    Configuración → Ruta de guardado se aplique de inmediato sin reiniciar.
    """
    try:
        if CONFIG_PATH.exists():
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            p = cfg.get("OUTPUT_PATH", "").strip()
            if p:
                return Path(p)
    except Exception:
        pass
    return OUTPUT_DIR


def _detectar_drives_rapidos() -> dict:
    """
    Detecta unidades de almacenamiento disponibles para acceso rápido.
    Devuelve {etiqueta: ruta_str}.
    """
    encontrados = {}
    home = Path.home()

    # OneDrive personal / empresarial
    for p in [
        home / "OneDrive",
        home / "OneDrive - Phican Ingenieros",
        home / "OneDrive - Phican",
        home / "OneDrive - Personal",
    ]:
        if p.exists():
            encontrados["☁ OneDrive"] = str(p)
            break

    # Google Drive (Drive for Desktop monta en letras)
    for letter in "GHIJKLMNOPQRSTUVWXYZ":
        for sub in ["Mi unidad", "My Drive", ""]:
            p = Path(f"{letter}:\\{sub}") if sub else Path(f"{letter}:\\")
            if p.exists():
                try:
                    import subprocess
                    r = subprocess.run(
                        f"vol {letter}:", capture_output=True, text=True, shell=True
                    )
                    if "google" in r.stdout.lower():
                        encontrados[f"☁ Google Drive ({letter}:)"] = str(p)
                        break
                except Exception:
                    pass

    # Unidad Z: red (Estudio PhicanServer)
    z = Path("Z:\\")
    if z.exists():
        encontrados["🖥 Z: Estudio (red)"] = str(z)

    # Otras unidades de red (tipo 4) que no sean Z:
    try:
        import subprocess
        r = subprocess.run(
            "wmic logicaldisk get Caption,DriveType,VolumeName",
            capture_output=True, text=True, shell=True
        )
        for line in r.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "4":
                letra = parts[0].rstrip(":")
                if letra.upper() != "Z":
                    p = Path(f"{letra}:\\")
                    if p.exists():
                        nombre = " ".join(parts[2:]) if len(parts) > 2 else ""
                        encontrados[f"🖥 {letra}: {nombre}".strip()] = str(p)
    except Exception:
        pass

    return encontrados


def siguiente_referencia():
    """
    Escanea la carpeta de salida configurada buscando subcarpetas con formato
    PH.NNN-YYYY y devuelve la siguiente referencia libre. Formato: PH.NNN/YYYY-0
    """
    hoy = datetime.now()
    anio = hoy.year
    max_num = 0

    patron_dir = re.compile(r"PH\.(\d+)-(\d{4})$", re.IGNORECASE)
    carpeta = _get_output_dir()
    if carpeta.exists():
        for d in carpeta.iterdir():
            if not d.is_dir():
                continue
            m = patron_dir.match(d.name)
            if m:
                num, anio_f = int(m.group(1)), int(m.group(2))
                if anio_f == anio:
                    max_num = max(max_num, num)

    return f"PH.{max_num + 1:03d}/{anio}-0"


def _listar_proyectos_revisables():
    """
    Devuelve lista de cadenas "PH.NNN-YYYY — RevN" para cada proyecto/revisión
    existente en la carpeta de salida configurada, ordenada por referencia.
    """
    carpeta = _get_output_dir()
    if not carpeta.exists():
        return []
    patron_dir = re.compile(r"PH\.(\d+)-(\d{4})$", re.IGNORECASE)
    patron_rev = re.compile(r"Rev(\d+)$", re.IGNORECASE)
    items = []
    for d in sorted(carpeta.iterdir()):
        if not d.is_dir():
            continue
        if not patron_dir.match(d.name):
            continue
        for rev_d in sorted(d.iterdir()):
            if not rev_d.is_dir():
                continue
            rm = patron_rev.match(rev_d.name)
            if rm and (rev_d / "datos.json").exists():
                items.append(f"{d.name} — {rev_d.name}")
    return items


def fecha_hoy_es():
    hoy = datetime.now()
    return f"{hoy.day} de {MESES_ES[hoy.month]} de {hoy.year}"


def mes_anio_hoy_es():
    hoy = datetime.now()
    return f"{MESES_ES_UPPER[hoy.month]} {hoy.year}"


# ── Tablas de tornillería métrica (EN ISO 898-1 / EN 1993-1-8) ───────────────
# A_bruta: área sección transversal bruta (mm²)
# A_s:     área resistente a tracción / corte en la rosca (mm²)
TORNILLO_DIAMETROS = ["M6", "M8", "M10", "M12", "M14", "M16", "M18",
                      "M20", "M22", "M24", "M27", "M30"]
TORNILLO_AREAS = {
    "M6":  {"d": 6,  "A_bruta":  28.3,  "A_s":  20.1},
    "M8":  {"d": 8,  "A_bruta":  50.3,  "A_s":  36.6},
    "M10": {"d": 10, "A_bruta":  78.5,  "A_s":  58.0},
    "M12": {"d": 12, "A_bruta": 113.1,  "A_s":  84.3},
    "M14": {"d": 14, "A_bruta": 153.9,  "A_s": 115.0},
    "M16": {"d": 16, "A_bruta": 201.1,  "A_s": 157.0},
    "M18": {"d": 18, "A_bruta": 254.5,  "A_s": 192.0},
    "M20": {"d": 20, "A_bruta": 314.2,  "A_s": 245.0},
    "M22": {"d": 22, "A_bruta": 380.1,  "A_s": 303.0},
    "M24": {"d": 24, "A_bruta": 452.4,  "A_s": 353.0},
    "M27": {"d": 27, "A_bruta": 572.6,  "A_s": 459.0},
    "M30": {"d": 30, "A_bruta": 706.9,  "A_s": 561.0},
}

# Calidades de tornillo: fyb = límite elástico (MPa), fub = resistencia última (MPa)
TORNILLO_CALIDADES_LIST = ["4.6", "5.6", "6.8", "8.8", "10.9", "12.9"]
TORNILLO_CALIDADES = {
    "4.6":  {"fyb": 240,  "fub":  400, "alpha_v": 0.6},
    "5.6":  {"fyb": 300,  "fub":  500, "alpha_v": 0.6},
    "6.8":  {"fyb": 480,  "fub":  600, "alpha_v": 0.6},
    "8.8":  {"fyb": 640,  "fub":  800, "alpha_v": 0.5},
    "10.9": {"fyb": 900,  "fub": 1000, "alpha_v": 0.5},
    "12.9": {"fyb": 1080, "fub": 1200, "alpha_v": 0.5},
}
GAMMA_M2 = 1.25   # coeficiente parcial de seguridad EN 1993-1-8

TORNILLO_TIPO_CORTE = ["Corte simple (1 plano)", "Corte doble (2 planos)",
                       "Tracción pura", "Combinado cortante + tracción"]
TORNILLO_ACABADO_EXT = ["Acero inoxidable A2-70", "Acero inoxidable A4-80",
                        "Galvanizado en caliente", "Galvanizado electrolítico",
                        "Cadmiado", "Pavonado + engrase"]
TORNILLO_CLASE_CORR  = ["C1 — Interior seco", "C2 — Interior húmedo / exterior cubierto",
                        "C3 — Exterior urbano / industrial leve",
                        "C4 — Exterior industrial / marino moderado",
                        "C5 — Marino / industrial severo"]

def calcular_resistencias_tornillo(diametro: str, calidad: str,
                                   tipo_corte: str) -> dict:
    """Calcula Fv,Rd y Ft,Rd según EN 1993-1-8 para un tornillo."""
    if diametro not in TORNILLO_AREAS or calidad not in TORNILLO_CALIDADES:
        return {}
    ta = TORNILLO_AREAS[diametro]
    tc = TORNILLO_CALIDADES[calidad]
    fub    = tc["fub"]
    alpha_v = tc["alpha_v"]
    A_s    = ta["A_s"]
    A_b    = ta["A_bruta"]
    # Área en cortante: rosca (A_s) si doble plano, bruta si plano en vástago
    A_v    = A_s
    # Resistencia a cortante por plano de corte (N)
    Fv_Rd_1plano = (alpha_v * fub * A_v) / GAMMA_M2
    planos = 2 if "doble" in tipo_corte.lower() else 1
    Fv_Rd  = Fv_Rd_1plano * planos
    # Resistencia a tracción (N)
    Ft_Rd  = (0.9 * fub * A_s) / GAMMA_M2
    return {
        "Fv_Rd_1plano_N": round(Fv_Rd_1plano, 1),
        "Fv_Rd_N":        round(Fv_Rd, 1),
        "Ft_Rd_N":        round(Ft_Rd, 1),
        "A_s_mm2":        A_s,
        "A_bruta_mm2":    A_b,
        "fub_MPa":        fub,
        "fyb_MPa":        tc["fyb"],
    }


# ── Tabla completa de métricas (M3–M39) para cálculos con c. aerodinámica ────
TORN_METRICAS_ALL = {
    "M3":   {"d": 3.0,  "De": 2.39,  "At": 5.03},
    "M3.5": {"d": 3.5,  "De": 2.76,  "At": 6.78},
    "M4":   {"d": 4.0,  "De": 3.14,  "At": 8.78},
    "M5":   {"d": 5.0,  "De": 4.02,  "At": 14.18},
    "M6":   {"d": 6.0,  "De": 4.77,  "At": 20.12},
    "M7":   {"d": 7.0,  "De": 5.77,  "At": 28.86},
    "M8":   {"d": 8.0,  "De": 6.47,  "At": 36.61},
    "M10":  {"d": 10.0, "De": 8.16,  "At": 57.99},
    "M12":  {"d": 12.0, "De": 9.85,  "At": 84.27},
    "M14":  {"d": 14.0, "De": 11.55, "At": 115.4},
    "M16":  {"d": 16.0, "De": 13.55, "At": 156.7},
    "M18":  {"d": 18.0, "De": 14.93, "At": 192.5},
    "M20":  {"d": 20.0, "De": 16.93, "At": 244.8},
    "M22":  {"d": 22.0, "De": 18.93, "At": 303.4},
    "M24":  {"d": 24.0, "De": 20.32, "At": 352.5},
    "M27":  {"d": 27.0, "De": 23.32, "At": 459.4},
    "M30":  {"d": 30.0, "De": 25.71, "At": 560.6},
    "M33":  {"d": 33.0, "De": 28.71, "At": 693.6},
    "M36":  {"d": 36.0, "De": 31.09, "At": 816.7},
    "M39":  {"d": 39.0, "De": 34.09, "At": 975.8},
}
TORN_METRICAS_ALL_LIST = list(TORN_METRICAS_ALL.keys())

# Calidades de tornillo (completas — EN ISO 898-1)
TORN_CALIDADES_ALL = {
    "4.6":  {"fyb": 240,  "fub": 400},
    "5.6":  {"fyb": 300,  "fub": 500},
    "6.8":  {"fyb": 480,  "fub": 600},
    "8.8":  {"fyb": 640,  "fub": 800},
    "10.9": {"fyb": 900,  "fub": 1000},
    "12.9": {"fyb": 1080, "fub": 1200},
}
TORN_CALIDADES_ALL_LIST = list(TORN_CALIDADES_ALL.keys())

# Chapas estructurales (fy / fu)
CHAPA_MAT = {
    "s235": {"fy": 235, "fu": 510},
    "s275": {"fy": 275, "fu": 580},
    "s355": {"fy": 355, "fu": 680},
}
CHAPA_MAT_LIST = list(CHAPA_MAT.keys())

# Adhesivos (resistencia característica a cortante, N/mm²)
ADHESIVOS = {
    "Sikaflex-11 FC Extreme Grab (Elem. Pesados)": 8.0,
    "Sikaflex-252 (Superficies Grandes)":          4.0,
    "Sikaflex-263 (Parabrisas / Cristales)":       7.0,
    "Sikaflex-117 (Pegado de Metales)":            5.0,
    "Cianocrilato Wurth":                          4.0,
    "Cinta 2 caras 3M Acrylic Plus":               0.55,
}
ADHESIVOS_LIST = list(ADHESIVOS.keys())

# Materiales para tacos de elevación (resist. a compresión, N/mm²)
TACOS_MAT = {
    "Poliuretano (Shore 90A-95A)":          30,
    "Poliuretano Extra Duro (Shore 75D)":   70,
    "Nylon 6 (PA6)":                        65,
    "Nylon 66 (PA66)":                      80,
    "Nylon 66 + Fibra Vidrio (PA66-GF30)": 180,
    "Teflon (PTFE)":                        10,
    "PTFE + Fibra de Vidrio":               18,
    "Aluminio 6061-T6":                    270,
    "Acero (S275)":                        275,
}
TACOS_MAT_LIST = list(TACOS_MAT.keys())


def calcular_carga_aerodinamica(Cx, V_kmh, ancho_cm, alto_cm, Pp_kg):
    """
    Fuerza aerodinámica sobre un elemento:
    Fx = Cx · 0.5 · V² · ρ · A  (A = 0.8 · ancho · alto)
    F_total = Fx + Pp·g
    """
    rho  = 1.2             # kg/m³ densidad del aire
    V_ms = V_kmh / 3.6
    A    = 0.8 * (ancho_cm / 100) * (alto_cm / 100)   # m²
    Fx   = Cx * 0.5 * V_ms**2 * rho * A               # N
    Pp_N = Pp_kg * 9.81
    return {"Fx_N": round(Fx, 2), "Pp_N": round(Pp_N, 2),
            "F_calc_N": round(Fx + Pp_N, 2), "A_m2": round(A, 4)}


def calcular_union_atornillada_aero(Cx, V_kmh, ancho_cm, alto_cm, Pp_kg,
                                     metrica, calidad, chapa, t_min_mm):
    """
    Unión atornillada con carga aerodinámica (metodología Calculo de Elementos.xlsx).
    Checks: tracción (Nu = 0.8·fyb·At), cortadura (Nt = 4F/(0.65·fyb·At)),
    aplastamiento (Nt = F/(De·(fy_chapa/1.25)·t_min)).
    """
    import math
    aero  = calcular_carga_aerodinamica(Cx, V_kmh, ancho_cm, alto_cm, Pp_kg)
    F     = aero["F_calc_N"]
    tm    = TORN_METRICAS_ALL.get(metrica, {})
    tc    = TORN_CALIDADES_ALL.get(calidad, {})
    ch    = CHAPA_MAT.get(chapa.lower(), {})
    if not tm or not tc or not ch or t_min_mm <= 0:
        return {}
    fyb       = tc["fyb"]
    At        = tm["At"]
    De        = tm["De"]
    sigma_adm = ch["fy"] / 1.25
    Nu        = 0.8 * fyb * At                         # resist. tracción/bolt (N)
    Nt_trac   = F / Nu if Nu > 0 else 9999             # fracción — tracción
    Nt_cort   = (4 * F) / (0.65 * fyb * At)           # fracción — cortadura
    Nt_aplast = F / (De * sigma_adm * t_min_mm)       # fracción — aplastamiento
    N_req     = max(1, math.ceil(max(Nt_trac, Nt_cort, Nt_aplast)))
    return {
        **aero,
        "Nu_N":      round(Nu, 2),
        "Nt_trac":   round(Nt_trac, 5),
        "Nt_cort":   round(Nt_cort, 5),
        "Nt_aplast": round(Nt_aplast, 5),
        "N_req":     N_req,
    }


def calcular_union_adhesiva_aero(Cx, V_kmh, ancho_cm, alto_cm, Pp_kg,
                                   adhesivo, b_mm, l_mm):
    """
    Unión adhesiva con carga aerodinámica.
    τ = F / (b · l)  ≤  R_adhesivo
    (factor 1 — directo; para cordón simple lineal)
    """
    aero = calcular_carga_aerodinamica(Cx, V_kmh, ancho_cm, alto_cm, Pp_kg)
    F    = aero["F_calc_N"]
    R    = ADHESIVOS.get(adhesivo, 0)
    if b_mm <= 0 or l_mm <= 0 or R <= 0:
        return {}
    tau  = F / (b_mm * l_mm)
    coef = tau / R
    return {**aero, "tau_MPa": round(tau, 4), "R_MPa": R,
            "coef": round(coef, 4), "verifica": coef <= 1.0}


def calcular_tacos_elevacion(MTMA_kg, material, cantidad, diametro_mm):
    """
    Tacos de elevación: σ = (MTMA·g / n) / Ar  ≤  R_comp_material
    Ar = π·d²/4
    """
    import math
    R = TACOS_MAT.get(material, 0)
    if cantidad <= 0 or diametro_mm <= 0 or R <= 0:
        return {}
    Ar      = math.pi * diametro_mm**2 / 4
    F_total = MTMA_kg * 9.81
    sigma   = (F_total / cantidad) / Ar
    coef    = sigma / R
    return {"Ar_mm2": round(Ar, 2), "sigma_MPa": round(sigma, 4),
            "R_MPa": R, "coef": round(coef, 4), "verifica": coef <= 1.0}


def calcular_proteccion_trasera(MTMA_kg, longitud_mm, W_cm3, material):
    """
    Protección trasera (barra antichoque):
    Mmax_carga = (MTMA·g/2) · (L/2)         [biapoyado, carga central]
    Mmax_perfil = Wpl_mm3 · σ_adm            [σ_adm = fy/1.25]
    """
    ch = CHAPA_MAT.get(material.lower(), {})
    if not ch or W_cm3 <= 0 or longitud_mm <= 0:
        return {}
    sigma_adm = ch["fy"] / 1.25
    F_half    = MTMA_kg * 9.81 / 2           # N (carga sobre cada apoyo)
    L_half    = longitud_mm / 2              # mm (semiluz)
    M_Ed      = F_half * L_half              # N·mm
    W_mm3     = W_cm3 * 1000                 # cm³ → mm³
    M_Rd      = W_mm3 * sigma_adm           # N·mm
    coef      = M_Ed / M_Rd if M_Rd > 0 else 9999
    return {
        "F_half_N":    round(F_half, 1),
        "M_Ed_Nmm":    round(M_Ed, 0),
        "sigma_adm":   round(sigma_adm, 1),
        "M_Rd_Nmm":    round(M_Rd, 0),
        "coef":        round(coef, 4),
        "verifica":    coef <= 1.0,
    }


def calcular_balance_masas_turismo(mT1, mT2, mP1_n, mP2_n, MMA, MMA_e1, MMA_e2,
                                    dT2_mm, dP1_mm, dP2_mm, dVt_mm, long_caja_mm,
                                    con_bola=False, mQb_N=0, dQb_mm=0):
    """
    Balance de masas para turismo (M1/M2).
    Ecuaciones de equilibrio estático:
      R2 = (mT2·dT2 + mP1·dP1 + mP2·dP2 + mQu·dQu) / dT2
      R1 = mT + mP1 + mP2 + mQu - R2
    dQu = dT2 + long_caja/2  (centro carga útil)
    mQu = MMA - TARA - (mP1 + mP2)
    """
    g    = 9.81
    mP1  = mP1_n * 75      # 75 kg/persona
    mP2  = mP2_n * 75
    TARA = mT1 + mT2
    mQu  = MMA - TARA - mP1 - mP2
    if mQu < 0:
        mQu = 0
    dQu  = dT2_mm + (long_caja_mm / 2 if long_caja_mm > 0 else dVt_mm / 2)

    if dT2_mm <= 0:
        return {}

    R2_sb  = (mT2*dT2_mm + mP1*dP1_mm + mP2*dP2_mm + mQu*dQu) / dT2_mm
    R1_sb  = TARA + mP1 + mP2 + mQu - R2_sb
    ok1_sb = R1_sb <= MMA_e1 if MMA_e1 > 0 else True
    ok2_sb = R2_sb <= MMA_e2 if MMA_e2 > 0 else True

    res = {
        "TARA_kg":    round(TARA, 1),
        "mQu_kg":     round(mQu, 1),
        "dQu_mm":     round(dQu, 1),
        "R1_sb":      round(R1_sb, 2),
        "R2_sb":      round(R2_sb, 2),
        "ok1_sb":     ok1_sb,
        "ok2_sb":     ok2_sb,
    }
    if con_bola and mQb_N > 0 and dQb_mm > 0:
        mQb_kg  = mQb_N / g
        mQu_cb  = mQu - mQb_kg
        R2_cb   = (mT2*dT2_mm + mP1*dP1_mm + mP2*dP2_mm + mQu_cb*dQu + mQb_kg*dQb_mm) / dT2_mm
        R1_cb   = TARA + mP1 + mP2 + mQu_cb + mQb_kg - R2_cb
        res["R1_cb"]   = round(R1_cb, 2)
        res["R2_cb"]   = round(R2_cb, 2)
        res["ok1_cb"]  = R1_cb <= MMA_e1 if MMA_e1 > 0 else True
        res["ok2_cb"]  = R2_cb <= MMA_e2 if MMA_e2 > 0 else True
    return res


def calcular_frenos_disco(MMA_kg, mu, aspecto, seccion_mm, llanta_pulg,
                           D_ext_del, D_int_del, L_past_del,
                           D_ext_tra, D_int_tra, L_past_tra,
                           d_piston_del, d_piston_tra, P_hidraul_MPa):
    """
    Eficacia de frenado con discos.
    α  = arcsin(L_pastilla / D_ext_disco)
    T  = (2/3) · μ · α · p · 10⁶ · (Re³ - Ri³)
    F  = T / R_llanta
    Ef = F / (MMA·g) × 100 %
    """
    import math
    g         = 9.81
    R_llanta  = (llanta_pulg * 25.4 + 2 * aspecto * seccion_mm / 100) / 2 / 1000  # m

    def torque(D_ext, D_int, L_past, p_MPa):
        if D_ext <= 0 or D_int <= 0:
            return 0
        alpha = math.asin(min(L_past / D_ext, 1.0))
        Re    = (D_ext / 2) / 1000   # m
        Ri    = (D_int / 2) / 1000   # m
        return (2/3) * mu * alpha * p_MPa * 1e6 * (Re**3 - Ri**3)

    T_del   = torque(D_ext_del, D_int_del, L_past_del, P_hidraul_MPa)
    T_tra   = torque(D_ext_tra, D_int_tra, L_past_tra, P_hidraul_MPa)
    T_total = T_del + T_tra
    F_fren  = T_total / R_llanta if R_llanta > 0 else 0
    eficacia = (F_fren / (MMA_kg * g)) * 100

    return {
        "R_llanta_m":  round(R_llanta, 5),
        "T_del_Nm":    round(T_del, 2),
        "T_tra_Nm":    round(T_tra, 2),
        "T_total_Nm":  round(T_total, 2),
        "F_fren_N":    round(F_fren, 2),
        "eficacia_pct":round(eficacia, 2),
        "ratio_50":    round(eficacia / 50, 3),
        "verifica":    eficacia >= 50.0,
    }


# ── Aceros estructurales (EN 10025) ──────────────────────────────────────────
ACERO_MATERIALES = ["S235", "S275", "S355", "S420", "S460"]
ACERO_PROPIEDADES = {
    "S235": {"fy": 235, "fu": 360, "E": 210000},
    "S275": {"fy": 275, "fu": 430, "E": 210000},
    "S355": {"fy": 355, "fu": 510, "E": 210000},
    "S420": {"fy": 420, "fu": 520, "E": 210000},
    "S460": {"fy": 460, "fu": 550, "E": 210000},
}

# Coeficientes de longitud eficaz de pandeo (Euler)
PANDEO_CONDICIONES = [
    "Biempotrado (μ=0.5)",
    "Empotrado-Articulado (μ=0.7)",
    "Biarticualado (μ=1.0)",
    "Empotrado-Libre (μ=2.0)",
]
PANDEO_MU = {
    "Biempotrado (μ=0.5)":          0.5,
    "Empotrado-Articulado (μ=0.7)": 0.7,
    "Biarticualado (μ=1.0)":        1.0,
    "Empotrado-Libre (μ=2.0)":      2.0,
}

# Factor de correlación βw para cordones soldados (EN 1993-1-8 Tab. 4.1)
SOLDADURA_BETA_W = {
    "S235": 0.80, "S275": 0.85, "S355": 0.90, "S420": 1.00, "S460": 1.00,
}
GAMMA_M2_SOLD = 1.25

TORSION_SECCIONES = [
    "Circular maciza",
    "Circular hueca (tubo)",
    "Rectangular maciza",
    "Perfil definido por usuario",
]


def calcular_flexion_viga(M_Nm: float, W_cm3: float, fy_MPa: float) -> dict:
    """
    Flexión simple — Navier: σmáx = M / Wpl  ≤  fy / γM0  (γM0=1.0)
    M_Nm   : momento flector de cálculo (N·m)
    W_cm3  : módulo resistente plástico Wpl (cm³)
    fy_MPa : límite elástico (MPa)
    """
    if W_cm3 <= 0 or fy_MPa <= 0:
        return {}
    W_mm3   = W_cm3 * 1000        # cm³ → mm³
    M_Nmm   = M_Nm * 1000         # N·m → N·mm
    sigma   = M_Nmm / W_mm3       # MPa
    fd      = fy_MPa              # γM0 = 1.0
    coef    = sigma / fd
    return {
        "sigma_MPa": round(sigma, 2),
        "fd_MPa":    round(fd, 2),
        "coef":      round(coef, 4),
        "verifica":  coef <= 1.0,
    }


def calcular_torsion(MT_Nm: float, Ip_cm4: float, r_mm: float,
                     fy_MPa: float) -> dict:
    """
    Torsión — Saint-Venant: τmáx = MT · r / Ip
    τadm = fy / √3  (Von Mises, γM0=1.0)
    """
    import math
    if Ip_cm4 <= 0 or r_mm <= 0:
        return {}
    Ip_mm4  = Ip_cm4 * 1e4
    MT_Nmm  = MT_Nm * 1000
    tau     = MT_Nmm * r_mm / Ip_mm4
    tau_adm = fy_MPa / math.sqrt(3) if fy_MPa > 0 else 0
    coef    = tau / tau_adm if tau_adm > 0 else 9999
    return {
        "tau_MPa":     round(tau, 2),
        "tau_adm_MPa": round(tau_adm, 2),
        "coef":        round(coef, 4),
        "verifica":    coef <= 1.0,
    }


def calcular_pandeo_euler(N_N: float, L_mm: float, mu: float,
                           I_cm4: float, A_cm2: float,
                           E_MPa: float, fy_MPa: float) -> dict:
    """
    Pandeo — Euler: Pcr = π²·E·I / (μL)²
    Esbeltez adimensional: λ̄ = (μL/i) / (π·√(E/fy))
    """
    import math
    if A_cm2 <= 0 or I_cm4 <= 0 or E_MPa <= 0 or L_mm <= 0:
        return {}
    I_mm4 = I_cm4 * 1e4
    A_mm2 = A_cm2 * 100
    Lc    = mu * L_mm
    Pcr   = (math.pi ** 2 * E_MPa * I_mm4) / (Lc ** 2)
    i_mm  = math.sqrt(I_mm4 / A_mm2)
    lam   = Lc / i_mm
    lam1  = math.pi * math.sqrt(E_MPa / fy_MPa) if fy_MPa > 0 else 1
    lam_r = lam / lam1
    coef  = N_N / Pcr if Pcr > 0 else 9999
    return {
        "Pcr_N":    round(Pcr, 0),
        "i_mm":     round(i_mm, 2),
        "lambda":   round(lam, 1),
        "lambda_r": round(lam_r, 3),
        "coef":     round(coef, 4),
        "verifica": coef <= 1.0,
    }


def calcular_distribucion_ejes(L_mm: float, d_mm: float, P_kg: float,
                                 Q1_kg: float, Q2_kg: float,
                                 MMA1_kg: float, MMA2_kg: float) -> dict:
    """
    Distribución de carga entre eje delantero (1) y trasero (2).
    Equilibrio: ΔQ₂ = P·d/L  ;  ΔQ₁ = P − ΔQ₂
    """
    if L_mm <= 0:
        return {}
    dQ2 = P_kg * d_mm / L_mm
    dQ1 = P_kg - dQ2
    Q1n = Q1_kg + dQ1
    Q2n = Q2_kg + dQ2
    ok1 = Q1n <= MMA1_kg if MMA1_kg > 0 else True
    ok2 = Q2n <= MMA2_kg if MMA2_kg > 0 else True
    return {
        "dQ1_kg": round(dQ1, 1), "dQ2_kg": round(dQ2, 1),
        "Q1n_kg": round(Q1n, 1), "Q2n_kg": round(Q2n, 1),
        "ok1": ok1, "ok2": ok2,
    }


def calcular_vuelco_lateral(s_mm: float, h_cg_mm: float) -> dict:
    """
    Estabilidad al vuelco lateral.
    Factor η = s/(2·hcg)  ;  a_lim = η·g  ;  v_lim = √(a_lim·R) (R=50 m)
    """
    import math
    if h_cg_mm <= 0 or s_mm <= 0:
        return {}
    eta    = s_mm / (2 * h_cg_mm)
    g      = 9.81
    a_lim  = eta * g
    R      = 50_000   # mm
    v_ms   = math.sqrt(a_lim * R / 1000)    # m/s (R en mm → /1000 → m)
    v_kmh  = v_ms * 3.6
    return {
        "eta":    round(eta, 3),
        "a_lim":  round(a_lim, 3),
        "v_kmh":  round(v_kmh, 1),
        "estable": eta >= 0.3,
    }


def calcular_union_soldada(F_N: float, a_mm: float, L_mm: float,
                            fu_MPa: float, beta_w: float) -> dict:
    """
    Cordón de ángulo — método simplificado EN 1993-1-8 §4.5.3.3
    fw,Rd = fu / (√3 · βw · γM2)
    τ_act = F / (a · Lw)
    """
    import math
    if a_mm <= 0 or L_mm <= 0 or beta_w <= 0 or fu_MPa <= 0:
        return {}
    fw_Rd = fu_MPa / (math.sqrt(3) * beta_w * GAMMA_M2_SOLD)
    tau   = F_N / (a_mm * L_mm)
    coef  = tau / fw_Rd if fw_Rd > 0 else 9999
    return {
        "fw_Rd_MPa": round(fw_Rd, 2),
        "tau_MPa":   round(tau, 2),
        "coef":      round(coef, 4),
        "verifica":  coef <= 1.0,
    }


def calcular_grua_autocarga(P_kg: float, L_mm: float, brazo_mm: float) -> dict:
    """
    Grúa autocarga: momento de vuelco y fuerza en cilindro.
    Mv = P·g·L  ;  F_cil = Mv / brazo_cil
    """
    g     = 9.81
    Mv    = P_kg * g * L_mm          # N·mm
    F_cil = Mv / brazo_mm if brazo_mm > 0 else 0
    return {
        "Mv_Nm":   round(Mv / 1000, 1),
        "F_cil_N": round(F_cil, 0),
    }


def calcular_suspension_neumatica(carga_total_kg, num_balonas, diam_balona_mm,
                                  presion_max_bar):
    """
    Suspensión neumática — Cálculo de presión de trabajo y margen de seguridad.
    Fórmulas:
      Carga_por_balona = Carga_total / N_balonas
      Área_efectiva = (π·d²) / 4 / 100   (cm²)
      Fuerza = Carga_total · 9.81         (N)
      P_trabajo = Fuerza / (Área · 100000)(bar)
      Margen = (P_max / P_trabajo - 1)·100 (%)
    """
    import math
    if num_balonas <= 0 or diam_balona_mm <= 0 or presion_max_bar <= 0:
        return {}
    carga_balona = carga_total_kg / num_balonas
    area_cm2     = (math.pi * diam_balona_mm ** 2) / 4 / 100
    fuerza_N     = carga_total_kg * 9.81
    p_trabajo    = fuerza_N / (area_cm2 * 100000) if area_cm2 > 0 else 0
    margen       = ((presion_max_bar / p_trabajo) - 1) * 100 if p_trabajo > 0 else 0
    return {
        "carga_balona_kg":  round(carga_balona, 2),
        "area_cm2":         round(area_cm2, 4),
        "fuerza_N":         round(fuerza_N, 2),
        "p_trabajo_bar":    round(p_trabajo, 4),
        "margen_pct":       round(margen, 1),
        "verifica":         margen > 0,
    }


# ── Tipos de cálculo justificativo disponibles ─────────────────────────────────
# Formato: "Nombre del tipo": [("CLAVE", "Etiqueta", "Valor por defecto"), ...]
CALC_TIPOS = {
    "— Sin cálculo —": [],

    "Suspensión neumática — Balonas / Airbag": [
        ("MARCA_BALONAS",       "Marca balonas",                    "FIRESTONE"),
        ("MODELO_BALONAS",      "Modelo balonas",                   ""),
        ("PRESION_BALONAS_BAR", "Presión máx. balonas (bar)",       "7"),
        ("NUM_BALONAS",         "Número de balonas",                "2"),
        ("DIAM_BALONA_MM",      "Diámetro efectivo balona (mm)",    ""),
        ("CARGA_TOTAL_KG",      "Carga total sobre eje (kg)",       ""),
        ("MARCA_COMPRESOR",     "Marca compresor",                  "DRIVERITE"),
        ("MODELO_COMPRESOR",    "Modelo compresor",                 "120 PSI"),
        ("MARCA_SOPORTE",       "Marca soporte / kit",              "DRIVERITE"),
        ("PESO_KIT_KG",         "Peso total del kit (kg)",          "12"),
        ("DIAMETRO_TORNILLO",   "Diámetro tornillo",                "M14"),
        ("CALIDAD_TORNILLO",    "Calidad tornillo",                 "8.8"),
        ("NUM_TORNILLOS",       "Número de tornillos",              "4"),
        ("FUERZA_CALCULO_N",    "Fuerza de cálculo (N)",            "16677.00"),
        ("TENSION_ADMISIBLE",   "Tensión admisible (MPa)",          ""),
        # — Resultados calculados —
        ("_SEP_RES_SN",  "RESULTADOS — VERIFICACIÓN NEUMÁTICA", "", "sep"),
        ("SN_CARGA_BALONA", "Carga por balona (kg)",              "", "calc"),
        ("SN_AREA_EFECT",  "Área efectiva (cm²)",                 "", "calc"),
        ("SN_FUERZA_N",    "Fuerza calculada (N)",                "", "calc"),
        ("SN_P_TRABAJO",   "Presión de trabajo (bar)",            "", "calc"),
        ("SN_MARGEN",      "Margen de seguridad (%)",             "", "calc"),
        ("SN_RESULTADO",   "Resultado verificación",              "", "calc"),
    ],

    "Suspensión mecánica — Sustitución muelles / amortiguadores": [
        ("MARCA_MUELLE_NUEVO",  "Marca muelles nuevos",             ""),
        ("MODELO_MUELLE_NUEVO", "Modelo muelles nuevos",            ""),
        ("RIGIDEZ_MUELLE",      "Rigidez muelle (N/mm)",            ""),
        ("MARCA_AMORT_NUEVO",   "Marca amortiguadores nuevos",      ""),
        ("MODELO_AMORT_NUEVO",  "Modelo amortiguadores nuevos",     ""),
        ("ALTURA_ANTES_MM",     "Altura vehículo antes (mm)",       ""),
        ("ALTURA_DESPUES_MM",   "Altura vehículo después (mm)",     ""),
        ("VARIACION_ALTURA_MM", "Variación de altura (mm)",         ""),
        # — Resultados calculados —
        ("_SEP_RES_SM",    "RESULTADOS", "",                        "sep"),
        ("SM_VAR_CALC",    "Variación calculada (mm)",         "",  "calc"),
        ("SM_PCT_VAR",     "Variación porcentual (%)",         "",  "calc"),
    ],

    "Cambio de motor / Sustitución unidad motriz": [
        ("MOTOR_ORIG_TIPO",         "Motor original — Tipo",            ""),
        ("MOTOR_ORIG_CILINDRADA_CC","Motor original — Cilindrada (cc)", ""),
        ("MOTOR_ORIG_POT_KW",       "Motor original — Potencia (kW)",   ""),
        ("MOTOR_ORIG_PAR_NM",       "Motor original — Par máx. (Nm)",   ""),
        ("MOTOR_NUEVO_MARCA",       "Motor nuevo — Marca",              ""),
        ("MOTOR_NUEVO_MODELO",      "Motor nuevo — Modelo",             ""),
        ("MOTOR_NUEVO_TIPO",        "Motor nuevo — Tipo",               ""),
        ("MOTOR_NUEVO_CILINDRADA_CC","Motor nuevo — Cilindrada (cc)",   ""),
        ("MOTOR_NUEVO_POT_KW",      "Motor nuevo — Potencia (kW)",      ""),
        ("MOTOR_NUEVO_PAR_NM",      "Motor nuevo — Par máx. (Nm)",      ""),
        ("MOTOR_NUEVO_HOMOLOG",     "Motor nuevo — N° homologación",    ""),
        ("MOTOR_TARA_KG",           "Tara del vehículo (kg)",           ""),
        # — Resultados calculados —
        ("_SEP_RES_MOT",  "RESULTADOS", "",                             "sep"),
        ("RATIO_POT_PESO",     "Relación potencia/peso (kW/t)",   "",  "calc"),
        ("INCREMENTO_POT_PCT", "Incremento de potencia (%)",      "",  "calc"),
        ("INCREMENTO_PAR_PCT", "Incremento de par (%)",           "",  "calc"),
        ("MOTOR_RESULTADO",    "Resultado verificación",          "",  "calc"),
    ],

    "Conversión eléctrica o híbrida": [
        ("MOTOR_ELEC_MARCA",    "Motor eléctrico — Marca",          ""),
        ("MOTOR_ELEC_MODELO",   "Motor eléctrico — Modelo",         ""),
        ("MOTOR_ELEC_POT_KW",   "Motor eléctrico — Potencia (kW)",  ""),
        ("MOTOR_ELEC_PAR_NM",   "Motor eléctrico — Par (Nm)",       ""),
        ("BATERIA_MARCA",       "Batería — Marca",                  ""),
        ("BATERIA_MODELO",      "Batería — Modelo",                 ""),
        ("BATERIA_CAPACIDAD_KWH","Batería — Capacidad (kWh)",       ""),
        ("BATERIA_TENSION_V",   "Batería — Tensión nominal (V)",    ""),
        ("BATERIA_UBICACION",   "Batería — Ubicación en vehículo",  ""),
        ("AUTONOMIA_KM",        "Autonomía estimada (km)",          ""),
        ("HOMOLOG_CONVERSION",  "N° homologación conversión",       ""),
        ("CONV_TARA_KG",        "Tara del vehículo (kg)",           ""),
        # — Resultados calculados —
        ("_SEP_RES_CONV", "RESULTADOS", "",                          "sep"),
        ("CONV_RATIO_POT", "Relación potencia/peso (kW/t)",    "",  "calc"),
        ("CONV_ENERGIA_PESO", "Energía/peso (Wh/kg)",          "",  "calc"),
    ],

    "Enganche / Dispositivo de acoplamiento": [
        ("ENGANCHE_MARCA",          "Marca enganche",                   ""),
        ("ENGANCHE_MODELO",         "Modelo enganche",                  ""),
        ("ENGANCHE_TIPO",           "Tipo de enganche",                 ""),
        ("ENGANCHE_HOMOLOG",        "N° homologación enganche",         ""),
        ("ENG_MMA_VEHICULO",        "MMA del vehículo tractor (kg)",    ""),
        ("MASA_REMOLCABLE_KG",      "Masa máx. remolcable (kg)",        ""),
        ("MASA_REMOLQUE_FRENO_KG",  "Masa máx. remolque con freno (kg)",""),
        ("MASA_REMOLQUE_SFRENO_KG", "Masa máx. remolque sin freno (kg)",""),
        ("CARGA_BOLA_KG",           "Carga máx. sobre bola (kg)",       ""),
        ("MMA_CONJUNTO_KG",         "MMA del conjunto (kg)",            ""),
        # — Resultados calculados —
        ("_SEP_RES_ENG",  "RESULTADOS", "",                             "sep"),
        ("ENG_MMA_CONJ_CALC", "MMA conjunto calculada (kg)",      "",  "calc"),
        ("ENG_VERIF_CONJ",    "Verificación MMA conjunto",        "",  "calc"),
    ],

    "Modificación de masas / MMA": [
        ("MMA_ANTERIOR_KG",     "MMA anterior (kg)",                ""),
        ("MMA_NUEVA_KG",        "MMA nueva (kg)",                   ""),
        ("MMTC_NUEVA_KG",       "MMTC nueva (kg)",                  ""),
        ("TARA_KG",             "Tara del vehículo (kg)",           ""),
        ("CARGA_EJE1_KG",       "Carga eje 1 (kg)",                 ""),
        ("CARGA_EJE2_KG",       "Carga eje 2 (kg)",                 ""),
        ("CARGA_EJE3_KG",       "Carga eje 3 (kg)",                 ""),
        ("MMA_MAX_LEGAL_KG",    "MMA máxima legal (kg)",            ""),
        # — Resultados calculados —
        ("_SEP_RES_MM",  "RESULTADOS", "",                           "sep"),
        ("MM_SUMA_EJES",      "Suma de cargas por eje (kg)",    "",  "calc"),
        ("MM_CARGA_UTIL",     "Carga útil = MMA − Tara (kg)",  "",  "calc"),
        ("MM_VERIF_MMA",      "Verificación MMA",              "",  "calc"),
        ("VERIFICACION_EJES", "Verificación carga por eje",    "",  "calc"),
    ],

    "Modificación de carrocería / Estructura": [
        ("MATERIAL_CARROCERIA",     "Material carrocería",              ""),
        ("LONG_ANTES_MM",           "Longitud total antes (mm)",        ""),
        ("LONG_DESPUES_MM",         "Longitud total después (mm)",      ""),
        ("ANCHO_ANTES_MM",          "Anchura total antes (mm)",         ""),
        ("ANCHO_DESPUES_MM",        "Anchura total después (mm)",       ""),
        ("ALTO_ANTES_MM",           "Altura total antes (mm)",          ""),
        ("ALTO_DESPUES_MM",         "Altura total después (mm)",        ""),
        ("VOLADIZO_DEL_ANTES_MM",   "Voladizo delantero antes (mm)",    ""),
        ("VOLADIZO_DEL_DESP_MM",    "Voladizo delantero después (mm)",  ""),
        ("VOLADIZO_TRA_ANTES_MM",   "Voladizo trasero antes (mm)",      ""),
        ("VOLADIZO_TRA_DESP_MM",    "Voladizo trasero después (mm)",    ""),
        # — Variaciones dimensionales calculadas —
        ("_SEP_RES_CAR",  "VARIACIONES DIMENSIONALES", "",              "sep"),
        ("CAR_VAR_LONG",     "Variación longitud (mm)",           "",  "calc"),
        ("CAR_VAR_ANCHO",    "Variación anchura (mm)",            "",  "calc"),
        ("CAR_VAR_ALTO",     "Variación altura (mm)",             "",  "calc"),
        ("CAR_VAR_VOL_DEL",  "Variación voladizo delantero (mm)", "",  "calc"),
        ("CAR_VAR_VOL_TRA",  "Variación voladizo trasero (mm)",   "",  "calc"),
    ],

    "Modificación alumbrado / Iluminación": [
        ("DISPOSITIVO_MARCA",   "Marca dispositivo",                ""),
        ("DISPOSITIVO_MODELO",  "Modelo dispositivo",               ""),
        ("DISPOSITIVO_TIPO",    "Tipo de dispositivo",              ""),
        ("DISPOSITIVO_HOMOLOG", "N° homologación dispositivo",      ""),
        ("UBICACION_DISPOSITIVO","Ubicación en el vehículo",        ""),
        ("NORMA_APLICABLE",     "Norma/Directiva aplicable",        ""),
    ],

    "Modificación del sistema de frenos": [
        ("FRENO_SISTEMA_TIPO",  "Tipo de sistema de frenos",        ""),
        ("FRENO_MARCA_COMP",    "Marca componente sustituido",      ""),
        ("FRENO_MODELO_COMP",   "Modelo componente sustituido",     ""),
        ("FRENO_HOMOLOG",       "N° homologación sistema",          ""),
        ("DIST_FRENADA_ANTES",  "Distancia frenada antes (m)",      ""),
        ("DIST_FRENADA_DESP",   "Distancia frenada después (m)",    ""),
        ("NORMA_FRENOS",        "Norma/Directiva aplicable",        ""),
        # — Resultados calculados —
        ("_SEP_RES_FRM",  "RESULTADOS", "",                          "sep"),
        ("FRMOD_MEJORA_PCT", "Mejora distancia frenada (%)",    "",  "calc"),
        ("FRMOD_RESULTADO",  "Resultado verificación",          "",  "calc"),
    ],

    "Acondicionamiento / Adaptación PMR": [
        ("RAMPA_MARCA",         "Marca rampa/elevador",             ""),
        ("RAMPA_MODELO",        "Modelo rampa/elevador",            ""),
        ("RAMPA_HOMOLOG",       "N° homologación rampa",            ""),
        ("PLAZAS_PMR",          "Número de plazas PMR",             "1"),
        ("ANCHO_ACCESO_MM",     "Anchura de acceso (mm)",           ""),
        ("CARGA_MAX_PMR_KG",    "Carga máxima PMR (kg)",            ""),
        ("CINTURON_TIPO",       "Tipo cinturón PMR",                ""),
    ],

    "Otro / Cálculo libre": [
        ("CALC_LIBRE_1",        "Campo 1",                          ""),
        ("CALC_LIBRE_2",        "Campo 2",                          ""),
        ("CALC_LIBRE_3",        "Campo 3",                          ""),
        ("CALC_LIBRE_4",        "Campo 4",                          ""),
        ("CALC_LIBRE_5",        "Campo 5",                          ""),
        ("CALC_LIBRE_6",        "Campo 6",                          ""),
    ],

    # ── Uniones atornilladas (tornillería métrica) ─────────────────────────
    # Formato extendido: (clave, etiqueta, default_o_opciones, tipo_widget)
    # tipo_widget: "entry" | "combo" | "calc" (sólo lectura, calculado) | "sep"
    "Uniones atornilladas — Interior": [
        # — Geometría y condiciones —
        ("_SEP_GEO",    "GEOMETRÍA DE LA UNIÓN", "",                        "sep"),
        ("TORN_TIPO_CORTE",  "Tipo de unión / esfuerzo",
         TORNILLO_TIPO_CORTE,                                               "combo"),
        ("TORN_NUM",    "Número de tornillos",              "4",            "entry"),
        ("TORN_FILAS",  "Número de filas",                  "1",            "entry"),
        # — Selección tornillo —
        ("_SEP_TORN",   "TORNILLO", "",                                     "sep"),
        ("TORN_DIAM",   "Diámetro tornillo",
         TORNILLO_DIAMETROS,                                                "combo"),
        ("TORN_CALIDAD","Calidad / clase resistente",
         TORNILLO_CALIDADES_LIST,                                           "combo"),
        # — Propiedades mecánicas (auto-rellenadas al seleccionar diámetro/calidad) —
        ("TORN_A_BRUTA","Área bruta A (mm²)",               "",            "calc"),
        ("TORN_A_S",    "Área resistente As (mm²)",          "",            "calc"),
        ("TORN_FYB",    "Límite elástico fyb (MPa)",         "",            "calc"),
        ("TORN_FUB",    "Resistencia última fub (MPa)",      "",            "calc"),
        # — Resistencias de cálculo (auto) —
        ("_SEP_RES",    "RESISTENCIAS DE CÁLCULO (EN 1993-1-8 / γM2=1.25)", "", "sep"),
        ("TORN_FV_RD_1","Fv,Rd por plano de corte (N)",     "",            "calc"),
        ("TORN_FV_RD",  "Fv,Rd total (N)",                  "",            "calc"),
        ("TORN_FT_RD",  "Ft,Rd por tornillo (N)",           "",            "calc"),
        # — Cargas aplicadas —
        ("_SEP_CARGA",  "CARGAS APLICADAS", "",                             "sep"),
        ("TORN_FV_ED",  "Fv,Ed — Cortante de cálculo (N)",  "",            "entry"),
        ("TORN_FT_ED",  "Ft,Ed — Tracción de cálculo (N)",  "0",           "entry"),
        # — Comprobaciones —
        ("_SEP_CHECK",  "COMPROBACIONES", "",                               "sep"),
        ("TORN_COEF_CORT", "Coef. utilización cortante (Fv,Ed/Fv,Rd)", "", "calc"),
        ("TORN_COEF_TRAC", "Coef. utilización tracción (Ft,Ed/Ft,Rd)", "", "calc"),
        ("TORN_INTER",  "Interacción cortante+tracción (≤1.0)",         "", "calc"),
        ("TORN_RESULTADO", "Resultado verificación",                    "", "calc"),
        # — Notas —
        ("TORN_NORMA",  "Norma de referencia",  "EN 1993-1-8 / CTE DB-SE-A","entry"),
        ("TORN_NOTAS",  "Notas adicionales",                "",            "entry"),
    ],

    "Uniones atornilladas — Exterior (ambiente agresivo)": [
        # — Condiciones ambientales —
        ("_SEP_AMB",    "CONDICIONES AMBIENTALES", "",                      "sep"),
        ("TORN_EXT_CLASE_CORR", "Clase de corrosividad",
         TORNILLO_CLASE_CORR,                                               "combo"),
        ("TORN_EXT_ACABADO",    "Acabado / protección tornillo",
         TORNILLO_ACABADO_EXT,                                              "combo"),
        # — Geometría y condiciones —
        ("_SEP_GEO",    "GEOMETRÍA DE LA UNIÓN", "",                        "sep"),
        ("TORN_TIPO_CORTE",  "Tipo de unión / esfuerzo",
         TORNILLO_TIPO_CORTE,                                               "combo"),
        ("TORN_NUM",    "Número de tornillos",              "4",            "entry"),
        ("TORN_FILAS",  "Número de filas",                  "1",            "entry"),
        # — Selección tornillo —
        ("_SEP_TORN",   "TORNILLO", "",                                     "sep"),
        ("TORN_DIAM",   "Diámetro tornillo",
         TORNILLO_DIAMETROS,                                                "combo"),
        ("TORN_CALIDAD","Calidad / clase resistente",
         TORNILLO_CALIDADES_LIST,                                           "combo"),
        # — Propiedades mecánicas —
        ("TORN_A_BRUTA","Área bruta A (mm²)",               "",            "calc"),
        ("TORN_A_S",    "Área resistente As (mm²)",          "",            "calc"),
        ("TORN_FYB",    "Límite elástico fyb (MPa)",         "",            "calc"),
        ("TORN_FUB",    "Resistencia última fub (MPa)",      "",            "calc"),
        # — Resistencias de cálculo —
        ("_SEP_RES",    "RESISTENCIAS DE CÁLCULO (EN 1993-1-8 / γM2=1.25)", "", "sep"),
        ("TORN_FV_RD_1","Fv,Rd por plano de corte (N)",     "",            "calc"),
        ("TORN_FV_RD",  "Fv,Rd total (N)",                  "",            "calc"),
        ("TORN_FT_RD",  "Ft,Rd por tornillo (N)",           "",            "calc"),
        # — Cargas aplicadas —
        ("_SEP_CARGA",  "CARGAS APLICADAS", "",                             "sep"),
        ("TORN_FV_ED",  "Fv,Ed — Cortante de cálculo (N)",  "",            "entry"),
        ("TORN_FT_ED",  "Ft,Ed — Tracción de cálculo (N)",  "0",           "entry"),
        # — Comprobaciones —
        ("_SEP_CHECK",  "COMPROBACIONES", "",                               "sep"),
        ("TORN_COEF_CORT", "Coef. utilización cortante (Fv,Ed/Fv,Rd)", "", "calc"),
        ("TORN_COEF_TRAC", "Coef. utilización tracción (Ft,Ed/Ft,Rd)", "", "calc"),
        ("TORN_INTER",  "Interacción cortante+tracción (≤1.0)",         "", "calc"),
        ("TORN_RESULTADO", "Resultado verificación",                    "", "calc"),
        # — Notas —
        ("TORN_NORMA",  "Norma de referencia",  "EN 1993-1-8 / CTE DB-SE-A","entry"),
        ("TORN_NOTAS",  "Notas adicionales",                "",            "entry"),
    ],

    # ── Flexión simple de viga / perfil ──────────────────────────────────────
    "Flexión simple de viga — Navier": [
        ("_SEP_SEC",      "SECCIÓN TRANSVERSAL", "",                         "sep"),
        ("FLEX_MATERIAL", "Material estructural",
         ACERO_MATERIALES,                                                   "combo"),
        ("FLEX_FY_MPA",   "Límite elástico fy (MPa)",       "235",          "calc"),
        ("FLEX_PERFIL",   "Referencia del perfil",           "IPE200",      "entry"),
        ("FLEX_W_CM3",    "Módulo resistente Wpl (cm³)",     "",            "entry"),
        ("_SEP_CARG",     "CARGAS", "",                                      "sep"),
        ("FLEX_M_NM",     "Momento flector de cálculo M (N·m)","",          "entry"),
        ("_SEP_RES",      "RESULTADOS  (EN 1993-1-1 / γM0=1.0)", "",        "sep"),
        ("FLEX_SIGMA",    "σmáx = M / Wpl (MPa)",           "",             "calc"),
        ("FLEX_FD",       "fd = fy / γM0 (MPa)",            "",             "calc"),
        ("FLEX_COEF",     "Coef. utilización (σ/fd)",        "",            "calc"),
        ("FLEX_RESULT",   "Resultado verificación",          "",             "calc"),
        ("FLEX_NORMA",    "Norma de referencia",  "EN 1993-1-1 / CTE DB-SE-A","entry"),
    ],

    # ── Torsión de perfil ────────────────────────────────────────────────────
    "Torsión de perfil — Saint-Venant": [
        ("_SEP_SEC",      "SECCIÓN TRANSVERSAL", "",                         "sep"),
        ("TORS_TIPO",     "Tipo de sección",
         TORSION_SECCIONES,                                                  "combo"),
        ("TORS_R_MM",     "Radio / dist. máx. al CG torsional (mm)","",     "entry"),
        ("TORS_IP_CM4",   "Momento de inercia polar Ip (cm⁴)",     "",      "entry"),
        ("TORS_FY_MPA",   "Límite elástico fy (MPa)",               "235",  "entry"),
        ("_SEP_CARG",     "CARGAS", "",                                      "sep"),
        ("TORS_MT_NM",    "Momento torsor de cálculo MT (N·m)",     "",     "entry"),
        ("_SEP_RES",      "RESULTADOS", "",                                  "sep"),
        ("TORS_TAU",      "τmáx = MT·r / Ip (MPa)",                 "",     "calc"),
        ("TORS_TAU_ADM",  "τadm = fy/√3 (MPa)",                     "",     "calc"),
        ("TORS_COEF",     "Coef. utilización (τ/τadm)",              "",    "calc"),
        ("TORS_RESULT",   "Resultado verificación",                  "",     "calc"),
        ("TORS_NORMA",    "Norma de referencia",  "EN 1993-1-1 / CTE DB-SE-A","entry"),
    ],

    # ── Pandeo de barra — Euler ──────────────────────────────────────────────
    "Pandeo de barra — Euler": [
        ("_SEP_SEC",      "SECCIÓN Y MATERIAL", "",                          "sep"),
        ("PAND_MATERIAL", "Material estructural",
         ACERO_MATERIALES,                                                   "combo"),
        ("PAND_FY_MPA",   "Límite elástico fy (MPa)",       "235",          "calc"),
        ("PAND_E_MPA",    "Módulo elasticidad E (MPa)",      "210000",      "entry"),
        ("PAND_PERFIL",   "Referencia del perfil",           "",             "entry"),
        ("PAND_I_CM4",    "Momento de inercia mínimo Imin (cm⁴)","",       "entry"),
        ("PAND_A_CM2",    "Área de la sección A (cm²)",      "",            "entry"),
        ("_SEP_BARR",     "BARRA", "",                                       "sep"),
        ("PAND_L_MM",     "Longitud de la barra L (mm)",     "",            "entry"),
        ("PAND_COND",     "Condición de contorno",
         PANDEO_CONDICIONES,                                                 "combo"),
        ("PAND_MU",       "Coeficiente de pandeo μ",         "1.0",         "calc"),
        ("PAND_N_N",      "Carga de compresión N (N)",        "",           "entry"),
        ("_SEP_RES",      "RESULTADOS  (EN 1993-1-1)", "",                  "sep"),
        ("PAND_IRG",      "Radio de giro i (mm)",             "",           "calc"),
        ("PAND_ESBELT",   "Esbeltez mecánica λ = μL/i",       "",          "calc"),
        ("PAND_ESBR",     "Esbeltez adimensional λ̄",          "",          "calc"),
        ("PAND_PCR",      "Carga crítica Pcr (N)",             "",          "calc"),
        ("PAND_COEF",     "Coef. utilización N/Pcr",           "",          "calc"),
        ("PAND_RESULT",   "Resultado verificación",            "",           "calc"),
        ("PAND_NORMA",    "Norma de referencia",  "EN 1993-1-1 / CTE DB-SE-A","entry"),
    ],

    # ── Distribución de cargas por ejes ──────────────────────────────────────
    "Distribución de cargas por ejes": [
        ("_SEP_VEH",      "VEHÍCULO", "",                                    "sep"),
        ("EJES_BATALL",   "Batalla entre ejes L (mm)",        "",            "entry"),
        ("_SEP_CARG",     "CARGA AÑADIDA", "",                               "sep"),
        ("EJES_P_KG",     "Peso de la carga P (kg)",          "",            "entry"),
        ("EJES_D_MM",     "Distancia CG carga → eje delantero (mm)","",     "entry"),
        ("_SEP_ACT",      "CARGAS ACTUALES POR EJE", "",                     "sep"),
        ("EJES_Q1_KG",    "Carga actual eje delantero Q₁ (kg)","",          "entry"),
        ("EJES_Q2_KG",    "Carga actual eje trasero Q₂ (kg)", "",           "entry"),
        ("EJES_MMA1",     "MMA eje delantero (kg)",            "",           "entry"),
        ("EJES_MMA2",     "MMA eje trasero (kg)",              "",           "entry"),
        ("_SEP_RES",      "INCREMENTO Y NUEVAS CARGAS POR EJE", "",          "sep"),
        ("EJES_DQ1",      "Incremento eje delantero ΔQ₁ (kg)","",           "calc"),
        ("EJES_DQ2",      "Incremento eje trasero ΔQ₂ (kg)",  "",           "calc"),
        ("EJES_NQ1",      "Nueva carga eje delantero (kg)",    "",           "calc"),
        ("EJES_NQ2",      "Nueva carga eje trasero (kg)",      "",           "calc"),
        ("EJES_RES1",     "Verificación eje delantero",        "",           "calc"),
        ("EJES_RES2",     "Verificación eje trasero",          "",           "calc"),
    ],

    # ── Estabilidad al vuelco lateral ────────────────────────────────────────
    "Estabilidad al vuelco lateral": [
        ("_SEP_GEO",      "GEOMETRÍA DEL VEHÍCULO", "",                      "sep"),
        ("VUELT_ANCHO",   "Ancho de vía s (mm)",                "",          "entry"),
        ("VUELT_HCG",     "Altura del centro de gravedad hcg (mm)","",       "entry"),
        ("VUELT_MASA",    "Masa total del vehículo (kg)",        "",          "entry"),
        ("_SEP_RES",      "RESULTADOS", "",                                   "sep"),
        ("VUELT_ETA",     "Factor de estabilidad η = s/(2·hcg)", "",         "calc"),
        ("VUELT_ALIM",    "Aceleración lat. límite a_lat (m/s²)","",         "calc"),
        ("VUELT_VLIM",    "Velocidad límite en curva R=50m (km/h)","",       "calc"),
        ("VUELT_RESULT",  "Resultado verificación",               "",         "calc"),
        ("VUELT_NORMA",   "Norma de referencia","Baselga Cap.7 / RD 2028/86","entry"),
    ],

    # ── Uniones soldadas — cordón en ángulo ──────────────────────────────────
    "Uniones soldadas — cordón en ángulo": [
        ("_SEP_MAT",      "MATERIAL Y SOLDADURA", "",                        "sep"),
        ("SOLD_MATERIAL", "Material base",
         ACERO_MATERIALES,                                                   "combo"),
        ("SOLD_FU_MPA",   "Resistencia última fu (MPa)",       "360",       "calc"),
        ("SOLD_BETA",     "Factor de correlación βw",           "0.80",     "calc"),
        ("SOLD_GARG",     "Garganta de soldadura a (mm)",        "",        "entry"),
        ("SOLD_LONG",     "Longitud total cordón Lw (mm)",       "",        "entry"),
        ("_SEP_CARG",     "CARGAS", "",                                      "sep"),
        ("SOLD_F_N",      "Fuerza de cálculo F (N)",             "",        "entry"),
        ("_SEP_RES",      "RESULTADOS  (EN 1993-1-8 / γM2=1.25)", "",       "sep"),
        ("SOLD_TAU",      "τ = F / (a·Lw) (MPa)",               "",        "calc"),
        ("SOLD_FW_RD",    "fw,Rd = fu/(√3·βw·γM2) (MPa)",       "",        "calc"),
        ("SOLD_COEF",     "Coef. utilización (τ/fw,Rd)",         "",        "calc"),
        ("SOLD_RESULT",   "Resultado verificación",              "",         "calc"),
        ("SOLD_NORMA",    "Norma de referencia","EN 1993-1-8 / CTE DB-SE-A","entry"),
    ],

    # ── Balance de masas — Turismo (M1/M2) ───────────────────────────────────
    "Balance de masas — Turismo (M1/M2)": [
        ("_SEP_VEH",   "DATOS DEL VEHÍCULO", "",                             "sep"),
        ("BM_MMA",     "MMA del vehículo (kg)",              "",             "entry"),
        ("BM_MMA_E1",  "MMA eje delantero (kg)",             "",             "entry"),
        ("BM_MMA_E2",  "MMA eje trasero (kg)",               "",             "entry"),
        ("BM_MT1",     "Tara eje delantero (kg)",            "",             "entry"),
        ("BM_MT2",     "Tara eje trasero (kg)",              "",             "entry"),
        ("_SEP_OC",    "OCUPANTES", "",                                       "sep"),
        ("BM_NP1",     "N.º pasajeros 1.ª fila (×75 kg/p)",  "2",           "entry"),
        ("BM_NP2",     "N.º pasajeros 2.ª fila (×75 kg/p)",  "0",           "entry"),
        ("_SEP_GEO",   "GEOMETRÍA (mm)", "",                                  "sep"),
        ("BM_DT2",     "Batalla eje 1–2 dT2 (mm)",           "",             "entry"),
        ("BM_DP1",     "Dist. eje 1 → fila 1 dP1 (mm)",     "",             "entry"),
        ("BM_DP2",     "Dist. eje 1 → fila 2 dP2 (mm)",     "",             "entry"),
        ("BM_DVT",     "Voladizo trasero dVt (mm)",           "",            "entry"),
        ("BM_CAJA",    "Longitud caja (0=sin caja) (mm)",    "0",            "entry"),
        ("_SEP_RES",   "RESULTADOS — SIN BOLA", "",                           "sep"),
        ("BM_TARA",    "Tara total (kg)",                    "",              "calc"),
        ("BM_MQU",     "Carga útil mQu (kg)",                "",             "calc"),
        ("BM_DQU",     "Dist. eje 1 → CG carga dQu (mm)",   "",             "calc"),
        ("BM_R1_SB",   "Reacción eje delantero R₁ (kgf)",   "",             "calc"),
        ("BM_R2_SB",   "Reacción eje trasero R₂ (kgf)",     "",             "calc"),
        ("BM_VER1_SB", "Verificación eje delantero",         "",             "calc"),
        ("BM_VER2_SB", "Verificación eje trasero",           "",             "calc"),
    ],

    # ── Unión atornillada con carga aerodinámica ──────────────────────────────
    "Unión atornillada — Carga aerodinámica": [
        ("_SEP_ELEM",  "ELEMENTO A FIJAR", "",                                "sep"),
        ("UA_OBJETO",  "Descripción del elemento",           "",              "entry"),
        ("UA_PP_KG",   "Peso propio Pp (kg)",                "",              "entry"),
        ("_SEP_AERO",  "CARGA AERODINÁMICA", "",                              "sep"),
        ("UA_V_KMH",   "Velocidad de diseño V (km/h)",       "220",          "entry"),
        ("UA_CX",      "Coef. aerodinámico Cx",              "0.65",         "entry"),
        ("UA_ANCHO",   "Anchura expuesta (cm)",               "",             "entry"),
        ("UA_ALTO",    "Altura expuesta (cm)",                "",             "entry"),
        ("UA_A_M2",    "Área de rozamiento A (m²)",          "",              "calc"),
        ("UA_FX_N",    "Fuerza aerodinámica Fx (N)",          "",             "calc"),
        ("UA_FC_N",    "Fuerza de cálculo F = Fx + Pp·g (N)","",             "calc"),
        ("_SEP_TORN",  "TORNILLO", "",                                        "sep"),
        ("UA_METRICA", "Métrica del tornillo",
         TORN_METRICAS_ALL_LIST,                                              "combo"),
        ("UA_CALIDAD", "Calidad del tornillo",
         TORN_CALIDADES_ALL_LIST,                                             "combo"),
        ("UA_CHAPA",   "Tipo de chapa",
         CHAPA_MAT_LIST,                                                     "combo"),
        ("UA_TMIN",    "Espesor mínimo chapa t_min (mm)",    "1.25",         "entry"),
        ("_SEP_RES",   "RESULTADOS", "",                                      "sep"),
        ("UA_NT_TRAC", "Nt tracción (fracción/tornillo)",    "",              "calc"),
        ("UA_NT_CORT", "Nt cortadura (fracción/tornillo)",   "",              "calc"),
        ("UA_NT_APC",  "Nt aplastamiento (fracción/tornillo)","",             "calc"),
        ("UA_NREQ",    "N.º tornillos necesarios",           "",              "calc"),
        ("UA_RESULT",  "Resultado verificación",             "",              "calc"),
        ("UA_NORMA",   "Norma de referencia","Calculo de Elementos / EN 1993","entry"),
    ],

    # ── Unión adhesiva con carga aerodinámica ────────────────────────────────
    "Unión adhesiva — Carga aerodinámica": [
        ("_SEP_ELEM",  "ELEMENTO A FIJAR", "",                                "sep"),
        ("ADH_OBJETO", "Descripción del elemento",           "",              "entry"),
        ("ADH_PP_KG",  "Peso propio Pp (kg)",                "",              "entry"),
        ("_SEP_AERO",  "CARGA AERODINÁMICA", "",                              "sep"),
        ("ADH_V_KMH",  "Velocidad de diseño V (km/h)",       "220",          "entry"),
        ("ADH_CX",     "Coef. aerodinámico Cx",              "0.45",         "entry"),
        ("ADH_ANCHO",  "Anchura expuesta (cm)",               "",             "entry"),
        ("ADH_ALTO",   "Altura expuesta (cm)",                "",             "entry"),
        ("ADH_A_M2",   "Área de rozamiento A (m²)",          "",              "calc"),
        ("ADH_FX_N",   "Fuerza aerodinámica Fx (N)",          "",             "calc"),
        ("ADH_FC_N",   "Fuerza de cálculo F = Fx + Pp·g (N)","",             "calc"),
        ("_SEP_ADH",   "ADHESIVO", "",                                        "sep"),
        ("ADH_TIPO",   "Tipo de adhesivo",
         ADHESIVOS_LIST,                                                      "combo"),
        ("ADH_R_MPA",  "Resistencia adhesivo R (N/mm²)",     "",              "calc"),
        ("ADH_B_MM",   "Anchura del cordón b (mm)",          "4",             "entry"),
        ("ADH_L_MM",   "Longitud del cordón l (mm)",         "",              "entry"),
        ("_SEP_RES",   "RESULTADOS", "",                                      "sep"),
        ("ADH_TAU",    "τ = F / (b·l) (N/mm²)",              "",             "calc"),
        ("ADH_COEF",   "Coef. utilización (τ/R)",             "",            "calc"),
        ("ADH_RESULT", "Resultado verificación",              "",             "calc"),
        ("ADH_NORMA",  "Norma de referencia","Calculo de Elementos / Sikaflex","entry"),
    ],

    # ── Tacos de elevación ────────────────────────────────────────────────────
    "Tacos de elevación — Suspensión / Altura": [
        ("_SEP_VEH",   "VEHÍCULO", "",                                        "sep"),
        ("TACO_MTMA",  "MTMA del vehículo (kg)",             "",              "entry"),
        ("_SEP_TACO",  "GEOMETRÍA DEL TACO", "",                              "sep"),
        ("TACO_MAT",   "Material del taco",
         TACOS_MAT_LIST,                                                      "combo"),
        ("TACO_RCOMP", "Resist. a compresión R (N/mm²)",     "",              "calc"),
        ("TACO_N",     "Número de tacos",                    "4",             "entry"),
        ("TACO_D_MM",  "Diámetro del taco (mm)",             "",              "entry"),
        ("TACO_H_MM",  "Altura del taco (mm)",               "",              "entry"),
        ("_SEP_RES",   "RESULTADOS", "",                                      "sep"),
        ("TACO_AR",    "Área resistente Ar = π·d²/4 (mm²)", "",              "calc"),
        ("TACO_SIGMA", "σ generada (N/mm²)",                 "",              "calc"),
        ("TACO_COEF",  "Coef. utilización (σ/R)",            "",             "calc"),
        ("TACO_RESULT","Resultado verificación",              "",              "calc"),
        ("TACO_NORMA", "Norma de referencia","Calculo de Elementos — Phican", "entry"),
    ],

    # ── Protección trasera — barra antichoque ────────────────────────────────
    "Protección trasera — barra antichoque": [
        ("_SEP_VEH",   "VEHÍCULO", "",                                        "sep"),
        ("PT_MTMA",    "MTMA del vehículo (kg)",              "",             "entry"),
        ("PT_LONG",    "Longitud de la barra (mm)",           "",             "entry"),
        ("_SEP_PERF",  "PERFIL DE LA BARRA", "",                              "sep"),
        ("PT_MAT",     "Material del perfil",
         CHAPA_MAT_LIST,                                                      "combo"),
        ("PT_W_CM3",   "Módulo resistente Wx (cm³)",          "",             "entry"),
        ("PT_I_CM4",   "Momento de inercia Ix (cm⁴)",         "",            "entry"),
        ("PT_A_MM",    "Ancho sección a (mm)",                "",             "entry"),
        ("PT_B_MM",    "Alto sección b (mm)",                 "",             "entry"),
        ("PT_E_MM",    "Espesor pared e (mm)",                "",             "entry"),
        ("_SEP_RES",   "RESULTADOS  (viga biapoyada c. central)", "",         "sep"),
        ("PT_F_HALF",  "F/2 = MTMA·g/2 (N)",                 "",             "calc"),
        ("PT_M_ED",    "M_Ed = F/2 · L/2 (N·mm)",            "",             "calc"),
        ("PT_SADM",    "σ_adm = fy/1.25 (N/mm²)",            "",             "calc"),
        ("PT_M_RD",    "M_Rd = Wx · σ_adm (N·mm)",           "",             "calc"),
        ("PT_COEF",    "Coef. utilización M_Ed/M_Rd",         "",            "calc"),
        ("PT_RESULT",  "Resultado verificación",              "",              "calc"),
        ("PT_NORMA",   "Norma de referencia","Calculo de Elementos / EN 1993","entry"),
    ],

    # ── Frenos — disco (comprobación eficacia) ────────────────────────────────
    "Frenos — disco (comprobación eficacia)": [
        ("_SEP_VEH",   "VEHÍCULO", "",                                        "sep"),
        ("FR_MMA",     "MMA del vehículo (kg)",               "",             "entry"),
        ("FR_MU",      "Coef. rozamiento pastilla-disco μ",   "0.4",          "entry"),
        ("_SEP_NEU",   "NEUMÁTICO", "",                                        "sep"),
        ("FR_ASPECTO", "Relación de aspecto (%)",             "65",           "entry"),
        ("FR_SECCION", "Anchura de sección (mm)",             "195",          "entry"),
        ("FR_LLANTA",  "Diámetro de llanta (pulgadas)",       "15",           "entry"),
        ("FR_RLLANTA", "Radio de llanta calculado (m)",       "",              "calc"),
        ("_SEP_DEL",   "DISCO DELANTERO", "",                                  "sep"),
        ("FR_DEXT_D",  "Diámetro exterior disco del. (mm)",   "",             "entry"),
        ("FR_DINT_D",  "Diámetro interior disco del. (mm)",   "",             "entry"),
        ("FR_LPAST_D", "Longitud pastilla del. (mm)",          "",            "entry"),
        ("FR_DPIST_D", "Diámetro pistón del. (mm)",            "",            "entry"),
        ("_SEP_TRA",   "DISCO TRASERO", "",                                    "sep"),
        ("FR_DEXT_T",  "Diámetro exterior disco tra. (mm)",   "",             "entry"),
        ("FR_DINT_T",  "Diámetro interior disco tra. (mm)",   "",             "entry"),
        ("FR_LPAST_T", "Longitud pastilla tra. (mm)",          "",            "entry"),
        ("FR_DPIST_T", "Diámetro pistón tra. (mm)",            "",            "entry"),
        ("_SEP_HID",   "PRESIÓN HIDRÁULICA (a fuerza máx.)", "",              "sep"),
        ("FR_P_MPa",   "Presión hidráulica de cálculo (MPa)",  "5.3",        "entry"),
        ("_SEP_RES",   "RESULTADOS", "",                                       "sep"),
        ("FR_T_DEL",   "Par frenado delantero T_del (N·m)",   "",             "calc"),
        ("FR_T_TRA",   "Par frenado trasero T_tra (N·m)",     "",             "calc"),
        ("FR_T_TOT",   "Par frenado total T_total (N·m)",     "",             "calc"),
        ("FR_F_FREN",  "Fuerza de frenado F (N)",             "",             "calc"),
        ("FR_EFIC",    "Eficacia de frenado (%)",             "",             "calc"),
        ("FR_RATIO50", "Ratio eficacia/50% (≥1.0)",           "",             "calc"),
        ("FR_RESULT",  "Resultado verificación",               "",            "calc"),
        ("FR_NORMA",   "Norma de referencia",
         "71/320/CEE / RD 2822/1998",                                        "entry"),
    ],

    # ── Grúa autocarga — momento de vuelco ───────────────────────────────────
    "Grúa autocarga — momento de vuelco": [
        ("_SEP_ID",       "IDENTIFICACIÓN GRÚA", "",                         "sep"),
        ("GRUA_MARCA",    "Marca de la grúa",                  "",           "entry"),
        ("GRUA_MODELO",   "Modelo de la grúa",                 "",           "entry"),
        ("GRUA_HOMOLOG",  "N° de homologación",                "",           "entry"),
        ("_SEP_GEO",      "GEOMETRÍA DE TRABAJO", "",                        "sep"),
        ("GRUA_CAP_KG",   "Capacidad de carga nominal (kg)",   "",           "entry"),
        ("GRUA_ALC_MM",   "Alcance máximo (mm)",               "",           "entry"),
        ("GRUA_BCIL_MM",  "Brazo del cilindro hidráulico (mm)","",           "entry"),
        ("_SEP_RES",      "RESULTADOS", "",                                   "sep"),
        ("GRUA_MV_NM",    "Momento de vuelco Mv = P·g·L (N·m)", "",         "calc"),
        ("GRUA_FCIL_N",   "Fuerza en cilindro F_cil = Mv/brazo (N)","",     "calc"),
        ("GRUA_NORMA",    "Norma de referencia","FEM 1.001 / Baselga Cap.5", "entry"),
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
class FormularioProyecto(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Generador de Proyectos — Phican Ingenieros")
        self.configure(bg=GRIS_BG)
        self.resizable(True, True)
        self.minsize(860, 680)   # garantiza que los botones siempre sean visibles

        self.entries = {}
        self._reforma_rows  = []
        self._calc_bloques  = []   # lista de bloques de cálculo justificativo
        self._fotos_cfo_rows = []  # lista de filas de foto para el CFO

        self._build_ui()
        self._centrar_ventana(980, 860)

    # ── Layout principal ──────────────────────────────────────────────────────
    def _build_ui(self):
        # Cabecera
        header = tk.Frame(self, bg=AZUL, pady=14)
        header.pack(fill="x")
        tk.Label(
            header,
            text="  GENERADOR DE PROYECTOS DE REFORMA DE VEHICULO",
            bg=AZUL, fg=BLANCO,
            font=("Segoe UI", 14, "bold"), anchor="w"
        ).pack(fill="x", padx=20)
        tk.Label(
            header,
            text="  Phican Ingenieros",
            bg=AZUL, fg="#90caf9",
            font=("Segoe UI", 10), anchor="w"
        ).pack(fill="x", padx=20)

        # Notebook de pestañas
        style = ttk.Style()
        style.configure("TNotebook",             background=GRIS_BG, borderwidth=0)
        style.configure("TNotebook.Tab",         padding=[14, 7], font=("Segoe UI", 10))
        style.map("TNotebook.Tab",
                  background=[("selected", BLANCO), ("", GRIS_BG)],
                  foreground=[("selected", AZUL),   ("", "#444")])

        # Barra inferior: se empaca PRIMERO con side="bottom" para que el
        # notebook con expand=True no la oculte en pantallas pequeñas
        bottom = tk.Frame(self, bg=GRIS_BG, pady=4)
        bottom.pack(side="bottom", fill="x", padx=16, pady=(4, 10))

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=14, pady=(10, 0))

        self._tab_expediente()
        self._tab_vehiculo()
        self._tab_planos()
        self._tab_ficha()
        self._tab_taller()
        self._tab_cfo()
        self._tab_reforma()
        self._tab_configuracion()

        self.estado_var = tk.StringVar(value="")
        self.lbl_estado = tk.Label(
            bottom, textvariable=self.estado_var,
            bg=GRIS_BG, fg="#555", font=("Segoe UI", 9)
        )
        self.lbl_estado.pack(side="left", padx=4)

        self.btn = tk.Button(
            bottom,
            text="  >  GENERAR PROYECTO  ",
            bg=VERDE, fg=BLANCO, activebackground=VERDE_H, activeforeground=BLANCO,
            font=("Segoe UI", 12, "bold"),
            relief="flat", padx=20, pady=10, cursor="hand2",
            command=self._generar
        )
        self.btn.pack(side="right")

        self.btn_anexo = tk.Button(
            bottom,
            text="  ≡  GENERAR ANEXO  ",
            bg="#1976D2", fg=BLANCO, activebackground="#1565C0", activeforeground=BLANCO,
            font=("Segoe UI", 12, "bold"),
            relief="flat", padx=16, pady=10, cursor="hand2",
            command=self._generar_anexo
        )
        self.btn_anexo.pack(side="right", padx=(0, 8))

        self.btn_ct = tk.Button(
            bottom,
            text="  CT  ",
            bg="#6a1b9a", fg=BLANCO, activebackground="#4a148c", activeforeground=BLANCO,
            font=("Segoe UI", 12, "bold"),
            relief="flat", padx=14, pady=10, cursor="hand2",
            command=self._generar_ct
        )
        self.btn_ct.pack(side="right", padx=(0, 6))

        self.btn_cfo = tk.Button(
            bottom,
            text="  CFO  ",
            bg="#00695c", fg=BLANCO, activebackground="#004d40", activeforeground=BLANCO,
            font=("Segoe UI", 12, "bold"),
            relief="flat", padx=14, pady=10, cursor="hand2",
            command=self._generar_cfo
        )
        self.btn_cfo.pack(side="right", padx=(0, 6))

        # Cargar valores predeterminados guardados (marca, lugar de firma, etc.)
        self.after(50, self._cargar_config)

    # ── Pestaña 1: Expediente + Peticionario + Firma ──────────────────────────
    def _tab_expediente(self):
        frame, canvas = self._nueva_pestana("  Expediente  ")

        self._seccion(frame, "Expediente", [
            ("REFERENCIA",             "Referencia",            siguiente_referencia()),
            ("MES_ANIO",               "Mes y año",             mes_anio_hoy_es()),
        ])
        self._seccion(frame, "Peticionario", [
            ("PETICIONARIO_NOMBRE",    "Nombre",                ""),
            ("PETICIONARIO_APELLIDOS", "Apellidos",             ""),
            ("PETICIONARIO_PROVINCIA", "Provincia",             ""),
        ])
        self._seccion(frame, "Firma", [
            ("LUGAR_FIRMA",            "Lugar de firma",        "Santa Ursula"),
            ("FECHA_FIRMA",            "Fecha de firma",        fecha_hoy_es()),
        ])

        self._seccion(frame, "Técnico firmante", [
            ("TECNICO_NOMBRE",         "Nombre completo",          ""),
            ("TECNICO_COLEGIO",        "Nombre del colegio",       "Ilustre Colegio Oficial de Ingenieros Técnicos de S/C de Tenerife"),
            ("TECNICO_COLEGIO_ABREV",  "Abreviatura del colegio",  "COITITF"),
            ("TECNICO_NUM_COLEGIADO",  "Nº de colegiado",          ""),
        ])

        self._seccion_revision(frame)

    def _seccion_revision(self, parent):
        """Panel para cargar un proyecto existente y generar una nueva revisión."""
        frm = tk.LabelFrame(
            parent, text="  Cargar proyecto para revisión  ",
            bg=BLANCO, fg="#e65100",
            font=("Segoe UI", 10, "bold"),
            relief="solid", bd=1, padx=14, pady=8
        )
        frm.pack(fill="x", padx=4, pady=(6, 2))

        # Fila selector
        row0 = tk.Frame(frm, bg=BLANCO)
        row0.pack(fill="x", pady=3)
        tk.Label(row0, text="Proyecto / Revisión:", bg=BLANCO, fg="#333",
                 font=("Segoe UI", 9), width=22, anchor="e"
                 ).pack(side="left", padx=(0, 8))
        self._rev_var = tk.StringVar()
        self._rev_cb = ttk.Combobox(row0, textvariable=self._rev_var,
                                    state="readonly", font=("Segoe UI", 9), width=36)
        self._rev_cb.pack(side="left")
        tk.Button(row0, text=" ↻ ", bg=BLANCO, fg=AZUL,
                  font=("Segoe UI", 9), relief="flat", cursor="hand2",
                  command=self._actualizar_lista_revisiones
                  ).pack(side="left", padx=(6, 0))

        # Fila botón
        row1 = tk.Frame(frm, bg=BLANCO)
        row1.pack(fill="x", pady=(4, 2))
        tk.Button(row1,
                  text="  Cargar datos y preparar nueva revisión  →",
                  bg="#fff3e0", fg="#e65100",
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", padx=10, pady=5, cursor="hand2",
                  command=self._cargar_revision
                  ).pack(anchor="e")

        self._actualizar_lista_revisiones()

    def _actualizar_lista_revisiones(self):
        opciones = _listar_proyectos_revisables()
        self._rev_cb["values"] = opciones
        if opciones:
            self._rev_cb.current(len(opciones) - 1)

    def _cargar_revision(self):
        sel = self._rev_var.get()
        if not sel:
            messagebox.showwarning("Revisión", "Selecciona un proyecto de la lista.")
            return
        # Formato: "PH.007-2026 — Rev0"
        m = re.match(r"(PH\.\d+-\d{4}) — Rev(\d+)", sel)
        if not m:
            messagebox.showerror("Revisión", f"Formato inesperado: {sel}")
            return
        base, rev_num = m.group(1), int(m.group(2))
        datos_path = _get_output_dir() / base / f"Rev{rev_num}" / "datos.json"
        if not datos_path.exists():
            messagebox.showerror("Revisión", f"No se encontró datos.json en:\n{datos_path}")
            return
        try:
            datos = json.loads(datos_path.read_text(encoding="utf-8"))
        except Exception as e:
            messagebox.showerror("Revisión", f"Error al leer datos:\n{e}")
            return

        # Cargar todos los campos de texto del formulario
        for clave, valor in datos.items():
            if clave in self.entries and isinstance(valor, str):
                self.entries[clave].set(valor)

        # Incrementar el número de revisión en REFERENCIA (PH.007/2026-0 → PH.007/2026-1)
        ref_actual = datos.get("REFERENCIA", "")
        m2 = re.match(r"(.*-)(\d+)$", ref_actual)
        if m2:
            nueva_ref = m2.group(1) + str(rev_num + 1)
            self.entries["REFERENCIA"].set(nueva_ref)

        messagebox.showinfo(
            "Revisión cargada",
            f"Datos de '{base} — Rev{rev_num}' cargados.\n"
            f"Nueva referencia: {self.entries['REFERENCIA'].get()}\n\n"
            "Modifica lo necesario y pulsa GENERAR PROYECTO."
        )

    # ── Pestaña 2: Categoría del vehículo ─────────────────────────────────────
    def _tab_vehiculo(self):
        frame, canvas = self._nueva_pestana("  Vehiculo  ")
        self._seccion_categoria(frame)

    def _seccion_categoria(self, parent):
        """Sección de categoría del vehículo con campos de la ficha técnica."""
        frm = tk.LabelFrame(
            parent, text="  Categoria del vehiculo  ",
            bg=BLANCO, fg=AZUL,
            font=("Segoe UI", 10, "bold"),
            relief="solid", bd=1, padx=14, pady=8
        )
        frm.pack(fill="x", padx=4, pady=(6, 2))

        # ── Categoría principal (combobox) ────────────────────────────────────
        row0 = tk.Frame(frm, bg=BLANCO)
        row0.pack(fill="x", pady=3)
        tk.Label(row0, text="Categoria del vehiculo:", bg=BLANCO, fg="#333",
                 font=("Segoe UI", 9), width=26, anchor="e"
                 ).pack(side="left", padx=(0, 8))
        self._cat_var = tk.StringVar(value="M1 — Turismos (hasta 8 plazas)")
        cb = ttk.Combobox(row0, textvariable=self._cat_var,
                          values=CATEGORIAS_VEHICULO, state="readonly",
                          font=("Segoe UI", 9), width=44)
        cb.pack(side="left")
        self.entries["CATEGORIA_VEHICULO"] = self._cat_var

        # Campo derivado: código corto (M1, N1, etc.) — se calcula al leer
        self._cat_var.trace_add("write", self._on_categoria_change)

        self._cat_codigo_var = tk.StringVar(value="M1")
        self.entries["CATEGORIA_CODIGO"] = self._cat_codigo_var

        # ── Uso del vehículo ──────────────────────────────────────────────────
        uso_opts = [
            "Transporte de personas",
            "Transporte de mercancías",
            "Uso mixto (personas y carga)",
            "Servicio público de viajeros",
            "Emergencias / Servicios especiales",
            "Agricola / Forestal",
            "Obra / Construccion",
            "Otro",
        ]
        row1 = tk.Frame(frm, bg=BLANCO)
        row1.pack(fill="x", pady=3)
        tk.Label(row1, text="Uso del vehiculo:", bg=BLANCO, fg="#333",
                 font=("Segoe UI", 9), width=26, anchor="e"
                 ).pack(side="left", padx=(0, 8))
        uso_var = tk.StringVar(value="Transporte de personas")
        cb2 = ttk.Combobox(row1, textvariable=uso_var, values=uso_opts,
                           state="readonly", font=("Segoe UI", 9), width=44)
        cb2.pack(side="left")
        self.entries["USO_VEHICULO"] = uso_var

    # ── Pestaña 3: Ficha Reducida de características ──────────────────────────
    def _seccion_ficha_ab(self, parent, titulo, campos):
        """LabelFrame con filas Antes → Después para la FICHA REDUCIDA."""
        frm = tk.LabelFrame(
            parent, text=f"  {titulo}  ",
            bg=BLANCO, fg=AZUL,
            font=("Segoe UI", 10, "bold"),
            relief="solid", bd=1, padx=14, pady=8
        )
        frm.pack(fill="x", padx=4, pady=(6, 2))

        hdr = tk.Frame(frm, bg=BLANCO)
        hdr.pack(fill="x", pady=(0, 4))
        tk.Label(hdr, text="", bg=BLANCO, width=40).pack(side="left")
        tk.Label(hdr, text="Antes", bg=BLANCO, fg=AZUL,
                 font=("Segoe UI", 8, "bold"), width=16, anchor="center"
                 ).pack(side="left")
        tk.Label(hdr, text="Después", bg=BLANCO, fg=VERDE,
                 font=("Segoe UI", 8, "bold"), width=16, anchor="center"
                 ).pack(side="left")

        for clave_a, clave_d, etiq in campos:
            r = tk.Frame(frm, bg=BLANCO)
            r.pack(fill="x", pady=2)
            tk.Label(r, text=etiq + ":", bg=BLANCO, fg="#333",
                     font=("Segoe UI", 9), width=40, anchor="e"
                     ).pack(side="left", padx=(0, 4))
            var_a = tk.StringVar()
            var_d = tk.StringVar()
            ttk.Entry(r, textvariable=var_a, font=("Segoe UI", 9), width=14
                      ).pack(side="left", padx=(0, 2))
            tk.Label(r, text="→", bg=BLANCO, fg="#aaa",
                     font=("Segoe UI", 9)).pack(side="left", padx=(0, 2))
            ttk.Entry(r, textvariable=var_d, font=("Segoe UI", 9), width=14
                      ).pack(side="left")
            self.entries[clave_a] = var_a
            self.entries[clave_d] = var_d

    # ── Pestaña Planos ────────────────────────────────────────────────────────
    def _tab_planos(self):
        frame, canvas = self._nueva_pestana("  Planos  ")

        # Estado interno: plano seleccionado
        self._plano_path = None
        self._plano_img_tk = None
        self.entries["PLANO_PATH"] = tk.StringVar(value="")

        # ── Sección principal ─────────────────────────────────────────────────
        frm = tk.LabelFrame(
            frame, text="  Plano técnico del vehículo  ",
            bg=BLANCO, fg=AZUL,
            font=("Segoe UI", 10, "bold"),
            relief="solid", bd=1, padx=14, pady=10
        )
        frm.pack(fill="x", padx=4, pady=(6, 4))

        if not _PLANOS_OK:
            tk.Label(
                frm,
                text="Modulo de planos no disponible.\nInstala las dependencias: pip install requests beautifulsoup4",
                bg=BLANCO, fg="#c62828",
                font=("Segoe UI", 9),
                justify="left"
            ).pack(anchor="w", pady=8)
            return

        # ── Botón buscar ──────────────────────────────────────────────────────
        row_btn = tk.Frame(frm, bg=BLANCO)
        row_btn.pack(fill="x", pady=(0, 8))

        tk.Button(
            row_btn,
            text="  Buscar plano de vehículo...",
            bg=AZUL, fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2",
            padx=16, pady=6,
            command=self._abrir_selector_plano
        ).pack(side="left")

        tk.Button(
            row_btn,
            text="Limpiar",
            bg="#f5f5f5", fg="#555",
            font=("Segoe UI", 9),
            relief="flat", cursor="hand2",
            padx=10, pady=6,
            command=self._limpiar_plano
        ).pack(side="left", padx=(8, 0))

        # ── Info del plano seleccionado ───────────────────────────────────────
        self._lbl_plano_info = tk.Label(
            frm,
            text="Sin plano seleccionado.",
            bg=BLANCO, fg="#777",
            font=("Segoe UI", 9),
            anchor="w", justify="left"
        )
        self._lbl_plano_info.pack(fill="x", pady=(0, 8))

        # ── Preview de imagen ─────────────────────────────────────────────────
        preview_outer = tk.Frame(frm, bg="#e0e0e0", bd=1, relief="solid")
        preview_outer.pack(fill="both", expand=False, pady=(0, 4))

        self._lbl_preview = tk.Label(
            preview_outer,
            text="Vista previa del plano",
            bg="#fafafa", fg="#bbb",
            font=("Segoe UI", 9),
            width=60, height=14,
            anchor="center"
        )
        self._lbl_preview.pack(padx=2, pady=2)

        # ── Planos descargados locales ────────────────────────────────────────
        frm2 = tk.LabelFrame(
            frame, text="  Planos descargados  ",
            bg=BLANCO, fg=AZUL,
            font=("Segoe UI", 10, "bold"),
            relief="solid", bd=1, padx=14, pady=8
        )
        frm2.pack(fill="both", expand=True, padx=4, pady=(4, 4))

        # Lista con scrollbar
        list_frame = tk.Frame(frm2, bg=BLANCO)
        list_frame.pack(fill="both", expand=True)

        sb = ttk.Scrollbar(list_frame, orient="vertical")
        sb.pack(side="right", fill="y")

        self._lb_planos = tk.Listbox(
            list_frame,
            bg=BLANCO, fg="#333",
            font=("Segoe UI", 9),
            selectbackground=AZUL, selectforeground="white",
            relief="flat", bd=0,
            yscrollcommand=sb.set
        )
        self._lb_planos.pack(side="left", fill="both", expand=True)
        sb.config(command=self._lb_planos.yview)

        self._lb_planos.bind("<<ListboxSelect>>", self._on_plano_lista_select)
        self._lb_planos.bind("<Double-Button-1>", self._on_plano_usar)

        btn_row2 = tk.Frame(frm2, bg=BLANCO)
        btn_row2.pack(fill="x", pady=(6, 0))
        tk.Button(
            btn_row2, text="Usar seleccionado",
            bg=AZUL, fg="white",
            font=("Segoe UI", 9), relief="flat", cursor="hand2",
            padx=10, pady=4,
            command=self._on_plano_usar
        ).pack(side="left")
        tk.Button(
            btn_row2, text="Actualizar lista",
            bg="#f5f5f5", fg="#555",
            font=("Segoe UI", 9), relief="flat", cursor="hand2",
            padx=10, pady=4,
            command=self._cargar_lista_planos
        ).pack(side="left", padx=(8, 0))

        # Cargar lista inicial
        self._cargar_lista_planos()

    def _abrir_selector_plano(self):
        """Abre el diálogo de búsqueda de planos, pre-rellenando marca/modelo."""
        marca  = self.entries.get("MARCA",  tk.StringVar()).get().strip()
        modelo = self.entries.get("MODELO", tk.StringVar()).get().strip()

        def _on_select(result, provider, local_path):
            self._aplicar_plano(local_path, result)

        VehicleBlueprintSelector(
            self,
            on_select_callback=_on_select,
            initial_make=marca,
            initial_model=modelo,
        )

    def _aplicar_plano(self, path, result=None, preview_path=None):
        """Actualiza UI con el plano seleccionado."""
        self._plano_path = path
        self.entries["PLANO_PATH"].set(str(path) if path else "")

        if result:
            info = f"Marca: {getattr(result, 'make', '')}  |  Modelo: {getattr(result, 'model', '')}  |  Vista: {getattr(result, 'view_type', '')}"
            if getattr(result, 'year', None):
                info += f"  |  Año: {result.year}"
            self._lbl_plano_info.config(text=info, fg="#1a1a1a")
        elif path:
            p = Path(path)
            self._lbl_plano_info.config(text=p.name, fg="#1a1a1a")
        else:
            self._lbl_plano_info.config(text="Sin plano seleccionado.", fg="#777")

        # Determinar imagen de preview: PNG explícito > PNG hermano del SVG > el propio archivo
        img_path = None
        if preview_path and Path(preview_path).exists():
            img_path = Path(preview_path)
        elif path:
            p = Path(path)
            # Buscar PNG hermano: mismo nombre con _preview.png
            candidato = p.with_name(p.stem + "_preview.png")
            if candidato.exists():
                img_path = candidato
            elif p.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp", ".gif"):
                img_path = p

        if img_path and _PIL_OK:
            try:
                img = Image.open(img_path)
                img.thumbnail((480, 220), Image.LANCZOS)
                self._plano_img_tk = ImageTk.PhotoImage(img)
                self._lbl_preview.config(image=self._plano_img_tk, text="", bg="#fafafa")
            except Exception:
                self._lbl_preview.config(image="", text="No se puede previsualizar", bg="#fafafa", fg="#999")
        elif path:
            self._lbl_preview.config(image="", text=Path(path).name, bg="#fafafa", fg="#555")
            self._plano_img_tk = None
        else:
            self._lbl_preview.config(image="", text="Vista previa del plano", bg="#fafafa", fg="#bbb")
            self._plano_img_tk = None

        self._cargar_lista_planos()

    def _limpiar_plano(self):
        self._aplicar_plano(None)

    def _cargar_lista_planos(self):
        """Rellena el listbox con los planos del índice local + descargados."""
        self._lb_planos.delete(0, "end")
        self._planos_locales = []

        PLANTILLAS_DIR = BASE_DIR / "plantillas_vehiculos"
        idx_path = PLANTILLAS_DIR / "indice.json"

        # 1. Leer índice de siluetas generadas
        if idx_path.exists():
            try:
                import json as _json
                index = _json.loads(idx_path.read_text(encoding="utf-8"))
                self._planos_previews = getattr(self, "_planos_previews", [])
                self._planos_previews.clear()
                for item in index:
                    ruta = PLANTILLAS_DIR / item["archivo"]
                    if ruta.exists():
                        etiqueta = f"[{item['categoria']}] {item['nombre']} — {item['vista']}"
                        self._lb_planos.insert("end", etiqueta)
                        self._planos_locales.append(str(ruta))
                        # PNG de preview
                        prev = item.get("preview", "")
                        prev_path = str(PLANTILLAS_DIR / prev) if prev else ""
                        self._planos_previews.append(prev_path)
            except Exception:
                pass

        # 2. Añadir planos descargados con DownloadManager (si los hay)
        if _PLANOS_OK:
            try:
                dm = DownloadManager()
                extra = dm.get_local_blueprints()
                for p in extra:
                    nombre = Path(p).name if isinstance(p, (str, Path)) else str(p)
                    self._lb_planos.insert("end", f"[Descargado] {nombre}")
                    self._planos_locales.append(str(p))
            except Exception:
                pass

    def _on_plano_lista_select(self, event=None):
        """Preview al seleccionar de la lista."""
        sel = self._lb_planos.curselection()
        if not sel:
            return
        idx = sel[0]
        if hasattr(self, "_planos_locales") and idx < len(self._planos_locales):
            path = self._planos_locales[idx]
            previews = getattr(self, "_planos_previews", [])
            prev = previews[idx] if idx < len(previews) else None
            self._aplicar_plano(path, preview_path=prev)

    def _on_plano_usar(self, event=None):
        """Marca el plano seleccionado en lista como plano activo."""
        self._on_plano_lista_select()

    def _tab_ficha(self):
        frame, _ = self._nueva_pestana("  Ficha  ")

        tk.Label(frame,
                 text="Ficha Reducida de Características — dejar en blanco los campos que no apliquen",
                 bg=GRIS_BG, fg="#888", font=("Segoe UI", 8, "italic")
                 ).pack(anchor="w", padx=8, pady=(4, 0))

        self._seccion(frame, "Datos del vehículo", [
            ("MARCA_PORTADA",   "Marca (portada)",  ""),
            ("MARCA",           "Marca",            ""),
            ("MODELO",          "Modelo",           ""),
            ("TIPO_VEHICULO",   "Tipo",             ""),
            ("VERSION_VEHICULO","Version",          ""),
            ("NUM_BASTIDOR",    "N de bastidor",    ""),
            ("PARTE_FIJA_VIN",  "Parte fija VIN",   ""),
            ("MATRICULA",       "Matricula",        ""),
        ])

        tk.Button(
            frame,
            text="  Guardar MARCA / LUGAR como predeterminados",
            bg="#e3f2fd", fg=AZUL,
            font=("Segoe UI", 8),
            relief="flat", padx=8, pady=3, cursor="hand2",
            command=self._guardar_config
        ).pack(anchor="e", padx=6, pady=(0, 2))

        self._seccion_ficha_ab(frame, "Fabricante del vehículo", [
            ("FABR_BASE_A",   "FABR_BASE_D",   "Fabricante del vehículo base"),
            ("FABR_ULTIMA_A", "FABR_ULTIMA_D", "Fabricante de la última fase de fabricación"),
            ("EMPL_PLACA_A",  "EMPL_PLACA_D",  "Emplazamiento de la placa del fabricante"),
        ])

        self._seccion_ficha_ab(frame, "Homologación e identificación", [
            ("EMPL_VIN_A",          "EMPL_VIN_D",          "Emplazamiento del VIN"),
            ("HOMOL_BASE_A",        "HOMOL_BASE_D",        "Nº homologación — vehículo base"),
            ("FECHA_HOMOL_BASE_A",  "FECHA_HOMOL_BASE_D",  "Fecha homologación — vehículo base"),
            ("HOMOL_COMPL_A",       "HOMOL_COMPL_D",       "Nº homologación — vehículo completo"),
            ("FECHA_HOMOL_COMPL_A", "FECHA_HOMOL_COMPL_D", "Fecha homologación — vehículo completo"),
        ])

        self._seccion_ficha_ab(frame, "Constitución general", [
            ("NUM_EJES",    "NUM_EJES_POST",  "Nº de ejes y ruedas"),
            ("EJES_MOTR_A", "EJES_MOTR_D",   "Ejes motrices (nº, localización, interconexión)"),
        ])

        self._seccion_ficha_ab(frame, "Masas y dimensiones", [
            ("DISTANCIA_EJES",    "DISTANCIA_EJES_POST",    "Distancia entre ejes (mm)"),
            ("VIAS_EJES_A",       "VIAS_EJES_D",            "Vías de los ejes"),
            ("LONGITUD_VEH",      "LONGITUD_VEH_POST",      "Longitud (mm)"),
            ("LONG_MAX_A",        "LONG_MAX_D",             "Longitud máxima admisible"),
            ("ANCHURA_VEH",       "ANCHURA_VEH_POST",       "Anchura (mm)"),
            ("ANCH_MAX_A",        "ANCH_MAX_D",             "Anchura máxima admisible"),
            ("ALTURA_VEH",        "ALTURA_VEH_POST",        "Altura (mm)"),
            ("VOLADIZO_A",        "VOLADIZO_D",             "Voladizo trasero"),
            ("TARA_VEHICULO_KG",  "TARA_VEHICULO_KG_POST",  "Tara / Masa en orden de marcha (kg)"),
            ("MASA_MIN_A",        "MASA_MIN_D",             "Masa mínima admisible — vehículo completado"),
            ("MMTA",              "MMTA_POST",              "MMTA (kg)"),
            ("MMA",               "MMA_POST",               "MMA (kg)"),
            ("MMTA_EJE_A",        "MMTA_EJE_D",             "MMTA por eje (1º, 2º…)"),
            ("MMA_EJE_A",         "MMA_EJE_D",              "MMA por eje"),
            ("MMTC",              "MMTC_POST",              "MMTC (kg)"),
            ("MMA_CONJ_A",        "MMA_CONJ_D",             "MMA del conjunto prevista"),
            ("MASA_REMOLC_A",     "MASA_REMOLC_D",          "Masa remolcable máx. técn. admisible"),
            ("REMOLQ_BARRA_A",    "REMOLQ_BARRA_D",         "Remolque con barra de tracción"),
            ("REMOLQ_EJE_A",      "REMOLQ_EJE_D",           "Remolque de eje central"),
            ("MASA_REMOLQ_SF_A",  "MASA_REMOLQ_SF_D",       "Masa máx. del remolque sin frenos"),
            ("CARGA_VERT_A",      "CARGA_VERT_D",           "Carga vertical estática / punto acoplamiento"),
        ])

        self._seccion_ficha_ab(frame, "Unidad motriz", [
            ("FABR_MOTOR_A",  "FABR_MOTOR_D",  "Fabricante o marca del motor"),
            ("COD_MOTOR_A",   "COD_MOTOR_D",   "Código del motor"),
            ("MOTOR_COMB_A",  "MOTOR_COMB_D",  "Motor de combustión interna"),
            ("FUNC_MOTOR_A",  "FUNC_MOTOR_D",  "Principio de funcionamiento"),
            ("CILINDROS_A",   "CILINDROS_D",   "Nº y disposición de cilindros"),
            ("CILINDRADA_A",  "CILINDRADA_D",  "Cilindrada (cm³)"),
            ("COMBUSTIBLE_A", "COMBUSTIBLE_D", "Tipo de combustible o fuente de energía"),
            ("POT_NETA_A",    "POT_NETA_D",    "Potencia neta máxima (kW a min⁻¹)"),
            ("MOTOR_ELEC_A",  "MOTOR_ELEC_D",  "Motor eléctrico puro (si/no)"),
            ("POT_HORA_A",    "POT_HORA_D",    "Potencia máxima por hora (kW)"),
            ("MOTOR_HIBR_A",  "MOTOR_HIBR_D",  "Motor híbrido (si/no)"),
            ("TIPO_HIBR_A",   "TIPO_HIBR_D",   "Tipo (híbrido)"),
        ])

        self._seccion_ficha_ab(frame, "Transmisión", [
            ("TRANS_TIPO_A", "TRANS_TIPO_D", "Tipo (Mecánica / Hidráulica / Eléctrica…)"),
            ("CAJA_CAMB_A",  "CAJA_CAMB_D",  "Caja de cambios (tipo)"),
            ("NUM_RELAC_A",  "NUM_RELAC_D",  "Nº de relaciones"),
        ])

        self._seccion_ficha_ab(frame, "Suspensión / Dirección / Frenado", [
            ("SUSPENSION_A", "SUSPENSION_D", "Tipo de suspensión delantera y trasera"),
            ("DIRECCION_A",  "DIRECCION_D",  "Dirección, tipo de asistencia"),
            ("FRENADO_A",    "FRENADO_D",    "Dispositivo de frenado / ABS (si/no)"),
        ])

        self._seccion_ficha_ab(frame, "Carrocería", [
            ("CARROCERIA_A", "CARROCERIA_D", "Tipo de carrocería"),
            ("VISION_IND_A", "VISION_IND_D", "Dispositivos de visión indirecta"),
            ("PUERTAS_A",    "PUERTAS_D",    "Nº y disposición de puertas"),
            ("PLAZAS_A",     "PLAZAS_D",     "Plazas de asiento (incluido conductor)"),
            ("HOMOL_CE_A",   "HOMOL_CE_D",   "Homologación CE de dispositivo de acoplamiento"),
            ("PROT_DELT_A",  "PROT_DELT_D",  "Sistemas de protección delantera"),
        ])

        self._seccion_ficha_ab(frame, "Alumbrado y señalización", [
            ("ALUMBR_OBL_A", "ALUMBR_OBL_D", "Dispositivos obligatorios (nº)"),
            ("ALUMBR_FAC_A", "ALUMBR_FAC_D", "Dispositivos facultativos (nº)"),
        ])

        self._seccion_ficha_ab(frame, "Varios", [
            ("VEL_MAX_A",        "VEL_MAX_D",        "Velocidad máxima"),
            ("RUIDO_A",          "RUIDO_D",          "Nivel de ruido parado Db(A) a min⁻¹"),
            ("EMISIONES_A",      "EMISIONES_D",      "Nivel de emisiones Euro"),
            ("CO2_A",            "CO2_D",            "Emisión de CO₂ ciclo mixto (g/km)"),
            ("POT_FISCAL_A",     "POT_FISCAL_D",     "Potencia fiscal (CVF)"),
            ("OBSERV_FICHA_A",   "OBSERV_FICHA_D",   "Observaciones"),
            ("OPCIONES_HOMOL_A", "OPCIONES_HOMOL_D", "Opciones incluidas en la homologación de tipo"),
        ])

    def _cargar_config(self):
        """Carga valores predeterminados desde config.json al iniciar."""
        if not CONFIG_PATH.exists():
            return
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            for clave, valor in cfg.items():
                if clave in self.entries:
                    self.entries[clave].set(valor)
            if "OUTPUT_PATH" in cfg and hasattr(self, "_output_path_var"):
                self._output_path_var.set(cfg["OUTPUT_PATH"])
            if hasattr(self, "_template_vars"):
                for clave, var in self._template_vars.items():
                    if clave in cfg:
                        var.set(cfg[clave])
        except Exception:
            pass

    def _guardar_config(self):
        """Guarda los campos fijos (marca, lugar, técnico, ruta) como predeterminados en config.json."""
        cfg = {c: self.entries[c].get() for c in CAMPOS_CONFIG if c in self.entries}
        if hasattr(self, "_output_path_var"):
            cfg["OUTPUT_PATH"] = self._output_path_var.get()
        if hasattr(self, "_template_vars"):
            for clave, var in self._template_vars.items():
                cfg[clave] = var.get()
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Configuración", "Configuración guardada correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuracion:\n{e}")

    def _on_categoria_change(self, *args):
        """Extrae el código corto (M1, N1, etc.) del texto del combo y filtra reformas."""
        full = self._cat_var.get()
        codigo = full.split(" ")[0] if full else ""
        self._cat_codigo_var.set(codigo)
        # Actualizar listas de reformas para mostrar solo las aplicables
        self._actualizar_listas_reformas()

    def _actualizar_listas_reformas(self):
        """Recarga los valores de todos los combobox de código según la categoría."""
        cat = self._cat_codigo_var.get()
        nuevos_codigos = _codigos_para_categoria(cat)
        for fila in getattr(self, "_reforma_rows", []):
            cb = fila.get("cb_codigo")
            if cb is not None:
                actual = fila["codigo_var"].get()
                cb["values"] = nuevos_codigos
                if actual and actual not in nuevos_codigos:
                    fila["codigo_var"].set("")
                    fila["grupo_var"].set("")
                    fila["desc_var"].set("")
            self._actualizar_directivas_card(fila)

    def _actualizar_directivas_card(self, fila_ref):
        """Muestra u oculta la tabla de directivas según el código y categoría seleccionados."""
        dir_frame = fila_ref.get("dir_frame")
        if dir_frame is None:
            return

        cod = fila_ref["codigo_var"].get().strip()
        directivas = DIRECTIVAS_POR_CODIGO.get(cod, [])

        # Limpiar contenido anterior
        for w in dir_frame.winfo_children():
            w.destroy()

        if not cod or not directivas:
            dir_frame.pack_forget()
            return

        # Categoría del vehículo y su índice en la lista [M1..O4]
        _CATS = ["M1", "M2", "M3", "N1", "N2", "N3", "O1", "O2", "O3", "O4"]
        cat_var = getattr(self, "_cat_codigo_var", None)
        cat_cod = cat_var.get() if cat_var else ""
        try:
            cat_idx = _CATS.index(cat_cod)
        except ValueError:
            cat_idx = None

        # Filtrar: solo filas aplicables a la categoría activa
        if cat_idx is not None:
            filas = [(s, r, vals) for s, r, vals in directivas
                     if vals[cat_idx] not in ("(x)", "(-)", "x", "-")]
        else:
            filas = list(directivas)

        if not filas:
            dir_frame.pack_forget()
            return

        # Insertar entre cabecera e items_frame
        items_frame = fila_ref.get("items_frame")
        if items_frame:
            dir_frame.pack(fill="x", padx=0, pady=0, before=items_frame)
        else:
            dir_frame.pack(fill="x")

        BG  = "#f0f4ff"
        BG2 = "#e8eeff"
        HDR = "#c5d3f7"

        # Fila de título
        hdr_row = tk.Frame(dir_frame, bg=HDR)
        hdr_row.pack(fill="x")
        cat_label = f" — {cat_cod}" if cat_cod else ""
        tk.Label(hdr_row, text=f"  Actos reglamentarios aplicables{cat_label}",
                 bg=HDR, fg=AZUL, font=("Segoe UI", 7, "bold"),
                 anchor="w").pack(side="left", padx=(4, 0), pady=2)
        tk.Label(hdr_row,
                 text="(1) última actualiz.   (2) versión matriculación  ",
                 bg=HDR, fg="#555", font=("Segoe UI", 7, "italic"),
                 anchor="e").pack(side="right", padx=4, pady=2)

        # Fila de columnas
        col_row = tk.Frame(dir_frame, bg=HDR)
        col_row.pack(fill="x")
        tk.Label(col_row, text="  Sistema afectado", bg=HDR, fg="#333",
                 font=("Segoe UI", 7, "bold"), anchor="w"
                 ).pack(side="left", fill="x", expand=True)
        tk.Label(col_row, text="Referencia normativa", bg=HDR, fg="#333",
                 font=("Segoe UI", 7, "bold"), anchor="w", width=26
                 ).pack(side="left")
        tk.Label(col_row, text="Aplic.", bg=HDR, fg="#333",
                 font=("Segoe UI", 7, "bold"), anchor="center", width=6
                 ).pack(side="left")

        # Filas de datos — valor de la columna de la categoría activa
        for i, (sistema, referencia, vals) in enumerate(filas):
            nivel = vals[cat_idx] if cat_idx is not None else "—"
            bg_row = BG if i % 2 == 0 else BG2
            row = tk.Frame(dir_frame, bg=bg_row)
            row.pack(fill="x")
            tk.Label(row, text=f"  {sistema}", bg=bg_row, fg="#222",
                     font=("Segoe UI", 7), anchor="w"
                     ).pack(side="left", fill="x", expand=True)
            tk.Label(row, text=referencia, bg=bg_row, fg="#444",
                     font=("Segoe UI", 7), anchor="w", width=26
                     ).pack(side="left")
            color = "#1a6b2a" if nivel == "(1)" else "#b35000" if nivel == "(2)" else "#555"
            tk.Label(row, text=nivel, bg=bg_row, fg=color,
                     font=("Segoe UI", 7, "bold"), anchor="center", width=6
                     ).pack(side="left")

    # ── Pestaña 4: Técnico y Taller ──────────────────────────────────────────
    def _tab_taller(self):
        frame, canvas = self._nueva_pestana("  Taller  ")

        # ── Sección datos del taller (por proyecto) ───────────────────────────
        self._seccion(frame, "Datos del taller", [
            ("TALLER_TITULAR",         "Titular del taller",       ""),
            ("TALLER_LOCALIDAD",       "Localidad",                ""),
            ("TALLER_CALLE",           "Dirección",                ""),
            ("TALLER_CP",              "Código postal",            ""),
            ("TALLER_PROVINCIA",       "Provincia",                ""),
            ("TALLER_TELEFONO",        "Teléfono",                 ""),
            ("TALLER_ACTIVIDAD",       "Actividad",                "Reparación de Vehículos"),
            ("TALLER_REG_INDUSTRIAL",  "Registro industrial",      ""),
        ])

    # ── Pestaña CFO — fotografías ─────────────────────────────────────────────
    def _tab_cfo(self):
        frame, canvas = self._nueva_pestana("  CFO  ")
        self._seccion_fotos_cfo(frame)

    # ── Sección dinámica de fotografías del CFO ───────────────────────────────
    def _seccion_fotos_cfo(self, parent):
        frm = tk.LabelFrame(
            parent, text="  Fotografías del CFO  ",
            bg=BLANCO, fg="#00695c",
            font=("Segoe UI", 10, "bold"),
            relief="solid", bd=1, padx=10, pady=8
        )
        frm.pack(fill="x", padx=4, pady=(6, 2))

        info = tk.Label(
            frm,
            text="Las fotos se insertan en el CFO en una cuadrícula de 2 columnas con su leyenda.",
            bg=BLANCO, fg="#555", font=("Segoe UI", 8)
        )
        info.pack(anchor="w", pady=(0, 4))

        self._fotos_cfo_container = tk.Frame(frm, bg=BLANCO)
        self._fotos_cfo_container.pack(fill="x")

        tk.Button(
            frm,
            text="  +  Añadir fotografía",
            bg="#e0f2f1", fg="#00695c",
            font=("Segoe UI", 9, "bold"),
            relief="flat", padx=8, pady=4, cursor="hand2",
            command=self._add_foto_cfo_row
        ).pack(anchor="w", pady=(6, 0))

    def _add_foto_cfo_row(self):
        idx = len(self._fotos_cfo_rows)

        row = tk.Frame(self._fotos_cfo_container, bg=BLANCO,
                       highlightbackground="#ddd", highlightthickness=1)
        row.pack(fill="x", pady=2, padx=2)

        # Número de foto (actualizable)
        lbl_num = tk.Label(row, text=f"Foto {idx + 1}:", bg=BLANCO, fg="#333",
                           font=("Segoe UI", 9), width=7, anchor="e")
        lbl_num.pack(side="left", padx=(4, 4))

        # Nombre de archivo (sólo lectura, actualizado al hacer browse)
        var_display = tk.StringVar(value="Sin seleccionar")
        lbl_file = tk.Label(row, textvariable=var_display, bg="#f5f5f5", fg="#444",
                            font=("Segoe UI", 8), width=28, anchor="w",
                            relief="flat", padx=4)
        lbl_file.pack(side="left")

        # Path completo (oculto, usado para exportar)
        var_path = tk.StringVar()

        tk.Button(
            row, text="...", bg=BLANCO, fg=AZUL,
            font=("Segoe UI", 8), relief="flat", padx=4, cursor="hand2",
            command=lambda vp=var_path, vd=var_display: self._browse_foto_cfo(vp, vd)
        ).pack(side="left", padx=(2, 8))

        # Leyenda
        tk.Label(row, text="Leyenda:", bg=BLANCO, fg="#333",
                 font=("Segoe UI", 8)).pack(side="left")
        var_caption = tk.StringVar()
        ttk.Entry(row, textvariable=var_caption,
                  font=("Segoe UI", 8), width=22).pack(side="left", padx=(4, 8))

        # Botones orden + eliminar
        row_data = {
            "frame":       row,
            "lbl_num":     lbl_num,
            "var_path":    var_path,
            "var_display": var_display,
            "var_caption": var_caption,
        }
        tk.Button(row, text="↑", bg=BLANCO, fg="#555",
                  font=("Segoe UI", 8), relief="flat", padx=3, cursor="hand2",
                  command=lambda rd=row_data: self._mover_foto_cfo(rd, -1)
                  ).pack(side="left")
        tk.Button(row, text="↓", bg=BLANCO, fg="#555",
                  font=("Segoe UI", 8), relief="flat", padx=3, cursor="hand2",
                  command=lambda rd=row_data: self._mover_foto_cfo(rd, +1)
                  ).pack(side="left")
        tk.Button(row, text="✕", bg=BLANCO, fg=ROJO,
                  font=("Segoe UI", 8), relief="flat", padx=3, cursor="hand2",
                  command=lambda rd=row_data: self._remove_foto_cfo(rd)
                  ).pack(side="left", padx=(0, 4))

        self._fotos_cfo_rows.append(row_data)

    def _browse_foto_cfo(self, var_path, var_display):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Seleccionar fotografía",
            filetypes=[
                ("Imágenes", "*.jpg *.jpeg *.png *.bmp"),
                ("Todos los archivos", "*.*"),
            ]
        )
        if path:
            var_path.set(path)
            name = Path(path).name
            var_display.set(name[:32] + "…" if len(name) > 32 else name)

    def _mover_foto_cfo(self, row_data, direccion):
        idx = self._fotos_cfo_rows.index(row_data)
        nuevo = idx + direccion
        if 0 <= nuevo < len(self._fotos_cfo_rows):
            self._fotos_cfo_rows[idx], self._fotos_cfo_rows[nuevo] = (
                self._fotos_cfo_rows[nuevo], self._fotos_cfo_rows[idx]
            )
            self._re_render_fotos_cfo()

    def _remove_foto_cfo(self, row_data):
        if row_data in self._fotos_cfo_rows:
            self._fotos_cfo_rows.remove(row_data)
            row_data["frame"].destroy()
            self._re_render_fotos_cfo()

    def _re_render_fotos_cfo(self):
        """Re-empaqueta las filas en el orden actual y actualiza los números."""
        for rd in self._fotos_cfo_rows:
            rd["frame"].pack_forget()
        for i, rd in enumerate(self._fotos_cfo_rows):
            rd["frame"].pack(fill="x", pady=2, padx=2)
            rd["lbl_num"].config(text=f"Foto {i + 1}:")

    def _recoger_fotos_cfo(self):
        return [
            {"path": rd["var_path"].get(), "caption": rd["var_caption"].get()}
            for rd in self._fotos_cfo_rows
            if rd["var_path"].get()
        ]

    # ── Pestaña Configuración ─────────────────────────────────────────────────
    def _tab_configuracion(self):
        from tkinter import filedialog
        frame, canvas = self._nueva_pestana("  Configuración  ")

        # ── Ruta de guardado ─────────────────────────────────────────────────
        frm_ruta = tk.LabelFrame(
            frame, text="  Ruta de guardado  ",
            bg=BLANCO, fg=AZUL,
            font=("Segoe UI", 10, "bold"),
            relief="solid", bd=1, padx=14, pady=10
        )
        frm_ruta.pack(fill="x", padx=4, pady=(10, 4))

        tk.Label(
            frm_ruta,
            text="Los proyectos generados se guardarán en la carpeta indicada.\n"
                 "Si se deja vacío se usa la carpeta 'proyectos_generados' junto al programa.",
            bg=BLANCO, fg="#555", font=("Segoe UI", 8)
        ).pack(anchor="w", pady=(0, 6))

        # ── Fila de acceso rápido a unidades detectadas ───────────────────────
        drives = _detectar_drives_rapidos()
        if drives:
            row_drives = tk.Frame(frm_ruta, bg=BLANCO)
            row_drives.pack(fill="x", pady=(0, 6))
            tk.Label(row_drives, text="Acceso rápido:", bg=BLANCO, fg="#555",
                     font=("Segoe UI", 8)).pack(side="left", padx=(0, 8))

            drive_colors = {
                "☁": ("#e3f2fd", "#1565c0"),   # nube → azul
                "🖥": ("#f3e5f5", "#6a1b9a"),   # red  → morado
            }
            for etiq, ruta_drive in drives.items():
                icono = etiq[0]
                bg_d, fg_d = drive_colors.get(icono, (AZUL_L, AZUL))

                def _set_drive(r=ruta_drive):
                    self._output_path_var.set(r)

                tk.Button(
                    row_drives, text=etiq,
                    bg=bg_d, fg=fg_d,
                    font=("Segoe UI", 8), relief="flat", padx=7, pady=2,
                    cursor="hand2", command=_set_drive
                ).pack(side="left", padx=(0, 4))

        # ── Fila entrada + botón examinar ─────────────────────────────────────
        row_path = tk.Frame(frm_ruta, bg=BLANCO)
        row_path.pack(fill="x")

        # Valor inicial: lo que haya en config.json, o el directorio por defecto
        _init_path = str(_get_output_dir())
        self._output_path_var = tk.StringVar(value=_init_path)
        entry_path = ttk.Entry(row_path, textvariable=self._output_path_var,
                               font=("Segoe UI", 9), width=52)
        entry_path.pack(side="left", padx=(0, 6))

        def _browse_output():
            carpeta = filedialog.askdirectory(
                title="Seleccionar carpeta de guardado",
                initialdir=self._output_path_var.get() or str(BASE_DIR)
            )
            if carpeta:
                self._output_path_var.set(carpeta)

        tk.Button(
            row_path, text="  Examinar…  ", bg=AZUL_L, fg=AZUL,
            font=("Segoe UI", 8), relief="flat", padx=6, cursor="hand2",
            command=_browse_output
        ).pack(side="left")

        # Nota informativa
        tk.Label(
            frm_ruta,
            text="⚠  Cambia la carpeta y pulsa «Guardar configuración» para que el cambio persista.",
            bg=BLANCO, fg="#e65100", font=("Segoe UI", 8, "italic")
        ).pack(anchor="w", pady=(6, 0))

        # ── Datos del técnico firmante (predeterminados) ──────────────────────
        frm_tec = tk.LabelFrame(
            frame, text="  Técnico firmante — valores predeterminados  ",
            bg=BLANCO, fg="#555",
            font=("Segoe UI", 10, "bold"),
            relief="solid", bd=1, padx=14, pady=6
        )
        frm_tec.pack(fill="x", padx=4, pady=(6, 4))

        tk.Label(
            frm_tec,
            text="Estos campos están vinculados a la pestaña «Expediente».\n"
                 "Al pulsar «Guardar configuración» se establecen como valores predeterminados al abrir el programa.",
            bg=BLANCO, fg="#777", font=("Segoe UI", 8)
        ).pack(anchor="w", pady=(0, 4))

        for clave, etiqueta in [
            ("TECNICO_NOMBRE",        "Nombre completo"),
            ("TECNICO_COLEGIO",       "Nombre del colegio"),
            ("TECNICO_COLEGIO_ABREV", "Abreviatura"),
            ("TECNICO_NUM_COLEGIADO", "Nº de colegiado"),
        ]:
            row = tk.Frame(frm_tec, bg=BLANCO)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=etiqueta + ":", bg=BLANCO, fg="#444",
                     font=("Segoe UI", 9), width=26, anchor="e"
                     ).pack(side="left", padx=(0, 8))
            if clave in self.entries:
                ttk.Entry(row, textvariable=self.entries[clave],
                          font=("Segoe UI", 9), width=40).pack(side="left")

        # ── Plantillas de documentos ──────────────────────────────────────────
        frm_plt = tk.LabelFrame(
            frame, text="  Plantillas de documentos  ",
            bg=BLANCO, fg="#7b1fa2",
            font=("Segoe UI", 10, "bold"),
            relief="solid", bd=1, padx=14, pady=10
        )
        frm_plt.pack(fill="x", padx=4, pady=(6, 4))

        tk.Label(
            frm_plt,
            text="Selecciona el archivo .docx que se usará como plantilla para cada documento.\n"
                 "Si se deja vacío se usa la plantilla por defecto junto al programa.",
            bg=BLANCO, fg="#555", font=("Segoe UI", 8)
        ).pack(anchor="w", pady=(0, 8))

        self._template_vars = {}
        _plantillas = [
            ("TEMPLATE_PROYECTO", "Proyecto técnico",    BASE_DIR / "PLANTILLA_BASE.docx"),
            ("TEMPLATE_CFO",      "CFO",                 BASE_DIR / "PLANTILLA_CFO.docx"),
            ("TEMPLATE_CT",       "Certificado de taller (CT)", BASE_DIR / "PLANTILLA_CT.docx"),
        ]

        for clave, etiqueta, default_path in _plantillas:
            var = tk.StringVar(value=str(default_path))
            self._template_vars[clave] = var

            row_t = tk.Frame(frm_plt, bg=BLANCO)
            row_t.pack(fill="x", pady=3)

            tk.Label(row_t, text=etiqueta + ":", bg=BLANCO, fg="#444",
                     font=("Segoe UI", 9), width=26, anchor="e"
                     ).pack(side="left", padx=(0, 6))

            ttk.Entry(row_t, textvariable=var,
                      font=("Segoe UI", 8), width=42).pack(side="left", padx=(0, 4))

            def _make_browse(v=var, d=default_path):
                def _browse():
                    p = filedialog.askopenfilename(
                        title="Seleccionar plantilla",
                        filetypes=[("Word document", "*.docx"), ("Todos los archivos", "*.*")],
                        initialdir=str(Path(v.get()).parent) if Path(v.get()).exists() else str(BASE_DIR)
                    )
                    if p:
                        v.set(p)
                return _browse

            def _make_open(v=var):
                def _open():
                    p = v.get().strip()
                    if p and Path(p).exists():
                        if sys.platform == "win32":
                            os.startfile(p)
                        else:
                            subprocess.Popen(["xdg-open", p])
                    else:
                        messagebox.showwarning("Plantilla", f"No se encuentra el archivo:\n{p}")
                return _open

            tk.Button(row_t, text="Examinar…", bg="#f3e5f5", fg="#7b1fa2",
                      font=("Segoe UI", 8), relief="flat", padx=5, cursor="hand2",
                      command=_make_browse(var, default_path)
                      ).pack(side="left", padx=(0, 3))

            tk.Button(row_t, text="Abrir", bg=GRIS_BG, fg="#444",
                      font=("Segoe UI", 8), relief="flat", padx=5, cursor="hand2",
                      command=_make_open(var)
                      ).pack(side="left")

        # ── Botón guardar ─────────────────────────────────────────────────────
        tk.Button(
            frame,
            text="  💾  Guardar configuración  ",
            bg=AZUL, fg=BLANCO, activebackground="#0d47a1", activeforeground=BLANCO,
            font=("Segoe UI", 10, "bold"),
            relief="flat", padx=16, pady=8, cursor="hand2",
            command=self._guardar_config
        ).pack(anchor="e", padx=10, pady=(10, 4))

        # ── Sección: Plantillas de cálculo ───────────────────────────────────
        frm_plt = tk.LabelFrame(
            frame,
            text="  Plantillas de cálculo  ",
            bg=BLANCO, fg="#6a1b9a",
            font=("Segoe UI", 10, "bold"),
            relief="solid", bd=1, padx=14, pady=8
        )
        frm_plt.pack(fill="x", padx=4, pady=(10, 4))

        tk.Label(
            frm_plt,
            text="Genera un documento Word por cada tipo de cálculo con las fórmulas "
                 "y pasos predefinidos. Puedes editarlos para añadir comentarios.",
            bg=BLANCO, fg="#777", font=("Segoe UI", 8), wraplength=600, justify="left"
        ).pack(anchor="w", pady=(0, 6))

        row_plt = tk.Frame(frm_plt, bg=BLANCO)
        row_plt.pack(fill="x", pady=2)

        tk.Button(
            row_plt,
            text="  Generar TODAS las plantillas  ",
            bg="#7b1fa2", fg=BLANCO, activebackground="#4a148c", activeforeground=BLANCO,
            font=("Segoe UI", 9, "bold"),
            relief="flat", padx=12, pady=5, cursor="hand2",
            command=self._generar_todas_plantillas
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            row_plt,
            text="  Abrir carpeta plantillas  ",
            bg=GRIS_BG, fg="#444",
            font=("Segoe UI", 9), relief="flat", padx=10, pady=5, cursor="hand2",
            command=self._abrir_carpeta_plantillas
        ).pack(side="left")

        # Selector individual
        row_plt2 = tk.Frame(frm_plt, bg=BLANCO)
        row_plt2.pack(fill="x", pady=(6, 2))

        tk.Label(row_plt2, text="Tipo:", bg=BLANCO, fg="#444",
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 4))
        self._plt_tipo_var = tk.StringVar()
        tipos_con_formula = [k for k in CALC_TIPOS if k != "— Sin cálculo —"]
        cb_plt = ttk.Combobox(
            row_plt2, textvariable=self._plt_tipo_var,
            values=tipos_con_formula,
            width=42, font=("Segoe UI", 9), state="readonly"
        )
        cb_plt.pack(side="left", padx=4)
        if tipos_con_formula:
            cb_plt.current(0)

        tk.Button(
            row_plt2,
            text="  Generar plantilla  ",
            bg="#e1bee7", fg="#6a1b9a",
            font=("Segoe UI", 9, "bold"),
            relief="flat", padx=10, pady=3, cursor="hand2",
            command=self._generar_una_plantilla
        ).pack(side="left", padx=6)

    def _generar_todas_plantillas(self):
        """Genera plantillas Word para todos los tipos de cálculo."""
        from generar_anexo import generar_todas_plantillas
        carpeta = BASE_DIR / "plantillas_calculo"
        try:
            resultados = generar_todas_plantillas(carpeta)
            ok = sum(1 for _, _, s in resultados if s)
            messagebox.showinfo("Plantillas generadas",
                                f"Se han generado {ok} plantillas en:\n{carpeta}")
        except Exception as e:
            messagebox.showerror("Error", f"Error generando plantillas:\n{e}")

    def _generar_una_plantilla(self):
        """Genera plantilla Word para un tipo de cálculo seleccionado."""
        from generar_anexo import generar_plantilla_tipo
        tipo = self._plt_tipo_var.get()
        if not tipo:
            messagebox.showwarning("Aviso", "Selecciona un tipo de cálculo.")
            return
        carpeta = BASE_DIR / "plantillas_calculo"
        try:
            ruta = generar_plantilla_tipo(tipo, carpeta)
            messagebox.showinfo("Plantilla generada", f"Plantilla guardada en:\n{ruta}")
            if os.name == "nt":
                os.startfile(str(ruta))
        except Exception as e:
            messagebox.showerror("Error", f"Error generando plantilla:\n{e}")

    def _abrir_carpeta_plantillas(self):
        """Abre la carpeta de plantillas de cálculo."""
        carpeta = BASE_DIR / "plantillas_calculo"
        carpeta.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(str(carpeta))

    # ── Pestaña 5: Actos reglamentarios + Cálculos justificativos ────────────
    def _tab_reforma(self):
        frame, canvas = self._nueva_pestana("  Reforma  ")
        self._seccion_reformas(frame)
        self._seccion_calculos(frame)

    # ── Sección de cálculos justificativos (dinámica) ────────────────────────
    def _seccion_calculos(self, parent):
        """Crea la sección de cálculos justificativos con bloques dinámicos."""
        self._frm_calculos_outer = tk.LabelFrame(
            parent,
            text="  Cálculos justificativos  ",
            bg=BLANCO, fg=AZUL,
            font=("Segoe UI", 10, "bold"),
            relief="solid", bd=1, padx=14, pady=8
        )
        self._frm_calculos_outer.pack(fill="x", padx=4, pady=(10, 2))

        self._calc_container = tk.Frame(self._frm_calculos_outer, bg=BLANCO)
        self._calc_container.pack(fill="x")

        btn_add = tk.Button(
            self._frm_calculos_outer,
            text="  +  Añadir bloque de cálculo",
            bg="#e3f2fd", fg=AZUL,
            font=("Segoe UI", 9, "bold"),
            relief="flat", padx=10, pady=5, cursor="hand2",
            command=self._add_calc_bloque
        )
        btn_add.pack(anchor="w", pady=(10, 2))

        # Un bloque por defecto
        self._add_calc_bloque()

    def _add_calc_bloque(self):
        """Añade un bloque de cálculo justificativo."""
        idx = len(self._calc_bloques)

        # Marco exterior del bloque con color de fondo alternado
        bg_color = "#f8f9fb" if idx % 2 == 0 else BLANCO
        bloque_frame = tk.Frame(
            self._calc_container,
            bg=bg_color, relief="solid", bd=1
        )
        bloque_frame.pack(fill="x", pady=(0, 6))

        # ── Cabecera del bloque ──────────────────────────────────────────────
        hdr = tk.Frame(bloque_frame, bg=AZUL_L)
        hdr.pack(fill="x")

        tk.Label(
            hdr, text=f"  Cálculo {idx + 1}", bg=AZUL_L, fg=AZUL,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left", padx=6, pady=4)

        # Reforma asociada (se actualiza con las filas de actos reglamentarios)
        tk.Label(hdr, text="Reforma asociada:", bg=AZUL_L, fg="#444",
                 font=("Segoe UI", 9)).pack(side="left", padx=(16, 4), pady=4)
        reforma_var = tk.StringVar(value="— General —")
        cb_reforma = ttk.Combobox(
            hdr, textvariable=reforma_var, width=22,
            font=("Segoe UI", 9), state="readonly"
        )
        cb_reforma.pack(side="left", padx=4, pady=4)

        # Tipo de cálculo
        tk.Label(hdr, text="Tipo de cálculo:", bg=AZUL_L, fg="#444",
                 font=("Segoe UI", 9)).pack(side="left", padx=(16, 4), pady=4)
        tipo_var = tk.StringVar(value="— Sin cálculo —")
        cb_tipo = ttk.Combobox(
            hdr, textvariable=tipo_var,
            values=list(CALC_TIPOS.keys()),
            width=38, font=("Segoe UI", 9), state="readonly"
        )
        cb_tipo.pack(side="left", padx=4, pady=4)

        # Botón eliminar bloque
        tk.Button(
            hdr, text=" ✕ ",
            bg="#ffebee", fg=ROJO,
            font=("Segoe UI", 9, "bold"),
            relief="flat", padx=6, pady=2, cursor="hand2",
            command=lambda bf=bloque_frame: self._del_calc_bloque(bf)
        ).pack(side="right", padx=6, pady=4)

        # ── Cuerpo del bloque (campos dinámicos) ────────────────────────────
        body_frame = tk.Frame(bloque_frame, bg=bg_color)
        body_frame.pack(fill="x", padx=12, pady=(4, 8))

        # Diccionario con toda la info del bloque
        bloque = {
            "frame":       bloque_frame,
            "body_frame":  body_frame,
            "reforma_var": reforma_var,
            "tipo_var":    tipo_var,
            "cb_reforma":  cb_reforma,
            "bg":          bg_color,
            "campos":      {},   # {clave: StringVar}
            "_recalcular_fn": None,  # se asigna en _bind_xxx_autocalc
        }

        # Botón Calcular (en cabecera, lado derecho antes del ✕)
        btn_calc = tk.Button(
            hdr, text="  Calcular  ",
            bg=VERDE, fg=BLANCO, activebackground=VERDE_H, activeforeground=BLANCO,
            font=("Segoe UI", 9, "bold"),
            relief="flat", padx=8, pady=2, cursor="hand2",
            command=lambda b=bloque: self._trigger_calcular(b)
        )
        btn_calc.pack(side="right", padx=(0, 4), pady=4)
        bloque["btn_calc"] = btn_calc
        self._calc_bloques.append(bloque)

        # Construir campos iniciales (vacíos para "— Sin cálculo —")
        self._rebuild_calc_campos(bloque)

        # Actualizar lista de reformas disponibles en el combo
        self._actualizar_combos_reforma()

        # Listener: reconstruir campos cuando cambia el tipo
        tipo_var.trace_add("write", lambda *a, b=bloque: self._rebuild_calc_campos(b))

    def _rebuild_calc_campos(self, bloque):
        """Destruye y recrea los campos del cuerpo según el tipo seleccionado."""
        for widget in bloque["body_frame"].winfo_children():
            widget.destroy()
        bloque["campos"] = {}
        tipo = bloque["tipo_var"].get()
        self._render_calc_campos(bloque["body_frame"], bloque["campos"],
                                 bloque["bg"], tipo)
        # Conectar autocalc según tipo
        if "Uniones atornilladas" in tipo:
            self._bind_tornillo_autocalc(bloque)
        elif tipo == "Flexión simple de viga — Navier":
            self._bind_flexion_autocalc(bloque)
        elif tipo == "Torsión de perfil — Saint-Venant":
            self._bind_torsion_autocalc(bloque)
        elif tipo == "Pandeo de barra — Euler":
            self._bind_pandeo_autocalc(bloque)
        elif tipo == "Distribución de cargas por ejes":
            self._bind_ejes_autocalc(bloque)
        elif tipo == "Estabilidad al vuelco lateral":
            self._bind_vuelco_autocalc(bloque)
        elif tipo == "Uniones soldadas — cordón en ángulo":
            self._bind_soldadura_autocalc(bloque)
        elif tipo == "Grúa autocarga — momento de vuelco":
            self._bind_grua_autocalc(bloque)
        elif tipo == "Balance de masas — Turismo (M1/M2)":
            self._bind_balance_masas_autocalc(bloque)
        elif tipo == "Unión atornillada — Carga aerodinámica":
            self._bind_ua_aero_autocalc(bloque)
        elif tipo == "Unión adhesiva — Carga aerodinámica":
            self._bind_adh_aero_autocalc(bloque)
        elif tipo == "Tacos de elevación — Suspensión / Altura":
            self._bind_tacos_autocalc(bloque)
        elif tipo == "Protección trasera — barra antichoque":
            self._bind_pt_autocalc(bloque)
        elif tipo == "Frenos — disco (comprobación eficacia)":
            self._bind_frenos_autocalc(bloque)
        elif tipo == "Suspensión neumática — Balonas / Airbag":
            self._bind_suspension_neumatica_autocalc(bloque)
        elif tipo == "Suspensión mecánica — Sustitución muelles / amortiguadores":
            self._bind_suspension_mecanica_autocalc(bloque)
        elif tipo == "Cambio de motor / Sustitución unidad motriz":
            self._bind_motor_autocalc(bloque)
        elif tipo == "Conversión eléctrica o híbrida":
            self._bind_conversion_electrica_autocalc(bloque)
        elif tipo == "Enganche / Dispositivo de acoplamiento":
            self._bind_enganche_autocalc(bloque)
        elif tipo == "Modificación de masas / MMA":
            self._bind_masas_autocalc(bloque)
        elif tipo == "Modificación de carrocería / Estructura":
            self._bind_carroceria_autocalc(bloque)
        elif tipo == "Modificación del sistema de frenos":
            self._bind_frenos_mod_autocalc(bloque)

    def _render_calc_campos(self, body, campos_dict, bg, tipo):
        """
        Renderiza los campos de cálculo de 'tipo' dentro de 'body'.
        Escribe StringVars en campos_dict. Devuelve True si es una unión
        atornillada (para que el llamador enganche el autocalc).
        """
        definicion = CALC_TIPOS.get(tipo, [])

        if not definicion:
            tk.Label(
                body,
                text="Selecciona un tipo de cálculo para mostrar los campos.",
                bg=bg, fg="#aaa", font=("Segoe UI", 9, "italic")
            ).pack(anchor="w", pady=4)
            return False

        grid_row = 0
        grid_col = 0
        col_wrap = 2

        def flush_col():
            nonlocal grid_row, grid_col
            if grid_col == 1:
                grid_row += 1
                grid_col  = 0

        for entrada in definicion:
            if len(entrada) == 3:
                clave, etiqueta, defecto = entrada
                widget_tipo = "entry"
                opciones    = defecto
            else:
                clave, etiqueta, opciones, widget_tipo = entrada
                defecto = opciones if isinstance(opciones, str) else \
                          (opciones[0] if opciones else "")

            if widget_tipo == "sep":
                flush_col()
                body.columnconfigure(0, weight=1)
                body.columnconfigure(1, weight=1)
                sep_frame = tk.Frame(body, bg=bg)
                sep_frame.grid(row=grid_row, column=0, columnspan=2,
                               sticky="ew", pady=(10, 2))
                tk.Label(sep_frame, text=f"  {etiqueta}  ",
                         bg=AZUL_L, fg=AZUL,
                         font=("Segoe UI", 8, "bold"), anchor="w"
                         ).pack(fill="x", ipady=2)
                grid_row += 1
                grid_col  = 0
                continue

            body.columnconfigure(grid_col, weight=1)
            cell = tk.Frame(body, bg=bg)
            cell.grid(row=grid_row, column=grid_col,
                      sticky="ew", padx=(0, 12), pady=2)
            tk.Label(cell, text=etiqueta + ":",
                     bg=bg, fg="#333", font=("Segoe UI", 9), anchor="w"
                     ).pack(anchor="w")

            var = tk.StringVar(value=defecto)
            if widget_tipo == "combo":
                ttk.Combobox(cell, textvariable=var, values=opciones,
                             width=26, font=("Segoe UI", 9),
                             state="readonly").pack(fill="x")
            elif widget_tipo == "calc":
                ttk.Entry(cell, textvariable=var, width=26,
                          font=("Segoe UI", 9, "italic"),
                          state="readonly").pack(fill="x")
            else:
                ttk.Entry(cell, textvariable=var, width=26,
                          font=("Segoe UI", 9)).pack(fill="x")

            campos_dict[clave] = var

            grid_col += 1
            if grid_col >= col_wrap:
                grid_col  = 0
                grid_row += 1

    def _bind_tornillo_autocalc(self, bloque):
        """Conecta los combos de diámetro/calidad/cargas al cálculo automático."""
        campos = bloque["campos"]

        def recalcular(*_):
            diam    = campos.get("TORN_DIAM",       tk.StringVar()).get()
            calidad = campos.get("TORN_CALIDAD",    tk.StringVar()).get()
            tipo_c  = campos.get("TORN_TIPO_CORTE", tk.StringVar()).get()

            # ── Propiedades mecánicas ────────────────────────────────────────
            res = calcular_resistencias_tornillo(diam, calidad, tipo_c)
            if res:
                _set(campos, "TORN_A_BRUTA", f"{res['A_bruta_mm2']:.1f}")
                _set(campos, "TORN_A_S",     f"{res['A_s_mm2']:.1f}")
                _set(campos, "TORN_FYB",     f"{res['fyb_MPa']}")
                _set(campos, "TORN_FUB",     f"{res['fub_MPa']}")
                _set(campos, "TORN_FV_RD_1", f"{res['Fv_Rd_1plano_N']:.1f}")
                _set(campos, "TORN_FV_RD",   f"{res['Fv_Rd_N']:.1f}")
                _set(campos, "TORN_FT_RD",   f"{res['Ft_Rd_N']:.1f}")

            # ── Comprobaciones ───────────────────────────────────────────────
            try:
                Fv_Rd = float(campos["TORN_FV_RD"].get() or 0)
                Ft_Rd = float(campos["TORN_FT_RD"].get() or 0)
                Fv_Ed = float(campos.get("TORN_FV_ED", tk.StringVar()).get() or 0)
                Ft_Ed = float(campos.get("TORN_FT_ED", tk.StringVar()).get() or 0)

                coef_cort = Fv_Ed / Fv_Rd if Fv_Rd > 0 else 0.0
                coef_trac = Ft_Ed / Ft_Rd if Ft_Rd > 0 else 0.0
                # Interacción: Fv,Ed/Fv,Rd + Ft,Ed/(1.4·Ft,Rd) ≤ 1.0
                interacc  = (Fv_Ed / Fv_Rd if Fv_Rd > 0 else 0) + \
                            (Ft_Ed / (1.4 * Ft_Rd) if Ft_Rd > 0 else 0)

                _set(campos, "TORN_COEF_CORT", f"{coef_cort:.3f}")
                _set(campos, "TORN_COEF_TRAC", f"{coef_trac:.3f}")
                _set(campos, "TORN_INTER",     f"{interacc:.3f}")
                ok = (coef_cort <= 1.0 and coef_trac <= 1.0 and interacc <= 1.0
                      and Fv_Ed > 0)
                _set(campos, "TORN_RESULTADO",
                     "✓ VERIFICA" if ok else ("✗ NO VERIFICA" if Fv_Ed > 0 else "—"))
            except (ValueError, ZeroDivisionError):
                pass

        def _set(c, key, val):
            if key in c:
                c[key].set(val)

        bloque["_recalcular_fn"] = recalcular
        # Disparar recálculo cuando cambian selector o cargas
        for key in ("TORN_DIAM", "TORN_CALIDAD", "TORN_TIPO_CORTE",
                    "TORN_FV_ED", "TORN_FT_ED"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    # ── Autocalc: Flexión simple de viga — Navier ────────────────────────────
    def _bind_flexion_autocalc(self, bloque):
        campos = bloque["campos"]

        def _set(key, val):
            if key in campos:
                campos[key].set(val)

        def recalcular(*_):
            # Actualizar fy según material
            mat = campos.get("FLEX_MATERIAL", tk.StringVar()).get()
            props = ACERO_PROPIEDADES.get(mat, {})
            if props:
                _set("FLEX_FY_MPA", str(props["fy"]))

            try:
                M   = float(campos.get("FLEX_M_NM",  tk.StringVar()).get() or 0)
                W   = float(campos.get("FLEX_W_CM3", tk.StringVar()).get() or 0)
                fy  = float(campos.get("FLEX_FY_MPA",tk.StringVar()).get() or 0)
                if M > 0 and W > 0 and fy > 0:
                    r = calcular_flexion_viga(M, W, fy)
                    _set("FLEX_SIGMA",  f"{r['sigma_MPa']:.2f}")
                    _set("FLEX_FD",     f"{r['fd_MPa']:.2f}")
                    _set("FLEX_COEF",   f"{r['coef']:.4f}")
                    _set("FLEX_RESULT",
                         "✓ VERIFICA" if r["verifica"] else "✗ NO VERIFICA")
            except (ValueError, ZeroDivisionError):
                pass

        bloque["_recalcular_fn"] = recalcular
        for key in ("FLEX_MATERIAL", "FLEX_M_NM", "FLEX_W_CM3", "FLEX_FY_MPA"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    # ── Autocalc: Torsión de perfil — Saint-Venant ───────────────────────────
    def _bind_torsion_autocalc(self, bloque):
        campos = bloque["campos"]

        def _set(key, val):
            if key in campos:
                campos[key].set(val)

        def recalcular(*_):
            try:
                MT  = float(campos.get("TORS_MT_NM", tk.StringVar()).get() or 0)
                Ip  = float(campos.get("TORS_IP_CM4",tk.StringVar()).get() or 0)
                r   = float(campos.get("TORS_R_MM",  tk.StringVar()).get() or 0)
                fy  = float(campos.get("TORS_FY_MPA",tk.StringVar()).get() or 0)
                if MT > 0 and Ip > 0 and r > 0 and fy > 0:
                    res = calcular_torsion(MT, Ip, r, fy)
                    _set("TORS_TAU",     f"{res['tau_MPa']:.2f}")
                    _set("TORS_TAU_ADM", f"{res['tau_adm_MPa']:.2f}")
                    _set("TORS_COEF",    f"{res['coef']:.4f}")
                    _set("TORS_RESULT",
                         "✓ VERIFICA" if res["verifica"] else "✗ NO VERIFICA")
            except (ValueError, ZeroDivisionError):
                pass

        bloque["_recalcular_fn"] = recalcular
        for key in ("TORS_MT_NM", "TORS_IP_CM4", "TORS_R_MM", "TORS_FY_MPA"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    # ── Autocalc: Pandeo de barra — Euler ────────────────────────────────────
    def _bind_pandeo_autocalc(self, bloque):
        campos = bloque["campos"]

        def _set(key, val):
            if key in campos:
                campos[key].set(val)

        def recalcular(*_):
            # Actualizar fy y μ según selecciones
            mat  = campos.get("PAND_MATERIAL", tk.StringVar()).get()
            props = ACERO_PROPIEDADES.get(mat, {})
            if props:
                _set("PAND_FY_MPA", str(props["fy"]))

            cond = campos.get("PAND_COND", tk.StringVar()).get()
            mu   = PANDEO_MU.get(cond, 1.0)
            _set("PAND_MU", f"{mu}")

            try:
                N   = float(campos.get("PAND_N_N",   tk.StringVar()).get() or 0)
                L   = float(campos.get("PAND_L_MM",  tk.StringVar()).get() or 0)
                I   = float(campos.get("PAND_I_CM4", tk.StringVar()).get() or 0)
                A   = float(campos.get("PAND_A_CM2", tk.StringVar()).get() or 0)
                E   = float(campos.get("PAND_E_MPA", tk.StringVar()).get() or 210000)
                fy  = float(campos.get("PAND_FY_MPA",tk.StringVar()).get() or 235)

                if L > 0 and I > 0 and A > 0:
                    res = calcular_pandeo_euler(N, L, mu, I, A, E, fy)
                    _set("PAND_IRG",    f"{res['i_mm']:.2f}")
                    _set("PAND_ESBELT", f"{res['lambda']:.1f}")
                    _set("PAND_ESBR",   f"{res['lambda_r']:.3f}")
                    _set("PAND_PCR",    f"{res['Pcr_N']:.0f}")
                    if N > 0:
                        _set("PAND_COEF",   f"{res['coef']:.4f}")
                        _set("PAND_RESULT",
                             "✓ VERIFICA" if res["verifica"] else "✗ NO VERIFICA")
            except (ValueError, ZeroDivisionError):
                pass

        bloque["_recalcular_fn"] = recalcular
        for key in ("PAND_MATERIAL", "PAND_COND", "PAND_N_N", "PAND_L_MM",
                    "PAND_I_CM4", "PAND_A_CM2", "PAND_E_MPA"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    # ── Autocalc: Distribución de cargas por ejes ────────────────────────────
    def _bind_ejes_autocalc(self, bloque):
        campos = bloque["campos"]

        def _set(key, val):
            if key in campos:
                campos[key].set(val)

        def recalcular(*_):
            try:
                L    = float(campos.get("EJES_BATALL", tk.StringVar()).get() or 0)
                d    = float(campos.get("EJES_D_MM",   tk.StringVar()).get() or 0)
                P    = float(campos.get("EJES_P_KG",   tk.StringVar()).get() or 0)
                Q1   = float(campos.get("EJES_Q1_KG",  tk.StringVar()).get() or 0)
                Q2   = float(campos.get("EJES_Q2_KG",  tk.StringVar()).get() or 0)
                MMA1 = float(campos.get("EJES_MMA1",   tk.StringVar()).get() or 0)
                MMA2 = float(campos.get("EJES_MMA2",   tk.StringVar()).get() or 0)
                if L > 0 and P > 0:
                    res = calcular_distribucion_ejes(L, d, P, Q1, Q2, MMA1, MMA2)
                    _set("EJES_DQ1", f"{res['dQ1_kg']:.1f}")
                    _set("EJES_DQ2", f"{res['dQ2_kg']:.1f}")
                    _set("EJES_NQ1", f"{res['Q1n_kg']:.1f}")
                    _set("EJES_NQ2", f"{res['Q2n_kg']:.1f}")
                    _set("EJES_RES1",
                         "✓ VERIFICA" if res["ok1"] else "✗ SUPERA MMA")
                    _set("EJES_RES2",
                         "✓ VERIFICA" if res["ok2"] else "✗ SUPERA MMA")
            except (ValueError, ZeroDivisionError):
                pass

        bloque["_recalcular_fn"] = recalcular
        for key in ("EJES_BATALL", "EJES_D_MM", "EJES_P_KG",
                    "EJES_Q1_KG", "EJES_Q2_KG", "EJES_MMA1", "EJES_MMA2"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    # ── Autocalc: Estabilidad al vuelco lateral ──────────────────────────────
    def _bind_vuelco_autocalc(self, bloque):
        campos = bloque["campos"]

        def _set(key, val):
            if key in campos:
                campos[key].set(val)

        def recalcular(*_):
            try:
                s   = float(campos.get("VUELT_ANCHO", tk.StringVar()).get() or 0)
                hcg = float(campos.get("VUELT_HCG",   tk.StringVar()).get() or 0)
                if s > 0 and hcg > 0:
                    res = calcular_vuelco_lateral(s, hcg)
                    _set("VUELT_ETA",   f"{res['eta']:.3f}")
                    _set("VUELT_ALIM",  f"{res['a_lim']:.3f}")
                    _set("VUELT_VLIM",  f"{res['v_kmh']:.1f}")
                    _set("VUELT_RESULT",
                         "✓ ESTABLE (η≥0.3)" if res["estable"]
                         else "✗ INESTABLE (η<0.3)")
            except (ValueError, ZeroDivisionError):
                pass

        bloque["_recalcular_fn"] = recalcular
        for key in ("VUELT_ANCHO", "VUELT_HCG"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    # ── Autocalc: Uniones soldadas — cordón en ángulo ────────────────────────
    def _bind_soldadura_autocalc(self, bloque):
        campos = bloque["campos"]

        def _set(key, val):
            if key in campos:
                campos[key].set(val)

        def recalcular(*_):
            mat = campos.get("SOLD_MATERIAL", tk.StringVar()).get()
            props = ACERO_PROPIEDADES.get(mat, {})
            if props:
                _set("SOLD_FU_MPA", str(props["fu"]))
                _set("SOLD_BETA",   str(SOLDADURA_BETA_W.get(mat, 0.8)))

            try:
                F    = float(campos.get("SOLD_F_N",   tk.StringVar()).get() or 0)
                a    = float(campos.get("SOLD_GARG",  tk.StringVar()).get() or 0)
                Lw   = float(campos.get("SOLD_LONG",  tk.StringVar()).get() or 0)
                fu   = float(campos.get("SOLD_FU_MPA",tk.StringVar()).get() or 0)
                beta = float(campos.get("SOLD_BETA",  tk.StringVar()).get() or 0)
                if F > 0 and a > 0 and Lw > 0 and fu > 0 and beta > 0:
                    res = calcular_union_soldada(F, a, Lw, fu, beta)
                    _set("SOLD_TAU",   f"{res['tau_MPa']:.2f}")
                    _set("SOLD_FW_RD", f"{res['fw_Rd_MPa']:.2f}")
                    _set("SOLD_COEF",  f"{res['coef']:.4f}")
                    _set("SOLD_RESULT",
                         "✓ VERIFICA" if res["verifica"] else "✗ NO VERIFICA")
            except (ValueError, ZeroDivisionError):
                pass

        bloque["_recalcular_fn"] = recalcular
        for key in ("SOLD_MATERIAL", "SOLD_F_N", "SOLD_GARG",
                    "SOLD_LONG", "SOLD_FU_MPA", "SOLD_BETA"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    # ── Autocalc: Grúa autocarga — momento de vuelco ─────────────────────────
    def _bind_grua_autocalc(self, bloque):
        campos = bloque["campos"]

        def _set(key, val):
            if key in campos:
                campos[key].set(val)

        def recalcular(*_):
            try:
                P    = float(campos.get("GRUA_CAP_KG",  tk.StringVar()).get() or 0)
                L    = float(campos.get("GRUA_ALC_MM",  tk.StringVar()).get() or 0)
                bcil = float(campos.get("GRUA_BCIL_MM", tk.StringVar()).get() or 0)
                if P > 0 and L > 0 and bcil > 0:
                    res = calcular_grua_autocarga(P, L, bcil)
                    _set("GRUA_MV_NM",  f"{res['Mv_Nm']:.1f}")
                    _set("GRUA_FCIL_N", f"{res['F_cil_N']:.0f}")
            except (ValueError, ZeroDivisionError):
                pass

        bloque["_recalcular_fn"] = recalcular
        for key in ("GRUA_CAP_KG", "GRUA_ALC_MM", "GRUA_BCIL_MM"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    # ── Autocalc: Balance de masas — Turismo ─────────────────────────────────
    def _bind_balance_masas_autocalc(self, bloque):
        campos = bloque["campos"]

        def _s(k, v):
            if k in campos: campos[k].set(v)

        def recalcular(*_):
            try:
                MMA    = float(campos.get("BM_MMA",    tk.StringVar()).get() or 0)
                MMAe1  = float(campos.get("BM_MMA_E1", tk.StringVar()).get() or 0)
                MMAe2  = float(campos.get("BM_MMA_E2", tk.StringVar()).get() or 0)
                mT1    = float(campos.get("BM_MT1",    tk.StringVar()).get() or 0)
                mT2    = float(campos.get("BM_MT2",    tk.StringVar()).get() or 0)
                nP1    = float(campos.get("BM_NP1",    tk.StringVar()).get() or 0)
                nP2    = float(campos.get("BM_NP2",    tk.StringVar()).get() or 0)
                dT2    = float(campos.get("BM_DT2",    tk.StringVar()).get() or 0)
                dP1    = float(campos.get("BM_DP1",    tk.StringVar()).get() or 0)
                dP2    = float(campos.get("BM_DP2",    tk.StringVar()).get() or 0)
                dVt    = float(campos.get("BM_DVT",    tk.StringVar()).get() or 0)
                caja   = float(campos.get("BM_CAJA",   tk.StringVar()).get() or 0)
                if dT2 > 0:
                    r = calcular_balance_masas_turismo(
                        mT1, mT2, nP1, nP2, MMA, MMAe1, MMAe2,
                        dT2, dP1, dP2, dVt, caja)
                    if r:
                        _s("BM_TARA",    f"{r['TARA_kg']:.1f}")
                        _s("BM_MQU",     f"{r['mQu_kg']:.1f}")
                        _s("BM_DQU",     f"{r['dQu_mm']:.1f}")
                        _s("BM_R1_SB",   f"{r['R1_sb']:.2f}")
                        _s("BM_R2_SB",   f"{r['R2_sb']:.2f}")
                        _s("BM_VER1_SB",
                           "✓ VERIFICA" if r["ok1_sb"] else "✗ SUPERA MMA")
                        _s("BM_VER2_SB",
                           "✓ VERIFICA" if r["ok2_sb"] else "✗ SUPERA MMA")
            except (ValueError, ZeroDivisionError):
                pass

        bloque["_recalcular_fn"] = recalcular
        for key in ("BM_MMA","BM_MMA_E1","BM_MMA_E2","BM_MT1","BM_MT2",
                    "BM_NP1","BM_NP2","BM_DT2","BM_DP1","BM_DP2","BM_DVT","BM_CAJA"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    # ── Autocalc: Unión atornillada con carga aerodinámica ───────────────────
    def _bind_ua_aero_autocalc(self, bloque):
        campos = bloque["campos"]

        def _s(k, v):
            if k in campos: campos[k].set(v)

        def recalcular(*_):
            try:
                Cx  = float(campos.get("UA_CX",      tk.StringVar()).get() or 0)
                V   = float(campos.get("UA_V_KMH",   tk.StringVar()).get() or 0)
                w   = float(campos.get("UA_ANCHO",   tk.StringVar()).get() or 0)
                h   = float(campos.get("UA_ALTO",    tk.StringVar()).get() or 0)
                Pp  = float(campos.get("UA_PP_KG",   tk.StringVar()).get() or 0)
                met = campos.get("UA_METRICA",  tk.StringVar()).get()
                cal = campos.get("UA_CALIDAD",  tk.StringVar()).get()
                cha = campos.get("UA_CHAPA",    tk.StringVar()).get()
                tmin= float(campos.get("UA_TMIN",    tk.StringVar()).get() or 0)

                if Cx > 0 and V > 0 and w > 0 and h > 0:
                    aero = calcular_carga_aerodinamica(Cx, V, w, h, Pp)
                    _s("UA_A_M2",  f"{aero['A_m2']:.4f}")
                    _s("UA_FX_N",  f"{aero['Fx_N']:.2f}")
                    _s("UA_FC_N",  f"{aero['F_calc_N']:.2f}")

                if met and cal and cha and tmin > 0 and Cx > 0 and V > 0:
                    r = calcular_union_atornillada_aero(Cx, V, w, h, Pp,
                                                        met, cal, cha, tmin)
                    if r:
                        _s("UA_NT_TRAC", f"{r['Nt_trac']:.5f}")
                        _s("UA_NT_CORT", f"{r['Nt_cort']:.5f}")
                        _s("UA_NT_APC",  f"{r['Nt_aplast']:.5f}")
                        _s("UA_NREQ",    f"{r['N_req']}")
                        _s("UA_RESULT",  "✓ VERIFICA" if r["N_req"] >= 1 else "—")
            except (ValueError, ZeroDivisionError):
                pass

        bloque["_recalcular_fn"] = recalcular
        for key in ("UA_CX","UA_V_KMH","UA_ANCHO","UA_ALTO","UA_PP_KG",
                    "UA_METRICA","UA_CALIDAD","UA_CHAPA","UA_TMIN"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    # ── Autocalc: Unión adhesiva con carga aerodinámica ──────────────────────
    def _bind_adh_aero_autocalc(self, bloque):
        campos = bloque["campos"]

        def _s(k, v):
            if k in campos: campos[k].set(v)

        def recalcular(*_):
            try:
                Cx  = float(campos.get("ADH_CX",     tk.StringVar()).get() or 0)
                V   = float(campos.get("ADH_V_KMH",  tk.StringVar()).get() or 0)
                w   = float(campos.get("ADH_ANCHO",  tk.StringVar()).get() or 0)
                h   = float(campos.get("ADH_ALTO",   tk.StringVar()).get() or 0)
                Pp  = float(campos.get("ADH_PP_KG",  tk.StringVar()).get() or 0)
                adh = campos.get("ADH_TIPO",  tk.StringVar()).get()
                b   = float(campos.get("ADH_B_MM",   tk.StringVar()).get() or 0)
                l   = float(campos.get("ADH_L_MM",   tk.StringVar()).get() or 0)

                if Cx > 0 and V > 0 and w > 0 and h > 0:
                    aero = calcular_carga_aerodinamica(Cx, V, w, h, Pp)
                    _s("ADH_A_M2", f"{aero['A_m2']:.4f}")
                    _s("ADH_FX_N", f"{aero['Fx_N']:.2f}")
                    _s("ADH_FC_N", f"{aero['F_calc_N']:.2f}")

                if adh:
                    _s("ADH_R_MPA", str(ADHESIVOS.get(adh, "")))

                if adh and b > 0 and l > 0 and Cx > 0:
                    r = calcular_union_adhesiva_aero(Cx, V, w, h, Pp, adh, b, l)
                    if r:
                        _s("ADH_TAU",    f"{r['tau_MPa']:.4f}")
                        _s("ADH_COEF",   f"{r['coef']:.4f}")
                        _s("ADH_RESULT",
                           "✓ VERIFICA" if r["verifica"] else "✗ NO VERIFICA")
            except (ValueError, ZeroDivisionError):
                pass

        bloque["_recalcular_fn"] = recalcular
        for key in ("ADH_CX","ADH_V_KMH","ADH_ANCHO","ADH_ALTO","ADH_PP_KG",
                    "ADH_TIPO","ADH_B_MM","ADH_L_MM"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    # ── Autocalc: Tacos de elevación ──────────────────────────────────────────
    def _bind_tacos_autocalc(self, bloque):
        campos = bloque["campos"]

        def _s(k, v):
            if k in campos: campos[k].set(v)

        def recalcular(*_):
            mat = campos.get("TACO_MAT", tk.StringVar()).get()
            if mat:
                _s("TACO_RCOMP", str(TACOS_MAT.get(mat, "")))
            try:
                MTMA = float(campos.get("TACO_MTMA", tk.StringVar()).get() or 0)
                n    = float(campos.get("TACO_N",    tk.StringVar()).get() or 0)
                d    = float(campos.get("TACO_D_MM", tk.StringVar()).get() or 0)
                if MTMA > 0 and n > 0 and d > 0 and mat:
                    r = calcular_tacos_elevacion(MTMA, mat, n, d)
                    if r:
                        _s("TACO_AR",    f"{r['Ar_mm2']:.2f}")
                        _s("TACO_SIGMA", f"{r['sigma_MPa']:.4f}")
                        _s("TACO_COEF",  f"{r['coef']:.4f}")
                        _s("TACO_RESULT",
                           "✓ VERIFICA" if r["verifica"] else "✗ NO VERIFICA")
            except (ValueError, ZeroDivisionError):
                pass

        bloque["_recalcular_fn"] = recalcular
        for key in ("TACO_MAT","TACO_MTMA","TACO_N","TACO_D_MM"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    # ── Autocalc: Protección trasera ──────────────────────────────────────────
    def _bind_pt_autocalc(self, bloque):
        campos = bloque["campos"]

        def _s(k, v):
            if k in campos: campos[k].set(v)

        def recalcular(*_):
            try:
                MTMA  = float(campos.get("PT_MTMA", tk.StringVar()).get() or 0)
                L     = float(campos.get("PT_LONG", tk.StringVar()).get() or 0)
                W     = float(campos.get("PT_W_CM3",tk.StringVar()).get() or 0)
                mat   = campos.get("PT_MAT", tk.StringVar()).get()
                if MTMA > 0 and L > 0 and W > 0 and mat:
                    r = calcular_proteccion_trasera(MTMA, L, W, mat)
                    if r:
                        _s("PT_F_HALF", f"{r['F_half_N']:.1f}")
                        _s("PT_M_ED",   f"{r['M_Ed_Nmm']:.0f}")
                        _s("PT_SADM",   f"{r['sigma_adm']:.1f}")
                        _s("PT_M_RD",   f"{r['M_Rd_Nmm']:.0f}")
                        _s("PT_COEF",   f"{r['coef']:.4f}")
                        _s("PT_RESULT",
                           "✓ VERIFICA" if r["verifica"] else "✗ NO VERIFICA")
            except (ValueError, ZeroDivisionError):
                pass

        bloque["_recalcular_fn"] = recalcular
        for key in ("PT_MTMA","PT_LONG","PT_W_CM3","PT_MAT"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    # ── Autocalc: Frenos — disco ──────────────────────────────────────────────
    def _bind_frenos_autocalc(self, bloque):
        campos = bloque["campos"]

        def _s(k, v):
            if k in campos: campos[k].set(v)

        def recalcular(*_):
            try:
                MMA    = float(campos.get("FR_MMA",     tk.StringVar()).get() or 0)
                mu     = float(campos.get("FR_MU",      tk.StringVar()).get() or 0)
                asp    = float(campos.get("FR_ASPECTO", tk.StringVar()).get() or 0)
                sec    = float(campos.get("FR_SECCION", tk.StringVar()).get() or 0)
                lla    = float(campos.get("FR_LLANTA",  tk.StringVar()).get() or 0)

                # Radio de llanta
                import math
                if asp > 0 and sec > 0 and lla > 0:
                    R_m = (lla * 25.4 + 2 * asp * sec / 100) / 2 / 1000
                    _s("FR_RLLANTA", f"{R_m:.5f}")

                # Par de frenado
                Dext_d = float(campos.get("FR_DEXT_D",  tk.StringVar()).get() or 0)
                Dint_d = float(campos.get("FR_DINT_D",  tk.StringVar()).get() or 0)
                Lp_d   = float(campos.get("FR_LPAST_D", tk.StringVar()).get() or 0)
                Dext_t = float(campos.get("FR_DEXT_T",  tk.StringVar()).get() or 0)
                Dint_t = float(campos.get("FR_DINT_T",  tk.StringVar()).get() or 0)
                Lp_t   = float(campos.get("FR_LPAST_T", tk.StringVar()).get() or 0)
                Dp_d   = float(campos.get("FR_DPIST_D", tk.StringVar()).get() or 0)
                Dp_t   = float(campos.get("FR_DPIST_T", tk.StringVar()).get() or 0)
                P_MPa  = float(campos.get("FR_P_MPa",   tk.StringVar()).get() or 0)

                if (MMA > 0 and mu > 0 and asp > 0 and sec > 0 and lla > 0
                        and Dext_d > 0 and Dint_d > 0 and Lp_d > 0
                        and Dext_t > 0 and Dint_t > 0 and Lp_t > 0
                        and P_MPa > 0):
                    r = calcular_frenos_disco(
                        MMA, mu, asp, sec, lla,
                        Dext_d, Dint_d, Lp_d,
                        Dext_t, Dint_t, Lp_t,
                        Dp_d, Dp_t, P_MPa)
                    if r:
                        _s("FR_T_DEL",   f"{r['T_del_Nm']:.2f}")
                        _s("FR_T_TRA",   f"{r['T_tra_Nm']:.2f}")
                        _s("FR_T_TOT",   f"{r['T_total_Nm']:.2f}")
                        _s("FR_F_FREN",  f"{r['F_fren_N']:.2f}")
                        _s("FR_EFIC",    f"{r['eficacia_pct']:.2f}")
                        _s("FR_RATIO50", f"{r['ratio_50']:.3f}")
                        _s("FR_RESULT",
                           "✓ VERIFICA (≥50%)" if r["verifica"]
                           else "✗ NO VERIFICA (<50%)")
            except (ValueError, ZeroDivisionError):
                pass

        bloque["_recalcular_fn"] = recalcular
        for key in ("FR_MMA","FR_MU","FR_ASPECTO","FR_SECCION","FR_LLANTA",
                    "FR_DEXT_D","FR_DINT_D","FR_LPAST_D","FR_DEXT_T","FR_DINT_T",
                    "FR_LPAST_T","FR_P_MPa"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    # ── Autocalc: Suspensión neumática — Balonas ──────────────────────────────
    def _bind_suspension_neumatica_autocalc(self, bloque):
        campos = bloque["campos"]

        def _s(k, v):
            if k in campos: campos[k].set(v)

        def recalcular(*_):
            try:
                carga  = float(campos.get("CARGA_TOTAL_KG",      tk.StringVar()).get() or 0)
                n_bal  = float(campos.get("NUM_BALONAS",          tk.StringVar()).get() or 0)
                diam   = float(campos.get("DIAM_BALONA_MM",       tk.StringVar()).get() or 0)
                p_max  = float(campos.get("PRESION_BALONAS_BAR",  tk.StringVar()).get() or 0)
                if carga > 0 and n_bal > 0 and diam > 0 and p_max > 0:
                    r = calcular_suspension_neumatica(carga, n_bal, diam, p_max)
                    if r:
                        _s("SN_CARGA_BALONA", f"{r['carga_balona_kg']:.2f}")
                        _s("SN_AREA_EFECT",   f"{r['area_cm2']:.4f}")
                        _s("SN_FUERZA_N",     f"{r['fuerza_N']:.2f}")
                        _s("SN_P_TRABAJO",    f"{r['p_trabajo_bar']:.4f}")
                        _s("SN_MARGEN",       f"{r['margen_pct']:.1f}")
                        _s("SN_RESULTADO",
                           "✓ VERIFICA" if r["verifica"] else "✗ NO VERIFICA")
            except (ValueError, ZeroDivisionError):
                pass

        bloque["_recalcular_fn"] = recalcular
        for key in ("CARGA_TOTAL_KG", "NUM_BALONAS", "DIAM_BALONA_MM",
                    "PRESION_BALONAS_BAR"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    # ── Autocalc: Suspensión mecánica ───────────────────────────────────────────
    def _bind_suspension_mecanica_autocalc(self, bloque):
        campos = bloque["campos"]

        def _s(k, v):
            if k in campos: campos[k].set(v)

        def recalcular(*_):
            try:
                antes   = float(campos.get("ALTURA_ANTES_MM",   tk.StringVar()).get() or 0)
                despues = float(campos.get("ALTURA_DESPUES_MM", tk.StringVar()).get() or 0)
                if antes > 0 and despues > 0:
                    var = despues - antes
                    pct = (var / antes) * 100
                    _s("SM_VAR_CALC", f"{var:.1f}")
                    _s("SM_PCT_VAR",  f"{pct:.2f}")
            except (ValueError, ZeroDivisionError):
                pass

        bloque["_recalcular_fn"] = recalcular
        for key in ("ALTURA_ANTES_MM", "ALTURA_DESPUES_MM"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    # ── Autocalc: Cambio de motor ───────────────────────────────────────────────
    def _bind_motor_autocalc(self, bloque):
        campos = bloque["campos"]

        def _s(k, v):
            if k in campos: campos[k].set(v)

        def recalcular(*_):
            try:
                pot_orig  = float(campos.get("MOTOR_ORIG_POT_KW",  tk.StringVar()).get() or 0)
                pot_nuevo = float(campos.get("MOTOR_NUEVO_POT_KW", tk.StringVar()).get() or 0)
                par_orig  = float(campos.get("MOTOR_ORIG_PAR_NM",  tk.StringVar()).get() or 0)
                par_nuevo = float(campos.get("MOTOR_NUEVO_PAR_NM", tk.StringVar()).get() or 0)
                tara      = float(campos.get("MOTOR_TARA_KG",      tk.StringVar()).get() or 0)

                if pot_nuevo > 0 and tara > 0:
                    ratio = pot_nuevo / (tara / 1000)
                    _s("RATIO_POT_PESO", f"{ratio:.2f}")

                if pot_orig > 0 and pot_nuevo > 0:
                    inc_pot = ((pot_nuevo - pot_orig) / pot_orig) * 100
                    _s("INCREMENTO_POT_PCT", f"{inc_pot:.2f}")

                if par_orig > 0 and par_nuevo > 0:
                    inc_par = ((par_nuevo - par_orig) / par_orig) * 100
                    _s("INCREMENTO_PAR_PCT", f"{inc_par:.2f}")

                if pot_orig > 0 and pot_nuevo > 0:
                    _s("MOTOR_RESULTADO", "Calculado")
            except (ValueError, ZeroDivisionError):
                pass

        bloque["_recalcular_fn"] = recalcular
        for key in ("MOTOR_ORIG_POT_KW", "MOTOR_NUEVO_POT_KW",
                    "MOTOR_ORIG_PAR_NM", "MOTOR_NUEVO_PAR_NM", "MOTOR_TARA_KG"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    # ── Autocalc: Conversión eléctrica ──────────────────────────────────────────
    def _bind_conversion_electrica_autocalc(self, bloque):
        campos = bloque["campos"]

        def _s(k, v):
            if k in campos: campos[k].set(v)

        def recalcular(*_):
            try:
                pot_kw = float(campos.get("MOTOR_ELEC_POT_KW",     tk.StringVar()).get() or 0)
                cap    = float(campos.get("BATERIA_CAPACIDAD_KWH", tk.StringVar()).get() or 0)
                tara   = float(campos.get("CONV_TARA_KG",          tk.StringVar()).get() or 0)

                if pot_kw > 0 and tara > 0:
                    _s("CONV_RATIO_POT", f"{pot_kw / (tara / 1000):.2f}")
                if cap > 0 and tara > 0:
                    _s("CONV_ENERGIA_PESO", f"{cap * 1000 / tara:.2f}")
            except (ValueError, ZeroDivisionError):
                pass

        bloque["_recalcular_fn"] = recalcular
        for key in ("MOTOR_ELEC_POT_KW", "BATERIA_CAPACIDAD_KWH", "CONV_TARA_KG"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    # ── Autocalc: Enganche ──────────────────────────────────────────────────────
    def _bind_enganche_autocalc(self, bloque):
        campos = bloque["campos"]

        def _s(k, v):
            if k in campos: campos[k].set(v)

        def recalcular(*_):
            try:
                mma_veh  = float(campos.get("ENG_MMA_VEHICULO",   tk.StringVar()).get() or 0)
                remolc   = float(campos.get("MASA_REMOLCABLE_KG", tk.StringVar()).get() or 0)
                mma_conj = float(campos.get("MMA_CONJUNTO_KG",    tk.StringVar()).get() or 0)

                if mma_veh > 0 and remolc > 0:
                    calc = mma_veh + remolc
                    _s("ENG_MMA_CONJ_CALC", f"{calc:.0f}")
                    if mma_conj > 0:
                        ok = calc <= mma_conj
                        _s("ENG_VERIF_CONJ",
                           "✓ VERIFICA" if ok else "✗ SUPERA MMA CONJUNTO")
            except (ValueError, ZeroDivisionError):
                pass

        bloque["_recalcular_fn"] = recalcular
        for key in ("ENG_MMA_VEHICULO", "MASA_REMOLCABLE_KG", "MMA_CONJUNTO_KG"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    # ── Autocalc: Modificación de masas ─────────────────────────────────────────
    def _bind_masas_autocalc(self, bloque):
        campos = bloque["campos"]

        def _s(k, v):
            if k in campos: campos[k].set(v)

        def recalcular(*_):
            try:
                mma_nueva = float(campos.get("MMA_NUEVA_KG",    tk.StringVar()).get() or 0)
                tara      = float(campos.get("TARA_KG",         tk.StringVar()).get() or 0)
                eje1      = float(campos.get("CARGA_EJE1_KG",   tk.StringVar()).get() or 0)
                eje2      = float(campos.get("CARGA_EJE2_KG",   tk.StringVar()).get() or 0)
                eje3      = float(campos.get("CARGA_EJE3_KG",   tk.StringVar()).get() or 0)
                mma_legal = float(campos.get("MMA_MAX_LEGAL_KG",tk.StringVar()).get() or 0)

                suma = eje1 + eje2 + eje3
                _s("MM_SUMA_EJES", f"{suma:.0f}")

                if mma_nueva > 0 and tara > 0:
                    _s("MM_CARGA_UTIL", f"{mma_nueva - tara:.0f}")

                if mma_nueva > 0 and mma_legal > 0:
                    _s("MM_VERIF_MMA",
                       "✓ VERIFICA" if mma_nueva <= mma_legal else "✗ SUPERA MMA LEGAL")

                if suma > 0 and mma_nueva > 0:
                    _s("VERIFICACION_EJES",
                       "✓ VERIFICA" if suma >= mma_nueva else "✗ Suma ejes < MMA")
            except (ValueError, ZeroDivisionError):
                pass

        bloque["_recalcular_fn"] = recalcular
        for key in ("MMA_NUEVA_KG", "TARA_KG", "CARGA_EJE1_KG",
                    "CARGA_EJE2_KG", "CARGA_EJE3_KG", "MMA_MAX_LEGAL_KG"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    # ── Autocalc: Modificación de carrocería ────────────────────────────────────
    def _bind_carroceria_autocalc(self, bloque):
        campos = bloque["campos"]

        def _s(k, v):
            if k in campos: campos[k].set(v)

        def recalcular(*_):
            pares = [
                ("LONG_ANTES_MM",           "LONG_DESPUES_MM",          "CAR_VAR_LONG"),
                ("ANCHO_ANTES_MM",          "ANCHO_DESPUES_MM",         "CAR_VAR_ANCHO"),
                ("ALTO_ANTES_MM",           "ALTO_DESPUES_MM",          "CAR_VAR_ALTO"),
                ("VOLADIZO_DEL_ANTES_MM",   "VOLADIZO_DEL_DESP_MM",    "CAR_VAR_VOL_DEL"),
                ("VOLADIZO_TRA_ANTES_MM",   "VOLADIZO_TRA_DESP_MM",    "CAR_VAR_VOL_TRA"),
            ]
            for antes_k, desp_k, res_k in pares:
                try:
                    a = float(campos.get(antes_k, tk.StringVar()).get() or 0)
                    d = float(campos.get(desp_k,  tk.StringVar()).get() or 0)
                    if a > 0 and d > 0:
                        _s(res_k, f"{d - a:.0f}")
                except (ValueError, ZeroDivisionError):
                    pass

        bloque["_recalcular_fn"] = recalcular
        for key in ("LONG_ANTES_MM", "LONG_DESPUES_MM",
                    "ANCHO_ANTES_MM", "ANCHO_DESPUES_MM",
                    "ALTO_ANTES_MM", "ALTO_DESPUES_MM",
                    "VOLADIZO_DEL_ANTES_MM", "VOLADIZO_DEL_DESP_MM",
                    "VOLADIZO_TRA_ANTES_MM", "VOLADIZO_TRA_DESP_MM"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    # ── Autocalc: Modificación del sistema de frenos ────────────────────────────
    def _bind_frenos_mod_autocalc(self, bloque):
        campos = bloque["campos"]

        def _s(k, v):
            if k in campos: campos[k].set(v)

        def recalcular(*_):
            try:
                antes   = float(campos.get("DIST_FRENADA_ANTES", tk.StringVar()).get() or 0)
                despues = float(campos.get("DIST_FRENADA_DESP",  tk.StringVar()).get() or 0)
                if antes > 0 and despues > 0:
                    mejora = ((antes - despues) / antes) * 100
                    _s("FRMOD_MEJORA_PCT", f"{mejora:.2f}")
                    _s("FRMOD_RESULTADO",
                       "✓ VERIFICA" if despues <= antes else "✗ EMPEORA")
            except (ValueError, ZeroDivisionError):
                pass

        bloque["_recalcular_fn"] = recalcular
        for key in ("DIST_FRENADA_ANTES", "DIST_FRENADA_DESP"):
            if key in campos:
                campos[key].trace_add("write", recalcular)

    def _del_calc_bloque(self, bloque_frame):
        """Elimina un bloque de cálculo."""
        self._calc_bloques = [b for b in self._calc_bloques
                               if b["frame"] is not bloque_frame]
        bloque_frame.destroy()
        # Renumerar cabeceras
        for i, bloque in enumerate(self._calc_bloques):
            for widget in bloque["frame"].winfo_children():
                if isinstance(widget, tk.Frame):  # es el hdr
                    for child in widget.winfo_children():
                        if isinstance(child, tk.Label) and child.cget("text").startswith("  Cálculo"):
                            child.config(text=f"  Cálculo {i + 1}")
                            break
                    break

    def _trigger_calcular(self, bloque):
        """Fuerza el recálculo manual del bloque."""
        tipo = bloque["tipo_var"].get()
        if tipo == "— Sin cálculo —":
            messagebox.showinfo("Info", "Selecciona un tipo de cálculo primero.")
            return
        fn = bloque.get("_recalcular_fn")
        if fn:
            fn()
        else:
            messagebox.showinfo("Info",
                                "Este tipo de cálculo no tiene fórmulas automáticas.")

    def _actualizar_combos_reforma(self):
        """Sincroniza los combos 'Reforma asociada' con los actos reglamentarios."""
        if not hasattr(self, "_calc_bloques"):
            return
        opciones = ["— General —"]
        for fila in self._reforma_rows:
            cod  = fila["codigo_var"].get().strip()
            desc = fila["desc_var"].get().strip()
            if cod:
                etiqueta = f"CR {cod}"
                if desc:
                    etiqueta += f" — {desc[:50]}"
                opciones.append(etiqueta)

        for bloque in self._calc_bloques:
            cb = bloque["cb_reforma"]
            actual = bloque["reforma_var"].get()
            cb["values"] = opciones
            if actual not in opciones:
                bloque["reforma_var"].set("— General —")

    def _recoger_calculos(self):
        """Recoge todos los bloques de cálculo como lista de dicts."""
        resultado = []
        for bloque in self._calc_bloques:
            tipo = bloque["tipo_var"].get()
            if tipo == "— Sin cálculo —":
                continue
            campos_vals = {k: v.get().strip() for k, v in bloque["campos"].items()}
            resultado.append({
                "reforma_ref": bloque["reforma_var"].get(),
                "tipo":        tipo,
                "campos":      campos_vals,
            })
        return resultado

    # ── Helper: crea una pestaña con canvas scrollable ────────────────────────
    def _nueva_pestana(self, titulo):
        tab = tk.Frame(self.nb, bg=GRIS_BG)
        self.nb.add(tab, text=titulo)

        outer = tk.Frame(tab, bg=GRIS_BG)
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, bg=GRIS_BG, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=GRIS_BG)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        inner.bind("<Configure>",
            lambda e, cv=canvas: cv.configure(scrollregion=cv.bbox("all")))
        canvas.bind("<Configure>",
            lambda e, cv=canvas, wid=win_id: cv.itemconfig(wid, width=e.width))

        # Scroll solo cuando el ratón está sobre este canvas (no bind_all global)
        def _on_enter(e, cv=canvas):
            cv.bind_all("<MouseWheel>",
                lambda ev, c=cv: c.yview_scroll(int(-1*(ev.delta/120)), "units"))
        def _on_leave(e, cv=canvas):
            cv.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", _on_enter)
        canvas.bind("<Leave>", _on_leave)

        return inner, canvas

    # ── Helper: sección genérica de campos de texto ───────────────────────────
    def _seccion(self, parent, titulo, campos):
        frm = tk.LabelFrame(
            parent, text=f"  {titulo}  ",
            bg=BLANCO, fg=AZUL,
            font=("Segoe UI", 10, "bold"),
            relief="solid", bd=1, padx=14, pady=8
        )
        frm.pack(fill="x", padx=4, pady=(6, 2))

        for clave, etiqueta, placeholder in campos:
            row = tk.Frame(frm, bg=BLANCO)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=etiqueta + ":",
                     bg=BLANCO, fg="#333", font=("Segoe UI", 9),
                     width=26, anchor="e"
                     ).pack(side="left", padx=(0, 8))
            var = tk.StringVar(value=placeholder)
            ttk.Entry(row, textvariable=var, font=("Segoe UI", 9), width=52
                      ).pack(side="left", fill="x", expand=True)
            self.entries[clave] = var

    # ── Sección dinámica de actos reglamentarios ──────────────────────────────
    def _seccion_reformas(self, parent):
        self._frm_reformas = tk.LabelFrame(
            parent,
            text="  Actos reglamentarios (reformas)  ",
            bg=BLANCO, fg=AZUL,
            font=("Segoe UI", 10, "bold"),
            relief="solid", bd=1, padx=14, pady=8
        )
        self._frm_reformas.pack(fill="x", padx=4, pady=(6, 2))

        self._filas_container = tk.Frame(self._frm_reformas, bg=BLANCO)
        self._filas_container.pack(fill="x")

        tk.Button(
            self._frm_reformas,
            text="  +  Añadir acto reglamentario",
            bg="#e8f5e9", fg=VERDE,
            font=("Segoe UI", 9, "bold"),
            relief="flat", padx=10, pady=5, cursor="hand2",
            command=self._add_reforma
        ).pack(anchor="w", pady=(8, 2))

        self._add_reforma()

    # ── Tarjeta de un código de reforma ──────────────────────────────────────
    def _add_reforma(self):
        """
        Crea una tarjeta para un código de reforma (p.ej. 4.1).
        Dentro de la tarjeta se pueden añadir una o varias reformas específicas.
        """
        idx = len(self._reforma_rows)

        # Tarjeta contenedora
        container = tk.Frame(self._filas_container, bg=BLANCO,
                             relief="solid", bd=1)
        container.pack(fill="x", pady=(0, 8))

        # ── Cabecera: código + grupo + descripción oficial ────────────────────
        hdr = tk.Frame(container, bg=AZUL_L)
        hdr.pack(fill="x")

        lbl_num = tk.Label(hdr, text=f"  {idx + 1}.", bg=AZUL_L, fg=AZUL,
                           font=("Segoe UI", 9, "bold"), width=4)
        lbl_num.pack(side="left", pady=5)

        cat_actual = getattr(self, "_cat_codigo_var", tk.StringVar()).get()
        codigos_lista = _codigos_para_categoria(cat_actual)

        codigo_var = tk.StringVar()
        cb = ttk.Combobox(hdr, textvariable=codigo_var, values=codigos_lista,
                          width=9, font=("Segoe UI", 9, "bold"), state="normal")
        cb.pack(side="left", padx=(0, 4), pady=5)

        grupo_var = tk.StringVar()
        ttk.Entry(hdr, textvariable=grupo_var, width=4,
                  font=("Segoe UI", 9), state="readonly"
                  ).pack(side="left", padx=2, pady=5)

        desc_var = tk.StringVar()
        ttk.Entry(hdr, textvariable=desc_var, font=("Segoe UI", 9)
                  ).pack(side="left", fill="x", expand=True, padx=4, pady=5)

        tk.Button(hdr, text=" X ", bg="#ffebee", fg=ROJO,
                  font=("Segoe UI", 8, "bold"), relief="flat",
                  padx=4, pady=2, cursor="hand2",
                  command=lambda c=container: self._del_reforma(c)
                  ).pack(side="right", padx=(2, 6), pady=5)

        # ── Tabla de directivas aplicables (se muestra al seleccionar código) ───
        dir_frame = tk.Frame(container, bg="#f0f4ff")
        # Se mostrará/ocultará por _actualizar_directivas_card; no se hace pack aquí

        # ── Contenedor de items de reforma ────────────────────────────────────
        items_frame = tk.Frame(container, bg=BLANCO)
        items_frame.pack(fill="x", padx=8, pady=(4, 0))

        fila_ref = {
            "container":       container,
            "lbl_num":         lbl_num,
            "cb_codigo":       cb,
            "codigo_var":      codigo_var,
            "grupo_var":       grupo_var,
            "desc_var":        desc_var,
            "dir_frame":       dir_frame,
            "items_frame":     items_frame,
            "reforma_items":   [],
        }
        self._reforma_rows.append(fila_ref)

        # Botón añadir reforma dentro de esta tarjeta
        tk.Button(container, text="  +  Añadir reforma",
                  bg="#f3e5f5", fg="#6a1b9a",
                  font=("Segoe UI", 8), relief="flat", padx=8, pady=3,
                  cursor="hand2",
                  command=lambda f=fila_ref: self._add_reforma_item(f)
                  ).pack(anchor="w", padx=8, pady=(2, 6))

        # Auto-rellenar grupo, descripción y directivas al elegir código
        def on_codigo_change(*_):
            cod = codigo_var.get().strip()
            if cod in CODIGOS_REFORMA_V7:
                grp, desc, _cats = CODIGOS_REFORMA_V7[cod]
                grupo_var.set(grp)
                desc_var.set(desc)
            elif cod:
                grupo_var.set("")
            self._actualizar_directivas_card(fila_ref)
            self._actualizar_combos_reforma()

        codigo_var.trace_add("write", on_codigo_change)

        # Un item de reforma por defecto
        self._add_reforma_item(fila_ref)

    # ── Item de reforma dentro de una tarjeta ─────────────────────────────────
    def _add_reforma_item(self, fila_ref):
        """Añade un item de reforma (título + descripción + estados) a la tarjeta."""
        items_frame = fila_ref["items_frame"]
        idx = len(fila_ref["reforma_items"])
        bg_item = "#fafafa" if idx % 2 == 0 else BLANCO

        item_frame = tk.Frame(items_frame, bg=bg_item, relief="solid", bd=1)
        item_frame.pack(fill="x", pady=(0, 4))

        # ── Fila compacta: índice + título + toggle + eliminar ────────────────
        top_row = tk.Frame(item_frame, bg=bg_item)
        top_row.pack(fill="x", padx=6, pady=(4, 2))

        lbl_idx = tk.Label(top_row, text=f"Reforma {idx + 1}:",
                           bg=bg_item, fg="#6a1b9a",
                           font=("Segoe UI", 8, "bold"), width=10, anchor="w")
        lbl_idx.pack(side="left")

        titulo_var = tk.StringVar()
        ttk.Entry(top_row, textvariable=titulo_var, font=("Segoe UI", 9)
                  ).pack(side="left", fill="x", expand=True, padx=(4, 4))

        _open = [False]
        detail_holder = [None]

        item = {
            "item_frame":  item_frame,
            "lbl_idx":     lbl_idx,
            "titulo_var":  titulo_var,
            "desc_text":   None,
            "prev_text":   None,
            "post_text":   None,
        }
        fila_ref["reforma_items"].append(item)

        def toggle_item():
            _open[0] = not _open[0]
            if detail_holder[0] is None:
                detail_holder[0] = self._crear_detalle_item(item_frame, item, bg_item)
            if _open[0]:
                detail_holder[0].pack(fill="x", padx=6, pady=(0, 6))
                btn_tog.config(text="▼ Detalle")
            else:
                detail_holder[0].pack_forget()
                btn_tog.config(text="▶ Detalle")

        btn_tog = tk.Button(top_row, text="▶ Detalle",
                            bg="#ede7f6", fg="#6a1b9a",
                            font=("Segoe UI", 8), relief="flat",
                            padx=6, pady=2, cursor="hand2",
                            command=toggle_item)
        btn_tog.pack(side="left", padx=2)

        btn_del = tk.Button(top_row, text=" − ",
                            bg="#ffebee", fg=ROJO,
                            font=("Segoe UI", 8), relief="flat",
                            padx=4, pady=2, cursor="hand2",
                            command=lambda f=fila_ref, it=item: self._del_reforma_item(f, it))
        btn_del.pack(side="left", padx=(2, 0))
        item["btn_del"] = btn_del

        self._actualizar_btn_del_item(fila_ref)

    def _crear_detalle_item(self, parent, item, bg):
        """Crea el panel expandible de un item de reforma (descripción + cálculo)."""
        frm = tk.Frame(parent, bg=bg)

        def _lbl(text):
            tk.Label(frm, text=text, bg=bg, fg="#444",
                     font=("Segoe UI", 8, "bold"), anchor="w"
                     ).pack(anchor="w", pady=(4, 0))

        def _txt(height=3):
            t = tk.Text(frm, height=height, font=("Segoe UI", 9),
                        wrap="word", bg=BLANCO, relief="solid", bd=1)
            t.pack(fill="x", pady=(2, 0))
            return t

        _lbl("Descripción del trabajo a realizar:")
        item["desc_text"] = _txt(4)

        _lbl("Estado previo — antes de la reforma:")
        item["prev_text"] = _txt(3)

        # ── Cálculo justificativo ─────────────────────────────────────────────
        ttk.Separator(frm, orient="horizontal").pack(fill="x", pady=(10, 4))
        tk.Label(frm, text="Cálculo justificativo", bg=bg, fg=AZUL,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 4))

        tipo_row = tk.Frame(frm, bg=bg)
        tipo_row.pack(fill="x", pady=(0, 4))
        tk.Label(tipo_row, text="Tipo:", bg=bg, fg="#444",
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 6))

        tipo_calc_var = tk.StringVar(value="— Sin cálculo —")
        ttk.Combobox(tipo_row, textvariable=tipo_calc_var,
                     values=list(CALC_TIPOS.keys()),
                     width=44, font=("Segoe UI", 9),
                     state="readonly").pack(side="left")

        calc_body = tk.Frame(frm, bg=bg)
        calc_body.pack(fill="x", pady=(4, 0))

        item["tipo_calc_var"] = tipo_calc_var
        item["calc_body"]     = calc_body
        item["calc_campos"]   = {}

        def rebuild_calc(*_):
            for w in calc_body.winfo_children():
                w.destroy()
            item["calc_campos"] = {}
            bind_torn = self._render_calc_campos(
                calc_body, item["calc_campos"], bg, tipo_calc_var.get())
            if bind_torn:
                self._bind_tornillo_autocalc({"campos": item["calc_campos"]})

        tipo_calc_var.trace_add("write", rebuild_calc)

        # ── Estado posterior (después del cálculo) ────────────────────────────
        ttk.Separator(frm, orient="horizontal").pack(fill="x", pady=(10, 4))
        _lbl("Estado posterior — tras la reforma (incluyendo tipo de fijación):")
        item["post_text"] = _txt(3)

        return frm

    def _del_reforma_item(self, fila_ref, item):
        """Elimina un item de reforma. Debe quedar al menos uno."""
        if len(fila_ref["reforma_items"]) <= 1:
            return
        fila_ref["reforma_items"] = [it for it in fila_ref["reforma_items"]
                                      if it is not item]
        item["item_frame"].destroy()
        # Renumerar
        for i, it in enumerate(fila_ref["reforma_items"]):
            it["lbl_idx"].config(text=f"Reforma {i + 1}:")
        self._actualizar_btn_del_item(fila_ref)

    def _actualizar_btn_del_item(self, fila_ref):
        """Oculta el botón − cuando solo hay un item."""
        solo_uno = len(fila_ref["reforma_items"]) <= 1
        for it in fila_ref["reforma_items"]:
            btn = it.get("btn_del")
            if btn:
                if solo_uno:
                    btn.pack_forget()
                else:
                    btn.pack(side="left", padx=(2, 0))

    def _del_reforma(self, container):
        if len(self._reforma_rows) <= 1:
            messagebox.showinfo("Aviso", "Debe haber al menos un acto reglamentario.")
            return
        self._reforma_rows = [r for r in self._reforma_rows
                               if r["container"] is not container]
        container.destroy()
        for i, fila in enumerate(self._reforma_rows):
            fila["lbl_num"].config(text=f"  {i + 1}.")
        self._actualizar_combos_reforma()

    def _recoger_reformas(self):
        resultado = []
        for fila in self._reforma_rows:
            cod  = fila["codigo_var"].get().strip()
            grp  = fila["grupo_var"].get().strip()
            desc = fila["desc_var"].get().strip()
            if not (cod or desc):
                continue

            items = []
            for it in fila.get("reforma_items", []):
                titulo     = it["titulo_var"].get().strip()
                desc_libre = it["desc_text"].get("1.0", "end").strip() \
                             if it["desc_text"] else ""
                prev       = it["prev_text"].get("1.0", "end").strip() \
                             if it["prev_text"] else ""
                post       = it["post_text"].get("1.0", "end").strip() \
                             if it["post_text"] else ""

                calculo = None
                tipo_v  = it.get("tipo_calc_var")
                if tipo_v:
                    tipo_str = tipo_v.get()
                    if tipo_str and tipo_str != "— Sin cálculo —":
                        calculo = {
                            "tipo":   tipo_str,
                            "campos": {
                                k: v.get().strip()
                                for k, v in it.get("calc_campos", {}).items()
                                if not k.startswith("_SEP_")
                            },
                        }

                items.append({
                    "titulo":              titulo,
                    "descripcion_trabajo": desc_libre,
                    "estado_previo":       prev,
                    "estado_posterior":    post,
                    "calculo":             calculo,
                })

            resultado.append({
                "codigo":      cod,
                "grupo":       grp,
                "descripcion": desc,
                "reformas":    items,
            })
        return resultado

    # ── Helper: recopila directivas aplicables por código de reforma ─────────
    def _recoger_directivas_doc(self):
        """
        Para cada código de reforma seleccionado, devuelve la lista de directivas
        aplicables filtradas por la categoría del vehículo activa.
        """
        _CATS = ["M1", "M2", "M3", "N1", "N2", "N3", "O1", "O2", "O3", "O4"]
        cat = self._cat_codigo_var.get() if hasattr(self, "_cat_codigo_var") else ""
        cat_idx = _CATS.index(cat) if cat in _CATS else 0

        seen, resultado = set(), []
        for fila in getattr(self, "_reforma_rows", []):
            cod = fila.get("codigo_var", tk.StringVar()).get().strip()
            if not cod or cod in seen:
                continue
            seen.add(cod)
            directivas_raw = DIRECTIVAS_POR_CODIGO.get(cod, [])
            filas = [
                {"sistema": s, "referencia": r, "valor": vals[cat_idx]}
                for s, r, vals in directivas_raw
                if vals[cat_idx] not in ("(x)", "(-)", "-")
            ]
            if filas:
                grp, desc, _ = CODIGOS_REFORMA_V7.get(cod, ("", cod, []))
                resultado.append({
                    "codigo":      cod,
                    "descripcion": desc,
                    "directivas":  filas,
                })
        return resultado

    # ── Acción generar ────────────────────────────────────────────────────────
    def _generar(self):
        datos = {k: v.get().strip() for k, v in self.entries.items()}
        datos["REFORMAS"]        = self._recoger_reformas()
        datos["CALCULOS"]        = self._recoger_calculos()
        datos["DIRECTIVAS_DOC"]  = self._recoger_directivas_doc()

        json_tmp = BASE_DIR / "_datos_tmp.json"
        with open(json_tmp, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)

        self.btn.config(state="disabled", text="  ...  Generando  ")
        self.estado_var.set("Procesando, por favor espera...")
        self.update()

        threading.Thread(target=self._ejecutar, args=(json_tmp,), daemon=True).start()

    def _env_con_ruta(self):
        """Devuelve el entorno con PHICAN_OUTPUT_DIR y rutas de plantillas configuradas."""
        env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
        out = getattr(self, "_output_path_var", None)
        ruta = out.get().strip() if out else ""
        if ruta:
            env["PHICAN_OUTPUT_DIR"] = ruta
        for clave, var in getattr(self, "_template_vars", {}).items():
            val = var.get().strip()
            if val:
                env[f"PHICAN_{clave}"] = val
        return env

    def _ejecutar(self, json_tmp):
        try:
            env_utf8 = self._env_con_ruta()
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PY), str(json_tmp)],
                capture_output=True, text=True, encoding="utf-8", env=env_utf8
            )
            if result.returncode == 0:
                ruta = None
                for line in result.stdout.splitlines():
                    if line.strip().endswith(".docx"):
                        ruta = line.strip()
                        break
                self.after(0, lambda: self._exito(ruta))
            else:
                error = result.stderr or result.stdout
                self.after(0, lambda: self._error(error))
        except Exception as e:
            self.after(0, lambda: self._error(str(e)))
        finally:
            try:
                os.remove(json_tmp)
            except Exception:
                pass

    def _exito(self, ruta):
        self.btn.config(state="normal", text="  >  GENERAR PROYECTO  ")
        self.estado_var.set("[OK]  Proyecto generado correctamente")
        self.lbl_estado.config(fg=VERDE)
        self.entries["REFERENCIA"].set(siguiente_referencia())

        if ruta and Path(ruta).exists():
            resp = messagebox.askyesno(
                "Proyecto generado",
                f"El proyecto se ha generado correctamente:\n\n{ruta}\n\n"
                "Abrir la carpeta de destino?"
            )
            if resp:
                carpeta = str(Path(ruta).parent)
                if sys.platform == "win32":
                    os.startfile(carpeta)
                else:
                    subprocess.Popen(["xdg-open", carpeta])
        else:
            messagebox.showinfo("Listo", "El proyecto se ha generado correctamente.")

    def _error(self, mensaje):
        self.btn.config(state="normal", text="  >  GENERAR PROYECTO  ")
        self.estado_var.set("[ERROR]  Error al generar")
        self.lbl_estado.config(fg="red")
        messagebox.showerror("Error", f"No se pudo generar el proyecto:\n\n{mensaje}")

    # ── Generación de Anexo Justificativo ────────────────────────────────────
    def _generar_anexo(self):
        """Recoge los datos y lanza generar_anexo.py para producir el Word de anexos."""
        calculos = self._recoger_calculos()

        datos = {k: v.get().strip() for k, v in self.entries.items()}
        datos["REFORMAS"]       = self._recoger_reformas()
        datos["CALCULOS"]       = calculos
        datos["DIRECTIVAS_DOC"] = self._recoger_directivas_doc()

        json_tmp = BASE_DIR / "_datos_anexo_tmp.json"
        with open(json_tmp, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)

        self.btn_anexo.config(state="disabled", text="  ...  Generando anexo  ")
        self.estado_var.set("Generando anexo justificativo...")
        self.update()

        threading.Thread(
            target=self._ejecutar_anexo, args=(json_tmp,), daemon=True
        ).start()

    def _ejecutar_anexo(self, json_tmp):
        """Ejecuta generar_anexo.py en subproceso."""
        script_anexo = BASE_DIR / "generar_anexo.py"
        try:
            env_utf8 = self._env_con_ruta()
            result = subprocess.run(
                [sys.executable, str(script_anexo), str(json_tmp)],
                capture_output=True, text=True, encoding="utf-8", env=env_utf8
            )
            if result.returncode == 0:
                ruta = None
                for line in result.stdout.splitlines():
                    if line.strip().endswith(".docx"):
                        ruta = line.strip()
                        break
                self.after(0, lambda: self._exito_anexo(ruta))
            else:
                error = result.stderr or result.stdout
                self.after(0, lambda: self._error_anexo(error))
        except Exception as e:
            self.after(0, lambda: self._error_anexo(str(e)))
        finally:
            try:
                os.remove(json_tmp)
            except Exception:
                pass

    def _exito_anexo(self, ruta):
        self.btn_anexo.config(state="normal", text="  ≡  GENERAR ANEXO  ")
        self.estado_var.set("[OK]  Anexo justificativo generado")
        self.lbl_estado.config(fg="#1976D2")

        if ruta and Path(ruta).exists():
            resp = messagebox.askyesno(
                "Anexo generado",
                f"Anexo justificativo generado:\n\n{ruta}\n\n"
                "¿Abrir la carpeta de destino?"
            )
            if resp:
                carpeta = str(Path(ruta).parent)
                if sys.platform == "win32":
                    os.startfile(carpeta)
                else:
                    subprocess.Popen(["xdg-open", carpeta])
        else:
            messagebox.showinfo("Listo", "El anexo se ha generado correctamente.")

    def _error_anexo(self, mensaje):
        self.btn_anexo.config(state="normal", text="  ≡  GENERAR ANEXO  ")
        self.estado_var.set("[ERROR]  Error al generar anexo")
        self.lbl_estado.config(fg="red")
        messagebox.showerror("Error", f"No se pudo generar el anexo:\n\n{mensaje}")

    # ── Generación de Certificado Final de Obra (CFO) ────────────────────────
    def _generar_cfo(self):
        datos = {k: v.get().strip() for k, v in self.entries.items()}
        datos["REFORMAS"]       = self._recoger_reformas()
        datos["CALCULOS"]       = self._recoger_calculos()
        datos["DIRECTIVAS_DOC"] = self._recoger_directivas_doc()
        datos["FOTOS_CFO"]      = self._recoger_fotos_cfo()

        json_tmp = BASE_DIR / "_datos_cfo_tmp.json"
        with open(json_tmp, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)

        self.btn_cfo.config(state="disabled", text="  ...  Generando CFO  ")
        self.estado_var.set("Generando CFO...")
        self.update()
        threading.Thread(target=self._ejecutar_cfo, args=(json_tmp,), daemon=True).start()

    def _ejecutar_cfo(self, json_tmp):
        try:
            env_utf8 = self._env_con_ruta()
            result = subprocess.run(
                [sys.executable, str(SCRIPT_CFO), str(json_tmp)],
                capture_output=True, text=True, encoding="utf-8", env=env_utf8
            )
            if result.returncode == 0:
                ruta = next(
                    (l.strip() for l in result.stdout.splitlines() if l.strip().endswith(".docx")),
                    None
                )
                self.after(0, lambda: self._exito_cfo(ruta))
            else:
                self.after(0, lambda: self._error_cert("CFO", result.stderr or result.stdout))
        except Exception as e:
            self.after(0, lambda: self._error_cert("CFO", str(e)))
        finally:
            try:
                os.remove(json_tmp)
            except Exception:
                pass

    def _exito_cfo(self, ruta):
        self.btn_cfo.config(state="normal", text="  CFO  ")
        self.estado_var.set("[OK]  CFO generado")
        self.lbl_estado.config(fg="#00695c")
        self._abrir_carpeta_docx(ruta, "CFO generado")

    # ── Generación de Certificado de Taller (CT) ──────────────────────────────
    def _generar_ct(self):
        datos = {k: v.get().strip() for k, v in self.entries.items()}
        datos["REFORMAS"]       = self._recoger_reformas()
        datos["CALCULOS"]       = self._recoger_calculos()
        datos["DIRECTIVAS_DOC"] = self._recoger_directivas_doc()

        json_tmp = BASE_DIR / "_datos_ct_tmp.json"
        with open(json_tmp, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)

        self.btn_ct.config(state="disabled", text="  ...  Generando CT  ")
        self.estado_var.set("Generando CT...")
        self.update()
        threading.Thread(target=self._ejecutar_ct, args=(json_tmp,), daemon=True).start()

    def _ejecutar_ct(self, json_tmp):
        try:
            env_utf8 = self._env_con_ruta()
            result = subprocess.run(
                [sys.executable, str(SCRIPT_CT), str(json_tmp)],
                capture_output=True, text=True, encoding="utf-8", env=env_utf8
            )
            if result.returncode == 0:
                ruta = next(
                    (l.strip() for l in result.stdout.splitlines() if l.strip().endswith(".docx")),
                    None
                )
                self.after(0, lambda: self._exito_ct(ruta))
            else:
                self.after(0, lambda: self._error_cert("CT", result.stderr or result.stdout))
        except Exception as e:
            self.after(0, lambda: self._error_cert("CT", str(e)))
        finally:
            try:
                os.remove(json_tmp)
            except Exception:
                pass

    def _exito_ct(self, ruta):
        self.btn_ct.config(state="normal", text="  CT  ")
        self.estado_var.set("[OK]  CT generado")
        self.lbl_estado.config(fg="#6a1b9a")
        self._abrir_carpeta_docx(ruta, "CT generado")

    # ── Helpers compartidos ────────────────────────────────────────────────────
    def _abrir_carpeta_docx(self, ruta, titulo):
        if ruta and Path(ruta).exists():
            resp = messagebox.askyesno(
                titulo,
                f"Documento generado:\n\n{ruta}\n\n¿Abrir la carpeta de destino?"
            )
            if resp:
                carpeta = str(Path(ruta).parent)
                if sys.platform == "win32":
                    os.startfile(carpeta)
                else:
                    subprocess.Popen(["xdg-open", carpeta])
        else:
            messagebox.showinfo("Listo", "Documento generado correctamente.")

    def _error_cert(self, tipo, mensaje):
        if tipo == "CFO":
            self.btn_cfo.config(state="normal", text="  CFO  ")
        else:
            self.btn_ct.config(state="normal", text="  CT  ")
        self.estado_var.set(f"[ERROR]  Error al generar {tipo}")
        self.lbl_estado.config(fg="red")
        messagebox.showerror("Error", f"No se pudo generar el {tipo}:\n\n{mensaje}")

    def _centrar_ventana(self, w, h):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")


if __name__ == "__main__":
    app = FormularioProyecto()
    app.mainloop()
