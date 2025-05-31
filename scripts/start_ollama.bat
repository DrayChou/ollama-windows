@echo off
echo ?? Ollama ??...
echo ??????:
echo   OLLAMA_MODELS=D:\Code\ollama-windows\models
echo   OLLAMA_HOST=0.0.0.0
echo   HSA_OVERRIDE_GFX_VERSION=11.0.0

echo.

rem ??????
set OLLAMA_MODELS=D:\Code\ollama-windows\models
set OLLAMA_HOST=0.0.0.0
set HSA_OVERRIDE_GFX_VERSION=11.0.0


rem ?? Ollama
echo ???? Ollama...
ollama.exe start
