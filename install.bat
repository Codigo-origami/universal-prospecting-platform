@echo off
color 0B
setlocal enabledelayedexpansion

echo ========================================================
echo   UNIVERSAL LEAD GENERATOR INSTALLER - Codigo Origami
echo ========================================================
echo.

set "PY_CMD=python"

:: 1. Detect if Python is installed
%PY_CMD% --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Python not detected on this system.
    echo [INFO] Downloading the core engine automatically...
    curl -o python_installer.exe https://www.python.org/ftp/python/3.12.6/python-3.12.6-amd64.exe
    
    if not exist python_installer.exe (
        echo [ERROR] Could not download the engine. Please check your internet connection.
        pause
        exit /b 1
    )

    echo [INFO] Installing the environment silently ^(this will take 1-2 minutes^)...
    start /wait python_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_pip=1
    del python_installer.exe
    
    echo [INFO] Environment installed successfully.
    
    :: Use the direct path since Windows doesn't update the PATH until the console is restarted
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    
    !PY_CMD! --version >nul 2>&1
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] A problem occurred during the automatic installation.
        echo Please restart your computer and try again.
        pause
        exit /b 1
    )
)

:: 2. Validate they don't have version 3.14+ (which breaks dependencies)
for /f "tokens=2" %%I in ('!PY_CMD! --version 2^>^&1') do set PYTHON_VERSION=%%I
echo Detected Python version: !PYTHON_VERSION!

for /f "tokens=1,2 delims=." %%a in ("!PYTHON_VERSION!") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if !MINOR! GEQ 14 (
    echo [ERROR] You have an experimental version of Python ^(3.14+^).
    echo Please uninstall Python from the Control Panel and run this installer again.
    pause
    exit /b 1
)

:: 3. Strict installation
echo.
echo [1/3] Updating pip...
!PY_CMD! -m pip install --upgrade pip >nul
if !ERRORLEVEL! NEQ 0 goto :error

echo.
echo [2/3] Installing required libraries...
!PY_CMD! -m pip install -r requirements.txt
if !ERRORLEVEL! NEQ 0 goto :error

echo.
echo [3/3] Installing Playwright Chromium browser...
!PY_CMD! -m playwright install chromium
if !ERRORLEVEL! NEQ 0 goto :error

echo.
echo ========================================================
echo   INSTALLATION COMPLETE!
echo   You can now close this window and run "start.bat"
echo ========================================================
pause
exit /b 0

:error
echo.
echo ========================================================
echo   INSTALLATION FAILED!
echo   Please resolve the errors mentioned above.
echo ========================================================
pause
exit /b 1