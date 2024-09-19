@echo off
setlocal enabledelayedexpansion

@REM 设置控制台编码为 UTF-8
chcp 65001 >nul

@REM 检查 pwsh 是否存在
where pwsh >nul 2>&1
if %errorlevel%==0 (
    @REM 使用 pwsh 启动脚本
    start "" pwsh -WindowStyle Hidden -ExecutionPolicy Bypass -Command "& { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; . '%~dp0ollama_start.ps1' }"
) else (
    @REM 使用 powershell 启动脚本
    start "" powershell -WindowStyle Hidden -ExecutionPolicy Bypass -Command "& { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; . '%~dp0ollama_start.ps1' }"
)

@REM 关闭当前 cmd 窗口
exit