@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
color 0B
cd /d "%~dp0"

echo ========================================================
echo   UNIVERSAL PROSPECTING PLATFORM - INSTALLER  v9
echo   Codigo Origami - Alejandro Moreno
echo ========================================================
echo.

:: ------------------------------------------------------------------
:: 1. Find a compatible Python (3.10 - 3.13). Prefer the "py" launcher.
:: ------------------------------------------------------------------
set "PY_CMD="
for %%V in (3.12 3.13 3.11 3.10) do (
    if not defined PY_CMD (
        py -%%V --version >nul 2>&1 && set "PY_CMD=py -%%V"
    )
)
if not defined PY_CMD (
    python --version >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        for /f "tokens=2" %%I in ('python --version 2^>^&1') do set "PYV=%%I"
        for /f "tokens=1,2 delims=." %%a in ("!PYV!") do (
            if "%%a"=="3" if %%b GEQ 10 if %%b LEQ 13 set "PY_CMD=python"
        )
    )
)
if not defined PY_CMD (
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
)

if not defined PY_CMD (
    echo [INFO] No compatible Python found. Downloading Python 3.12 / Descargando Python 3.12...
    curl -L -o python_installer.exe https://www.python.org/ftp/python/3.12.6/python-3.12.6-amd64.exe
    if not exist python_installer.exe (
        echo [ERROR] Download failed. Check your internet connection.
        echo [ERROR] No se pudo descargar. Revisa tu conexion a internet.
        goto :error
    )
    echo [INFO] Installing Python silently (1-2 minutes) / Instalando Python (1-2 minutos)...
    start /wait python_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_pip=1 Include_launcher=1
    del python_installer.exe
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "!PY_CMD!" --version >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Python installation failed. Restart the computer and run this again.
        echo [ERROR] Fallo la instalacion de Python. Reinicia el ordenador y vuelve a ejecutarlo.
        goto :error
    )
)
echo [OK] Python: !PY_CMD!

:: ------------------------------------------------------------------
:: 2. Private environment for this app (does not touch other Python apps)
:: ------------------------------------------------------------------
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo [1/4] Creating private environment / Creando entorno privado...
    if "!PY_CMD:~0,3!"=="py " (
        !PY_CMD! -m venv .venv
    ) else (
        "!PY_CMD!" -m venv .venv
    )
    if not exist ".venv\Scripts\python.exe" goto :error
)
set "VPY=.venv\Scripts\python.exe"

echo.
echo [2/4] Updating pip / Actualizando pip...
"%VPY%" -m pip install --upgrade pip --quiet
if !ERRORLEVEL! NEQ 0 goto :error

echo.
echo [3/4] Installing libraries / Instalando librerias...
"%VPY%" -m pip install -r requirements.txt --quiet
if !ERRORLEVEL! NEQ 0 goto :error

echo.
echo [4/4] Installing the Chromium browser / Instalando el navegador Chromium...
"%VPY%" -m playwright install chromium
if !ERRORLEVEL! NEQ 0 goto :error

copy /y requirements.txt ".venv\requirements.installed" >nul
echo ok> ".venv\installed.ok"

echo.
echo ========================================================
echo   INSTALLATION COMPLETE / INSTALACION COMPLETADA
echo   Next time just double-click "start.bat"
echo   La proxima vez solo haz doble clic en "start.bat"
echo ========================================================
if /i not "%~1"=="/auto" pause
exit /b 0

:error
echo.
echo ========================================================
echo   INSTALLATION FAILED / LA INSTALACION FALLO
echo   Read the messages above / Lee los mensajes de arriba
echo ========================================================
pause
exit /b 1
