@echo off
color 0A
echo Starting Universal Lead Generator by Codigo Origami...

set "PY_CMD=python"
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    :: If the global command does not respond yet, use the direct path where we installed it
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
)

"%PY_CMD%" -m streamlit run app.py
pause