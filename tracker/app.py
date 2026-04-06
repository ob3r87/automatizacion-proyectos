"""
Flask application – Gestor de Trabajos Diarios.
Ejecutar: python tracker/app.py
"""
import json
import os
import subprocess
import sys
from datetime import datetime, date
from pathlib import Path

# Auto-instalar Flask si falta
try:
    from flask import (Flask, render_template, request, jsonify,
                       redirect, url_for, send_file)
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
    from flask import (Flask, render_template, request, jsonify,
                       redirect, url_for, send_file)

from db import (init_db, init_crm_db, init_work_types_defaults, init_ensayo_types_defaults,
                init_vehiculos_db, query, execute, get_db)
from project_scanner import scan_projects, get_project_files, get_project_datos
from config import FLASK_PORT, FLASK_HOST, FLASK_DEBUG, DB_PATH, PROJECT_ROOT, TRACKER_DIR

BASE_DIR = TRACKER_DIR

app = Flask(__name__)
_secret = os.environ.get("SECRET_KEY")
if not _secret:
    _secret_file = BASE_DIR / ".secret_key"
    if _secret_file.exists():
        _secret = _secret_file.read_text().strip()
    else:
        import secrets as _secrets
        _secret = _secrets.token_hex(32)
        _secret_file.write_text(_secret)
app.secret_key = _secret

from datetime import date as _date

@app.template_filter('diasrestantes')
def _diasrestantes(fecha_str):
    try:
        d = _date.fromisoformat(str(fecha_str)[:10])
        return (d - _date.today()).days
    except Exception:
        return 999

from crm_routes import crm_bp
app.register_blueprint(crm_bp)

from form_routes import form_bp
app.register_blueprint(form_bp)

from boletin_routes import bol_bp
app.register_blueprint(bol_bp)

CATEGORIES = [
    ("proyecto", "Proyecto"),
    ("calculo", "Cálculo"),
    ("cfo", "Certificado Final Obra"),
    ("ct", "Certificado Taller"),
    ("revision", "Revisión"),
    ("consulta", "Consulta"),
    ("gestion", "Gestión"),
    ("inspeccion", "Inspección"),
    ("otro", "Otro"),
]

STATUSES = [
    ("en_curso", "En curso"),
    ("completado", "Completado"),
    ("pendiente", "Pendiente"),
    ("facturado", "Facturado"),
]


# ─── Páginas HTML ────────────────────────────────────────────────

@app.route("/qr")
def qr_page():
    """Muestra QR para conectar desde móvil/tablet."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "192.168.1.18"
    url = f"http://{local_ip}:{FLASK_PORT}/formulario/nuevo"
    return render_template("qr.html", url=url, ip=local_ip, port=FLASK_PORT)

@app.route("/")
def index():
    today = date.today().isoformat()
    entries = query(
        "SELECT * FROM work_entries WHERE date = ? ORDER BY created_at DESC",
        (today,),
    )
    total_hours = sum(e["hours"] for e in entries)
    projects = scan_projects()
    templates = query("SELECT * FROM work_templates ORDER BY name")
    return render_template(
        "index.html",
        entries=entries,
        total_hours=total_hours,
        today=today,
        projects=projects,
        templates=templates,
        categories=CATEGORIES,
        statuses=STATUSES,
    )


@app.route("/entries")
def entries_page():
    projects = scan_projects()
    return render_template(
        "entries.html",
        projects=projects,
        categories=CATEGORIES,
        statuses=STATUSES,
    )


@app.route("/entries/new")
def entry_new():
    projects = scan_projects()
    templates = query("SELECT * FROM work_templates ORDER BY name")
    return render_template(
        "entry_form.html",
        entry=None,
        projects=projects,
        templates=templates,
        categories=CATEGORIES,
        statuses=STATUSES,
    )


@app.route("/entries/<int:entry_id>/edit")
def entry_edit(entry_id):
    entry = query("SELECT * FROM work_entries WHERE id = ?", (entry_id,), one=True)
    if not entry:
        return redirect(url_for("index"))
    files = query("SELECT * FROM entry_files WHERE entry_id = ?", (entry_id,))
    projects = scan_projects()
    templates = query("SELECT * FROM work_templates ORDER BY name")
    return render_template(
        "entry_form.html",
        entry=entry,
        entry_files=files,
        projects=projects,
        templates=templates,
        categories=CATEGORIES,
        statuses=STATUSES,
    )


@app.route("/templates")
def templates_page():
    templates = query("SELECT * FROM work_templates ORDER BY name")
    return render_template(
        "templates_list.html",
        templates=templates,
        categories=CATEGORIES,
    )


# ─── API: Entries ────────────────────────────────────────────────

@app.route("/api/entries", methods=["GET"])
def api_list_entries():
    sql = "SELECT * FROM work_entries WHERE 1=1"
    params = []

    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    project_ref = request.args.get("project_ref")
    category = request.args.get("category")
    status = request.args.get("status")
    q = request.args.get("q", "").strip()

    if date_from:
        sql += " AND date >= ?"
        params.append(date_from)
    if date_to:
        sql += " AND date <= ?"
        params.append(date_to)
    if project_ref:
        sql += " AND project_ref = ?"
        params.append(project_ref)
    if category:
        sql += " AND category = ?"
        params.append(category)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if q:
        sql += " AND (description LIKE ? OR client_name LIKE ? OR notes LIKE ?)"
        like = f"%{q}%"
        params.extend([like, like, like])

    sql += " ORDER BY date DESC, created_at DESC"

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 25))
    offset = (page - 1) * per_page

    count_sql = sql.replace("SELECT *", "SELECT COUNT(*)", 1)
    total = query(count_sql, params, one=True)
    total_count = list(total.values())[0] if total else 0

    sql += " LIMIT ? OFFSET ?"
    params.extend([per_page, offset])

    entries = query(sql, params)

    # Calcular total de horas de los resultados filtrados
    hours_sql = sql.replace("SELECT *", "SELECT COALESCE(SUM(hours),0) as total_hours", 1)
    # Quitar el LIMIT/OFFSET para sumar todas
    hours_sql_no_limit = hours_sql.rsplit("LIMIT", 1)[0]
    hours_params = params[:-2]  # sin limit/offset
    hours_result = query(hours_sql_no_limit, hours_params, one=True)
    total_hours = hours_result["total_hours"] if hours_result else 0

    return jsonify({
        "entries": entries,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_hours": total_hours,
    })


@app.route("/api/entries", methods=["POST"])
def api_create_entry():
    data = request.get_json()
    now = datetime.now().isoformat()
    entry_id = execute(
        """INSERT INTO work_entries
           (date, description, client_name, project_ref, revision, hours,
            category, status, notes, template_id, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data.get("date", date.today().isoformat()),
            data.get("description", ""),
            data.get("client_name", ""),
            data.get("project_ref", ""),
            data.get("revision", ""),
            float(data.get("hours", 0)),
            data.get("category", "otro"),
            data.get("status", "completado"),
            data.get("notes", ""),
            data.get("template_id"),
            now, now,
        ),
    )
    # Archivos asociados
    for fp in data.get("files", []):
        execute(
            "INSERT INTO entry_files (entry_id, file_path, file_type, description) VALUES (?,?,?,?)",
            (entry_id, fp.get("path", ""), fp.get("type", ""), fp.get("desc", "")),
        )
    return jsonify({"id": entry_id}), 201


@app.route("/api/entries/<int:entry_id>", methods=["PUT"])
def api_update_entry(entry_id):
    data = request.get_json()
    now = datetime.now().isoformat()
    execute(
        """UPDATE work_entries SET
           date=?, description=?, client_name=?, project_ref=?, revision=?,
           hours=?, category=?, status=?, notes=?, updated_at=?
           WHERE id=?""",
        (
            data.get("date"),
            data.get("description"),
            data.get("client_name"),
            data.get("project_ref"),
            data.get("revision"),
            float(data.get("hours", 0)),
            data.get("category"),
            data.get("status"),
            data.get("notes", ""),
            now,
            entry_id,
        ),
    )
    return jsonify({"ok": True})


@app.route("/api/entries/<int:entry_id>", methods=["DELETE"])
def api_delete_entry(entry_id):
    execute("DELETE FROM entry_files WHERE entry_id = ?", (entry_id,))
    execute("DELETE FROM work_entries WHERE id = ?", (entry_id,))
    return jsonify({"ok": True})


# ─── API: Files ──────────────────────────────────────────────────

@app.route("/api/entries/<int:entry_id>/files", methods=["GET"])
def api_entry_files(entry_id):
    files = query("SELECT * FROM entry_files WHERE entry_id = ?", (entry_id,))
    return jsonify(files)


@app.route("/api/entries/<int:entry_id>/files", methods=["POST"])
def api_add_file(entry_id):
    data = request.get_json()
    fid = execute(
        "INSERT INTO entry_files (entry_id, file_path, file_type, description) VALUES (?,?,?,?)",
        (entry_id, data["path"], data.get("type", ""), data.get("desc", "")),
    )
    return jsonify({"id": fid}), 201


@app.route("/api/files/<int:file_id>", methods=["DELETE"])
def api_delete_file(file_id):
    execute("DELETE FROM entry_files WHERE id = ?", (file_id,))
    return jsonify({"ok": True})


# ─── API: Projects ───────────────────────────────────────────────

@app.route("/api/projects")
def api_projects():
    return jsonify(scan_projects())


@app.route("/api/projects/<path:ref>/files")
def api_project_files(ref):
    rev = request.args.get("revision")
    return jsonify(get_project_files(ref, rev))


@app.route("/api/projects/<path:ref>/datos")
def api_project_datos(ref):
    rev = request.args.get("revision")
    datos = get_project_datos(ref, rev)
    return jsonify(datos or {})


# ─── API: System actions ────────────────────────────────────────

@app.route("/api/open-folder", methods=["POST"])
def api_open_folder():
    data = request.get_json()
    folder = data.get("path", "")
    if folder and Path(folder).is_dir():
        os.startfile(folder)
        return jsonify({"ok": True})
    return jsonify({"error": "Carpeta no encontrada"}), 404


@app.route("/api/open-file", methods=["POST"])
def api_open_file():
    data = request.get_json()
    filepath = data.get("path", "")
    if filepath and Path(filepath).is_file():
        os.startfile(filepath)
        return jsonify({"ok": True})
    return jsonify({"error": "Archivo no encontrado"}), 404


@app.route("/api/launch-formulario", methods=["POST"])
def api_launch_formulario():
    formulario = PROJECT_ROOT / "formulario.py"
    if formulario.exists():
        subprocess.Popen(
            [sys.executable, str(formulario)],
            cwd=str(PROJECT_ROOT),
        )
        return jsonify({"ok": True})
    return jsonify({"error": "formulario.py no encontrado"}), 404


# ─── API: Templates ─────────────────────────────────────────────

@app.route("/api/templates", methods=["GET"])
def api_list_templates():
    return jsonify(query("SELECT * FROM work_templates ORDER BY name"))


@app.route("/api/templates", methods=["POST"])
def api_create_template():
    data = request.get_json()
    now = datetime.now().isoformat()
    tid = execute(
        """INSERT INTO work_templates
           (name, description, default_category, default_hours, default_notes, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            data["name"],
            data.get("description", ""),
            data.get("default_category", "otro"),
            float(data.get("default_hours", 0)),
            data.get("default_notes", ""),
            now,
        ),
    )
    return jsonify({"id": tid}), 201


@app.route("/api/templates/from-entry/<int:entry_id>", methods=["POST"])
def api_template_from_entry(entry_id):
    entry = query("SELECT * FROM work_entries WHERE id = ?", (entry_id,), one=True)
    if not entry:
        return jsonify({"error": "Entrada no encontrada"}), 404
    data = request.get_json() or {}
    name = data.get("name", f"Plantilla de: {entry['description'][:50]}")
    now = datetime.now().isoformat()
    tid = execute(
        """INSERT INTO work_templates
           (name, description, default_category, default_hours, default_notes, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (name, entry["description"], entry["category"], entry["hours"], entry["notes"], now),
    )
    return jsonify({"id": tid}), 201


@app.route("/api/templates/<int:tid>", methods=["PUT"])
def api_update_template(tid):
    data = request.get_json()
    execute(
        """UPDATE work_templates SET
           name=?, description=?, default_category=?, default_hours=?, default_notes=?
           WHERE id=?""",
        (
            data["name"],
            data.get("description", ""),
            data.get("default_category", "otro"),
            float(data.get("default_hours", 0)),
            data.get("default_notes", ""),
            tid,
        ),
    )
    return jsonify({"ok": True})


@app.route("/api/templates/<int:tid>", methods=["DELETE"])
def api_delete_template(tid):
    execute("DELETE FROM work_templates WHERE id = ?", (tid,))
    return jsonify({"ok": True})


# ─── API: Stats ──────────────────────────────────────────────────

@app.route("/api/stats")
def api_stats():
    date_from = request.args.get("date_from", "2000-01-01")
    date_to = request.args.get("date_to", "2099-12-31")

    by_category = query(
        """SELECT category, COUNT(*) as count, COALESCE(SUM(hours),0) as hours
           FROM work_entries WHERE date BETWEEN ? AND ?
           GROUP BY category ORDER BY hours DESC""",
        (date_from, date_to),
    )
    by_project = query(
        """SELECT project_ref, client_name, COUNT(*) as count, COALESCE(SUM(hours),0) as hours
           FROM work_entries WHERE date BETWEEN ? AND ? AND project_ref != ''
           GROUP BY project_ref ORDER BY hours DESC""",
        (date_from, date_to),
    )
    by_status = query(
        """SELECT status, COUNT(*) as count, COALESCE(SUM(hours),0) as hours
           FROM work_entries WHERE date BETWEEN ? AND ?
           GROUP BY status""",
        (date_from, date_to),
    )
    totals = query(
        """SELECT COUNT(*) as count, COALESCE(SUM(hours),0) as hours
           FROM work_entries WHERE date BETWEEN ? AND ?""",
        (date_from, date_to),
        one=True,
    )
    return jsonify({
        "by_category": by_category,
        "by_project": by_project,
        "by_status": by_status,
        "totals": totals,
    })


# ─── Exportar CSV ────────────────────────────────────────────────

@app.route("/api/export/csv")
def api_export_csv():
    import csv
    import io

    date_from = request.args.get("date_from", "2000-01-01")
    date_to = request.args.get("date_to", "2099-12-31")

    entries = query(
        "SELECT * FROM work_entries WHERE date BETWEEN ? AND ? ORDER BY date DESC",
        (date_from, date_to),
    )

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Fecha", "Proyecto", "Cliente", "Categoria", "Descripcion",
                      "Horas", "Estado", "Notas"])
    for e in entries:
        writer.writerow([
            e["date"], e["project_ref"], e["client_name"], e["category"],
            e["description"], e["hours"], e["status"], e["notes"],
        ])

    from flask import Response
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=trabajos.csv"},
    )


# ─── Main ────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    init_crm_db()
    init_vehiculos_db()
    init_work_types_defaults()
    init_ensayo_types_defaults()
    print(f"PHICAN WebApp disponible en http://{FLASK_HOST}:{FLASK_PORT}")
    app.jinja_env.auto_reload = True
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
