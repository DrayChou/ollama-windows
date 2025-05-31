# -*- coding: utf-8 -*-
"""
配置选项卡模块

提供分页显示不同类型配置的功能：
- 系统配置：从系统环境变量读取的配置
- 当前配置：程序当前使用的配置
- 文件配置：保存在配置文件中的配置
- 环境变量编辑：可编辑的环境变量管理
- 配置同步：在不同配置源之间同步
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Dict, Any

# 导入配置同步工具
try:
    from ..utils.config_sync import ConfigSyncManager
except ImportError:
    # 如果导入失败，创建一个占位符类
    class ConfigSyncManager:
        def __init__(self, *args, **kwargs):
            pass
        
        def sync_ui_to_ps(self, *args, **kwargs):
            return False
        
        def sync_ps_to_ui(self, *args, **kwargs):
            return {}
        
        def detect_config_differences(self, *args, **kwargs):
            return {}
        
        def generate_sync_report(self, *args, **kwargs):
            return "配置同步功能不可用"
        
        def read_ps_script_config(self, *args, **kwargs):
            return {}


class ConfigTabs:
    """
    配置选项卡管理器
    
    提供分页显示不同来源的配置信息
    """
    
    def __init__(self, parent, config_manager, logger):
        """初始化配置选项卡"""
        self.parent = parent
        self.config_manager = config_manager
        self.logger = logger
        
        # 直接使用传入的notebook作为容器
        self.notebook = parent
        
        # 存储环境变量编辑控件
        self.env_var_entries = {}
        
        # 初始化配置同步管理器
        try:
            self.sync_manager = ConfigSyncManager(config_manager, logger)
        except Exception as e:
            self.logger.warning(f"配置同步管理器初始化失败: {e}")
            self.sync_manager = None
        
        # 创建各个选项卡
        self.create_system_config_tab()
        self.create_current_config_tab()
        self.create_env_editor_tab()
        self.create_sync_tab()
        self.create_file_config_tab()
    
    def create_sync_tab(self):
        """创建配置同步选项卡"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="配置同步")
        
        # 创建滚动区域
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 添加说明
        ttk.Label(scrollable_frame, text="配置同步管理", 
                 font=('Arial', 12, 'bold')).pack(pady=(10, 5))
        ttk.Label(scrollable_frame, text="在管理界面、PowerShell 脚本和系统环境变量之间同步配置", 
                 foreground="gray").pack(pady=(0, 10))
        
        # 同步操作区域
        sync_frame = ttk.LabelFrame(scrollable_frame, text="同步操作")
        sync_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # 同步按钮行1
        button_row1 = ttk.Frame(sync_frame)
        button_row1.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_row1, text="管理界面 → PowerShell", 
                  command=self.sync_ui_to_ps).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_row1, text="PowerShell → 管理界面", 
                  command=self.sync_ps_to_ui).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_row1, text="检测配置差异", 
                  command=self.detect_differences).pack(side=tk.LEFT, padx=(0, 5))
        
        # 同步按钮行2
        button_row2 = ttk.Frame(sync_frame)
        button_row2.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Button(button_row2, text="生成同步报告", 
                  command=self.generate_report).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_row2, text="刷新状态", 
                  command=self.refresh_sync_status).pack(side=tk.LEFT, padx=(0, 5))
        
        # 状态显示区域
        status_frame = ttk.LabelFrame(scrollable_frame, text="同步状态")
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # 创建文本显示区域
        self.sync_status_text = scrolledtext.ScrolledText(
            status_frame, 
            height=15, 
            wrap=tk.WORD,
            font=('Consolas', 9)
        )
        self.sync_status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 初始加载状态
        self.refresh_sync_status()
    
    def sync_ui_to_ps(self):
        """将管理界面配置同步到 PowerShell 脚本"""
        if not self.sync_manager:
            messagebox.showerror("错误", "配置同步功能不可用")
            return
        
        try:
            if messagebox.askyesno("确认同步", 
                                 "确定要将管理界面的配置同步到 PowerShell 脚本吗？\n\n" +
                                 "这将覆盖 PowerShell 脚本中的环境变量设置。"):
                
                success = self.sync_manager.sync_ui_to_ps()
                
                if success:
                    messagebox.showinfo("同步成功", "已将管理界面配置同步到 PowerShell 脚本")
                    self.refresh_sync_status()
                else:
                    messagebox.showerror("同步失败", "同步过程中发生错误，请查看日志")
                    
        except Exception as e:
            self.logger.error(f"同步配置失败: {e}")
            messagebox.showerror("错误", f"同步失败: {e}")
    
    def sync_ps_to_ui(self):
        """将 PowerShell 脚本配置同步到管理界面"""
        if not self.sync_manager:
            messagebox.showerror("错误", "配置同步功能不可用")
            return
        
        try:
            if messagebox.askyesno("确认同步", 
                                 "确定要将 PowerShell 脚本的配置同步到管理界面吗？\n\n" +
                                 "这将覆盖管理界面中的环境变量设置。"):
                
                success = self.sync_manager.sync_ps_to_ui()
                
                if success:
                    messagebox.showinfo("同步成功", "已将 PowerShell 脚本配置同步到管理界面")
                    # 刷新环境变量编辑器
                    self.refresh_env_editors()
                    self.refresh_sync_status()
                else:
                    messagebox.showerror("同步失败", "同步过程中发生错误，请查看日志")
                    
        except Exception as e:
            self.logger.error(f"同步配置失败: {e}")
            messagebox.showerror("错误", f"同步失败: {e}")
    
    def detect_differences(self):
        """检测配置差异"""
        if not self.sync_manager:
            messagebox.showerror("错误", "配置同步功能不可用")
            return
        
        try:
            differences = self.sync_manager.detect_config_differences()
            
            # 显示差异信息
            diff_text = "=== 配置差异检测结果 ===\n\n"
            
            if differences.get("conflicts"):
                diff_text += "存在冲突的配置：\n"
                for var, vals in differences["conflicts"].items():
                    diff_text += f"  {var}:\n"
                    diff_text += f"    管理界面: {vals['ui']}\n"
                    diff_text += f"    PowerShell: {vals['ps']}\n"
                    diff_text += f"    系统环境: {vals['system']}\n"
                diff_text += "\n"
            
            if differences.get("ui_only"):
                diff_text += "仅在管理界面中存在：\n"
                for var, val in differences["ui_only"].items():
                    diff_text += f"  {var} = {val}\n"
                diff_text += "\n"
            
            if differences.get("ps_only"):
                diff_text += "仅在 PowerShell 脚本中存在：\n"
                for var, val in differences["ps_only"].items():
                    diff_text += f"  {var} = {val}\n"
                diff_text += "\n"
            
            if not any(differences.values()):
                diff_text += "所有配置源的配置都是一致的。\n"
            
            # 更新状态显示
            self.sync_status_text.delete(1.0, tk.END)
            self.sync_status_text.insert(1.0, diff_text)
            
        except Exception as e:
            self.logger.error(f"检测配置差异失败: {e}")
            messagebox.showerror("错误", f"检测差异失败: {e}")
    
    def generate_report(self):
        """生成同步报告"""
        if not self.sync_manager:
            messagebox.showerror("错误", "配置同步功能不可用")
            return
        
        try:
            report = self.sync_manager.generate_sync_report()
            
            # 更新状态显示
            self.sync_status_text.delete(1.0, tk.END)
            self.sync_status_text.insert(1.0, report)
            
        except Exception as e:
            self.logger.error(f"生成同步报告失败: {e}")
            messagebox.showerror("错误", f"生成报告失败: {e}")
    
    def refresh_sync_status(self):
        """刷新同步状态"""
        try:
            status_text = "=== 配置同步状态 ===\n\n"
            
            # 检查各个配置源的状态
            status_text += "配置源状态：\n"
            
            # 管理界面配置
            ui_env_count = len(self.config_manager.config.get("environment_variables", {}))
            status_text += f"  管理界面配置: {ui_env_count} 个环境变量\n"
            
            # PowerShell 脚本配置
            if self.sync_manager:
                try:
                    ps_config = self.sync_manager.read_ps_script_config()
                    ps_env_count = len(ps_config)
                    status_text += f"  PowerShell 脚本: {ps_env_count} 个环境变量\n"
                except Exception as e:
                    status_text += f"  PowerShell 脚本: 读取失败 ({e})\n"
            else:
                status_text += "  PowerShell 脚本: 同步功能不可用\n"
            
            # 系统环境变量
            system_env_count = sum(1 for var in ["OLLAMA_HOST", "OLLAMA_MODELS", "OLLAMA_KEEP_ALIVE", 
                                                "OLLAMA_NUM_PARALLEL", "OLLAMA_MAX_LOADED_MODELS", 
                                                "OLLAMA_FLASH_ATTENTION", "OLLAMA_DEBUG", "OLLAMA_ORIGINS",
                                                "HSA_OVERRIDE_GFX_VERSION"] 
                                 if os.environ.get(var))
            status_text += f"  系统环境变量: {system_env_count} 个环境变量\n\n"
            
            # 添加使用说明
            status_text += "使用说明：\n"
            status_text += "1. 使用'检测配置差异'查看不同配置源之间的差异\n"
            status_text += "2. 使用同步按钮在配置源之间同步设置\n"
            status_text += "3. 修改配置后建议重启 Ollama 服务以确保生效\n"
            status_text += "4. PowerShell 脚本的修改会自动备份原文件\n"
            
            # 更新显示
            self.sync_status_text.delete(1.0, tk.END)
            self.sync_status_text.insert(1.0, status_text)
            
        except Exception as e:
            self.logger.error(f"刷新同步状态失败: {e}")
    
    def refresh_env_editors(self):
        """刷新环境变量编辑器的值"""
        try:
            env_config = self.config_manager.config.get("environment_variables", {})
            
            for var_name, entry in self.env_var_entries.items():
                current_value = env_config.get(var_name, "")
                entry.set(current_value)
                
        except Exception as e:
            self.logger.error(f"刷新环境变量编辑器失败: {e}")

    def create_system_config_tab(self):
        """创建系统配置选项卡"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="系统环境变量")
        
        # 创建滚动区域
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 添加说明
        ttk.Label(scrollable_frame, text="系统环境变量（只读）", 
                 font=('Arial', 12, 'bold')).pack(pady=(10, 5))
        ttk.Label(scrollable_frame, text="这些是从系统环境变量中读取的 Ollama 相关配置", 
                 foreground="gray").pack(pady=(0, 10))
        
        # 显示系统环境变量
        ollama_env_vars = [
            "OLLAMA_HOST", "OLLAMA_MODELS", "OLLAMA_KEEP_ALIVE", 
            "OLLAMA_NUM_PARALLEL", "OLLAMA_MAX_LOADED_MODELS", 
            "OLLAMA_FLASH_ATTENTION", "OLLAMA_DEBUG", "OLLAMA_ORIGINS",
            "HSA_OVERRIDE_GFX_VERSION"  # 添加 AMD 显卡相关配置
        ]
        
        for var_name in ollama_env_vars:
            var_frame = ttk.Frame(scrollable_frame)
            var_frame.pack(fill=tk.X, padx=10, pady=2)
            
            ttk.Label(var_frame, text=f"{var_name}:", width=25, anchor="w").pack(side=tk.LEFT)
            
            value = os.environ.get(var_name, "(未设置)")
            value_label = ttk.Label(var_frame, text=value, foreground="blue" if value != "(未设置)" else "gray")
            value_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_env_editor_tab(self):
        """创建环境变量编辑选项卡"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="环境变量编辑")
        
        # 创建滚动区域
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 添加说明
        ttk.Label(scrollable_frame, text="环境变量编辑器", 
                 font=('Arial', 12, 'bold')).pack(pady=(10, 5))
        ttk.Label(scrollable_frame, text="编辑 Ollama 环境变量配置，修改后需要重启 Ollama 服务生效", 
                 foreground="gray").pack(pady=(0, 10))
        
        # 操作按钮区域
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="保存配置", 
                  command=self.save_env_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="重置为默认值", 
                  command=self.reset_env_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="从系统加载", 
                  command=self.load_from_system).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="应用到系统", 
                  command=self.apply_to_system).pack(side=tk.LEFT)
        
        # 环境变量编辑区域
        self.env_edit_frame = ttk.Frame(scrollable_frame)
        self.env_edit_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # 创建环境变量编辑控件
        self.create_env_editors()
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_env_editors(self):
        """创建环境变量编辑控件"""
        # 定义环境变量及其说明
        env_vars_config = {
            "OLLAMA_HOST": {
                "default": "127.0.0.1:11434",
                "description": "Ollama 服务监听地址和端口",
                "examples": ["127.0.0.1:11434", "0.0.0.0:11434", "localhost:11434"]
            },
            "OLLAMA_MODELS": {
                "default": "",
                "description": "模型存储目录路径",
                "examples": ["./models", "D:\\ollama\\models", "C:\\Users\\用户名\\.ollama\\models"]
            },
            "OLLAMA_KEEP_ALIVE": {
                "default": "5m",
                "description": "模型在内存中保持活跃的时间",
                "examples": ["5m", "10m", "1h", "0"]
            },
            "OLLAMA_NUM_PARALLEL": {
                "default": "1",
                "description": "并行处理请求的数量",
                "examples": ["1", "2", "4"]
            },
            "OLLAMA_MAX_LOADED_MODELS": {
                "default": "1",
                "description": "同时加载到内存的最大模型数量",
                "examples": ["1", "2", "3"]
            },
            "OLLAMA_FLASH_ATTENTION": {
                "default": "1",
                "description": "启用 Flash Attention 优化（1=启用，0=禁用）",
                "examples": ["1", "0"]
            },
            "OLLAMA_DEBUG": {
                "default": "",
                "description": "启用调试模式（1=启用，空=禁用）",
                "examples": ["", "1"]
            },
            "OLLAMA_ORIGINS": {
                "default": "",
                "description": "允许的跨域请求来源",
                "examples": ["", "*", "http://localhost:3000"]
            },
            "HSA_OVERRIDE_GFX_VERSION": {
                "default": "",
                "description": "AMD 显卡 HSA 版本覆盖（仅 AMD 集显需要）",
                "examples": ["", "11.0.0", "10.3.0"]
            }
        }
        
        for var_name, config in env_vars_config.items():
            # 创建变量组
            var_group = ttk.LabelFrame(self.env_edit_frame, text=var_name)
            var_group.pack(fill=tk.X, pady=(0, 10))
            
            # 说明文字
            ttk.Label(var_group, text=config["description"], 
                     foreground="gray", font=('Arial', 9)).pack(anchor="w", padx=5, pady=(5, 0))
            
            # 输入框和下拉菜单
            input_frame = ttk.Frame(var_group)
            input_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # 创建组合框（可编辑的下拉菜单）
            combo = ttk.Combobox(input_frame, values=config["examples"])
            combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # 设置当前值
            current_value = self.config_manager.config.get("environment_variables", {}).get(var_name, config["default"])
            combo.set(current_value)
            
            # 存储引用
            self.env_var_entries[var_name] = combo
            
            # 重置按钮
            ttk.Button(input_frame, text="重置", width=8,
                      command=lambda v=var_name, d=config["default"]: self.reset_single_var(v, d)).pack(side=tk.RIGHT, padx=(5, 0))
    
    def save_env_config(self):
        """保存环境变量配置"""
        try:
            # 更新配置
            if "environment_variables" not in self.config_manager.config:
                self.config_manager.config["environment_variables"] = {}
            
            for var_name, entry in self.env_var_entries.items():
                value = entry.get().strip()
                self.config_manager.config["environment_variables"][var_name] = value
            
            # 保存到文件
            if self.config_manager.save_config():
                messagebox.showinfo("成功", "环境变量配置已保存到配置文件")
                self.logger.info("环境变量配置已保存")
            else:
                messagebox.showerror("错误", "保存配置文件失败")
                
        except Exception as e:
            self.logger.error(f"保存环境变量配置失败: {e}")
            messagebox.showerror("错误", f"保存配置失败: {e}")
    
    def reset_env_config(self):
        """重置环境变量为默认值"""
        if messagebox.askyesno("确认", "确定要重置所有环境变量为默认值吗？"):
            default_config = self.config_manager._load_default_config()
            default_env = default_config.get("environment_variables", {})
            
            for var_name, entry in self.env_var_entries.items():
                default_value = default_env.get(var_name, "")
                entry.set(default_value)
    
    def reset_single_var(self, var_name, default_value):
        """重置单个环境变量"""
        if var_name in self.env_var_entries:
            self.env_var_entries[var_name].set(default_value)
    
    def load_from_system(self):
        """从系统环境变量加载"""
        if messagebox.askyesno("确认", "确定要从系统环境变量加载配置吗？这将覆盖当前的编辑内容。"):
            for var_name, entry in self.env_var_entries.items():
                system_value = os.environ.get(var_name, "")
                entry.set(system_value)
    
    def apply_to_system(self):
        """应用配置到系统环境变量（当前进程）"""
        try:
            applied_vars = []
            for var_name, entry in self.env_var_entries.items():
                value = entry.get().strip()
                if value:
                    os.environ[var_name] = value
                    applied_vars.append(f"{var_name}={value}")
                elif var_name in os.environ:
                    del os.environ[var_name]
                    applied_vars.append(f"{var_name}=(已删除)")
            
            if applied_vars:
                message = "已应用到当前进程环境变量：\n" + "\n".join(applied_vars)
                message += "\n\n注意：这只影响当前程序进程，重启后需要重新应用。"
                messagebox.showinfo("成功", message)
                self.logger.info("环境变量已应用到当前进程")
            else:
                messagebox.showinfo("提示", "没有需要应用的环境变量")
                
        except Exception as e:
            self.logger.error(f"应用环境变量失败: {e}")
            messagebox.showerror("错误", f"应用环境变量失败: {e}")

    def create_current_config_tab(self):
        """创建当前配置选项卡"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="当前程序配置")
        
        # 创建滚动区域
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 添加说明
        ttk.Label(scrollable_frame, text="当前程序使用的配置", 
                 font=('Arial', 12, 'bold')).pack(pady=(10, 5))
        ttk.Label(scrollable_frame, text="这些是程序当前实际使用的配置值（可能来自文件或环境变量）", 
                 foreground="gray").pack(pady=(0, 10))
        
        # 刷新按钮
        ttk.Button(scrollable_frame, text="刷新配置信息", 
                  command=self.refresh_current_config).pack(pady=(0, 10))
        
        # 配置显示区域
        self.current_config_frame = ttk.Frame(scrollable_frame)
        self.current_config_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 初始加载
        self.refresh_current_config()
    
    def create_file_config_tab(self):
        """创建文件配置选项卡"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="配置文件内容")
        
        # 添加说明
        ttk.Label(frame, text="配置文件内容（ollama_config.json）", 
                 font=('Arial', 12, 'bold')).pack(pady=(10, 5))
        ttk.Label(frame, text="这些是保存在配置文件中的设置", 
                 foreground="gray").pack(pady=(0, 10))
        
        # 刷新按钮
        ttk.Button(frame, text="刷新文件内容", 
                  command=self.refresh_file_config).pack(pady=(0, 10))
        
        # 文本显示区域
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.file_config_text = tk.Text(text_frame, wrap=tk.WORD, height=20)
        file_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.file_config_text.yview)
        self.file_config_text.configure(yscrollcommand=file_scrollbar.set)
        
        self.file_config_text.pack(side="left", fill="both", expand=True)
        file_scrollbar.pack(side="right", fill="y")
        
        # 初始加载
        self.refresh_file_config()
    
    def refresh_current_config(self):
        """刷新当前配置显示"""
        try:
            # 清空现有内容
            for widget in self.current_config_frame.winfo_children():
                widget.destroy()
            
            # 获取当前配置
            config = self.config_manager.config
            
            # 显示路径配置
            path_frame = ttk.LabelFrame(self.current_config_frame, text="路径配置")
            path_frame.pack(fill=tk.X, pady=(0, 10))
            
            self._add_config_item(path_frame, "Ollama 程序路径", config.get("ollama_path", "(未设置)"))
            self._add_config_item(path_frame, "模型存储路径", config.get("model_path", "(未设置)"))
            
            # 显示环境变量配置
            env_frame = ttk.LabelFrame(self.current_config_frame, text="环境变量配置")
            env_frame.pack(fill=tk.X, pady=(0, 10))
            
            env_vars = config.get("environment_variables", {})
            for key, value in env_vars.items():
                self._add_config_item(env_frame, key, value or "(未设置)")
            
            # 显示高级设置
            advanced_frame = ttk.LabelFrame(self.current_config_frame, text="高级设置")
            advanced_frame.pack(fill=tk.X, pady=(0, 10))
            
            advanced_settings = config.get("advanced_settings", {})
            for key, value in advanced_settings.items():
                self._add_config_item(advanced_frame, key, str(value))
            
            # 显示UI设置
            ui_frame = ttk.LabelFrame(self.current_config_frame, text="界面设置")
            ui_frame.pack(fill=tk.X, pady=(0, 10))
            
            ui_settings = config.get("ui_settings", {})
            for key, value in ui_settings.items():
                self._add_config_item(ui_frame, key, str(value))
                
        except Exception as e:
            self.logger.error(f"刷新当前配置失败: {e}")
    
    def refresh_file_config(self):
        """刷新文件配置显示"""
        try:
            import json
            
            # 读取配置文件
            if self.config_manager.config_file.exists():
                with open(self.config_manager.config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 格式化JSON
                try:
                    parsed = json.loads(content)
                    formatted_content = json.dumps(parsed, indent=2, ensure_ascii=False)
                except json.JSONDecodeError:
                    formatted_content = content
            else:
                formatted_content = "配置文件不存在"
            
            # 显示内容
            self.file_config_text.delete(1.0, tk.END)
            self.file_config_text.insert(1.0, formatted_content)
            
        except Exception as e:
            self.logger.error(f"刷新文件配置失败: {e}")
            self.file_config_text.delete(1.0, tk.END)
            self.file_config_text.insert(1.0, f"读取配置文件失败: {e}")
    
    def _add_config_item(self, parent, label, value):
        """添加配置项显示"""
        item_frame = ttk.Frame(parent)
        item_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(item_frame, text=f"{label}:", width=25, anchor="w").pack(side=tk.LEFT)
        
        value_str = str(value) if value else "(未设置)"
        color = "blue" if value else "gray"
        ttk.Label(item_frame, text=value_str, foreground=color).pack(side=tk.LEFT, fill=tk.X, expand=True)
