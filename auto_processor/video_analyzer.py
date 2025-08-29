#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能视频自动化处理系统 - 视频分析模块
Author: nya~ 🐱
"""

import subprocess
import json
import re
from pathlib import Path
from datetime import timedelta

from .config import config
from .logger import logger

class VideoAnalyzer:
    """视频分析器 - 使用FFprobe分析视频信息"""
    
    def __init__(self):
        self.ffprobe_cmd = self._find_ffprobe()
    
    def _find_ffprobe(self):
        """查找ffprobe可执行文件"""
        for cmd in ['ffprobe', '/usr/bin/ffprobe', '/usr/local/bin/ffprobe']:
            try:
                result = subprocess.run([cmd, '-version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    logger.debug(f"找到FFprobe: {cmd}")
                    return cmd
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        raise RuntimeError("未找到FFprobe，请确保已安装FFmpeg")
    
    def analyze_video(self, video_path):
        """分析视频文件，返回详细信息"""
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        logger.debug(f"开始分析视频: {video_path}")
        
        try:
            # 使用ffprobe获取视频信息
            cmd = [
                self.ffprobe_cmd,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(video_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise RuntimeError(f"FFprobe执行失败: {result.stderr}")
            
            probe_data = json.loads(result.stdout)
            
            # 解析视频信息
            video_info = self._parse_probe_data(probe_data, video_path)
            
            logger.debug(f"视频分析完成: {video_info['filename']}")
            return video_info
            
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"视频分析超时: {video_path}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"解析FFprobe输出失败: {e}")
        except Exception as e:
            raise RuntimeError(f"视频分析失败: {e}")
    
    def _parse_probe_data(self, probe_data, video_path):
        """解析FFprobe数据"""
        video_path = Path(video_path)
        
        # 获取格式信息
        format_info = probe_data.get('format', {})
        streams = probe_data.get('streams', [])
        
        # 查找视频流和音频流
        video_stream = None
        audio_stream = None
        
        for stream in streams:
            if stream.get('codec_type') == 'video' and not video_stream:
                video_stream = stream
            elif stream.get('codec_type') == 'audio' and not audio_stream:
                audio_stream = stream
        
        # 基本信息
        duration_seconds = float(format_info.get('duration', 0))
        file_size = int(format_info.get('size', video_path.stat().st_size))
        
        # 视频信息
        video_info = {
            # 文件基本信息
            'filename': video_path.name,
            'filepath': str(video_path),
            'file_size': file_size,
            'file_size_mb': round(file_size / (1024 * 1024), 2),
            
            # 视频时长
            'duration_seconds': duration_seconds,
            'duration_formatted': self._format_duration(duration_seconds),
            
            # 视频流信息
            'video_codec': video_stream.get('codec_name', 'unknown') if video_stream else None,
            'width': int(video_stream.get('width', 0)) if video_stream else 0,
            'height': int(video_stream.get('height', 0)) if video_stream else 0,
            'fps': self._parse_fps(video_stream.get('r_frame_rate', '0/1')) if video_stream else 0,
            'video_bitrate': int(video_stream.get('bit_rate', 0)) if video_stream else 0,
            
            # 音频流信息  
            'audio_codec': audio_stream.get('codec_name', 'unknown') if audio_stream else None,
            'audio_sample_rate': int(audio_stream.get('sample_rate', 0)) if audio_stream else 0,
            'audio_channels': int(audio_stream.get('channels', 0)) if audio_stream else 0,
            'audio_bitrate': int(audio_stream.get('bit_rate', 0)) if audio_stream else 0,
            
            # 总比特率
            'total_bitrate': int(format_info.get('bit_rate', 0)),
            
            # 分辨率描述
            'resolution': f"{video_stream.get('width', 0)}x{video_stream.get('height', 0)}" if video_stream else "0x0",
            
            # 视频质量评估
            'quality_assessment': self._assess_video_quality(video_stream, audio_stream) if video_stream else 'unknown'
        }
        
        return video_info
    
    def _format_duration(self, seconds):
        """格式化时长为 HH:MM:SS 或 MM:SS"""
        if seconds <= 0:
            return "00:00"
        
        td = timedelta(seconds=int(seconds))
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def _parse_fps(self, fps_string):
        """解析帧率字符串"""
        try:
            if '/' in fps_string:
                numerator, denominator = map(int, fps_string.split('/'))
                if denominator == 0:
                    return 0
                return round(numerator / denominator, 2)
            else:
                return float(fps_string)
        except (ValueError, ZeroDivisionError):
            return 0
    
    def _assess_video_quality(self, video_stream, audio_stream):
        """评估视频质量"""
        if not video_stream:
            return 'unknown'
        
        width = int(video_stream.get('width', 0))
        height = int(video_stream.get('height', 0))
        bitrate = int(video_stream.get('bit_rate', 0))
        
        # 基于分辨率和比特率评估质量
        if height >= 1080:
            return 'high'  # 高清
        elif height >= 720:
            return 'medium'  # 标清
        elif height >= 480:
            return 'low'  # 低清
        else:
            return 'very_low'  # 极低清

class VideoIDGenerator:
    """视频ID生成器"""
    
    def __init__(self):
        self.id_rule = config.get("templates.id_generation_rule", "filename_based")
    
    def generate_id(self, video_path, video_info=None):
        """生成视频ID"""
        video_path = Path(video_path)
        
        if self.id_rule == "filename_based":
            return self._generate_filename_based_id(video_path)
        elif self.id_rule == "timestamp_based":
            return self._generate_timestamp_based_id(video_path)
        elif self.id_rule == "uuid_based":
            return self._generate_uuid_based_id()
        else:
            # 默认使用文件名
            return self._generate_filename_based_id(video_path)
    
    def _generate_filename_based_id(self, video_path):
        """基于文件名生成ID"""
        filename = video_path.stem  # 不包含扩展名
        
        # 清理文件名，只保留安全字符
        clean_name = re.sub(r'[^\w\-_.]', '-', filename)
        clean_name = re.sub(r'-+', '-', clean_name)  # 合并多个连字符
        clean_name = clean_name.strip('-')  # 移除首尾连字符
        
        # 转为小写
        clean_name = clean_name.lower()
        
        # 应用已知的映射规则（兼容现有数据）
        name_mappings = {
            '讲课视频1': 'lecture-video-1',
            '讲课视频2': 'lecture-video-2', 
            '一对一1': 'one-on-one-1',
            '一对一2': 'one-on-one-2'
        }
        
        if filename in name_mappings:
            return name_mappings[filename]
        
        return clean_name or 'video'
    
    def _generate_timestamp_based_id(self, video_path):
        """基于时间戳生成ID"""
        import time
        timestamp = int(time.time())
        filename = video_path.stem.lower()
        return f"{filename}-{timestamp}"
    
    def _generate_uuid_based_id(self):
        """基于UUID生成ID"""
        import uuid
        return str(uuid.uuid4())

class CategoryClassifier:
    """视频分类器"""
    
    def __init__(self):
        self.categories = config.get("templates.auto_categories", {})
    
    def classify_video(self, video_path, video_info=None):
        """自动分类视频"""
        filename = Path(video_path).stem.lower()
        
        # 基于文件名关键词分类
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in filename:
                    logger.debug(f"视频分类: {filename} -> {category} (关键词: {keyword})")
                    return category
        
        # 如果没有匹配的分类，返回默认
        return 'general'
    
    def get_category_info(self, category):
        """获取分类信息"""
        category_info = {
            'lecture': {
                'title_prefix': '专业讲课视频',
                'description_template': '系统性课堂教学，内容丰富全面，深入系统的讲解备课理论知识和方法。'
            },
            'tutorial': {
                'title_prefix': '教程视频',
                'description_template': '详细的教程指导，帮助您快速掌握相关技能和知识。'
            },
            'oneOnOne': {
                'title_prefix': '一对一',
                'description_template': '上课采用一对一专业辅导方式，精准有效。'
            },
            'general': {
                'title_prefix': '视频',
                'description_template': '精彩的视频内容，值得观看。'
            }
        }
        
        return category_info.get(category, category_info['general']) 