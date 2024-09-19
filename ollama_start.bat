@echo off
setlocal enabledelayedexpansion

@REM 设置控制台编码为 UTF-8
chcp 65001 >nul

@REM 启动同目录下的 ollama_start.ps1 脚本，并关闭当前 cmd 窗口
start "" pwsh -ExecutionPolicy Bypass -Command "& { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; . '%~dp0ollama_start.ps1' }"

@REM 关闭当前 cmd 窗口
exit