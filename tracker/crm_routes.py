# -*- coding: utf-8 -*-
"""
Blueprint Flask para el CRM de Phican Ingenieros.
Gestión de clientes, ofertas/presupuestos y tipos de trabajo.
"""
import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from flask import (Blueprint, render_template, request, redirect,
                   url_for, jsonify, send_file, flash)

from db import query, execute, get_db, init_crm_db, init_work_types_defaults

import json as _json_mod
_CODIGOS_REFORMA = {}
try:
    _cr_path = Path(__file__).parent / "codigos_reforma.json"
    if _cr_path.exists():
        _CODIGOS_REFORMA = _json_mod.loads(_cr_path.read_text(encoding="utf-8"))
except Exception:
    pass

# Nombres de grupos de reforma
GRUPOS_REFORMA = {
    "1": "Identificación", "2": "Unidad motriz", "3": "Transmisión",
    "4": "Ejes y ruedas", "5": "Dirección", "6": "Frenos",
    "7": "Carrocería", "8": "Masas y dimensiones", "9": "Acoplamiento",
    "10": "Accesorios y equipos", "11": "Otras modificaciones"
}


# Tarifa HOV por número de actos reglamentarios
def _precio_hov(n_actos: int) -> float:
    if n_actos <= 0:
        return 650.0
    if n_actos == 1:
        return 650.0
    if n_actos == 2:
        return 750.0
    if n_actos == 3:
        return 900.0
    return 900.0 + (n_actos - 3) * 120.0


crm_bp = Blueprint("crm", __name__, url_prefix="/crm")

BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent


# ─── Utilidades ──────────────────────────────────────────────────

def _now():
    return datetime.now().isoformat()


def _today_iso():
    return datetime.now().date().isoformat()


def _fmt_date_es(iso_str):
    """ISO → DD/MM/YYYY."""
    if not iso_str:
        return ""
    try:
        return datetime.fromisoformat(iso_str[:10]).strftime("%d/%m/%Y")
    except Exception:
        return iso_str


def _get_output_path():
    """Lee OUTPUT_PATH desde config.json en la raíz del proyecto."""
    config_path = PROJECT_ROOT / "config.json"
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                cfg = json.load(f)
            return cfg.get("OUTPUT_PATH", str(PROJECT_ROOT / "proyectos_generados"))
        except Exception:
            pass
    return str(PROJECT_ROOT / "proyectos_generados")


def siguiente_referencia_oferta():
    """Genera la siguiente referencia en formato PR.NNN/YYYY."""
    year = datetime.now().year
    row = query(
        "SELECT referencia FROM offers WHERE referencia LIKE ? ORDER BY id DESC LIMIT 1",
        (f"PR.%/{year}",),
        one=True,
    )
    if row:
        try:
            num = int(row["referencia"].split(".")[1].split("/")[0])
            num += 1
        except Exception:
            num = 1
    else:
        num = 1
    return f"PR.{num:03d}/{year}"


def _calcular_totales(lines, descuento_pct, iva_pct, irpf_pct=15):
    subtotal = sum(float(l.get("cantidad", 1)) * float(l.get("precio_unitario", 0))
                   for l in lines)
    descuento_pct = float(descuento_pct or 0)
    iva_pct       = float(iva_pct or 7)
    irpf_pct      = float(irpf_pct if irpf_pct is not None else 15)
    descuento  = subtotal * descuento_pct / 100
    base       = subtotal - descuento
    iva        = base * iva_pct / 100
    irpf       = base * irpf_pct / 100          # retención — se resta al total a cobrar
    total      = base + iva - irpf
    return {
        "subtotal":   subtotal,
        "descuento":  descuento,
        "base":       base,
        "iva":        iva,
        "irpf":       irpf,
        "total":      total,         # lo que cobra el profesional
        "total_bruto": base + iva,   # lo que paga el cliente (sin retención visible)
    }


def _oferta_total(offer_id):
    lines = query("SELECT * FROM offer_lines WHERE offer_id = ?", (offer_id,))
    oferta = query("SELECT * FROM offers WHERE id = ?", (offer_id,), one=True)
    if not oferta:
        return 0.0
    tots = _calcular_totales(lines, oferta.get("descuento_pct", 0),
                             oferta.get("iva_pct", 7), oferta.get("irpf_pct", 15))
    return tots["total"]


# ─── Dashboard CRM ───────────────────────────────────────────────

@crm_bp.route("/")
def dashboard():
    # KPIs
    total_ofertas = query("SELECT COUNT(*) as c FROM offers", one=True)["c"]
    pendientes = query("SELECT COUNT(*) as c FROM offers WHERE status IN ('borrador','enviado','pendiente')", one=True)["c"]

    mes_ini = datetime.now().replace(day=1).date().isoformat()
    aceptadas_mes = query(
        "SELECT COUNT(*) as c FROM offers WHERE status='aceptado' AND fecha_respuesta >= ?",
        (mes_ini,), one=True,
    )["c"]

    # Importe aceptado este mes (aproximado con suma de líneas)
    ofertas_acept_mes = query(
        "SELECT id, descuento_pct, iva_pct FROM offers WHERE status='aceptado' AND fecha_respuesta >= ?",
        (mes_ini,),
    )
    importe_mes = 0.0
    for o in ofertas_acept_mes:
        importe_mes += _oferta_total(o["id"])

    enviadas = query("SELECT COUNT(*) as c FROM offers WHERE status IN ('enviado','pendiente','aceptado','rechazado')", one=True)["c"]
    tasa = round(aceptadas_mes / max(enviadas, 1) * 100, 1) if enviadas else 0

    # Ofertas por estado para kanban
    estados = ["borrador", "enviado", "pendiente", "aceptado", "rechazado"]
    kanban = {}
    for est in estados:
        ofertas_est = query(
            """SELECT o.*, c.nombre as cliente_nombre
               FROM offers o LEFT JOIN clients c ON o.client_id = c.id
               WHERE o.status = ? ORDER BY o.created_at DESC LIMIT 20""",
            (est,),
        )
        for of in ofertas_est:
            of["total"] = _oferta_total(of["id"])
        kanban[est] = ofertas_est

    # Últimas 10 ofertas
    ultimas = query(
        """SELECT o.*, c.nombre as cliente_nombre
           FROM offers o LEFT JOIN clients c ON o.client_id = c.id
           ORDER BY o.created_at DESC LIMIT 10""",
    )
    for of in ultimas:
        of["total"] = _oferta_total(of["id"])

    return render_template(
        "crm_dashboard.html",
        total_ofertas=total_ofertas,
        pendientes=pendientes,
        aceptadas_mes=aceptadas_mes,
        importe_mes=importe_mes,
        tasa_conversion=tasa,
        kanban=kanban,
        ultimas=ultimas,
        fmt_date=_fmt_date_es,
    )


# ─── Clientes ────────────────────────────────────────────────────

@crm_bp.route("/clientes")
def clientes_lista():
    clientes = query("SELECT * FROM clients ORDER BY nombre")
    # Contar ofertas por cliente
    for c in clientes:
        cnt = query("SELECT COUNT(*) as n FROM offers WHERE client_id = ?", (c["id"],), one=True)
        c["n_ofertas"] = cnt["n"] if cnt else 0
    return render_template("crm_clientes.html", clientes=clientes)


@crm_bp.route("/clientes/nuevo", methods=["GET", "POST"])
def cliente_nuevo():
    if request.method == "POST":
        now = _now()
        cid = execute(
            """INSERT INTO clients
               (nombre, empresa, email, telefono, nif, direccion, ciudad, cp, notas,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                request.form.get("nombre", "").strip(),
                request.form.get("empresa", "").strip(),
                request.form.get("email", "").strip(),
                request.form.get("telefono", "").strip(),
                request.form.get("nif", "").strip(),
                request.form.get("direccion", "").strip(),
                request.form.get("ciudad", "").strip(),
                request.form.get("cp", "").strip(),
                request.form.get("notas", "").strip(),
                now, now,
            ),
        )
        flash("Cliente creado correctamente.", "success")
        next_url = request.args.get("next")
        if next_url:
            return redirect(next_url)
        return redirect(url_for("crm.clientes_lista"))

    return render_template("crm_cliente_form.html", cliente=None)


@crm_bp.route("/clientes/<int:cid>/editar", methods=["GET", "POST"])
def cliente_editar(cid):
    cliente = query("SELECT * FROM clients WHERE id = ?", (cid,), one=True)
    if not cliente:
        flash("Cliente no encontrado.", "danger")
        return redirect(url_for("crm.clientes_lista"))

    if request.method == "POST":
        now = _now()
        execute(
            """UPDATE clients SET
               nombre=?, empresa=?, email=?, telefono=?, nif=?,
               direccion=?, ciudad=?, cp=?, notas=?, updated_at=?
               WHERE id=?""",
            (
                request.form.get("nombre", "").strip(),
                request.form.get("empresa", "").strip(),
                request.form.get("email", "").strip(),
                request.form.get("telefono", "").strip(),
                request.form.get("nif", "").strip(),
                request.form.get("direccion", "").strip(),
                request.form.get("ciudad", "").strip(),
                request.form.get("cp", "").strip(),
                request.form.get("notas", "").strip(),
                now, cid,
            ),
        )
        flash("Cliente actualizado correctamente.", "success")
        return redirect(url_for("crm.clientes_lista"))

    return render_template("crm_cliente_form.html", cliente=cliente)


@crm_bp.route("/clientes/<int:cid>", methods=["DELETE"])
def cliente_eliminar(cid):
    n_ofertas = query("SELECT COUNT(*) as n FROM offers WHERE client_id = ?", (cid,), one=True)
    if n_ofertas and n_ofertas["n"] > 0:
        return jsonify({"error": "El cliente tiene ofertas asociadas. Elimínalas primero."}), 409
    execute("DELETE FROM clients WHERE id = ?", (cid,))
    return jsonify({"ok": True})


# ─── Ofertas ─────────────────────────────────────────────────────

@crm_bp.route("/ofertas")
def ofertas_lista():
    status_filter = request.args.get("status", "")
    year_filter = request.args.get("year", "")

    sql = """SELECT o.*, c.nombre as cliente_nombre
             FROM offers o LEFT JOIN clients c ON o.client_id = c.id
             WHERE 1=1"""
    params = []
    if status_filter:
        sql += " AND o.status = ?"
        params.append(status_filter)
    if year_filter:
        sql += " AND o.referencia LIKE ?"
        params.append(f"%/{year_filter}")
    sql += " ORDER BY o.created_at DESC"

    ofertas = query(sql, params)
    for of in ofertas:
        of["total"] = _oferta_total(of["id"])

    years = query("SELECT DISTINCT substr(referencia, -4) as yr FROM offers ORDER BY yr DESC")
    years = [r["yr"] for r in years if r["yr"]]

    return render_template(
        "crm_ofertas.html",
        ofertas=ofertas,
        status_filter=status_filter,
        year_filter=year_filter,
        years=years,
        fmt_date=_fmt_date_es,
    )


@crm_bp.route("/ofertas/nueva", methods=["GET", "POST"])
def oferta_nueva():
    if request.method == "POST":
        return _guardar_oferta(None)

    clientes = query("SELECT * FROM clients ORDER BY nombre")
    work_types = query("SELECT * FROM work_types WHERE activo=1 ORDER BY codigo")
    referencia = siguiente_referencia_oferta()
    return render_template(
        "crm_oferta_form.html",
        oferta=None,
        lines=[],
        clientes=clientes,
        work_types=work_types,
        referencia=referencia,
        hov_data=None,
        codigos_reforma=_CODIGOS_REFORMA,
    )


@crm_bp.route("/ofertas/<int:oid>")
def oferta_detalle(oid):
    oferta = query(
        """SELECT o.*, c.nombre as cliente_nombre, c.empresa as cliente_empresa,
                  c.email as cliente_email, c.telefono as cliente_telefono,
                  c.nif as cliente_nif, c.direccion as cliente_direccion,
                  c.ciudad as cliente_ciudad, c.cp as cliente_cp
           FROM offers o LEFT JOIN clients c ON o.client_id = c.id
           WHERE o.id = ?""",
        (oid,), one=True,
    )
    if not oferta:
        flash("Oferta no encontrada.", "danger")
        return redirect(url_for("crm.ofertas_lista"))

    lines = query("SELECT * FROM offer_lines WHERE offer_id = ? ORDER BY orden", (oid,))
    historial = query("SELECT * FROM offer_history WHERE offer_id = ? ORDER BY fecha DESC", (oid,))
    totals = _calcular_totales(lines, oferta.get("descuento_pct", 0),
                               oferta.get("iva_pct", 7), oferta.get("irpf_pct", 15))

    hov_data = None
    if oferta.get("tipo_trabajo") == "HOV":
        hov_data = query("SELECT * FROM offer_hov_data WHERE offer_id=?", (oid,), one=True)
        if hov_data and hov_data.get("actos_reglamentarios"):
            try:
                hov_data["actos_lista"] = _json_mod.loads(hov_data["actos_reglamentarios"])
            except Exception:
                hov_data["actos_lista"] = []

    return render_template(
        "crm_oferta_detalle.html",
        oferta=oferta,
        lines=lines,
        historial=historial,
        totals=totals,
        fmt_date=_fmt_date_es,
        hov_data=hov_data,
        codigos_reforma=_CODIGOS_REFORMA,
    )


@crm_bp.route("/ofertas/<int:oid>/editar", methods=["GET", "POST"])
def oferta_editar(oid):
    oferta = query("SELECT * FROM offers WHERE id = ?", (oid,), one=True)
    if not oferta:
        flash("Oferta no encontrada.", "danger")
        return redirect(url_for("crm.ofertas_lista"))

    if request.method == "POST":
        return _guardar_oferta(oid)

    clientes = query("SELECT * FROM clients ORDER BY nombre")
    work_types = query("SELECT * FROM work_types WHERE activo=1 ORDER BY codigo")
    lines = query("SELECT * FROM offer_lines WHERE offer_id = ? ORDER BY orden", (oid,))
    hov_data = query("SELECT * FROM offer_hov_data WHERE offer_id=?", (oid,), one=True) if oferta.get("tipo_trabajo") == "HOV" else None
    if hov_data and hov_data.get("actos_reglamentarios"):
        try:
            hov_data["actos_lista"] = _json_mod.loads(hov_data["actos_reglamentarios"])
        except Exception:
            hov_data["actos_lista"] = []
    return render_template(
        "crm_oferta_form.html",
        oferta=oferta,
        lines=lines,
        clientes=clientes,
        work_types=work_types,
        referencia=oferta["referencia"],
        hov_data=hov_data,
        codigos_reforma=_CODIGOS_REFORMA,
    )


def _guardar_oferta(oid):
    """Lógica compartida para crear/editar oferta con sus líneas."""
    f = request.form
    now = _now()

    client_id = f.get("client_id") or None
    if client_id:
        client_id = int(client_id)

    validez = int(f.get("validez_dias", 30) or 30)
    fecha_creacion = f.get("fecha_creacion") or _today_iso()
    fecha_venc = f.get("fecha_vencimiento", "")
    if not fecha_venc and fecha_creacion:
        try:
            d = datetime.fromisoformat(fecha_creacion)
            fecha_venc = (d + timedelta(days=validez)).date().isoformat()
        except Exception:
            fecha_venc = ""

    if oid is None:
        referencia = f.get("referencia") or siguiente_referencia_oferta()
        new_oid = execute(
            """INSERT INTO offers
               (referencia, client_id, titulo, tipo_trabajo, descripcion, status,
                fecha_creacion, fecha_vencimiento, validez_dias,
                descuento_pct, iva_pct, irpf_pct, notas_internas, notas_cliente,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                referencia,
                client_id,
                f.get("titulo", "").strip(),
                f.get("tipo_trabajo", "").strip(),
                f.get("descripcion", "").strip(),
                f.get("status", "borrador"),
                fecha_creacion,
                fecha_venc,
                validez,
                float(f.get("descuento_pct", 0) or 0),
                float(f.get("iva_pct", 7) or 7),
                float(f.get("irpf_pct", 15) or 15),
                f.get("notas_internas", "").strip(),
                f.get("notas_cliente", "").strip(),
                now, now,
            ),
        )
        oid = new_oid
    else:
        execute(
            """UPDATE offers SET
               client_id=?, titulo=?, tipo_trabajo=?, descripcion=?,
               fecha_vencimiento=?, validez_dias=?,
               descuento_pct=?, iva_pct=?, irpf_pct=?, notas_internas=?, notas_cliente=?,
               updated_at=?
               WHERE id=?""",
            (
                client_id,
                f.get("titulo", "").strip(),
                f.get("tipo_trabajo", "").strip(),
                f.get("descripcion", "").strip(),
                fecha_venc,
                validez,
                float(f.get("descuento_pct", 0) or 0),
                float(f.get("iva_pct", 7) or 7),
                float(f.get("irpf_pct", 15) or 15),
                f.get("notas_internas", "").strip(),
                f.get("notas_cliente", "").strip(),
                now, oid,
            ),
        )
        execute("DELETE FROM offer_lines WHERE offer_id = ?", (oid,))

    # Guardar líneas
    conceptos = f.getlist("concepto[]")
    descs = f.getlist("descripcion_linea[]")
    cantidades = f.getlist("cantidad[]")
    precios = f.getlist("precio_unitario[]")

    for i, concepto in enumerate(conceptos):
        if not concepto.strip():
            continue
        execute(
            """INSERT INTO offer_lines (offer_id, orden, concepto, descripcion, cantidad, precio_unitario)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                oid,
                i,
                concepto.strip(),
                descs[i] if i < len(descs) else "",
                float(cantidades[i]) if i < len(cantidades) and cantidades[i] else 1.0,
                float(precios[i]) if i < len(precios) and precios[i] else 0.0,
            ),
        )

    # Guardar datos HOV si aplica
    if f.get("tipo_trabajo") == "HOV":
        actos = f.getlist("actos_reglamentarios[]")
        actos_json = _json_mod.dumps(actos)
        n_actos = len(actos)
        hov_campos = {
            "marca": f.get("hov_marca", ""), "modelo": f.get("hov_modelo", ""),
            "tipo_vehiculo": f.get("hov_tipo_vehiculo", ""),
            "matricula": f.get("hov_matricula", ""), "bastidor": f.get("hov_bastidor", ""),
            "categoria": f.get("hov_categoria", ""),
            "anio_matriculacion": f.get("hov_anio", ""),
            "actos_reglamentarios": actos_json, "n_actos": n_actos,
            "mma_antes": f.get("hov_mma_antes", ""), "mma_despues": f.get("hov_mma_despues", ""),
            "tara_antes": f.get("hov_tara_antes", ""), "tara_despues": f.get("hov_tara_despues", ""),
            "plazas_antes": f.get("hov_plazas_antes", ""), "plazas_despues": f.get("hov_plazas_despues", ""),
            "longitud_antes": f.get("hov_longitud_antes", ""), "longitud_despues": f.get("hov_longitud_despues", ""),
            "anchura_antes": f.get("hov_anchura_antes", ""), "anchura_despues": f.get("hov_anchura_despues", ""),
            "altura_antes": f.get("hov_altura_antes", ""), "altura_despues": f.get("hov_altura_despues", ""),
            "mmta_antes": f.get("hov_mmta_antes", ""), "mmta_despues": f.get("hov_mmta_despues", ""),
            "mma_eje_antes": f.get("hov_mma_eje_antes", ""), "mma_eje_despues": f.get("hov_mma_eje_despues", ""),
            "potencia_antes": f.get("hov_potencia_antes", ""), "potencia_despues": f.get("hov_potencia_despues", ""),
            "cilindrada_antes": f.get("hov_cilindrada_antes", ""), "cilindrada_despues": f.get("hov_cilindrada_despues", ""),
            "combustible_antes": f.get("hov_combustible_antes", ""), "combustible_despues": f.get("hov_combustible_despues", ""),
            "vel_max_antes": f.get("hov_vel_max_antes", ""), "vel_max_despues": f.get("hov_vel_max_despues", ""),
            "notas_tecnicas": f.get("hov_notas_tecnicas", ""),
        }
        existing = query("SELECT id FROM offer_hov_data WHERE offer_id=?", (oid,), one=True)
        if existing:
            sets = ", ".join(f"{k}=?" for k in hov_campos)
            vals = list(hov_campos.values()) + [oid]
            execute(f"UPDATE offer_hov_data SET {sets} WHERE offer_id=?", vals)
        else:
            keys = ", ".join(hov_campos.keys())
            phs = ", ".join("?" for _ in hov_campos)
            execute(f"INSERT INTO offer_hov_data (offer_id, {keys}) VALUES (?, {phs})",
                    [oid] + list(hov_campos.values()))

    flash("Oferta guardada correctamente.", "success")
    return redirect(url_for("crm.oferta_detalle", oid=oid))


@crm_bp.route("/ofertas/<int:oid>/estado", methods=["POST"])
def oferta_cambiar_estado(oid):
    data = request.get_json() or {}
    nuevo_status = data.get("status", "")
    notas = data.get("notas", "")

    oferta = query("SELECT * FROM offers WHERE id = ?", (oid,), one=True)
    if not oferta:
        return jsonify({"error": "Oferta no encontrada"}), 404

    status_anterior = oferta["status"]
    now = _now()
    today = _today_iso()

    campos_extra = ""
    params_extra = []

    if nuevo_status == "enviado" or nuevo_status == "pendiente":
        campos_extra = ", fecha_envio=?"
        params_extra.append(today)
    elif nuevo_status in ("aceptado", "rechazado"):
        campos_extra = ", fecha_respuesta=?"
        params_extra.append(today)

    execute(
        f"UPDATE offers SET status=?{campos_extra}, updated_at=? WHERE id=?",
        [nuevo_status] + params_extra + [now, oid],
    )

    execute(
        """INSERT INTO offer_history (offer_id, status_anterior, status_nuevo, fecha, notas)
           VALUES (?, ?, ?, ?, ?)""",
        (oid, status_anterior, nuevo_status, now, notas),
    )

    # Lógica especial al aceptar
    if nuevo_status == "aceptado":
        referencia = oferta["referencia"].replace("/", "-")
        output_path = _get_output_path()
        carpeta_dest = Path(output_path) / "PRESUPUESTOS" / referencia
        carpeta_dest.mkdir(parents=True, exist_ok=True)

        pdf_path = oferta.get("pdf_path", "")
        if pdf_path and Path(pdf_path).is_file():
            shutil.copy2(pdf_path, str(carpeta_dest / Path(pdf_path).name))

        return jsonify({"ok": True, "carpeta": str(carpeta_dest)})

    return jsonify({"ok": True})


@crm_bp.route("/ofertas/<int:oid>/pdf")
def oferta_pdf(oid):
    from pdf_generator import generar_pdf_oferta

    oferta = query("SELECT * FROM offers WHERE id = ?", (oid,), one=True)
    if not oferta:
        return jsonify({"error": "Oferta no encontrada"}), 404

    client_data = {}
    if oferta.get("client_id"):
        c = query("SELECT * FROM clients WHERE id = ?", (oferta["client_id"],), one=True)
        if c:
            client_data = dict(c)

    lines = query("SELECT * FROM offer_lines WHERE offer_id = ? ORDER BY orden", (oid,))

    # Directorio de PDFs
    pdf_dir = BASE_DIR / "pdfs"
    pdf_dir.mkdir(exist_ok=True)
    ref_safe = oferta["referencia"].replace("/", "-").replace(".", "_")
    pdf_path = str(pdf_dir / f"presupuesto_{ref_safe}.pdf")

    generar_pdf_oferta(dict(oferta), [dict(l) for l in lines], client_data, pdf_path)

    # Actualizar ruta en BD
    execute("UPDATE offers SET pdf_path=?, updated_at=? WHERE id=?", (pdf_path, _now(), oid))

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"Presupuesto_{oferta['referencia'].replace('/', '-')}.pdf",
        mimetype="application/pdf",
    )


@crm_bp.route("/ofertas/<int:oid>/duplicar", methods=["POST"])
def oferta_duplicar(oid):
    oferta = query("SELECT * FROM offers WHERE id = ?", (oid,), one=True)
    if not oferta:
        return jsonify({"error": "Oferta no encontrada"}), 404

    now = _now()
    nueva_ref = siguiente_referencia_oferta()
    nuevo_oid = execute(
        """INSERT INTO offers
           (referencia, client_id, titulo, tipo_trabajo, descripcion, status,
            fecha_creacion, validez_dias, descuento_pct, iva_pct, irpf_pct,
            notas_internas, notas_cliente, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, 'borrador', ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            nueva_ref,
            oferta["client_id"],
            f"[COPIA] {oferta['titulo']}",
            oferta["tipo_trabajo"],
            oferta["descripcion"],
            _today_iso(),
            oferta["validez_dias"],
            oferta["descuento_pct"],
            oferta["iva_pct"],
            oferta.get("irpf_pct", 15),
            oferta["notas_internas"],
            oferta["notas_cliente"],
            now, now,
        ),
    )

    # Copiar líneas
    lines = query("SELECT * FROM offer_lines WHERE offer_id = ? ORDER BY orden", (oid,))
    for line in lines:
        execute(
            """INSERT INTO offer_lines (offer_id, orden, concepto, descripcion, cantidad, precio_unitario)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (nuevo_oid, line["orden"], line["concepto"],
             line["descripcion"], line["cantidad"], line["precio_unitario"]),
        )

    return jsonify({"ok": True, "id": nuevo_oid, "referencia": nueva_ref})


# ─── Tipos de trabajo ─────────────────────────────────────────────

@crm_bp.route("/tipos-trabajo")
def tipos_trabajo():
    tipos = query("SELECT * FROM work_types ORDER BY codigo")
    return render_template("crm_tipos_trabajo.html", tipos=tipos)


@crm_bp.route("/tipos-trabajo", methods=["POST"])
def tipos_trabajo_crear():
    data = request.get_json() or {}
    now = _now()
    try:
        tid = execute(
            """INSERT INTO work_types (codigo, nombre, descripcion, precio_base, unidad, activo, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                data.get("codigo", "").strip().upper(),
                data.get("nombre", "").strip(),
                data.get("descripcion", "").strip(),
                float(data.get("precio_base", 0) or 0),
                data.get("unidad", "ud").strip(),
                1,
                now,
            ),
        )
        return jsonify({"ok": True, "id": tid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@crm_bp.route("/tipos-trabajo/<int:tid>", methods=["PUT"])
def tipos_trabajo_editar(tid):
    data = request.get_json() or {}
    try:
        execute(
            """UPDATE work_types SET
               nombre=?, descripcion=?, precio_base=?, unidad=?, activo=?
               WHERE id=?""",
            (
                data.get("nombre", "").strip(),
                data.get("descripcion", "").strip(),
                float(data.get("precio_base", 0) or 0),
                data.get("unidad", "ud").strip(),
                int(data.get("activo", 1)),
                tid,
            ),
        )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ─── API auxiliar para clientes (uso en formularios) ─────────────

@crm_bp.route("/api/codigos-reforma")
def api_codigos_reforma():
    categoria = request.args.get("cat", "")
    result = {}
    for codigo, data in _CODIGOS_REFORMA.items():
        if not categoria or categoria in data.get("categorias", []):
            result[codigo] = data
    # Agrupar por grupo
    grupos = {}
    for codigo, data in sorted(result.items(), key=lambda x: (int(x[1]["grupo"]), x[0])):
        g = data["grupo"]
        if g not in grupos:
            grupos[g] = {"nombre": GRUPOS_REFORMA.get(g, f"Grupo {g}"), "codigos": []}
        grupos[g]["codigos"].append({"codigo": codigo, "descripcion": data["descripcion"]})
    return jsonify({"grupos": grupos, "precio_hov": _precio_hov(0)})


@crm_bp.route("/api/precio-hov/<int:n>")
def api_precio_hov(n):
    return jsonify({"n_actos": n, "precio": _precio_hov(n)})


@crm_bp.route("/api/clientes")
def api_clientes():
    clientes = query("SELECT id, nombre, empresa, email, telefono FROM clients ORDER BY nombre")
    return jsonify(clientes)


@crm_bp.route("/api/tipos-trabajo")
def api_tipos_trabajo():
    tipos = query("SELECT * FROM work_types WHERE activo=1 ORDER BY codigo")
    return jsonify(tipos)
