#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能视频自动化处理系统 - 文件监控模块
Author: nya~ 🐱
"""

import os
import time
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .config import config
from .logger import logger

class VideoFileHandler(FileSystemEventHandler):
    """视频文件事件处理器"""
    
    def __init__(self, processor_callback):
        super().__init__()
        self.processor_callback = processor_callback
        self.watch_extensions = [ext.lower() for ext in config.get("monitor.watch_extensions", [])]
        self.ignore_patterns = config.get("monitor.ignore_patterns", [])
        self.debounce_time = config.get("monitor.debounce_time", 5)
        self.max_file_size = config.get("monitor.max_file_size", 1024*1024*1024)  # 1GB
        
        # 防抖动处理 - 存储正在处理的文件
        self.pending_files = {}
        self.processing_files = set()
        self.lock = threading.Lock()
    
    def on_created(self, event):
        """文件创建事件"""
        if not event.is_directory:
            self._handle_file_event("created", event.src_path)
    
    def on_modified(self, event):
        """文件修改事件"""
        if not event.is_directory:
            self._handle_file_event("modified", event.src_path)
    
    def on_moved(self, event):
        """文件移动事件"""
        if not event.is_directory:
            self._handle_file_event("moved_to", event.dest_path)
    
    def _handle_file_event(self, event_type, file_path):
        """处理文件事件"""
        file_path = Path(file_path)
        
        # 检查文件扩展名
        if not self._is_video_file(file_path):
            return
        
        # 检查忽略模式
        if self._should_ignore_file(file_path):
            logger.debug(f"忽略文件: {file_path} (匹配忽略模式)")
            return
        
        logger.log_file_monitor_event(event_type, file_path)
        
        # 防抖动处理
        with self.lock:
            if str(file_path) in self.processing_files:
                logger.debug(f"文件正在处理中，跳过: {file_path}")
                return
            
            # 重置防抖计时器
            if str(file_path) in self.pending_files:
                self.pending_files[str(file_path)].cancel()
            
            # 创建新的防抖计时器
            timer = threading.Timer(self.debounce_time, self._process_file_delayed, [file_path])
            self.pending_files[str(file_path)] = timer
            timer.start()
    
    def _process_file_delayed(self, file_path):
        """延迟处理文件（防抖动后执行）"""
        try:
            with self.lock:
                # 移除防抖记录
                if str(file_path) in self.pending_files:
                    del self.pending_files[str(file_path)]
                
                # 添加到正在处理列表
                self.processing_files.add(str(file_path))
            
            # 验证文件状态
            if not self._validate_file(file_path):
                return
            
            logger.info(f"触发视频处理: {file_path}")
            
            # 调用处理回调
            if self.processor_callback:
                self.processor_callback(file_path)
                
        except Exception as e:
            logger.error(f"处理文件事件时发生错误: {e}")
        finally:
            # 移除正在处理标记
            with self.lock:
                self.processing_files.discard(str(file_path))
    
    def _is_video_file(self, file_path):
        """检查是否为视频文件"""
        return file_path.suffix.lower() in self.watch_extensions
    
    def _should_ignore_file(self, file_path):
        """检查是否应该忽略文件"""
        file_name = file_path.name
        
        for pattern in self.ignore_patterns:
            if pattern.replace('*', '') in file_name:
                return True
        
        return False
    
    def _validate_file(self, file_path):
        """验证文件有效性"""
        try:
            # 检查文件是否存在
            if not file_path.exists():
                logger.warning(f"文件不存在: {file_path}")
                return False
            
            # 检查文件大小
            file_size = file_path.stat().st_size
            if file_size == 0:
                logger.warning(f"文件为空: {file_path}")
                return False
            
            if file_size > self.max_file_size:
                logger.warning(f"文件过大 ({file_size / (1024*1024):.1f}MB): {file_path}")
                return False
            
            # 等待文件写入完成（检查文件大小是否稳定）
            logger.debug(f"等待文件稳定: {file_path}")
            prev_size = file_size
            time.sleep(1)  # 短暂等待
            
            current_size = file_path.stat().st_size
            if current_size != prev_size:
                logger.debug(f"文件仍在写入中: {file_path} ({prev_size} -> {current_size})")
                return False
            
            # 尝试打开文件检查是否被占用
            try:
                with open(file_path, 'rb') as f:
                    f.read(1024)  # 读取一小部分数据
            except IOError as e:
                logger.warning(f"文件被占用或无法读取: {file_path} - {e}")
                return False
            
            logger.debug(f"文件验证通过: {file_path} ({file_size / (1024*1024):.1f}MB)")
            return True
            
        except Exception as e:
            logger.error(f"文件验证失败: {file_path} - {e}")
            return False

class FileMonitor:
    """文件监控器"""
    
    def __init__(self, processor_callback=None):
        self.processor_callback = processor_callback
        self.observer = None
        self.handler = None
        self.watch_dir = config.videos_dir
        self.is_running = False
    
    def start(self):
        """启动文件监控"""
        if self.is_running:
            logger.warning("文件监控已在运行中")
            return
        
        try:
            # 确保监控目录存在
            self.watch_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建事件处理器
            self.handler = VideoFileHandler(self.processor_callback)
            
            # 创建观察者
            self.observer = Observer()
            self.observer.schedule(self.handler, str(self.watch_dir), recursive=False)
            
            # 启动观察者
            self.observer.start()
            self.is_running = True
            
            logger.info(f"文件监控已启动: {self.watch_dir}")
            logger.info(f"监控文件类型: {config.get('monitor.watch_extensions')}")
            logger.info(f"防抖动时间: {config.get('monitor.debounce_time')}秒")
            
        except Exception as e:
            logger.error(f"启动文件监控失败: {e}")
            self.stop()
            raise
    
    def stop(self):
        """停止文件监控"""
        if not self.is_running:
            return
        
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5)
                self.observer = None
            
            self.handler = None
            self.is_running = False
            
            logger.info("文件监控已停止")
            
        except Exception as e:
            logger.error(f"停止文件监控时发生错误: {e}")
    
    def is_alive(self):
        """检查监控是否存活"""
        return self.is_running and self.observer and self.observer.is_alive()
    
    def scan_existing_files(self):
        """扫描现有文件并处理"""
        if not self.watch_dir.exists():
            logger.warning(f"监控目录不存在: {self.watch_dir}")
            return
        
        logger.info("扫描现有视频文件...")
        
        watch_extensions = [ext.lower() for ext in config.get("monitor.watch_extensions", [])]
        found_files = []
        
        for file_path in self.watch_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in watch_extensions:
                found_files.append(file_path)
        
        if found_files:
            logger.info(f"发现 {len(found_files)} 个视频文件待处理")
            
            for file_path in found_files:
                try:
                    if self.processor_callback:
                        logger.info(f"处理现有文件: {file_path}")
                        self.processor_callback(file_path)
                except Exception as e:
                    logger.error(f"处理现有文件失败: {file_path} - {e}")
        else:
            logger.info("未发现待处理的视频文件")
    
    def get_status(self):
        """获取监控状态"""
        return {
            'is_running': self.is_running,
            'is_alive': self.is_alive(),
            'watch_directory': str(self.watch_dir),
            'watch_extensions': config.get("monitor.watch_extensions"),
            'pending_files': len(self.handler.pending_files) if self.handler else 0,
            'processing_files': len(self.handler.processing_files) if self.handler else 0
        } 