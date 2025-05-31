@echo off
chcp 65001 >nul
cd /d "%~dp0\.."

echo ========================================
echo    Ollama Manager EXE 打包脚本
echo ========================================
echo.

REM 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python 环境
    pause
    exit /b 1
)

echo [信息] Python 环境检测成功

REM 检查 uv 环境
uv --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 uv 包管理器
    echo 请先安装 uv: pip install uv
    pause
    exit /b 1
)

echo [信息] uv 包管理器检测成功

REM 安装 PyInstaller（如果尚未安装）
echo [信息] 检查 PyInstaller...
uv run python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [信息] 安装 PyInstaller...
    uv add --dev pyinstaller
    if errorlevel 1 (
        echo [错误] PyInstaller 安装失败
        pause
        exit /b 1
    )
)

echo [信息] PyInstaller 检查完成

REM 清理之前的构建文件
echo [信息] 清理之前的构建文件...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

REM 开始打包
echo [信息] 开始打包应用程序...
echo 这可能需要几分钟时间，请耐心等待...
echo.

uv run pyinstaller build.spec

if errorlevel 1 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo.
echo [成功] 打包完成！
echo [信息] 可执行文件位置: dist\OllamaManager.exe

REM 显示文件信息
if exist "dist\OllamaManager.exe" (
    echo.
    echo [文件信息]
    dir "dist\OllamaManager.exe"
    echo.
    echo [提示] 您可以运行 dist\OllamaManager.exe 来测试应用程序
    echo [提示] 可执行文件已包含所有依赖，可以在没有 Python 环境的机器上运行
else (
    echo [错误] 可执行文件未生成
    pause
    exit /b 1
)

echo.
echo [完成] 打包任务完成！
echo.
pause