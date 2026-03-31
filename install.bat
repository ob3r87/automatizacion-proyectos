@echo off
setlocal enabledelayedexpansion
title Phican Ingenieros — Instalador
color 0B

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   PHICAN INGENIEROS — Instalador v1.0   ║
echo  ╚══════════════════════════════════════════╝
echo.

:: ── 1. Buscar Python ──────────────────────────────────────────────
set "PYTHON_EXE="
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
    "%LOCALAPPDATA%\Python\pythoncore-3.13-64\python.exe"
) do (
    if exist %%P (
        set "PYTHON_EXE=%%~P"
        goto :found_python
    )
)
where python >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=*" %%i in ('where python') do (
        set "PYTHON_EXE=%%i"
        goto :found_python
    )
)
echo [ERROR] No se encontro Python 3.10+. Descargalo desde https://python.org
pause & exit /b 1

:found_python
echo [OK] Python encontrado: %PYTHON_EXE%

:: ── 2. Verificar version Python ───────────────────────────────────
for /f "tokens=2 delims= " %%v in ('"%PYTHON_EXE%" --version 2^>^&1') do set "PY_VER=%%v"
echo [OK] Version: %PY_VER%

:: ── 3. Crear entorno virtual ──────────────────────────────────────
set "VENV_DIR=%~dp0.venv"
if not exist "%VENV_DIR%" (
    echo [..] Creando entorno virtual en .venv ...
    "%PYTHON_EXE%" -m venv "%VENV_DIR%"
    if errorlevel 1 ( echo [ERROR] Fallo al crear venv. & pause & exit /b 1 )
    echo [OK] Entorno virtual creado.
) else (
    echo [OK] Entorno virtual existente detectado.
)

set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"

:: ── 4. Instalar dependencias ──────────────────────────────────────
echo [..] Instalando dependencias (Flask, ReportLab, python-docx)...
"%VENV_PIP%" install --upgrade pip -q
"%VENV_PIP%" install -r "%~dp0requirements.txt" -q
if errorlevel 1 ( echo [ERROR] Fallo al instalar dependencias. & pause & exit /b 1 )
echo [OK] Dependencias instaladas.

:: ── 5. Inicializar base de datos ──────────────────────────────────
echo [..] Inicializando base de datos...
"%VENV_PYTHON%" -c "import sys; sys.path.insert(0,'%~dp0tracker'); from db import init_db, init_crm_db; init_db(); init_crm_db(); print('[OK] Base de datos inicializada.')"

:: ── 6. Crear config.json si no existe ────────────────────────────
if not exist "%~dp0config.json" (
    echo [..] Creando configuracion inicial...
    "%VENV_PYTHON%" -c "import json,pathlib; p=pathlib.Path(r'%~dp0'); cfg={'OUTPUT_PATH':str(p/'proyectos_generados'),'TEMPLATE_PROYECTO':str(p/'PLANTILLA_BASE.docx'),'TEMPLATE_CFO':str(p/'PLANTILLA_CFO.docx'),'TEMPLATE_CT':str(p/'PLANTILLA_CT.docx')}; (p/'config.json').write_text(json.dumps(cfg,indent=2,ensure_ascii=False)); print('[OK] config.json creado.')"
)

:: ── 7. Crear acceso directo en escritorio ─────────────────────────
echo [..] Creando accesos directos en el escritorio...
set "DESKTOP=%USERPROFILE%\Desktop"
set "SCRIPT_DIR=%~dp0"

:: Shortcut: Gestor (Tracker Web)
set "VBS_TEMP=%TEMP%\create_shortcut_gestor.vbs"
(
echo Set oWS = WScript.CreateObject^("WScript.Shell"^)
echo sLinkFile = "%DESKTOP%\Phican - Gestor.lnk"
echo Set oLink = oWS.CreateShortcut^(sLinkFile^)
echo oLink.TargetPath = "%SCRIPT_DIR%ABRIR_TRACKER.bat"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%"
echo oLink.IconLocation = "%SystemRoot%\System32\SHELL32.dll,14"
echo oLink.Description = "Phican Ingenieros - Gestor de Trabajos CRM"
echo oLink.WindowStyle = 7
echo oLink.Save
) > "%VBS_TEMP%"
cscript //nologo "%VBS_TEMP%"

:: Shortcut: Formulario
set "VBS_TEMP2=%TEMP%\create_shortcut_form.vbs"
(
echo Set oWS = WScript.CreateObject^("WScript.Shell"^)
echo sLinkFile = "%DESKTOP%\Phican - Formulario.lnk"
echo Set oLink = oWS.CreateShortcut^(sLinkFile^)
echo oLink.TargetPath = "%VENV_DIR%\Scripts\pythonw.exe"
echo oLink.Arguments = Chr^(34^) ^& "%SCRIPT_DIR%formulario.py" ^& Chr^(34^)
echo oLink.WorkingDirectory = "%SCRIPT_DIR%"
echo oLink.IconLocation = "%SystemRoot%\System32\SHELL32.dll,1"
echo oLink.Description = "Phican Ingenieros - Formulario de Proyectos"
echo oLink.Save
) > "%VBS_TEMP2%"
cscript //nologo "%VBS_TEMP2%"

echo [OK] Accesos directos creados en el escritorio.

:: ── 8. Actualizar ABRIR_TRACKER.bat para usar venv ────────────────
echo [..] Actualizando script de arranque...
(
echo @echo off
echo setlocal
echo set "DIR=%%~dp0"
echo set "PYTHON=%%DIR%%.venv\Scripts\python.exe"
echo if not exist "%%PYTHON%%" set "PYTHON=python"
echo cd /d "%%DIR%%tracker"
echo start "" "%%DIR%%.venv\Scripts\pythonw.exe" -c "import webbrowser,time,threading; threading.Timer(1.5,lambda:webbrowser.open('http://localhost:5050')).start()"
echo "%%PYTHON%%" app.py
echo endlocal
) > "%~dp0ABRIR_TRACKER.bat"

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║        Instalacion completada ^!          ║
echo  ║                                          ║
echo  ║  Accesos directos creados:               ║
echo  ║  - Phican - Gestor (escritorio)          ║
echo  ║  - Phican - Formulario (escritorio)      ║
echo  ╚══════════════════════════════════════════╝
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
