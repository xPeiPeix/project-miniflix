#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能视频自动化处理系统 - 主处理器
Author: nya~ 🐱
"""

import signal
import sys
import time
import threading
from pathlib import Path

from .config import config
from .logger import logger, metrics
from .file_monitor import FileMonitor
from .video_processor import VideoProcessor
from .template_generator import VideoMetadataGenerator, VideosJsonManager
from .video_analyzer import VideoIDGenerator

class AutoVideoProcessor:
    """自动视频处理器主控制器"""
    
    def __init__(self):
        self.is_running = False
        self.monitor = None
        self.processor = VideoProcessor()
        self.metadata_generator = VideoMetadataGenerator()
        self.json_manager = VideosJsonManager()
        self.id_generator = VideoIDGenerator()
        
        # 并发控制
        self.processing_semaphore = threading.Semaphore(
            config.get("system.concurrent_processing", 2)
        )
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def start(self):
        """启动自动处理系统"""
        if self.is_running:
            logger.warning("自动处理系统已在运行中")
            return
        
        try:
            logger.info("🚀 启动智能视频自动化处理系统...")
            
            # 1. 验证环境和依赖
            self._check_environment()
            
            # 2. 启动文件监控
            self.monitor = FileMonitor(processor_callback=self._process_video_callback)
            self.monitor.start()
            
            # 3. 扫描现有文件
            logger.info("🔍 扫描现有视频文件...")
            self.scan_and_process_existing_files()
            
            self.is_running = True
            logger.info("✅ 自动处理系统启动成功")
            
            # 4. 开始监控循环
            self._run_monitoring_loop()
            
        except Exception as e:
            logger.error(f"启动失败: {e}")
            self.stop()
            raise
    
    def stop(self):
        """停止自动处理系统"""
        if not self.is_running:
            return
        
        logger.info("🛑 停止自动处理系统...")
        
        try:
            self.is_running = False
            
            # 停止文件监控
            if self.monitor:
                self.monitor.stop()
                self.monitor = None
            
            # 等待正在处理的任务完成
            active_tasks = self.processing_semaphore._value
            max_tasks = config.get("system.concurrent_processing", 2)
            waiting_tasks = max_tasks - active_tasks
            
            if waiting_tasks > 0:
                logger.info(f"等待 {waiting_tasks} 个处理任务完成...")
                for _ in range(waiting_tasks):
                    self.processing_semaphore.acquire(timeout=30)
            
            logger.info("✅ 自动处理系统已停止")
            
            # 输出最终统计
            summary = metrics.get_summary()
            logger.info(f"📊 运行统计: {summary}")
            
        except Exception as e:
            logger.error(f"停止过程中发生错误: {e}")
    
    def _check_environment(self):
        """检查运行环境"""
        logger.info("🔧 检查运行环境...")
        
        # 检查FFmpeg
        capabilities = self.processor.get_processing_capabilities()
        if not capabilities.get('ffmpeg_available', False):
            raise RuntimeError("FFmpeg不可用，请确保已正确安装")
        
        logger.info(f"✅ FFmpeg版本: {capabilities.get('ffmpeg_version', 'Unknown')}")
        
        # 检查目录权限
        for dir_key, dir_path in config.config["directories"].items():
            path = Path(dir_path)
            try:
                path.mkdir(parents=True, exist_ok=True)
                # 测试写权限
                test_file = path / ".test_write"
                test_file.touch()
                test_file.unlink()
                logger.debug(f"✅ 目录权限正常: {dir_key} -> {dir_path}")
            except Exception as e:
                raise RuntimeError(f"目录权限检查失败 {dir_key}: {e}")
        
        logger.info("✅ 环境检查完成")
    
    def should_process_video(self, video_path):
        """判断是否需要处理视频"""
        video_path = Path(video_path)
        video_id = self.id_generator.generate_id(video_path)
        
        hls_output_dir = config.hls_output_dir
        thumbnails_dir = config.thumbnails_dir
        
        m3u8_path = hls_output_dir / f"{video_id}.m3u8"
        thumbnail_path = thumbnails_dir / f"{video_id}.jpg"
        
        # 检查输出文件是否存在
        if not m3u8_path.exists() or not thumbnail_path.exists():
            logger.debug(f"[{video_id}] 需要处理: 输出文件不完整")
            return True
            
        # 检查源文件修改时间
        try:
            source_mtime = video_path.stat().st_mtime
            output_mtime = m3u8_path.stat().st_mtime
            
            if source_mtime > output_mtime:
                logger.info(f"[{video_id}] 需要重新处理: 源文件已更新")
                return True
                
        except FileNotFoundError:
            # 如果在检查期间文件被删除，也认为需要处理（虽然不太可能）
            return True
            
        logger.info(f"[{video_id}] 已是最新版本，跳过处理")
        return False

    def _process_video_callback(self, video_path):
        """文件监控回调函数"""
        # 检查是否需要处理
        if not self.should_process_video(video_path):
            return

        # 使用信号量控制并发
        if not self.processing_semaphore.acquire(blocking=False):
            video_id = self.id_generator.generate_id(video_path)
            logger.warning(f"[{video_id}] 并发处理数已达上限，视频将等待处理...")
            self.processing_semaphore.acquire()  # 阻塞等待
        
        try:
            # 在单独线程中处理视频
            processing_thread = threading.Thread(
                target=self._process_video_with_error_handling,
                args=(video_path,),
                name=f"VideoProcess-{Path(video_path).stem}"
            )
            processing_thread.start()
            
        except Exception as e:
            logger.error(f"启动处理线程失败: {e}")
            self.processing_semaphore.release()
    
    def _process_video_with_error_handling(self, video_path):
        """带错误处理的视频处理包装器"""
        try:
            self._process_single_video(video_path)
        except Exception as e:
            logger.error(f"处理视频失败: {video_path} - {e}")
        finally:
            self.processing_semaphore.release()
    
    def _process_single_video(self, video_path):
        """处理单个视频的完整流程"""
        video_path = Path(video_path)
        
        logger.info(f"🎬 开始处理视频: {video_path.name}")
        
        try:
            # 1. 视频处理 (HLS转码 + 缩略图)
            processing_result = self.processor.process_video(video_path)
            
            # 2. 生成元数据
            logger.info("📝 生成视频元数据...")
            metadata = self.metadata_generator.generate_metadata(
                video_path, 
                processing_result['video_info'], 
                processing_result
            )
            
            # 3. 更新videos.json
            logger.info("💾 更新videos.json...")
            self.json_manager.add_video_metadata(metadata)
            
            # 4. 成功完成
            logger.info(f"🎉 视频处理完成: {processing_result['video_id']}")
            
            # 输出处理摘要
            self._log_processing_summary(video_path, processing_result, metadata)
            
        except Exception as e:
            logger.error(f"视频处理流程失败: {video_path} - {e}")
            raise
    
    def _log_processing_summary(self, video_path, processing_result, metadata):
        """记录处理摘要"""
        summary = {
            'source_file': str(video_path.name),
            'video_id': processing_result['video_id'],
            'title': metadata['title'],
            'duration': metadata['duration'],
            'hls_segments': processing_result['hls_output']['segment_count'],
            'output_size_mb': processing_result['hls_output']['total_size_mb'],
            'thumbnail_size_kb': processing_result['thumbnail_path']['file_size_kb']
        }
        
        logger.info(f"📋 处理摘要: {summary}")
    
    def _run_monitoring_loop(self):
        """运行监控循环"""
        health_check_interval = config.get("system.health_check_interval", 60)
        last_health_check = time.time()
        
        logger.info("🔄 进入监控循环...")
        
        try:
            while self.is_running:
                time.sleep(1)
                
                # 定期健康检查
                current_time = time.time()
                if current_time - last_health_check >= health_check_interval:
                    self._perform_health_check()
                    last_health_check = current_time
                
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在停止...")
        except Exception as e:
            logger.error(f"监控循环异常: {e}")
        finally:
            self.stop()
    
    def _perform_health_check(self):
        """执行健康检查"""
        try:
            # 检查文件监控状态
            if not self.monitor or not self.monitor.is_alive():
                logger.warning("文件监控已停止，尝试重启...")
                self.monitor = FileMonitor(processor_callback=self._process_video_callback)
                self.monitor.start()
            
            # 检查系统资源
            import psutil
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            
            if memory_percent > 90:
                logger.warning(f"内存使用率过高: {memory_percent:.1f}%")
            
            if disk_percent > 90:
                logger.warning(f"磁盘使用率过高: {disk_percent:.1f}%")
            
            # 记录运行状态
            status_info = {
                'uptime': metrics.get_summary()['uptime_formatted'],
                'total_processed': metrics.get_summary()['total_processed'],
                'success_rate': metrics.get_summary()['success_rate'],
                'memory_usage': f"{memory_percent:.1f}%",
                'disk_usage': f"{disk_percent:.1f}%"
            }
            
            logger.log_system_status(status_info)
            
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        signal_names = {2: 'SIGINT', 15: 'SIGTERM'}
        signal_name = signal_names.get(signum, f'Signal-{signum}')
        
        logger.info(f"收到信号 {signal_name}，准备停止...")
        self.stop()
        sys.exit(0)
    
    def get_status(self):
        """获取系统状态"""
        return {
            'is_running': self.is_running,
            'monitor_status': self.monitor.get_status() if self.monitor else None,
            'processing_metrics': metrics.get_summary(),
            'concurrent_limit': config.get("system.concurrent_processing", 2),
            'active_processing': config.get("system.concurrent_processing", 2) - self.processing_semaphore._value
        }

    def scan_and_process_existing_files(self):
        """扫描并处理所有现有文件"""
        watch_dir = config.videos_dir
        if not watch_dir.exists():
            logger.warning(f"监控目录不存在: {watch_dir}")
            return

        watch_extensions = [ext.lower() for ext in config.get("monitor.watch_extensions", [])]
        found_files = []
        
        for file_path in sorted(watch_dir.iterdir()):
            if file_path.is_file() and file_path.suffix.lower() in watch_extensions:
                found_files.append(file_path)
        
        if found_files:
            logger.info(f"发现 {len(found_files)} 个视频文件，开始智能检查...")
            for file_path in found_files:
                self._process_video_callback(file_path)
        else:
            logger.info("未发现待处理的视频文件")

# 创建全局实例
auto_processor = AutoVideoProcessor() 