#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能视频自动化处理系统 - 日志模块
Author: nya~ 🐱
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
import json

from .config import config

class ColorFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色  
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }
    
    def format(self, record):
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)

class VideoProcessLogger:
    """视频处理专用日志器"""
    
    def __init__(self, name="auto_video_processor"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.setup_logger()
    
    def setup_logger(self):
        """设置日志器"""
        # 避免重复设置
        if self.logger.handlers:
            return
            
        log_level = getattr(logging, config.get("system.log_level", "INFO").upper())
        self.logger.setLevel(log_level)
        
        # 创建日志目录
        log_dir = config.logs_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 文件处理器 - 详细日志
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"{self.name}.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台处理器 - 彩色输出
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = ColorFormatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(log_level)
        
        # 错误日志单独文件
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"{self.name}_error.log",
            maxBytes=5*1024*1024,   # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setFormatter(file_formatter)
        error_handler.setLevel(logging.ERROR)
        
        # 添加所有处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler) 
        self.logger.addHandler(error_handler)
    
    def log_video_process_start(self, video_path, video_info=None):
        """记录视频处理开始"""
        self.logger.info(f"🎬 开始处理视频: {video_path}")
        if video_info:
            self.logger.info(f"   📊 视频信息: {video_info}")
    
    def log_video_process_success(self, video_path, output_info=None):
        """记录视频处理成功"""
        self.logger.info(f"✅ 视频处理完成: {video_path}")
        if output_info:
            self.logger.info(f"   📁 输出信息: {output_info}")
    
    def log_video_process_error(self, video_path, error, step=None):
        """记录视频处理错误"""
        step_info = f" (步骤: {step})" if step else ""
        self.logger.error(f"❌ 视频处理失败: {video_path}{step_info}")
        self.logger.error(f"   🚨 错误详情: {error}")
    
    def log_file_monitor_event(self, event_type, file_path):
        """记录文件监控事件"""
        self.logger.info(f"👁️ 文件监控: {event_type} - {file_path}")
    
    def log_system_status(self, status_info):
        """记录系统状态"""
        self.logger.info(f"🖥️ 系统状态: {status_info}")
    
    def log_performance_metrics(self, metrics):
        """记录性能指标"""
        self.logger.info(f"📈 性能指标: {json.dumps(metrics, ensure_ascii=False)}")
    
    def debug(self, message):
        self.logger.debug(f"🔍 {message}")
    
    def info(self, message):
        self.logger.info(f"ℹ️  {message}")
    
    def warning(self, message):
        self.logger.warning(f"⚠️  {message}")
    
    def error(self, message):
        self.logger.error(f"🚨 {message}")
    
    def critical(self, message):
        self.logger.critical(f"💥 {message}")

class ProcessingMetrics:
    """处理过程指标收集器"""
    
    def __init__(self):
        self.metrics = {
            'total_processed': 0,
            'successful_processed': 0,
            'failed_processed': 0,
            'processing_times': [],
            'start_time': datetime.now(),
            'last_processed': None
        }
        self.logger = VideoProcessLogger("metrics")
    
    def record_processing_start(self, video_path):
        """记录处理开始"""
        self.current_processing = {
            'video_path': video_path,
            'start_time': datetime.now()
        }
    
    def record_processing_success(self, video_path, processing_time=None):
        """记录处理成功"""
        if not processing_time and hasattr(self, 'current_processing'):
            processing_time = (datetime.now() - self.current_processing['start_time']).total_seconds()
        
        self.metrics['total_processed'] += 1
        self.metrics['successful_processed'] += 1
        self.metrics['processing_times'].append(processing_time)
        self.metrics['last_processed'] = datetime.now()
        
        # 只保留最近100次的处理时间
        if len(self.metrics['processing_times']) > 100:
            self.metrics['processing_times'] = self.metrics['processing_times'][-100:]
        
        self.logger.log_performance_metrics({
            'video_path': str(video_path),
            'processing_time': f"{processing_time:.2f}s",
            'total_processed': self.metrics['total_processed'],
            'success_rate': f"{self.get_success_rate():.1f}%"
        })
    
    def record_processing_failure(self, video_path, error):
        """记录处理失败"""
        self.metrics['total_processed'] += 1
        self.metrics['failed_processed'] += 1
        self.metrics['last_processed'] = datetime.now()
        
        self.logger.log_performance_metrics({
            'video_path': str(video_path),
            'status': 'failed',
            'error': str(error),
            'total_processed': self.metrics['total_processed'],
            'success_rate': f"{self.get_success_rate():.1f}%"
        })
    
    def get_success_rate(self):
        """获取成功率"""
        if self.metrics['total_processed'] == 0:
            return 100.0
        return (self.metrics['successful_processed'] / self.metrics['total_processed']) * 100
    
    def get_average_processing_time(self):
        """获取平均处理时间"""
        if not self.metrics['processing_times']:
            return 0
        return sum(self.metrics['processing_times']) / len(self.metrics['processing_times'])
    
    def get_summary(self):
        """获取指标摘要"""
        uptime = (datetime.now() - self.metrics['start_time']).total_seconds()
        return {
            'uptime_seconds': uptime,
            'uptime_formatted': f"{uptime//3600:.0f}h {(uptime%3600)//60:.0f}m",
            'total_processed': self.metrics['total_processed'],
            'successful': self.metrics['successful_processed'],
            'failed': self.metrics['failed_processed'],
            'success_rate': f"{self.get_success_rate():.1f}%",
            'avg_processing_time': f"{self.get_average_processing_time():.2f}s",
            'last_processed': self.metrics['last_processed'].isoformat() if self.metrics['last_processed'] else None
        }

# 全局实例
logger = VideoProcessLogger()
metrics = ProcessingMetrics() 