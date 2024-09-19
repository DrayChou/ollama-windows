# 项目名称

## 简介

这是一个示例项目，包含一个用于检查和更新 Ollama 版本的 PowerShell 脚本。该项目还包含一个 `.gitignore` 文件，用于忽略特定类型的文件和目录。

## 文件结构

- `ollama_start.bat`：用于启动 PowerShell 脚本并关闭当前 cmd 窗口。
- `ollama_start.ps1`：用于检查和更新 Ollama 版本的 PowerShell 脚本。
- `.gitignore`：用于忽略特定类型的文件和目录。
- `README.md`：项目的说明文档。

## 使用方法

1. 确保已安装 PowerShell 7 并且 `pwsh` 命令在系统的 PATH 环境变量中可用。
2. 运行 `ollama_start.bat` 文件，该文件将启动 `ollama_start.ps1` 脚本并关闭当前 cmd 窗口。

### 示例

在命令行中运行以下命令：

```sh
.\ollama_start.bat
```

## 常用命令

### 检查 Ollama 版本

```sh
ollama --version
```

### 批量更新 Ollama models

```powershell
ollama list | Select-Object -Skip 2 | ForEach-Object { $name = $_.Split()[0]; Write-Host "Pulling model: $name"; ollama pull $name }
```

## 贡献

欢迎提交问题和请求。如果您有任何建议或改进，请随时提交 Pull Request。

## 许可证

该项目使用 MIT 许可证。有关详细信息，请参阅 LICENSE 文件。
