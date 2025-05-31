#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器模块

负责管理 Ollama 的所有配置，包括：
- 程序路径配置
- 环境变量管理
- 用户偏好设置
- 配置文件的读取和保存
"""

import os
import json
import winreg
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """
    配置管理器
    
    管理所有与配置相关的操作，包括路径、环境变量、用户设置等
    """
    
    def __init__(self, config_file: str = "ollama_config.json"):
        """初始化配置管理器"""
        self.config_file = Path(config_file)
        self.config = self._load_default_config()
        self.load_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        return {
            "ollama_path": "",
            "model_path": "",
            "environment_variables": {
                "OLLAMA_HOST": "127.0.0.1:11434",
                "OLLAMA_MODELS": "",
                "OLLAMA_KEEP_ALIVE": "5m",
                "OLLAMA_NUM_PARALLEL": "1",
                "OLLAMA_MAX_LOADED_MODELS": "1",
                "OLLAMA_FLASH_ATTENTION": "1"
            },
            "ui_settings": {
                "window_width": 1000,
                "window_height": 700,
                "theme": "default",
                "auto_refresh": True,
                "refresh_interval": 5000
            },
            "advanced_settings": {
                "auto_start": False,
                "minimize_to_tray": False,
                "check_updates": True,
                "log_level": "INFO",
                "max_log_size": 10485760  # 10MB
            }
        }
    
    def load_config(self) -> bool:
        """从文件加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并配置，保留默认值
                    self._merge_config(self.config, loaded_config)
                return True
        except Exception as e:
            print(f"加载配置文件失败: {e}")
        
        # 如果加载失败，尝试自动检测路径
        self._auto_detect_paths()
        return False
    
    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def _merge_config(self, default: Dict, loaded: Dict) -> None:
        """递归合并配置"""
        for key, value in loaded.items():
            if key in default:
                if isinstance(default[key], dict) and isinstance(value, dict):
                    self._merge_config(default[key], value)
                else:
                    default[key] = value
    
    def _auto_detect_paths(self) -> None:
        """自动检测 Ollama 路径"""
        # 检测 Ollama 程序路径
        possible_paths = [
            # 首先检查当前目录
            os.path.join(os.getcwd(), "ollama.exe"),
            # 然后检查脚本所在目录
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ollama.exe"),
            # 系统安装路径
            r"C:\Users\{username}\AppData\Local\Programs\Ollama\ollama.exe",
            r"C:\Program Files\Ollama\ollama.exe",
            r"C:\Program Files (x86)\Ollama\ollama.exe"
        ]
        
        username = os.getenv('USERNAME', '')
        for path_template in possible_paths:
            if '{username}' in path_template:
                path = path_template.format(username=username)
            else:
                path = os.path.abspath(path_template)
            
            if os.path.exists(path):
                self.config["ollama_path"] = path
                print(f"自动检测到 Ollama 路径: {path}")
                break
        
        # 检测模型路径 - 优先读取环境变量 OLLAMA_MODELS
        env_model_path = os.environ.get("OLLAMA_MODELS", "")
        if env_model_path and os.path.exists(env_model_path):
            self.config["model_path"] = env_model_path
            self.config["environment_variables"]["OLLAMA_MODELS"] = env_model_path
        else:
            # 如果环境变量未设置或路径不存在，使用默认路径
            default_model_path = os.path.expanduser("~/.ollama/models")
            if os.path.exists(default_model_path):
                self.config["model_path"] = default_model_path
                self.config["environment_variables"]["OLLAMA_MODELS"] = default_model_path
            elif env_model_path:
                # 如果环境变量设置了但路径不存在，仍然使用环境变量的值
                self.config["model_path"] = env_model_path
                self.config["environment_variables"]["OLLAMA_MODELS"] = env_model_path
    
    def get_ollama_path(self) -> str:
        """获取 Ollama 程序路径"""
        return self.config.get("ollama_path", "")
    
    def set_ollama_path(self, path: str) -> None:
        """设置 Ollama 程序路径"""
        self.config["ollama_path"] = path
    
    def get_model_path(self) -> str:
        """获取模型存储路径"""
        return self.config.get("model_path", "")
    
    def set_model_path(self, path: str) -> None:
        """设置模型存储路径"""
        self.config["model_path"] = path
        self.config["environment_variables"]["OLLAMA_MODELS"] = path
    
    def get_environment_variables(self) -> Dict[str, str]:
        """获取环境变量配置"""
        return self.config.get("environment_variables", {})
    
    def set_environment_variable(self, key: str, value: str) -> None:
        """设置环境变量"""
        if "environment_variables" not in self.config:
            self.config["environment_variables"] = {}
        self.config["environment_variables"][key] = value
    
    def get_ui_setting(self, key: str, default: Any = None) -> Any:
        """获取 UI 设置"""
        return self.config.get("ui_settings", {}).get(key, default)
    
    def set_ui_setting(self, key: str, value: Any) -> None:
        """设置 UI 设置"""
        if "ui_settings" not in self.config:
            self.config["ui_settings"] = {}
        self.config["ui_settings"][key] = value
    
    def get_advanced_setting(self, key: str, default: Any = None) -> Any:
        """获取高级设置"""
        return self.config.get("advanced_settings", {}).get(key, default)
    
    def set_advanced_setting(self, key: str, value: Any) -> None:
        """设置高级设置"""
        if "advanced_settings" not in self.config:
            self.config["advanced_settings"] = {}
        self.config["advanced_settings"][key] = value
    
    def apply_environment_variables(self) -> None:
        """应用环境变量到系统"""
        env_vars = self.get_environment_variables()
        for key, value in env_vars.items():
            if value:  # 只设置非空值
                os.environ[key] = value
    
    def get_registry_value(self, key_path: str, value_name: str) -> Optional[str]:
        """从注册表读取值"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                value, _ = winreg.QueryValueEx(key, value_name)
                return value
        except (FileNotFoundError, OSError):
            return None
    
    def set_registry_value(self, key_path: str, value_name: str, value: str) -> bool:
        """设置注册表值"""
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, value)
            return True
        except OSError as e:
            print(f"设置注册表失败: {e}")
            return False
    
    def export_config(self, file_path: str) -> bool:
        """导出配置到指定文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """从指定文件导入配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
                self._merge_config(self.config, imported_config)
            return True
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False
    
    def reset_to_defaults(self) -> None:
        """重置为默认配置"""
        self.config = self._load_default_config()
        self._auto_detect_paths()
    
    def validate_config(self) -> Dict[str, str]:
        """验证配置的有效性"""
        errors = {}
        
        # 验证 Ollama 路径
        ollama_path = self.get_ollama_path()
        if ollama_path and not os.path.exists(ollama_path):
            errors["ollama_path"] = "Ollama 程序路径不存在"
        
        # 验证模型路径
        model_path = self.get_model_path()
        if model_path and not os.path.exists(model_path):
            errors["model_path"] = "模型存储路径不存在"
        
        # 验证环境变量
        env_vars = self.get_environment_variables()
        if "OLLAMA_HOST" in env_vars:
            host = env_vars["OLLAMA_HOST"]
            if not host or ":" not in host:
                errors["OLLAMA_HOST"] = "主机地址格式不正确"
        
        return errors