@echo off
title Phican - Gestor
cd /d "%~dp0"

:: ── Auto-actualizar desde GitHub ──────────────────────────
where git >nul 2>&1
if errorlevel 1 goto sin_git
echo Comprobando actualizaciones...
git pull origin master --ff-only --quiet 2>nul
if errorlevel 1 (
    echo AVISO: No se pudo actualizar desde GitHub.
) else (
    echo Codigo actualizado correctamente.
)
goto lanzar

:sin_git
echo INFO: Git no encontrado, omitiendo actualizacion.

:lanzar
echo.

:: ── Buscar Python ─────────────────────────────────────────
set "PYTHON_EXE=C:\Users\ober_\AppData\Local\Python\pythoncore-3.14-64\python.exe"
if exist "%PYTHON_EXE%" goto python_ok
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado.
    pause
    exit /b 1
)
set "PYTHON_EXE=python"

:python_ok
:: ── Instalar Flask si falta ───────────────────────────────
"%PYTHON_EXE%" -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Instalando Flask...
    "%PYTHON_EXE%" -m pip install flask
)

:: ── Lanzar servidor ───────────────────────────────────────
echo.
echo  ===================================
echo    PHICAN - Registro de Trabajos
echo    http://localhost:5050
echo  ===================================
echo.
echo  Pulsa Ctrl+C para detener el servidor.
echo.
start "" http://localhost:5050
"%PYTHON_EXE%" tracker/app.py
