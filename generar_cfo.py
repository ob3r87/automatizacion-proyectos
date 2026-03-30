#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================
  GENERADOR DE CERTIFICADO FINAL DE OBRA (CFO)
  Phican Ingenieros

  Uso:
    python generar_cfo.py datos_proyecto.json

  Genera CFO_{ref}_{mat}.docx en la misma carpeta Rev{N}
  que el proyecto correspondiente.
=============================================================
"""

import sys
import os
import io
import json
import shutil
import re
import struct
import subprocess
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR   = Path(__file__).parent
SKILLS_DIR   = SCRIPT_DIR / "scripts" / "office"
TEMPLATE_CFO = Path(os.environ.get("PHICAN_TEMPLATE_CFO", "") or (SCRIPT_DIR / "PLANTILLA_CFO.docx"))
OUTPUT_DIR   = Path(os.environ.get("PHICAN_OUTPUT_DIR", "") or (SCRIPT_DIR / "proyectos_generados"))

# ── Meses en español ──────────────────────────────────────
_MESES_ES = {
    "enero": "ENERO", "febrero": "FEBRERO", "marzo": "MARZO",
    "abril": "ABRIL", "mayo": "MAYO", "junio": "JUNIO",
    "julio": "JULIO", "agosto": "AGOSTO", "septiembre": "SEPTIEMBRE",
    "octubre": "OCTUBRE", "noviembre": "NOVIEMBRE", "diciembre": "DICIEMBRE",
}


def _xml_escape(text):
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _fecha_condensada(fecha_es):
    """
    Convierte '28 de noviembre de 2025' → '28NOVIEMBRE 2025'
    (formato usado en algunos CFO).
    """
    m = re.match(r"(\d+)\s+de\s+(\w+)\s+de\s+(\d+)", fecha_es, re.IGNORECASE)
    if m:
        day   = m.group(1)
        month = m.group(2).lower()
        year  = m.group(3)
        return f"{day}{_MESES_ES.get(month, month.upper())} {year}"
    return fecha_es


# ══════════════════════════════════════════════════════════════════════════════
# ── Soporte de fotografías ────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

# Tamaño máximo de imagen por columna (2 columnas por fila)
_MAX_IMG_CX = 2_700_000   # ≈ 7.5 cm  (EMU: 1 cm = 360 000)
_MAX_IMG_CY = 3_600_000   # ≈ 10 cm

_NS_WP  = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
_NS_A   = "http://schemas.openxmlformats.org/drawingml/2006/main"
_NS_PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"
_NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_TYPE_IMG = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"


def _get_image_size_px(path):
    """
    Devuelve (ancho_px, alto_px) sin dependencias externas.
    Soporta JPEG, PNG y BMP.  Fallback: (1200, 900).
    """
    try:
        ext = Path(path).suffix.lower()
        with open(path, "rb") as f:
            raw = f.read(65536)

        if ext in (".jpg", ".jpeg"):
            i = 2
            while i + 4 <= len(raw):
                if raw[i] != 0xFF:
                    break
                mk = raw[i + 1]
                if mk in (0xC0, 0xC1, 0xC2, 0xC3):
                    h, w = struct.unpack(">HH", raw[i + 5: i + 9])
                    return w, h
                ln = struct.unpack(">H", raw[i + 2: i + 4])[0]
                i += 2 + ln
        elif ext == ".png":
            if len(raw) >= 24:
                w, h = struct.unpack(">II", raw[16:24])
                return w, h
        elif ext == ".bmp":
            if len(raw) >= 26:
                w = struct.unpack("<I", raw[18:22])[0]
                h = abs(struct.unpack("<i", raw[22:26])[0])
                return w, h
    except Exception:
        pass
    return 1200, 900


def _calcular_emu(w_px, h_px, max_cx=_MAX_IMG_CX, max_cy=_MAX_IMG_CY):
    """Calcula (cx, cy) en EMU manteniendo la relación de aspecto."""
    if h_px == 0:
        h_px = 1
    aspect = w_px / h_px
    cx = max_cx
    cy = int(cx / aspect)
    if cy > max_cy:
        cy = max_cy
        cx = int(cy * aspect)
    return cx, cy


def _drawing_run_xml(rid, pic_id, name, cx, cy):
    """Genera el <w:r><w:drawing>...</w:drawing></w:r> para una imagen inline."""
    return (
        f"<w:r><w:drawing>"
        f'<wp:inline xmlns:wp="{_NS_WP}" distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx}" cy="{cy}"/>'
        f'<wp:effectExtent l="19050" t="0" r="0" b="0"/>'
        f'<wp:docPr id="{pic_id}" name="{name}"/>'
        f"<wp:cNvGraphicFramePr>"
        f'<a:graphicFrameLocks xmlns:a="{_NS_A}" noChangeAspect="1"/>'
        f"</wp:cNvGraphicFramePr>"
        f'<a:graphic xmlns:a="{_NS_A}">'
        f'<a:graphicData uri="{_NS_PIC}">'
        f'<pic:pic xmlns:pic="{_NS_PIC}">'
        f"<pic:nvPicPr>"
        f'<pic:cNvPr id="0" name="{name}"/>'
        f"<pic:cNvPicPr/>"
        f"</pic:nvPicPr>"
        f"<pic:blipFill>"
        f'<a:blip xmlns:r="{_NS_REL}" r:embed="{rid}"/>'
        f"<a:stretch><a:fillRect/></a:stretch>"
        f"</pic:blipFill>"
        f'<pic:spPr bwMode="auto">'
        f'<a:xfrm xmlns:a="{_NS_A}">'
        f'<a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/>'
        f"</a:xfrm>"
        f'<a:prstGeom xmlns:a="{_NS_A}" prst="rect"><a:avLst/></a:prstGeom>'
        f"</pic:spPr>"
        f"</pic:pic>"
        f"</a:graphicData>"
        f"</a:graphic>"
        f"</wp:inline>"
        f"</w:drawing></w:r>"
    )


def _foto_p_xml(rid, pic_id, name, cx, cy):
    """Párrafo centrado que contiene la imagen."""
    return (
        f"<w:p>"
        f"<w:pPr>"
        f'<w:jc w:val="center"/>'
        f'<w:spacing w:before="0" w:after="60"/>'
        f"</w:pPr>"
        f"{_drawing_run_xml(rid, pic_id, name, cx, cy)}"
        f"</w:p>"
    )


def _caption_p_xml(text):
    """Párrafo de leyenda centrado en cursiva pequeña."""
    t = _xml_escape(text)
    return (
        f"<w:p>"
        f"<w:pPr>"
        f'<w:jc w:val="center"/>'
        f'<w:spacing w:before="0" w:after="200"/>'
        f"</w:pPr>"
        f"<w:r>"
        f"<w:rPr><w:i/><w:sz w:val=\"18\"/><w:szCs w:val=\"18\"/></w:rPr>"
        f'<w:t xml:space="preserve">{t}</w:t>'
        f"</w:r>"
        f"</w:p>"
    )


def _heading_p_xml(texto):
    """Párrafo de encabezado de sección (negrita, centrado)."""
    t = _xml_escape(texto)
    return (
        f"<w:p>"
        f"<w:pPr>"
        f'<w:jc w:val="center"/>'
        f'<w:spacing w:before="360" w:after="120"/>'
        f"</w:pPr>"
        f"<w:r>"
        f'<w:rPr><w:b/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr>'
        f"<w:t>{t}</w:t>"
        f"</w:r>"
        f"</w:p>"
    )


def _fotos_tabla_xml(fotos_info):
    """
    Tabla de 2 columnas con foto + leyenda por celda.
    fotos_info: lista de dicts {rid, pic_id, name, cx, cy, caption}.
    """
    COL = 4680   # twips por columna ≈ 8.27 cm

    encabezado = (
        f"<w:tblPr>"
        f'<w:tblW w:w="0" w:type="auto"/>'
        f"<w:tblBorders>"
        f'<w:top w:val="none"/><w:left w:val="none"/>'
        f'<w:bottom w:val="none"/><w:right w:val="none"/>'
        f'<w:insideH w:val="none"/><w:insideV w:val="none"/>'
        f"</w:tblBorders>"
        f"<w:tblCellMar>"
        f'<w:left w:w="144" w:type="dxa"/>'
        f'<w:right w:w="144" w:type="dxa"/>'
        f"</w:tblCellMar>"
        f"</w:tblPr>"
        f"<w:tblGrid>"
        f'<w:gridCol w:w="{COL}"/>'
        f'<w:gridCol w:w="{COL}"/>'
        f"</w:tblGrid>"
    )

    def celda(info):
        if info is None:
            return (
                f"<w:tc>"
                f'<w:tcPr><w:tcW w:w="{COL}" w:type="dxa"/></w:tcPr>'
                f"<w:p/>"
                f"</w:tc>"
            )
        return (
            f"<w:tc>"
            f'<w:tcPr><w:tcW w:w="{COL}" w:type="dxa"/></w:tcPr>'
            f"{_foto_p_xml(info['rid'], info['pic_id'], info['name'], info['cx'], info['cy'])}"
            f"{_caption_p_xml(info['caption'])}"
            f"</w:tc>"
        )

    filas = []
    for i in range(0, len(fotos_info), 2):
        c1 = celda(fotos_info[i])
        c2 = celda(fotos_info[i + 1] if i + 1 < len(fotos_info) else None)
        filas.append(
            f"<w:tr>"
            f"<w:trPr><w:trHeight w:val=\"0\" w:hRule=\"auto\"/></w:trPr>"
            f"{c1}{c2}"
            f"</w:tr>"
        )

    return f"<w:tbl>{encabezado}{''.join(filas)}</w:tbl>"


def insertar_fotos(xml_content, fotos, tmp_dir):
    """
    Copia las imágenes al DOCX desempaquetado, actualiza las relaciones y
    el [Content_Types].xml, y añade un bloque 'FOTOGRAFÍAS' al documento.

    fotos: lista de {"path": str, "caption": str}
    Devuelve el xml_content actualizado.
    """
    fotos_validas = [
        f for f in fotos
        if f.get("path") and Path(f["path"]).is_file()
    ]
    if not fotos_validas:
        return xml_content

    media_dir = tmp_dir / "word" / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    # ── [Content_Types].xml — asegurar extensiones de imagen ─────────────────
    ct_path = tmp_dir / "[Content_Types].xml"
    if ct_path.exists():
        ct = ct_path.read_text(encoding="utf-8")
        for ext, mime in [
            ("jpeg", "image/jpeg"), ("jpg", "image/jpeg"),
            ("png",  "image/png"),  ("bmp", "image/bmp"),
        ]:
            if f'Extension="{ext}"' not in ct:
                ct = ct.replace(
                    "</Types>",
                    f'<Default Extension="{ext}" ContentType="{mime}"/></Types>',
                )
        ct_path.write_text(ct, encoding="utf-8")

    # ── word/_rels/document.xml.rels — añadir relaciones de imagen ───────────
    rels_path = tmp_dir / "word" / "_rels" / "document.xml.rels"
    if rels_path.exists():
        rels = rels_path.read_text(encoding="utf-8")
    else:
        rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            "</Relationships>"
        )

    fotos_info = []
    for i, foto in enumerate(fotos_validas, start=1):
        src = Path(foto["path"])
        ext = src.suffix.lower()
        dst_name = f"imageCFO{i}{ext}"
        shutil.copy2(str(src), str(media_dir / dst_name))

        rid = f"rIdFOTO{i}"
        if rid not in rels:
            rels = rels.replace(
                "</Relationships>",
                f'<Relationship Id="{rid}" Type="{_TYPE_IMG}" Target="media/{dst_name}"/>\n'
                f"</Relationships>",
            )

        w_px, h_px = _get_image_size_px(str(src))
        cx, cy = _calcular_emu(w_px, h_px)
        fotos_info.append({
            "rid":     rid,
            "pic_id":  i,
            "name":    f"FotoCFO{i}",
            "cx":      cx,
            "cy":      cy,
            "caption": foto.get("caption", ""),
        })

    rels_path.write_text(rels, encoding="utf-8")

    # ── Generar bloque XML ────────────────────────────────────────────────────
    bloque = _heading_p_xml("FOTOGRAFÍAS") + _fotos_tabla_xml(fotos_info)

    # ── Encontrar punto de inserción ──────────────────────────────────────────
    # Opción 1: marcador «FOTOS_CFO» en el documento
    marcador = "\u00abFOTOS_CFO\u00bb"
    if marcador in xml_content:
        for m in re.finditer(r"<w:p\b.*?</w:p>", xml_content, re.DOTALL):
            texts = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>",
                                       m.group(0), re.DOTALL))
            if marcador in texts:
                return xml_content[: m.start()] + bloque + xml_content[m.end():]

    # Opción 2: insertar antes del último <w:p> de <w:body>
    body_end = xml_content.rfind("</w:body>")
    if body_end < 0:
        return xml_content + bloque

    zona = xml_content[:body_end]
    last_p = max(zona.rfind("<w:p "), zona.rfind("<w:p>"))
    if last_p < 0:
        return zona + bloque + xml_content[body_end:]

    return xml_content[:last_p] + bloque + xml_content[last_p:]


def reemplazar_parrafos(xml_content, mapa):
    """
    Reemplaza texto en el XML trabajando párrafo a párrafo.

    Para cada <w:p> concatena el contenido de todos los <w:t> y comprueba
    si alguna clave del mapa aparece en el texto combinado.  Si hay
    coincidencia, el PRIMER <w:t> del párrafo recibe el texto completo
    ya reemplazado y los demás <w:t> se vacían — el resto de la estructura
    del párrafo (pPr, rPr, hyperlinks, fields, etc.) se conserva intacta
    para no generar XML inválido.

    El mapa se ordena por longitud de clave descendente para evitar que
    cadenas cortas enmascaren a las largas.
    """
    sorted_mapa = sorted(mapa.items(), key=lambda x: -len(x[0]))

    partes  = []
    pos_fin = 0

    for m in re.finditer(r"<w:p\b.*?</w:p>", xml_content, re.DOTALL):
        p_xml   = m.group(0)
        p_ini   = m.start()
        p_fin   = m.end()

        # Texto completo del párrafo (concatenación de todos los <w:t>)
        textos = re.findall(r"<w:t[^>]*>(.*?)</w:t>", p_xml, re.DOTALL)
        texto  = "".join(textos)

        nuevo_texto = texto
        modificado  = False
        for buscar, nuevo in sorted_mapa:
            if buscar in nuevo_texto:
                nuevo_texto = nuevo_texto.replace(buscar, str(nuevo))
                modificado  = True

        if modificado:
            t_esc  = _xml_escape(nuevo_texto)
            primer = [True]

            def _sub_t(mt, _t=t_esc, _p=primer):
                if _p[0]:
                    _p[0] = False
                    return f'<w:t xml:space="preserve">{_t}</w:t>'
                return "<w:t></w:t>"

            nuevo_p = re.sub(r"<w:t[^>]*>.*?</w:t>", _sub_t, p_xml,
                             flags=re.DOTALL)
            partes.append(xml_content[pos_fin:p_ini])
            partes.append(nuevo_p)
            pos_fin = p_fin

    partes.append(xml_content[pos_fin:])
    return "".join(partes)


def _normalizar_reformas(reformas):
    resultado = []
    for r in reformas:
        base  = {"codigo": r.get("codigo", ""), "grupo": r.get("grupo", ""),
                 "descripcion": r.get("descripcion", "")}
        items = r.get("reformas", [])
        if not items:
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


def construir_mapa_cfo(datos):
    """
    Mapa de sustitución: texto literal de la plantilla → valor del formulario.
    Los textos de la plantilla son los valores originales del documento base
    (CF.014/2025-0, Miryam Ester..., Roberto García..., etc.).
    Edita este mapa cuando actualices la plantilla CFO.
    """
    def g(key, default=""):
        return datos.get(key, default) or default

    # ── Referencias ───────────────────────────────────────────────────────────
    ref_proyecto = g("REFERENCIA")
    _m = re.match(r"[A-Za-z]+\.(\d+)[/\-](\d{4})-(\d+)", ref_proyecto)
    if _m:
        num, anio, rev = _m.group(1), _m.group(2), _m.group(3)
        ref_cfo  = f"CF.{num}/{anio}-{rev}"       # CF.014/2025-0
        ref_ph   = f"PH_{num}/{anio}-{rev}"        # PH_014/2025-0  (con guion bajo)
        ref_ph2  = f"PH.{num}/{anio}-{rev}"        # PH.014/2025-0  (con punto)
    else:
        ref_cfo  = ref_proyecto
        ref_ph   = ref_proyecto.replace("PH.", "PH_")
        ref_ph2  = ref_proyecto

    # ── Personas ──────────────────────────────────────────────────────────────
    peticionario = f"{g('PETICIONARIO_NOMBRE')} {g('PETICIONARIO_APELLIDOS')}".strip()
    tecnico      = g("TECNICO_NOMBRE")

    # ── Fechas ────────────────────────────────────────────────────────────────
    fecha_completa  = g("FECHA_FIRMA")                     # "28 de noviembre de 2025"
    fecha_condensada = _fecha_condensada(fecha_completa)   # "28NOVIEMBRE 2025"
    fecha_upper      = fecha_completa.upper()              # "28 DE NOVIEMBRE DE 2025"

    return {
        # ── Plantilla: valores originales ─────────────────────────────────────
        # Referencias (de más específico a más general)
        "CF.014/2025-0":                              ref_cfo,
        "PH_014/2025-0":                              ref_ph,
        "PH.014/2025-0":                              ref_ph2,
        # Peticionario
        "Miryam Ester Chávez Rodríguez":              peticionario,
        "Miryam Ester Ch\u00e1vez Rodr\u00edguez":   peticionario,
        # Técnico
        "Roberto Garc\u00eda Guti\u00e9rrez":         tecnico,
        "Roberto García Gutiérrez":                   tecnico,
        # Colegio
        "Ilustre Colegio Oficial de Ingenieros T\u00e9cnicos de S/C de Tenerife":
            g("TECNICO_COLEGIO"),
        "Ilustre Colegio Oficial de Ingenieros Técnicos de S/C de Tenerife":
            g("TECNICO_COLEGIO"),
        "COITI S/C de Tenerife":                      g("TECNICO_COLEGIO_ABREV"),
        # Número de colegiado
        "1816":                                       g("TECNICO_NUM_COLEGIADO"),
        # Fechas (de más específico a más general)
        fecha_condensada if fecha_condensada != fecha_completa else "__NO_MATCH__":
            fecha_condensada,
        "28NOVIEMBRE 2025":                           fecha_condensada,
        "28 DE NOVIEMBRE DE 2025":                    fecha_upper,
        "28 de noviembre de 2025":                    fecha_completa,
        # Vehículo — ajustar si la plantilla usa valores distintos
        "Fiat Ducato":       f"{g('MARCA')} {g('MODELO')}".strip() or "Fiat Ducato",
    }


def generar_cfo(json_path):
    # 1. Cargar datos
    with open(json_path, "r", encoding="utf-8") as f:
        datos = json.load(f)

    if "REFORMAS" in datos:
        datos["REFORMAS"] = _normalizar_reformas(datos["REFORMAS"])

    # 2. Verificar plantilla
    if not TEMPLATE_CFO.exists():
        print(f"[ERROR] No se encuentra la plantilla CFO: {TEMPLATE_CFO}")
        sys.exit(1)

    # 3. Crear carpeta de salida (misma estructura que generar_proyecto.py)
    OUTPUT_DIR.mkdir(exist_ok=True)
    ref_raw = datos.get("REFERENCIA", "SIN_REF")
    _m_ref  = re.match(r"([A-Za-z]+\.\d+)[/\-](\d{4})-(\d+)", ref_raw)
    if _m_ref:
        base_carpeta = f"{_m_ref.group(1)}-{_m_ref.group(2)}"
        rev_num      = int(_m_ref.group(3))
    else:
        base_carpeta = ref_raw.replace("/", "-").replace(" ", "_")
        rev_num      = 0

    rev_dir = OUTPUT_DIR / base_carpeta / f"Rev{rev_num}"
    rev_dir.mkdir(parents=True, exist_ok=True)

    ref_clean   = ref_raw.replace("/", "-").replace(" ", "_")
    mat         = datos.get("MATRICULA", "").upper()
    output_name = f"CFO_{ref_clean}_{mat}.docx"
    output_path = rev_dir / output_name

    # 4. Desempaquetar plantilla
    tmp_dir  = Path(tempfile.mkdtemp(prefix="phican_cfo_"))
    env_utf8 = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

    result = subprocess.run(
        [sys.executable, str(SKILLS_DIR / "unpack.py"),
         str(TEMPLATE_CFO), str(tmp_dir)],
        capture_output=True, text=True, encoding="utf-8", env=env_utf8
    )
    if result.returncode != 0:
        print(f"[ERROR] Al desempaquetar CFO: {result.stderr}")
        sys.exit(1)
    print("[OK] Plantilla CFO desempaquetada")

    # 5. Aplicar reemplazos al document.xml
    mapa         = construir_mapa_cfo(datos)
    doc_xml_path = tmp_dir / "word" / "document.xml"

    with open(doc_xml_path, "r", encoding="utf-8") as f:
        contenido = f.read()

    contenido = reemplazar_parrafos(contenido, mapa)

    # 5b. Insertar fotografías (si las hay)
    fotos = datos.get("FOTOS_CFO", [])
    if fotos:
        contenido = insertar_fotos(contenido, fotos, tmp_dir)
        print(f"[OK] {len([f for f in fotos if f.get('path')])} fotografía(s) insertada(s)")

    with open(doc_xml_path, "w", encoding="utf-8") as f:
        f.write(contenido)

    # 6. Reempaquetar
    result = subprocess.run(
        [sys.executable, str(SKILLS_DIR / "pack.py"),
         str(tmp_dir), str(output_path),
         "--original", str(TEMPLATE_CFO),
         "--validate", "false"],
        capture_output=True, text=True, encoding="utf-8", env=env_utf8
    )
    if result.returncode != 0:
        detalle = (result.stderr or result.stdout or "sin detalle").strip()
        print(f"[ERROR] Al reempaquetar CFO: {detalle}")
        sys.exit(1)

    # 7. Limpiar temporales
    shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"\n[OK] CFO generado correctamente:\n   {output_path}\n")
    return str(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python generar_cfo.py datos_proyecto.json")
        sys.exit(1)
    generar_cfo(sys.argv[1])
