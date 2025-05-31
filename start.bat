@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo    Ollama Manager Quick Start
echo ========================================
echo.

REM Check uv environment
if exist "uv.lock" (
    echo [INFO] Starting with uv environment...
    uv run python ollama_manager.py
) else (
    echo [INFO] Starting with system Python...
    python ollama_manager.py
)

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start, please check Python environment
    echo To install dependencies, run: scripts\install_dependencies.py
    pause
)