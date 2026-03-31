"""
Generador de plantilla PDF para planos técnicos de vehículos.
Formato: PROYECTO DE REFORMA DE VEHÍCULO - PHICAN INGENIEROS

Genera PDFs A4 con:
- Zona de dibujo superior (para insertar vistas del vehículo)
- Cajetín inferior con campos técnicos
- Barra de empresa en el pie
- Numeración de planos

Uso:
    python plano_vehiculo_template.py
    python plano_vehiculo_template.py --output mi_plano.pdf --config datos.json
"""

import json
import os
import sys
from datetime import datetime

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import Color, black, white, HexColor
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# =============================================================================
# CONFIGURACIÓN POR DEFECTO
# =============================================================================

DEFAULT_CONFIG = {
    "empresa": {
        "nombre": "PHICAN INGENIEROS",
        "subtitulo": "ESTUDIO DE INGENIERÍA",
        "direccion": "C/ RAMBLA DOCTOR PÉREZ, 5 - LOCAL 22 - 38390 SANTA URSULA (SANTA CRUZ DE TENERIFE)",
        "logo_path": ""  # Ruta al logo PNG/JPG (opcional)
    },
    "proyecto": {
        "titulo": "PROYECTO DE REFORMA DE VEHÍCULO",
        "vehiculo": "",
        "matricula": "",
        "expediente": "",
        "fecha": "",
        "escala": "A4 - S/E",
        "unidades": "Medidas en mm."
    },
    "personas": {
        "dibujado": "",
        "peticionario": "",
        "ingeniero": "",
        "colegiado": "",
        "firma_path": ""  # Ruta a imagen de firma (opcional)
    },
    "planos": [
        {"contenido": "Antes de la Reforma", "imagen_path": ""},
        {"contenido": "Después de la Reforma", "imagen_path": "", "extras": {}},
    ]
}

# =============================================================================
# COLORES
# =============================================================================

COLOR_BARRA_FONDO = HexColor("#2D2D2D")    # Gris oscuro barra inferior
COLOR_BARRA_TEXTO = HexColor("#CCCCCC")    # Texto gris claro en barra
COLOR_TRIANGULO = HexColor("#333333")       # Triángulo decorativo
COLOR_LINEA = black
COLOR_TEXTO = black
COLOR_GRIS_LABEL = HexColor("#666666")     # Labels pequeños


# =============================================================================
# CLASE PRINCIPAL
# =============================================================================

class PlanoVehiculoTemplate:
    """Genera PDFs de planos técnicos de vehículos con cajetín normalizado."""

    def __init__(self, config=None):
        self.config = config or DEFAULT_CONFIG
        self.page_width, self.page_height = A4  # 210 x 297 mm en portrait
        # Márgenes
        self.margin = 10 * mm
        # Altura del cajetín (zona inferior)
        self.cajetin_height = 72 * mm
        # Altura de la barra de empresa
        self.barra_height = 12 * mm
        # Zona de dibujo disponible
        self.dibujo_top = self.page_height - self.margin
        self.dibujo_bottom = self.margin + self.cajetin_height + 5 * mm

    def generar(self, output_path="plano_vehiculo.pdf"):
        """Genera el PDF completo con todos los planos definidos."""
        c = canvas.Canvas(output_path, pagesize=A4)
        c.setTitle(self.config["proyecto"]["titulo"])
        c.setAuthor(self.config["personas"].get("ingeniero", ""))

        planos = self.config.get("planos", [])
        if not planos:
            planos = [{"contenido": "Sin contenido"}]

        for i, plano in enumerate(planos):
            num_plano = i + 1
            self._dibujar_pagina(c, plano, num_plano, len(planos))
            if i < len(planos) - 1:
                c.showPage()

        c.save()
        print(f"PDF generado: {os.path.abspath(output_path)}")
        return output_path

    def _dibujar_pagina(self, c, plano, num_plano, total_planos):
        """Dibuja una página completa del plano."""
        # 1. Marco exterior
        self._dibujar_marco(c)

        # 2. Zona de dibujo (placeholder o imagen)
        self._dibujar_zona_dibujo(c, plano)

        # 3. Cajetín inferior
        self._dibujar_cajetin(c, plano, num_plano)

        # 4. Barra de empresa
        self._dibujar_barra_empresa(c)

    # -------------------------------------------------------------------------
    # MARCO
    # -------------------------------------------------------------------------
    def _dibujar_marco(self, c):
        """Dibuja el marco rectangular exterior del plano."""
        c.setStrokeColor(COLOR_LINEA)
        c.setLineWidth(0.8)
        x0 = self.margin
        y0 = self.margin
        w = self.page_width - 2 * self.margin
        h = self.page_height - 2 * self.margin
        c.rect(x0, y0, w, h)

    # -------------------------------------------------------------------------
    # ZONA DE DIBUJO
    # -------------------------------------------------------------------------
    def _dibujar_zona_dibujo(self, c, plano):
        """Dibuja la zona de dibujo superior con imagen o placeholder."""
        x0 = self.margin + 2 * mm
        y0 = self.dibujo_bottom
        w = self.page_width - 2 * self.margin - 4 * mm
        h = self.dibujo_top - self.dibujo_bottom - 2 * mm

        imagen = plano.get("imagen_path", "")
        if imagen and os.path.exists(imagen):
            # Insertar imagen centrada manteniendo proporción
            try:
                from reportlab.lib.utils import ImageReader
                img = ImageReader(imagen)
                img_w, img_h = img.getSize()
                ratio = min(w / img_w, h / img_h)
                draw_w = img_w * ratio
                draw_h = img_h * ratio
                draw_x = x0 + (w - draw_w) / 2
                draw_y = y0 + (h - draw_h) / 2
                c.drawImage(imagen, draw_x, draw_y, draw_w, draw_h,
                            preserveAspectRatio=True, mask='auto')
            except Exception as e:
                self._dibujar_placeholder(c, x0, y0, w, h, str(e))
        else:
            self._dibujar_placeholder(c, x0, y0, w, h, plano.get("contenido", ""))

    def _dibujar_placeholder(self, c, x, y, w, h, texto):
        """Dibuja un placeholder con marco punteado y texto centrado."""
        c.saveState()
        c.setStrokeColor(HexColor("#BBBBBB"))
        c.setDash(3, 3)
        c.setLineWidth(0.5)
        c.rect(x, y, w, h)

        # Texto central
        c.setDash()
        c.setFillColor(HexColor("#999999"))
        c.setFont("Helvetica", 12)
        c.drawCentredString(x + w / 2, y + h / 2 + 5, "ZONA DE DIBUJO")
        c.setFont("Helvetica", 9)
        c.drawCentredString(x + w / 2, y + h / 2 - 10, texto)

        # Indicadores de vista (guías)
        c.setFont("Helvetica", 7)
        c.setFillColor(HexColor("#BBBBBB"))
        mid_x = x + w / 2
        mid_y = y + h / 2

        # Sugerir layout: vista frontal + lateral + posterior
        third_w = w / 3
        c.drawCentredString(x + third_w * 0.5, y + h - 8, "Vista frontal")
        c.drawCentredString(x + third_w * 1.5, y + h - 8, "Vista posterior")
        c.drawCentredString(mid_x, y + 8, "Vista lateral")

        c.restoreState()

    # -------------------------------------------------------------------------
    # CAJETÍN
    # -------------------------------------------------------------------------
    def _dibujar_cajetin(self, c, plano, num_plano):
        """Dibuja el cajetín inferior con todos los campos técnicos."""
        proy = self.config["proyecto"]
        pers = self.config["personas"]
        empresa = self.config["empresa"]

        x0 = self.margin
        y_barra_top = self.margin + self.barra_height
        y_cajetin_top = self.margin + self.cajetin_height

        # Ancho total del cajetín
        w_total = self.page_width - 2 * self.margin

        # Columna derecha (logo + número de plano + escala)
        right_col_w = 35 * mm
        right_col_x = x0 + w_total - right_col_w
        # Ancho disponible para campos de la izquierda
        w_campos = w_total - right_col_w

        # --- "Medidas en mm." arriba a la derecha del cajetín ---
        c.setFont("Helvetica", 7)
        c.setFillColor(COLOR_TEXTO)
        c.drawRightString(x0 + w_total - 2 * mm, y_cajetin_top + 3 * mm,
                          proy.get("unidades", "Medidas en mm."))

        # =====================================================================
        # TÍTULO PRINCIPAL (fila superior del cajetín)
        # =====================================================================
        y_titulo = y_cajetin_top - 2 * mm
        titulo_h = 12 * mm
        y_titulo_bottom = y_titulo - titulo_h

        # Triángulo decorativo
        c.setFillColor(COLOR_TRIANGULO)
        path = c.beginPath()
        path.moveTo(x0, y_titulo)
        path.lineTo(x0, y_titulo_bottom)
        path.lineTo(x0 + 10 * mm, y_titulo_bottom)
        path.close()
        c.drawPath(path, fill=1, stroke=0)

        # Título texto (centrado en la zona izquierda)
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(COLOR_TEXTO)
        titulo_text = proy.get("titulo", "PROYECTO DE REFORMA DE VEHÍCULO")
        c.drawCentredString(x0 + w_campos / 2, y_titulo_bottom + 3 * mm,
                            titulo_text)

        # Línea bajo el título (todo el ancho)
        c.setStrokeColor(COLOR_LINEA)
        c.setLineWidth(0.5)
        c.line(x0, y_titulo_bottom, x0 + w_total, y_titulo_bottom)

        # =====================================================================
        # COLUMNA DERECHA: Logo (arriba) + Número (centro) + Escala (abajo)
        # =====================================================================
        # Línea vertical izquierda de la columna derecha
        c.setLineWidth(0.3)
        c.line(right_col_x, y_titulo, right_col_x, y_barra_top)

        # Logo empresa (mitad superior de columna derecha, alineado con título)
        logo_pad = 2 * mm
        logo_area_w = right_col_w - 2 * logo_pad
        logo_area_h = titulo_h - 2 * logo_pad
        logo_x = right_col_x + logo_pad
        logo_y = y_titulo_bottom + logo_pad

        logo_path = empresa.get("logo_path", "")
        if logo_path and os.path.exists(logo_path):
            try:
                c.drawImage(logo_path, logo_x, logo_y,
                            logo_area_w, logo_area_h,
                            preserveAspectRatio=True, mask='auto')
            except Exception:
                self._dibujar_logo_placeholder(c, right_col_x, y_titulo_bottom,
                                                right_col_w, titulo_h, empresa)
        else:
            self._dibujar_logo_placeholder(c, right_col_x, y_titulo_bottom,
                                            right_col_w, titulo_h, empresa)

        # Número de plano grande (zona central de columna derecha)
        num_area_top = y_titulo_bottom
        num_area_bottom = y_barra_top
        num_area_h = num_area_top - num_area_bottom

        c.setFont("Helvetica-Bold", 56)
        c.setFillColor(COLOR_TEXTO)
        c.drawCentredString(right_col_x + right_col_w / 2,
                            num_area_bottom + num_area_h * 0.35,
                            str(num_plano))

        # Escala (parte inferior de columna derecha)
        c.setFont("Helvetica", 6)
        c.setFillColor(COLOR_GRIS_LABEL)
        c.drawString(right_col_x + 2 * mm,
                     num_area_bottom + num_area_h * 0.18, "Escala.")
        c.setFont("Helvetica", 8)
        c.setFillColor(COLOR_TEXTO)
        c.drawCentredString(right_col_x + right_col_w / 2,
                            num_area_bottom + num_area_h * 0.05,
                            proy.get("escala", "A4 - S/E"))

        # =====================================================================
        # FILAS DE DATOS (zona izquierda)
        # =====================================================================
        fila_h = 8 * mm
        y_fila1_top = y_titulo_bottom
        y_fila1_bottom = y_fila1_top - fila_h
        y_fila2_top = y_fila1_bottom
        y_fila2_bottom = y_fila2_top - fila_h
        y_fila3_top = y_fila2_bottom
        y_fila3_bottom = y_fila3_top - fila_h
        y_fila4_top = y_fila3_bottom
        y_fila4_bottom = y_barra_top

        col_label = x0 + 1 * mm

        # ---- FILA 1: Contenido ----
        c.setStrokeColor(COLOR_LINEA)
        c.setLineWidth(0.3)
        c.line(x0, y_fila1_bottom, right_col_x, y_fila1_bottom)

        c.setFont("Helvetica", 6)
        c.setFillColor(COLOR_GRIS_LABEL)
        c.drawString(col_label, y_fila1_top - 3 * mm, "Contenido")

        c.setFont("Helvetica", 10)
        c.setFillColor(COLOR_TEXTO)
        contenido = plano.get("contenido", "")
        c.drawCentredString(x0 + w_campos / 2, y_fila1_bottom + 2 * mm, contenido)

        # ---- FILA 2: Vehículo ----
        c.line(x0, y_fila2_bottom, right_col_x, y_fila2_bottom)

        c.setFont("Helvetica", 6)
        c.setFillColor(COLOR_GRIS_LABEL)
        c.drawString(col_label, y_fila2_top - 3 * mm, "Vehículo")

        c.setFont("Helvetica", 10)
        c.setFillColor(COLOR_TEXTO)
        vehiculo = proy.get("vehiculo", "")
        matricula = proy.get("matricula", "")
        vehiculo_text = f"{vehiculo}  {matricula}" if vehiculo else ""
        c.drawCentredString(x0 + w_campos / 2, y_fila2_bottom + 2 * mm,
                            vehiculo_text)

        # ---- FILA 3: Dibujado | Fecha | Exp. ----
        c.line(x0, y_fila3_bottom, right_col_x, y_fila3_bottom)

        # Sub-columnas para fila 3 (sin Escala, que ahora está en columna derecha)
        f3_col1_w = w_campos * 0.40
        f3_col2_w = w_campos * 0.28
        f3_col3_w = w_campos * 0.32

        f3_x1 = x0
        f3_x2 = f3_x1 + f3_col1_w
        f3_x3 = f3_x2 + f3_col2_w

        # Líneas verticales
        c.line(f3_x2, y_fila3_top, f3_x2, y_fila3_bottom)
        c.line(f3_x3, y_fila3_top, f3_x3, y_fila3_bottom)

        # Labels
        c.setFont("Helvetica", 6)
        c.setFillColor(COLOR_GRIS_LABEL)
        c.drawString(f3_x1 + 1 * mm, y_fila3_top - 3 * mm, "Dibujado.")
        c.drawString(f3_x2 + 1 * mm, y_fila3_top - 3 * mm, "Fecha")
        c.drawString(f3_x3 + 1 * mm, y_fila3_top - 3 * mm, "Exp.")

        # Valores
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(COLOR_TEXTO)
        c.drawCentredString(f3_x1 + f3_col1_w / 2, y_fila3_bottom + 2 * mm,
                            pers.get("dibujado", ""))

        fecha = proy.get("fecha", "")
        if not fecha:
            fecha = datetime.now().strftime("%d/%m/%Y")
        c.setFont("Helvetica", 8)
        c.drawCentredString(f3_x2 + f3_col2_w / 2, y_fila3_bottom + 2 * mm, fecha)
        c.drawCentredString(f3_x3 + f3_col3_w / 2, y_fila3_bottom + 2 * mm,
                            proy.get("expediente", ""))

        # ---- FILA 4: Peticionario | Ingeniero | Firma ----
        fila4_h = y_fila3_bottom - y_barra_top

        f4_col1_w = w_campos * 0.40
        f4_col2_w = w_campos * 0.38
        f4_col3_w = w_campos * 0.22

        f4_x1 = x0
        f4_x2 = f4_x1 + f4_col1_w
        f4_x3 = f4_x2 + f4_col2_w

        # Líneas verticales
        c.line(f4_x2, y_fila3_bottom, f4_x2, y_barra_top)
        c.line(f4_x3, y_fila3_bottom, f4_x3, y_barra_top)

        # Labels
        c.setFont("Helvetica", 6)
        c.setFillColor(COLOR_GRIS_LABEL)
        c.drawString(f4_x1 + 1 * mm, y_fila3_bottom - 3 * mm, "Peticionario")
        c.drawString(f4_x2 + 1 * mm, y_fila3_bottom - 3 * mm,
                     "Ingeniero Técnico Industrial")

        # Valores
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(COLOR_TEXTO)
        c.drawCentredString(f4_x1 + f4_col1_w / 2,
                            y_barra_top + fila4_h / 2 - 1 * mm,
                            pers.get("peticionario", ""))

        # Ingeniero + colegiado
        c.setFont("Helvetica-Bold", 9)
        ingeniero = pers.get("ingeniero", "")
        colegiado = pers.get("colegiado", "")
        c.drawCentredString(f4_x2 + f4_col2_w / 2,
                            y_barra_top + fila4_h / 2 + 2 * mm,
                            ingeniero)
        if colegiado:
            c.setFont("Helvetica", 7)
            c.drawCentredString(f4_x2 + f4_col2_w / 2,
                                y_barra_top + fila4_h / 2 - 4 * mm,
                                f"Colegiado. n\u00ba {colegiado}")

        # Firma
        c.setFont("Helvetica", 6)
        c.setFillColor(COLOR_GRIS_LABEL)
        c.drawCentredString(f4_x3 + f4_col3_w / 2,
                            y_barra_top + 2 * mm, "Firma")

        firma_path = pers.get("firma_path", "")
        if firma_path and os.path.exists(firma_path):
            try:
                firma_size = min(f4_col3_w - 4 * mm, fila4_h - 6 * mm)
                c.drawImage(firma_path,
                            f4_x3 + (f4_col3_w - firma_size) / 2,
                            y_barra_top + 5 * mm,
                            firma_size, firma_size,
                            preserveAspectRatio=True, mask='auto')
            except Exception:
                pass

        # --- Extras del plano (ej: MASA REAL, TARA) ---
        extras = plano.get("extras", {})
        if extras:
            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(COLOR_TEXTO)
            y_extra = self.dibujo_bottom + 5 * mm
            for key, value in extras.items():
                c.drawString(self.margin + 4 * mm, y_extra,
                             f"{key}: {value}")
                y_extra -= 4 * mm

    def _dibujar_logo_placeholder(self, c, x, y, w, h, empresa):
        """Dibuja un placeholder circular para el logo de empresa."""
        c.saveState()
        cx = x + w / 2
        cy = y + h / 2
        r = min(w, h) / 2 - 1 * mm
        # Círculo de placeholder
        c.setStrokeColor(HexColor("#AAAAAA"))
        c.setLineWidth(0.5)
        c.setFillColor(white)
        c.circle(cx, cy, r, fill=1, stroke=1)
        # Texto dentro
        c.setFont("Helvetica-Bold", 6)
        c.setFillColor(COLOR_TEXTO)
        nombre = empresa.get("nombre", "EMPRESA")
        # Dividir en 2 líneas si es largo
        parts = nombre.split(" ", 1)
        if len(parts) == 2:
            c.drawCentredString(cx, cy + 1 * mm, parts[0])
            c.setFont("Helvetica", 5)
            c.drawCentredString(cx, cy - 3 * mm, parts[1])
        else:
            c.drawCentredString(cx, cy, nombre)
        c.restoreState()

    # -------------------------------------------------------------------------
    # BARRA DE EMPRESA
    # -------------------------------------------------------------------------
    def _dibujar_barra_empresa(self, c):
        """Dibuja la barra inferior con datos de la empresa."""
        empresa = self.config["empresa"]
        x0 = self.margin
        y0 = self.margin
        w = self.page_width - 2 * self.margin
        h = self.barra_height

        # Fondo oscuro
        c.setFillColor(COLOR_BARRA_FONDO)
        c.rect(x0, y0, w, h, fill=1, stroke=0)

        # Texto empresa
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 9)
        nombre = empresa.get("nombre", "")
        subtitulo = empresa.get("subtitulo", "")
        texto_empresa = f"{nombre}  -  {subtitulo}" if subtitulo else nombre
        c.drawCentredString(x0 + w / 2, y0 + h / 2 + 1 * mm, texto_empresa)

        # Dirección
        c.setFont("Helvetica", 6)
        c.setFillColor(COLOR_BARRA_TEXTO)
        c.drawCentredString(x0 + w / 2, y0 + 2 * mm,
                            empresa.get("direccion", ""))


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def cargar_config(json_path):
    """Carga configuración desde archivo JSON, fusionándola con defaults."""
    config = dict(DEFAULT_CONFIG)
    if json_path and os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            user_config = json.load(f)
        # Fusión superficial por sección
        for section in config:
            if section in user_config:
                if isinstance(config[section], dict):
                    config[section] = {**config[section], **user_config[section]}
                else:
                    config[section] = user_config[section]
    return config


def crear_config_ejemplo(output_path="plano_config_ejemplo.json"):
    """Crea un archivo JSON de ejemplo con la configuración."""
    ejemplo = {
        "empresa": {
            "nombre": "PHICAN INGENIEROS",
            "subtitulo": "ESTUDIO DE INGENIERÍA",
            "direccion": "C/ RAMBLA DOCTOR PÉREZ, 5 - LOCAL 22 - 38390 SANTA URSULA (SANTA CRUZ DE TENERIFE)",
            "logo_path": ""
        },
        "proyecto": {
            "titulo": "PROYECTO DE REFORMA DE VEHÍCULO",
            "vehiculo": "Citroen / Capron - V66",
            "matricula": "6378LZD",
            "expediente": "PH_006/2025",
            "fecha": "1/10/2025",
            "escala": "A4 - S/E",
            "unidades": "Medidas en mm."
        },
        "personas": {
            "dibujado": "Roberto García Gutiérrez",
            "peticionario": "Agustín Regalado García",
            "ingeniero": "Roberto García Gutiérrez",
            "colegiado": "1816",
            "firma_path": ""
        },
        "planos": [
            {
                "contenido": "Antes de la Reforma",
                "imagen_path": "",
                "extras": {}
            },
            {
                "contenido": "Después de la Reforma",
                "imagen_path": "",
                "extras": {
                    "MASA REAL": "3015 Kg",
                    "TARA": "2940 Kg"
                }
            },
            {
                "contenido": "Balonas de suspensión",
                "imagen_path": "",
                "extras": {}
            },
            {
                "contenido": "Compresor",
                "imagen_path": "",
                "extras": {}
            }
        ]
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ejemplo, f, ensure_ascii=False, indent=2)
    print(f"Config de ejemplo creada: {os.path.abspath(output_path)}")
    return output_path


# =============================================================================
# GUI - FORMULARIO DE EDICIÓN
# =============================================================================

def abrir_formulario(config=None):
    """Abre una ventana GUI para editar la configuración y generar el PDF."""
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    if config is None:
        config = dict(DEFAULT_CONFIG)

    root = tk.Tk()
    root.title("Planos Técnicos de Vehículos - PHICAN INGENIEROS")
    root.geometry("920x720")
    root.resizable(True, True)

    # Estilo
    style = ttk.Style()
    style.configure("Title.TLabel", font=("Segoe UI", 11, "bold"))
    style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"))

    # Variables para almacenar los valores
    vars_empresa = {}
    vars_proyecto = {}
    vars_personas = {}

    # --- Scrollable frame ---
    main_canvas = tk.Canvas(root, highlightthickness=0)
    scrollbar = ttk.Scrollbar(root, orient="vertical", command=main_canvas.yview)
    scroll_frame = ttk.Frame(main_canvas)

    scroll_frame.bind("<Configure>",
                      lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
    main_canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    main_canvas.configure(yscrollcommand=scrollbar.set)

    # Scroll con rueda del ratón
    def _on_mousewheel(event):
        main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    root.bind_all("<MouseWheel>", _on_mousewheel)

    scrollbar.pack(side="right", fill="y")
    main_canvas.pack(side="left", fill="both", expand=True)

    pad = {"padx": 8, "pady": 3}

    def crear_campo(parent, label, valor_default="", row=0, width=40):
        """Crea un label + entry y devuelve la StringVar."""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="e", **pad)
        var = tk.StringVar(value=valor_default)
        entry = ttk.Entry(parent, textvariable=var, width=width)
        entry.grid(row=row, column=1, sticky="ew", **pad)
        return var

    def crear_campo_archivo(parent, label, valor_default="", row=0,
                            filetypes=None):
        """Crea un label + entry + botón examinar para archivos."""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="e", **pad)
        var = tk.StringVar(value=valor_default)
        frame_f = ttk.Frame(parent)
        frame_f.grid(row=row, column=1, sticky="ew", **pad)
        entry = ttk.Entry(frame_f, textvariable=var, width=34)
        entry.pack(side="left", fill="x", expand=True)
        ft = filetypes or [("Imágenes", "*.png *.jpg *.jpeg *.bmp"),
                           ("Todos", "*.*")]

        def browse():
            path = filedialog.askopenfilename(filetypes=ft)
            if path:
                var.set(path)

        ttk.Button(frame_f, text="...", width=3, command=browse).pack(
            side="right", padx=(4, 0))
        return var

    # =====================================================================
    # SECCIÓN: EMPRESA
    # =====================================================================
    frame_emp = ttk.LabelFrame(scroll_frame, text="  Datos de Empresa  ",
                                style="Section.TLabelframe")
    frame_emp.pack(fill="x", padx=10, pady=(10, 5))
    frame_emp.columnconfigure(1, weight=1)

    emp = config.get("empresa", {})
    vars_empresa["nombre"] = crear_campo(frame_emp, "Nombre:", emp.get("nombre", ""), 0)
    vars_empresa["subtitulo"] = crear_campo(frame_emp, "Subtítulo:", emp.get("subtitulo", ""), 1)
    vars_empresa["direccion"] = crear_campo(frame_emp, "Dirección:", emp.get("direccion", ""), 2, 60)
    vars_empresa["logo_path"] = crear_campo_archivo(frame_emp, "Logo (imagen):",
                                                     emp.get("logo_path", ""), 3)

    # =====================================================================
    # SECCIÓN: PROYECTO
    # =====================================================================
    frame_proy = ttk.LabelFrame(scroll_frame, text="  Datos del Proyecto  ",
                                 style="Section.TLabelframe")
    frame_proy.pack(fill="x", padx=10, pady=5)
    frame_proy.columnconfigure(1, weight=1)

    proy = config.get("proyecto", {})
    vars_proyecto["titulo"] = crear_campo(frame_proy, "Título:", proy.get("titulo", ""), 0, 50)
    vars_proyecto["vehiculo"] = crear_campo(frame_proy, "Vehículo:", proy.get("vehiculo", ""), 1)
    vars_proyecto["matricula"] = crear_campo(frame_proy, "Matrícula:", proy.get("matricula", ""), 2, 15)
    vars_proyecto["expediente"] = crear_campo(frame_proy, "Expediente:", proy.get("expediente", ""), 3, 20)
    vars_proyecto["fecha"] = crear_campo(frame_proy, "Fecha:", proy.get("fecha", ""), 4, 15)
    vars_proyecto["escala"] = crear_campo(frame_proy, "Escala:", proy.get("escala", "A4 - S/E"), 5, 15)
    vars_proyecto["unidades"] = crear_campo(frame_proy, "Unidades:", proy.get("unidades", "Medidas en mm."), 6, 20)

    # =====================================================================
    # SECCIÓN: PERSONAS
    # =====================================================================
    frame_pers = ttk.LabelFrame(scroll_frame, text="  Personas  ",
                                 style="Section.TLabelframe")
    frame_pers.pack(fill="x", padx=10, pady=5)
    frame_pers.columnconfigure(1, weight=1)

    pers = config.get("personas", {})
    vars_personas["dibujado"] = crear_campo(frame_pers, "Dibujado por:", pers.get("dibujado", ""), 0)
    vars_personas["peticionario"] = crear_campo(frame_pers, "Peticionario:", pers.get("peticionario", ""), 1)
    vars_personas["ingeniero"] = crear_campo(frame_pers, "Ingeniero:", pers.get("ingeniero", ""), 2)
    vars_personas["colegiado"] = crear_campo(frame_pers, "Nº Colegiado:", pers.get("colegiado", ""), 3, 10)
    vars_personas["firma_path"] = crear_campo_archivo(frame_pers, "Firma (imagen):",
                                                       pers.get("firma_path", ""), 4)

    # =====================================================================
    # SECCIÓN: PLANOS (lista dinámica)
    # =====================================================================
    frame_planos = ttk.LabelFrame(scroll_frame, text="  Planos  ",
                                   style="Section.TLabelframe")
    frame_planos.pack(fill="x", padx=10, pady=5)

    planos_widgets = []  # Lista de dicts con las variables de cada plano

    planos_container = ttk.Frame(frame_planos)
    planos_container.pack(fill="x", padx=5, pady=5)

    def agregar_plano(contenido="", imagen_path="", extras_text=""):
        """Agrega una fila de plano al formulario."""
        idx = len(planos_widgets)
        frame_p = ttk.Frame(planos_container, relief="groove", borderwidth=1)
        frame_p.pack(fill="x", pady=3)
        frame_p.columnconfigure(1, weight=1)

        ttk.Label(frame_p, text=f"Plano {idx + 1}",
                  font=("Segoe UI", 9, "bold")).grid(row=0, column=0, **pad)

        # Contenido
        ttk.Label(frame_p, text="Contenido:").grid(row=0, column=0, sticky="e", **pad)
        var_cont = tk.StringVar(value=contenido)
        ttk.Entry(frame_p, textvariable=var_cont, width=35).grid(
            row=0, column=1, sticky="ew", **pad)

        # Imagen
        ttk.Label(frame_p, text="Imagen:").grid(row=1, column=0, sticky="e", **pad)
        var_img = tk.StringVar(value=imagen_path)
        f_img = ttk.Frame(frame_p)
        f_img.grid(row=1, column=1, sticky="ew", **pad)
        ttk.Entry(f_img, textvariable=var_img, width=30).pack(side="left", fill="x", expand=True)

        def browse_img():
            path = filedialog.askopenfilename(
                filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.pdf"),
                           ("Todos", "*.*")])
            if path:
                var_img.set(path)

        ttk.Button(f_img, text="...", width=3, command=browse_img).pack(
            side="right", padx=(4, 0))

        # Botón buscar plantilla en proveedores
        def buscar_plantilla():
            try:
                from vehiculo_blueprints.gui_selector import VehicleBlueprintSelector

                def on_select(file_path, dimensions):
                    var_img.set(file_path)
                    if dimensions:
                        extras_parts = []
                        if dimensions.get("length_mm"):
                            extras_parts.append(
                                f"LONGITUD: {dimensions['length_mm']} mm")
                        if dimensions.get("width_mm"):
                            extras_parts.append(
                                f"ANCHURA: {dimensions['width_mm']} mm")
                        if dimensions.get("height_mm"):
                            extras_parts.append(
                                f"ALTURA: {dimensions['height_mm']} mm")
                        if dimensions.get("wheelbase_mm"):
                            extras_parts.append(
                                f"BATALLA: {dimensions['wheelbase_mm']} mm")
                        if extras_parts:
                            current = var_extras.get().strip()
                            new_extras = ", ".join(extras_parts)
                            if current:
                                var_extras.set(f"{current}, {new_extras}")
                            else:
                                var_extras.set(new_extras)

                # Intentar pre-rellenar con datos del vehículo del proyecto
                init_make = vars_proyecto.get("vehiculo",
                                               tk.StringVar()).get().split("/")[0].strip()
                init_model = ""
                veh_parts = vars_proyecto.get("vehiculo",
                                               tk.StringVar()).get().split("/")
                if len(veh_parts) > 1:
                    init_model = veh_parts[1].strip().split("-")[0].strip()

                VehicleBlueprintSelector(root, on_select,
                                          initial_make=init_make,
                                          initial_model=init_model)
            except ImportError as e:
                messagebox.showerror(
                    "Error",
                    f"Módulo de búsqueda no disponible:\n{e}\n\n"
                    f"Instala: pip install requests beautifulsoup4 Pillow")

        ttk.Button(f_img, text="Buscar", width=7,
                   command=buscar_plantilla).pack(side="right", padx=(4, 0))

        # Extras (texto libre: CLAVE: valor, una por línea)
        ttk.Label(frame_p, text="Extras:").grid(row=2, column=0, sticky="ne", **pad)
        var_extras = tk.StringVar(value=extras_text)
        ttk.Entry(frame_p, textvariable=var_extras, width=35).grid(
            row=2, column=1, sticky="ew", **pad)
        ttk.Label(frame_p, text="(ej: MASA REAL: 3015 Kg, TARA: 2940 Kg)",
                  font=("Segoe UI", 7)).grid(row=3, column=1, sticky="w", padx=8)

        # Botón eliminar
        def eliminar():
            frame_p.destroy()
            planos_widgets[:] = [pw for pw in planos_widgets if pw["frame"] is not frame_p]
            # Re-numerar
            for i, pw in enumerate(planos_widgets):
                pass  # Los números se asignan al generar

        ttk.Button(frame_p, text="X", width=3, command=eliminar).grid(
            row=0, column=2, **pad)

        planos_widgets.append({
            "frame": frame_p,
            "contenido": var_cont,
            "imagen_path": var_img,
            "extras": var_extras,
        })

    # Cargar planos existentes
    for pl in config.get("planos", []):
        extras_dict = pl.get("extras", {})
        extras_str = ", ".join(f"{k}: {v}" for k, v in extras_dict.items())
        agregar_plano(pl.get("contenido", ""), pl.get("imagen_path", ""), extras_str)

    # Botón añadir plano
    ttk.Button(frame_planos, text="+ Añadir plano", command=agregar_plano).pack(
        pady=5)

    # =====================================================================
    # BOTONES INFERIORES
    # =====================================================================
    frame_botones = ttk.Frame(scroll_frame)
    frame_botones.pack(fill="x", padx=10, pady=15)

    def recoger_config():
        """Recoge todos los valores del formulario en un dict config."""
        cfg = {
            "empresa": {k: v.get() for k, v in vars_empresa.items()},
            "proyecto": {k: v.get() for k, v in vars_proyecto.items()},
            "personas": {k: v.get() for k, v in vars_personas.items()},
            "planos": [],
        }
        for pw in planos_widgets:
            extras_raw = pw["extras"].get().strip()
            extras = {}
            if extras_raw:
                for part in extras_raw.split(","):
                    if ":" in part:
                        k, v = part.split(":", 1)
                        extras[k.strip()] = v.strip()
            cfg["planos"].append({
                "contenido": pw["contenido"].get(),
                "imagen_path": pw["imagen_path"].get(),
                "extras": extras,
            })
        return cfg

    def generar_pdf():
        """Genera el PDF con los datos del formulario."""
        cfg = recoger_config()
        output = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="plano_vehiculo.pdf",
            title="Guardar PDF como...")
        if not output:
            return
        try:
            template = PlanoVehiculoTemplate(cfg)
            template.generar(output)
            messagebox.showinfo("Éxito", f"PDF generado:\n{output}")
            # Abrir el PDF
            os.startfile(output)
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar PDF:\n{e}")

    def guardar_config():
        """Guarda la configuración actual a JSON."""
        cfg = recoger_config()
        output = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            initialfile="plano_config.json",
            title="Guardar configuración como...")
        if not output:
            return
        with open(output, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("Éxito", f"Configuración guardada:\n{output}")

    def cargar_config_gui():
        """Carga una configuración JSON y recarga el formulario."""
        path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
            title="Cargar configuración...")
        if not path:
            return
        root.destroy()
        cfg = cargar_config(path)
        abrir_formulario(cfg)

    ttk.Button(frame_botones, text="Generar PDF",
               command=generar_pdf).pack(side="right", padx=5)
    ttk.Button(frame_botones, text="Guardar Config",
               command=guardar_config).pack(side="right", padx=5)
    ttk.Button(frame_botones, text="Cargar Config",
               command=cargar_config_gui).pack(side="right", padx=5)

    root.mainloop()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Genera plantilla PDF de planos técnicos de vehículos"
    )
    parser.add_argument("--output", "-o", default=None,
                        help="Ruta del PDF de salida (modo CLI)")
    parser.add_argument("--config", "-c", default=None,
                        help="Ruta al JSON de configuración")
    parser.add_argument("--ejemplo", action="store_true",
                        help="Genera un archivo JSON de configuración de ejemplo")
    parser.add_argument("--gui", action="store_true",
                        help="Abre el formulario gráfico")

    args = parser.parse_args()

    if args.ejemplo:
        crear_config_ejemplo()
        sys.exit(0)

    config = cargar_config(args.config)

    # Si no se especifica output, abrir GUI por defecto
    if args.output:
        template = PlanoVehiculoTemplate(config)
        template.generar(args.output)
    else:
        abrir_formulario(config)
