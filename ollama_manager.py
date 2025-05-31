#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama Manager - 完整的 Ollama 管理工具

这是一个现代化的 Ollama 管理工具，提供图形界面和完整的功能支持：
- 实时状态监控
- 一键安装/更新
- 启动/停止/重启服务
- 智能硬件检测
- 环境变量配置管理
- 模型管理
- 内置对话测试
- 完整的日志系统

作者: AI Assistant
版本: 2.0.0
"""

import sys
import os
from pathlib import Path

# 添加当前目录到 Python 路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    import threading
    import json
    from datetime import datetime
except ImportError as e:
    print(f"导入基础模块失败: {e}")
    print("请确保 Python 环境正确安装")
    sys.exit(1)

# 导入自定义模块
try:
    from src.ui.main_window import MainWindow
    from src.core.config_manager import ConfigManager
    from src.core.ollama_service import OllamaService
    from src.utils.logger import Logger
    from src.utils.dependency_checker import check_dependencies
except ImportError as e:
    print(f"导入自定义模块失败: {e}")
    print("正在尝试安装依赖...")
    
    # 尝试安装依赖
    try:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "psutil", "requests", "pywin32"], 
                      check=True, capture_output=True)
        print("依赖安装完成，请重新运行程序")
    except Exception as install_error:
        print(f"自动安装依赖失败: {install_error}")
        print("请手动运行: pip install psutil requests pywin32")
    
    sys.exit(1)


class OllamaManager:
    """
    Ollama Manager 主应用类
    
    负责协调各个组件，管理应用生命周期
    """
    
    def __init__(self):
        """初始化 Ollama Manager"""
        self.logger = Logger()
        self.config_manager = ConfigManager()
        self.ollama_service = OllamaService(self.config_manager, self.logger)
        
        # 检查依赖
        missing_deps = check_dependencies()
        if missing_deps:
            self._handle_missing_dependencies(missing_deps)
            return
        
        # 初始化 UI
        self.root = tk.Tk()
        self.main_window = MainWindow(
            self.root, 
            self.ollama_service, 
            self.config_manager, 
            self.logger
        )
        
        self.logger.info("Ollama Manager 初始化完成")
    
    def _handle_missing_dependencies(self, missing_deps):
        """处理缺失的依赖"""
        print(f"缺少必要的依赖模块: {', '.join(missing_deps)}")
        print("请运行以下命令安装依赖:")
        print(f"pip install {' '.join(missing_deps)}")
        
        # 尝试自动安装
        try:
            import subprocess
            result = messagebox.askyesno(
                "缺少依赖", 
                f"检测到缺少以下依赖模块:\n{', '.join(missing_deps)}\n\n是否自动安装？"
            )
            
            if result:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install"] + missing_deps,
                    check=True
                )
                messagebox.showinfo("成功", "依赖安装完成，请重新启动程序")
            
        except Exception as e:
            messagebox.showerror("安装失败", f"自动安装失败: {e}\n请手动安装依赖")
        
        sys.exit(1)
    
    def run(self):
        """运行应用"""
        if not hasattr(self, 'root'):
            return
        
        try:
            # 设置窗口关闭事件
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            # 启动应用
            self.logger.info("启动 Ollama Manager")
            self.root.mainloop()
            
        except Exception as e:
            self.logger.error(f"应用运行出错: {e}")
            messagebox.showerror("错误", f"应用运行出错: {e}")
    
    def _on_closing(self):
        """应用关闭时的清理工作"""
        try:
            # 保存配置
            self.config_manager.save_config()
            
            # 停止服务（如果需要）
            # self.ollama_service.stop()
            
            self.logger.info("Ollama Manager 正常退出")
            
        except Exception as e:
            self.logger.error(f"退出时出错: {e}")
        
        finally:
            self.root.destroy()


def main():
    """主函数"""
    try:
        # 创建应用实例
        app = OllamaManager()
        
        # 运行应用
        app.run()
        
    except KeyboardInterrupt:
        print("\n用户中断程序")
    except Exception as e:
        print(f"程序运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()