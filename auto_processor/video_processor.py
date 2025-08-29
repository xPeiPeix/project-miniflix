#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能视频自动化处理系统 - 视频处理模块
Author: nya~ 🐱
"""

import subprocess
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import re
import time

from .config import config
from .logger import logger, metrics
from .video_analyzer import VideoAnalyzer, VideoIDGenerator

class VideoProcessor:
    """视频处理器 - 负责HLS转码和缩略图生成"""
    
    def __init__(self):
        self.ffmpeg_cmd = self._find_ffmpeg()
        self.analyzer = VideoAnalyzer()
        self.id_generator = VideoIDGenerator()
        
        # 处理参数
        self.segment_time = config.get("video_processing.segment_time", 3)
        self.video_codec = config.get("video_processing.video_codec", "libx264")
        self.audio_codec = config.get("video_processing.audio_codec", "aac")
        self.preset = config.get("video_processing.preset", "fast")
        self.crf = config.get("video_processing.crf", 23)
        self.maxrate = config.get("video_processing.maxrate", "1500k")
        self.bufsize = config.get("video_processing.bufsize", "3000k")
        self.thumbnail_time = config.get("video_processing.thumbnail_time", "00:00:01")
    
    def _find_ffmpeg(self):
        """查找ffmpeg可执行文件"""
        for cmd in ['ffmpeg', '/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg']:
            try:
                result = subprocess.run([cmd, '-version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    logger.debug(f"找到FFmpeg: {cmd}")
                    return cmd
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        raise RuntimeError("未找到FFmpeg，请确保已安装FFmpeg")
    
    def process_video(self, video_path):
        """处理单个视频文件"""
        video_path = Path(video_path)
        logger.log_video_process_start(video_path)
        metrics.record_processing_start(video_path)
        
        try:
            # 1. 分析视频信息
            logger.info("📊 分析视频信息...")
            video_info = self.analyzer.analyze_video(video_path)
            logger.debug(f"视频信息: {video_info['resolution']}, {video_info['duration_formatted']}, {video_info['file_size_mb']}MB")
            
            # 2. 生成视频ID
            video_id = self.id_generator.generate_id(video_path, video_info)
            logger.info(f"🆔 生成视频ID: {video_id}")
            
            # 3. 创建备份
            backup_info = self._backup_original_if_needed()
            
            # 4. 转码为HLS
            logger.info("🎬 开始HLS转码...")
            hls_output = self._convert_to_hls(video_path, video_id, video_info)
            
            # 5. 生成缩略图
            logger.info("🖼️ 生成视频缩略图...")
            thumbnail_path = self._generate_thumbnail(video_path, video_id, video_info)
            
            # 处理结果
            processing_result = {
                'video_id': video_id,
                'video_info': video_info,
                'hls_output': hls_output,
                'thumbnail_path': thumbnail_path,
                'backup_info': backup_info
            }
            
            logger.log_video_process_success(video_path, processing_result)
            metrics.record_processing_success(video_path)
            
            return processing_result
            
        except Exception as e:
            logger.log_video_process_error(video_path, e)
            metrics.record_processing_failure(video_path, e)
            raise
    
    def _backup_original_if_needed(self):
        """备份原始HLS文件（如果存在）"""
        hls_videos_dir = Path(config.get("directories.hls_output")).parent / "hls_videos"
        backup_dir = Path(config.get("directories.backup"))
        
        if not hls_videos_dir.exists():
            return None
        
        try:
            backup_name = f"hls_videos_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_path = backup_dir / backup_name
            
            shutil.copytree(hls_videos_dir, backup_path)
            logger.info(f"💾 原始HLS文件已备份到: {backup_path}")
            
            return {
                'backup_path': str(backup_path),
                'backup_time': datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"备份失败: {e}")
            return None
    
    def _convert_to_hls(self, video_path, video_id, video_info):
        """转码视频为HLS格式"""
        output_dir = Path(config.get("directories.hls_output"))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 输出文件路径
        m3u8_path = output_dir / f"{video_id}.m3u8"
        segment_pattern = output_dir / f"{video_id}-%03d.ts"
        
        # 构建FFmpeg命令
        cmd = [
            self.ffmpeg_cmd,
            '-i', str(video_path),
            
            # 视频编码参数
            '-c:v', self.video_codec,
            '-c:a', self.audio_codec,
            '-preset', self.preset,
            '-crf', str(self.crf),
            '-maxrate', self.maxrate,
            '-bufsize', self.bufsize,
            
            # GOP和关键帧设置 (针对HLS优化)
            '-g', '90',              # GOP大小 (30fps * 3秒)
            '-keyint_min', '30',     # 最小关键帧间隔
            '-sc_threshold', '0',    # 禁用场景切换检测
            
            # HLS特定参数
            '-hls_time', str(self.segment_time),
            '-hls_playlist_type', 'vod',
            '-hls_segment_filename', str(segment_pattern),
            '-hls_list_size', '0',
            '-hls_flags', 'independent_segments',
            
            # 输出文件
            str(m3u8_path),
            
            # 覆盖现有文件
            '-y'
        ]
        
        logger.debug(f"FFmpeg命令: {' '.join(cmd)}")
        
        try:
            # 使用Popen实时监控FFmpeg输出
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )

            duration_seconds = video_info.get('duration_seconds', 0)
            progress_regex = re.compile(r'time=(\S+)')
            
            logger.info("...[实时转码日志开始]...")
            
            while True:
                line = process.stderr.readline()
                if not line and process.poll() is not None:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                match = progress_regex.search(line)
                if 'frame=' in line and match:
                    timestr = match.group(1)
                    try:
                        # 解析 HH:MM:SS.ms 格式的时间
                        t = time.strptime(timestr.split('.')[0], '%H:%M:%S')
                        current_seconds = timedelta(hours=t.tm_hour, minutes=t.tm_min, seconds=t.tm_sec).total_seconds()
                        if '.' in timestr:
                            current_seconds += float('0.' + timestr.split('.')[1])
                        
                        if duration_seconds > 0:
                            percent = (current_seconds / duration_seconds) * 100
                            logger.info(f"🔄 [{video_id}] 转码进度: {percent:.1f}%")
                        else:
                            logger.info(f"🔄 [{video_id}] 转码时间: {timestr}")
                        logger.debug(f"[ffmpeg-progress] {line}")
                            
                    except ValueError:
                        logger.debug(f"[ffmpeg] {line}")
                else:
                    logger.debug(f"[ffmpeg] {line}")
            
            logger.info("...[实时转码日志结束]...")

            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"FFmpeg转码失败 (code {process.returncode}): {stderr}")
            
            if not m3u8_path.exists():
                raise RuntimeError("HLS播放列表文件未生成")
            
            # 统计分片信息
            segment_files = list(output_dir.glob(f"{video_id}-*.ts"))
            total_size = sum(f.stat().st_size for f in segment_files) + m3u8_path.stat().st_size
            
            hls_info = {
                'playlist_path': str(m3u8_path),
                'segment_count': len(segment_files),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'segment_duration': self.segment_time
            }
            
            logger.info(f"✅ HLS转码完成: {len(segment_files)}个分片, {hls_info['total_size_mb']}MB")
            return hls_info
            
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"FFmpeg转码超时 (视频可能过长或损坏)")
        except Exception as e:
            raise RuntimeError(f"HLS转码过程出错: {e}")
    
    def _generate_thumbnail(self, video_path, video_id, video_info):
        """生成视频缩略图"""
        thumbnails_dir = Path(config.get("directories.thumbnails"))
        thumbnails_dir.mkdir(parents=True, exist_ok=True)
        
        thumbnail_path = thumbnails_dir / f"{video_id}.jpg"
        
        # 计算缩略图提取时间点 (视频的5%位置或1秒，取较大值)
        duration = video_info.get('duration_seconds', 0)
        extract_time = max(1, duration * 0.05)
        
        # 格式化时间
        hours = int(extract_time // 3600)
        minutes = int((extract_time % 3600) // 60)
        seconds = int(extract_time % 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # FFmpeg命令生成缩略图
        cmd = [
            self.ffmpeg_cmd,
            '-i', str(video_path),
            '-ss', time_str,          # 跳转到指定时间
            '-vframes', '1',          # 只提取1帧
            '-vf', 'scale=320:240',   # 缩放到合适尺寸
            '-q:v', '2',              # 高质量JPEG
            str(thumbnail_path),
            '-y'                      # 覆盖现有文件
        ]
        
        logger.debug(f"缩略图命令: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise RuntimeError(f"缩略图生成失败: {result.stderr}")
            
            if not thumbnail_path.exists():
                raise RuntimeError("缩略图文件未生成")
            
            thumbnail_size = thumbnail_path.stat().st_size
            logger.info(f"🖼️ 缩略图生成完成: {thumbnail_path.name} ({thumbnail_size // 1024}KB)")
            
            return {
                'thumbnail_path': str(thumbnail_path),
                'file_size_kb': thumbnail_size // 1024,
                'extract_time': time_str
            }
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("缩略图生成超时")
        except Exception as e:
            raise RuntimeError(f"缩略图生成过程出错: {e}")
    
    def get_processing_capabilities(self):
        """获取处理能力信息"""
        try:
            # 检查FFmpeg版本和支持的编码器
            version_result = subprocess.run([self.ffmpeg_cmd, '-version'], 
                                          capture_output=True, text=True, timeout=5)
            
            encoders_result = subprocess.run([self.ffmpeg_cmd, '-encoders'], 
                                           capture_output=True, text=True, timeout=5)
            
            capabilities = {
                'ffmpeg_available': True,
                'ffmpeg_version': version_result.stdout.split('\n')[0] if version_result.returncode == 0 else 'Unknown',
                'supported_video_codecs': [],
                'supported_audio_codecs': [],
                'hls_support': True,
                'thumbnail_support': True
            }
            
            # 解析支持的编码器
            if encoders_result.returncode == 0:
                encoders_text = encoders_result.stdout
                for line in encoders_text.split('\n'):
                    if 'libx264' in line:
                        capabilities['supported_video_codecs'].append('libx264')
                    if 'aac' in line:
                        capabilities['supported_audio_codecs'].append('aac')
            
            return capabilities
            
        except Exception as e:
            logger.error(f"获取处理能力信息失败: {e}")
            return {
                'ffmpeg_available': False,
                'error': str(e)
            } 