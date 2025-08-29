# 智能视频自动化处理系统 - 使用说明

> **Author**: nya~ 🐱  
> **Version**: 1.0.0

---

## 概述

本系统是一个全自动的视频处理服务，专为Peipei主人的`show_media`项目设计。它可以实时监控`videos`目录，一旦有新的视频文件（如`.mp4`）被添加或修改，系统会自动执行以下操作：

1.  **智能分析**: 使用`FFprobe`分析视频的时长、分辨率等元数据。
2.  **HLS转码**: 使用`FFmpeg`将视频高效地转码为HLS流媒体格式，存放到`hls_videos_optimized`目录。
3.  **缩略图生成**: 自动截取视频中的一帧作为预览图，存放到`thumbnails`目录。
4.  **配置更新**: 自动更新主页使用的`videos.json`文件，使新视频能够立即在网站上展示。

系统被设计为**增量处理**模式，只对新增或被修改过的视频进行处理，已存在的最新视频会被自动跳过，以提高效率。

---

## 目录结构

```
show_media/
├── auto_processor/         # 自动化系统的核心Python代码
│   ├── __init__.py
│   ├── config.py           # 配置文件加载
│   ├── file_monitor.py     # 文件监控模块 (watchdog)
│   ├── logger.py           # 日志系统
│   ├── main_processor.py   # 主处理逻辑
│   ├── template_generator.py # videos.json生成
│   └── video_processor.py  # 视频处理引擎 (ffmpeg)
│
├── auto_processor.service  # systemd服务配置文件
├── auto_processor_requirements.txt # Python依赖
├── run_auto_processor.py   # 系统主启动和管理脚本
│
├── videos/                 # 【您需要操作的目录】视频源文件存放处
├── hls_videos_optimized/   # HLS转码输出目录 (自动生成)
├── thumbnails/             # 缩略图输出目录 (自动生成)
├── logs/                   # 日志文件目录
│   └── auto_processor/
│       ├── auto_video_processor.log      # 主日志
│       └── auto_video_processor_error.log # 错误日志
│
└── videos.json             # 视频元数据文件 (自动更新)
```

---

## 如何使用

### 核心操作

**您唯一需要做的就是：将新的视频文件（如`新视频.mp4`）上传或复制到`/home/peipei/show_media/videos/`目录下。**

系统会自动完成后续所有处理。

### 安装与配置

系统首次部署时，需要进行简单的安装和配置。

1.  **安装依赖**:
    ```bash
    # 进入项目根目录
    cd /home/peipei/show_media

    # 使用apt安装Python依赖 (推荐)
    sudo apt update
    sudo apt install python3-watchdog python3-psutil -y
    
    # 或者使用pip (如果环境允许)
    # pip3 install -r auto_processor_requirements.txt
    ```

2.  **确认FFmpeg**:
    系统依赖`ffmpeg`和`ffprobe`。通常它们已经安装在您的服务器上。您可以通过以下命令检查：
    ```bash
    ffmpeg -version
    ```

### 运行方式

提供了两种运行方式：**前台测试模式**和**后台服务模式**。

#### 方式一：前台运行 (用于测试和调试)

1.  **启动服务**:
    ```bash
    cd /home/peipei/show_media
    python3 run_auto_processor.py
    ```
    此时，服务会在当前终端运行，您可以实时看到日志输出。按`Ctrl+C`可以停止服务。

2.  **仅扫描一次**:
    如果您不想启动持续监控，只想处理一下`videos`目录里现有的文件，可以运行：
    ```bash
    python3 run_auto_processor.py --scan-only
    ```

#### 方式二：部署为后台服务 (推荐的生产环境用法)

将本系统部署为`systemd`服务，可以让它开机自启，并在后台稳定运行。

1.  **部署服务文件**:
    ```bash
    # 复制service文件到系统目录
    sudo cp /home/peipei/show_media/auto_processor.service /etc/systemd/system/
    ```

2.  **重载并启动服务**:
    ```bash
    # 重载systemd，让它发现新服务
    sudo systemctl daemon-reload

    # 设为开机自启
    sudo systemctl enable auto_processor.service

    # 立即启动服务
    sudo systemctl start auto_processor.service
    ```

3.  **管理服务**:
    *   **查看状态**:
        ```bash
        sudo systemctl status auto_processor.service
        ```
        (按`q`退出查看)

    *   **实时查看日志**:
        ```bash
        sudo journalctl -u auto_processor.service -f
        ```

    *   **停止服务**:
        ```bash
        sudo systemctl stop auto_processor.service
        ```

    *   **重启服务**:
        ```bash
        sudo systemctl restart auto_processor.service
        ```

---

## 配置文件

系统的所有行为都可以通过`/home/peipei/show_media/auto_processor/config.py`中的默认配置进行调整。如果需要自定义，可以创建一个`config.json`文件放在`auto_processor`目录下，系统会优先加载它。
