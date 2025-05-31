#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用程序主类

负责初始化和协调各个组件：
- 配置管理器
- 日志系统
- Ollama 服务
- 主窗口界面
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os
import threading
from typing import Optional

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入自定义模块
from core.config_manager import ConfigManager
from core.ollama_service import OllamaService
from utils.logger import Logger
from utils import dependency_checker
from ui.main_window import MainWindow


class OllamaManagerApp:
    """
    Ollama Manager 应用程序主类
    
    负责整个应用的生命周期管理
    """
    
    def __init__(self):
        """初始化应用程序"""
        self.root: Optional[tk.Tk] = None
        self.config_manager: Optional[ConfigManager] = None
        self.logger: Optional[Logger] = None
        self.ollama_service: Optional[OllamaService] = None
        self.main_window: Optional[MainWindow] = None
        
        # 应用信息
        self.app_name = "Ollama Manager"
        self.app_version = "2.0.0"
        self.app_author = "Ollama Manager Team"
    
    def initialize(self) -> bool:
        """
        初始化应用程序组件
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 1. 检查依赖
            if not self._check_dependencies():
                return False
            
            # 2. 初始化配置管理器
            if not self._initialize_config_manager():
                return False
            
            # 3. 初始化日志系统
            if not self._initialize_logger():
                return False
            
            # 4. 初始化 Ollama 服务
            if not self._initialize_ollama_service():
                return False
            
            # 5. 初始化 GUI
            if not self._initialize_gui():
                return False
            
            self.logger.info(f"{self.app_name} v{self.app_version} 初始化完成")
            return True
            
        except Exception as e:
            error_msg = f"应用程序初始化失败: {e}"
            print(error_msg)
            if self.logger:
                self.logger.error(error_msg)
            messagebox.showerror("初始化错误", error_msg)
            return False
    
    def _check_dependencies(self) -> bool:
        """
        检查依赖包
        
        Returns:
            bool: 依赖检查是否通过
        """
        try:
            # 检查必需依赖
            missing_required = dependency_checker.check_dependencies()
            if missing_required:
                error_msg = f"缺少必需的依赖包: {', '.join(missing_required)}"
                print(error_msg)
                
                # 尝试自动安装
                if messagebox.askyesno(
                    "依赖检查", 
                    f"{error_msg}\n\n是否尝试自动安装？"
                ):
                    success = dependency_checker.install_packages(missing_required)
                    if not success:
                        messagebox.showerror("安装失败", "依赖包安装失败，请手动安装")
                        return False
                else:
                    return False
            
            # 检查可选依赖
            missing_optional = dependency_checker.check_optional_dependencies()
            if missing_optional:
                missing_list = [pkg for pkg, available in missing_optional.items() if not available]
                if missing_list:
                    print(f"缺少可选依赖包: {', '.join(missing_list)}")
                    print("这些包不是必需的，但可能影响某些功能")
            
            return True
            
        except Exception as e:
            print(f"依赖检查失败: {e}")
            return False
    
    def _initialize_config_manager(self) -> bool:
        """
        初始化配置管理器
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.config_manager = ConfigManager()
            
            # 加载配置
            if not self.config_manager.load_config():
                print("警告: 配置文件加载失败，使用默认配置")
            
            return True
            
        except Exception as e:
            print(f"配置管理器初始化失败: {e}")
            return False
    
    def _initialize_logger(self) -> bool:
        """
        初始化日志系统
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 获取日志配置
            log_level = self.config_manager.get_advanced_setting('log_level', 'INFO')
            log_file = self.config_manager.get_advanced_setting('log_file', 'ollama_manager.log')
            max_log_size = self.config_manager.get_advanced_setting('max_log_size', 10 * 1024 * 1024)  # 10MB
            backup_count = self.config_manager.get_advanced_setting('backup_count', 5)
            
            self.logger = Logger(
                name=self.app_name,
                log_dir="logs"
            )
            
            return True
            
        except Exception as e:
            print(f"日志系统初始化失败: {e}")
            return False
    
    def _initialize_ollama_service(self) -> bool:
        """
        初始化 Ollama 服务
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            self.ollama_service = OllamaService(
                config_manager=self.config_manager,
                logger=self.logger
            )
            
            # 检查 Ollama 状态
            self.ollama_service.check_status()
            
            # 如果配置了自动启动且服务未运行，则启动服务
            if (self.config_manager.get_advanced_setting('auto_start', False) and 
                not self.ollama_service.is_running):
                
                self.logger.info("自动启动 Ollama 服务")
                
                def auto_start():
                    success = self.ollama_service.start()
                    if success:
                        self.logger.info("Ollama 服务自动启动成功")
                    else:
                        self.logger.warning("Ollama 服务自动启动失败")
                
                # 在后台线程中启动服务
                threading.Thread(target=auto_start, daemon=True).start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ollama 服务初始化失败: {e}")
            return False
    
    def _initialize_gui(self) -> bool:
        """
        初始化图形界面
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 创建主窗口
            self.root = tk.Tk()
            
            # 设置主题（如果支持）
            try:
                import tkinter.ttk as ttk
                style = ttk.Style()
                
                # 尝试设置现代主题
                available_themes = style.theme_names()
                preferred_themes = ['vista', 'xpnative', 'winnative', 'clam']
                
                for theme in preferred_themes:
                    if theme in available_themes:
                        style.theme_use(theme)
                        break
                        
            except Exception as e:
                self.logger.warning(f"主题设置失败: {e}")
            
            # 创建主窗口
            self.main_window = MainWindow(
                root=self.root,
                ollama_service=self.ollama_service,
                config_manager=self.config_manager,
                logger=self.logger
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"GUI 初始化失败: {e}")
            return False
    
    def run(self) -> None:
        """
        运行应用程序主循环
        """
        if not self.root:
            raise RuntimeError("应用程序未正确初始化")
        
        try:
            self.logger.info("启动应用程序主循环")
            
            # 检查更新（如果启用）
            if self.config_manager.get_advanced_setting('check_updates', True):
                self._check_updates_on_startup()
            
            # 启动主循环
            self.root.mainloop()
            
        except KeyboardInterrupt:
            self.logger.info("收到键盘中断信号")
        except Exception as e:
            self.logger.error(f"应用程序运行时错误: {e}")
            messagebox.showerror("运行时错误", f"应用程序发生错误: {e}")
        finally:
            self.cleanup()
    
    def _check_updates_on_startup(self) -> None:
        """
        启动时检查更新
        """
        def check_updates():
            try:
                # 延迟几秒后检查，避免影响启动速度
                import time
                time.sleep(3)
                
                update_info = self.ollama_service.check_for_updates()
                if update_info and update_info.get('has_update'):
                    def show_update_notification():
                        result = messagebox.askyesno(
                            "发现更新",
                            f"发现新版本 {update_info['latest_version']}\n"
                            f"当前版本 {update_info['current_version']}\n\n"
                            "是否打开下载页面？"
                        )
                        if result:
                            import webbrowser
                            webbrowser.open(update_info['download_url'])
                    
                    # 在主线程中显示通知
                    self.root.after(0, show_update_notification)
                    
            except Exception as e:
                self.logger.warning(f"启动时检查更新失败: {e}")
        
        # 在后台线程中检查更新
        threading.Thread(target=check_updates, daemon=True).start()
    
    def cleanup(self) -> None:
        """
        清理资源
        """
        try:
            self.logger.info("开始清理应用程序资源")
            
            # 保存配置
            if self.config_manager:
                self.config_manager.save_config()
                self.logger.info("配置已保存")
            
            # 停止服务（如果需要）
            if (self.ollama_service and 
                self.ollama_service.is_running and 
                self.config_manager and
                self.config_manager.get_advanced_setting('stop_on_exit', False)):
                
                self.logger.info("正在停止 Ollama 服务")
                self.ollama_service.stop()
            
            # 关闭日志
            if self.logger:
                self.logger.info("应用程序退出")
                self.logger.close()
            
        except Exception as e:
            print(f"清理资源时发生错误: {e}")
    
    def get_app_info(self) -> dict:
        """
        获取应用程序信息
        
        Returns:
            dict: 应用程序信息
        """
        return {
            'name': self.app_name,
            'version': self.app_version,
            'author': self.app_author,
            'python_version': sys.version,
            'platform': sys.platform,
            'executable': sys.executable
        }
    
    @staticmethod
    def create_and_run() -> None:
        """
        创建并运行应用程序的便捷方法
        """
        app = OllamaManagerApp()
        
        if app.initialize():
            app.run()
        else:
            print("应用程序初始化失败")
            sys.exit(1)


def main():
    """
    主函数入口
    """
    try:
        # 设置工作目录为脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(os.path.dirname(script_dir))
        
        # 创建并运行应用程序
        OllamaManagerApp.create_and_run()
        
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()