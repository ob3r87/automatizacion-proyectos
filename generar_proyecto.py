#!/usr/bin/env python3
"""
=============================================================
  GENERADOR AUTOMÁTICO DE PROYECTOS DE REFORMA DE VEHÍCULO
  Phican Ingenieros

  Uso:
    python generar_proyecto.py datos_proyecto.json

  El script genera un .docx completo listo para firmar
  a partir de los datos del nuevo expediente.
=============================================================
"""

import sys
import os
import io
import json
import shutil
import re
import math
import subprocess
import tempfile
from pathlib import Path

# Forzar UTF-8 en la salida estándar (necesario en Windows con cp1252)
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Auto-instalación de dependencias ────────────────────────
def _ensure_deps():
    deps = {"defusedxml": "defusedxml", "lxml": "lxml"}
    to_install = []
    for module, package in deps.items():
        try:
            __import__(module)
        except ImportError:
            to_install.append(package)
    if to_install:
        print(f"[INFO] Instalando dependencias: {', '.join(to_install)} ...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install"] + to_install + ["--quiet"]
        )
        print("[INFO] Dependencias instaladas correctamente.")

_ensure_deps()

# ── Rutas ───────────────────────────────────────────────────
SCRIPT_DIR    = Path(__file__).parent
SKILLS_DIR    = SCRIPT_DIR / "scripts" / "office"   # scripts incluidos en el proyecto
TEMPLATE_DOCX = Path(os.environ.get("PHICAN_TEMPLATE_PROYECTO", "") or (SCRIPT_DIR / "PLANTILLA_BASE.docx"))
OUTPUT_DIR    = Path(os.environ.get("PHICAN_OUTPUT_DIR", "") or (SCRIPT_DIR / "proyectos_generados"))


def _normalizar_reformas(reformas):
    """
    Convierte el formato {codigo, grupo, descripcion, reformas: [{titulo,...},...]}
    al formato plano {codigo, grupo, descripcion, titulo, descripcion_trabajo,
    estado_previo, estado_posterior} que usan las funciones internas.

    Si un código tiene N items de reforma se generan N entradas con el mismo
    código pero distinto titulo/descripcion_trabajo/estado_previo/estado_posterior.
    El formato legado (sin campo 'reformas') se pasa sin cambios.
    """
    resultado = []
    for r in reformas:
        base = {
            "codigo":      r.get("codigo", ""),
            "grupo":       r.get("grupo", ""),
            "descripcion": r.get("descripcion", ""),
        }
        items = r.get("reformas", [])
        if not items:
            # Formato legado o acto sin items: pasar tal cual
            resultado.append({**base,
                               "titulo":              r.get("titulo", ""),
                               "descripcion_trabajo": r.get("descripcion_trabajo", ""),
                               "estado_previo":       r.get("estado_previo", ""),
                               "estado_posterior":    r.get("estado_posterior", "")})
        else:
            for item in items:
                resultado.append({**base,
                                   "titulo":              item.get("titulo", ""),
                                   "descripcion_trabajo": item.get("descripcion_trabajo", ""),
                                   "estado_previo":       item.get("estado_previo", ""),
                                   "estado_posterior":    item.get("estado_posterior", "")})
    return resultado


def _to_float(value, default):
    """Convierte a float ignorando valores vacíos o no numéricos."""
    try:
        return float(str(value).replace(",", ".").strip()) if str(value).strip() else default
    except (ValueError, TypeError):
        return default


def calcular_campos(d):
    """Calcula los campos derivados automáticamente a partir de los datos base."""
    peso_kit  = _to_float(d.get("PESO_KIT_KG", ""), 12)
    tara      = _to_float(d.get("TARA_VEHICULO_KG", ""), 2561)
    porcentaje = round((peso_kit / tara) * 100, 1)
    # Formateamos como el original: "0,4"
    porcentaje_str = str(porcentaje).replace(".", ",")
    d["PORCENTAJE_INCREMENTO"] = porcentaje_str

    # Texto completo para la sección de cálculos
    tara_str  = f"{tara:,.0f}".replace(",", ".")
    d["TARA_STR"]      = tara_str        # "2.561"
    d["TARA_TEXTO"]    = str(int(tara))  # "2561"  (para la fórmula)
    d["PESO_KIT_STR"]  = str(int(peso_kit))

    # Porcentaje del 3%
    tres_pct = round(tara * 0.03, 2)
    d["TRES_PCT_TARA"] = f"{tres_pct:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    return d


def reemplazar_en_xml(xml_content, replacements):
    """Aplica todos los reemplazos de texto en el contenido XML."""
    for original, nuevo in replacements.items():
        xml_content = xml_content.replace(original, nuevo)
    return xml_content


def reemplazar_celda_ficha(xml_content, campo_label, nuevo_valor):
    """
    Localiza la fila de la FICHA REDUCIDA cuya primera celda contiene campo_label
    y reemplaza todas las ocurrencias de '- -' en esa fila con nuevo_valor.
    No modifica el resto del documento.
    """
    idx = xml_content.find(campo_label)
    if idx < 0:
        return xml_content
    # Retroceder al inicio del <w:tr> que contiene la celda
    tr_start = xml_content.rfind("<w:tr ", 0, idx)
    if tr_start < 0:
        tr_start = xml_content.rfind("<w:tr>", 0, idx)
    tr_end = xml_content.find("</w:tr>", idx) + len("</w:tr>")
    old_row = xml_content[tr_start:tr_end]
    new_row = old_row.replace("- -", nuevo_valor)
    return xml_content[:tr_start] + new_row + xml_content[tr_end:]


def reemplazar_celda_ficha_ab(xml_content, campo_label, valor_antes, valor_despues):
    """
    Como reemplazar_celda_ficha pero diferencia la columna Antes (primera '- -')
    de la columna Después (segunda '- -' / '-   -' / '- - ').
    Las columnas sin valor se dejan con su placeholder original.
    """
    import re as _re
    idx = xml_content.find(campo_label)
    if idx < 0:
        return xml_content
    tr_start = xml_content.rfind("<w:tr ", 0, idx)
    if tr_start < 0:
        tr_start = xml_content.rfind("<w:tr>", 0, idx)
    tr_end = xml_content.find("</w:tr>", idx) + len("</w:tr>")
    old_row = xml_content[tr_start:tr_end]
    new_row = old_row
    # Replace first occurrence of any dash-space-dash placeholder (antes)
    if valor_antes:
        new_row = _re.sub(r'- {1,4}-', valor_antes, new_row, count=1)
    # Replace second occurrence (después)
    if valor_despues:
        new_row = _re.sub(r'- {1,4}-', valor_despues, new_row, count=1)
    return xml_content[:tr_start] + new_row + xml_content[tr_end:]


def reemplazar_ficha_por_posicion(xml_content, datos):
    """
    Reemplaza placeholders '- -' en la tabla FICHA REDUCIDA usando índices de fila
    en lugar de búsqueda por texto de etiqueta.  Evita falsos positivos con etiquetas
    duplicadas (p.ej. 'Número de homologación' aparece en filas 13 y 16).

    Mapeo: {índice_fila: (clave_antes, clave_despues)}
      - clave_antes=None → valor único: se rellena clave_despues en ambas columnas.
      - ambas str        → columna Antes con clave_antes, Después con clave_despues.
    """
    import re as _re

    _FICHA_POS = {
        # Fila : (clave_antes, clave_despues)  — None en clave_antes → valor único en ambas cols
        6:  (None,                  "CATEGORIA_CODIGO"),
        7:  ("FABR_BASE_A",         "FABR_BASE_D"),
        8:  ("FABR_ULTIMA_A",       "FABR_ULTIMA_D"),
        9:  ("EMPL_PLACA_A",        "EMPL_PLACA_D"),
        11: ("EMPL_VIN_A",          "EMPL_VIN_D"),
        13: ("HOMOL_BASE_A",        "HOMOL_BASE_D"),
        14: ("FECHA_HOMOL_BASE_A",  "FECHA_HOMOL_BASE_D"),
        16: ("HOMOL_COMPL_A",       "HOMOL_COMPL_D"),
        17: ("FECHA_HOMOL_COMPL_A", "FECHA_HOMOL_COMPL_D"),
        19: ("NUM_EJES",            "NUM_EJES_POST"),
        20: ("EJES_MOTR_A",         "EJES_MOTR_D"),
        22: ("DISTANCIA_EJES",      "DISTANCIA_EJES_POST"),
        23: ("VIAS_EJES_A",         "VIAS_EJES_D"),
        24: ("LONGITUD_VEH",        "LONGITUD_VEH_POST"),
        25: ("LONG_MAX_A",          "LONG_MAX_D"),
        26: ("ANCHURA_VEH",         "ANCHURA_VEH_POST"),
        27: ("ANCH_MAX_A",          "ANCH_MAX_D"),
        28: ("ALTURA_VEH",          "ALTURA_VEH_POST"),
        29: ("VOLADIZO_A",          "VOLADIZO_D"),
        30: ("TARA_VEHICULO_KG",    "TARA_VEHICULO_KG_POST"),
        31: ("MASA_MIN_A",          "MASA_MIN_D"),
        32: ("MMTA",                "MMTA_POST"),
        33: ("MMA",                 "MMA_POST"),
        34: ("MMTA_EJE_A",          "MMTA_EJE_D"),
        35: ("MMA_EJE_A",           "MMA_EJE_D"),
        36: ("MMTC",                "MMTC_POST"),
        37: ("MMA_CONJ_A",          "MMA_CONJ_D"),
        38: ("MASA_REMOLC_A",       "MASA_REMOLC_D"),
        39: ("REMOLQ_BARRA_A",      "REMOLQ_BARRA_D"),
        40: ("REMOLQ_EJE_A",        "REMOLQ_EJE_D"),
        41: ("MASA_REMOLQ_SF_A",    "MASA_REMOLQ_SF_D"),
        42: ("CARGA_VERT_A",        "CARGA_VERT_D"),
        44: ("FABR_MOTOR_A",        "FABR_MOTOR_D"),
        45: ("COD_MOTOR_A",         "COD_MOTOR_D"),
        46: ("MOTOR_COMB_A",        "MOTOR_COMB_D"),
        47: ("FUNC_MOTOR_A",        "FUNC_MOTOR_D"),
        48: ("CILINDROS_A",         "CILINDROS_D"),
        49: ("CILINDRADA_A",        "CILINDRADA_D"),
        50: ("COMBUSTIBLE_A",       "COMBUSTIBLE_D"),
        51: ("POT_NETA_A",          "POT_NETA_D"),
        52: ("MOTOR_ELEC_A",        "MOTOR_ELEC_D"),
        53: ("POT_HORA_A",          "POT_HORA_D"),
        54: ("MOTOR_HIBR_A",        "MOTOR_HIBR_D"),
        55: ("TIPO_HIBR_A",         "TIPO_HIBR_D"),
        57: ("TRANS_TIPO_A",        "TRANS_TIPO_D"),
        58: ("CAJA_CAMB_A",         "CAJA_CAMB_D"),
        59: ("NUM_RELAC_A",         "NUM_RELAC_D"),
        61: ("SUSPENSION_A",        "SUSPENSION_D"),
        64: ("DIRECCION_A",         "DIRECCION_D"),
        66: ("FRENADO_A",           "FRENADO_D"),
        68: ("CARROCERIA_A",        "CARROCERIA_D"),
        69: ("VISION_IND_A",        "VISION_IND_D"),
        70: ("PUERTAS_A",           "PUERTAS_D"),
        71: ("PLAZAS_A",            "PLAZAS_D"),
        72: ("HOMOL_CE_A",          "HOMOL_CE_D"),
        73: ("PROT_DELT_A",         "PROT_DELT_D"),
        75: ("ALUMBR_OBL_A",        "ALUMBR_OBL_D"),
        76: ("ALUMBR_FAC_A",        "ALUMBR_FAC_D"),
        78: ("VEL_MAX_A",           "VEL_MAX_D"),
        79: ("RUIDO_A",             "RUIDO_D"),
        80: ("EMISIONES_A",         "EMISIONES_D"),
        81: ("CO2_A",               "CO2_D"),
        82: ("POT_FISCAL_A",        "POT_FISCAL_D"),
        83: ("OBSERV_FICHA_A",      "OBSERV_FICHA_D"),
        84: ("OPCIONES_HOMOL_A",    "OPCIONES_HOMOL_D"),
    }

    # Localizar la tabla FICHA REDUCIDA
    idx = xml_content.find("FICHA REDUCIDA")
    if idx < 0:
        return xml_content
    tbl_start = xml_content.rfind("<w:tbl", 0, idx)
    if tbl_start < 0:
        return xml_content
    tbl_end = xml_content.find("</w:tbl>", idx) + len("</w:tbl>")
    tbl_xml = xml_content[tbl_start:tbl_end]

    # Recoger posiciones de cada <w:tr> dentro de la tabla
    rows_bounds = []
    scan = 0
    while True:
        a = tbl_xml.find("<w:tr ", scan)
        b = tbl_xml.find("<w:tr>", scan)
        if a < 0 and b < 0:
            break
        rs = min(x for x in [a, b] if x >= 0)
        re_pos = tbl_xml.find("</w:tr>", rs) + len("</w:tr>")
        rows_bounds.append((rs, re_pos))
        scan = re_pos

    # Aplicar sustituciones de mayor a menor índice para no desplazar posiciones
    new_tbl = tbl_xml
    for row_idx in sorted(_FICHA_POS.keys(), reverse=True):
        if row_idx >= len(rows_bounds):
            continue
        rs, re_pos = rows_bounds[row_idx]
        key_a, key_d = _FICHA_POS[row_idx]

        if key_a is None:
            val = datos.get(key_d, "").strip()
            if not val:
                continue
            old_row = new_tbl[rs:re_pos]
            new_row = old_row.replace("- -", val)
        else:
            val_a = datos.get(key_a, "").strip()
            val_d = datos.get(key_d, "").strip()
            if not val_a and not val_d:
                continue
            old_row = new_tbl[rs:re_pos]
            new_row = old_row
            if val_a:
                new_row = _re.sub(r'- {1,4}-', val_a, new_row, count=1)
            if val_d:
                new_row = _re.sub(r'- {1,4}-', val_d, new_row, count=1)

        new_tbl = new_tbl[:rs] + new_row + new_tbl[re_pos:]

    return xml_content[:tbl_start] + new_tbl + xml_content[tbl_end:]


def _xml_escape(text):
    """Escapa caracteres especiales para XML."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _encontrar_parrafo(xml_content, texto, desde=0):
    """
    Retorna (p_start, p_end) del <w:p> que contiene 'texto' buscando desde 'desde'.
    Retorna (-1, -1) si no se encuentra.

    Nota: se busca '<w:p>' o '<w:p ' exactos para evitar coincidir con
    '<w:pPr>', '<w:pStyle>', '<w:pBdr>', etc., que también empiezan por '<w:p'
    y causarían que el corte del XML quedara en medio de una etiqueta.
    """
    pos = xml_content.find(texto, desde)
    if pos < 0:
        return (-1, -1)
    # Tomar el más cercano (mayor posición) entre <w:p> y <w:p (con atributos)
    p_start_a = xml_content.rfind("<w:p>", 0, pos)
    p_start_b = xml_content.rfind("<w:p ", 0, pos)
    p_start = max(p_start_a, p_start_b)
    if p_start < 0:
        return (-1, -1)
    p_end = xml_content.find("</w:p>", pos)
    if p_end < 0:
        return (-1, -1)
    return (p_start, p_end + len("</w:p>"))


def _encontrar_parrafo_cuerpo(xml_content, texto, desde=0):
    """
    Igual que _encontrar_parrafo pero localiza la ÚLTIMA ocurrencia del texto.
    Necesario cuando el mismo texto aparece en el índice (TOC) y en el cuerpo:
    el índice va primero en el XML, el cuerpo va al final → la última ocurrencia
    siempre corresponde al cuerpo del documento.
    """
    pos = -1
    search = desde
    while True:
        found = xml_content.find(texto, search)
        if found < 0:
            break
        pos = found
        search = found + 1
    if pos < 0:
        return (-1, -1)
    p_start_a = xml_content.rfind("<w:p>", 0, pos)
    p_start_b = xml_content.rfind("<w:p ", 0, pos)
    p_start = max(p_start_a, p_start_b)
    if p_start < 0:
        return (-1, -1)
    p_end = xml_content.find("</w:p>", pos)
    if p_end < 0:
        return (-1, -1)
    return (p_start, p_end + len("</w:p>"))


def _parrafo_xml(texto, negrita=False, fuente="Arial", estilo=None, lista=False):
    """Genera XML de un párrafo simple con formato configurable."""
    t = _xml_escape(str(texto))
    estilo_xml = f'<w:pStyle w:val="{estilo}"/>' if estilo else ""
    num_xml = '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="26"/></w:numPr>' if lista else ""
    negrita_xml = "<w:b/>" if negrita else ""
    return (
        f'<w:p><w:pPr>{estilo_xml}{num_xml}'
        f'<w:spacing w:line="276" w:lineRule="auto"/>'
        f'<w:jc w:val="both"/>'
        f'<w:rPr><w:rFonts w:ascii="{fuente}" w:hAnsi="{fuente}" w:cs="{fuente}"/>'
        f'{negrita_xml}</w:rPr></w:pPr>'
        f'<w:r><w:rPr>'
        f'<w:rFonts w:ascii="{fuente}" w:hAnsi="{fuente}" w:cs="{fuente}"/>'
        f'{negrita_xml}</w:rPr>'
        f'<w:t xml:space="preserve">{t}</w:t></w:r></w:p>'
    )


def _parrafo_vacio_xml():
    return '<w:p><w:pPr><w:spacing w:line="276" w:lineRule="auto"/></w:pPr></w:p>'


def _tipo_fijacion_de_calculos(codigo_reforma, calculos):
    """
    Busca en los bloques de cálculo el tipo de fijación asociado a un código de reforma.
    Retorna una cadena descriptiva o vacía si no hay cálculos asociados.
    """
    for calc in calculos:
        ref = calc.get("reforma_ref", "")
        # La ref tiene formato "CR X.Y — título" o "CR X.Y — desc"
        if f"CR {codigo_reforma}" in ref or f"CR{codigo_reforma}" in ref:
            tipo = calc.get("tipo", "")
            campos = calc.get("campos", {})
            if "atornilladas" in tipo.lower():
                diam  = campos.get("TORN_DIAM", "")
                cal   = campos.get("TORN_CALIDAD", "")
                ntor  = campos.get("TORN_NUM", "")
                partes = []
                if ntor:
                    partes.append(f"mediante {ntor} tornillos")
                if diam:
                    partes.append(diam)
                if cal:
                    partes.append(f"calidad {cal}")
                if partes:
                    return "Fijación " + " ".join(partes) + ", según EN\u00a01993-1-8."
            elif "neumática" in tipo.lower() or "balonas" in tipo.lower():
                marca = campos.get("MARCA_BALONAS", "")
                pres  = campos.get("PRESION_BALONAS_BAR", campos.get("PRESION_BALONAS", ""))
                if marca or pres:
                    return f"Sistema neumático de balonas{(' marca ' + marca) if marca else ''}" \
                           f"{(' a ' + pres + ' bar') if pres else ''}."
            elif tipo and tipo != "— Sin cálculo —":
                return f"Cálculo: {tipo}."
    return ""


def reemplazar_seccion_12(xml_content, reformas, calculos):
    """
    Reemplaza el bloque descriptivo de la sección 1.2 ANTECEDENTES
    (entre 'Siendo las reformas…' y 'Los actos reglamentarios aplicados…')
    con una entrada por cada reforma aplicada.
    """
    if not reformas:
        return xml_content

    anchor_inicio = "Siendo las reformas a realizar en el veh\u00edculo las siguientes:"
    anchor_fin    = "Los actos reglamentarios aplicados seg\u00fan las reformas aplicadas:"

    ini_p_start, ini_p_end = _encontrar_parrafo(xml_content, anchor_inicio)
    if ini_p_start < 0:
        return xml_content
    fin_p_start, fin_p_end = _encontrar_parrafo(xml_content, anchor_fin, ini_p_end)
    if fin_p_start < 0:
        return xml_content

    # Bloque a reemplazar: desde el fin del párrafo ancla hasta el inicio del párrafo final
    bloque_nuevo = ""
    for r in reformas:
        cod    = r.get("codigo", "")
        titulo = r.get("titulo", "").strip()
        desc   = r.get("descripcion", "").strip()
        estado = r.get("estado_posterior", "").strip()

        etiqueta = titulo if titulo else desc
        if cod:
            linea = f"CR {cod}"
            if etiqueta:
                linea += f" — {etiqueta}"
            bloque_nuevo += _parrafo_xml(linea, negrita=True, lista=True)
        if estado:
            bloque_nuevo += _parrafo_xml(estado, lista=False)
        bloque_nuevo += _parrafo_vacio_xml()

    return xml_content[:ini_p_end] + bloque_nuevo + xml_content[fin_p_start:]


def reemplazar_seccion_152(xml_content, reformas, calculos):
    """
    Reemplaza el bloque de la sección 1.5.2 Variaciones y sustituciones.
    Busca el encabezado 'Variaciones y sustituciones.' e inserta las reformas
    inmediatamente después, eliminando cualquier contenido hasta 'Materiales empleados.'
    """
    if not reformas:
        return xml_content

    anchor_inicio = "Variaciones y sustituciones."
    anchor_fin    = "Materiales empleados."

    # Usar la última ocurrencia para saltar la entrada del índice (TOC),
    # que repite los mismos encabezados antes del cuerpo real del documento.
    ini_p_start, ini_p_end = _encontrar_parrafo_cuerpo(xml_content, anchor_inicio)
    if ini_p_start < 0:
        print("[AVISO] No se encontró el ancla '1.5.2 Variaciones y sustituciones.' en la plantilla.")
        return xml_content
    fin_p_start, fin_p_end = _encontrar_parrafo_cuerpo(xml_content, anchor_fin)
    if fin_p_start < 0 or fin_p_start <= ini_p_end:
        print("[AVISO] No se encontró el ancla 'Materiales empleados.' tras la sección 1.5.2.")
        return xml_content

    bloque_nuevo = ""
    for r in reformas:
        cod    = r.get("codigo", "")
        titulo = r.get("titulo", "").strip()
        desc   = r.get("descripcion", "").strip()
        prev   = r.get("estado_previo", "").strip()
        post   = r.get("estado_posterior", "").strip()

        etiqueta = titulo if titulo else desc
        titulo_linea = f"CR {cod}" + (f" — {etiqueta}" if etiqueta else "") if cod else etiqueta
        if titulo_linea:
            bloque_nuevo += _parrafo_xml(titulo_linea, negrita=True)

        if prev:
            bloque_nuevo += _parrafo_xml(f"Estado previo: {prev}")
        if post:
            bloque_nuevo += _parrafo_xml(f"Estado posterior: {post}")

        fijacion = _tipo_fijacion_de_calculos(cod, calculos)
        if fijacion:
            bloque_nuevo += _parrafo_xml(fijacion)

        bloque_nuevo += _parrafo_vacio_xml()

    # Conservar el encabezado (hasta ini_p_end), insertar reformas,
    # luego saltar al inicio de "Materiales empleados."
    return xml_content[:ini_p_end] + bloque_nuevo + xml_content[fin_p_start:]


def _bloque_directiva_xml(codigo, descripcion, directivas):
    """Genera el XML de un bloque completo de directivas para un código de reforma."""
    d = _xml_escape
    R = (
        '<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>'
        '<w:sz w:val="18"/><w:szCs w:val="18"/>'
    )
    Rb = f'<w:b/><w:bCs/>{R}'

    def celda(ancho, span, texto, bold=False, center=False):
        span_xml = f'<w:gridSpan w:val="{span}"/>' if span > 1 else ""
        jc_xml   = '<w:jc w:val="center"/>' if center else ""
        rpr      = Rb if bold else R
        return (
            f'<w:tc><w:tcPr><w:tcW w:w="{ancho}" w:type="dxa"/>{span_xml}'
            f'<w:vAlign w:val="center"/></w:tcPr>'
            f'<w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/>{jc_xml}'
            f'<w:rPr>{rpr}</w:rPr></w:pPr>'
            f'<w:r><w:rPr>{rpr}</w:rPr>'
            f'<w:t xml:space="preserve">{d(texto)}</w:t></w:r></w:p></w:tc>'
        )

    TR = '<w:trPr><w:gridAfter w:val="1"/><w:wAfter w:w="20" w:type="dxa"/><w:trHeight w:val="300"/></w:trPr>'

    rows = []
    # Fila 1: código + descripción
    rows.append(
        f'<w:tr><w:trPr><w:gridAfter w:val="1"/><w:wAfter w:w="20" w:type="dxa"/>'
        f'<w:trHeight w:val="400"/></w:trPr>'
        + celda(1200, 1, codigo, bold=True, center=True)
        + celda(8400, 7, descripcion)
        + '</w:tr>'
    )
    # Fila 2: "ACTOS REGLAMENTARIOS" (merged)
    rows.append(
        f'<w:tr>{TR}'
        + celda(9600, 8, "ACTOS REGLAMENTARIOS", bold=True, center=True)
        + '</w:tr>'
    )
    # Fila 3: cabeceras columnas
    rows.append(
        f'<w:tr>{TR}'
        + celda(6100, 4, "SISTEMA AFECTADO", bold=True)
        + celda(1840, 2, "REFERENCIA", bold=True)
        + celda(1660, 2, "APLICABLE", bold=True, center=True)
        + '</w:tr>'
    )
    # Filas de datos
    for item in directivas:
        rows.append(
            f'<w:tr>{TR}'
            + celda(6100, 4, item.get("sistema", ""))
            + celda(1840, 2, item.get("referencia", ""))
            + celda(1660, 2, item.get("valor", ""), center=True)
            + '</w:tr>'
        )
    return "".join(rows)


def generar_tabla_directivas(xml_content, directivas_doc):
    """
    Reemplaza el contenido de la tabla ACTOS REGLAMENTARIOS con los bloques
    generados dinámicamente a partir de directivas_doc (lista de
    {codigo, descripcion, directivas: [{sistema, referencia, valor}]}).
    Si directivas_doc está vacío, deja la tabla intacta.
    """
    if not directivas_doc:
        return xml_content

    marker = "ACTOS REGLAMENTARIOS"
    idx_marker = xml_content.find(marker)
    if idx_marker < 0:
        return xml_content

    tbl_start = xml_content.rfind("<w:tbl>", 0, idx_marker)
    if tbl_start < 0:
        tbl_start = xml_content.rfind("<w:tbl ", 0, idx_marker)
    if tbl_start < 0:
        return xml_content

    tbl_end = xml_content.find("</w:tbl>", tbl_start) + len("</w:tbl>")
    tbl_xml = xml_content[tbl_start:tbl_end]

    # Conservar el prefijo de la tabla (tblPr + tblGrid, antes del primer <w:tr>)
    primera_tr = tbl_xml.find("<w:tr")
    tbl_prefijo = tbl_xml[:primera_tr]

    nuevas_filas = "".join(
        _bloque_directiva_xml(
            b["codigo"],
            b.get("descripcion", ""),
            b.get("directivas", []),
        )
        for b in directivas_doc
    )

    nueva_tabla = f"{tbl_prefijo}{nuevas_filas}</w:tbl>"
    return xml_content[:tbl_start] + nueva_tabla + xml_content[tbl_end:]


def _fila_reforma_xml(grupo, codigo, descripcion):
    """Genera el XML de una fila de la tabla de actos reglamentarios."""
    g = _xml_escape(str(grupo))
    c = _xml_escape(str(codigo))
    d = _xml_escape(str(descripcion))
    return (
        '<w:tr><w:trPr><w:jc w:val="center"/></w:trPr>'
        # Celda Grupo
        '<w:tc><w:tcPr><w:tcW w:w="846" w:type="dxa"/></w:tcPr>'
        '<w:p><w:pPr><w:spacing w:line="276" w:lineRule="auto"/>'
        '<w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>'
        '<w:bCs/><w:sz w:val="20"/></w:rPr></w:pPr>'
        '<w:r><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>'
        f'<w:bCs/><w:sz w:val="20"/></w:rPr><w:t>{g}</w:t></w:r></w:p></w:tc>'
        # Celda Código
        '<w:tc><w:tcPr><w:tcW w:w="1276" w:type="dxa"/></w:tcPr>'
        '<w:p><w:pPr><w:spacing w:line="276" w:lineRule="auto"/>'
        '<w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>'
        '<w:bCs/><w:sz w:val="20"/></w:rPr></w:pPr>'
        '<w:r><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>'
        f'<w:bCs/><w:sz w:val="20"/></w:rPr><w:t>{c}</w:t></w:r></w:p></w:tc>'
        # Celda Descripción
        '<w:tc><w:tcPr><w:tcW w:w="7796" w:type="dxa"/></w:tcPr>'
        '<w:p><w:pPr><w:spacing w:line="276" w:lineRule="auto"/>'
        '<w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>'
        '<w:bCs/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr></w:pPr>'
        '<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>'
        f'<w:bCs/><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr><w:t>{d}</w:t></w:r></w:p></w:tc>'
        '</w:tr>'
    )


def reemplazar_tabla_reformas(xml_content, reformas):
    """
    Localiza la tabla de actos reglamentarios y reemplaza sus filas de datos
    con las filas generadas a partir de la lista 'reformas'.
    Cada elemento de 'reformas' es un dict {codigo, grupo, descripcion}.
    Si 'reformas' está vacío, deja la tabla original intacta.
    """
    if not reformas:
        return xml_content

    # El marcador de la tabla es el párrafo anterior con "reglamentarios"
    marker = "reglamentarios aplicados"
    idx_marker = xml_content.find(marker)
    if idx_marker < 0:
        print("[AVISO] No se encontró la tabla de actos reglamentarios en el documento.")
        return xml_content

    tbl_start = xml_content.find("<w:tbl>", idx_marker)
    if tbl_start < 0:
        print("[AVISO] No se encontró <w:tbl> después del marcador de reformas.")
        return xml_content

    tbl_end = xml_content.find("</w:tbl>", tbl_start) + len("</w:tbl>")
    tbl_original = xml_content[tbl_start:tbl_end]

    # Extraer la cabecera (primer <w:tr>)
    tr_start = tbl_original.find("<w:tr ")
    if tr_start < 0:
        tr_start = tbl_original.find("<w:tr>")
    # La cabecera termina en el primer </w:tr>
    tr_end = tbl_original.find("</w:tr>", tr_start) + len("</w:tr>")
    header_row = tbl_original[tr_start:tr_end]

    # Extraer el prefijo de la tabla (tblPr + tblGrid)
    tbl_prefix = tbl_original[len("<w:tbl>"):tr_start]

    # Construir las nuevas filas
    nuevas_filas = ""
    for ref in reformas:
        nuevas_filas += _fila_reforma_xml(
            ref.get("grupo", ""),
            ref.get("codigo", ""),
            ref.get("descripcion", ""),
        )

    # Montar la nueva tabla
    nueva_tabla = f"<w:tbl>{tbl_prefix}{header_row}{nuevas_filas}</w:tbl>"

    return xml_content[:tbl_start] + nueva_tabla + xml_content[tbl_end:]


def construir_mapa_reemplazos(d):
    """
    Construye el diccionario completo de buscar→reemplazar.
    El orden importa: los textos más específicos van primero.
    Todos los accesos usan .get() para no fallar si un campo no está presente.
    """
    def g(key, default=""):
        return d.get(key, default) or default

    marca_modelo_portada = f"{g('MARCA_PORTADA')} {g('MODELO')}".strip()
    tipo_var_ver = f"{g('TIPO_VEHICULO')} / - / {g('VERSION_VEHICULO')}"
    nombre_completo = f"{g('PETICIONARIO_NOMBRE')} {g('PETICIONARIO_APELLIDOS')}".strip()

    marca_compresor  = g("MARCA_COMPRESOR",  "DRIVERITE")
    modelo_compresor = g("MODELO_COMPRESOR", "120 PSI")
    marca_balonas    = g("MARCA_BALONAS",    "FIRESTONE")
    presion_balonas  = g("PRESION_BALONAS",  "7")
    diam_tornillo    = g("DIAMETRO_TORNILLO","M14")
    fuerza_n         = g("FUERZA_CALCULO_N", "16677.00")
    peso_kit         = g("PESO_KIT_KG",      "12")
    lugar_firma      = g("LUGAR_FIRMA",      "Santa Úrsula")
    fecha_firma      = g("FECHA_FIRMA",      "")
    tara_str         = g("TARA_STR",         "")
    tara_texto       = g("TARA_TEXTO",       "")
    pct              = g("PORCENTAJE_INCREMENTO", "")

    r = {
        # ── Portada ────────────────────────────────────────────────
        "\u00abREFERENCIA\u00bb":                     g("REFERENCIA"),
        "\u00abMARCA_PORTADA\u00bb":                  g("MARCA_PORTADA") or g("MARCA"),
        "\u00abMES_ANIO\u00bb":                       g("MES_ANIO").upper(),
        "\u00abMATRICULA\u00bb":                      g("MATRICULA").upper(),

        # ── Peticionario ───────────────────────────────────────────
        "\u00abPETICIONARIO_COMPLETO\u00bb":          nombre_completo,
        "\u00abPETICIONARIO_NOMBRE\u00bb":            g("PETICIONARIO_NOMBRE"),
        "\u00abPETICIONARIO_APELLIDOS\u00bb":         g("PETICIONARIO_APELLIDOS"),
        "\u00abPROVINCIA\u00bb":                      g("PETICIONARIO_PROVINCIA"),

        # ── Datos vehículo ─────────────────────────────────────────
        "\u00abMARCA\u00bb":                          g("MARCA"),
        "\u00abMODELO\u00bb":                         g("MODELO"),
        "\u00abTIPO\u00bb":                           g("TIPO_VEHICULO"),
        "\u00abVERSION\u00bb":                        g("VERSION_VEHICULO"),
        "\u00abBASTIDOR\u00bb":                       g("NUM_BASTIDOR"),
        "\u00abVIN_FIJO\u00bb":                       g("PARTE_FIJA_VIN"),

        # ── Componentes de la reforma ──────────────────────────────
        "Compresor. Modelo: 120PSI. Marca: DRIVERITE":
            f"Compresor. Modelo: {modelo_compresor}. Marca: {marca_compresor}",
        "Balonas marca FIRESTONE de presión máxima 7 bar":
            f"Balonas marca {marca_balonas} de presión máxima {presion_balonas} bar",
        "DRIVERITE, ":                                f"{marca_compresor}, ",
        "DRIVERITE":                                  marca_compresor,
        "FIRESTONE":                                  marca_balonas,
        "120 PSI":                                    modelo_compresor,
        "7 bar":                                      f"{presion_balonas} bar",

        # ── Tornillería ────────────────────────────────────────────
        "M14":                                        diam_tornillo,

        # ── Cálculos justificativos ────────────────────────────────
        "La tara (masa en vacío) del vehículo afectado (Fiat Ducato) es de 3.005 kg.":
            f"La tara (masa en vacío) del vehículo afectado ({g('MARCA')} {g('MODELO')}) es de {tara_str} kg.",
        " El peso total del kit de balonas con compresor instalado es de aproximadamente 12 kg.":
            f" El peso total del kit de balonas con compresor instalado es de aproximadamente {peso_kit} kg.",
        " El peso del kit representa únicamente el 0,4% de la tara del vehículo.":
            f" El peso del kit representa únicamente el {pct}% de la tara del vehículo.",
        "2561 kg ":                                   f"{tara_texto} kg ",
        "x100≈ 0,4%":                                 f"x100≈ {pct}%",
        "Peso del Kit Instalado:** El peso total del kit de balonas con compresor instalado es de aproximadamente 12 kg.":
            f"Peso del Kit Instalado:** El peso total del kit de balonas con compresor instalado es de aproximadamente {peso_kit} kg.",
        "16677,00":                                   fuerza_n.replace(".", ","),

        # ── Fecha y lugar de firma ─────────────────────────────────
        "En Santa Úrsula, a 1 de Octubre de 2025":
            f"En {lugar_firma}, a {fecha_firma}",
        "En Santa Úrsula, a 1 de octubre de 2025":
            f"En {lugar_firma}, a {fecha_firma}",
        "En Santa Úrsula, a ":
            f"En {lugar_firma}, a ",
        "En Santa Úrsula, ":
            f"En {lugar_firma}, ",
        "1 de Octubre de 2025":                       fecha_firma,
        "1 de octubre de 2025":                       fecha_firma,

        # ── Ficha Reducida de Características ─────────────────────
        # Cada marcador se reemplaza con el valor del formulario,
        # o con "- -" si el campo está vacío (conserva el aspecto original).
        "\u00abCATEGORIA_CODIGO\u00bb":       g("CATEGORIA_CODIGO") or "- -",
        # Fabricante
        "\u00abFABR_BASE_A\u00bb":            g("FABR_BASE_A") or "- -",
        "\u00abFABR_BASE_D\u00bb":            g("FABR_BASE_D") or "- -",
        "\u00abFABR_ULTIMA_A\u00bb":          g("FABR_ULTIMA_A") or "- -",
        "\u00abFABR_ULTIMA_D\u00bb":          g("FABR_ULTIMA_D") or "- -",
        "\u00abEMPL_PLACA_A\u00bb":           g("EMPL_PLACA_A") or "- -",
        "\u00abEMPL_PLACA_D\u00bb":           g("EMPL_PLACA_D") or "- -",
        # Homologación e identificación
        "\u00abEMPL_VIN_A\u00bb":             g("EMPL_VIN_A") or "- -",
        "\u00abEMPL_VIN_D\u00bb":             g("EMPL_VIN_D") or "- -",
        "\u00abHOMOL_BASE_A\u00bb":           g("HOMOL_BASE_A") or "- -",
        "\u00abHOMOL_BASE_D\u00bb":           g("HOMOL_BASE_D") or "- -",
        "\u00abFECHA_HOMOL_BASE_A\u00bb":     g("FECHA_HOMOL_BASE_A") or "- -",
        "\u00abFECHA_HOMOL_BASE_D\u00bb":     g("FECHA_HOMOL_BASE_D") or "- -",
        "\u00abHOMOL_COMPL_A\u00bb":          g("HOMOL_COMPL_A") or "- -",
        "\u00abHOMOL_COMPL_D\u00bb":          g("HOMOL_COMPL_D") or "- -",
        "\u00abFECHA_HOMOL_COMPL_A\u00bb":    g("FECHA_HOMOL_COMPL_A") or "- -",
        "\u00abFECHA_HOMOL_COMPL_D\u00bb":    g("FECHA_HOMOL_COMPL_D") or "- -",
        # Constitución general
        "\u00abNUM_EJES\u00bb":               g("NUM_EJES") or "- -",
        "\u00abNUM_EJES_POST\u00bb":          g("NUM_EJES_POST") or "- -",
        "\u00abEJES_MOTR_A\u00bb":            g("EJES_MOTR_A") or "- -",
        "\u00abEJES_MOTR_D\u00bb":            g("EJES_MOTR_D") or "- -",
        # Masas y dimensiones
        "\u00abDISTANCIA_EJES\u00bb":         g("DISTANCIA_EJES") or "- -",
        "\u00abDISTANCIA_EJES_POST\u00bb":    g("DISTANCIA_EJES_POST") or "- -",
        "\u00abVIAS_EJES_A\u00bb":            g("VIAS_EJES_A") or "- -",
        "\u00abVIAS_EJES_D\u00bb":            g("VIAS_EJES_D") or "- -",
        "\u00abLONGITUD_VEH\u00bb":           g("LONGITUD_VEH") or "- -",
        "\u00abLONGITUD_VEH_POST\u00bb":      g("LONGITUD_VEH_POST") or "- -",
        "\u00abLONG_MAX_A\u00bb":             g("LONG_MAX_A") or "- -",
        "\u00abLONG_MAX_D\u00bb":             g("LONG_MAX_D") or "- -",
        "\u00abANCHURA_VEH\u00bb":            g("ANCHURA_VEH") or "- -",
        "\u00abANCHURA_VEH_POST\u00bb":       g("ANCHURA_VEH_POST") or "- -",
        "\u00abANCH_MAX_A\u00bb":             g("ANCH_MAX_A") or "- -",
        "\u00abANCH_MAX_D\u00bb":             g("ANCH_MAX_D") or "- -",
        "\u00abALTURA_VEH\u00bb":             g("ALTURA_VEH") or "- -",
        "\u00abALTURA_VEH_POST\u00bb":        g("ALTURA_VEH_POST") or "- -",
        "\u00abVOLADIZO_A\u00bb":             g("VOLADIZO_A") or "- -",
        "\u00abVOLADIZO_D\u00bb":             g("VOLADIZO_D") or "- -",
        "\u00abTARA_VEHICULO_KG\u00bb":       g("TARA_VEHICULO_KG") or "- -",
        "\u00abTARA_VEHICULO_KG_POST\u00bb":  g("TARA_VEHICULO_KG_POST") or "- -",
        "\u00abMASA_MIN_A\u00bb":             g("MASA_MIN_A") or "- -",
        "\u00abMASA_MIN_D\u00bb":             g("MASA_MIN_D") or "- -",
        "\u00abMMTA\u00bb":                   g("MMTA") or "- -",
        "\u00abMMTA_POST\u00bb":              g("MMTA_POST") or "- -",
        "\u00abMMA\u00bb":                    g("MMA") or "- -",
        "\u00abMMA_POST\u00bb":               g("MMA_POST") or "- -",
        "\u00abMMTA_EJE_A\u00bb":             g("MMTA_EJE_A") or "- -",
        "\u00abMMTA_EJE_D\u00bb":             g("MMTA_EJE_D") or "- -",
        "\u00abMMA_EJE_A\u00bb":              g("MMA_EJE_A") or "- -",
        "\u00abMMA_EJE_D\u00bb":              g("MMA_EJE_D") or "- -",
        "\u00abMMTC\u00bb":                   g("MMTC") or "- -",
        "\u00abMMTC_POST\u00bb":              g("MMTC_POST") or "- -",
        "\u00abMMA_CONJ_A\u00bb":             g("MMA_CONJ_A") or "- -",
        "\u00abMMA_CONJ_D\u00bb":             g("MMA_CONJ_D") or "- -",
        "\u00abMASA_REMOLC_A\u00bb":          g("MASA_REMOLC_A") or "- -",
        "\u00abMASA_REMOLC_D\u00bb":          g("MASA_REMOLC_D") or "- -",
        "\u00abREMOLQ_BARRA_A\u00bb":         g("REMOLQ_BARRA_A") or "- -",
        "\u00abREMOLQ_BARRA_D\u00bb":         g("REMOLQ_BARRA_D") or "- -",
        "\u00abREMOLQ_EJE_A\u00bb":           g("REMOLQ_EJE_A") or "- -",
        "\u00abREMOLQ_EJE_D\u00bb":           g("REMOLQ_EJE_D") or "- -",
        "\u00abMASA_REMOLQ_SF_A\u00bb":       g("MASA_REMOLQ_SF_A") or "- -",
        "\u00abMASA_REMOLQ_SF_D\u00bb":       g("MASA_REMOLQ_SF_D") or "- -",
        "\u00abCARGA_VERT_A\u00bb":           g("CARGA_VERT_A") or "- -",
        "\u00abCARGA_VERT_D\u00bb":           g("CARGA_VERT_D") or "- -",
        # Unidad motriz
        "\u00abFABR_MOTOR_A\u00bb":           g("FABR_MOTOR_A") or "- -",
        "\u00abFABR_MOTOR_D\u00bb":           g("FABR_MOTOR_D") or "- -",
        "\u00abCOD_MOTOR_A\u00bb":            g("COD_MOTOR_A") or "- -",
        "\u00abCOD_MOTOR_D\u00bb":            g("COD_MOTOR_D") or "- -",
        "\u00abMOTOR_COMB_A\u00bb":           g("MOTOR_COMB_A") or "- -",
        "\u00abMOTOR_COMB_D\u00bb":           g("MOTOR_COMB_D") or "- -",
        "\u00abFUNC_MOTOR_A\u00bb":           g("FUNC_MOTOR_A") or "- -",
        "\u00abFUNC_MOTOR_D\u00bb":           g("FUNC_MOTOR_D") or "- -",
        "\u00abCILINDROS_A\u00bb":            g("CILINDROS_A") or "- -",
        "\u00abCILINDROS_D\u00bb":            g("CILINDROS_D") or "- -",
        "\u00abCILINDRADA_A\u00bb":           g("CILINDRADA_A") or "- -",
        "\u00abCILINDRADA_D\u00bb":           g("CILINDRADA_D") or "- -",
        "\u00abCOMBUSTIBLE_A\u00bb":          g("COMBUSTIBLE_A") or "- -",
        "\u00abCOMBUSTIBLE_D\u00bb":          g("COMBUSTIBLE_D") or "- -",
        "\u00abPOT_NETA_A\u00bb":             g("POT_NETA_A") or "- -",
        "\u00abPOT_NETA_D\u00bb":             g("POT_NETA_D") or "- -",
        "\u00abMOTOR_ELEC_A\u00bb":           g("MOTOR_ELEC_A") or "- -",
        "\u00abMOTOR_ELEC_D\u00bb":           g("MOTOR_ELEC_D") or "- -",
        "\u00abPOT_HORA_A\u00bb":             g("POT_HORA_A") or "- -",
        "\u00abPOT_HORA_D\u00bb":             g("POT_HORA_D") or "- -",
        "\u00abMOTOR_HIBR_A\u00bb":           g("MOTOR_HIBR_A") or "- -",
        "\u00abMOTOR_HIBR_D\u00bb":           g("MOTOR_HIBR_D") or "- -",
        "\u00abTIPO_HIBR_A\u00bb":            g("TIPO_HIBR_A") or "- -",
        "\u00abTIPO_HIBR_D\u00bb":            g("TIPO_HIBR_D") or "- -",
        # Transmisión
        "\u00abTRANS_TIPO_A\u00bb":           g("TRANS_TIPO_A") or "- -",
        "\u00abTRANS_TIPO_D\u00bb":           g("TRANS_TIPO_D") or "- -",
        "\u00abCAJA_CAMB_A\u00bb":            g("CAJA_CAMB_A") or "- -",
        "\u00abCAJA_CAMB_D\u00bb":            g("CAJA_CAMB_D") or "- -",
        "\u00abNUM_RELAC_A\u00bb":            g("NUM_RELAC_A") or "- -",
        "\u00abNUM_RELAC_D\u00bb":            g("NUM_RELAC_D") or "- -",
        # Suspensión / Dirección / Frenado
        "\u00abSUSPENSION_A\u00bb":           g("SUSPENSION_A") or "- -",
        "\u00abSUSPENSION_D\u00bb":           g("SUSPENSION_D") or "- -",
        "\u00abDIRECCION_A\u00bb":            g("DIRECCION_A") or "- -",
        "\u00abDIRECCION_D\u00bb":            g("DIRECCION_D") or "- -",
        "\u00abFRENADO_A\u00bb":              g("FRENADO_A") or "- -",
        "\u00abFRENADO_D\u00bb":              g("FRENADO_D") or "- -",
        # Carrocería
        "\u00abCARROCERIA_A\u00bb":           g("CARROCERIA_A") or "- -",
        "\u00abCARROCERIA_D\u00bb":           g("CARROCERIA_D") or "- -",
        "\u00abVISION_IND_A\u00bb":           g("VISION_IND_A") or "- -",
        "\u00abVISION_IND_D\u00bb":           g("VISION_IND_D") or "- -",
        "\u00abPUERTAS_A\u00bb":              g("PUERTAS_A") or "- -",
        "\u00abPUERTAS_D\u00bb":              g("PUERTAS_D") or "- -",
        "\u00abPLAZAS_A\u00bb":               g("PLAZAS_A") or "- -",
        "\u00abPLAZAS_D\u00bb":               g("PLAZAS_D") or "- -",
        "\u00abHOMOL_CE_A\u00bb":             g("HOMOL_CE_A") or "- -",
        "\u00abHOMOL_CE_D\u00bb":             g("HOMOL_CE_D") or "- -",
        "\u00abPROT_DELT_A\u00bb":            g("PROT_DELT_A") or "- -",
        "\u00abPROT_DELT_D\u00bb":            g("PROT_DELT_D") or "- -",
        # Alumbrado
        "\u00abALUMBR_OBL_A\u00bb":           g("ALUMBR_OBL_A") or "- -",
        "\u00abALUMBR_OBL_D\u00bb":           g("ALUMBR_OBL_D") or "- -",
        "\u00abALUMBR_FAC_A\u00bb":           g("ALUMBR_FAC_A") or "- -",
        "\u00abALUMBR_FAC_D\u00bb":           g("ALUMBR_FAC_D") or "- -",
        # Varios
        "\u00abVEL_MAX_A\u00bb":              g("VEL_MAX_A") or "- -",
        "\u00abVEL_MAX_D\u00bb":              g("VEL_MAX_D") or "- -",
        "\u00abRUIDO_A\u00bb":                g("RUIDO_A") or "- -",
        "\u00abRUIDO_D\u00bb":                g("RUIDO_D") or "- -",
        "\u00abEMISIONES_A\u00bb":            g("EMISIONES_A") or "- -",
        "\u00abEMISIONES_D\u00bb":            g("EMISIONES_D") or "- -",
        "\u00abCO2_A\u00bb":                  g("CO2_A") or "- -",
        "\u00abCO2_D\u00bb":                  g("CO2_D") or "- -",
        "\u00abPOT_FISCAL_A\u00bb":           g("POT_FISCAL_A") or "- -",
        "\u00abPOT_FISCAL_D\u00bb":           g("POT_FISCAL_D") or "- -",
        "\u00abOBSERV_FICHA_A\u00bb":         g("OBSERV_FICHA_A") or "- -",
        "\u00abOBSERV_FICHA_D\u00bb":         g("OBSERV_FICHA_D") or "- -",
        "\u00abOPCIONES_HOMOL_A\u00bb":       g("OPCIONES_HOMOL_A") or "- -",
        "\u00abOPCIONES_HOMOL_D\u00bb":       g("OPCIONES_HOMOL_D") or "- -",
    }

    # Tornillo calidad (cuidado: "8,8" puede aparecer en otros contextos)
    calidad = d.get("CALIDAD_TORNILLO", "")
    if calidad:
        r["8,8"] = calidad.replace(".", ",")

    # Eliminar entradas donde el valor de reemplazo sea cadena vacía
    # (evita borrar texto de la plantilla si el campo no se rellenó)
    r = {k: v for k, v in r.items() if v and v != k}

    return r


def _aplanar_calculos(datos):
    """
    Los campos definidos en bloques de cálculo (CALCULOS[i].campos) se suben
    al nivel raíz para que construir_mapa_reemplazos los encuentre con d['KEY'].
    Los campos ya presentes en el nivel raíz NO se sobreescriben.
    También resuelve alias de nombres entre formulario y plantilla.
    """
    for bloque in datos.get("CALCULOS", []):
        for k, v in bloque.get("campos", {}).items():
            if k not in datos and not k.startswith("_SEP_"):
                datos[k] = v

    # Alias: el formulario usa PRESION_BALONAS_BAR, la plantilla busca PRESION_BALONAS
    if "PRESION_BALONAS" not in datos:
        datos["PRESION_BALONAS"] = datos.get("PRESION_BALONAS_BAR", "7")

    return datos


def generar(json_path):
    # 1. Cargar datos
    with open(json_path, "r", encoding="utf-8") as f:
        datos = json.load(f)

    # 1b. Extraer cálculos incrustados en cada item de reforma
    calculos_incrustados = []
    for r in datos.get("REFORMAS", []):
        cod = r.get("codigo", "")
        for item in r.get("reformas", []):
            calc = item.get("calculo")
            if calc and calc.get("tipo") and calc["tipo"] != "— Sin cálculo —":
                ref = f"CR {cod}"
                if item.get("titulo"):
                    ref += f" — {item['titulo']}"
                calculos_incrustados.append({
                    "reforma_ref": ref,
                    "tipo":        calc["tipo"],
                    "campos":      calc.get("campos", {}),
                })
    if calculos_incrustados:
        datos.setdefault("CALCULOS", [])
        datos["CALCULOS"] = calculos_incrustados + datos["CALCULOS"]

    # 1c. Normalizar reformas al formato plano
    if "REFORMAS" in datos:
        datos["REFORMAS"] = _normalizar_reformas(datos["REFORMAS"])

    # 1c. Aplanar campos de bloques de cálculo al nivel raíz
    datos = _aplanar_calculos(datos)

    # 2. Calcular campos derivados
    datos = calcular_campos(datos)

    # 3. Verificar que existe la plantilla
    if not TEMPLATE_DOCX.exists():
        print(f"[ERROR] No se encuentra la plantilla base: {TEMPLATE_DOCX}")
        print("        Copia el archivo original como PLANTILLA_BASE.docx")
        sys.exit(1)

    # 4. Crear carpeta de salida con estructura de revisiones
    #    REFERENCIA "PH.007/2026-0" → carpeta base "PH.007-2026", revisión 0
    #    Salida: proyectos_generados/PH.007-2026/Rev0/PR_PH.007-2026-0_MAT.docx
    OUTPUT_DIR.mkdir(exist_ok=True)
    ref_raw = datos.get("REFERENCIA", "SIN_REF")
    _m_ref = re.match(r"([A-Za-z]+\.\d+)[/\-](\d{4})-(\d+)", ref_raw)
    if _m_ref:
        base_carpeta = f"{_m_ref.group(1)}-{_m_ref.group(2)}"   # PH.007-2026
        rev_num      = int(_m_ref.group(3))                       # 0, 1, 2…
    else:
        base_carpeta = ref_raw.replace("/", "-").replace(" ", "_")
        rev_num      = 0

    rev_dir = OUTPUT_DIR / base_carpeta / f"Rev{rev_num}"
    rev_dir.mkdir(parents=True, exist_ok=True)

    # 5. Preparar nombre del fichero de salida
    ref_clean  = ref_raw.replace("/", "-").replace(" ", "_")
    mat        = datos.get("MATRICULA", "").upper()
    output_name = f"PR_{ref_clean}_{mat}.docx"
    output_path = rev_dir / output_name

    # Guardar datos del formulario para poder generar revisiones futuras
    datos_json_path = rev_dir / "datos.json"
    with open(datos_json_path, "w", encoding="utf-8") as _fj:
        json.dump(datos, _fj, ensure_ascii=False, indent=2)

    # 6. Desempaquetar plantilla en carpeta temporal del sistema
    tmp_dir = Path(tempfile.mkdtemp(prefix="phican_reforma_"))

    # PYTHONIOENCODING=utf-8 evita errores con caracteres especiales en Windows
    env_utf8 = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

    result = subprocess.run(
        [sys.executable, str(SKILLS_DIR / "unpack.py"),
         str(TEMPLATE_DOCX), str(tmp_dir)],
        capture_output=True, text=True, encoding="utf-8", env=env_utf8
    )
    if result.returncode != 0:
        print(f"[ERROR] Al desempaquetar: {result.stderr}")
        sys.exit(1)
    print("[OK] Plantilla desempaquetada")

    # 6b. Corregir referencias rotas a plantilla .dotx (común en documentos copiados)
    settings_rels = tmp_dir / "word" / "_rels" / "settings.xml.rels"
    settings_xml  = tmp_dir / "word" / "settings.xml"
    if settings_rels.exists():
        content = settings_rels.read_text(encoding="utf-8")
        if "attachedTemplate" in content or "dotx" in content:
            settings_rels.write_text(
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
                '</Relationships>\n',
                encoding="utf-8"
            )
    if settings_xml.exists():
        content = settings_xml.read_text(encoding="utf-8")
        if "attachedTemplate" in content:
            import re as _re
            content = _re.sub(r'<w:attachedTemplate[^/]*/>', '', content)
            settings_xml.write_text(content, encoding="utf-8")

    # 7. Construir mapa de reemplazos y aplicar al document.xml
    mapa = construir_mapa_reemplazos(datos)
    doc_xml_path = tmp_dir / "word" / "document.xml"

    with open(doc_xml_path, "r", encoding="utf-8") as f:
        contenido = f.read()

    contenido_nuevo = reemplazar_en_xml(contenido, mapa)

    reformas = datos.get("REFORMAS", [])
    calculos = datos.get("CALCULOS", [])

    if reformas:
        # Tabla de actos reglamentarios (§1.2, tabla Grupo|Código|Descripción)
        contenido_nuevo = reemplazar_tabla_reformas(contenido_nuevo, reformas)

        # Bloque descriptivo de §1.2 ANTECEDENTES
        contenido_nuevo = reemplazar_seccion_12(contenido_nuevo, reformas, calculos)

        # Bloque descriptivo de §1.5.2 Variaciones y sustituciones
        contenido_nuevo = reemplazar_seccion_152(contenido_nuevo, reformas, calculos)

        # Tabla de directivas: generar dinámicamente desde DIRECTIVAS_DOC
        directivas_doc = datos.get("DIRECTIVAS_DOC", [])
        contenido_nuevo = generar_tabla_directivas(contenido_nuevo, directivas_doc)

    with open(doc_xml_path, "w", encoding="utf-8") as f:
        f.write(contenido_nuevo)

    # 8. Reempaquetar (sin validación de schema: el XML se genera manualmente)
    result = subprocess.run(
        [sys.executable, str(SKILLS_DIR / "pack.py"),
         str(tmp_dir), str(output_path),
         "--original", str(TEMPLATE_DOCX),
         "--validate", "false"],
        capture_output=True, text=True, encoding="utf-8", env=env_utf8
    )
    if result.returncode != 0:
        detalle = (result.stderr or result.stdout or "sin detalle").strip()
        print(f"[ERROR] Al reempaquetar: {detalle}")
        sys.exit(1)

    # 9. Limpiar temporales (ignorar errores de permisos)
    try:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception:
        pass

    print(f"\n[OK] Proyecto generado correctamente:")
    print(f"   {output_path}\n")
    return str(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python generar_proyecto.py datos_proyecto.json")
        sys.exit(1)
    generar(sys.argv[1])
