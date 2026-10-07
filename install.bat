@echo off
setlocal
chcp 65001 >nul
color 0B
cd /d "%~dp0"

echo ========================================================
echo   UNIVERSAL PROSPECTING PLATFORM - INSTALLER  v9
echo   Codigo Origami - Alejandro Moreno
echo ========================================================
echo.

rem ------------------------------------------------------------------
rem 1. Find a compatible Python 3.10 - 3.13
rem ------------------------------------------------------------------
set "PY_CMD="
call :try_py "py -3.12"
call :try_py "py -3.13"
call :try_py "py -3.11"
call :try_py "py -3.10"
call :try_py "python"
if not defined PY_CMD if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PY_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if defined PY_CMD goto :have_python

echo [INFO] No compatible Python found - downloading Python 3.12...
echo [INFO] No se encontro Python compatible - descargando Python 3.12...
curl -L -o python_installer.exe https://www.python.org/ftp/python/3.12.6/python-3.12.6-amd64.exe
if not exist python_installer.exe goto :err_download
echo [INFO] Installing Python, 1-2 minutes... / Instalando Python, 1-2 minutos...
start /wait "" python_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_pip=1 Include_launcher=1
del python_installer.exe
set PY_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
%PY_CMD% --version >nul 2>&1
if errorlevel 1 goto :err_python

:have_python
echo [OK] Python: %PY_CMD%

rem ------------------------------------------------------------------
rem 2. Private environment for this app - does not touch other Python apps
rem ------------------------------------------------------------------
if exist ".venv\Scripts\python.exe" goto :have_venv
echo.
echo [1/4] Creating private environment / Creando entorno privado...
%PY_CMD% -m venv .venv
if not exist ".venv\Scripts\python.exe" goto :error
:have_venv

echo.
echo [2/4] Updating pip / Actualizando pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
if errorlevel 1 goto :error

echo.
echo [3/4] Installing libraries / Instalando librerias...
".venv\Scripts\python.exe" -m pip install -r requirements.txt --quiet
if errorlevel 1 goto :error

echo.
echo [4/4] Installing the Chromium browser / Instalando el navegador Chromium...
".venv\Scripts\python.exe" -m playwright install chromium
if errorlevel 1 goto :error

copy /y requirements.txt ".venv\requirements.installed" >nul
echo ok> ".venv\installed.ok"

echo.
echo ========================================================
echo   INSTALLATION COMPLETE / INSTALACION COMPLETADA
echo   Next time just double-click start.bat
echo   La proxima vez solo haz doble clic en start.bat
echo ========================================================
if /i not "%~1"=="/auto" pause
exit /b 0

rem ------------------------------------------------------------------
:try_py
if defined PY_CMD exit /b 0
%~1 -c "import sys; sys.exit(0 if (3,10) <= sys.version_info[:2] <= (3,13) else 1)" >nul 2>&1
if errorlevel 1 exit /b 0
set "PY_CMD=%~1"
exit /b 0

:err_download
echo [ERROR] Download failed. Check your internet connection.
echo [ERROR] No se pudo descargar. Revisa tu conexion a internet.
goto :error

:err_python
echo [ERROR] Python installation failed. Restart the computer and run start.bat again.
echo [ERROR] Fallo la instalacion de Python. Reinicia el ordenador y vuelve a ejecutar start.bat.
goto :error

:error
echo.
echo ========================================================
echo   INSTALLATION FAILED / LA INSTALACION FALLO
echo   Read the messages above / Lee los mensajes de arriba
echo ========================================================
pause
exit /b 1
