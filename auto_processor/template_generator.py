#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能视频自动化处理系统 - 模板生成模块
Author: nya~ 🐱
"""

import json
from pathlib import Path
from datetime import datetime
import threading

from .config import config
from .logger import logger
from .video_analyzer import CategoryClassifier

class VideoMetadataGenerator:
    """视频元数据生成器"""
    
    def __init__(self):
        self.classifier = CategoryClassifier()
        self.ai_enabled = config.get("ai_integration.enabled", False)
    
    def generate_metadata(self, video_path, video_info, processing_result):
        """生成视频元数据"""
        video_id = processing_result['video_id']
        
        # 基本元数据
        metadata = {
            'id': video_id,
            'title': self._generate_title(video_path, video_info),
            'description': self._generate_description(video_path, video_info),
            'thumbnail': f"thumbnails/{video_id}.jpg",
            'hls_url': f"hls_videos_optimized/{video_id}.m3u8",
            'duration': video_info['duration_formatted']
        }
        
        return metadata
    
    def _generate_title(self, video_path, video_info):
        """生成视频标题"""
        filename = Path(video_path).stem
        
        # 获取分类信息
        category = self.classifier.classify_video(video_path, video_info)
        category_info = self.classifier.get_category_info(category)
        
        # 使用分类前缀
        title_prefix = category_info['title_prefix']
        
        # 智能标题生成逻辑
        if '讲课' in filename or 'lecture' in filename.lower():
            # 提取数字
            import re
            number_match = re.search(r'(\d+)', filename)
            number = number_match.group(1) if number_match else '1'
            return f"{title_prefix} 视频{number}"
        
        elif '一对一' in filename or 'one-on-one' in filename.lower():
            # 提取数字  
            import re
            number_match = re.search(r'(\d+)', filename)
            number = number_match.group(1) if number_match else '1'
            return f"{title_prefix} 视频{number}"
        
        else:
            # 默认清理文件名作为标题
            clean_title = filename.replace('_', ' ').replace('-', ' ').title()
            return f"{title_prefix} - {clean_title}"
    
    def _generate_description(self, video_path, video_info):
        """生成视频描述"""
        # 获取分类信息
        category = self.classifier.classify_video(video_path, video_info)
        category_info = self.classifier.get_category_info(category)
        
        return category_info['description_template']

class VideosJsonManager:
    """videos.json文件管理器"""
    
    def __init__(self):
        self.videos_json_path = Path(config.get("directories.videos")).parent / "videos.json"
        self.lock = threading.Lock()  # 确保线程安全
    
    def add_video_metadata(self, metadata):
        """添加视频元数据到videos.json"""
        with self.lock:
            try:
                # 读取现有数据
                existing_videos = self._load_videos_json()
                
                # 检查是否已存在相同ID的视频
                video_id = metadata['id']
                existing_index = None
                
                for i, video in enumerate(existing_videos):
                    if video.get('id') == video_id:
                        existing_index = i
                        break
                
                # 更新或添加视频
                if existing_index is not None:
                    logger.info(f"更新现有视频元数据: {video_id}")
                    existing_videos[existing_index] = metadata
                else:
                    logger.info(f"添加新视频元数据: {video_id}")
                    existing_videos.append(metadata)
                
                # 按ID排序
                existing_videos.sort(key=lambda x: x.get('id', ''))
                
                # 保存到文件
                self._save_videos_json(existing_videos)
                
                logger.info(f"✅ videos.json已更新 (共{len(existing_videos)}个视频)")
                
            except Exception as e:
                logger.error(f"更新videos.json失败: {e}")
                raise
    
    def _load_videos_json(self):
        """加载videos.json文件"""
        if not self.videos_json_path.exists():
            logger.info("videos.json不存在，将创建新文件")
            return []
        
        try:
            with open(self.videos_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            logger.debug(f"加载了{len(data)}个视频记录")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"videos.json格式错误: {e}")
            # 备份损坏的文件
            backup_path = self.videos_json_path.with_suffix('.json.backup')
            self.videos_json_path.rename(backup_path)
            logger.info(f"已备份损坏文件到: {backup_path}")
            return []
        
        except Exception as e:
            logger.error(f"读取videos.json失败: {e}")
            return []
    
    def _save_videos_json(self, videos_data):
        """保存videos.json文件"""
        try:
            # 创建临时文件
            temp_path = self.videos_json_path.with_suffix('.json.tmp')
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(videos_data, f, ensure_ascii=False, indent=2)
            
            # 原子性替换
            temp_path.replace(self.videos_json_path)
            
            logger.debug(f"videos.json已保存 ({self.videos_json_path})")
            
        except Exception as e:
            logger.error(f"保存videos.json失败: {e}")
            raise 