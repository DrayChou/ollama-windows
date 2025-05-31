#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama Manager - 完整的 Ollama 管理工具
功能包括：安装、更新、配置、模型管理、对话等
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import subprocess
import requests
import json
import os
import sys
import zipfile
import tempfile
import shutil
import time
import psutil
import re
from datetime import datetime

# 可选依赖
try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False


class OllamaManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Ollama Manager v1.0")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # 配置样式
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 应用状态
        self.ollama_process = None
        self.ollama_path = ""
        self.models_path = ""
        self.current_version = ""
        self.latest_version = ""
        self.gpu_info = []
        
        # 初始化界面
        self.init_ui()
        
        # 启动时检查状态
        self.refresh_status()
        
    def init_ui(self):
        """初始化用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 创建选项卡
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # 各个选项卡
        self.create_status_tab()
        self.create_config_tab()
        self.create_models_tab()
        self.create_chat_tab()
        self.create_logs_tab()
        
        # 底部状态栏
        self.create_status_bar()
        
    def create_status_tab(self):
        """状态监控选项卡"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="状态监控")
        
        # 服务状态框架
        status_frame = ttk.LabelFrame(tab, text="服务状态", padding=10)
        status_frame.pack(fill='x', padx=5, pady=5)
        
        # 状态信息显示
        info_frame = ttk.Frame(status_frame)
        info_frame.pack(fill='x')
        
        # 左侧状态信息
        left_frame = ttk.Frame(info_frame)
        left_frame.pack(side='left', fill='both', expand=True)
        
        ttk.Label(left_frame, text="运行状态:").grid(
            row=0, column=0, sticky='w', padx=(0, 10))
        self.status_label = ttk.Label(
            left_frame, text="检查中...", foreground='orange')
        self.status_label.grid(row=0, column=1, sticky='w')
        
        ttk.Label(left_frame, text="安装路径:").grid(
            row=1, column=0, sticky='w', padx=(0, 10))
        self.path_label = ttk.Label(left_frame, text="未检测到")
        self.path_label.grid(row=1, column=1, sticky='w')
        
        ttk.Label(left_frame, text="当前版本:").grid(
            row=2, column=0, sticky='w', padx=(0, 10))
        self.version_label = ttk.Label(left_frame, text="未知")
        self.version_label.grid(row=2, column=1, sticky='w')
        
        ttk.Label(left_frame, text="最新版本:").grid(
            row=3, column=0, sticky='w', padx=(0, 10))
        self.latest_label = ttk.Label(left_frame, text="检查中...")
        self.latest_label.grid(row=3, column=1, sticky='w')
        
        # 右侧控制按钮
        right_frame = ttk.Frame(info_frame)
        right_frame.pack(side='right', fill='y')
        
        self.start_btn = ttk.Button(
            right_frame, text="启动", command=self.start_ollama)
        self.start_btn.pack(pady=2, fill='x')
        
        self.stop_btn = ttk.Button(
            right_frame, text="停止", command=self.stop_ollama)
        self.stop_btn.pack(pady=2, fill='x')
        
        self.restart_btn = ttk.Button(
            right_frame, text="重启", command=self.restart_ollama)
        self.restart_btn.pack(pady=2, fill='x')
        
        ttk.Separator(right_frame, orient='horizontal').pack(fill='x', pady=5)
        
        self.refresh_btn = ttk.Button(
            right_frame, text="刷新状态", command=self.refresh_status)
        self.refresh_btn.pack(pady=2, fill='x')
        
        # 更新框架
        update_frame = ttk.LabelFrame(tab, text="版本管理", padding=10)
        update_frame.pack(fill='x', padx=5, pady=5)
        
        update_info_frame = ttk.Frame(update_frame)
        update_info_frame.pack(fill='x')
        
        self.update_status_label = ttk.Label(
            update_info_frame, text="点击检查更新")
        self.update_status_label.pack(side='left')
        
        update_btn_frame = ttk.Frame(update_info_frame)
        update_btn_frame.pack(side='right')
        
        self.check_update_btn = ttk.Button(
            update_btn_frame, text="检查更新", command=self.check_updates)
        self.check_update_btn.pack(side='left', padx=2)
        
        self.install_btn = ttk.Button(
            update_btn_frame, text="安装/更新",
            command=self.install_ollama, state='disabled')
        self.install_btn.pack(side='left', padx=2)
        
        # 硬件信息框架
        hw_frame = ttk.LabelFrame(tab, text="硬件信息", padding=10)
        hw_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # GPU 信息树形视图
        self.gpu_tree = ttk.Treeview(
            hw_frame, columns=('name', 'type', 'memory', 'status'),
            show='headings', height=6)
        self.gpu_tree.heading('name', text='显卡名称')
        self.gpu_tree.heading('type', text='类型')
        self.gpu_tree.heading('memory', text='显存')
        self.gpu_tree.heading('status', text='支持状态')
        
        self.gpu_tree.column('name', width=300)
        self.gpu_tree.column('type', width=100)
        self.gpu_tree.column('memory', width=100)
        self.gpu_tree.column('status', width=150)
        
        self.gpu_tree.pack(fill='both', expand=True)
        
        # 刷新硬件信息
        self.refresh_hardware_info()
        
    def create_config_tab(self):
        """配置管理选项卡"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="配置管理")
        
        # 路径配置
        path_frame = ttk.LabelFrame(tab, text="路径配置", padding=10)
        path_frame.pack(fill='x', padx=5, pady=5)
        
        # Ollama 路径
        ttk.Label(path_frame, text="Ollama 程序路径:").grid(
            row=0, column=0, sticky='w', padx=(0, 10))
        self.ollama_path_var = tk.StringVar()
        ttk.Entry(path_frame, textvariable=self.ollama_path_var,
                  width=50).grid(row=0, column=1, sticky='ew', padx=(0, 5))
        ttk.Button(path_frame, text="浏览",
                   command=self.browse_ollama_path).grid(row=0, column=2)
        
        # Models 路径
        ttk.Label(path_frame, text="模型存储路径:").grid(
            row=1, column=0, sticky='w', padx=(0, 10), pady=(5, 0))
        self.models_path_var = tk.StringVar()
        ttk.Entry(path_frame, textvariable=self.models_path_var,
                  width=50).grid(
                  row=1, column=1, sticky='ew',
                  padx=(0, 5), pady=(5, 0))
        ttk.Button(path_frame, text="浏览",
                   command=self.browse_models_path).grid(
                   row=1, column=2, pady=(5, 0))
        
        path_frame.columnconfigure(1, weight=1)
        
        # 环境变量配置
        env_frame = ttk.LabelFrame(tab, text="环境变量", padding=10)
        env_frame.pack(fill='x', padx=5, pady=5)
        
        # OLLAMA_HOST
        ttk.Label(env_frame, text="OLLAMA_HOST:").grid(
            row=0, column=0, sticky='w', padx=(0, 10))
        self.host_var = tk.StringVar(value="0.0.0.0")
        ttk.Entry(env_frame, textvariable=self.host_var,
                  width=20).grid(row=0, column=1, sticky='w')
        ttk.Label(env_frame, text="(设置为 0.0.0.0 允许外部访问)").grid(
            row=0, column=2, sticky='w', padx=(10, 0))
        
        # OLLAMA_PORT
        ttk.Label(env_frame, text="OLLAMA_PORT:").grid(
            row=1, column=0, sticky='w', padx=(0, 10), pady=(5, 0))
        self.port_var = tk.StringVar(value="11434")
        ttk.Entry(env_frame, textvariable=self.port_var,
                  width=20).grid(row=1, column=1, sticky='w', pady=(5, 0))
        ttk.Label(env_frame, text="(默认端口 11434)").grid(
            row=1, column=2, sticky='w', padx=(10, 0), pady=(5, 0))
        
        # HSA_OVERRIDE_GFX_VERSION (AMD)
        ttk.Label(env_frame, text="HSA_OVERRIDE_GFX_VERSION:").grid(
            row=2, column=0, sticky='w', padx=(0, 10), pady=(5, 0))
        self.hsa_var = tk.StringVar()
        ttk.Entry(env_frame, textvariable=self.hsa_var,
                  width=20).grid(row=2, column=1, sticky='w', pady=(5, 0))
        ttk.Label(env_frame, text="(AMD 集显支持，通常设置为 11.0.0)").grid(
            row=2, column=2, sticky='w', padx=(10, 0), pady=(5, 0))
        
        # 高级配置
        advanced_frame = ttk.LabelFrame(tab, text="高级配置", padding=10)
        advanced_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 启动参数
        ttk.Label(advanced_frame, text="额外启动参数:").pack(anchor='w')
        self.args_text = scrolledtext.ScrolledText(
            advanced_frame, height=4, width=50)
        self.args_text.pack(fill='x', pady=(5, 10))
        
        # 配置按钮
        btn_frame = ttk.Frame(advanced_frame)
        btn_frame.pack(fill='x')
        
        ttk.Button(btn_frame, text="保存配置",
                   command=self.save_config).pack(side='left', padx=(0, 5))
        ttk.Button(btn_frame, text="重置配置",
                   command=self.reset_config).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="应用并重启",
                   command=self.apply_and_restart).pack(side='left', padx=5)
        
    def create_models_tab(self):
        """模型管理选项卡"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="模型管理")
        
        # 分割窗口
        paned = ttk.PanedWindow(tab, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 左侧：已安装模型
        left_frame = ttk.LabelFrame(paned, text="已安装模型", padding=5)
        paned.add(left_frame, weight=1)
        
        # 模型列表
        self.models_tree = ttk.Treeview(
            left_frame, columns=('size', 'modified'),
            show='tree headings', height=15)
        self.models_tree.heading('#0', text='模型名称')
        self.models_tree.heading('size', text='大小')
        self.models_tree.heading('modified', text='修改时间')
        
        self.models_tree.column('#0', width=200)
        self.models_tree.column('size', width=100)
        self.models_tree.column('modified', width=150)
        
        # 添加滚动条
        models_scroll = ttk.Scrollbar(
            left_frame, orient='vertical', command=self.models_tree.yview)
        self.models_tree.configure(yscrollcommand=models_scroll.set)
        
        self.models_tree.pack(side='left', fill='both', expand=True)
        models_scroll.pack(side='right', fill='y')
        
        # 模型操作按钮
        models_btn_frame = ttk.Frame(left_frame)
        models_btn_frame.pack(fill='x', pady=(5, 0))
        
        ttk.Button(models_btn_frame, text="刷新列表",
                   command=self.refresh_models).pack(side='left', padx=(0, 5))
        ttk.Button(models_btn_frame, text="删除模型",
                   command=self.delete_model).pack(side='left', padx=5)
        ttk.Button(models_btn_frame, text="模型详情",
                   command=self.show_model_info).pack(side='left', padx=5)
        
        # 右侧：可用模型/下载
        right_frame = ttk.LabelFrame(paned, text="模型库", padding=5)
        paned.add(right_frame, weight=1)
        
        # 搜索框
        search_frame = ttk.Frame(right_frame)
        search_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(search_frame, text="搜索:").pack(side='left')
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side='left', fill='x', expand=True, padx=(5, 5))
        ttk.Button(search_frame, text="搜索",
                   command=self.search_models).pack(side='left')
        
        # 或者直接输入模型名下载
        download_frame = ttk.Frame(right_frame)
        download_frame.pack(fill='x', pady=(0, 5))
        
        ttk.Label(download_frame, text="模型名:").pack(side='left')
        self.model_name_var = tk.StringVar()
        model_entry = ttk.Entry(
            download_frame, textvariable=self.model_name_var)
        model_entry.pack(side='left', fill='x', expand=True, padx=(5, 5))
        ttk.Button(download_frame, text="下载",
                   command=self.download_model).pack(side='left')
        
        # 常用模型快速下载
        quick_frame = ttk.LabelFrame(right_frame, text="推荐模型", padding=5)
        quick_frame.pack(fill='x', pady=(0, 5))
        
        # 创建推荐模型按钮
        popular_models = [
            ("llama3.2", "3B"),
            ("qwen2.5", "7B"),
            ("gemma2", "2B"),
            ("phi3", "3.8B"),
            ("mistral", "7B"),
            ("codellama", "7B")
        ]
        
        for i, (model, size) in enumerate(popular_models):
            row = i // 3
            col = i % 3
            btn_text = f"{model}\n({size})"
            btn = ttk.Button(
                quick_frame, text=btn_text,
                command=lambda m=model: self.quick_download(m))
            btn.grid(row=row, column=col, padx=2, pady=2, sticky='ew')
        
        # 配置列权重
        for i in range(3):
            quick_frame.columnconfigure(i, weight=1)
        
        # 下载进度
        progress_frame = ttk.LabelFrame(
            right_frame, text="下载进度", padding=5)
        progress_frame.pack(fill='x', pady=(0, 5))
        
        self.download_progress = ttk.Progressbar(
            progress_frame, mode='indeterminate')
        self.download_progress.pack(fill='x', pady=(0, 5))
        
        self.download_status = ttk.Label(progress_frame, text="就绪")
        self.download_status.pack()
        
        # 初始化模型列表
        self.refresh_models()
        
    def create_chat_tab(self):
        """对话测试选项卡"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="对话测试")
        
        # 模型选择
        model_frame = ttk.Frame(tab)
        model_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(model_frame, text="选择模型:").pack(side='left')
        self.chat_model_var = tk.StringVar()
        self.chat_model_combo = ttk.Combobox(
            model_frame, textvariable=self.chat_model_var, state='readonly')
        self.chat_model_combo.pack(
            side='left', padx=(5, 10), fill='x', expand=True)
        
        ttk.Button(model_frame, text="刷新",
                   command=self.refresh_chat_models).pack(side='left')
        
        # 对话区域
        chat_frame = ttk.LabelFrame(tab, text="对话", padding=5)
        chat_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 对话历史
        self.chat_history = scrolledtext.ScrolledText(
            chat_frame, height=20, state='disabled')
        self.chat_history.pack(fill='both', expand=True, pady=(0, 5))
        
        # 输入区域
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill='x')
        
        ttk.Label(input_frame, text="输入:").pack(side='left')
        self.chat_input = tk.Text(input_frame, height=3)
        self.chat_input.pack(
            side='left', fill='x', expand=True, padx=(5, 5))
        
        # 按钮
        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(side='right', fill='y')
        
        ttk.Button(btn_frame, text="发送",
                   command=self.send_message).pack(fill='x', pady=(0, 2))
        ttk.Button(btn_frame, text="清空",
                   command=self.clear_chat).pack(fill='x')
        
        # 绑定回车发送
        self.chat_input.bind('<Control-Return>',
                             lambda e: self.send_message())
        
        # 初始化模型列表
        self.refresh_chat_models()
        
    def create_logs_tab(self):
        """日志查看选项卡"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="日志")
        
        # 日志类型选择
        log_type_frame = ttk.Frame(tab)
        log_type_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(log_type_frame, text="日志类型:").pack(side='left')
        self.log_type_var = tk.StringVar(value="应用日志")
        log_type_combo = ttk.Combobox(
            log_type_frame, textvariable=self.log_type_var,
            values=["应用日志", "Ollama 输出"], state='readonly')
        log_type_combo.pack(side='left', padx=(5, 10))
        
        ttk.Button(log_type_frame, text="刷新",
                   command=self.refresh_logs).pack(side='left')
        ttk.Button(log_type_frame, text="清空",
                   command=self.clear_logs).pack(side='left', padx=(5, 0))
        ttk.Button(log_type_frame, text="导出",
                   command=self.export_logs).pack(side='left', padx=(5, 0))
        
        # 日志显示区域
        self.log_text = scrolledtext.ScrolledText(
            tab, height=25, font=('Consolas', 9))
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 初始化日志
        self.log("应用启动")
        
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill='x', side='bottom')
        
        self.status_text = ttk.Label(self.status_bar, text="就绪")
        self.status_text.pack(side='left', padx=5)
        
        # 版本信息
        version_label = ttk.Label(self.status_bar, text="Ollama Manager v1.0")
        version_label.pack(side='right', padx=5)
        
    # 核心功能方法
    def log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, log_message)
        self.log_text.config(state='disabled')
        self.log_text.see(tk.END)
        
        # 同时更新状态栏
        self.status_text.config(text=message)
        self.root.update_idletasks()
        
    def refresh_status(self):
        """刷新 Ollama 运行状态"""
        def check_status():
            try:
                # 检查进程
                ollama_running = False
                for proc in psutil.process_iter(['pid', 'name', 'exe']):
                    if (proc.info['name'] and
                            'ollama' in proc.info['name'].lower()):
                        ollama_running = True
                        if proc.info['exe']:
                            self.ollama_path = proc.info['exe']
                        break
                
                # 更新状态显示
                if ollama_running:
                    self.status_label.config(text="运行中", foreground='green')
                    self.start_btn.config(state='disabled')
                    self.stop_btn.config(state='normal')
                    self.restart_btn.config(state='normal')
                else:
                    self.status_label.config(text="未运行", foreground='red')
                    self.start_btn.config(state='normal')
                    self.stop_btn.config(state='disabled')
                    self.restart_btn.config(state='disabled')
                
                # 检查 ollama.exe 路径
                if not self.ollama_path:
                    # 尝试在当前目录找
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    possible_path = os.path.join(current_dir, "ollama.exe")
                    if os.path.exists(possible_path):
                        self.ollama_path = possible_path
                
                if self.ollama_path and os.path.exists(self.ollama_path):
                    self.path_label.config(text=self.ollama_path)
                    self.ollama_path_var.set(self.ollama_path)
                    
                    # 获取版本号
                    try:
                        result = subprocess.run(
                            [self.ollama_path, "--version"],
                            capture_output=True, text=True, timeout=5)
                        if result.stdout:
                            match = re.search(
                                r'ollama version is ([0-9]+\.[0-9]+\.[0-9]+)',
                                result.stdout)
                            if match:
                                self.current_version = match.group(1)
                                self.version_label.config(
                                    text=self.current_version)
                    except Exception:
                        pass
                else:
                    self.path_label.config(text="未找到")
                
                # 设置默认 models 路径
                if self.ollama_path and not self.models_path:
                    self.models_path = os.path.join(
                        os.path.dirname(self.ollama_path), "models")
                    self.models_path_var.set(self.models_path)
                
                self.log("状态检查完成")
                
            except Exception as e:
                self.log(f"状态检查出错: {str(e)}")
        
        # 在后台线程执行
        threading.Thread(target=check_status, daemon=True).start()
        
    def refresh_hardware_info(self):
        """刷新硬件信息"""
        def get_gpu_info():
            try:
                # 清空现有信息
                for item in self.gpu_tree.get_children():
                    self.gpu_tree.delete(item)
                
                # 尝试多种方式获取显卡信息
                gpu_found = False
                
                # 方法1: 使用 WMI (如果可用)
                if WMI_AVAILABLE:
                    try:
                        import wmi
                        c = wmi.WMI()
                        gpus = c.Win32_VideoController()
                        
                        for gpu in gpus:
                            if (gpu.Name and
                                    not any(x in gpu.Name.lower()
                                             for x in ['basic', 'generic'])):
                                # 显存大小
                                memory = "未知"
                                if gpu.AdapterRAM:
                                    memory = f"{gpu.AdapterRAM // (1024**3)} GB"
                                
                                # 判断显卡类型和支持状态
                                gpu_type = "未知"
                                support_status = "未知"
                                
                                if any(x in gpu.Name.lower() for x in
                                       ['nvidia', 'geforce', 'rtx', 'gtx']):
                                    gpu_type = "NVIDIA"
                                    support_status = "支持 (CUDA)"
                                elif any(x in gpu.Name.lower()
                                         for x in ['amd', 'radeon']):
                                    gpu_type = "AMD"
                                    if any(x in gpu.Name.lower() for x in
                                           ['integrated', 'graphics', 'vega']):
                                        support_status = "集显 (需配置)"
                                    else:
                                        support_status = "支持 (ROCm)"
                                elif any(x in gpu.Name.lower()
                                         for x in ['intel', 'uhd', 'iris']):
                                    gpu_type = "Intel"
                                    support_status = "不支持"
                                
                                # 添加到树形视图
                                self.gpu_tree.insert(
                                    '', 'end',
                                    values=(gpu.Name, gpu_type,
                                            memory, support_status))
                                gpu_found = True
                    
                    except Exception as e:
                        self.log(f"WMI 检测失败: {str(e)}")
                
                # 方法2: 使用 PowerShell (备用方法)
                if not gpu_found:
                    try:
                        ps_script = """
Get-WmiObject -Class Win32_VideoController | Where-Object { $_.Name -notlike "*Basic*" -and $_.Name -notlike "*Generic*" } | ForEach-Object {
    $memory = if ($_.AdapterRAM) { [math]::Round($_.AdapterRAM / 1GB, 2) } else { "未知" }
    Write-Output "$($_.Name)|$memory GB"
}
                        """
                        
                        result = subprocess.run(
                            ['powershell', '-Command', ps_script],
                            capture_output=True, text=True, timeout=10)
                        
                        if result.stdout:
                            lines = result.stdout.strip().split('\n')
                            for line in lines:
                                if '|' in line:
                                    name, memory = line.split('|', 1)
                                    
                                    # 判断显卡类型
                                    gpu_type = "未知"
                                    support_status = "未知"
                                    
                                    if any(x in name.lower() for x in
                                           ['nvidia', 'geforce', 'rtx', 'gtx']):
                                        gpu_type = "NVIDIA"
                                        support_status = "支持 (CUDA)"
                                    elif any(x in name.lower()
                                             for x in ['amd', 'radeon']):
                                        gpu_type = "AMD"
                                        if any(x in name.lower() for x in
                                               ['integrated', 'graphics',
                                                'vega']):
                                            support_status = "集显 (需配置)"
                                        else:
                                            support_status = "支持 (ROCm)"
                                    elif any(x in name.lower()
                                             for x in ['intel', 'uhd', 'iris']):
                                        gpu_type = "Intel"
                                        support_status = "不支持"
                                    
                                    self.gpu_tree.insert(
                                        '', 'end',
                                        values=(name.strip(), gpu_type,
                                                memory.strip(), support_status))
                                    gpu_found = True
                    
                    except Exception as e:
                        self.log(f"PowerShell 检测失败: {str(e)}")
                
                # 如果都失败了，显示提示信息
                if not gpu_found:
                    self.gpu_tree.insert(
                        '', 'end',
                        values=("无法检测显卡信息", "请检查系统", "",
                                "可能需要管理员权限"))
                
                self.log("硬件信息刷新完成")
                
            except Exception as e:
                self.log(f"获取硬件信息出错: {str(e)}")
        
        threading.Thread(target=get_gpu_info, daemon=True).start()
        
    def check_updates(self):
        """检查更新"""
        def check():
            try:
                self.check_update_btn.config(state='disabled')
                self.update_status_label.config(text="检查中...")
                
                # 获取最新版本信息
                response = requests.get(
                    "https://api.github.com/repos/ollama/ollama/releases/latest",
                    timeout=10)
                data = response.json()
                
                self.latest_version = data['tag_name'].replace('v', '')
                self.latest_label.config(text=self.latest_version)
                
                # 比较版本
                if self.current_version:
                    if self.current_version == self.latest_version:
                        self.update_status_label.config(text="已是最新版本")
                        self.install_btn.config(state='disabled')
                    else:
                        self.update_status_label.config(
                            text=f"发现新版本: {self.latest_version}")
                        self.install_btn.config(state='normal')
                else:
                    self.update_status_label.config(
                        text="未检测到 Ollama，可以安装")
                    self.install_btn.config(state='normal')
                
                self.log(f"版本检查完成，最新版本: {self.latest_version}")
                
            except Exception as e:
                self.update_status_label.config(text="检查失败")
                self.log(f"检查更新出错: {str(e)}")
            finally:
                self.check_update_btn.config(state='normal')
        
        threading.Thread(target=check, daemon=True).start()
        
    def install_ollama(self):
        """安装/更新 Ollama"""
        if not self.latest_version:
            messagebox.showerror("错误", "请先检查更新")
            return
        
        if messagebox.askyesno(
                "确认", f"确定要安装/更新到版本 {self.latest_version} 吗？"):
            def install():
                try:
                    self.install_btn.config(state='disabled')
                    self.log("开始下载 Ollama...")
                    
                    # 停止现有服务
                    if self.ollama_process:
                        self.stop_ollama()
                        time.sleep(2)
                    
                    # 下载最新版本
                    download_url = (
                        f"https://github.com/ollama/ollama/releases/"
                        f"download/v{self.latest_version}/"
                        f"ollama-windows-amd64.zip")
                    
                    with tempfile.TemporaryDirectory() as temp_dir:
                        zip_path = os.path.join(temp_dir, "ollama.zip")
                        
                        # 下载文件
                        response = requests.get(download_url, stream=True)
                        total_size = int(
                            response.headers.get('content-length', 0))
                        
                        with open(zip_path, 'wb') as f:
                            downloaded = 0
                            for chunk in response.iter_content(
                                    chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    if total_size > 0:
                                        progress = int(
                                            (downloaded / total_size) * 100)
                                        self.log(f"下载进度: {progress}%")
                        
                        self.log("下载完成，正在解压...")
                        
                        # 解压文件
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(temp_dir)
                        
                        # 安装到目标位置
                        target_path = self.ollama_path_var.get()
                        if not target_path:
                            target_path = os.path.join(
                                os.path.dirname(os.path.abspath(__file__)),
                                "ollama.exe")
                        
                        source_exe = os.path.join(temp_dir, "ollama.exe")
                        if os.path.exists(source_exe):
                            shutil.copy2(source_exe, target_path)
                            self.ollama_path = target_path
                            self.log(f"安装完成: {target_path}")
                            
                            # 刷新状态
                            self.refresh_status()
                        else:
                            raise Exception("解压后未找到 ollama.exe")
                    
                except Exception as e:
                    self.log(f"安装失败: {str(e)}")
                    messagebox.showerror("安装失败", str(e))
                finally:
                    self.install_btn.config(state='normal')
            
            threading.Thread(target=install, daemon=True).start()
    
    def start_ollama(self):
        """启动 Ollama"""
        if not self.ollama_path or not os.path.exists(self.ollama_path):
            messagebox.showerror("错误", "未找到 Ollama 程序")
            return
        
        def start():
            try:
                # 准备环境变量
                env = os.environ.copy()
                if self.models_path_var.get():
                    env['OLLAMA_MODELS'] = self.models_path_var.get()
                if self.host_var.get():
                    env['OLLAMA_HOST'] = self.host_var.get()
                if self.port_var.get():
                    env['OLLAMA_PORT'] = self.port_var.get()
                if self.hsa_var.get():
                    env['HSA_OVERRIDE_GFX_VERSION'] = self.hsa_var.get()
                
                # 启动进程
                self.ollama_process = subprocess.Popen(
                    [self.ollama_path, "serve"],
                    env=env,
                    cwd=os.path.dirname(self.ollama_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                self.log("Ollama 启动中...")
                time.sleep(3)
                self.refresh_status()
                
            except Exception as e:
                self.log(f"启动失败: {str(e)}")
                messagebox.showerror("启动失败", str(e))
        
        threading.Thread(target=start, daemon=True).start()
    
    def stop_ollama(self):
        """停止 Ollama"""
        try:
            # 停止我们启动的进程
            if self.ollama_process:
                self.ollama_process.terminate()
                self.ollama_process = None
            
            # 停止所有 ollama 进程
            for proc in psutil.process_iter(['pid', 'name']):
                if (proc.info['name'] and
                        'ollama' in proc.info['name'].lower()):
                    proc.terminate()
            
            time.sleep(1)
            self.refresh_status()
            self.log("Ollama 已停止")
            
        except Exception as e:
            self.log(f"停止失败: {str(e)}")
    
    def restart_ollama(self):
        """重启 Ollama"""
        self.stop_ollama()
        time.sleep(2)
        self.start_ollama()
    
    def browse_ollama_path(self):
        """浏览 Ollama 程序路径"""
        filename = filedialog.askopenfilename(
            title="选择 Ollama 程序",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
        )
        if filename:
            self.ollama_path_var.set(filename)
            self.ollama_path = filename
    
    def browse_models_path(self):
        """浏览模型存储路径"""
        dirname = filedialog.askdirectory(title="选择模型存储目录")
        if dirname:
            self.models_path_var.set(dirname)
            self.models_path = dirname
    
    def save_config(self):
        """保存配置"""
        try:
            config = {
                'ollama_path': self.ollama_path_var.get(),
                'models_path': self.models_path_var.get(),
                'host': self.host_var.get(),
                'port': self.port_var.get(),
                'hsa_override': self.hsa_var.get(),
                'extra_args': self.args_text.get('1.0', tk.END).strip()
            }
            
            config_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "ollama_config.json")
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.log("配置已保存")
            messagebox.showinfo("成功", "配置已保存")
            
        except Exception as e:
            self.log(f"保存配置失败: {str(e)}")
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
    
    def reset_config(self):
        """重置配置"""
        if messagebox.askyesno("确认", "确定要重置所有配置吗？"):
            self.ollama_path_var.set("")
            self.models_path_var.set("")
            self.host_var.set("0.0.0.0")
            self.port_var.set("11434")
            self.hsa_var.set("")
            self.args_text.delete('1.0', tk.END)
            self.log("配置已重置")
    
    def apply_and_restart(self):
        """应用配置并重启"""
        self.save_config()
        if self.ollama_process:
            self.restart_ollama()
    
    def refresh_models(self):
        """刷新模型列表"""
        def get_models():
            try:
                # 清空现有列表
                for item in self.models_tree.get_children():
                    self.models_tree.delete(item)
                
                # 检查 Ollama 是否运行
                ollama_running = any(
                    'ollama' in proc.info['name'].lower()
                    for proc in psutil.process_iter(['name'])
                    if proc.info['name'])
                
                if ollama_running and self.ollama_path:
                    try:
                        # 获取模型列表
                        result = subprocess.run(
                            [self.ollama_path, "list"],
                            capture_output=True, text=True, timeout=10)
                        
                        if result.stdout:
                            lines = result.stdout.strip().split('\n')[1:]
                            for line in lines:
                                if line.strip():
                                    parts = line.split()
                                    if len(parts) >= 3:
                                        name = parts[0]
                                        size = (parts[2] if len(parts) > 2
                                                else "未知")
                                        modified = (" ".join(parts[3:])
                                                    if len(parts) > 3
                                                    else "未知")
                                        
                                        self.models_tree.insert(
                                            '', 'end', text=name,
                                            values=(size, modified))
                    
                    except subprocess.TimeoutExpired:
                        self.models_tree.insert(
                            '', 'end', text="获取超时", values=("", ""))
                    except Exception as e:
                        self.models_tree.insert(
                            '', 'end', text=f"错误: {str(e)}",
                            values=("", ""))
                else:
                    self.models_tree.insert(
                        '', 'end', text="Ollama 未运行", values=("", ""))
                
                self.log("模型列表刷新完成")
                
            except Exception as e:
                self.log(f"刷新模型列表出错: {str(e)}")
        
        threading.Thread(target=get_models, daemon=True).start()
    
    def delete_model(self):
        """删除选中的模型"""
        selection = self.models_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的模型")
            return
        
        model_name = self.models_tree.item(selection[0], 'text')
        
        if messagebox.askyesno("确认删除", f"确定要删除模型 {model_name} 吗？"):
            def delete():
                try:
                    if self.ollama_path:
                        result = subprocess.run(
                            [self.ollama_path, "rm", model_name],
                            capture_output=True, text=True, timeout=30)
                        
                        if result.returncode == 0:
                            self.log(f"模型 {model_name} 删除成功")
                            self.refresh_models()
                        else:
                            error_msg = (result.stderr or result.stdout or
                                         "删除失败")
                            self.log(f"删除模型失败: {error_msg}")
                            messagebox.showerror("删除失败", error_msg)
                
                except Exception as e:
                    self.log(f"删除模型出错: {str(e)}")
                    messagebox.showerror("错误", str(e))
            
            threading.Thread(target=delete, daemon=True).start()
    
    def show_model_info(self):
        """显示模型详细信息"""
        selection = self.models_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要查看的模型")
            return
        
        model_name = self.models_tree.item(selection[0], 'text')
        
        def get_info():
            try:
                if self.ollama_path:
                    result = subprocess.run(
                        [self.ollama_path, "show", model_name],
                        capture_output=True, text=True, timeout=30)
                    
                    if result.stdout:
                        # 在新窗口显示信息
                        info_window = tk.Toplevel(self.root)
                        info_window.title(f"模型信息 - {model_name}")
                        info_window.geometry("600x400")
                        
                        text_widget = scrolledtext.ScrolledText(
                            info_window, font=('Consolas', 9))
                        text_widget.pack(
                            fill='both', expand=True, padx=10, pady=10)
                        text_widget.insert('1.0', result.stdout)
                        text_widget.config(state='disabled')
                    else:
                        messagebox.showinfo("模型信息", "无法获取模型信息")
            
            except Exception as e:
                messagebox.showerror("错误", f"获取模型信息失败: {str(e)}")
        
        threading.Thread(target=get_info, daemon=True).start()
    
    def download_model(self):
        """下载指定的模型"""
        model_name = self.model_name_var.get().strip()
        if not model_name:
            messagebox.showwarning("警告", "请输入模型名称")
            return
        
        self.quick_download(model_name)
    
    def quick_download(self, model_name):
        """快速下载模型"""
        if not self.ollama_path:
            messagebox.showerror("错误", "未找到 Ollama 程序")
            return
        
        def download():
            try:
                self.download_progress.start()
                self.download_status.config(text=f"正在下载 {model_name}...")
                self.log(f"开始下载模型: {model_name}")
                
                # 使用 Popen 以便实时获取输出
                process = subprocess.Popen(
                    [self.ollama_path, "pull", model_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # 实时读取输出
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        self.log(f"下载: {output.strip()}")
                
                if process.returncode == 0:
                    self.download_status.config(text=f"下载完成: {model_name}")
                    self.log(f"模型 {model_name} 下载成功")
                    self.refresh_models()
                    self.refresh_chat_models()
                else:
                    self.download_status.config(text="下载失败")
                    self.log(f"模型 {model_name} 下载失败")
                
            except Exception as e:
                self.download_status.config(text="下载出错")
                self.log(f"下载模型出错: {str(e)}")
            finally:
                self.download_progress.stop()
        
        threading.Thread(target=download, daemon=True).start()
    
    def search_models(self):
        """搜索模型（这里可以扩展为在线搜索）"""
        search_term = self.search_var.get().strip()
        if search_term:
            # 简单的建议列表
            suggestions = [
                f"{search_term}:latest",
                f"{search_term}:7b",
                f"{search_term}:13b",
                f"{search_term}:3b"
            ]
            
            result = "\n".join(suggestions)
            messagebox.showinfo(
                "搜索建议", f"基于 '{search_term}' 的建议:\n\n{result}")
    
    def refresh_chat_models(self):
        """刷新对话模型列表"""
        def get_models():
            try:
                models = []
                
                # 从已安装模型中获取
                if self.ollama_path:
                    try:
                        result = subprocess.run(
                            [self.ollama_path, "list"],
                            capture_output=True, text=True, timeout=10)
                        
                        if result.stdout:
                            lines = result.stdout.strip().split('\n')[1:]
                            for line in lines:
                                if line.strip():
                                    parts = line.split()
                                    if parts:
                                        models.append(parts[0])
                    except Exception:
                        pass
                
                # 更新下拉框
                self.chat_model_combo['values'] = models
                if models and not self.chat_model_var.get():
                    self.chat_model_combo.current(0)
                
            except Exception as e:
                self.log(f"获取对话模型列表出错: {str(e)}")
        
        threading.Thread(target=get_models, daemon=True).start()
    
    def send_message(self):
        """发送对话消息"""
        model = self.chat_model_var.get()
        if not model:
            messagebox.showwarning("警告", "请选择模型")
            return
        
        message = self.chat_input.get('1.0', tk.END).strip()
        if not message:
            return
        
        # 清空输入框
        self.chat_input.delete('1.0', tk.END)
        
        # 添加用户消息到历史
        self.add_chat_message("用户", message)
        
        def chat():
            try:
                if self.ollama_path:
                    # 准备请求数据
                    data = {
                        "model": model,
                        "prompt": message,
                        "stream": False
                    }
                    
                    # 发送请求到 Ollama API
                    host = self.host_var.get() or 'localhost'
                    port = self.port_var.get() or '11434'
                    response = requests.post(
                        f"http://{host}:{port}/api/generate",
                        json=data,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        reply = result.get('response', '无响应')
                        self.add_chat_message("助手", reply)
                    else:
                        self.add_chat_message(
                            "系统", f"请求失败: {response.status_code}")
                
            except Exception as e:
                self.add_chat_message("系统", f"对话出错: {str(e)}")
        
        threading.Thread(target=chat, daemon=True).start()
    
    def add_chat_message(self, sender, message):
        """添加对话消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.chat_history.config(state='normal')
        self.chat_history.insert(
            tk.END, f"[{timestamp}] {sender}: {message}\n\n")
        self.chat_history.config(state='disabled')
        self.chat_history.see(tk.END)
    
    def clear_chat(self):
        """清空对话历史"""
        self.chat_history.config(state='normal')
        self.chat_history.delete('1.0', tk.END)
        self.chat_history.config(state='disabled')
    
    def refresh_logs(self):
        """刷新日志"""
        # 这里可以从文件或其他来源加载日志
        pass
    
    def clear_logs(self):
        """清空日志"""
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state='disabled')
    
    def export_logs(self):
        """导出日志"""
        try:
            filename = filedialog.asksaveasfilename(
                title="导出日志",
                defaultextension=".log",
                filetypes=[("日志文件", "*.log"), ("文本文件", "*.txt"),
                           ("所有文件", "*.*")]
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    content = self.log_text.get('1.0', tk.END)
                    f.write(content)
                
                messagebox.showinfo("成功", f"日志已导出到: {filename}")
                
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def load_config(self):
        """加载配置"""
        try:
            config_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "ollama_config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.ollama_path_var.set(config.get('ollama_path', ''))
                self.models_path_var.set(config.get('models_path', ''))
                self.host_var.set(config.get('host', '0.0.0.0'))
                self.port_var.set(config.get('port', '11434'))
                self.hsa_var.set(config.get('hsa_override', ''))
                self.args_text.insert('1.0', config.get('extra_args', ''))
                
                # 更新实例变量
                self.ollama_path = self.ollama_path_var.get()
                self.models_path = self.models_path_var.get()
                
                self.log("配置加载完成")
        
        except Exception as e:
            self.log(f"加载配置出错: {str(e)}")
    
    def run(self):
        """运行应用"""
        # 加载配置
        self.load_config()
        
        # 启动主循环
        self.root.mainloop()


if __name__ == "__main__":
    # 检查依赖
    required_modules = ['psutil', 'requests']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"缺少必要的模块: {', '.join(missing_modules)}")
        print("请运行: pip install " + " ".join(missing_modules))
        input("按回车键退出...")
        sys.exit(1)
    
    # 启动应用
    app = OllamaManager()
    app.run()
