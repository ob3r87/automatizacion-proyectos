"""
Módulo de base de datos SQLite para el tracker de trabajos diarios.
"""
import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent / "tracker.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS work_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    description TEXT NOT NULL,
    client_name TEXT DEFAULT '',
    project_ref TEXT DEFAULT '',
    revision TEXT DEFAULT '',
    hours REAL NOT NULL DEFAULT 0,
    category TEXT NOT NULL DEFAULT 'otro',
    status TEXT NOT NULL DEFAULT 'completado',
    notes TEXT DEFAULT '',
    template_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entry_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_type TEXT DEFAULT '',
    description TEXT DEFAULT '',
    FOREIGN KEY (entry_id) REFERENCES work_entries(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS work_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    default_category TEXT NOT NULL DEFAULT 'otro',
    default_hours REAL DEFAULT 0,
    default_notes TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
"""


def init_db():
    with get_db() as db:
        db.executescript(SCHEMA)


@contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def query(sql, params=(), one=False):
    with get_db() as db:
        cur = db.execute(sql, params)
        rows = cur.fetchall()
        if one:
            return dict(rows[0]) if rows else None
        return [dict(r) for r in rows]


def execute(sql, params=()):
    with get_db() as db:
        cur = db.execute(sql, params)
        return cur.lastrowid


# ─── CRM Schema ──────────────────────────────────────────────────

SCHEMA2 = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    empresa TEXT DEFAULT '',
    email TEXT DEFAULT '',
    telefono TEXT DEFAULT '',
    nif TEXT DEFAULT '',
    direccion TEXT DEFAULT '',
    ciudad TEXT DEFAULT '',
    cp TEXT DEFAULT '',
    notas TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS work_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT DEFAULT '',
    precio_base REAL DEFAULT 0,
    unidad TEXT DEFAULT 'ud',
    activo INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referencia TEXT UNIQUE NOT NULL,
    client_id INTEGER,
    titulo TEXT NOT NULL,
    tipo_trabajo TEXT DEFAULT '',
    descripcion TEXT DEFAULT '',
    status TEXT DEFAULT 'borrador',
    fecha_creacion TEXT NOT NULL,
    fecha_envio TEXT DEFAULT '',
    fecha_respuesta TEXT DEFAULT '',
    fecha_vencimiento TEXT DEFAULT '',
    validez_dias INTEGER DEFAULT 30,
    descuento_pct REAL DEFAULT 0,
    iva_pct REAL DEFAULT 7,
    notas_internas TEXT DEFAULT '',
    notas_cliente TEXT DEFAULT '',
    pdf_path TEXT DEFAULT '',
    project_ref TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

CREATE TABLE IF NOT EXISTS offer_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    offer_id INTEGER NOT NULL,
    orden INTEGER DEFAULT 0,
    concepto TEXT NOT NULL,
    descripcion TEXT DEFAULT '',
    cantidad REAL DEFAULT 1,
    precio_unitario REAL DEFAULT 0,
    FOREIGN KEY (offer_id) REFERENCES offers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS offer_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    offer_id INTEGER NOT NULL,
    status_anterior TEXT DEFAULT '',
    status_nuevo TEXT NOT NULL,
    fecha TEXT NOT NULL,
    notas TEXT DEFAULT '',
    FOREIGN KEY (offer_id) REFERENCES offers(id) ON DELETE CASCADE
);
"""

WORK_TYPES_DEFAULT = [
    ("HOV", "Homologación de Reforma de Vehículo", "Proyecto técnico + tramitación ITV", 650.0),
    ("PT",  "Proyecto Técnico", "Redacción de proyecto técnico", 500.0),
    ("CFO", "Certificado Final de Obra", "Emisión de CFO para reforma", 180.0),
    ("CT",  "Certificado de Taller", "Certificado de instalador autorizado", 120.0),
    ("IT",  "Inspección Técnica", "Visita e informe de inspección", 200.0),
    ("DT",  "Dictamen Técnico", "Dictamen o informe técnico", 350.0),
    ("CON", "Consultoría Técnica", "Asesoramiento técnico por horas", 90.0),
    ("EST", "Estudio Técnico", "Estudio de viabilidad o análisis", 400.0),
    ("DIR", "Dirección de Obra", "Dirección facultativa de obra", 600.0),
    ("CAL", "Cálculo Estructural", "Cálculo y memoria de estructuras", 300.0),
    ("OTR", "Otro", "Trabajo no categorizado", 0.0),
]


def init_crm_db():
    """Inicializa las tablas del CRM."""
    with get_db() as db:
        db.executescript(SCHEMA2)


def init_work_types_defaults():
    """Inserta los tipos de trabajo predeterminados si la tabla está vacía."""
    count = query("SELECT COUNT(*) as c FROM work_types", one=True)
    if count and count["c"] == 0:
        now = __import__("datetime").datetime.now().isoformat()
        for codigo, nombre, descripcion, precio_base in WORK_TYPES_DEFAULT:
            execute(
                """INSERT INTO work_types
                   (codigo, nombre, descripcion, precio_base, unidad, activo, created_at)
                   VALUES (?, ?, ?, ?, 'ud', 1, ?)""",
                (codigo, nombre, descripcion, precio_base, now),
            )
