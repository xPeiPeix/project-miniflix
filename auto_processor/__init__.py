#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能视频自动化处理系统
Author: nya~ 🐱
"""

__version__ = "1.0.0"
__author__ = "nya~ 🐱"

from .config import config
from .logger import logger, metrics
from .file_monitor import FileMonitor

__all__ = ['config', 'logger', 'metrics', 'FileMonitor'] 