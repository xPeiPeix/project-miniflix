#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能视频自动化处理系统 - 启动脚本
Author: nya~ 🐱

使用方法:
    python run_auto_processor.py                   # 启动守护进程
    python run_auto_processor.py --test           # 测试模式
    python run_auto_processor.py --status         # 查看状态
    python run_auto_processor.py --stop           # 停止服务
"""

import sys
from pathlib import Path

# 强制将项目根目录添加到Python模块搜索路径
# 确保无论从哪里启动，都能找到 auto_processor 模块
project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import argparse

from auto_processor.main_processor import auto_processor
from auto_processor.logger import logger
from auto_processor.config import config

def main():
    parser = argparse.ArgumentParser(description='智能视频自动化处理系统')
    parser.add_argument('--test', action='store_true', help='测试模式运行')
    parser.add_argument('--status', action='store_true', help='查看系统状态')
    parser.add_argument('--stop', action='store_true', help='停止服务')
    parser.add_argument('--scan-only', action='store_true', help='仅扫描现有文件，不启动监控')
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
        return
    
    if args.stop:
        stop_service()
        return
    
    if args.test:
        run_test_mode()
        return
    
    if args.scan_only:
        scan_existing_files()
        return
    
    # 默认启动守护进程
    run_daemon_mode()

def show_status():
    """显示系统状态"""
    try:
        status = auto_processor.get_status()
        
        print("🖥️  智能视频自动化处理系统状态")
        print("=" * 50)
        print(f"运行状态: {'🟢 运行中' if status['is_running'] else '🔴 已停止'}")
        
        if status['monitor_status']:
            monitor = status['monitor_status']
            print(f"文件监控: {'🟢 正常' if monitor['is_running'] else '🔴 停止'}")
            print(f"监控目录: {monitor['watch_directory']}")
            print(f"监控类型: {', '.join(monitor['watch_extensions'])}")
            print(f"待处理文件: {monitor['pending_files']}")
            print(f"正在处理: {monitor['processing_files']}")
        
        metrics = status['processing_metrics']
        print(f"\n📊 处理统计:")
        print(f"运行时间: {metrics['uptime_formatted']}")
        print(f"处理总数: {metrics['total_processed']}")
        print(f"成功率: {metrics['success_rate']}")
        print(f"平均处理时间: {metrics['avg_processing_time']}")
        print(f"并发限制: {status['concurrent_limit']}")
        print(f"当前活跃: {status['active_processing']}")
        
    except Exception as e:
        print(f"❌ 获取状态失败: {e}")

def stop_service():
    """停止服务"""
    try:
        logger.info("正在停止服务...")
        auto_processor.stop()
        print("✅ 服务已停止")
    except Exception as e:
        print(f"❌ 停止服务失败: {e}")

def run_test_mode():
    """测试模式运行"""
    print("🧪 启动测试模式...")
    
    try:
        # 创建测试配置
        original_log_level = config.get("system.log_level")
        config.set("system.log_level", "DEBUG")
        config.set("system.concurrent_processing", 1)
        
        print("📋 配置信息:")
        print(f"  监控目录: {config.videos_dir}")
        print(f"  输出目录: {config.hls_output_dir}")
        print(f"  缩略图目录: {config.thumbnails_dir}")
        print(f"  日志目录: {config.logs_dir}")
        print(f"  并发处理: {config.get('system.concurrent_processing')}")
        
        print("\n🚀 启动测试...")
        auto_processor.start()
        
    except KeyboardInterrupt:
        print("\n🛑 测试被用户中断")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    finally:
        # 恢复原始配置
        config.set("system.log_level", original_log_level)

def scan_existing_files():
    """仅扫描现有文件"""
    print("🔍 扫描现有视频文件...")
    
    try:
        from auto_processor.main_processor import auto_processor
        
        auto_processor.scan_and_process_existing_files()
        
        print("✅ 扫描完成")
        
    except Exception as e:
        print(f"❌ 扫描失败: {e}")

def run_daemon_mode():
    """守护进程模式"""
    print("🚀 启动智能视频自动化处理系统...")
    print(f"📁 监控目录: {config.videos_dir}")
    print(f"📋 配置文件: {config.config_file}")
    print("按 Ctrl+C 停止服务\n")
    
    try:
        auto_processor.start()
    except KeyboardInterrupt:
        print("\n🛑 收到停止信号")
    except Exception as e:
        logger.error(f"运行失败: {e}")
        print(f"❌ 系统运行失败: {e}")
    finally:
        auto_processor.stop()

if __name__ == "__main__":
    main() 