@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo    Ollama Manager v2.0 Startup Script
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not detected, please install Python 3.8 or higher
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [INFO] Python environment detected

REM Check virtual environment
if exist ".venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] No virtual environment detected, using system Python
)

REM Check dependencies
echo [INFO] Checking dependencies...
python -c "import tkinter, requests, psutil" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Missing dependencies detected, installing automatically...
    python install_dependencies.py
    if errorlevel 1 (
        echo [ERROR] Dependency installation failed, please run manually: pip install -r requirements.txt
        pause
        exit /b 1
    )
)

echo [INFO] Starting Ollama Manager...
echo.

REM Start program
python ollama_manager.py

REM Show error if program exits abnormally
if errorlevel 1 (
    echo.
    echo [ERROR] Program exited abnormally, error code: %errorlevel%
    echo Please check log file ollama_manager.log for details
    pause
)
