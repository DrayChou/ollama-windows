# Ollama Manager 项目结构说明

## 快速启动

### 方式一：使用快速启动脚本（推荐）
```bash
# 双击运行或在命令行执行
start.bat
```

### 方式二：使用完整启动脚本
```bash
# 完整的启动脚本，包含环境检查
scripts\start_manager.bat
```

### 方式三：直接运行Python
```bash
# 使用uv环境（推荐）
uv run python ollama_manager.py

# 或使用系统Python
python ollama_manager.py
```

## 项目结构

```
ollama-windows/
├── start.bat                    # 快速启动脚本
├── ollama_manager.py            # 主程序入口
├── pyproject.toml              # 项目配置文件
├── requirements.txt            # 依赖列表
├── uv.lock                     # uv锁定文件
│
├── src/                        # 源代码目录
│   ├── app.py                  # 应用程序主模块
│   ├── core/                   # 核心功能模块
│   │   ├── config_manager.py   # 配置管理
│   │   └── ollama_service.py   # Ollama服务管理
│   ├── ui/                     # 用户界面模块
│   │   └── main_window.py      # 主窗口界面
│   └── utils/                  # 工具模块
│       ├── dependency_checker.py # 依赖检查
│       └── logger.py           # 日志系统
│
├── scripts/                    # 脚本目录
│   ├── start_manager.bat       # 完整启动脚本
│   ├── start_ollama.bat        # Ollama启动脚本
│   ├── build_test.bat          # 构建测试脚本
│   ├── install_dependencies.py # 依赖安装脚本
│   └── organize_project.bat    # 项目整理脚本
│
├── assets/                     # 资源文件
│   ├── icon.ico               # 应用图标
│   └── icon.svg               # 矢量图标
│
├── archive/                    # 归档文件
│   ├── ollama_manager_fixed.py
│   ├── ollama_manager_old.py
│   └── ollama_manager_simple.py
│
└── .github/                    # GitHub配置
    └── workflows/
        └── build-release.yml   # 自动构建配置
```

## 功能特性

- ✅ 实时状态监控
- ✅ 一键启动/停止/重启服务
- ✅ 智能路径自动检测
- ✅ 模型管理
- ✅ 内置对话测试
- ✅ 完整的日志系统
- ✅ 现代化图形界面
- ✅ 配置管理

## 性能优化

最新版本包含以下性能优化：

1. **减少UI更新频率**
   - 自动刷新间隔从5秒增加到10秒
   - 时间显示更新从1秒增加到5秒
   - 日志刷新频率降低到30秒一次

2. **智能缓存机制**
   - 状态变化检测，避免重复更新
   - 模型列表缓存（60秒）
   - 日志内容变化检测

3. **防抖机制**
   - 窗口配置保存防抖（1秒延迟）
   - UI更新使用100ms延迟避免阻塞

4. **异常处理**
   - 完善的错误处理机制
   - 窗口状态检查
   - 资源清理

## 故障排除

### 界面卡死问题
如果遇到界面卡死，可能的原因和解决方案：

1. **关闭自动刷新**：在设置中关闭自动刷新功能
2. **增加刷新间隔**：将刷新间隔设置为更大的值
3. **检查系统资源**：确保系统有足够的内存和CPU资源
4. **重启应用**：关闭并重新启动Ollama Manager

### 依赖问题
如果遇到依赖缺失：
```bash
# 安装依赖
scripts\install_dependencies.py

# 或使用uv
uv sync
```

## 开发说明

本项目使用现代Python开发实践：
- 使用 `uv` 进行包管理
- 模块化架构设计
- 完整的日志系统
- 配置文件管理
- 异常处理机制