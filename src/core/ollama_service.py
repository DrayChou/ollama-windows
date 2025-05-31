#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama 服务管理模块

负责管理 Ollama 服务的所有操作：
- 服务启动/停止/重启
- 状态监控
- 版本检查和更新
- 模型管理
- 硬件信息检测
"""

import os
import sys
import json
import time
import psutil
import requests
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime


class OllamaService:
    """
    Ollama 服务管理器
    
    提供完整的 Ollama 服务管理功能
    """
    
    def __init__(self, config_manager, logger):
        """初始化服务管理器"""
        self.config_manager = config_manager
        self.logger = logger
        self.process = None
        self.is_running = False
        self.version = ""
        self.models = []
        self.hardware_info = {}
        
        # API 配置
        self.api_base = "http://127.0.0.1:11434"
        self.github_api = "https://api.github.com/repos/ollama/ollama/releases/latest"
        
        # 状态回调
        self.status_callbacks = []
        self.model_callbacks = []
    
    def add_status_callback(self, callback: Callable) -> None:
        """添加状态变化回调"""
        self.status_callbacks.append(callback)
    
    def add_model_callback(self, callback: Callable) -> None:
        """添加模型变化回调"""
        self.model_callbacks.append(callback)
    
    def _notify_status_change(self) -> None:
        """通知状态变化"""
        for callback in self.status_callbacks:
            try:
                callback(self.is_running, self.version)
            except Exception as e:
                self.logger.error(f"状态回调执行失败: {e}")
    
    def _notify_model_change(self) -> None:
        """通知模型变化"""
        for callback in self.model_callbacks:
            try:
                callback(self.models)
            except Exception as e:
                self.logger.error(f"模型回调执行失败: {e}")
    
    def check_status(self) -> bool:
        """检查 Ollama 服务状态"""
        try:
            # 优先通过 API 检查状态
            api_running = self._check_api_status()
            
            if api_running:
                self.is_running = True
                # 如果 API 可用，尝试找到对应的进程
                self._find_process()
            else:
                # API 不可用时，检查进程是否存在
                process_running = self._check_process_status()
                self.is_running = process_running
                if not process_running:
                    self.process = None
                    self.version = ""
            
            self._notify_status_change()
            return self.is_running
            
        except Exception as e:
            self.logger.error(f"检查状态失败: {e}")
            self.is_running = False
            return False
    
    def _check_api_status(self) -> bool:
        """通过 API 检查服务状态"""
        try:
            response = requests.get(f"{self.api_base}/api/version", timeout=3)
            if response.status_code == 200:
                data = response.json()
                self.version = data.get('version', 'Unknown')
                return True
        except (requests.RequestException, requests.Timeout):
            pass
        return False
    
    def _check_process_status(self) -> bool:
        """检查进程状态"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'ollama' in proc.info['name'].lower():
                        if 'serve' in ' '.join(proc.info['cmdline'] or []):
                            self.process = proc
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        return False
    
    def _find_process(self) -> None:
        """查找 Ollama 进程"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'ollama' in proc.info['name'].lower():
                        if 'serve' in ' '.join(proc.info['cmdline'] or []):
                            self.process = proc
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
    
    def _get_version(self) -> None:
        """获取 Ollama 版本信息"""
        try:
            response = requests.get(f"{self.api_base}/api/version", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.version = data.get('version', 'Unknown')
            else:
                # 尝试命令行方式
                ollama_path = self.config_manager.get_ollama_path()
                if ollama_path and os.path.exists(ollama_path):
                    result = subprocess.run(
                        [ollama_path, '--version'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        self.version = result.stdout.strip()
        except Exception as e:
            self.logger.debug(f"获取版本信息失败: {e}")
            self.version = "Unknown"
    
    def start(self, callback: Optional[Callable] = None) -> bool:
        """启动 Ollama 服务"""
        if self.is_running:
            self.logger.info("Ollama 服务已在运行")
            return True
        
        ollama_path = self.config_manager.get_ollama_path()
        if not ollama_path or not os.path.exists(ollama_path):
            self.logger.info("Ollama 程序路径未配置，尝试自动检测...")
            # 尝试重新检测路径
            self.config_manager._auto_detect_paths()
            ollama_path = self.config_manager.get_ollama_path()
            
            if not ollama_path or not os.path.exists(ollama_path):
                self.logger.error("Ollama 程序路径未配置或不存在，请手动配置或下载 Ollama")
                return False
        
        try:
            # 应用环境变量
            self.config_manager.apply_environment_variables()
            
            # 启动服务
            self.logger.info("正在启动 Ollama 服务...")
            
            # 使用 subprocess.Popen 启动服务
            env = os.environ.copy()
            env.update(self.config_manager.get_environment_variables())
            
            self.process = subprocess.Popen(
                [ollama_path, 'serve'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            # 等待服务启动
            for i in range(30):  # 最多等待30秒
                time.sleep(1)
                if self.check_status():
                    self.logger.info("Ollama 服务启动成功")
                    if callback:
                        callback(True, "服务启动成功")
                    return True
            
            self.logger.error("Ollama 服务启动超时")
            if callback:
                callback(False, "服务启动超时")
            return False
            
        except Exception as e:
            self.logger.error(f"启动 Ollama 服务失败: {e}")
            if callback:
                callback(False, f"启动失败: {e}")
            return False
    
    def stop(self, callback: Optional[Callable] = None) -> bool:
        """停止 Ollama 服务"""
        if not self.is_running:
            self.logger.info("Ollama 服务未运行")
            return True
        
        try:
            self.logger.info("正在停止 Ollama 服务...")
            
            # 尝试优雅关闭
            if self.process:
                self.process.terminate()
                
                # 等待进程结束
                for i in range(10):
                    if not self.check_status():
                        self.logger.info("Ollama 服务已停止")
                        if callback:
                            callback(True, "服务已停止")
                        return True
                    time.sleep(1)
                
                # 强制结束
                self.process.kill()
            
            # 查找并结束所有 ollama 进程
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'ollama' in proc.info['name'].lower():
                        proc.terminate()
                        proc.wait(timeout=5)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                    try:
                        proc.kill()
                    except:
                        pass
            
            self.is_running = False
            self.process = None
            self._notify_status_change()
            
            self.logger.info("Ollama 服务已停止")
            if callback:
                callback(True, "服务已停止")
            return True
            
        except Exception as e:
            self.logger.error(f"停止 Ollama 服务失败: {e}")
            if callback:
                callback(False, f"停止失败: {e}")
            return False
    
    def restart(self, callback: Optional[Callable] = None) -> bool:
        """重启 Ollama 服务"""
        self.logger.info("正在重启 Ollama 服务...")
        
        def restart_callback(success, message):
            if callback:
                callback(success, f"重启{'成功' if success else '失败'}: {message}")
        
        # 先停止
        if not self.stop():
            if callback:
                callback(False, "重启失败: 无法停止服务")
            return False
        
        # 等待一下
        time.sleep(2)
        
        # 再启动
        return self.start(restart_callback)
    
    def get_models(self) -> List[Dict]:
        """获取已安装的模型列表"""
        try:
            response = requests.get(f"{self.api_base}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.models = data.get('models', [])
                self._notify_model_change()
                return self.models
        except Exception as e:
            self.logger.error(f"获取模型列表失败: {e}")
        
        return []
    
    def pull_model(self, model_name: str, progress_callback: Optional[Callable] = None) -> bool:
        """下载模型"""
        try:
            self.logger.info(f"开始下载模型: {model_name}")
            
            # 发送下载请求
            response = requests.post(
                f"{self.api_base}/api/pull",
                json={"name": model_name},
                stream=True,
                timeout=3600  # 1小时超时
            )
            
            if response.status_code != 200:
                self.logger.error(f"下载模型失败: HTTP {response.status_code}")
                return False
            
            # 处理流式响应
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if progress_callback:
                            progress_callback(data)
                        
                        # 检查是否完成
                        if data.get('status') == 'success':
                            self.logger.info(f"模型 {model_name} 下载完成")
                            self.get_models()  # 刷新模型列表
                            return True
                        
                        # 检查错误
                        if 'error' in data:
                            self.logger.error(f"下载模型失败: {data['error']}")
                            return False
                            
                    except json.JSONDecodeError:
                        continue
            
            return True
            
        except Exception as e:
            self.logger.error(f"下载模型失败: {e}")
            return False
    
    def delete_model(self, model_name: str) -> bool:
        """删除模型"""
        try:
            self.logger.info(f"删除模型: {model_name}")
            
            response = requests.delete(
                f"{self.api_base}/api/delete",
                json={"name": model_name},
                timeout=30
            )
            
            if response.status_code == 200:
                self.logger.info(f"模型 {model_name} 删除成功")
                self.get_models()  # 刷新模型列表
                return True
            else:
                self.logger.error(f"删除模型失败: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"删除模型失败: {e}")
            return False
    
    def chat(self, model: str, messages: List[Dict], stream: bool = True) -> requests.Response:
        """与模型对话"""
        try:
            response = requests.post(
                f"{self.api_base}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": stream
                },
                stream=stream,
                timeout=300
            )
            return response
        except Exception as e:
            self.logger.error(f"对话请求失败: {e}")
            raise
    
    def check_for_updates(self) -> Optional[Dict]:
        """检查更新"""
        try:
            response = requests.get(self.github_api, timeout=10)
            if response.status_code == 200:
                release_info = response.json()
                latest_version = release_info.get('tag_name', '').lstrip('v')
                current_version = self.version.lstrip('v')
                
                if latest_version and current_version:
                    # 简单的版本比较
                    if latest_version != current_version:
                        return {
                            'has_update': True,
                            'latest_version': latest_version,
                            'current_version': current_version,
                            'download_url': self._get_download_url(release_info),
                            'release_notes': release_info.get('body', '')
                        }
                
                return {'has_update': False}
                
        except Exception as e:
            self.logger.error(f"检查更新失败: {e}")
            return None
    
    def _get_download_url(self, release_info: Dict) -> str:
        """获取适合当前系统的下载链接"""
        assets = release_info.get('assets', [])
        
        # Windows 系统查找 .exe 文件
        for asset in assets:
            name = asset.get('name', '').lower()
            if 'windows' in name and name.endswith('.exe'):
                return asset.get('browser_download_url', '')
        
        return release_info.get('html_url', '')
    
    def get_hardware_info(self) -> Dict:
        """获取硬件信息"""
        try:
            import wmi
            
            hardware_info = {
                'cpu': {},
                'memory': {},
                'gpu': []
            }
            
            # CPU 信息
            cpu_info = psutil.cpu_freq()
            hardware_info['cpu'] = {
                'name': 'Unknown',
                'cores': psutil.cpu_count(logical=False),
                'threads': psutil.cpu_count(logical=True),
                'frequency': f"{cpu_info.current:.0f} MHz" if cpu_info else "Unknown"
            }
            
            # 内存信息
            memory = psutil.virtual_memory()
            hardware_info['memory'] = {
                'total': f"{memory.total / (1024**3):.1f} GB",
                'available': f"{memory.available / (1024**3):.1f} GB",
                'usage': f"{memory.percent}%"
            }
            
            # GPU 信息（使用 WMI）
            wmi_success = False
            try:
                c = wmi.WMI()
                gpu_list = []
                for gpu in c.Win32_VideoController():
                    if gpu.Name and 'Basic' not in gpu.Name and 'Generic' not in gpu.Name:
                        gpu_info = {
                            'name': gpu.Name,
                            'memory': 'Unknown',
                            'driver': gpu.DriverVersion or 'Unknown',
                            'cuda_support': 'NVIDIA' in gpu.Name.upper(),
                            'opencl_support': True  # 大多数现代GPU都支持
                        }
                        
                        # 尝试获取显存信息（修复负数问题）
                        memory_detected = False
                        if gpu.AdapterRAM and gpu.AdapterRAM > 0:
                            gpu_info['memory'] = f"{gpu.AdapterRAM / (1024**3):.1f} GB"
                            memory_detected = True
                        
                        # 如果WMI无法获取显存信息，标记为需要使用PowerShell
                        if not memory_detected:
                            gpu_info['memory'] = "Unknown (检测失败)"
                        
                        # 添加GPU类型检测
                        if 'NVIDIA' in gpu.Name.upper():
                            gpu_info['type'] = 'NVIDIA'
                            gpu_info['ollama_support'] = 'CUDA支持'
                        elif 'AMD' in gpu.Name.upper() or 'Radeon' in gpu.Name.upper():
                            gpu_info['type'] = 'AMD'
                            if 'Graphics' in gpu.Name or 'APU' in gpu.Name:
                                gpu_info['ollama_support'] = 'ROCm支持（集成显卡可能需要特殊配置）'
                            else:
                                gpu_info['ollama_support'] = 'ROCm支持'
                        elif 'Intel' in gpu.Name.upper():
                            gpu_info['type'] = 'Intel'
                            gpu_info['ollama_support'] = '通常不支持GPU加速'
                        else:
                            gpu_info['type'] = 'Unknown'
                            gpu_info['ollama_support'] = '未知'
                        
                        gpu_list.append(gpu_info)
                
                # 检查是否有任何GPU的显存信息获取失败
                has_memory_failure = any(gpu['memory'] == "Unknown (检测失败)" for gpu in gpu_list)
                
                if has_memory_failure:
                    # 如果有显存检测失败，使用PowerShell方法重新获取
                    self.logger.debug("WMI显存检测部分失败，使用PowerShell方法重新获取GPU信息")
                    hardware_info['gpu'] = self._get_gpu_info_via_powershell()
                else:
                    hardware_info['gpu'] = gpu_list
                    wmi_success = True
                    
            except Exception as e:
                self.logger.debug(f"获取GPU信息失败: {e}")
                # 如果WMI完全失败，尝试使用PowerShell获取GPU信息
                hardware_info['gpu'] = self._get_gpu_info_via_powershell()
            
            self.hardware_info = hardware_info
            return hardware_info
            
        except ImportError:
            self.logger.warning("WMI 模块未安装，无法获取详细硬件信息")
            return self._get_basic_hardware_info()
        except Exception as e:
            self.logger.error(f"获取硬件信息失败: {e}")
            return self._get_basic_hardware_info()
    
    def _get_gpu_info_via_powershell(self) -> List[Dict]:
        """通过PowerShell获取GPU信息"""
        try:
            import subprocess
            
            # 首先尝试使用nvidia-smi获取NVIDIA GPU信息
            nvidia_gpus = []
            try:
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader,nounits'],
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            parts = [p.strip() for p in line.split(',')]
                            if len(parts) >= 3:
                                name = parts[0]
                                memory_mb = int(parts[1])
                                memory_gb = round(memory_mb / 1024, 2)
                                driver = parts[2]
                                
                                gpu_info = {
                                    'name': name,
                                    'memory': f"{memory_gb} GB",
                                    'driver': driver,
                                    'type': 'NVIDIA',
                                    'cuda_support': True,
                                    'opencl_support': True,
                                    'ollama_support': 'CUDA支持'
                                }
                                nvidia_gpus.append(gpu_info)
            except Exception as e:
                self.logger.debug(f"nvidia-smi获取失败: {e}")
            
            # PowerShell命令获取所有GPU信息（包括非NVIDIA）
            ps_command = '''
            Get-WmiObject -Class Win32_VideoController | Where-Object { $_.Name -notlike "*Basic*" -and $_.Name -notlike "*Generic*" } | ForEach-Object {
                $dedicatedMemory = 0
                $totalMemory = 0
                
                # 尝试获取专用显存
                if ($_.AdapterRAM -and $_.AdapterRAM -gt 0) {
                    $dedicatedMemory = [math]::Round($_.AdapterRAM / 1GB, 2)
                    $totalMemory = $dedicatedMemory
                }
                
                Write-Output "$($_.Name)|$totalMemory|$($_.DriverVersion)|$dedicatedMemory"
            }
            '''
            
            result = subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            gpu_list = []
            
            # 添加nvidia-smi检测到的GPU
            gpu_list.extend(nvidia_gpus)
            
            # 处理PowerShell检测到的GPU
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split('|')
                        if len(parts) >= 3:
                            name = parts[0]
                            total_memory = parts[1] if parts[1] != '0' else 'Unknown'
                            driver = parts[2] if parts[2] else 'Unknown'
                            dedicated_memory = parts[3] if len(parts) > 3 and parts[3] != '0' else None
                            
                            # 检查是否已经通过nvidia-smi添加了这个GPU
                            already_added = False
                            for existing_gpu in gpu_list:
                                if existing_gpu['name'] == name:
                                    already_added = True
                                    break
                            
                            if not already_added:
                                # 构建显存信息字符串
                                memory_info = 'Unknown'
                                if total_memory != 'Unknown':
                                    memory_info = f"{total_memory} GB"
                                    if dedicated_memory and float(dedicated_memory) != float(total_memory):
                                        shared_memory = float(total_memory) - float(dedicated_memory)
                                        if shared_memory > 0:
                                            memory_info += f" (专用: {dedicated_memory} GB, 共享: {shared_memory:.1f} GB)"
                                
                                gpu_info = {
                                    'name': name,
                                    'memory': memory_info,
                                    'driver': driver,
                                    'cuda_support': 'NVIDIA' in name.upper(),
                                    'opencl_support': True
                                }
                                
                                # 添加GPU类型检测
                                if 'NVIDIA' in name.upper():
                                    gpu_info['type'] = 'NVIDIA'
                                    gpu_info['ollama_support'] = 'CUDA支持'
                                elif 'AMD' in name.upper() or 'Radeon' in name.upper():
                                    gpu_info['type'] = 'AMD'
                                    if 'Graphics' in name or 'APU' in name:
                                        gpu_info['ollama_support'] = 'ROCm支持（集成显卡可能需要特殊配置）'
                                    else:
                                        gpu_info['ollama_support'] = 'ROCm支持'
                                elif 'Intel' in name.upper():
                                    gpu_info['type'] = 'Intel'
                                    gpu_info['ollama_support'] = '通常不支持GPU加速'
                                else:
                                    gpu_info['type'] = 'Unknown'
                                    gpu_info['ollama_support'] = '未知'
                                
                                gpu_list.append(gpu_info)
            
            return gpu_list
            
        except Exception as e:
            self.logger.error(f"通过PowerShell获取GPU信息失败: {e}")
            return []
    
    def _get_basic_hardware_info(self) -> Dict:
        """获取基础硬件信息（不依赖WMI）"""
        try:
            hardware_info = {
                'cpu': {
                    'cores': psutil.cpu_count(logical=False),
                    'threads': psutil.cpu_count(logical=True)
                },
                'memory': {},
                'gpu': []
            }
            
            # 内存信息
            memory = psutil.virtual_memory()
            hardware_info['memory'] = {
                'total': f"{memory.total / (1024**3):.1f} GB",
                'available': f"{memory.available / (1024**3):.1f} GB",
                'usage': f"{memory.percent}%"
            }
            
            # 尝试通过PowerShell获取GPU信息
            hardware_info['gpu'] = self._get_gpu_info_via_powershell()
            
            return hardware_info
        except Exception as e:
            self.logger.error(f"获取基础硬件信息失败: {e}")
            return {
                'cpu': {'cores': 'Unknown', 'threads': 'Unknown'},
                'memory': {'total': 'Unknown', 'available': 'Unknown', 'usage': 'Unknown'},
                'gpu': []
            }