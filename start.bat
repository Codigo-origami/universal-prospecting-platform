@echo off
chcp 65001 >nul
color 0A
cd /d "%~dp0"
title Universal Prospecting Platform - Codigo Origami / Alejandro Moreno

echo Starting Universal Prospecting Platform...
echo Iniciando Universal Prospecting Platform...
echo.

:: First run, or requirements changed: install everything automatically
if not exist ".venv\Scripts\python.exe" goto :install
if not exist ".venv\installed.ok" goto :install
fc /b "requirements.txt" ".venv\requirements.installed" >nul 2>&1
if errorlevel 1 goto :install
goto :run

:install
echo First run: installing everything needed (only once, 3-5 minutes)...
echo Primera vez: instalando todo lo necesario (solo una vez, 3-5 minutos)...
echo.
call "%~dp0install.bat" /auto
if errorlevel 1 exit /b 1

:run
".venv\Scripts\python.exe" -m streamlit run app.py
pause
