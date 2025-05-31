@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo    Ollama Manager Build Test Script
echo ========================================
echo.

REM Check Python environment
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python environment not detected
    pause
    exit /b 1
)

echo [INFO] Python environment detected

REM Check PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] PyInstaller installation failed
        pause
        exit /b 1
    )
)

echo [INFO] Checking dependencies...
python -c "import tkinter, requests, psutil" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Missing dependencies detected, installing...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Dependencies installation failed
        pause
        exit /b 1
    )
)

echo [INFO] Cleaning previous build files...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

echo [INFO] Starting build process...
pyinstaller build.spec

if errorlevel 1 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

echo [INFO] Build successful!
echo [INFO] Executable location: dist\OllamaManager.exe

REM Test executable
echo [INFO] Testing executable...
if exist "dist\OllamaManager.exe" (
    echo [SUCCESS] Executable generated
    dir "dist\OllamaManager.exe"
    echo.
    echo [INFO] You can run dist\OllamaManager.exe to test the application
else (
    echo [ERROR] Executable not generated
    pause
    exit /b 1
)

echo.
echo [COMPLETE] Build test completed!
pause