"""
Base de datos SQLite para catálogo de plantillas de vehículos.
Sigue el patrón de tracker/db.py: context manager, query/execute helpers.
"""

import hashlib
import json
import os
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path


# Detectar modo frozen (PyInstaller)
if getattr(sys, 'frozen', False):
    _BASE = Path(sys.executable).parent
else:
    _BASE = Path(__file__).parent

DB_PATH = _BASE / "vehiculos.db"


# =============================================================================
# ESQUEMA
# =============================================================================

SCHEMA = """
CREATE TABLE IF NOT EXISTS vehicle_makes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    name_display TEXT DEFAULT '',
    source TEXT DEFAULT '',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vehicle_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    make_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    year_start INTEGER,
    year_end INTEGER,
    body_type TEXT DEFAULT '',
    source TEXT DEFAULT '',
    updated_at TEXT NOT NULL,
    FOREIGN KEY (make_id) REFERENCES vehicle_makes(id),
    UNIQUE(make_id, name, year_start)
);

CREATE TABLE IF NOT EXISTS vehicle_dimensions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL,
    year INTEGER,
    length_mm INTEGER,
    width_mm INTEGER,
    height_mm INTEGER,
    wheelbase_mm INTEGER,
    weight_kg INTEGER,
    source TEXT DEFAULT '',
    raw_data TEXT DEFAULT '{}',
    updated_at TEXT NOT NULL,
    FOREIGN KEY (model_id) REFERENCES vehicle_models(id)
);

CREATE TABLE IF NOT EXISTS vehicle_blueprints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER,
    make_name TEXT NOT NULL,
    model_name TEXT NOT NULL,
    year INTEGER,
    source_key TEXT NOT NULL,
    source_url TEXT DEFAULT '',
    file_path TEXT NOT NULL,
    file_format TEXT DEFAULT '',
    view_type TEXT DEFAULT 'mixed',
    width_px INTEGER,
    height_px INTEGER,
    file_size INTEGER,
    thumbnail_path TEXT DEFAULT '',
    is_favorite INTEGER DEFAULT 0,
    notes TEXT DEFAULT '',
    downloaded_at TEXT NOT NULL,
    FOREIGN KEY (model_id) REFERENCES vehicle_models(id)
);

CREATE TABLE IF NOT EXISTS search_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_key TEXT NOT NULL,
    query_hash TEXT NOT NULL,
    results_json TEXT NOT NULL,
    cached_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    UNIQUE(provider_key, query_hash)
);
"""


# =============================================================================
# CONEXIÓN
# =============================================================================

def init_db():
    """Inicializa la base de datos y crea las tablas si no existen."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;")
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


@contextmanager
def get_db():
    """Context manager para conexiones a la base de datos."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
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
    """Ejecuta una consulta SELECT y devuelve dicts."""
    with get_db() as conn:
        rows = conn.execute(sql, params).fetchall()
        result = [dict(r) for r in rows]
        if one:
            return result[0] if result else None
        return result


def execute(sql, params=()):
    """Ejecuta INSERT/UPDATE/DELETE y devuelve lastrowid."""
    with get_db() as conn:
        cursor = conn.execute(sql, params)
        return cursor.lastrowid


# =============================================================================
# HELPERS: MARCAS Y MODELOS
# =============================================================================

def get_makes(source=None):
    """Devuelve lista de marcas, opcionalmente filtrada por fuente."""
    if source:
        return query("SELECT * FROM vehicle_makes WHERE source=? ORDER BY name",
                     (source,))
    return query("SELECT * FROM vehicle_makes ORDER BY name")


def get_models(make_id=None, make_name=None):
    """Devuelve modelos por make_id o make_name."""
    if make_id:
        return query(
            "SELECT * FROM vehicle_models WHERE make_id=? ORDER BY name",
            (make_id,))
    if make_name:
        make = query(
            "SELECT id FROM vehicle_makes WHERE UPPER(name)=UPPER(?)",
            (make_name,), one=True)
        if make:
            return query(
                "SELECT * FROM vehicle_models WHERE make_id=? ORDER BY name",
                (make["id"],))
    return []


def save_make(name, name_display="", source=""):
    """Inserta o actualiza una marca. Devuelve el ID."""
    now = datetime.now().isoformat()
    existing = query("SELECT id FROM vehicle_makes WHERE UPPER(name)=UPPER(?)",
                     (name,), one=True)
    if existing:
        execute("UPDATE vehicle_makes SET name_display=?, source=?, updated_at=? "
                "WHERE id=?", (name_display or name, source, now, existing["id"]))
        return existing["id"]
    return execute(
        "INSERT INTO vehicle_makes (name, name_display, source, updated_at) "
        "VALUES (?, ?, ?, ?)",
        (name.upper(), name_display or name, source, now))


def save_model(make_id, name, year_start=None, year_end=None,
               body_type="", source=""):
    """Inserta o actualiza un modelo. Devuelve el ID."""
    now = datetime.now().isoformat()
    existing = query(
        "SELECT id FROM vehicle_models "
        "WHERE make_id=? AND UPPER(name)=UPPER(?) AND "
        "(year_start=? OR (year_start IS NULL AND ? IS NULL))",
        (make_id, name, year_start, year_start), one=True)
    if existing:
        execute("UPDATE vehicle_models SET year_end=?, body_type=?, source=?, "
                "updated_at=? WHERE id=?",
                (year_end, body_type, source, now, existing["id"]))
        return existing["id"]
    return execute(
        "INSERT INTO vehicle_models "
        "(make_id, name, year_start, year_end, body_type, source, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (make_id, name, year_start, year_end, body_type, source, now))


# =============================================================================
# HELPERS: DIMENSIONES
# =============================================================================

def save_dimensions(model_id, year, dims, source=""):
    """Guarda dimensiones de un vehículo."""
    now = datetime.now().isoformat()
    return execute(
        "INSERT OR REPLACE INTO vehicle_dimensions "
        "(model_id, year, length_mm, width_mm, height_mm, wheelbase_mm, "
        "weight_kg, source, raw_data, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (model_id, year,
         dims.get("length_mm"), dims.get("width_mm"),
         dims.get("height_mm"), dims.get("wheelbase_mm"),
         dims.get("weight_kg"), source,
         json.dumps(dims), now))


def get_dimensions(model_id=None, make_name=None, model_name=None, year=None):
    """Obtiene dimensiones por model_id o por nombre."""
    if model_id:
        return query(
            "SELECT * FROM vehicle_dimensions WHERE model_id=? "
            "ORDER BY year DESC LIMIT 1",
            (model_id,), one=True)
    if make_name and model_name:
        sql = """
            SELECT d.* FROM vehicle_dimensions d
            JOIN vehicle_models m ON d.model_id = m.id
            JOIN vehicle_makes mk ON m.make_id = mk.id
            WHERE UPPER(mk.name) = UPPER(?)
            AND UPPER(m.name) = UPPER(?)
        """
        params = [make_name, model_name]
        if year:
            sql += " AND d.year = ?"
            params.append(year)
        sql += " ORDER BY d.year DESC LIMIT 1"
        return query(sql, params, one=True)
    return None


# =============================================================================
# HELPERS: BLUEPRINTS
# =============================================================================

def save_blueprint(make_name, model_name, year, source_key, source_url,
                   file_path, file_format="", view_type="mixed",
                   width_px=0, height_px=0, file_size=0,
                   thumbnail_path="", model_id=None):
    """Registra una plantilla descargada en la base de datos."""
    now = datetime.now().isoformat()
    return execute(
        "INSERT INTO vehicle_blueprints "
        "(model_id, make_name, model_name, year, source_key, source_url, "
        "file_path, file_format, view_type, width_px, height_px, file_size, "
        "thumbnail_path, downloaded_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (model_id, make_name.upper(), model_name, year, source_key,
         source_url, file_path, file_format, view_type,
         width_px, height_px, file_size, thumbnail_path, now))


def find_blueprint(make, model, year=None, source=None):
    """Busca una plantilla en la base de datos local."""
    sql = ("SELECT * FROM vehicle_blueprints "
           "WHERE UPPER(make_name)=UPPER(?) AND UPPER(model_name)=UPPER(?)")
    params = [make, model]
    if year:
        sql += " AND year=?"
        params.append(year)
    if source:
        sql += " AND source_key=?"
        params.append(source)
    sql += " ORDER BY downloaded_at DESC"
    return query(sql, params)


def get_cached_blueprints(make=None, model=None):
    """Devuelve todas las plantillas descargadas, opcionalmente filtradas."""
    sql = "SELECT * FROM vehicle_blueprints WHERE 1=1"
    params = []
    if make:
        sql += " AND UPPER(make_name)=UPPER(?)"
        params.append(make)
    if model:
        sql += " AND UPPER(model_name)=UPPER(?)"
        params.append(model)
    sql += " ORDER BY make_name, model_name, downloaded_at DESC"
    return query(sql, params)


def delete_blueprint(blueprint_id):
    """Elimina un registro de plantilla de la BD."""
    execute("DELETE FROM vehicle_blueprints WHERE id=?", (blueprint_id,))


# =============================================================================
# HELPERS: CACHE DE BÚSQUEDAS
# =============================================================================

def _hash_query(provider_key, **kwargs):
    """Genera hash para clave de cache."""
    data = json.dumps({"provider": provider_key, **kwargs}, sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()


def get_search_cache(provider_key, query_hash):
    """Obtiene resultados cacheados si no han expirado."""
    now = datetime.now().isoformat()
    result = query(
        "SELECT * FROM search_cache "
        "WHERE provider_key=? AND query_hash=? AND expires_at > ?",
        (provider_key, query_hash, now), one=True)
    if result:
        return json.loads(result["results_json"])
    return None


def get_search_cache_expired(provider_key, query_hash):
    """Obtiene resultados cacheados aunque hayan expirado (modo offline)."""
    result = query(
        "SELECT * FROM search_cache WHERE provider_key=? AND query_hash=?",
        (provider_key, query_hash), one=True)
    if result:
        return json.loads(result["results_json"])
    return None


def set_search_cache(provider_key, query_hash, results, ttl_hours=24):
    """Guarda resultados de búsqueda en cache."""
    now = datetime.now()
    expires = now + timedelta(hours=ttl_hours)
    execute(
        "INSERT OR REPLACE INTO search_cache "
        "(provider_key, query_hash, results_json, cached_at, expires_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (provider_key, query_hash, json.dumps(results),
         now.isoformat(), expires.isoformat()))


# Inicializar BD al importar
init_db()
