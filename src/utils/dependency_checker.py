#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖检查器模块

检查和管理项目所需的依赖包：
- 检查必需的 Python 包
- 提供安装建议
- 版本兼容性检查
"""

import sys
import importlib
import subprocess
from typing import List, Dict, Tuple, Optional


# 必需的依赖包及其最低版本要求
REQUIRED_PACKAGES = {
    'tkinter': None,  # 内置模块
    'psutil': '5.8.0',
    'requests': '2.25.0',
    'pywin32': '227',  # Windows 特定
}

# 可选的依赖包
OPTIONAL_PACKAGES = {
    'wmi': '1.5.1',  # 用于硬件信息检测
    'pillow': '8.0.0',  # 用于图像处理
    'matplotlib': '3.3.0',  # 用于图表显示
}


def check_dependencies() -> List[str]:
    """
    检查所有必需的依赖包
    
    Returns:
        List[str]: 缺失的包名列表
    """
    missing_packages = []
    
    for package, min_version in REQUIRED_PACKAGES.items():
        if not is_package_available(package, min_version):
            missing_packages.append(package)
    
    return missing_packages


def check_optional_dependencies() -> Dict[str, bool]:
    """
    检查可选依赖包的可用性
    
    Returns:
        Dict[str, bool]: 包名到可用性的映射
    """
    optional_status = {}
    
    for package, min_version in OPTIONAL_PACKAGES.items():
        optional_status[package] = is_package_available(package, min_version)
    
    return optional_status


def is_package_available(package_name: str, min_version: Optional[str] = None) -> bool:
    """
    检查单个包是否可用
    
    Args:
        package_name: 包名
        min_version: 最低版本要求
    
    Returns:
        bool: 包是否可用且满足版本要求
    """
    try:
        # 特殊处理 tkinter
        if package_name == 'tkinter':
            import tkinter
            return True
        
        # 特殊处理 pywin32
        if package_name == 'pywin32':
            try:
                import win32api
                return True
            except ImportError:
                return False
        
        # 导入包
        module = importlib.import_module(package_name)
        
        # 检查版本
        if min_version:
            package_version = getattr(module, '__version__', None)
            if package_version:
                return compare_versions(package_version, min_version) >= 0
        
        return True
        
    except ImportError:
        return False
    except Exception:
        return False


def compare_versions(version1: str, version2: str) -> int:
    """
    比较两个版本号
    
    Args:
        version1: 版本1
        version2: 版本2
    
    Returns:
        int: 1 if version1 > version2, 0 if equal, -1 if version1 < version2
    """
    try:
        def normalize_version(v):
            return [int(x) for x in v.split('.')]
        
        v1_parts = normalize_version(version1)
        v2_parts = normalize_version(version2)
        
        # 补齐长度
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        for i in range(max_len):
            if v1_parts[i] > v2_parts[i]:
                return 1
            elif v1_parts[i] < v2_parts[i]:
                return -1
        
        return 0
        
    except Exception:
        return 0


def get_package_version(package_name: str) -> Optional[str]:
    """
    获取包的版本号
    
    Args:
        package_name: 包名
    
    Returns:
        Optional[str]: 版本号，如果无法获取则返回 None
    """
    try:
        if package_name == 'tkinter':
            import tkinter
            return getattr(tkinter, 'TkVersion', 'Unknown')
        
        if package_name == 'pywin32':
            try:
                import win32api
                return 'Available'
            except ImportError:
                return None
        
        module = importlib.import_module(package_name)
        return getattr(module, '__version__', 'Unknown')
        
    except ImportError:
        return None
    except Exception:
        return 'Unknown'


def install_package(package_name: str, upgrade: bool = False) -> Tuple[bool, str]:
    """
    安装指定的包
    
    Args:
        package_name: 包名
        upgrade: 是否升级到最新版本
    
    Returns:
        Tuple[bool, str]: (是否成功, 输出信息)
    """
    try:
        cmd = [sys.executable, '-m', 'pip', 'install']
        
        if upgrade:
            cmd.append('--upgrade')
        
        cmd.append(package_name)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        return False, "安装超时"
    except Exception as e:
        return False, str(e)


def install_all_dependencies(include_optional: bool = False) -> Dict[str, Tuple[bool, str]]:
    """
    安装所有依赖包
    
    Args:
        include_optional: 是否包含可选依赖
    
    Returns:
        Dict[str, Tuple[bool, str]]: 包名到安装结果的映射
    """
    results = {}
    
    # 安装必需依赖
    packages_to_install = list(REQUIRED_PACKAGES.keys())
    
    # 排除内置模块
    packages_to_install = [pkg for pkg in packages_to_install if pkg != 'tkinter']
    
    if include_optional:
        packages_to_install.extend(OPTIONAL_PACKAGES.keys())
    
    for package in packages_to_install:
        print(f"正在安装 {package}...")
        success, message = install_package(package)
        results[package] = (success, message)
        
        if success:
            print(f"✓ {package} 安装成功")
        else:
            print(f"✗ {package} 安装失败: {message}")
    
    return results


def generate_requirements_txt(file_path: str = "requirements.txt", include_optional: bool = False) -> bool:
    """
    生成 requirements.txt 文件
    
    Args:
        file_path: 输出文件路径
        include_optional: 是否包含可选依赖
    
    Returns:
        bool: 是否成功生成
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# Ollama Manager 依赖包\n")
            f.write("# 必需依赖\n")
            
            for package, min_version in REQUIRED_PACKAGES.items():
                if package == 'tkinter':  # 跳过内置模块
                    continue
                
                if min_version:
                    f.write(f"{package}>={min_version}\n")
                else:
                    f.write(f"{package}\n")
            
            if include_optional:
                f.write("\n# 可选依赖\n")
                for package, min_version in OPTIONAL_PACKAGES.items():
                    if min_version:
                        f.write(f"{package}>={min_version}\n")
                    else:
                        f.write(f"{package}\n")
        
        return True
        
    except Exception as e:
        print(f"生成 requirements.txt 失败: {e}")
        return False


def get_dependency_report() -> Dict[str, Dict]:
    """
    生成依赖检查报告
    
    Returns:
        Dict: 包含所有依赖信息的报告
    """
    report = {
        'required': {},
        'optional': {},
        'system_info': {
            'python_version': sys.version,
            'platform': sys.platform
        }
    }
    
    # 检查必需依赖
    for package, min_version in REQUIRED_PACKAGES.items():
        available = is_package_available(package, min_version)
        current_version = get_package_version(package) if available else None
        
        report['required'][package] = {
            'available': available,
            'required_version': min_version,
            'current_version': current_version,
            'status': 'OK' if available else 'MISSING'
        }
    
    # 检查可选依赖
    for package, min_version in OPTIONAL_PACKAGES.items():
        available = is_package_available(package, min_version)
        current_version = get_package_version(package) if available else None
        
        report['optional'][package] = {
            'available': available,
            'required_version': min_version,
            'current_version': current_version,
            'status': 'OK' if available else 'NOT_INSTALLED'
        }
    
    return report


def print_dependency_report():
    """打印依赖检查报告"""
    report = get_dependency_report()
    
    print("\n=== Ollama Manager 依赖检查报告 ===")
    print(f"Python 版本: {report['system_info']['python_version']}")
    print(f"平台: {report['system_info']['platform']}")
    
    print("\n必需依赖:")
    for package, info in report['required'].items():
        status_symbol = "✓" if info['status'] == 'OK' else "✗"
        print(f"  {status_symbol} {package}: {info['status']} (当前: {info['current_version']})")
    
    print("\n可选依赖:")
    for package, info in report['optional'].items():
        status_symbol = "✓" if info['status'] == 'OK' else "○"
        print(f"  {status_symbol} {package}: {info['status']} (当前: {info['current_version']})")
    
    # 检查是否有缺失的必需依赖
    missing_required = [pkg for pkg, info in report['required'].items() if info['status'] != 'OK']
    if missing_required:
        print(f"\n⚠️  缺少必需依赖: {', '.join(missing_required)}")
        print("请运行以下命令安装:")
        print(f"pip install {' '.join(missing_required)}")
    else:
        print("\n✅ 所有必需依赖都已满足")


if __name__ == "__main__":
    print_dependency_report()