"""Launcher para el preview tool — cambia al directorio correcto y arranca Flask."""
import os
import sys

# Ir al directorio raíz del proyecto (donde está tracker/)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Si ya estamos en el raíz, no cambiar
if os.path.exists(os.path.join(project_root, "tracker", "app.py")):
    os.chdir(project_root)
else:
    # Fallback: subir un nivel
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

sys.path.insert(0, "tracker")
exec(open("tracker/app.py").read())
