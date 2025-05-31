# Ollama Manager v2.0

一个功能强大的 Ollama 管理工具，提供图形化界面来管理 Ollama 服务、模型和配置。

### 🚀 服务管理
- **一键启动/停止/重启** Ollama 服务
- **实时状态监控** 显示服务运行状态和版本信息
- **自动启动** 支持程序启动时自动启动 Ollama 服务
- **进程管理** 智能检测和管理 Ollama 进程

### 📦 模型管理
- **模型列表** 查看已安装的所有模型及其详细信息
- **一键下载** 支持从官方仓库下载模型
- **推荐模型** 提供常用模型的快速下载
- **模型删除** 安全删除不需要的模型
- **下载进度** 实时显示模型下载进度

### 💬 对话测试
- **模型对话** 直接在界面中测试模型对话功能
- **流式响应** 支持实时流式对话响应
- **对话历史** 保存和查看对话记录
- **多模型支持** 可切换不同模型进行对话

### ⚙️ 配置管理
- **路径配置** 自定义 Ollama 程序和模型存储路径
- **环境变量** 管理 Ollama 相关环境变量
- **高级设置** 日志级别、自动更新等高级选项
- **配置导入/导出** 备份和恢复配置设置

### 🖥️ 硬件信息
- **GPU 检测** 自动检测和显示 GPU 信息
- **兼容性检查** 检查硬件对 Ollama 的支持情况
- **性能监控** 显示系统资源使用情况

### 📋 日志系统
- **多级别日志** 支持 DEBUG、INFO、WARNING、ERROR 等级别
- **实时查看** 在界面中实时查看日志信息
- **日志过滤** 按级别过滤日志内容
- **日志导出** 导出日志文件用于问题排查

### 🔄 自动更新
- **版本检查** 自动检查 Ollama 新版本
- **更新提醒** 发现新版本时提供下载链接
- **可选更新** 用户可选择是否检查和安装更新

## 系统要求

- **操作系统**: Windows 10/11 (64位)
- **Python**: 3.8 或更高版本
- **内存**: 建议 4GB 以上
- **存储**: 至少 1GB 可用空间（不包括模型文件）
- **网络**: 用于下载模型和检查更新

## 安装说明

### 方法一：使用 uv（推荐）

1. **安装 uv**（如果尚未安装）:
   ```bash
   pip install uv
   ```

2. **克隆项目**:
   ```bash
   git clone https://github.com/your-repo/ollama-manager.git
   cd ollama-manager
   ```

3. **创建虚拟环境并安装依赖**:
   ```bash
   uv venv
   uv pip install -r requirements.txt
   ```

4. **激活虚拟环境**:
   ```bash
   # Windows
   .venv\Scripts\activate
   ```

### 方法二：使用传统 pip

1. **克隆项目**:
   ```bash
   git clone https://github.com/your-repo/ollama-manager.git
   cd ollama-manager
   ```

2. **创建虚拟环境**:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

### 方法三：自动安装脚本

运行项目根目录下的安装脚本:
```bash
python install_dependencies.py
```

## 使用方法

### 启动应用

```bash
python ollama_manager.py
```

或者直接运行:
```bash
python -m src.app
```

### 首次使用

1. **配置 Ollama 路径**: 在"配置"选项卡中设置 Ollama 程序的安装路径
2. **设置模型路径**: 配置模型文件的存储目录
3. **启动服务**: 点击"启动"按钮启动 Ollama 服务
4. **下载模型**: 在"模型管理"选项卡中下载需要的模型
5. **开始使用**: 在"对话测试"选项卡中测试模型功能

### 主要界面说明

#### 服务状态面板
- 显示 Ollama 服务的运行状态
- 提供启动、停止、重启按钮
- 显示当前版本信息
- 检查更新功能

#### 配置选项卡
- **路径配置**: 设置 Ollama 程序和模型存储路径
- **环境变量**: 配置 OLLAMA_HOST、OLLAMA_MODELS 等环境变量
- **高级设置**: 自动启动、日志级别、更新检查等选项

#### 模型管理选项卡
- **已安装模型**: 显示所有已下载的模型
- **模型下载**: 输入模型名称或选择推荐模型进行下载
- **模型操作**: 删除、查看模型信息

#### 对话测试选项卡
- **模型选择**: 选择要使用的模型
- **对话界面**: 发送消息并查看模型响应
- **历史记录**: 查看和清空对话历史

#### 日志选项卡
- **日志查看**: 实时查看应用和服务日志
- **级别过滤**: 按日志级别过滤显示内容
- **日志导出**: 导出日志文件

## 配置文件

应用程序会在用户目录下创建配置文件:
- **Windows**: `%USERPROFILE%\.ollama_manager\config.json`

配置文件包含:
- Ollama 程序路径
- 模型存储路径
- 环境变量设置
- 用户界面偏好
- 高级选项

## 故障排除

### 常见问题

**Q: 无法启动 Ollama 服务**
A: 
1. 检查 Ollama 程序路径是否正确
2. 确认 Ollama 已正确安装
3. 查看日志选项卡中的错误信息
4. 尝试手动运行 Ollama 命令

**Q: 模型下载失败**
A:
1. 检查网络连接
2. 确认模型名称正确
3. 检查磁盘空间是否充足
4. 查看日志中的详细错误信息

**Q: 界面显示异常**
A:
1. 检查 Python 版本是否符合要求
2. 确认所有依赖包已正确安装
3. 尝试重置配置文件
4. 重启应用程序

**Q: GPU 检测失败**
A:
1. 确认已安装 GPU 驱动
2. 检查 WMI 服务是否正常
3. 以管理员权限运行程序

### 日志文件位置

- **应用日志**: `ollama_manager.log`
- **配置目录**: `%USERPROFILE%\.ollama_manager\`

### 重置配置

如果遇到配置相关问题，可以删除配置文件重置:
```bash
# Windows
del "%USERPROFILE%\.ollama_manager\config.json"
```

## 开发说明

### 项目结构

```
ollama-manager/
├── src/                    # 源代码目录
│   ├── __init__.py
│   ├── app.py             # 应用程序主类
│   ├── core/              # 核心功能模块
│   │   ├── __init__.py
│   │   ├── config_manager.py    # 配置管理
│   │   └── ollama_service.py    # Ollama 服务管理
│   ├── ui/                # 用户界面模块
│   │   ├── __init__.py
│   │   └── main_window.py       # 主窗口界面
│   └── utils/             # 工具模块
│       ├── __init__.py
│       ├── logger.py            # 日志系统
│       └── dependency_checker.py # 依赖检查
├── ollama_manager.py      # 程序入口
├── install_dependencies.py # 依赖安装脚本
├── requirements.txt       # 依赖列表
├── README.md             # 项目说明
└── start_manager.bat     # Windows 启动脚本
```

### 代码规范

- 使用 Python 3.8+ 特性
- 遵循 PEP 8 代码风格
- 使用类型提示
- 编写详细的文档字符串
- 适当的错误处理和日志记录

### 扩展开发

1. **添加新功能**: 在相应模块中添加新的类和方法
2. **修改界面**: 编辑 `main_window.py` 文件
3. **配置选项**: 在 `config_manager.py` 中添加新的配置项
4. **服务功能**: 在 `ollama_service.py` 中扩展服务管理功能

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。n
## 贡献

欢迎提交 Issue 和 Pull Request！

### 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 更新日志

### v2.0.0 (当前版本)
- 🎉 全新的模块化架构
- ✨ 改进的用户界面设计
- 🚀 更稳定的服务管理
- 📦 增强的模型管理功能
- 💬 新增对话测试功能
- 🔧 完善的配置管理系统
- 📋 强化的日志系统
- 🖥️ 详细的硬件信息显示
- 🔄 自动更新检查
- 🐛 修复了多个已知问题

### v1.x
- 基础的 Ollama 管理功能
- 简单的图形界面
- 基本的模型下载和管理

## 支持

如果您觉得这个项目有用，请给我们一个 ⭐️！

如有问题或建议，请通过以下方式联系:
- 提交 [GitHub Issue](https://github.com/your-repo/ollama-manager/issues)
- 发送邮件至: your-email@example.com

---

**Ollama Manager** - 让 Ollama 管理变得简单高效！

## 快速开始

### 方式一：图形界面 (推荐)

1. **自动启动**
   ```bash
   # 双击运行，会自动安装依赖
   start_manager.bat
   ```

2. **手动安装依赖**
   ```bash
   python install_dependencies.py
   python ollama_manager.py
   ```

### 方式二：命令行脚本

```bash
# 直接运行 PowerShell 脚本
powershell -ExecutionPolicy Bypass -File ollama_start.ps1
```

## 文件结构

### GUI 管理器文件
- `ollama_manager.py` - 主要的图形界面程序
- `install_dependencies.py` - 依赖安装脚本
- `start_manager.bat` - 快速启动脚本
- `ollama_config.json` - 配置文件 (自动生成)

### PowerShell 脚本文件
- `ollama_start.ps1` - 功能完整的命令行管理脚本
- `ollama_start.bat` - PowerShell 脚本启动器
- `start_ollama.bat` - Ollama 服务启动器 (自动生成)

### 其他文件
- `ollama.exe` - Ollama 程序本体
- `ollama.jsonc` - GitHub API 缓存
- `models/` - 模型存储目录
- `README.md` - 项目说明文档

## 详细功能说明

### 🖼️ GUI 界面详解

#### 状态监控页
- **服务状态**: 实时显示 Ollama 运行状态
- **路径信息**: 显示程序和模型存储路径
- **版本管理**: 显示当前版本和最新版本，支持一键更新
- **硬件信息**: 自动检测显卡并显示 Ollama 支持状态

#### 配置管理页
- **路径配置**: 自定义 Ollama 程序和模型存储路径
- **环境变量**: 配置 HOST、PORT、AMD 显卡支持等
- **高级选项**: 自定义启动参数
- **配置保存**: 支持配置导入导出

#### 模型管理页
- **已安装模型**: 树形视图显示所有已安装模型
- **模型操作**: 删除、查看详情
- **模型下载**: 搜索和下载新模型
- **推荐模型**: 快速下载常用模型
- **下载进度**: 实时显示下载状态

#### 对话测试页
- **模型选择**: 从已安装模型中选择
- **实时对话**: 直接与模型对话测试
- **对话历史**: 完整的对话记录

#### 日志页面
- **应用日志**: 显示应用运行日志
- **实时输出**: Ollama 服务的实时输出
- **日志导出**: 支持导出日志文件

### ⚙️ PowerShell 脚本功能

#### 智能下载系统
- **多线程下载**: 支持 aria2c 16线程下载
- **分块下载**: PowerShell 并行分块下载
- **容错机制**: 多种下载方式自动切换
- **进度显示**: 实时下载进度

#### 硬件检测
- **显卡识别**: 自动识别 NVIDIA/AMD/Intel 显卡
- **驱动建议**: 根据硬件给出配置建议
- **环境配置**: 自动设置 AMD 集显支持

#### 版本管理
- **智能比较**: 使用 .NET Version 类进行准确比较
- **缓存机制**: 本地缓存 GitHub API 响应
- **完整性校验**: 文件大小验证

## 系统要求

### GUI 版本
- **操作系统**: Windows 10/11
- **Python**: 3.7+
- **依赖包**: psutil, requests, pywin32 (自动安装)

### PowerShell 版本
- **操作系统**: Windows 10/11
- **PowerShell**: 5.1+ (系统自带)
- **网络**: 能访问 GitHub 和 Ollama 官网

## 使用技巧

### 🎯 快速配置

1. **首次使用**
   - 运行 `start_manager.bat` 启动图形界面
   - 点击"检查更新"自动下载 Ollama
   - 设置模型存储路径
   - 配置显卡支持 (AMD 用户)

2. **模型管理**
   - 使用"推荐模型"快速下载常用模型
   - 支持自定义模型名称下载
   - 可删除不需要的模型释放空间

3. **远程访问**
   - 设置 OLLAMA_HOST 为 `0.0.0.0`
   - 配置防火墙允许 11434 端口
   - 其他设备可通过 IP 访问

### 🔧 高级配置

1. **AMD 集成显卡支持**
   ```bash
   # 自动检测并设置
   HSA_OVERRIDE_GFX_VERSION=11.0.0
   ```

2. **自定义模型路径**
   ```bash
   # 在配置页面设置
   OLLAMA_MODELS=D:\MyModels
   ```

3. **性能优化**
   - 将模型存储在 SSD 上
   - 确保有足够的 RAM 和 VRAM
   - 关闭不必要的后台程序

## 故障排除

### 常见问题

1. **Python 依赖问题**
   ```bash
   # 手动安装依赖
   pip install psutil requests pywin32
   ```

2. **Ollama 启动失败**
   - 检查端口 11434 是否被占用
   - 确认防火墙设置
   - 查看日志页面的错误信息

3. **模型下载慢**
   - 使用 PowerShell 脚本的多线程下载
   - 检查网络连接
   - 尝试更换网络环境

4. **AMD 显卡不识别**
   - 手动设置 `HSA_OVERRIDE_GFX_VERSION=11.0.0`
   - 更新显卡驱动
   - 检查 ROCm 支持

### 🐛 问题反馈

如果遇到问题，请提供以下信息：
- 操作系统版本
- Python 版本 (GUI 版本)
- 错误日志信息
- 硬件配置 (显卡型号)

## 更新日志

### v1.0.0 (当前版本)
- ✅ 完整的 GUI 管理界面
- ✅ 多线程下载支持
- ✅ 智能硬件检测
- ✅ 配置管理系统
- ✅ 模型管理功能
- ✅ 内置对话测试
- ✅ 完善的日志系统

## 贡献

欢迎提交问题和建议！如果您有任何改进想法，请随时提交 Pull Request。

## 许可证

本项目基于 MIT 许可证开源。

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

### 下载最新的 jsonc

```powershell
Invoke-RestMethod -Uri "https://api.github.com/repos/ollama/ollama/releases/latest" | ConvertTo-Json -Depth 10 > .\ollama.jsonc
```

```bash
curl -s https://api.github.com/repos/ollama/ollama/releases/latest > .\ollama.jsonc
```

## 贡献

欢迎提交问题和请求。如果您有任何建议或改进，请随时提交 Pull Request。

## 许可证

该项目使用 MIT 许可证。有关详细信息，请参阅 LICENSE 文件。
