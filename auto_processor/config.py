#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能视频自动化处理系统 - 配置模块
Author: nya~ 🐱
"""

import os
import json
from pathlib import Path

class Config:
    """配置管理类"""
    
    def __init__(self, config_file=None):
        self.base_dir = Path(__file__).parent.parent
        self.config_file = config_file or self.base_dir / "auto_processor" / "config.json"
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        default_config = {
            # 目录配置
            "directories": {
                "videos": str(self.base_dir / "videos"),
                "hls_output": str(self.base_dir / "hls_videos_optimized"),
                "thumbnails": str(self.base_dir / "thumbnails"), 
                "backup": str(self.base_dir / "backup"),
                "logs": str(self.base_dir / "logs" / "auto_processor")
            },
            
            # 视频处理配置
            "video_processing": {
                "segment_time": 3,  # HLS分片时长(秒)
                "video_codec": "libx264",
                "audio_codec": "aac",
                "preset": "fast",
                "crf": 23,
                "maxrate": "1500k",
                "bufsize": "3000k",
                "thumbnail_time": "00:00:01"  # 缩略图提取时间点
            },
            
            # 文件监控配置
            "monitor": {
                "watch_extensions": [".mp4", ".avi", ".mov", ".mkv", ".flv"],
                "ignore_patterns": ["*.tmp", "*.part", "*.crdownload"],
                "debounce_time": 5,  # 文件稳定等待时间(秒)
                "max_file_size": 1024 * 1024 * 1024  # 1GB
            },
            
            # 模板配置
            "templates": {
                "default_title_template": "{filename}",
                "default_description_template": "自动生成的视频内容",
                "id_generation_rule": "filename_based",  # filename_based, timestamp_based, uuid_based
                "auto_categories": {
                    "lecture": ["讲课", "授课", "教学", "课程"],
                    "tutorial": ["教程", "指导", "演示"],
                    "oneOnOne": ["一对一", "个人", "私教"]
                }
            },
            
            # AI接口配置 (预留)
            "ai_integration": {
                "enabled": False,
                "title_generation": {
                    "enabled": False,
                    "model": "gpt-3.5-turbo",
                    "prompt_template": "为这个视频生成一个简洁有吸引力的标题: {video_info}"
                },
                "description_generation": {
                    "enabled": False,
                    "model": "gpt-3.5-turbo", 
                    "prompt_template": "为这个视频生成一个详细的描述: {video_info}"
                }
            },
            
            # 系统配置
            "system": {
                "concurrent_processing": 2,  # 并发处理数量
                "retry_attempts": 3,
                "retry_delay": 10,
                "health_check_interval": 60,
                "log_level": "INFO"
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    self._merge_config(default_config, user_config)
            except Exception as e:
                print(f"警告: 配置文件加载失败 {e}, 使用默认配置")
        
        self.config = default_config
        self._create_directories()
    
    def _merge_config(self, default, user):
        """递归合并配置"""
        for key, value in user.items():
            if key in default:
                if isinstance(default[key], dict) and isinstance(value, dict):
                    self._merge_config(default[key], value)
                else:
                    default[key] = value
    
    def _create_directories(self):
        """创建必要的目录"""
        for dir_path in self.config["directories"].values():
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def save_config(self):
        """保存配置到文件"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def get(self, key_path, default=None):
        """获取配置值 (支持点号路径 如: 'video_processing.segment_time')"""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path, value):
        """设置配置值"""
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    @property
    def videos_dir(self):
        return Path(self.get("directories.videos"))
    
    @property 
    def hls_output_dir(self):
        return Path(self.get("directories.hls_output"))
    
    @property
    def thumbnails_dir(self):
        return Path(self.get("directories.thumbnails"))
    
    @property
    def logs_dir(self):
        return Path(self.get("directories.logs"))


# 全局配置实例
config = Config() 