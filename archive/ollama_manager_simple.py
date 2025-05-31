#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama Manager 简化测试版本
用于验证基本功能是否正常
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import requests
import json
import os
import psutil
from datetime import datetime

class SimpleOllamaManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Ollama Manager - 测试版")
        self.root.geometry("800x600")
        
        # 应用状态
        self.ollama_path = ""
        self.current_version = ""
        self.latest_version = ""
        
        # 创建界面
        self.create_ui()
        
        # 检查状态
        self.check_ollama_status()
        
    def create_ui(self):
        """创建简化的用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 状态显示
        status_frame = ttk.LabelFrame(main_frame, text="Ollama 状态", padding=10)
        status_frame.pack(fill='x', pady=(0, 10))
        
        # 状态标签
        self.status_label = ttk.Label(status_frame, text="检查中...", font=('Arial', 12, 'bold'))
        self.status_label.pack(pady=5)
        
        self.path_label = ttk.Label(status_frame, text="路径: 未检测到")
        self.path_label.pack()
        
        self.version_label = ttk.Label(status_frame, text="版本: 未知")
        self.version_label.pack()
        
        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="检查状态", command=self.check_ollama_status).pack(side='left', padx=(0, 5))
        ttk.Button(button_frame, text="启动 Ollama", command=self.start_ollama).pack(side='left', padx=5)
        ttk.Button(button_frame, text="停止 Ollama", command=self.stop_ollama).pack(side='left', padx=5)
        ttk.Button(button_frame, text="检查更新", command=self.check_updates).pack(side='left', padx=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="日志", padding=10)
        log_frame.pack(fill='both', expand=True)
        
        # 创建文本框和滚动条
        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill='both', expand=True)
        
        self.log_text = tk.Text(text_frame, height=15, font=('Consolas', 9))
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 测试区域
        test_frame = ttk.LabelFrame(main_frame, text="快速测试", padding=10)
        test_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(test_frame, text="测试 API", command=self.test_api).pack(side='left', padx=(0, 5))
        ttk.Button(test_frame, text="列出模型", command=self.list_models).pack(side='left', padx=5)
        ttk.Button(test_frame, text="清空日志", command=self.clear_log).pack(side='left', padx=5)
        
    def log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def check_ollama_status(self):
        """检查 Ollama 状态"""
        def check():
            try:
                # 检查进程
                ollama_running = False
                for proc in psutil.process_iter(['pid', 'name', 'exe']):
                    if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                        ollama_running = True
                        if proc.info['exe']:
                            self.ollama_path = proc.info['exe']
                        break
                
                # 更新状态
                if ollama_running:
                    self.status_label.config(text="✅ Ollama 正在运行", foreground='green')
                else:
                    self.status_label.config(text="❌ Ollama 未运行", foreground='red')
                
                # 检查 ollama.exe 路径
                if not self.ollama_path:
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    possible_path = os.path.join(current_dir, "ollama.exe")
                    if os.path.exists(possible_path):
                        self.ollama_path = possible_path
                
                if self.ollama_path and os.path.exists(self.ollama_path):
                    self.path_label.config(text=f"路径: {self.ollama_path}")
                    
                    # 获取版本
                    try:
                        result = subprocess.run([self.ollama_path, "--version"], 
                                              capture_output=True, text=True, timeout=5)
                        if result.stdout:
                            import re
                            match = re.search(r'ollama version is ([0-9]+\.[0-9]+\.[0-9]+)', result.stdout)
                            if match:
                                self.current_version = match.group(1)
                                self.version_label.config(text=f"版本: {self.current_version}")
                    except:
                        pass
                else:
                    self.path_label.config(text="路径: 未找到 ollama.exe")
                
                self.log("状态检查完成")
                
            except Exception as e:
                self.log(f"状态检查出错: {str(e)}")
        
        threading.Thread(target=check, daemon=True).start()
        
    def start_ollama(self):
        """启动 Ollama"""
        if not self.ollama_path or not os.path.exists(self.ollama_path):
            messagebox.showerror("错误", "未找到 Ollama 程序")
            return
        
        def start():
            try:
                # 设置环境变量
                env = os.environ.copy()
                models_path = os.path.join(os.path.dirname(self.ollama_path), "models")
                env['OLLAMA_MODELS'] = models_path
                env['OLLAMA_HOST'] = "0.0.0.0"
                
                # 启动进程
                subprocess.Popen(
                    [self.ollama_path, "serve"],
                    env=env,
                    cwd=os.path.dirname(self.ollama_path)
                )
                
                self.log("Ollama 启动命令已发送")
                # 等待一会儿再检查状态
                self.root.after(3000, self.check_ollama_status)
                
            except Exception as e:
                self.log(f"启动失败: {str(e)}")
        
        threading.Thread(target=start, daemon=True).start()
        
    def stop_ollama(self):
        """停止 Ollama"""
        try:
            # 停止所有 ollama 进程
            killed = False
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                    proc.terminate()
                    killed = True
            
            if killed:
                self.log("Ollama 进程已停止")
            else:
                self.log("未找到运行中的 Ollama 进程")
            
            # 等待一会儿再检查状态
            self.root.after(2000, self.check_ollama_status)
            
        except Exception as e:
            self.log(f"停止失败: {str(e)}")
            
    def check_updates(self):
        """检查更新"""
        def check():
            try:
                self.log("正在检查更新...")
                
                response = requests.get("https://api.github.com/repos/ollama/ollama/releases/latest", timeout=10)
                data = response.json()
                
                self.latest_version = data['tag_name'].replace('v', '')
                
                if self.current_version:
                    if self.current_version == self.latest_version:
                        self.log(f"✅ 已是最新版本: {self.current_version}")
                    else:
                        self.log(f"🆕 发现新版本: {self.latest_version} (当前: {self.current_version})")
                else:
                    self.log(f"💾 最新版本: {self.latest_version}")
                
            except Exception as e:
                self.log(f"检查更新失败: {str(e)}")
        
        threading.Thread(target=check, daemon=True).start()
        
    def test_api(self):
        """测试 Ollama API"""
        def test():
            try:
                self.log("正在测试 API 连接...")
                
                response = requests.get("http://localhost:11434/api/version", timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    self.log(f"✅ API 测试成功，版本: {data.get('version', '未知')}")
                else:
                    self.log(f"❌ API 测试失败，状态码: {response.status_code}")
                    
            except Exception as e:
                self.log(f"❌ API 连接失败: {str(e)}")
        
        threading.Thread(target=test, daemon=True).start()
        
    def list_models(self):
        """列出模型"""
        def list_models():
            try:
                if not self.ollama_path:
                    self.log("❌ 未找到 Ollama 程序")
                    return
                
                self.log("正在获取模型列表...")
                
                result = subprocess.run([self.ollama_path, "list"], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.stdout:
                    lines = result.stdout.strip().split('\n')
                    self.log("📋 已安装的模型:")
                    for line in lines:
                        self.log(f"   {line}")
                else:
                    self.log("📋 暂无已安装的模型")
                    
            except Exception as e:
                self.log(f"获取模型列表失败: {str(e)}")
        
        threading.Thread(target=list_models, daemon=True).start()
        
    def clear_log(self):
        """清空日志"""
        self.log_text.delete('1.0', tk.END)
        self.log("日志已清空")
        
    def run(self):
        """运行应用"""
        self.log("=== Ollama Manager 测试版启动 ===")
        self.root.mainloop()

if __name__ == "__main__":
    # 检查依赖
    try:
        import psutil
        import requests
    except ImportError as e:
        print(f"缺少依赖: {e}")
        print("请运行: pip install psutil requests")
        input("按回车键退出...")
        exit(1)
    
    # 启动应用
    app = SimpleOllamaManager()
    app.run()
