"""Launcher para la webapp PHICAN — ejecutar desde cualquier directorio."""
import os, sys

# Cambiar al directorio raíz del proyecto (padre de AUTOMATIZACION_PROYECTOS)
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "tracker"))

# Importar DESPUÉS de cambiar CWD
from db import init_db, init_crm_db, init_vehiculos_db, init_work_types_defaults, init_ensayo_types_defaults
from app import app

init_db()
init_crm_db()
init_vehiculos_db()
init_work_types_defaults()
init_ensayo_types_defaults()

app.jinja_env.auto_reload = True
app.config["TEMPLATES_AUTO_RELOAD"] = True

print(f"PHICAN WebApp en http://127.0.0.1:5050")
app.run(host="0.0.0.0", port=5050)
