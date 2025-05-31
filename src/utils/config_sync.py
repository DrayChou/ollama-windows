#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置同步管理器

负责在管理界面配置和 PowerShell 脚本配置之间进行同步：
- 读取和写入 PowerShell 脚本配置
- 检测配置差异
- 生成同步报告
- 双向同步功能
"""

import os
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class ConfigSyncManager:
    """
    配置同步管理器
    
    管理管理界面配置和 PowerShell 脚本配置之间的同步
    """
    
    def __init__(self, ps_script_path: str):
        """初始化配置同步管理器"""
        self.ps_script_path = Path(ps_script_path)
        
        # 支持的环境变量列表
        self.supported_env_vars = [
            "OLLAMA_HOST",
            "OLLAMA_PORT", 
            "OLLAMA_ORIGINS",
            "OLLAMA_MODELS",
            "OLLAMA_KEEP_ALIVE",
            "OLLAMA_DEBUG",
            "OLLAMA_FLASH_ATTENTION",
            "OLLAMA_LLM_LIBRARY",
            "OLLAMA_MAX_LOADED_MODELS",
            "OLLAMA_MAX_QUEUE",
            "OLLAMA_MAX_VRAM",
            "OLLAMA_NOHISTORY",
            "OLLAMA_NOPRUNE",
            "OLLAMA_NUM_PARALLEL",
            "OLLAMA_RUNNERS_DIR",
            "OLLAMA_SCHED_SPREAD",
            "OLLAMA_TMPDIR",
            "HSA_OVERRIDE_GFX_VERSION"
        ]
    
    def read_ps_script_config(self) -> Dict[str, str]:
        """
        从 PowerShell 脚本中读取配置
        
        Returns:
            Dict[str, str]: 环境变量配置字典
        """
        config = {}
        
        if not self.ps_script_path.exists():
            return config
        
        try:
            with open(self.ps_script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找环境变量设置模式
            # 匹配类似 $env:OLLAMA_HOST = "127.0.0.1:11434" 的模式
            # 使用简单的字符串处理替代复杂正则
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('$env:') and '=' in line:
                    try:
                        # 分割环境变量名和值
                        env_part, value_part = line.split('=', 1)
                        var_name = env_part.replace('$env:', '').strip()
                        # 移除引号
                        var_value = value_part.strip().strip('"\'')
                        if var_name in self.supported_env_vars and var_value:
                            config[var_name] = var_value
                    except ValueError:
                        continue
            
            # 查找写入批处理文件的模式
            # 匹配类似 "set OLLAMA_HOST=127.0.0.1:11434" >> "$batFile" 的模式
            # 使用简单的字符串处理替代正则
            for line in lines:
                line = line.strip()
                if line.startswith('"set ') and '=' in line and '>>"$batFile"' in line:
                    try:
                        # 提取set命令部分
                        set_part = line.split('>>')[0].strip().strip('"')
                        if set_part.startswith('set '):
                            # 分割变量名和值
                            var_part = set_part[4:]  # 移除'set '
                            if '=' in var_part:
                                var_name, var_value = var_part.split('=', 1)
                                var_name = var_name.strip()
                                var_value = var_value.strip()
                                if var_name in self.supported_env_vars and var_value:
                                    config[var_name] = var_value
                    except (ValueError, IndexError):
                        continue
            
            return config
            
        except Exception as e:
            print(f"读取 PowerShell 脚本配置失败: {e}")
            return config
    
    def write_ps_script_config(self, config: Dict[str, str]) -> bool:
        """
        将配置写入 PowerShell 脚本
        
        Args:
            config: 环境变量配置字典
            
        Returns:
            bool: 写入是否成功
        """
        try:
            # 读取现有脚本内容
            if self.ps_script_path.exists():
                with open(self.ps_script_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = self._get_default_script_template()
            
            # 更新脚本内容
            updated_content = self._update_script_content(content, config)
            
            # 写入更新后的内容
            with open(self.ps_script_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            return True
            
        except Exception as e:
            print(f"写入 PowerShell 脚本配置失败: {e}")
            return False
    
    def _update_script_content(self, content: str, config: Dict[str, str]) -> str:
        """
        更新脚本内容中的环境变量设置
        
        Args:
            content: 原始脚本内容
            config: 新的配置
            
        Returns:
            str: 更新后的脚本内容
        """
        lines = content.split('\n')
        updated_lines = []
        
        # 为每个支持的环境变量更新或添加设置
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            line_updated = False
            
            # 检查是否是环境变量设置行
            if line_stripped.startswith('$env:') and '=' in line_stripped:
                for var_name in self.supported_env_vars:
                    if line_stripped.startswith(f'$env:{var_name}') or line_stripped.startswith(f'# $env:{var_name}'):
                        var_value = config.get(var_name, "")
                        if var_value:
                            updated_lines.append(f'$env:{var_name} = "{var_value}"')
                        else:
                            updated_lines.append(f'# $env:{var_name} = ""')
                        line_updated = True
                        break
            
            # 检查是否是批处理文件写入行
            elif '"set ' in line_stripped and '>>' in line_stripped and '$batFile' in line_stripped:
                for var_name in self.supported_env_vars:
                    if f'set {var_name}=' in line_stripped or f'# "set {var_name}=' in line_stripped:
                        var_value = config.get(var_name, "")
                        if var_value:
                            updated_lines.append(f'"set {var_name}={var_value}" >> "$batFile"')
                        else:
                            updated_lines.append(f'# "set {var_name}=" >> "$batFile"')
                        line_updated = True
                        break
            
            if not line_updated:
                updated_lines.append(line)
        
        # 检查是否有新的环境变量需要添加
        existing_vars = set()
        for line in updated_lines:
            line_stripped = line.strip()
            if line_stripped.startswith('$env:') or line_stripped.startswith('# $env:'):
                for var_name in self.supported_env_vars:
                    if f'$env:{var_name}' in line_stripped:
                        existing_vars.add(var_name)
                        break
        
        # 添加缺失的环境变量
        for var_name in self.supported_env_vars:
            if var_name not in existing_vars and var_name in config and config[var_name]:
                # 在环境变量设置区域添加
                env_section_found = False
                for i, line in enumerate(updated_lines):
                    if '# 设置环境变量' in line:
                        # 在此区域后添加新变量
                        updated_lines.insert(i + 1, f'$env:{var_name} = "{config[var_name]}"')
                        env_section_found = True
                        break
                
                if not env_section_found:
                    # 如果没找到环境变量区域，在开头添加
                    updated_lines.insert(0, f'$env:{var_name} = "{config[var_name]}"')
                
                # 在批处理文件区域添加对应的写入命令
                bat_section_found = False
                for i, line in enumerate(updated_lines):
                    if '# 写入环境变量到批处理文件' in line:
                        updated_lines.insert(i + 1, f'"set {var_name}={config[var_name]}" >> "$batFile"')
                        bat_section_found = True
                        break
                
                if not bat_section_found:
                    # 如果没找到批处理区域，在末尾添加
                    updated_lines.append(f'"set {var_name}={config[var_name]}" >> "$batFile"')
        
        return '\n'.join(updated_lines)
    
    def _add_env_var_to_script(self, content: str, var_name: str, env_line: str) -> str:
        """
        在脚本中添加新的环境变量设置
        """
        # 查找环境变量设置区域
        env_section_pattern = r'(# 设置环境变量.*?\n)(.*?)(\n# 创建批处理文件)'
        match = re.search(env_section_pattern, content, re.DOTALL)
        
        if match:
            before = match.group(1)
            env_vars = match.group(2)
            after = match.group(3)
            
            # 在环境变量区域末尾添加新变量
            new_env_vars = env_vars.rstrip() + f'\n{env_line}'
            return before + new_env_vars + after
        else:
            # 如果找不到特定区域，在文件开头添加
            return f'{env_line}\n{content}'
    
    def _add_bat_var_to_script(self, content: str, var_name: str, bat_line: str) -> str:
        """
        在脚本中添加新的批处理文件变量写入
        """
        # 查找批处理文件写入区域
        bat_section_pattern = r'(# 写入环境变量到批处理文件.*?\n)(.*?)(\n# 启动 Ollama)'
        match = re.search(bat_section_pattern, content, re.DOTALL)
        
        if match:
            before = match.group(1)
            bat_vars = match.group(2)
            after = match.group(3)
            
            # 在批处理变量区域末尾添加新变量
            new_bat_vars = bat_vars.rstrip() + f'\n{bat_line}'
            return before + new_bat_vars + after
        else:
            # 如果找不到特定区域，在文件末尾添加
            return f'{content}\n{bat_line}'
    
    def _get_default_script_template(self) -> str:
        """
        获取默认的 PowerShell 脚本模板
        """
        return '''# Ollama 启动脚本
# 自动生成，请勿手动编辑

# 设置环境变量
$env:OLLAMA_HOST = "127.0.0.1:11434"
$env:OLLAMA_PORT = "11434"

# 创建批处理文件
$batFile = "ollama_env.bat"
if (Test-Path $batFile) {
    Remove-Item $batFile
}

# 写入环境变量到批处理文件
"set OLLAMA_HOST=127.0.0.1:11434" >> "$batFile"
"set OLLAMA_PORT=11434" >> "$batFile"

# 启动 Ollama
Start-Process -FilePath "ollama" -ArgumentList "serve" -NoNewWindow
'''
    
    def sync_ui_to_ps(self, ui_config: Dict[str, str]) -> bool:
        """
        将管理界面配置同步到 PowerShell 脚本
        
        Args:
            ui_config: 管理界面的配置
            
        Returns:
            bool: 同步是否成功
        """
        return self.write_ps_script_config(ui_config)
    
    def sync_ps_to_ui(self) -> Dict[str, str]:
        """
        将 PowerShell 脚本配置同步到管理界面
        
        Returns:
            Dict[str, str]: PowerShell 脚本中的配置
        """
        return self.read_ps_script_config()
    
    def detect_config_differences(self, ui_config: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        """
        检测管理界面配置和 PowerShell 脚本配置之间的差异
        
        Args:
            ui_config: 管理界面的配置
            
        Returns:
            Dict: 包含差异信息的字典
        """
        ps_config = self.read_ps_script_config()
        differences = {
            'ui_only': {},      # 只在管理界面中存在的配置
            'ps_only': {},      # 只在 PowerShell 脚本中存在的配置
            'different': {},    # 两边都存在但值不同的配置
            'same': {}          # 两边相同的配置
        }
        
        # 检查所有支持的环境变量
        for var_name in self.supported_env_vars:
            ui_value = ui_config.get(var_name, "")
            ps_value = ps_config.get(var_name, "")
            
            if ui_value and ps_value:
                if ui_value == ps_value:
                    differences['same'][var_name] = ui_value
                else:
                    differences['different'][var_name] = {
                        'ui': ui_value,
                        'ps': ps_value
                    }
            elif ui_value and not ps_value:
                differences['ui_only'][var_name] = ui_value
            elif ps_value and not ui_value:
                differences['ps_only'][var_name] = ps_value
        
        return differences
    
    def _get_system_env_config(self) -> Dict[str, str]:
        """
        获取系统环境变量中的 Ollama 配置
        
        Returns:
            Dict[str, str]: 系统环境变量配置
        """
        system_config = {}
        
        for var_name in self.supported_env_vars:
            value = os.environ.get(var_name)
            if value:
                system_config[var_name] = value
        
        return system_config
    
    def generate_sync_report(self, ui_config: Dict[str, str]) -> str:
        """
        生成配置同步报告
        
        Args:
            ui_config: 管理界面的配置
            
        Returns:
            str: 同步报告文本
        """
        ps_config = self.read_ps_script_config()
        system_config = self._get_system_env_config()
        differences = self.detect_config_differences(ui_config)
        
        report_lines = [
            "=== Ollama 配置同步报告 ===",
            f"PowerShell 脚本: {self.ps_script_path}",
            f"生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "=== 配置概览 ===",
            f"管理界面配置项: {len([k for k, v in ui_config.items() if v])}",
            f"PowerShell 脚本配置项: {len(ps_config)}",
            f"系统环境变量配置项: {len(system_config)}",
            ""
        ]
        
        # 相同配置
        if differences['same']:
            report_lines.extend([
                "=== 相同配置 ===",
                *[f"  {var}: {value}" for var, value in differences['same'].items()],
                ""
            ])
        
        # 不同配置
        if differences['different']:
            report_lines.extend([
                "=== 配置差异 ===",
                *[f"  {var}:\n    管理界面: {info['ui']}\n    PowerShell: {info['ps']}" 
                  for var, info in differences['different'].items()],
                ""
            ])
        
        # 仅在管理界面的配置
        if differences['ui_only']:
            report_lines.extend([
                "=== 仅在管理界面的配置 ===",
                *[f"  {var}: {value}" for var, value in differences['ui_only'].items()],
                ""
            ])
        
        # 仅在 PowerShell 脚本的配置
        if differences['ps_only']:
            report_lines.extend([
                "=== 仅在 PowerShell 脚本的配置 ===",
                *[f"  {var}: {value}" for var, value in differences['ps_only'].items()],
                ""
            ])
        
        # 系统环境变量
        if system_config:
            report_lines.extend([
                "=== 系统环境变量 ===",
                *[f"  {var}: {value}" for var, value in system_config.items()],
                ""
            ])
        
        # 同步建议
        report_lines.extend([
            "=== 同步建议 ==="
        ])
        
        if differences['different'] or differences['ui_only'] or differences['ps_only']:
            if differences['ui_only']:
                report_lines.append("  - 建议将管理界面的配置同步到 PowerShell 脚本")
            if differences['ps_only']:
                report_lines.append("  - 建议将 PowerShell 脚本的配置同步到管理界面")
            if differences['different']:
                report_lines.append("  - 存在配置冲突，请手动确认正确的配置值")
        else:
            report_lines.append("  - 配置已同步，无需操作")
        
        return "\n".join(report_lines)