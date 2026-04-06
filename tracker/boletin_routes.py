"""
Rutas Flask para la gestión de Boletines (eléctrico, gas, fontanería).
"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from db import (
    init_boletines_db, BOLETIN_PREFIJOS, siguiente_numero_boletin,
    crear_boletin, listar_boletines, get_boletin, actualizar_boletin, eliminar_boletin,
)
import os

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
    return render_template("boletines_detalle.html", bol=bol, prefijos=BOLETIN_PREFIJOS)


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


# ── API: siguiente número ────────────────────────────────────────────────────
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
