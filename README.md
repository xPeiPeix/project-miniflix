# 🎬 Project Miniflix

> 一个现代化、美观、响应式的个人视频展示平台
> 
> **基于 HLS 流媒体技术 + 智能自动化处理系统**

![GitHub](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-brightgreen.svg)
![Nginx](https://img.shields.io/badge/nginx-latest-green.svg)

---

## 📋 核心特性

- 🎨 **现代化UI设计** - 响应式卡片布局，适配桌面和移动设备
- 🎞️ **HLS流媒体播放** - 基于hls.js的高性能视频播放体验
- 🤖 **智能自动处理** - 自动监控、转码、生成缩略图和更新数据库
- ⚡ **高性能架构** - Nginx + 静态文件 + 缓存优化
- 🔧 **易于维护** - 模块化代码结构，JSON数据管理
- 📱 **完全响应式** - 在各种设备上都有优秀的用户体验

---

## 🏗️ 项目架构

```mermaid
graph TD
    A["🎬 Project Miniflix<br/>视频展示平台"] --> B["📁 代码部分<br/>(上传GitHub)"]
    A --> C["💾 数据部分<br/>(本地私有，不上传)"]
    
    B --> B1["🌐 前端代码"]
    B --> B2["🤖 自动处理系统"] 
    B --> B3["📋 配置文件"]
    B --> B4["📚 文档说明"]
    
    B1 --> B11["index.html<br/>视频画廊主页"]
    B1 --> B12["player.html<br/>视频播放页面"]
    B1 --> B13["css/ 样式文件"]
    B1 --> B14["js/ JavaScript逻辑"]
    B1 --> B15["lib/ hls.js库"]
    
    B2 --> B21["auto_processor/<br/>Python处理系统"]
    B2 --> B22["run_auto_processor.py<br/>启动脚本"]
    B2 --> B23["auto_processor_requirements.txt<br/>依赖包清单"]
    
    B3 --> B31["auto_processor.service<br/>系统服务配置"]
    B3 --> B32["nginx配置示例<br/>(如果需要)"]
    
    B4 --> B41["README.md<br/>使用说明"]
    B4 --> B42["requirements.md<br/>需求文档"]
    
    C --> C1["📹 原始视频文件"]
    C --> C2["🎞️ 处理后的HLS文件"]
    C --> C3["🖼️ 视频缩略图"]
    C --> C4["📊 视频数据库"]
    C --> C5["📝 运行日志"]
    
    C1 --> C11["videos/<br/>原始mp4等格式"]
    C2 --> C21["hls_videos_optimized/<br/>转码后的.m3u8和.ts文件"]
    C3 --> C31["thumbnails/<br/>视频封面图片"]
    C4 --> C41["videos.json<br/>视频元数据"]
    C5 --> C51["logs/<br/>系统运行日志"]
    C5 --> C52["backup/<br/>备份文件"]
    
    style B fill:#e1f5fe
    style C fill:#fff3e0
    style B1 fill:#f3e5f5
    style B2 fill:#e8f5e8
    style C1 fill:#ffebee
    style C2 fill:#ffebee
    style C3 fill:#ffebee
    style C4 fill:#ffebee
```

---

## ⚡ 工作原理

```mermaid
sequenceDiagram
    participant User as 👤 用户
    participant Web as 🌐 Web浏览器
    participant Nginx as 🚀 Nginx服务器
    participant AutoP as 🤖 自动处理系统
    participant FFmpeg as 🎬 FFmpeg
    participant JSON as 📊 videos.json

    Note over AutoP: 后台持续运行，监控视频文件夹
    
    User->>+AutoP: 1️⃣ 上传新视频文件到videos/目录
    AutoP->>+FFmpeg: 2️⃣ 自动检测到新文件，启动转码
    FFmpeg->>FFmpeg: 转换为HLS格式(.m3u8 + .ts)
    FFmpeg->>AutoP: 生成缩略图
    AutoP->>+JSON: 3️⃣ 自动更新videos.json元数据
    JSON-->>-AutoP: 更新完成
    FFmpeg-->>-AutoP: 转码完成
    AutoP-->>-User: 处理完成通知

    Note over User,JSON: 用户访问网站

    User->>+Web: 4️⃣ 访问 http://域名/
    Web->>+Nginx: 请求 index.html
    Nginx-->>-Web: 返回视频画廊页面
    Web->>+Nginx: 5️⃣ 异步请求 videos.json
    Nginx-->>-Web: 返回视频列表数据
    Web->>Web: JavaScript渲染视频卡片
    Web-->>-User: 显示视频画廊

    User->>+Web: 6️⃣ 点击某个视频
    Web->>+Nginx: 跳转到 player.html?id=xxx
    Nginx-->>-Web: 返回播放页面
    Web->>+Nginx: 请求对应的.m3u8文件
    Nginx-->>-Web: 返回HLS视频流
    Web->>Web: hls.js播放器加载视频
    Web-->>-User: 开始播放视频
```

---

## 🚀 快速开始

### 环境要求

- **Python 3.7+**
- **FFmpeg & FFprobe** (系统级安装)
- **Nginx** (推荐，也可用其他Web服务器)
- **Linux/macOS** (推荐，Windows需要额外配置)

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/xPeiPeix/project-miniflix.git
cd project-miniflix
```

2. **安装Python依赖**
```bash
pip install -r auto_processor_requirements.txt
```

3. **安装系统依赖**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg nginx

# CentOS/RHEL
sudo yum install epel-release
sudo yum install ffmpeg nginx

# macOS
brew install ffmpeg nginx
```

4. **配置目录结构**
```bash
mkdir -p videos thumbnails hls_videos_optimized logs backup
```

5. **创建初始配置**
```bash
# 复制示例配置
cp videos.json.example videos.json

# 编辑配置文件，添加您的视频信息
nano videos.json
```

### 快速启动

#### 开发测试
```bash
# 1. 启动视频处理系统
python run_auto_processor.py --test

# 2. 启动Web服务器
python -m http.server 8000
# 访问: http://localhost:8000
```

#### 生产部署
```bash
# 1. 修改配置文件
# 更新项目路径和用户
sed -i 's|/home/peipei/show_media|'$(pwd)'|g' auto_processor.service
sed -i 's|User=peipei|User='$(whoami)'|g' auto_processor.service

# 更新nginx配置路径和域名
cp nginx.conf.example nginx.conf
sed -i 's|/path/to/your/project-miniflix|'$(pwd)'|g' nginx.conf
sed -i 's|your-domain.com|localhost|g' nginx.conf

# 2. 安装为系统服务
sudo cp auto_processor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable auto_processor
sudo systemctl start auto_processor

# 3. 配置Nginx (根据系统选择一种方式)
# 方式A: 使用sites-available (Ubuntu/Debian标准)
sudo cp nginx.conf /etc/nginx/sites-available/miniflix
sudo ln -s /etc/nginx/sites-available/miniflix /etc/nginx/sites-enabled/

# 方式B: 使用conf.d (如果没有sites-available目录)
sudo cp nginx.conf /etc/nginx/conf.d/miniflix.conf

# 4. 设置权限和启动
sudo chown -R www-data:www-data $(pwd)
sudo systemctl reload nginx
```

---

## 📁 项目结构

```
project-miniflix/
├── 🌐 前端文件
│   ├── index.html              # 视频画廊主页
│   ├── player.html             # 视频播放页面
│   ├── css/
│   │   └── style.css           # 样式文件
│   ├── js/
│   │   ├── gallery.js          # 画廊逻辑
│   │   └── player.js           # 播放器逻辑
│   └── lib/
│       └── hls.min.js          # HLS.js 库
│
├── 🤖 自动处理系统
│   ├── auto_processor/         # 核心处理模块
│   │   ├── main_processor.py   # 主处理器
│   │   ├── video_processor.py  # 视频处理
│   │   ├── file_monitor.py     # 文件监控
│   │   ├── video_analyzer.py   # 视频分析
│   │   └── config.py           # 配置管理
│   ├── run_auto_processor.py   # 启动脚本
│   └── auto_processor_requirements.txt
│
├── ⚙️ 配置文件
│   ├── auto_processor.service  # Systemd服务配置
│   ├── videos.json.example     # 视频数据示例
│   └── nginx.conf.example      # Nginx配置示例
│
├── 📚 文档
│   ├── README.md               # 本文件
│   ├── requirements.md         # 详细需求文档
│   └── docs/                   # 其他文档
│
└── 📁 数据目录 (运行时创建，不上传Git)
    ├── videos/                 # 原始视频文件
    ├── hls_videos_optimized/   # HLS转码输出
    ├── thumbnails/             # 视频缩略图
    ├── videos.json             # 视频数据库
    ├── logs/                   # 系统日志
    └── backup/                 # 备份文件
```

---

## 🛠️ 开发指南

### 添加视频
```bash
# 将视频文件放入videos目录，系统会自动处理
cp your-video.mp4 videos/

# 手动扫描处理现有文件
python run_auto_processor.py --scan-only
```

### 系统管理
```bash
# 查看系统服务状态 (推荐)
sudo systemctl status auto_processor

# 查看脚本内部状态 (仅在直接运行脚本时有效)
python run_auto_processor.py --status

# 停止/启动系统服务
sudo systemctl stop auto_processor
sudo systemctl start auto_processor

# 测试模式 (需要先停止系统服务)
sudo systemctl stop auto_processor
python run_auto_processor.py --test
```

**⚠️ 重要说明**：
- 当使用systemd服务时，用 `systemctl status` 查看服务状态
- `python run_auto_processor.py --status` 只能检查脚本直接运行的状态
- 两者使用不同的状态管理机制，不要混淆

### 自定义配置
- 修改 `auto_processor/config.py` 调整视频处理参数
- 编辑 `nginx.conf.example` 配置Web服务器
- 手动编辑 `videos.json` 自定义视频信息（系统会保护用户修改）

---

## 📊 GitHub上传策略

```mermaid
graph LR
    A["📁 show_media项目"] --> B["✅ 上传到GitHub"]
    A --> C["❌ 不上传(添加到.gitignore)"]
    
    B --> B1["🌐 前端代码<br/>• index.html<br/>• player.html<br/>• css/<br/>• js/<br/>• lib/"]
    
    B --> B2["🤖 处理系统<br/>• auto_processor/<br/>• run_auto_processor.py<br/>• auto_processor_requirements.txt<br/>• auto_processor.service"]
    
    B --> B3["📋 配置模板<br/>• nginx.conf.example<br/>• .env.example<br/>• videos.json.example"]
    
    B --> B4["📚 文档<br/>• README.md<br/>• requirements.md<br/>• docs/"]
    
    C --> C1["📹 个人视频<br/>• videos/<br/>• hls_videos_optimized/<br/>• thumbnails/<br/>• videos.json"]
    
    C --> C2["🗂️ 运行数据<br/>• logs/<br/>• backup/<br/>• delete_videos/<br/>• issues/"]
    
    C --> C3["⚙️ 本地配置<br/>• .env<br/>• nginx本地配置<br/>• 个人路径相关文件"]
    
    style B fill:#c8e6c9
    style C fill:#ffcdd2
    style B1 fill:#e8f5e8
    style B2 fill:#e8f5e8
    style B3 fill:#e8f5e8
    style B4 fill:#e8f5e8
    style C1 fill:#ffebee
    style C2 fill:#ffebee
    style C3 fill:#ffebee
```

---

## 🔧 配置说明

### Nginx配置
```bash
# 1. 复制并修改配置文件
cp nginx.conf.example nginx.conf

# 2. 修改域名设置 (选择一种)
# 接受所有域名访问
sed -i 's|your-domain.com|localhost _;|g' nginx.conf

# 或指定具体域名
sed -i 's|your-domain.com|yourdomain.com|g' nginx.conf

# 3. 修改端口 (可选)
sed -i 's|listen 80;|listen 8080;|g' nginx.conf

# 4. 设置正确的权限
sudo chown -R www-data:www-data $(pwd)
sudo chmod -R 755 $(pwd)
```

### 常见Nginx问题
- **403 Forbidden**: 检查文件权限，确保nginx用户可以访问
- **sites-available不存在**: 使用 `/etc/nginx/conf.d/` 目录
- **配置测试**: 使用 `sudo nginx -t` 验证配置

### 视频处理参数
编辑 `auto_processor/config.py` 调整：
```python
"video_processing": {
    "segment_time": 3,      # HLS分片时长
    "crf": 23,             # 视频质量 (18-28，越小质量越高)
    "maxrate": "1500k"     # 最大码率
}
```

### 故障排除
```bash
# 检查服务日志
sudo journalctl -u auto_processor -f

# 检查nginx日志
sudo tail -f /var/log/nginx/error.log

# 检查文件权限
ls -la videos/ hls_videos_optimized/ thumbnails/

# 重启所有服务
sudo systemctl restart auto_processor nginx
```

---

## 🐛 常见问题 (QA)

### Q: 视频上传后没有自动处理？
**A:** 检查自动处理系统是否正在运行：
```bash
python run_auto_processor.py --status
```

### Q: 视频播放失败？
**A:** 检查以下几点：
1. HLS文件是否正确生成
2. Nginx配置是否正确
3. 浏览器是否支持HLS
4. 网络连接是否正常

### Q: 如何批量处理现有视频？
**A:** 使用扫描命令：
```bash
python run_auto_processor.py --scan-only
```

### Q: 如何修改视频质量设置？
**A:** 编辑 `auto_processor/config.py` 中的FFmpeg参数。

---

## 🤝 贡献指南

1. Fork 本项目
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

---

## 📜 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 👏 致谢

- [hls.js](https://github.com/video-dev/hls.js/) - 优秀的HLS播放器库
- [FFmpeg](https://ffmpeg.org/) - 强大的视频处理工具
- [Nginx](https://nginx.org/) - 高性能Web服务器

---

<div align="center">
**🎬 Project Miniflix - 让视频分享变得简单美好**

Made with ❤️ by nya

[⭐ Star](https://github.com/xPeiPeix/project-miniflix) | [🐛 Report Bug](https://github.com/xPeiPeix/project-miniflix/issues) | [💡 Request Feature](https://github.com/xPeiPeix/project-miniflix/issues)

</div>
