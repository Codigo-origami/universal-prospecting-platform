@echo off
chcp 65001 >nul
color 0A
cd /d "%~dp0"
title Universal Prospecting Platform - Codigo Origami / Alejandro Moreno

echo Starting Universal Prospecting Platform...
echo Iniciando Universal Prospecting Platform...
echo.

rem Streamlit asks for an email on its very first run: answer it once so it never blocks
if exist "%USERPROFILE%\.streamlit\credentials.toml" goto :creds_ok
mkdir "%USERPROFILE%\.streamlit" >nul 2>&1
> "%USERPROFILE%\.streamlit\credentials.toml" echo [general]
>> "%USERPROFILE%\.streamlit\credentials.toml" echo email = ""
:creds_ok

rem First run, or requirements changed: install everything automatically
if not exist ".venv\Scripts\python.exe" goto :install
if not exist ".venv\installed.ok" goto :install
fc /b "requirements.txt" ".venv\requirements.installed" >nul 2>&1
if errorlevel 1 goto :install
goto :run

:install
echo First run: installing everything needed - only once, 3-5 minutes...
echo Primera vez: instalando todo lo necesario - solo una vez, 3-5 minutos...
echo.
cmd /c ""%~dp0install.bat" /auto"
if errorlevel 1 goto :failed
if not exist ".venv\installed.ok" goto :failed

:run
".venv\Scripts\python.exe" -m streamlit run app.py
echo.
echo The app has stopped. / La app se ha detenido.
pause
exit /b 0

:failed
echo.
echo Installation did not finish. Send a screenshot of this window.
echo La instalacion no termino. Envia una captura de esta ventana.
pause
exit /b 1
