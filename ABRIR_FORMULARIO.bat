@echo off
cd /d "%~dp0"

:: ─── Auto-actualizar desde GitHub ───────────────────────────────────────────
where git >nul 2>&1
if %errorlevel%==0 (
    echo Comprobando actualizaciones en GitHub...
    git -C "%~dp0" pull origin master --ff-only --quiet 2>nul
    if %errorlevel%==0 (
        echo OK - Codigo actualizado.
    ) else (
        echo [AVISO] No se pudo actualizar desde GitHub (sin conexion o conflicto).
    )
) else (
    echo [INFO] Git no esta instalado; omitiendo actualizacion automatica.
)
echo.

:: ─── Verificar Python ────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo.
    echo Instala Python desde https://www.python.org/downloads/
    echo Marca la opcion "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)

:: ─── Lanzar formulario (instala dependencias si faltan) ──────────────────────
python formulario.py
