#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口模块

实现 Ollama Manager 的主界面，包括：
- 状态监控面板
- 服务控制
- 配置管理
- 模型管理
- 对话测试
- 日志查看
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
from datetime import datetime
from typing import Dict, List, Optional, Callable
from .config_tabs import ConfigTabs


class MainWindow:
    """
    主窗口类
    
    管理整个应用的用户界面
    """
    
    def __init__(self, root, ollama_service, config_manager, logger):
        """初始化主窗口"""
        self.root = root
        self.ollama_service = ollama_service
        self.config_manager = config_manager
        self.logger = logger
        
        # 窗口配置
        self.setup_window()
        
        # 创建界面
        self.create_widgets()
        
        # 绑定事件
        self.bind_events()
        
        # 延迟加载配置，避免阻塞主线程
        self.root.after(200, self.load_config_values)
        
        # 延迟初始化状态，避免阻塞主线程
        self.root.after(500, self.refresh_status)
        
        # 不启动自动刷新，只在需要时手动刷新
    
    def setup_window(self):
        """设置窗口属性"""
        self.root.title("Ollama Manager v2.0")
        
        # 使用默认窗口大小，避免在初始化时读取配置文件
        width = 1000
        height = 700
        
        # 居中显示
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(800, 600)
        
        # 延迟加载窗口配置
        self.root.after(100, self.load_window_config)
        
        # 设置图标（如果有的话）
        try:
            # self.root.iconbitmap('icon.ico')
            pass
        except:
            pass
    
    def load_window_config(self):
        """延迟加载窗口配置"""
        try:
            width = self.config_manager.get_ui_setting('window_width', 1000)
            height = self.config_manager.get_ui_setting('window_height', 700)
            
            # 只有配置与当前不同时才更新
            current_geometry = self.root.geometry()
            if f"{width}x{height}" not in current_geometry:
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                x = (screen_width - width) // 2
                y = (screen_height - height) // 2
                self.root.geometry(f"{width}x{height}+{x}+{y}")
        except Exception as e:
            self.logger.error(f"加载窗口配置失败: {e}")
    
    def load_config_values(self):
        """延迟加载配置值"""
        try:
            # 加载路径配置
            self.ollama_path_var.set(self.config_manager.get_ollama_path())
            self.model_path_var.set(self.config_manager.get_model_path())
            
            # 加载环境变量
            env_vars = self.config_manager.get_environment_variables()
            for key, var in self.env_vars.items():
                if key in env_vars:
                    var.set(env_vars[key])
            
            # 加载高级设置
            self.auto_start_var.set(self.config_manager.get_advanced_setting('auto_start', False))
            self.check_updates_var.set(self.config_manager.get_advanced_setting('check_updates', True))
            self.log_level_var.set(self.config_manager.get_advanced_setting('log_level', 'INFO'))
        except Exception as e:
            self.logger.error(f"加载配置值失败: {e}")
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建顶部状态栏
        self.create_status_bar(main_frame)
        
        # 创建主要内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 创建左侧控制面板
        self.create_control_panel(content_frame)
        
        # 创建右侧选项卡
        self.create_notebook(content_frame)
        
        # 创建底部状态栏
        self.create_bottom_status_bar(main_frame)
    
    def create_status_bar(self, parent):
        """创建顶部状态栏"""
        status_frame = ttk.LabelFrame(parent, text="服务状态", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 状态信息
        info_frame = ttk.Frame(status_frame)
        info_frame.pack(fill=tk.X)
        
        # 运行状态
        ttk.Label(info_frame, text="运行状态:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.status_label = ttk.Label(info_frame, text="检查中...", foreground="orange")
        self.status_label.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # 版本信息
        ttk.Label(info_frame, text="版本:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.version_label = ttk.Label(info_frame, text="未知")
        self.version_label.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))
        
        # 控制按钮
        button_frame = ttk.Frame(status_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.start_button = ttk.Button(button_frame, text="启动", command=self.start_service)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="停止", command=self.stop_service)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.restart_button = ttk.Button(button_frame, text="重启", command=self.restart_service)
        self.restart_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.refresh_button = ttk.Button(button_frame, text="刷新状态", command=self.refresh_status)
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 20))
        
        # 更新检查
        self.update_button = ttk.Button(button_frame, text="检查更新", command=self.check_updates)
        self.update_button.pack(side=tk.RIGHT)
    
    def create_control_panel(self, parent):
        """创建左侧控制面板"""
        control_frame = ttk.LabelFrame(parent, text="控制面板", padding=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        # 硬件信息
        hardware_frame = ttk.LabelFrame(control_frame, text="硬件信息")
        hardware_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.hardware_tree = ttk.Treeview(hardware_frame, height=8)
        self.hardware_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 刷新硬件信息按钮
        ttk.Button(hardware_frame, text="刷新硬件信息", 
                  command=self.refresh_hardware_info).pack(pady=5)
        
        # 快速操作
        quick_frame = ttk.LabelFrame(control_frame, text="快速操作")
        quick_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(quick_frame, text="打开模型目录", 
                  command=self.open_model_directory).pack(fill=tk.X, pady=2)
        ttk.Button(quick_frame, text="打开程序目录", 
                  command=self.open_program_directory).pack(fill=tk.X, pady=2)
        ttk.Button(quick_frame, text="导出配置", 
                  command=self.export_config).pack(fill=tk.X, pady=2)
        ttk.Button(quick_frame, text="导入配置", 
                  command=self.import_config).pack(fill=tk.X, pady=2)
    
    def create_notebook(self, parent):
        """创建右侧选项卡"""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 配置选项卡
        self.create_config_tab()
        
        # 模型管理选项卡
        self.create_model_tab()
        
        # 对话测试选项卡
        self.create_chat_tab()
        
        # 日志查看选项卡
        self.create_log_tab()
    
    def create_config_tab(self):
        """创建配置选项卡"""
        config_frame = ttk.Frame(self.notebook)
        self.notebook.add(config_frame, text="配置")
        
        # 创建主配置区域（用于编辑）
        main_frame = ttk.Frame(config_frame)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建配置编辑选项卡
        config_notebook = ttk.Notebook(main_frame)
        config_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 编辑配置选项卡
        edit_frame = ttk.Frame(config_notebook)
        config_notebook.add(edit_frame, text="编辑配置")
        
        # 创建滚动框架
        canvas = tk.Canvas(edit_frame)
        scrollbar = ttk.Scrollbar(edit_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 路径配置
        path_frame = ttk.LabelFrame(scrollable_frame, text="路径配置", padding=10)
        path_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Ollama 程序路径
        ttk.Label(path_frame, text="Ollama 程序路径:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.ollama_path_var = tk.StringVar()
        ollama_path_frame = ttk.Frame(path_frame)
        ollama_path_frame.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0), pady=2)
        ttk.Entry(ollama_path_frame, textvariable=self.ollama_path_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(ollama_path_frame, text="浏览", command=self.browse_ollama_path).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 模型存储路径
        ttk.Label(path_frame, text="模型存储路径:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.model_path_var = tk.StringVar()
        model_path_frame = ttk.Frame(path_frame)
        model_path_frame.grid(row=1, column=1, sticky=tk.EW, padx=(10, 0), pady=2)
        ttk.Entry(model_path_frame, textvariable=self.model_path_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(model_path_frame, text="浏览", command=self.browse_model_path).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 添加说明标签
        ttk.Label(path_frame, text="提示：模型存储路径会自动读取 OLLAMA_MODELS 环境变量", 
                 foreground="gray", font=('Arial', 8)).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        path_frame.columnconfigure(1, weight=1)
        
        # 环境变量配置
        env_frame = ttk.LabelFrame(scrollable_frame, text="环境变量", padding=10)
        env_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.env_vars = {}
        
        for i, (key, default_value) in enumerate([
            ('OLLAMA_HOST', '127.0.0.1:11434'),
            ('OLLAMA_MODELS', ''),
            ('OLLAMA_KEEP_ALIVE', '5m'),
            ('OLLAMA_NUM_PARALLEL', '1'),
            ('OLLAMA_MAX_LOADED_MODELS', '1'),
            ('OLLAMA_DEBUG', 'false')
        ]):
            ttk.Label(env_frame, text=f"{key}:").grid(row=i, column=0, sticky=tk.W, pady=2)
            var = tk.StringVar(value=default_value)
            self.env_vars[key] = var
            ttk.Entry(env_frame, textvariable=var, width=50).grid(row=i, column=1, sticky=tk.EW, padx=(10, 0), pady=2)
        
        env_frame.columnconfigure(1, weight=1)
        
        # 高级设置
        advanced_frame = ttk.LabelFrame(scrollable_frame, text="高级设置", padding=10)
        advanced_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 自动启动
        self.auto_start_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_frame, text="程序启动时自动启动 Ollama 服务", 
                       variable=self.auto_start_var).pack(anchor=tk.W, pady=2)
        
        # 检查更新
        self.check_updates_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(advanced_frame, text="启动时检查更新", 
                       variable=self.check_updates_var).pack(anchor=tk.W, pady=2)
        
        # 日志级别
        log_frame = ttk.Frame(advanced_frame)
        log_frame.pack(fill=tk.X, pady=5)
        ttk.Label(log_frame, text="日志级别:").pack(side=tk.LEFT)
        self.log_level_var = tk.StringVar(value='INFO')
        log_combo = ttk.Combobox(log_frame, textvariable=self.log_level_var, 
                                values=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                                state='readonly', width=10)
        log_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # 配置按钮
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="保存配置", command=self.save_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="重置配置", command=self.reset_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="应用并重启", command=self.apply_and_restart).pack(side=tk.LEFT)
        
        # 重置配置说明
        reset_info = ttk.Label(scrollable_frame, 
                              text="重置配置：将所有设置恢复为默认值，包括路径、环境变量和高级设置", 
                              foreground="gray", font=('Arial', 8))
        reset_info.pack(fill=tk.X, pady=(5, 0))
        
        # 打包滚动组件
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 创建配置查看选项卡
        self.config_tabs = ConfigTabs(config_notebook, self.config_manager, self.logger)
    
    def create_model_tab(self):
        """创建模型管理选项卡"""
        model_frame = ttk.Frame(self.notebook)
        self.notebook.add(model_frame, text="模型管理")
        
        # 已安装模型
        installed_frame = ttk.LabelFrame(model_frame, text="已安装模型", padding=10)
        installed_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # 模型列表
        columns = ('name', 'size', 'modified')
        self.model_tree = ttk.Treeview(installed_frame, columns=columns, show='tree headings')
        self.model_tree.heading('#0', text='模型名称')
        self.model_tree.heading('name', text='标签')
        self.model_tree.heading('size', text='大小')
        self.model_tree.heading('modified', text='修改时间')
        
        # 设置列宽
        self.model_tree.column('#0', width=200)
        self.model_tree.column('name', width=150)
        self.model_tree.column('size', width=100)
        self.model_tree.column('modified', width=150)
        
        # 滚动条
        model_scrollbar = ttk.Scrollbar(installed_frame, orient="vertical", command=self.model_tree.yview)
        self.model_tree.configure(yscrollcommand=model_scrollbar.set)
        
        self.model_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        model_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 模型操作按钮
        model_button_frame = ttk.Frame(installed_frame)
        model_button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(model_button_frame, text="刷新列表", command=self.refresh_models).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(model_button_frame, text="删除模型", command=self.delete_model).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(model_button_frame, text="模型信息", command=self.show_model_info).pack(side=tk.LEFT)
        
        # 下载模型
        download_frame = ttk.LabelFrame(model_frame, text="下载模型", padding=10)
        download_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 模型名称输入
        input_frame = ttk.Frame(download_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(input_frame, text="模型名称:").pack(side=tk.LEFT)
        self.model_name_var = tk.StringVar()
        model_entry = ttk.Entry(input_frame, textvariable=self.model_name_var, width=30)
        model_entry.pack(side=tk.LEFT, padx=(10, 5), fill=tk.X, expand=True)
        ttk.Button(input_frame, text="下载", command=self.download_model).pack(side=tk.LEFT)
        
        # 推荐模型列表已移除，用户可直接输入模型名称下载
        
        # 下载进度
        self.progress_var = tk.StringVar(value="就绪")
        self.progress_label = ttk.Label(download_frame, textvariable=self.progress_var)
        self.progress_label.pack(fill=tk.X, pady=(10, 0))
        
        self.progress_bar = ttk.Progressbar(download_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
    
    def create_chat_tab(self):
        """创建对话测试选项卡"""
        chat_frame = ttk.Frame(self.notebook)
        self.notebook.add(chat_frame, text="对话测试")
        
        # 模型选择
        model_frame = ttk.Frame(chat_frame)
        model_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(model_frame, text="选择模型:").pack(side=tk.LEFT)
        self.chat_model_var = tk.StringVar()
        self.chat_model_combo = ttk.Combobox(model_frame, textvariable=self.chat_model_var, 
                                           state='readonly', width=30)
        self.chat_model_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(model_frame, text="刷新模型", command=self.refresh_chat_models).pack(side=tk.LEFT, padx=(10, 0))
        
        # 对话历史
        history_frame = ttk.LabelFrame(chat_frame, text="对话历史")
        history_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.chat_history = tk.Text(history_frame, wrap=tk.WORD, state=tk.DISABLED)
        chat_scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.chat_history.yview)
        self.chat_history.configure(yscrollcommand=chat_scrollbar.set)
        
        self.chat_history.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # 输入区域
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X)
        
        self.chat_input = tk.Text(input_frame, height=3, wrap=tk.WORD)
        input_scrollbar = ttk.Scrollbar(input_frame, orient="vertical", command=self.chat_input.yview)
        self.chat_input.configure(yscrollcommand=input_scrollbar.set)
        
        self.chat_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        input_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮
        button_frame = ttk.Frame(chat_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(button_frame, text="发送", command=self.send_message).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="清空历史", command=self.clear_chat_history).pack(side=tk.LEFT)
        
        # 绑定回车键
        self.chat_input.bind('<Control-Return>', lambda e: self.send_message())
    
    def create_log_tab(self):
        """创建日志查看选项卡"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="日志")
        
        # 日志控制
        control_frame = ttk.Frame(log_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 日志级别过滤
        ttk.Label(control_frame, text="级别:").pack(side=tk.LEFT)
        self.log_filter_var = tk.StringVar(value="全部")
        log_filter_combo = ttk.Combobox(control_frame, textvariable=self.log_filter_var,
                                       values=['全部', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                                       state='readonly', width=10)
        log_filter_combo.pack(side=tk.LEFT, padx=(5, 20))
        log_filter_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_logs())
        
        # 控制按钮
        ttk.Button(control_frame, text="刷新", command=self.refresh_logs).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="清空", command=self.clear_logs).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="导出", command=self.export_logs).pack(side=tk.LEFT)
        
        # 自动滚动
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="自动滚动", variable=self.auto_scroll_var).pack(side=tk.RIGHT)
        
        # 日志显示
        log_display_frame = ttk.Frame(log_frame)
        log_display_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_display_frame, wrap=tk.WORD, state=tk.DISABLED, font=('Consolas', 9))
        log_text_scrollbar = ttk.Scrollbar(log_display_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_text_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 配置日志颜色
        self.log_text.tag_configure('DEBUG', foreground='gray')
        self.log_text.tag_configure('INFO', foreground='black')
        self.log_text.tag_configure('WARNING', foreground='orange')
        self.log_text.tag_configure('ERROR', foreground='red')
        self.log_text.tag_configure('CRITICAL', foreground='red', background='yellow')
    
    def create_bottom_status_bar(self, parent):
        """创建底部状态栏"""
        self.status_bar = ttk.Frame(parent)
        self.status_bar.pack(fill=tk.X, pady=(5, 0))
        
        # 状态信息
        self.status_text = tk.StringVar(value="就绪")
        ttk.Label(self.status_bar, textvariable=self.status_text).pack(side=tk.LEFT)
        
        # 时间显示
        self.time_label = ttk.Label(self.status_bar)
        self.time_label.pack(side=tk.RIGHT)
        
        # 更新时间
        self.update_time()
    
    def bind_events(self):
        """绑定事件"""
        # 注册服务状态回调
        self.ollama_service.add_status_callback(self.on_status_change)
        self.ollama_service.add_model_callback(self.on_model_change)
        
        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 窗口大小变化事件
        self.root.bind('<Configure>', self.on_window_configure)
    
    def on_status_change(self, is_running, version):
        """状态变化回调"""
        # 避免重复更新相同状态
        if hasattr(self, '_last_status') and self._last_status == (is_running, version):
            return
        
        self._last_status = (is_running, version)
        
        def update_ui():
            try:
                if is_running:
                    self.status_label.config(text="运行中", foreground="green")
                    self.start_button.config(state=tk.DISABLED)
                    self.stop_button.config(state=tk.NORMAL)
                    self.restart_button.config(state=tk.NORMAL)
                else:
                    self.status_label.config(text="已停止", foreground="red")
                    self.start_button.config(state=tk.NORMAL)
                    self.stop_button.config(state=tk.DISABLED)
                    self.restart_button.config(state=tk.DISABLED)
                
                self.version_label.config(text=version or "未知")
            except Exception as e:
                self.logger.error(f"更新UI状态失败: {e}")
        
        # 使用较小的延迟来避免UI阻塞
        self.root.after(100, update_ui)
    
    def on_model_change(self, models):
        """模型变化回调"""
        # 检查模型列表是否真的发生了变化
        model_names = [model.get('name', '') for model in models]
        if hasattr(self, '_last_models') and self._last_models == model_names:
            return
        
        self._last_models = model_names
        
        def update_ui():
            try:
                # 更新模型列表
                for item in self.model_tree.get_children():
                    self.model_tree.delete(item)
                
                for model in models:
                    name = model.get('name', '')
                    size = self._format_size(model.get('size', 0))
                    modified = model.get('modified_at', '')
                    if modified:
                        try:
                            dt = datetime.fromisoformat(modified.replace('Z', '+00:00'))
                            modified = dt.strftime('%Y-%m-%d %H:%M')
                        except:
                            pass
                    
                    self.model_tree.insert('', tk.END, text=name, values=(name, size, modified))
                
                # 更新对话模型列表
                self.chat_model_combo['values'] = model_names
                if model_names and not self.chat_model_var.get():
                    self.chat_model_var.set(model_names[0])
            except Exception as e:
                self.logger.error(f"更新模型列表失败: {e}")
        
        # 使用较小的延迟来避免UI阻塞
        self.root.after(100, update_ui)
    
    def on_window_configure(self, event):
        """窗口配置变化事件"""
        if event.widget == self.root:
            # 使用防抖机制，避免频繁保存配置
            if hasattr(self, '_config_save_timer'):
                self.root.after_cancel(self._config_save_timer)
            
            def save_config_delayed():
                try:
                    self.config_manager.set_ui_setting('window_width', self.root.winfo_width())
                    self.config_manager.set_ui_setting('window_height', self.root.winfo_height())
                except Exception as e:
                    self.logger.error(f"保存窗口配置失败: {e}")
            
            # 延迟1秒保存配置，避免拖拽时频繁保存
            self._config_save_timer = self.root.after(1000, save_config_delayed)
    
    def on_closing(self):
        """窗口关闭事件"""
        # 保存配置
        self.save_config()
        
        # 询问是否停止服务
        if self.ollama_service.is_running:
            result = messagebox.askyesnocancel(
                "退出确认",
                "Ollama 服务正在运行，是否停止服务？\n\n是：停止服务并退出\n否：保持服务运行并退出\n取消：不退出"
            )
            
            if result is None:  # 取消
                return
            elif result:  # 是，停止服务
                self.ollama_service.stop()
        
        self.root.destroy()
    
    # 服务控制方法
    def start_service(self):
        """启动服务"""
        def start_thread():
            success = self.ollama_service.start()
            if success:
                self.logger.info("Ollama 服务启动成功")
            else:
                self.logger.error("Ollama 服务启动失败")
        
        threading.Thread(target=start_thread, daemon=True).start()
    
    def stop_service(self):
        """停止服务"""
        def stop_thread():
            success = self.ollama_service.stop()
            if success:
                self.logger.info("Ollama 服务已停止")
            else:
                self.logger.error("停止 Ollama 服务失败")
        
        threading.Thread(target=stop_thread, daemon=True).start()
    
    def restart_service(self):
        """重启服务"""
        def restart_thread():
            success = self.ollama_service.restart()
            if success:
                self.logger.info("Ollama 服务重启成功")
            else:
                self.logger.error("Ollama 服务重启失败")
        
        threading.Thread(target=restart_thread, daemon=True).start()
    
    def refresh_status(self, retry_count=0):
        """刷新状态"""
        def refresh_thread():
            try:
                # 先检查状态
                self.ollama_service.check_status()
                
                # 只有在状态发生变化或首次运行时才获取模型列表
                if self.ollama_service.is_running:
                    # 避免频繁获取模型列表，增加缓存机制
                    if not hasattr(self, '_last_model_refresh') or \
                       (datetime.now() - self._last_model_refresh).seconds >= 60:
                        self.ollama_service.get_models()
                        self._last_model_refresh = datetime.now()
            except Exception as e:
                self.logger.error(f"刷新状态失败: {e}")
                # 失败后重试，最多重试2次
                if retry_count < 2:
                    self.logger.info(f"刷新失败，{3}秒后重试 (第{retry_count + 1}次)")
                    self.root.after(3000, lambda: self.refresh_status(retry_count + 1))
        
        threading.Thread(target=refresh_thread, daemon=True).start()
    
    def check_updates(self):
        """检查更新"""
        def check_thread():
            try:
                update_info = self.ollama_service.check_for_updates()
                if update_info:
                    if update_info.get('has_update'):
                        message = f"发现新版本: {update_info['latest_version']}\n当前版本: {update_info['current_version']}\n\n是否打开下载页面？"
                        if messagebox.askyesno("发现更新", message):
                            import webbrowser
                            webbrowser.open(update_info['download_url'])
                    else:
                        messagebox.showinfo("检查更新", "当前已是最新版本")
                else:
                    messagebox.showerror("检查更新", "检查更新失败，请检查网络连接")
            except Exception as e:
                self.logger.error(f"检查更新失败: {e}")
                messagebox.showerror("错误", f"检查更新失败: {e}")
        
        threading.Thread(target=check_thread, daemon=True).start()
    
    # 配置相关方法
    def browse_ollama_path(self):
        """浏览 Ollama 程序路径"""
        filename = filedialog.askopenfilename(
            title="选择 Ollama 程序",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
        )
        if filename:
            self.ollama_path_var.set(filename)
    
    def browse_model_path(self):
        """浏览模型存储路径"""
        dirname = filedialog.askdirectory(title="选择模型存储目录")
        if dirname:
            self.model_path_var.set(dirname)
    
    def save_config(self):
        """保存配置"""
        try:
            # 保存路径配置
            self.config_manager.set_ollama_path(self.ollama_path_var.get())
            self.config_manager.set_model_path(self.model_path_var.get())
            
            # 保存环境变量
            for key, var in self.env_vars.items():
                self.config_manager.set_environment_variable(key, var.get())
            
            # 保存高级设置
            self.config_manager.set_advanced_setting('auto_start', self.auto_start_var.get())
            self.config_manager.set_advanced_setting('check_updates', self.check_updates_var.get())
            self.config_manager.set_advanced_setting('log_level', self.log_level_var.get())
            
            # 应用日志级别
            self.logger.set_level(self.log_level_var.get())
            
            # 保存到文件
            if self.config_manager.save_config():
                self.status_text.set("配置已保存")
                self.logger.info("配置保存成功")
                # 保存配置后自动刷新一次
                self.root.after(100, self.refresh_status)
            else:
                messagebox.showerror("错误", "配置保存失败")
                
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            messagebox.showerror("错误", f"保存配置失败: {e}")
    
    def reset_config(self):
        """重置配置"""
        if messagebox.askyesno("确认重置", "确定要重置所有配置到默认值吗？"):
            self.config_manager.reset_to_defaults()
            self._load_config_to_ui()
            self.logger.info("配置已重置")
    
    def apply_and_restart(self):
        """应用配置并重启服务"""
        self.save_config()
        if self.ollama_service.is_running:
            self.restart_service()
    
    def _load_config_to_ui(self):
        """加载配置到界面"""
        self.ollama_path_var.set(self.config_manager.get_ollama_path())
        self.model_path_var.set(self.config_manager.get_model_path())
        
        env_vars = self.config_manager.get_environment_variables()
        for key, var in self.env_vars.items():
            var.set(env_vars.get(key, ''))
        
        self.auto_start_var.set(self.config_manager.get_advanced_setting('auto_start', False))
        self.check_updates_var.set(self.config_manager.get_advanced_setting('check_updates', True))
        self.log_level_var.set(self.config_manager.get_advanced_setting('log_level', 'INFO'))
    
    # 其他功能方法
    def refresh_hardware_info(self):
        """刷新硬件信息"""
        def refresh_thread():
            try:
                hardware_info = self.ollama_service.get_hardware_info()
                
                def update_ui():
                    # 清空现有内容
                    for item in self.hardware_tree.get_children():
                        self.hardware_tree.delete(item)
                    
                    # CPU 信息
                    cpu_info = hardware_info.get('cpu', {})
                    cpu_node = self.hardware_tree.insert('', tk.END, text='CPU', open=True)
                    for key, value in cpu_info.items():
                        self.hardware_tree.insert(cpu_node, tk.END, text=f"{key}: {value}")
                    
                    # 内存信息
                    memory_info = hardware_info.get('memory', {})
                    memory_node = self.hardware_tree.insert('', tk.END, text='内存', open=True)
                    for key, value in memory_info.items():
                        self.hardware_tree.insert(memory_node, tk.END, text=f"{key}: {value}")
                    
                    # GPU 信息
                    gpu_list = hardware_info.get('gpu', [])
                    if gpu_list:
                        gpu_node = self.hardware_tree.insert('', tk.END, text='GPU', open=True)
                        for i, gpu in enumerate(gpu_list):
                            gpu_item = self.hardware_tree.insert(gpu_node, tk.END, text=f"GPU {i+1}: {gpu.get('name', 'Unknown')}")
                            for key, value in gpu.items():
                                if key != 'name':
                                    self.hardware_tree.insert(gpu_item, tk.END, text=f"{key}: {value}")
                
                self.root.after(0, update_ui)
                
            except Exception as e:
                self.logger.error(f"刷新硬件信息失败: {e}")
        
        threading.Thread(target=refresh_thread, daemon=True).start()
    
    def open_model_directory(self):
        """打开模型目录"""
        import subprocess
        import os
        
        model_path = self.config_manager.get_model_path()
        if model_path and os.path.exists(model_path):
            subprocess.run(['explorer', model_path])
        else:
            messagebox.showwarning("警告", "模型目录不存在或未配置")
    
    def open_program_directory(self):
        """打开程序目录"""
        import subprocess
        import os
        
        ollama_path = self.config_manager.get_ollama_path()
        if ollama_path and os.path.exists(ollama_path):
            program_dir = os.path.dirname(ollama_path)
            subprocess.run(['explorer', program_dir])
        else:
            messagebox.showwarning("警告", "程序路径不存在或未配置")
    
    def export_config(self):
        """导出配置"""
        filename = filedialog.asksaveasfilename(
            title="导出配置",
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
        )
        if filename:
            if self.config_manager.export_config(filename):
                messagebox.showinfo("成功", "配置导出成功")
            else:
                messagebox.showerror("错误", "配置导出失败")
    
    def import_config(self):
        """导入配置"""
        filename = filedialog.askopenfilename(
            title="导入配置",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
        )
        if filename:
            if self.config_manager.import_config(filename):
                self._load_config_to_ui()
                messagebox.showinfo("成功", "配置导入成功")
            else:
                messagebox.showerror("错误", "配置导入失败")
    
    # 模型管理方法
    def refresh_models(self):
        """刷新模型列表"""
        def refresh_thread():
            self.ollama_service.get_models()
        
        threading.Thread(target=refresh_thread, daemon=True).start()
    
    def delete_model(self):
        """删除模型"""
        selection = self.model_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的模型")
            return
        
        item = selection[0]
        model_name = self.model_tree.item(item, 'text')
        
        if messagebox.askyesno("确认删除", f"确定要删除模型 '{model_name}' 吗？"):
            def delete_thread():
                success = self.ollama_service.delete_model(model_name)
                if success:
                    self.logger.info(f"模型 {model_name} 删除成功")
                else:
                    self.logger.error(f"删除模型 {model_name} 失败")
            
            threading.Thread(target=delete_thread, daemon=True).start()
    
    def show_model_info(self):
        """显示模型信息"""
        selection = self.model_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要查看的模型")
            return
        
        item = selection[0]
        model_name = self.model_tree.item(item, 'text')
        values = self.model_tree.item(item, 'values')
        
        info = f"模型名称: {model_name}\n"
        info += f"标签: {values[0] if values else 'N/A'}\n"
        info += f"大小: {values[1] if len(values) > 1 else 'N/A'}\n"
        info += f"修改时间: {values[2] if len(values) > 2 else 'N/A'}"
        
        messagebox.showinfo("模型信息", info)
    
    def download_model(self):
        """下载模型"""
        model_name = self.model_name_var.get().strip()
        if not model_name:
            messagebox.showwarning("警告", "请输入模型名称")
            return
        
        self._start_download(model_name)
    
    # download_recommended_model 方法已移除，推荐模型功能不再需要
    
    def _start_download(self, model_name):
        """开始下载模型"""
        def download_thread():
            def progress_callback(data):
                status = data.get('status', '')
                if 'total' in data and 'completed' in data:
                    total = data['total']
                    completed = data['completed']
                    percent = (completed / total) * 100 if total > 0 else 0
                    message = f"下载 {model_name}: {percent:.1f}% ({self._format_size(completed)}/{self._format_size(total)})"
                else:
                    message = f"下载 {model_name}: {status}"
                
                def update_ui():
                    self.progress_var.set(message)
                    if not self.progress_bar.cget('mode') == 'determinate':
                        self.progress_bar.config(mode='determinate')
                    if 'total' in data and 'completed' in data and data['total'] > 0:
                        progress = (data['completed'] / data['total']) * 100
                        self.progress_bar['value'] = progress
                
                self.root.after(0, update_ui)
            
            # 开始下载
            self.root.after(0, lambda: self.progress_bar.start())
            self.root.after(0, lambda: self.progress_var.set(f"开始下载 {model_name}..."))
            
            success = self.ollama_service.pull_model(model_name, progress_callback)
            
            def finish_download():
                self.progress_bar.stop()
                self.progress_bar['value'] = 0
                if success:
                    self.progress_var.set(f"模型 {model_name} 下载完成")
                    self.logger.info(f"模型 {model_name} 下载完成")
                else:
                    self.progress_var.set(f"模型 {model_name} 下载失败")
                    self.logger.error(f"模型 {model_name} 下载失败")
            
            self.root.after(0, finish_download)
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    # 对话功能方法
    def refresh_chat_models(self):
        """刷新对话模型列表"""
        self.refresh_models()
    
    def send_message(self):
        """发送消息"""
        model = self.chat_model_var.get()
        if not model:
            messagebox.showwarning("警告", "请选择模型")
            return
        
        message = self.chat_input.get(1.0, tk.END).strip()
        if not message:
            messagebox.showwarning("警告", "请输入消息")
            return
        
        # 清空输入框
        self.chat_input.delete(1.0, tk.END)
        
        # 添加用户消息到历史
        self._add_chat_message("用户", message)
        
        def chat_thread():
            try:
                messages = [{'role': 'user', 'content': message}]
                response = self.ollama_service.chat(model, messages, stream=True)
                
                if response.status_code == 200:
                    assistant_message = ""
                    
                    def start_assistant_message():
                        self._add_chat_message("助手", "", start_new=True)
                    
                    self.root.after(0, start_assistant_message)
                    
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line.decode('utf-8'))
                                if 'message' in data and 'content' in data['message']:
                                    content = data['message']['content']
                                    assistant_message += content
                                    
                                    def update_message():
                                        self._update_last_chat_message(assistant_message)
                                    
                                    self.root.after(0, update_message)
                                
                                if data.get('done', False):
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    def show_error():
                        self._add_chat_message("系统", f"请求失败: HTTP {response.status_code}")
                    
                    self.root.after(0, show_error)
                    
            except Exception as e:
                self.logger.error(f"对话请求失败: {e}")
                
                def show_error():
                    self._add_chat_message("系统", f"对话失败: {e}")
                
                self.root.after(0, show_error)
        
        threading.Thread(target=chat_thread, daemon=True).start()
    
    def _add_chat_message(self, sender, message, start_new=False):
        """添加聊天消息"""
        self.chat_history.config(state=tk.NORMAL)
        
        if start_new:
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.chat_history.insert(tk.END, f"\n[{timestamp}] {sender}: ")
            self.chat_history.see(tk.END)
        else:
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.chat_history.insert(tk.END, f"\n[{timestamp}] {sender}: {message}\n")
            self.chat_history.see(tk.END)
        
        self.chat_history.config(state=tk.DISABLED)
    
    def _update_last_chat_message(self, message):
        """更新最后一条聊天消息"""
        self.chat_history.config(state=tk.NORMAL)
        
        # 获取最后一行的位置
        last_line = self.chat_history.index(tk.END + "-1c linestart")
        
        # 查找最后一个 ": " 的位置
        content = self.chat_history.get(last_line, tk.END)
        colon_pos = content.find(": ")
        
        if colon_pos != -1:
            # 删除 ": " 之后的内容
            start_pos = f"{last_line}+{colon_pos + 2}c"
            self.chat_history.delete(start_pos, tk.END)
            
            # 插入新内容
            self.chat_history.insert(start_pos, message)
            self.chat_history.see(tk.END)
        
        self.chat_history.config(state=tk.DISABLED)
    
    def clear_chat_history(self):
        """清空聊天历史"""
        if messagebox.askyesno("确认清空", "确定要清空聊天历史吗？"):
            self.chat_history.config(state=tk.NORMAL)
            self.chat_history.delete(1.0, tk.END)
            self.chat_history.config(state=tk.DISABLED)
    
    # 日志功能方法
    def refresh_logs(self):
        """刷新日志"""
        try:
            level_filter = self.log_filter_var.get()
            level = None if level_filter == "全部" else level_filter
            
            logs = self.logger.get_memory_logs(level=level, limit=500)
            
            # 检查日志是否有变化，避免不必要的UI更新
            current_log_hash = hash(str(logs))
            if hasattr(self, '_last_log_hash') and self._last_log_hash == current_log_hash:
                return
            
            self._last_log_hash = current_log_hash
            
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            
            for log in logs:
                timestamp = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                level = log['level']
                message = log['message']
                
                log_line = f"[{timestamp}] [{level}] {message}\n"
                self.log_text.insert(tk.END, log_line, level)
            
            if self.auto_scroll_var.get():
                self.log_text.see(tk.END)
            
            self.log_text.config(state=tk.DISABLED)
        except Exception as e:
            self.logger.error(f"刷新日志失败: {e}")
    
    def clear_logs(self):
        """清空日志"""
        if messagebox.askyesno("确认清空", "确定要清空内存中的日志吗？"):
            self.logger.clear_memory_logs()
            self.refresh_logs()
    
    def export_logs(self):
        """导出日志"""
        filename = filedialog.asksaveasfilename(
            title="导出日志",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            level_filter = self.log_filter_var.get()
            level = None if level_filter == "全部" else level_filter
            
            if self.logger.export_logs(filename, level=level):
                messagebox.showinfo("成功", "日志导出成功")
            else:
                messagebox.showerror("错误", "日志导出失败")
    
    # 工具方法
    def _format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
    
    def update_time(self):
        """更新时间显示"""
        try:
            if self.root.winfo_exists():
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.time_label.config(text=current_time)
                # 减少时间更新频率到5秒
                self.root.after(5000, self.update_time)
        except Exception as e:
            self.logger.error(f"更新时间显示失败: {e}")
    
    def start_auto_refresh(self):
        """启动自动刷新（已禁用，仅保留方法以兼容现有代码）"""
        # 自动刷新已禁用，只在需要时手动刷新
        pass