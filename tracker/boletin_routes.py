"""
Rutas Flask para la gestión de Boletines (eléctrico, gas, fontanería).
"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from db import (
    init_boletines_db, BOLETIN_PREFIJOS, siguiente_numero_boletin,
    crear_boletin, listar_boletines, get_boletin, actualizar_boletin, eliminar_boletin,
    actualizar_datos_json,
)
import json
import os
import sys
from pathlib import Path

# Añadir la raíz del proyecto al path para importar generar_boletin_electrico
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

bol_bp = Blueprint("bol", __name__, url_prefix="/boletines")


@bol_bp.before_request
def _init():
    init_boletines_db()


# ── Lista ────────────────────────────────────────────────────────────────────
@bol_bp.route("/")
def lista():
    tipo   = request.args.get("tipo", "")
    estado = request.args.get("estado", "")
    texto  = request.args.get("q", "")
    boletines = listar_boletines(
        tipo=tipo or None,
        estado=estado or None,
        texto=texto or None,
    )
    return render_template(
        "boletines_lista.html",
        boletines=boletines,
        prefijos=BOLETIN_PREFIJOS,
        filtro_tipo=tipo,
        filtro_estado=estado,
        filtro_texto=texto,
    )


# ── Nuevo ────────────────────────────────────────────────────────────────────
@bol_bp.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    if request.method == "POST":
        tipo = request.form.get("tipo", "electrico_local")
        bid, numero = crear_boletin(
            tipo=tipo,
            peticionario=request.form.get("peticionario", ""),
            nif=request.form.get("nif", ""),
            direccion=request.form.get("direccion", ""),
            poblacion=request.form.get("poblacion", ""),
            cp=request.form.get("cp", ""),
            tecnico=request.form.get("tecnico", ""),
            expediente_id=request.form.get("expediente_id") or None,
            oferta_id=int(request.form["oferta_id"]) if request.form.get("oferta_id") else None,
            observaciones=request.form.get("observaciones", ""),
        )
        flash(f"Boletín {numero} creado correctamente.", "success")
        # Redirigir al detalle de la oferta si venía de ella
        if request.form.get("oferta_id"):
            return redirect(url_for("crm.oferta_detalle", oid=request.form["oferta_id"]))
        return redirect(url_for("bol.detalle", bid=bid))

    # Pre-fill si viene en la URL (ej: desde oferta CRM o formulario vehículo)
    tipo_presel      = request.args.get("tipo", "electrico_local")
    expediente_presel = request.args.get("expediente_id", "")
    oferta_id_presel  = request.args.get("oferta_id", "")
    siguiente_nums   = {t: siguiente_numero_boletin(t) for t in BOLETIN_PREFIJOS}
    return render_template(
        "boletines_nuevo.html",
        prefijos=BOLETIN_PREFIJOS,
        tipo_presel=tipo_presel,
        expediente_presel=expediente_presel,
        oferta_id_presel=oferta_id_presel,
        siguiente_nums=siguiente_nums,
    )


# ── Detalle / Edición ────────────────────────────────────────────────────────
@bol_bp.route("/<int:bid>")
def detalle(bid):
    bol = get_boletin(bid)
    if not bol:
        flash("Boletín no encontrado.", "danger")
        return redirect(url_for("bol.lista"))

    # Parsear datos_json para el template
    datos_json = {}
    raw = bol.get("datos_json") or "{}"
    if isinstance(raw, str):
        try:
            datos_json = json.loads(raw)
        except Exception:
            datos_json = {}

    # Verificar si los documentos ya fueron generados
    carpeta = bol.get("carpeta") or ""
    cie_numero = datos_json.get("CIE_NUMERO") or bol.get("numero", "")
    mtd_path = ""
    cie_path = ""
    if carpeta and os.path.isdir(carpeta):
        candidate_mtd = os.path.join(carpeta, f"MTD_{cie_numero}.docx")
        # CIE es ahora un PDF oficial rellenado
        candidate_cie = os.path.join(carpeta, f"CIE_{cie_numero}.pdf")
        if os.path.isfile(candidate_mtd):
            mtd_path = candidate_mtd
        if os.path.isfile(candidate_cie):
            cie_path = candidate_cie

    return render_template(
        "boletines_detalle.html",
        bol=bol,
        prefijos=BOLETIN_PREFIJOS,
        datos_json=datos_json,
        mtd_path=mtd_path,
        cie_path=cie_path,
    )


@bol_bp.route("/<int:bid>/editar", methods=["GET", "POST"])
def editar(bid):
    bol = get_boletin(bid)
    if not bol:
        return redirect(url_for("bol.lista"))
    if request.method == "POST":
        actualizar_boletin(
            bid,
            peticionario=request.form.get("peticionario", ""),
            nif=request.form.get("nif", ""),
            direccion=request.form.get("direccion", ""),
            poblacion=request.form.get("poblacion", ""),
            cp=request.form.get("cp", ""),
            tecnico=request.form.get("tecnico", ""),
            estado=request.form.get("estado", "borrador"),
            observaciones=request.form.get("observaciones", ""),
        )
        flash("Boletín actualizado.", "success")
        return redirect(url_for("bol.detalle", bid=bid))
    return render_template("boletines_editar.html", bol=bol, prefijos=BOLETIN_PREFIJOS)


@bol_bp.route("/<int:bid>/estado", methods=["POST"])
def cambiar_estado(bid):
    nuevo_estado = request.form.get("estado", "borrador")
    actualizar_boletin(bid, estado=nuevo_estado)
    return redirect(url_for("bol.detalle", bid=bid))


@bol_bp.route("/<int:bid>/eliminar", methods=["POST"])
def eliminar(bid):
    eliminar_boletin(bid)
    flash("Boletín eliminado.", "warning")
    return redirect(url_for("bol.lista"))


@bol_bp.route("/<int:bid>/abrir-carpeta")
def abrir_carpeta(bid):
    bol = get_boletin(bid)
    if bol and bol["carpeta"] and os.path.isdir(bol["carpeta"]):
        os.startfile(bol["carpeta"])
    return jsonify({"ok": True})


# ── Generar documentos MTD + CIE ─────────────────────────────────────────────
@bol_bp.route("/<int:bid>/generar", methods=["POST"])
def generar(bid):
    try:
        from generar_boletin_electrico import generar_boletin_docs
        resultado = generar_boletin_docs(bid)
        return jsonify(resultado)
    except Exception as e:
        import traceback
        return jsonify({"ok": False, "error": str(e), "traceback": traceback.format_exc()}), 500


@bol_bp.route("/<int:bid>/abrir-mtd")
def abrir_mtd(bid):
    bol = get_boletin(bid)
    if not bol:
        return jsonify({"ok": False, "error": "Boletín no encontrado"}), 404
    datos_json = {}
    raw = bol.get("datos_json") or "{}"
    try:
        datos_json = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        pass
    cie_numero = datos_json.get("CIE_NUMERO") or bol.get("numero", "")
    carpeta = bol.get("carpeta") or ""
    mtd_file = os.path.join(carpeta, f"MTD_{cie_numero}.docx") if carpeta else ""
    if mtd_file and os.path.isfile(mtd_file):
        os.startfile(mtd_file)
        return jsonify({"ok": True, "path": mtd_file})
    return jsonify({"ok": False, "error": "Archivo MTD no encontrado. Genera primero el documento."}), 404


@bol_bp.route("/<int:bid>/abrir-cie")
def abrir_cie(bid):
    bol = get_boletin(bid)
    if not bol:
        return jsonify({"ok": False, "error": "Boletín no encontrado"}), 404
    datos_json = {}
    raw = bol.get("datos_json") or "{}"
    try:
        datos_json = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        pass
    cie_numero = datos_json.get("CIE_NUMERO") or bol.get("numero", "")
    carpeta = bol.get("carpeta") or ""
    cie_file = os.path.join(carpeta, f"CIE_{cie_numero}.pdf") if carpeta else ""
    if cie_file and os.path.isfile(cie_file):
        os.startfile(cie_file)
        return jsonify({"ok": True, "path": cie_file})
    return jsonify({"ok": False, "error": "Archivo CIE no encontrado. Genera primero el documento."}), 404


# ── Guardar datos técnicos (datos_json) ──────────────────────────────────────
@bol_bp.route("/<int:bid>/datos-tecnicos", methods=["POST"])
def guardar_datos_tecnicos(bid):
    bol = get_boletin(bid)
    if not bol:
        return jsonify({"ok": False, "error": "Boletín no encontrado"}), 404

    # Campos técnicos esperados del formulario
    campos = [
        "CIE_NUMERO", "CIE_EXPEDIENTE",
        "TITULAR_NOMBRE", "TITULAR_APELLIDOS", "TITULAR_DNI",
        "TITULAR_TELEFONO", "TITULAR_EMAIL",
        "VEH_MARCA", "VEH_TIPO", "VEH_DENOMINACION", "VEH_BASTIDOR", "VEH_MATRICULA",
        "POT_NOMINAL", "POT_PICO_CAMPO", "TENSION_NOMINAL",
        "P_PREVISTA", "P_INSTALADA", "P_CONTRATADA", "TENSION",
        "DERIVACION_CU", "ACOMETIDA_BT",
        "GEN_FABRICANTE", "GEN_MODELO", "GEN_POT_PICO", "GEN_NUM_MODULOS",
        "COND_NATURALEZA_CC", "COND_AISLAMIENTO_CC", "COND_CLASE_CC", "COND_SECCION_CC",
        "ALUM_DENOMINACION", "ALUM_POTENCIA", "FUERZA_DENOMINACION", "FUERZA_POTENCIA",
        "POT_TOTAL",
        "CALC_LONGITUD", "CALC_MATERIAL", "CALC_INTENSIDAD",
        "CALC_CAIDA_PCT", "CALC_CAIDA_V", "CALC_TENSION", "CALC_SECCION",
        "PROT_IGA", "PROT_MAGNETO", "PROT_SOBRETENCION", "PROT_DIFERENCIAL",
        "PROT_IGA_ICC", "PROT_MAGNETO_ICC", "PROT_SOBRETENCION_CAT", "PROT_DIFERENCIAL_MA",
        "MED_PAT", "MED_AISLAMIENTO",
        "EMP_DISTRIBUIDORA", "OBJETIVO", "DOCS_TECNICOS",
        "EMPLAZAMIENTO_DIRECCION", "EMPLAZAMIENTO_NUM", "EMPLAZAMIENTO_PORTAL",
        "EMPLAZAMIENTO_TM", "EMPLAZAMIENTO_CP", "EMPLAZAMIENTO_ISLA",
        "EMPLAZAMIENTO_USO", "EMPLAZAMIENTO_SUPERFICIE", "EMPLAZAMIENTO_PLANTAS",
        "LINEA_GENERAL",
        "TEC_NOMBRE", "TEC_APELLIDOS", "TEC_DOMICILIO", "TEC_TELEFONO",
        "TEC_EMAIL", "TEC_NUM_COLEGIADO", "TEC_COLEGIO",
        "LUGAR_FIRMA", "DIA_FIRMA", "MES_FIRMA", "ANIO_FIRMA",
        "OBSERVACIONES", "OBSERVACIONES_L1", "OBSERVACIONES_L2", "OBSERVACIONES_L3", "OBSERVACIONES_L4",
    ]

    if request.is_json:
        payload = request.get_json(silent=True) or {}
    else:
        payload = {k: request.form.get(k, "") for k in campos}

    datos_extra = {k: v for k, v in payload.items() if k in campos}
    actualizar_datos_json(bid, datos_extra)

    return jsonify({"ok": True})


# ── API: siguiente número ────────────────────────────────────────────────────
@bol_bp.route("/plantilla-cie", methods=["POST"])
def crear_plantilla_cie():
    """Genera/actualiza la plantilla CIE con los datos fijos de empresa desde config.json."""
    try:
        from generar_boletin_electrico import generar_plantilla_cie
        import json as _json
        config_path = _ROOT / "config.json"
        config = {}
        if config_path.exists():
            with open(config_path, encoding="utf-8") as f:
                config = _json.load(f)
        out = generar_plantilla_cie(config=config)
        return jsonify({"ok": True, "plantilla": str(out)})
    except Exception as e:
        import traceback
        return jsonify({"ok": False, "error": str(e), "traceback": traceback.format_exc()}), 500


@bol_bp.route("/api/siguiente-numero")
def api_siguiente_numero():
    tipo = request.args.get("tipo", "electrico_local")
    return jsonify({"numero": siguiente_numero_boletin(tipo)})


# ── API: boletines vinculados a un expediente ────────────────────────────────
@bol_bp.route("/api/por-expediente")
def api_por_expediente():
    expediente_id = request.args.get("expediente_id", "")
    if not expediente_id:
        return jsonify([])
    init_boletines_db()
    from db import query
    rows = query(
        "SELECT id, numero, tipo, estado, fecha FROM boletines WHERE expediente_id = ? ORDER BY id DESC",
        (expediente_id,)
    )
    return jsonify([dict(r) for r in (rows or [])])
