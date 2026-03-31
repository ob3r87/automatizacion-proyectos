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

:: ─── Buscar Python ───────────────────────────────────────────────────────────
set "PYTHON_EXE=C:\Users\ober_\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if not exist "%PYTHON_EXE%" (
    where python >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Python no esta instalado o no esta en el PATH.
        pause
        exit /b 1
    )
    set "PYTHON_EXE=python"
)

:: ─── Instalar Flask si no existe ─────────────────────────────────────────────
"%PYTHON_EXE%" -c "import flask" 2>nul
if errorlevel 1 (
    echo Instalando Flask...
    "%PYTHON_EXE%" -m pip install flask
)

:: ─── Lanzar servidor ─────────────────────────────────────────────────────────
echo.
echo  ===================================
echo    Registro de Trabajos Diarios
echo    http://localhost:5050
echo  ===================================
echo.
echo  Pulsa Ctrl+C para detener el servidor.
echo.
start http://localhost:5050
"%PYTHON_EXE%" tracker/app.py
