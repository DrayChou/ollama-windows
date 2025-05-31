#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理器模块

提供完整的日志记录功能：
- 多级别日志记录
- 文件和控制台输出
- 日志轮转
- 日志查看和导出
"""

import os
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class Logger:
    """
    日志管理器
    
    提供统一的日志记录接口和管理功能
    """
    
    def __init__(self, name: str = "OllamaManager", log_dir: str = "logs"):
        """初始化日志管理器"""
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 创建日志器
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()
        
        # 内存日志缓存（用于UI显示）
        self.memory_logs = []
        self.max_memory_logs = 1000
    
    def _setup_handlers(self):
        """设置日志处理器"""
        # 文件处理器 - 详细日志
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "ollama_manager.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # 控制台处理器 - 简化输出
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # 内存处理器 - 用于UI显示
        memory_handler = MemoryHandler(self)
        memory_handler.setLevel(logging.INFO)
        memory_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s'
        )
        memory_handler.setFormatter(memory_formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(memory_handler)
    
    def debug(self, message: str):
        """记录调试信息"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """记录一般信息"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """记录警告信息"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """记录错误信息"""
        self.logger.error(message)
    
    def critical(self, message: str):
        """记录严重错误"""
        self.logger.critical(message)
    
    def add_memory_log(self, record: logging.LogRecord):
        """添加日志到内存缓存"""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module
        }
        
        self.memory_logs.append(log_entry)
        
        # 保持缓存大小
        if len(self.memory_logs) > self.max_memory_logs:
            self.memory_logs.pop(0)
    
    def get_memory_logs(self, level: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
        """获取内存中的日志"""
        logs = self.memory_logs
        
        # 按级别过滤
        if level:
            logs = [log for log in logs if log['level'] == level]
        
        # 限制数量
        if limit:
            logs = logs[-limit:]
        
        return logs
    
    def clear_memory_logs(self):
        """清空内存日志"""
        self.memory_logs.clear()
    
    def get_log_files(self) -> List[Path]:
        """获取所有日志文件"""
        return list(self.log_dir.glob("*.log*"))
    
    def read_log_file(self, file_path: Path, lines: Optional[int] = None) -> List[str]:
        """读取日志文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if lines:
                    # 读取最后几行
                    all_lines = f.readlines()
                    return all_lines[-lines:] if len(all_lines) > lines else all_lines
                else:
                    return f.readlines()
        except Exception as e:
            self.error(f"读取日志文件失败: {e}")
            return []
    
    def export_logs(self, output_file: str, level: Optional[str] = None, 
                   start_time: Optional[datetime] = None, 
                   end_time: Optional[datetime] = None) -> bool:
        """导出日志到文件"""
        try:
            logs = self.get_memory_logs(level)
            
            # 时间过滤
            if start_time or end_time:
                filtered_logs = []
                for log in logs:
                    log_time = log['timestamp']
                    if start_time and log_time < start_time:
                        continue
                    if end_time and log_time > end_time:
                        continue
                    filtered_logs.append(log)
                logs = filtered_logs
            
            # 写入文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# Ollama Manager 日志导出\n")
                f.write(f"# 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 日志级别: {level or '全部'}\n")
                f.write(f"# 日志数量: {len(logs)}\n\n")
                
                for log in logs:
                    timestamp = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                    f.write(f"[{timestamp}] [{log['level']}] {log['message']}\n")
            
            self.info(f"日志导出成功: {output_file}")
            return True
            
        except Exception as e:
            self.error(f"导出日志失败: {e}")
            return False
    
    def set_level(self, level: str):
        """设置日志级别"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        if level.upper() in level_map:
            self.logger.setLevel(level_map[level.upper()])
            self.info(f"日志级别设置为: {level.upper()}")
        else:
            self.warning(f"无效的日志级别: {level}")
    
    def cleanup_old_logs(self, days: int = 30):
        """清理旧日志文件"""
        try:
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(days=days)
            
            removed_count = 0
            for log_file in self.get_log_files():
                if log_file.stat().st_mtime < cutoff_time.timestamp():
                    log_file.unlink()
                    removed_count += 1
            
            if removed_count > 0:
                self.info(f"清理了 {removed_count} 个旧日志文件")
            
        except Exception as e:
            self.error(f"清理旧日志失败: {e}")
    
    def close(self):
        """关闭日志管理器，清理资源"""
        try:
            # 关闭所有处理器
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)
            
            # 清空内存日志
            self.memory_logs.clear()
            
        except Exception as e:
            # 使用 print 而不是 self.error，因为日志系统可能已经关闭
            print(f"关闭日志管理器时发生错误: {e}")


class MemoryHandler(logging.Handler):
    """内存日志处理器"""
    
    def __init__(self, logger_instance):
        super().__init__()
        self.logger_instance = logger_instance
    
    def emit(self, record):
        """处理日志记录"""
        try:
            self.logger_instance.add_memory_log(record)
        except Exception:
            self.handleError(record)