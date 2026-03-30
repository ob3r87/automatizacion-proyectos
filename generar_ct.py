#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================
  GENERADOR DE CERTIFICADO DE TALLER (CT)
  Phican Ingenieros

  Uso:
    python generar_ct.py datos_proyecto.json

  Genera CT_{ref}_{mat}.docx en la misma carpeta Rev{N}
  que el proyecto correspondiente.
=============================================================
"""

import sys
import os
import io
import json
import shutil
import re
import subprocess
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR  = Path(__file__).parent
SKILLS_DIR  = SCRIPT_DIR / "scripts" / "office"
TEMPLATE_CT = Path(os.environ.get("PHICAN_TEMPLATE_CT", "") or (SCRIPT_DIR / "PLANTILLA_CT.docx"))
OUTPUT_DIR  = Path(os.environ.get("PHICAN_OUTPUT_DIR", "") or (SCRIPT_DIR / "proyectos_generados"))

# ── Meses en español ──────────────────────────────────────
_MESES_ES = {
    "enero": "enero", "febrero": "febrero", "marzo": "marzo",
    "abril": "abril", "mayo": "mayo", "junio": "junio",
    "julio": "julio", "agosto": "agosto", "septiembre": "septiembre",
    "octubre": "octubre", "noviembre": "noviembre", "diciembre": "diciembre",
}


def _xml_escape(text):
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


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


def construir_mapa_ct(datos):
    """
    Mapa de sustitución: texto literal de la plantilla → valor del formulario.
    Los textos de la plantilla son los valores originales del documento base
    (Pedro Pablo Pacheco Cruz, Santa Úrsula, etc.).
    Edita este mapa cuando actualices la plantilla CT.
    """
    def g(key, default=""):
        return datos.get(key, default) or default

    # ── Referencias ───────────────────────────────────────────────────────────
    ref_proyecto = g("REFERENCIA")
    _m = re.match(r"[A-Za-z]+\.(\d+)[/\-](\d{4})-(\d+)", ref_proyecto)
    if _m:
        num, anio, rev = _m.group(1), _m.group(2), _m.group(3)
        ref_ph  = f"PH_{num}/{anio}-{rev}"    # PH_014/2025-0  (guion bajo)
        ref_ph2 = f"PH.{num}/{anio}-{rev}"    # PH.014/2025-0  (punto)
    else:
        ref_ph  = ref_proyecto.replace("PH.", "PH_")
        ref_ph2 = ref_proyecto

    # ── Taller ────────────────────────────────────────────────────────────────
    titular       = g("TALLER_TITULAR")
    titular_pref  = f"D. {titular}." if titular else ""   # "D. Nombre Apellidos."

    # ── Técnico ───────────────────────────────────────────────────────────────
    tecnico      = g("TECNICO_NOMBRE")
    num_colegiado = g("TECNICO_NUM_COLEGIADO")

    # ── Fechas ────────────────────────────────────────────────────────────────
    fecha = g("FECHA_FIRMA")   # "27 de noviembre de 2025"

    return {
        # ── Taller (orden: más específico primero) ────────────────────────────
        "D. Pedro Pablo Pacheco Cruz.":         titular_pref or "D. Pedro Pablo Pacheco Cruz.",
        "Pedro Pablo Pacheco Cruz":             titular or "Pedro Pablo Pacheco Cruz",
        "Pedro Pablo Pacheco":                  g("TALLER_TITULAR", "Pedro Pablo Pacheco"),
        # Datos del taller
        "Calle San Bartolom\u00e9, N.\u00ba 19": g("TALLER_CALLE"),
        "Calle San Bartolomé, N.º 19":          g("TALLER_CALLE"),
        "Santa \u00dasula":                     g("TALLER_LOCALIDAD"),
        "Santa Úrsula":                         g("TALLER_LOCALIDAD"),
        "38399":                                g("TALLER_CP"),
        "Santa Cruz de Tenerife":               g("TALLER_PROVINCIA"),
        "922 30 12 72":                         g("TALLER_TELEFONO"),
        "Reparaci\u00f3n de Veh\u00edculos":    g("TALLER_ACTIVIDAD"),
        "Reparación de Vehículos":              g("TALLER_ACTIVIDAD"),
        "05-A-452-38013889":                    g("TALLER_REG_INDUSTRIAL"),
        # ── Técnico ───────────────────────────────────────────────────────────
        "Roberto Garc\u00eda Guti\u00e9rrez":  tecnico,
        "Roberto García Gutiérrez":             tecnico,
        "COITITF":                              g("TECNICO_COLEGIO_ABREV"),
        "1816":                                 num_colegiado,
        # ── Referencias ───────────────────────────────────────────────────────
        "PH_014/2025-0":                        ref_ph,
        "PH.014/2025-0":                        ref_ph2,
        # ── Fecha ─────────────────────────────────────────────────────────────
        "27 de noviembre de 2025":              fecha,
        "28 de noviembre de 2025":              fecha,
    }


def generar_ct(json_path):
    # 1. Cargar datos
    with open(json_path, "r", encoding="utf-8") as f:
        datos = json.load(f)

    if "REFORMAS" in datos:
        datos["REFORMAS"] = _normalizar_reformas(datos["REFORMAS"])

    # 2. Verificar plantilla
    if not TEMPLATE_CT.exists():
        print(f"[ERROR] No se encuentra la plantilla CT: {TEMPLATE_CT}")
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
    output_name = f"CT_{ref_clean}_{mat}.docx"
    output_path = rev_dir / output_name

    # 4. Desempaquetar plantilla
    tmp_dir  = Path(tempfile.mkdtemp(prefix="phican_ct_"))
    env_utf8 = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}

    result = subprocess.run(
        [sys.executable, str(SKILLS_DIR / "unpack.py"),
         str(TEMPLATE_CT), str(tmp_dir)],
        capture_output=True, text=True, encoding="utf-8", env=env_utf8
    )
    if result.returncode != 0:
        print(f"[ERROR] Al desempaquetar CT: {result.stderr}")
        sys.exit(1)
    print("[OK] Plantilla CT desempaquetada")

    # 5. Aplicar reemplazos al document.xml
    mapa         = construir_mapa_ct(datos)
    doc_xml_path = tmp_dir / "word" / "document.xml"

    with open(doc_xml_path, "r", encoding="utf-8") as f:
        contenido = f.read()

    contenido = reemplazar_parrafos(contenido, mapa)

    with open(doc_xml_path, "w", encoding="utf-8") as f:
        f.write(contenido)

    # 6. Reempaquetar
    result = subprocess.run(
        [sys.executable, str(SKILLS_DIR / "pack.py"),
         str(tmp_dir), str(output_path),
         "--original", str(TEMPLATE_CT),
         "--validate", "false"],
        capture_output=True, text=True, encoding="utf-8", env=env_utf8
    )
    if result.returncode != 0:
        detalle = (result.stderr or result.stdout or "sin detalle").strip()
        print(f"[ERROR] Al reempaquetar CT: {detalle}")
        sys.exit(1)

    # 7. Limpiar temporales
    shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"\n[OK] CT generado correctamente:\n   {output_path}\n")
    return str(output_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python generar_ct.py datos_proyecto.json")
        sys.exit(1)
    generar_ct(sys.argv[1])
