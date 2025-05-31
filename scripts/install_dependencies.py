#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama Manager 依赖安装脚本
自动安装所需的 Python 模块
"""

import subprocess
import sys
import os

def install_package(package):
    """安装单个包"""
    try:
        print(f"正在安装 {package}...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", package], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✓ {package} 安装成功")
            return True
        else:
            print(f"✗ {package} 安装失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ {package} 安装出错: {str(e)}")
        return False

def main():
    print("=== Ollama Manager 依赖安装器 ===")
    print()
    
    # 必需的包
    required_packages = [
        "psutil",      # 进程管理
        "requests",    # HTTP 请求
        "pywin32",     # Windows API (可选，用于 WMI)
    ]
    
    # 可选的包
    optional_packages = [
        "WMI",         # 硬件信息检测 (Windows)
    ]
    
    print("检查必需的依赖包...")
    
    failed_packages = []
    
    # 安装必需包
    for package in required_packages:
        if not install_package(package):
            failed_packages.append(package)
    
    print()
    print("检查可选的依赖包...")
    
    # 安装可选包
    for package in optional_packages:
        try:
            install_package(package)
        except:
            print(f"可选包 {package} 安装失败，但不影响主要功能")
    
    print()
    print("=== 安装完成 ===")
    
    if failed_packages:
        print(f"警告: 以下包安装失败: {', '.join(failed_packages)}")
        print("某些功能可能无法正常工作")
    else:
        print("所有依赖包安装成功！")
    
    print()
    print("现在可以运行: python ollama_manager.py")
    
    input("按回车键退出...")

if __name__ == "__main__":
    main()
