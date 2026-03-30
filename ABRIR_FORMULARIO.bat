@echo off
cd /d "%~dp0"

:: Verificar que Python esta instalado
python --version >/dev/null 2>/dev/null
if errorlevel 1 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo.
    echo Instala Python desde https://www.python.org/downloads/
    echo Marca la opcion "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)

:: Lanzar el formulario (las dependencias se instalan solas si faltan)
python formulario.py
