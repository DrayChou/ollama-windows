@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo    项目目录整理脚本
echo ========================================
echo.

REM 创建archive目录用于存放旧文件
if not exist "archive" mkdir "archive"

echo [信息] 移动旧版本文件到archive目录...

REM 移动旧的管理器文件（保留用户指定的文件）
if exist "ollama_manager_fixed.py" (
    move "ollama_manager_fixed.py" "archive\"
    echo [移动] ollama_manager_fixed.py -> archive/
)

if exist "ollama_manager_simple.py" (
    move "ollama_manager_simple.py" "archive\"
    echo [移动] ollama_manager_simple.py -> archive/
)

if exist "ollama_manager_old.py" (
    move "ollama_manager_old.py" "archive\"
    echo [移动] ollama_manager_old.py -> archive/
)

REM 移动其他可能的临时文件
if exist "*.pyc" (
    move "*.pyc" "archive\" 2>nul
    echo [移动] Python缓存文件 -> archive/
)

if exist "__pycache__" (
    move "__pycache__" "archive\" 2>nul
    echo [移动] __pycache__ -> archive/
)

REM 创建docs目录并移动文档
if not exist "docs" mkdir "docs"

echo.
echo [信息] 当前项目结构:
echo.
echo 📁 主要文件:
echo   📄 ollama_manager.py          # 主程序入口
echo   📄 README.md                 # 项目说明
echo   📄 requirements.txt          # 依赖列表
echo   📄 start_manager.bat         # 启动脚本
echo   📄 install_dependencies.py   # 依赖安装
echo.
echo 📁 构建相关:
echo   📄 build.spec                # PyInstaller配置
echo   📄 version_info.txt          # 版本信息
echo   📄 build_test.bat            # 构建测试脚本
echo   📁 .github/workflows/        # GitHub Actions
echo   📁 assets/                   # 资源文件
echo.
echo 📁 源代码:
echo   📁 src/                      # 源代码目录
echo     📁 core/                   # 核心功能
echo     📁 ui/                     # 用户界面
echo     📁 utils/                  # 工具模块
echo.
echo 📁 保留文件（用户指定）:
echo   📄 ollama_start.bat          # 用户脚本
echo   📄 ollama_start.ps1          # 用户脚本
echo   📄 start_ollama.bat          # 用户脚本
echo   📄 ollama.jsonc              # 配置文件
echo.
echo 📁 归档文件:
echo   📁 archive/                  # 旧版本文件
echo.
echo [完成] 项目目录整理完成！
echo [提示] 旧文件已移动到 archive/ 目录
echo [提示] 用户指定的脚本文件已保留在根目录
echo.
pause