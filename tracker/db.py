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
    irpf_pct REAL DEFAULT 15,
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

CREATE TABLE IF NOT EXISTS offer_hov_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    offer_id INTEGER UNIQUE NOT NULL,
    marca TEXT DEFAULT '',
    modelo TEXT DEFAULT '',
    tipo_vehiculo TEXT DEFAULT '',
    matricula TEXT DEFAULT '',
    bastidor TEXT DEFAULT '',
    categoria TEXT DEFAULT '',
    anio_matriculacion TEXT DEFAULT '',
    actos_reglamentarios TEXT DEFAULT '[]',
    n_actos INTEGER DEFAULT 0,
    mma_antes TEXT DEFAULT '',       mma_despues TEXT DEFAULT '',
    tara_antes TEXT DEFAULT '',      tara_despues TEXT DEFAULT '',
    plazas_antes TEXT DEFAULT '',    plazas_despues TEXT DEFAULT '',
    longitud_antes TEXT DEFAULT '',  longitud_despues TEXT DEFAULT '',
    anchura_antes TEXT DEFAULT '',   anchura_despues TEXT DEFAULT '',
    altura_antes TEXT DEFAULT '',    altura_despues TEXT DEFAULT '',
    mmta_antes TEXT DEFAULT '',      mmta_despues TEXT DEFAULT '',
    mma_eje_antes TEXT DEFAULT '',   mma_eje_despues TEXT DEFAULT '',
    potencia_antes TEXT DEFAULT '',  potencia_despues TEXT DEFAULT '',
    cilindrada_antes TEXT DEFAULT '', cilindrada_despues TEXT DEFAULT '',
    combustible_antes TEXT DEFAULT '', combustible_despues TEXT DEFAULT '',
    vel_max_antes TEXT DEFAULT '',   vel_max_despues TEXT DEFAULT '',
    notas_tecnicas TEXT DEFAULT '',
    FOREIGN KEY (offer_id) REFERENCES offers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ensayo_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT DEFAULT '',
    normativa TEXT DEFAULT '',
    organismo TEXT DEFAULT '',
    precio_estimado REAL DEFAULT 0,
    activo INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS offer_ensayos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    offer_id INTEGER NOT NULL,
    ensayo_type_id INTEGER,
    nombre TEXT NOT NULL,
    normativa TEXT DEFAULT '',
    organismo TEXT DEFAULT '',
    precio REAL DEFAULT 0,
    incluido_oferta INTEGER DEFAULT 1,
    estado TEXT DEFAULT 'pendiente',
    notas TEXT DEFAULT '',
    FOREIGN KEY (offer_id) REFERENCES offers(id) ON DELETE CASCADE,
    FOREIGN KEY (ensayo_type_id) REFERENCES ensayo_types(id)
);
"""

WORK_TYPES_DEFAULT = [
    # (codigo, nombre, descripcion, precio_base, subcategoria, requiere_ensayos)
    # ── Homologaciones de reforma ──────────────────────────────────────────────
    ("HOV",  "Homologación de Reforma de Vehículo",
     "Proyecto técnico + tramitación ITV", 650.0, "Reforma vehículo", 0),
    ("VIV",  "Conversión a furgón vivienda (camper)",
     "Reforma 7.1/7.3 — habilitación interior como vivienda", 850.0, "Reforma vehículo", 0),
    ("FRIG", "Conversión furgoneta frigorífica",
     "Reforma 7.1 — instalación equipo frío / carrocería isotérmica", 750.0, "Reforma vehículo", 0),
    ("CARG", "Instalación grúa autocargante",
     "Reforma 5.1 — montaje grúa Palfinger / Hiab / Atlas", 900.0, "Reforma vehículo", 1),
    ("PLAT", "Instalación plataforma elevadora",
     "Reforma 4.6 — plataforma hidráulica para accesibilidad PMR", 750.0, "Reforma vehículo", 0),
    ("CARC", "Quita de carrocería con modificación de suspensión",
     "Reforma 7.1 + 4.1 — quita de caja y adecuación suspensión", 1100.0, "Reforma vehículo", 1),
    ("REMO", "Acondicionamiento para remolque",
     "Reforma 9.1 — instalación enganche y verificación MMA conjunto", 450.0, "Reforma vehículo", 0),
    ("MMA",  "Modificación MMA (aumento de masa)",
     "Reforma 8.1 — justificación y tramitación aumento MMA", 550.0, "Reforma vehículo", 1),
    ("ELEC", "Conversión a vehículo eléctrico / híbrido",
     "Reforma 2.11 — sustitución grupo motopropulsor", 1500.0, "Reforma vehículo", 1),
    ("CARC2","Extensión de carrocería (alargamiento)",
     "Reforma 7.1 + 8.2 — prolongación bastidor y carrocería", 1200.0, "Reforma vehículo", 1),
    ("SUSP", "Modificación sistema de suspensión",
     "Reforma 4.1 — sustitución o modificación suspensión neumática/mecánica", 600.0, "Reforma vehículo", 1),
    ("COMB", "Transformación a GLP / GNC",
     "Reforma 2.2 — instalación sistema combustible alternativo", 700.0, "Reforma vehículo", 0),
    # ── Documentación técnica ─────────────────────────────────────────────────
    ("PT",   "Proyecto Técnico",
     "Redacción de proyecto técnico", 500.0, "Documentación", 0),
    ("CFO",  "Certificado Final de Obra",
     "Emisión de CFO para reforma", 180.0, "Documentación", 0),
    ("CT",   "Certificado de Taller",
     "Certificado de instalador autorizado", 120.0, "Documentación", 0),
    ("DT",   "Dictamen Técnico",
     "Dictamen o informe técnico para tramitación", 350.0, "Documentación", 0),
    ("EST",  "Estudio Técnico",
     "Estudio de viabilidad o análisis previo", 400.0, "Documentación", 0),
    # ── Servicios de ingeniería ───────────────────────────────────────────────
    ("IT",   "Inspección Técnica",
     "Visita e informe de inspección", 200.0, "Ingeniería", 0),
    ("CAL",  "Cálculo Estructural",
     "Cálculo y memoria de estructuras", 300.0, "Ingeniería", 0),
    ("DIR",  "Dirección de Obra",
     "Dirección facultativa de obra", 600.0, "Ingeniería", 0),
    ("CON",  "Consultoría Técnica",
     "Asesoramiento técnico por horas", 90.0, "Ingeniería", 0),
    # ── Otros ─────────────────────────────────────────────────────────────────
    ("OTR",  "Otro",
     "Trabajo no categorizado", 0.0, "", 0),
]


def init_crm_db():
    """Inicializa las tablas del CRM y aplica migraciones si hacen falta."""
    with get_db() as db:
        db.executescript(SCHEMA2)
        # Migración: añadir irpf_pct si no existe (BD creada antes de esta versión)
        cols = [r[1] for r in db.execute("PRAGMA table_info(offers)").fetchall()]
        if "irpf_pct" not in cols:
            db.execute("ALTER TABLE offers ADD COLUMN irpf_pct REAL DEFAULT 15")
        # Migración: crear offer_hov_data si no existe
        db.execute("""CREATE TABLE IF NOT EXISTS offer_hov_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    offer_id INTEGER UNIQUE NOT NULL,
    marca TEXT DEFAULT '', modelo TEXT DEFAULT '',
    tipo_vehiculo TEXT DEFAULT '', matricula TEXT DEFAULT '',
    bastidor TEXT DEFAULT '', categoria TEXT DEFAULT '',
    anio_matriculacion TEXT DEFAULT '',
    actos_reglamentarios TEXT DEFAULT '[]', n_actos INTEGER DEFAULT 0,
    mma_antes TEXT DEFAULT '', mma_despues TEXT DEFAULT '',
    tara_antes TEXT DEFAULT '', tara_despues TEXT DEFAULT '',
    plazas_antes TEXT DEFAULT '', plazas_despues TEXT DEFAULT '',
    longitud_antes TEXT DEFAULT '', longitud_despues TEXT DEFAULT '',
    anchura_antes TEXT DEFAULT '', anchura_despues TEXT DEFAULT '',
    altura_antes TEXT DEFAULT '', altura_despues TEXT DEFAULT '',
    mmta_antes TEXT DEFAULT '', mmta_despues TEXT DEFAULT '',
    mma_eje_antes TEXT DEFAULT '', mma_eje_despues TEXT DEFAULT '',
    potencia_antes TEXT DEFAULT '', potencia_despues TEXT DEFAULT '',
    cilindrada_antes TEXT DEFAULT '', cilindrada_despues TEXT DEFAULT '',
    combustible_antes TEXT DEFAULT '', combustible_despues TEXT DEFAULT '',
    vel_max_antes TEXT DEFAULT '', vel_max_despues TEXT DEFAULT '',
    notas_tecnicas TEXT DEFAULT '',
    FOREIGN KEY (offer_id) REFERENCES offers(id) ON DELETE CASCADE
)""")
        # Migración: añadir columnas extra a work_types si no existen
        wt_cols = [r[1] for r in db.execute("PRAGMA table_info(work_types)").fetchall()]
        if "subcategoria" not in wt_cols:
            db.execute("ALTER TABLE work_types ADD COLUMN subcategoria TEXT DEFAULT ''")
        if "notas_tarificacion" not in wt_cols:
            db.execute("ALTER TABLE work_types ADD COLUMN notas_tarificacion TEXT DEFAULT ''")
        if "requiere_ensayos" not in wt_cols:
            db.execute("ALTER TABLE work_types ADD COLUMN requiere_ensayos INTEGER DEFAULT 0")
        if "actos_aplicables" not in wt_cols:
            db.execute("ALTER TABLE work_types ADD COLUMN actos_aplicables TEXT DEFAULT '[]'")
        # Migración: crear ensayo_types y offer_ensayos si no existen
        db.execute("""CREATE TABLE IF NOT EXISTS ensayo_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT DEFAULT '',
    normativa TEXT DEFAULT '',
    organismo TEXT DEFAULT '',
    precio_estimado REAL DEFAULT 0,
    activo INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
)""")
        db.execute("""CREATE TABLE IF NOT EXISTS offer_ensayos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    offer_id INTEGER NOT NULL,
    ensayo_type_id INTEGER,
    nombre TEXT NOT NULL,
    normativa TEXT DEFAULT '',
    organismo TEXT DEFAULT '',
    precio REAL DEFAULT 0,
    incluido_oferta INTEGER DEFAULT 1,
    estado TEXT DEFAULT 'pendiente',
    notas TEXT DEFAULT '',
    FOREIGN KEY (offer_id) REFERENCES offers(id) ON DELETE CASCADE,
    FOREIGN KEY (ensayo_type_id) REFERENCES ensayo_types(id)
)""")
        # pdf_template_settings (fila única id=1)
        db.execute("""CREATE TABLE IF NOT EXISTS pdf_template_settings (
            id INTEGER PRIMARY KEY CHECK(id=1),
            empresa_nombre TEXT DEFAULT 'PHICAN INGENIEROS',
            empresa_subtitulo TEXT DEFAULT 'Ingeniería Técnica',
            empresa_direccion TEXT DEFAULT '',
            empresa_tel TEXT DEFAULT '',
            empresa_email TEXT DEFAULT '',
            empresa_cif TEXT DEFAULT '',
            empresa_logo_path TEXT DEFAULT '',
            watermark_activa INTEGER DEFAULT 0,
            watermark_texto TEXT DEFAULT 'BORRADOR',
            watermark_color TEXT DEFAULT '#CC0000',
            watermark_opacidad REAL DEFAULT 0.15,
            watermark_angulo INTEGER DEFAULT 45,
            pdf_notas_pie TEXT DEFAULT '',
            updated_at TEXT DEFAULT ''
        )""")
        # Insertar fila por defecto si no existe
        db.execute("INSERT OR IGNORE INTO pdf_template_settings (id) VALUES (1)")
        # Tabla de tareas
        db.execute("""CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            offer_id INTEGER,
            titulo TEXT NOT NULL,
            descripcion TEXT DEFAULT '',
            tipo TEXT DEFAULT 'manual',
            estado TEXT DEFAULT 'pendiente',
            prioridad TEXT DEFAULT 'media',
            fecha_limite TEXT DEFAULT '',
            fecha_completado TEXT DEFAULT '',
            orden INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT DEFAULT '',
            FOREIGN KEY (offer_id) REFERENCES offers(id) ON DELETE SET NULL
        )""")
        # App settings genérico (clave/valor)
        db.execute("""CREATE TABLE IF NOT EXISTS app_settings (
            clave TEXT PRIMARY KEY,
            valor TEXT DEFAULT ''
        )""")

        # Secuencia de códigos de proyecto por año
        db.execute("""CREATE TABLE IF NOT EXISTS codigos_proyecto (
            anio INTEGER PRIMARY KEY,
            ultimo_numero INTEGER DEFAULT 0
        )""")

        # Jerarquía de tipos de trabajo (tipo > categoría > subcategoría)
        db.execute("""CREATE TABLE IF NOT EXISTS tipos_jerarquia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            categoria TEXT NOT NULL DEFAULT '',
            subcategoria TEXT NOT NULL DEFAULT '',
            codigo TEXT DEFAULT '',
            es_vehiculo INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            orden INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT ''
        )""")

        # Plantillas de carpetas por tipo de trabajo (tipo_jerarquia_id NULL = global)
        db.execute("""CREATE TABLE IF NOT EXISTS plantillas_carpetas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_jerarquia_id INTEGER,
            nombre_carpeta TEXT NOT NULL,
            orden INTEGER DEFAULT 0,
            FOREIGN KEY (tipo_jerarquia_id) REFERENCES tipos_jerarquia(id) ON DELETE CASCADE
        )""")

        # Migración: añadir codigo_proyecto a offers si no existe
        off_cols = [r[1] for r in db.execute("PRAGMA table_info(offers)").fetchall()]
        if "codigo_proyecto" not in off_cols:
            db.execute("ALTER TABLE offers ADD COLUMN codigo_proyecto TEXT DEFAULT ''")
        if "he_path" not in off_cols:
            db.execute("ALTER TABLE offers ADD COLUMN he_path TEXT DEFAULT ''")

        # Poblar tipos_jerarquia con valores por defecto si está vacía
        count_tj = db.execute("SELECT COUNT(*) FROM tipos_jerarquia").fetchone()[0]
        if count_tj == 0:
            import datetime as _dt
            _now2 = _dt.datetime.now().isoformat(timespec="seconds")
            _tipos_default = [
                # (tipo, categoria, subcategoria, codigo, es_vehiculo, orden)
                ("Vehículos", "Homologación de Reforma", "Individual", "HOV", 1, 0),
                ("Vehículos", "Homologación de Reforma", "Camper / Vivienda", "VIV", 1, 1),
                ("Vehículos", "Homologación de Reforma", "Frigorífico", "FRIG", 1, 2),
                ("Vehículos", "Homologación de Reforma", "Grúa autocargante", "CARG", 1, 3),
                ("Vehículos", "Homologación de Reforma", "Plataforma elevadora", "PLAT", 1, 4),
                ("Vehículos", "Homologación de Reforma", "Carrocería", "CARC", 1, 5),
                ("Vehículos", "Homologación de Reforma", "Remolque", "REMO", 1, 6),
                ("Vehículos", "Homologación de Reforma", "MMA", "MMA", 1, 7),
                ("Vehículos", "Homologación de Reforma", "Eléctrico / Híbrido", "ELEC", 1, 8),
                ("Vehículos", "Homologación de Reforma", "Extensión carrocería", "CARC2", 1, 9),
                ("Vehículos", "Homologación de Reforma", "Suspensión", "SUSP", 1, 10),
                ("Vehículos", "Homologación de Reforma", "GLP / GNC", "COMB", 1, 11),
                ("Documentación", "Técnica", "Proyecto Técnico", "PT", 0, 0),
                ("Documentación", "Técnica", "Certificado Final de Obra", "CFO", 0, 1),
                ("Documentación", "Técnica", "Certificado de Taller", "CT", 0, 2),
                ("Documentación", "Técnica", "Dictamen Técnico", "DT", 0, 3),
                ("Documentación", "Técnica", "Estudio Técnico", "EST", 0, 4),
                ("Ingeniería", "Servicios", "Inspección Técnica", "IT", 0, 0),
                ("Ingeniería", "Servicios", "Cálculo Estructural", "CAL", 0, 1),
                ("Ingeniería", "Servicios", "Dirección de Obra", "DIR", 0, 2),
                ("Ingeniería", "Servicios", "Consultoría", "CON", 0, 3),
                ("Otros", "General", "Otro", "OTR", 0, 0),
            ]
            for tipo, cat, sub, cod, es_veh, ord_ in _tipos_default:
                db.execute(
                    """INSERT INTO tipos_jerarquia
                       (tipo, categoria, subcategoria, codigo, es_vehiculo, activo, orden, created_at)
                       VALUES (?, ?, ?, ?, ?, 1, ?, ?)""",
                    (tipo, cat, sub, cod, es_veh, ord_, _now2),
                )

        # Tabla de eventos de agenda
        db.execute("""CREATE TABLE IF NOT EXISTS agenda_eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descripcion TEXT DEFAULT '',
            fecha_inicio TEXT NOT NULL,
            fecha_fin TEXT DEFAULT '',
            todo_el_dia INTEGER DEFAULT 1,
            tipo TEXT DEFAULT 'evento',
            color TEXT DEFAULT '#1565c0',
            offer_id INTEGER,
            tarea_id INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (offer_id) REFERENCES offers(id) ON DELETE SET NULL,
            FOREIGN KEY (tarea_id) REFERENCES tareas(id) ON DELETE SET NULL
        )""")


def init_work_types_defaults():
    """Inserta o actualiza los tipos de trabajo predeterminados.

    - Si la tabla está vacía, inserta todos.
    - Si ya hay registros, inserta los que falten y actualiza subcategoria/requiere_ensayos
      de los existentes para que reflejen la definición canónica.
    """
    now = __import__("datetime").datetime.now().isoformat()
    existing_rows = query("SELECT codigo FROM work_types")
    existing = {r["codigo"] for r in existing_rows}
    for item in WORK_TYPES_DEFAULT:
        codigo, nombre, descripcion, precio_base = item[0], item[1], item[2], item[3]
        subcategoria = item[4] if len(item) > 4 else ""
        requiere_ensayos = item[5] if len(item) > 5 else 0
        if codigo in existing:
            execute(
                "UPDATE work_types SET subcategoria=?, requiere_ensayos=? WHERE codigo=?",
                (subcategoria, requiere_ensayos, codigo),
            )
        else:
            execute(
                """INSERT INTO work_types
                   (codigo, nombre, descripcion, precio_base, unidad, activo,
                    subcategoria, requiere_ensayos, created_at)
                   VALUES (?, ?, ?, ?, 'ud', 1, ?, ?, ?)""",
                (codigo, nombre, descripcion, precio_base,
                 subcategoria, requiere_ensayos, now),
            )


ENSAYO_TYPES_DEFAULT = [
    ("ENS-FREN",  "Ensayo de eficacia de frenos",
     "Verificación según Directiva 71/320/CEE / R13-H", "71/320/CEE · R13", "ITV / Laboratorio acreditado", 250.0),
    ("ENS-EMIS",  "Ensayo de emisiones contaminantes",
     "Medición emisiones motor según normativa Euro", "Euro VI · RD 2028/1986", "ITV / CITA", 180.0),
    ("ENS-RUID",  "Ensayo de emisiones sonoras",
     "Medición nivel sonoro exterior según R51", "R51 / ISO 362", "Laboratorio acreditado", 350.0),
    ("ENS-ILUM",  "Ensayo de iluminación y señalización",
     "Verificación fotometría y orientación faros", "R48 / R7", "ITV", 120.0),
    ("ENS-ESTR",  "Ensayo de resistencia estructural",
     "Prueba de carga o cálculo según EN 1993", "EN 1993-1-1 / EN 12999", "Laboratorio acreditado", 600.0),
    ("ENS-ESTAB", "Ensayo de estabilidad lateral",
     "Verificación coeficiente estabilidad η ≥ 0.3", "Manual Reformas DGT", "Técnico competente", 200.0),
    ("ENS-GRU",   "Ensayo de grúa / equipo de carga",
     "Prueba de carga y estabilidad grúa autocargante", "EN 12999 · FEM 1.001", "Laboratorio / fabricante", 450.0),
    ("ENS-PROT",  "Ensayo de protección trasera",
     "Verificación resistencia barra protección trasera", "Directiva 70/221/CEE", "Laboratorio acreditado", 300.0),
    ("ENS-MASA",  "Pesaje oficial (distribución de masas)",
     "Pesaje en báscula oficial para verificar MMA y distribución", "RD 2822/1998", "Báscula oficial", 150.0),
    ("ENS-PMEC",  "Prueba de mecanismo (plataforma / elevador)",
     "Verificación funcional y de seguridad plataforma PMR", "EN 1756 / R107", "Técnico competente", 200.0),
    ("ENS-ELEC",  "Ensayo sistema eléctrico / baterías",
     "Verificación instalación eléctrica e baterías vehículo eléctrico", "ECE R100 / IEC 62660", "Laboratorio acreditado", 500.0),
]


def init_ensayo_types_defaults():
    """Inserta los tipos de ensayo predeterminados si la tabla está vacía."""
    count = query("SELECT COUNT(*) as c FROM ensayo_types", one=True)
    if count and count["c"] == 0:
        now = __import__("datetime").datetime.now().isoformat()
        for codigo, nombre, descripcion, normativa, organismo, precio in ENSAYO_TYPES_DEFAULT:
            execute(
                """INSERT INTO ensayo_types
                   (codigo, nombre, descripcion, normativa, organismo, precio_estimado, activo, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, 1, ?)""",
                (codigo, nombre, descripcion, normativa, organismo, precio, now),
            )


def get_pdf_settings() -> dict:
    """Devuelve la configuración de plantilla PDF (fila única)."""
    with get_db() as db:
        row = db.execute("SELECT * FROM pdf_template_settings WHERE id=1").fetchone()
        return dict(row) if row else {}


def save_pdf_settings(data: dict) -> None:
    """Guarda la configuración de plantilla PDF."""
    allowed = [
        "empresa_nombre", "empresa_subtitulo", "empresa_direccion",
        "empresa_tel", "empresa_email", "empresa_cif", "empresa_logo_path",
        "watermark_activa", "watermark_texto", "watermark_color",
        "watermark_opacidad", "watermark_angulo", "pdf_notas_pie",
    ]
    cols, vals = [], []
    for k in allowed:
        if k in data:
            cols.append(f"{k}=?")
            vals.append(data[k])
    if not cols:
        return
    from datetime import datetime
    cols.append("updated_at=?")
    vals.append(datetime.now().isoformat(timespec="seconds"))
    vals.append(1)
    with get_db() as db:
        db.execute(f"UPDATE pdf_template_settings SET {', '.join(cols)} WHERE id=?", vals)


# Plantillas de tareas por código de tipo de trabajo
TAREA_PLANTILLAS = {
    "HOV": [
        ("Inspección previa del vehículo",            "alta"),
        ("Redactar proyecto técnico de reforma",       "alta"),
        ("Elaborar planos / esquemas técnicos",        "media"),
        ("Solicitar cita en ITV / SITRAN",             "alta"),
        ("Acompañar inspección en ITV",                "alta"),
        ("Presentar documentación en organismos",      "media"),
        ("Recoger certificado / informe final",        "baja"),
        ("Entrega al cliente",                         "baja"),
    ],
    "VIV": [
        ("Visita técnica al vehículo",                 "alta"),
        ("Redactar memoria de habitabilidad",          "alta"),
        ("Elaborar planos de distribución interior",   "alta"),
        ("Solicitar inspección técnica",               "alta"),
        ("Presentar en organismos",                    "media"),
        ("Entrega documentación al cliente",           "baja"),
    ],
    "FRIG": [
        ("Inspección instalación frigorífica",         "alta"),
        ("Redactar memoria técnica",                   "alta"),
        ("Solicitar inspección ITV",                   "alta"),
        ("Entrega al cliente",                         "baja"),
    ],
    "CARG": [
        ("Inspección grúa / autocargante",             "alta"),
        ("Redactar proyecto de instalación",           "alta"),
        ("Certificado fabricante / cálculos",          "alta"),
        ("Solicitar inspección",                       "alta"),
        ("Entrega documentación",                      "baja"),
    ],
    "CARC": [
        ("Inspección previa carrocería",               "alta"),
        ("Redactar proyecto de modificación",          "alta"),
        ("Planos carrocería nueva",                    "media"),
        ("Solicitar inspección ITV",                   "alta"),
        ("Entrega al cliente",                         "baja"),
    ],
    "ELEC": [
        ("Inspección instalación eléctrica",           "alta"),
        ("Redactar proyecto eléctrico",                "alta"),
        ("Solicitar inspección homologación",          "alta"),
        ("Entrega documentación",                      "baja"),
    ],
    "MMA": [
        ("Recopilar datos técnicos del vehículo",      "alta"),
        ("Redactar informe de masa",                   "alta"),
        ("Tramitar ante organismos",                   "media"),
        ("Entrega al cliente",                         "baja"),
    ],
    "DEFAULT": [
        ("Planificar y ejecutar trabajo",              "alta"),
        ("Generar documentación técnica",              "media"),
        ("Revisión y validación interna",              "media"),
        ("Entrega al cliente",                         "baja"),
    ],
}


# ---------------------------------------------------------------------------
# App settings (clave/valor genérico)
# ---------------------------------------------------------------------------

def get_app_setting(clave: str, default: str = "") -> str:
    """Lee un valor de la tabla app_settings."""
    with get_db() as db:
        row = db.execute("SELECT valor FROM app_settings WHERE clave=?", (clave,)).fetchone()
        return row[0] if row else default


def save_app_setting(clave: str, valor: str) -> None:
    """Guarda o actualiza un valor en app_settings."""
    with get_db() as db:
        db.execute(
            "INSERT INTO app_settings (clave, valor) VALUES (?, ?) "
            "ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor",
            (clave, valor),
        )


# ---------------------------------------------------------------------------
# Código de proyecto: P{año}-{NNNN}
# ---------------------------------------------------------------------------

def generar_codigo_proyecto() -> str:
    """Genera el siguiente código de proyecto del año en curso: P2026-0001."""
    from datetime import datetime
    anio = datetime.now().year
    with get_db() as db:
        row = db.execute(
            "SELECT ultimo_numero FROM codigos_proyecto WHERE anio=?", (anio,)
        ).fetchone()
        siguiente = (row[0] + 1) if row else 1
        db.execute(
            "INSERT INTO codigos_proyecto (anio, ultimo_numero) VALUES (?, ?) "
            "ON CONFLICT(anio) DO UPDATE SET ultimo_numero=excluded.ultimo_numero",
            (anio, siguiente),
        )
    return f"P{anio}-{siguiente:04d}"


# ---------------------------------------------------------------------------
# Jerarquía de tipos de trabajo
# ---------------------------------------------------------------------------

def get_tipos_jerarquia() -> list:
    """Devuelve todos los tipos de trabajo jerárquicos."""
    rows = query("SELECT * FROM tipos_jerarquia WHERE activo=1 ORDER BY tipo, categoria, subcategoria, orden")
    return [dict(r) for r in rows] if rows else []


def get_plantillas_carpetas(tipo_id=None) -> list:
    """Devuelve las carpetas plantilla para un tipo (o globales si tipo_id=None)."""
    if tipo_id is None:
        rows = query(
            "SELECT * FROM plantillas_carpetas WHERE tipo_jerarquia_id IS NULL ORDER BY orden"
        )
    else:
        rows = query(
            "SELECT * FROM plantillas_carpetas WHERE tipo_jerarquia_id=? ORDER BY orden",
            (tipo_id,)
        )
    return [dict(r) for r in rows] if rows else []


# ---------------------------------------------------------------------------
# Crear estructura de carpetas de proyecto
# ---------------------------------------------------------------------------

def crear_carpetas_proyecto(codigo_proyecto: str, tipo_jerarquia_id=None) -> str:
    """
    Crea la estructura de carpetas para un proyecto.
    Devuelve la ruta raíz creada como string.
    """
    base_path = get_app_setting("proyectos_base_path", "")
    if not base_path:
        base_path = str(Path(__file__).parent.parent / "PROYECTOS")

    carpeta_raiz = Path(base_path) / codigo_proyecto
    carpeta_raiz.mkdir(parents=True, exist_ok=True)

    # Obtener plantilla del tipo específico; si no tiene, usar la global
    carpetas = get_plantillas_carpetas(tipo_jerarquia_id)
    if not carpetas:
        carpetas = get_plantillas_carpetas(None)

    # Carpetas por defecto si no hay ninguna configurada
    if not carpetas:
        carpetas_default = [
            "01_Encargo",
            "02_Presupuesto",
            "03_Documentacion_cliente",
            "04_Trabajo_tecnico",
            "05_Entrega_final",
        ]
        for nombre in carpetas_default:
            (carpeta_raiz / nombre).mkdir(exist_ok=True)
    else:
        for c in carpetas:
            nombre = c.get("nombre_carpeta", "").strip()
            if nombre:
                (carpeta_raiz / nombre).mkdir(exist_ok=True)

    return str(carpeta_raiz)


def crear_tareas_oferta(offer_id: int, tipo_trabajo_codigo: str, referencia: str) -> int:
    """Crea tareas automáticas para una oferta aceptada. Devuelve nº de tareas creadas."""
    codigo = (tipo_trabajo_codigo or "").upper()
    plantilla = TAREA_PLANTILLAS.get(codigo, TAREA_PLANTILLAS["DEFAULT"])
    from datetime import datetime
    now = datetime.now().isoformat(timespec="seconds")
    creadas = 0
    with get_db() as db:
        for orden, (titulo, prioridad) in enumerate(plantilla):
            desc = f"Oferta {referencia}" if referencia else ""
            db.execute(
                """INSERT INTO tareas
                   (offer_id, titulo, descripcion, tipo, estado, prioridad, orden, created_at)
                   VALUES (?, ?, ?, 'auto', 'pendiente', ?, ?, ?)""",
                (offer_id, titulo, desc, prioridad, orden, now),
            )
            creadas += 1
    return creadas


# ════════════════════════════════════════════════════════════════════════════
#  Base de datos de vehículos (autocompletado de fichas técnicas)
# ════════════════════════════════════════════════════════════════════════════

SCHEMA_VEHICULOS = """
CREATE TABLE IF NOT EXISTS vehiculos_ficha (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula TEXT,
    bastidor TEXT,
    marca TEXT,
    modelo TEXT,
    tipo_vehiculo TEXT,
    version_vehiculo TEXT,
    categoria TEXT,
    distancia_ejes TEXT,
    longitud TEXT,
    anchura TEXT,
    altura TEXT,
    voladizo TEXT,
    tara TEXT,
    mma TEXT,
    mmta TEXT,
    mmtc TEXT,
    mmta_eje TEXT,
    mma_eje TEXT,
    plazas TEXT,
    cilindrada TEXT,
    potencia TEXT,
    combustible TEXT,
    vel_max TEXT,
    emisiones TEXT,
    co2 TEXT,
    pot_fiscal TEXT,
    carroceria TEXT,
    num_ejes TEXT,
    suspension TEXT,
    direccion TEXT,
    frenado TEXT,
    fabricante TEXT,
    fabricante_motor TEXT,
    cod_motor TEXT,
    ruido TEXT,
    homol_base TEXT,
    homol_completo TEXT,
    datos_extra TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(matricula, bastidor)
);
"""


def init_vehiculos_db():
    """Crea la tabla de vehículos si no existe."""
    with get_db() as db:
        db.executescript(SCHEMA_VEHICULOS)


def guardar_vehiculo(datos):
    """Guarda o actualiza un vehículo en la BD local.
    datos: dict con claves como MATRICULA, MARCA, MODELO, etc."""
    init_vehiculos_db()
    import json
    from datetime import datetime
    now = datetime.now().isoformat()

    mat = datos.get("MATRICULA", "").strip()
    bas = datos.get("NUM_BASTIDOR", "").strip()
    if not mat and not bas:
        return

    # Campos extra no mapeados
    campos_conocidos = {
        "MATRICULA", "NUM_BASTIDOR", "MARCA", "MODELO", "TIPO_VEHICULO",
        "VERSION_VEHICULO", "DISTANCIA_EJES", "LONGITUD_VEH", "ANCHURA_VEH",
        "ALTURA_VEH", "VOLADIZO_A", "TARA_VEHICULO_KG", "MMA", "MMTA", "MMTC",
        "MMTA_EJE_A", "MMA_EJE_A", "PLAZAS_A", "CILINDRADA_A", "POT_NETA_A",
        "COMBUSTIBLE_A", "VEL_MAX_A", "EMISIONES_A", "CO2_A", "POT_FISCAL_A",
        "CARROCERIA_A", "NUM_EJES", "SUSPENSION_A", "DIRECCION_A", "FRENADO_A",
        "FABR_BASE_A", "FABR_MOTOR_A", "COD_MOTOR_A", "RUIDO_A",
        "HOMOL_BASE_A", "HOMOL_COMPL_A",
    }
    extras = {k: v for k, v in datos.items() if k not in campos_conocidos and v}

    with get_db() as db:
        db.execute("""
            INSERT INTO vehiculos_ficha
            (matricula, bastidor, marca, modelo, tipo_vehiculo, version_vehiculo,
             categoria, distancia_ejes, longitud, anchura, altura, voladizo,
             tara, mma, mmta, mmtc, mmta_eje, mma_eje, plazas,
             cilindrada, potencia, combustible, vel_max, emisiones, co2,
             pot_fiscal, carroceria, num_ejes, suspension, direccion, frenado,
             fabricante, fabricante_motor, cod_motor, ruido,
             homol_base, homol_completo,
             datos_extra, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(matricula, bastidor) DO UPDATE SET
             marca=excluded.marca, modelo=excluded.modelo,
             tipo_vehiculo=excluded.tipo_vehiculo, version_vehiculo=excluded.version_vehiculo,
             distancia_ejes=excluded.distancia_ejes, longitud=excluded.longitud,
             anchura=excluded.anchura, altura=excluded.altura, voladizo=excluded.voladizo,
             tara=excluded.tara, mma=excluded.mma, mmta=excluded.mmta, mmtc=excluded.mmtc,
             mmta_eje=excluded.mmta_eje, mma_eje=excluded.mma_eje, plazas=excluded.plazas,
             cilindrada=excluded.cilindrada, potencia=excluded.potencia,
             combustible=excluded.combustible, vel_max=excluded.vel_max,
             emisiones=excluded.emisiones, co2=excluded.co2, pot_fiscal=excluded.pot_fiscal,
             carroceria=excluded.carroceria, num_ejes=excluded.num_ejes,
             suspension=excluded.suspension, direccion=excluded.direccion,
             frenado=excluded.frenado, fabricante=excluded.fabricante,
             fabricante_motor=excluded.fabricante_motor, cod_motor=excluded.cod_motor,
             ruido=excluded.ruido,
             homol_base=excluded.homol_base, homol_completo=excluded.homol_completo,
             datos_extra=excluded.datos_extra,
             updated_at=excluded.updated_at
        """, (
            mat, bas,
            datos.get("MARCA", ""), datos.get("MODELO", ""),
            datos.get("TIPO_VEHICULO", ""), datos.get("VERSION_VEHICULO", ""),
            datos.get("CATEGORIA_VEH", ""),
            datos.get("DISTANCIA_EJES", ""), datos.get("LONGITUD_VEH", ""),
            datos.get("ANCHURA_VEH", ""), datos.get("ALTURA_VEH", ""),
            datos.get("VOLADIZO_A", ""),
            datos.get("TARA_VEHICULO_KG", ""), datos.get("MMA", ""),
            datos.get("MMTA", ""), datos.get("MMTC", ""),
            datos.get("MMTA_EJE_A", ""), datos.get("MMA_EJE_A", ""),
            datos.get("PLAZAS_A", ""),
            datos.get("CILINDRADA_A", ""), datos.get("POT_NETA_A", ""),
            datos.get("COMBUSTIBLE_A", ""), datos.get("VEL_MAX_A", ""),
            datos.get("EMISIONES_A", ""), datos.get("CO2_A", ""),
            datos.get("POT_FISCAL_A", ""),
            datos.get("CARROCERIA_A", ""), datos.get("NUM_EJES", ""),
            datos.get("SUSPENSION_A", ""), datos.get("DIRECCION_A", ""),
            datos.get("FRENADO_A", ""),
            datos.get("FABR_BASE_A", ""), datos.get("FABR_MOTOR_A", ""),
            datos.get("COD_MOTOR_A", ""), datos.get("RUIDO_A", ""),
            datos.get("HOMOL_BASE_A", ""), datos.get("HOMOL_COMPL_A", ""),
            json.dumps(extras, ensure_ascii=False) if extras else "",
            now, now,
        ))


def buscar_vehiculo(matricula="", bastidor=""):
    """Busca un vehículo por matrícula o bastidor. Devuelve dict o None."""
    init_vehiculos_db()
    if matricula:
        row = query(
            "SELECT * FROM vehiculos_ficha WHERE matricula = ? LIMIT 1",
            (matricula.strip().upper(),), one=True)
        if row:
            return row
    if bastidor:
        row = query(
            "SELECT * FROM vehiculos_ficha WHERE bastidor = ? LIMIT 1",
            (bastidor.strip().upper(),), one=True)
        if row:
            return row
    return None


def buscar_vehiculos_por_texto(texto):
    """Busca vehículos por texto parcial en matrícula, bastidor, marca o modelo."""
    init_vehiculos_db()
    like = f"%{texto.strip()}%"
    return query(
        """SELECT * FROM vehiculos_ficha
           WHERE matricula LIKE ? OR bastidor LIKE ?
                 OR marca LIKE ? OR modelo LIKE ?
           ORDER BY updated_at DESC LIMIT 20""",
        (like, like, like, like))
