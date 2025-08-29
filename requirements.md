

### **项目需求书：个人视频展示平台 (Project Miniflix)**

#### **1. 项目概述 (Project Overview)**

本项目旨在基于用户已有的Linux公网服务器，创建一个现代化、美观、响应式的视频展示网站。网站包含一个视频画廊主页，用于陈列所有视频，以及一个独立的视频播放页面，提供流畅的HLS流媒体播放体验。

**核心目标:**

* **美观的界面**: 提供一个干净、现代、有吸引力的用户界面。
* **集中展示**: 在一个页面以“卡片”形式优雅地展示所有视频。
* **高性能播放**: 利用HLS技术实现视频的快速加载和流畅播放。
* **易于维护**: 能够方便地添加新视频，而无需修改大量前端代码。
* **响应式设计**: 确保在桌面电脑、平板和手机上都有良好的浏览和播放体验。

---

#### **2. 功能性需求 (Functional Requirements)**

**2.1. 后端与视频处理**

* **视频转码**: 所有上传的源视频文件 (`.mp4`, `.mov` 等) 必须能通过 `FFmpeg` 命令转换为HLS格式（生成 `.m3u8` 索引文件和一系列 `.ts` 切片文件）。
* **数据管理**:
    * 创建一个 `videos.json` 文件作为“数据库”，用于存储所有视频的元数据（metadata）。
    * 每个视频对象应包含以下信息：
        * `id`: 唯一标识符 (例如: "intro-to-python")
        * `title`: 视频标题 (例如: "Python入门教程")
        * `description`: 视频的简短描述。
        * `thumbnail`: 视频封面的图片链接 (例如: "/thumbnails/intro-to-python.jpg")
        * `hls_url`: 指向该视频 `.m3u8` 文件的路径 (例如: "/videos/intro-to-python/index.m3u8")
        * `duration`: 视频时长 (例如: "15:30")

**2.2. 前端 - 视频画廊页 (`index.html`)**

* **动态加载**: 页面加载时，通过JavaScript `fetch` API 读取 `videos.json` 文件的内容。
* **网格布局**:
    * 动态地将 `videos.json` 中的每一个视频渲染成一个卡片（Card）。
    * 所有卡片以响应式的网格（Grid）布局排列。在宽屏上显示多列，在手机上自动变为单列。
* **视频卡片**: 每个卡片上必须展示：
    * 视频封面图 (`thumbnail`)。
    * 视频标题 (`title`)。
    * 视频时长 (`duration`)，可以叠加在封面的右下角。
* **交互**: 点击任意一个视频卡片，应跳转到视频播放页，并通过URL参数传递该视频的 `id`。例如，点击ID为 `intro-to-python` 的视频后，页面跳转到 `player.html?id=intro-to-python`。

**2.3. 前端 - 视频播放页 (`player.html`)**

* **参数解析**: 页面加载时，JavaScript需要从URL中解析出视频 `id` 参数。
* **数据查找**: 根据获取的 `id`，在 `videos.json`（同样需要重新 `fetch`）中找到对应的视频数据。
* **播放器集成**:
    * 页面中央是一个HLS视频播放器（使用 `hls.js`）。
    * 播放器加载并播放从 `videos.json` 中找到的 `hls_url`。
    * 播放器需要有标准的控制条：播放/暂停、音量控制、全屏切换、进度条。
* **信息展示**:
    * 在播放器下方，显示当前视频的完整标题 (`title`) 和描述 (`description`)。
* **导航**: 提供一个清晰的“返回首页”或“返回画廊”的链接，方便用户回到 `index.html`。

---

#### **3. 非功能性需求 (Non-Functional Requirements)**

* **UI/UX**: 界面设计应简洁、直观，避免不必要的元素干扰。色彩搭配和谐，字体清晰易读。
* **性能**:
    * 页面加载速度要快。图片等静态资源应适当压缩。
    * 视频启播时间要短，播放过程中卡顿率要低。
* **兼容性**: 网站必须在最新版本的 Chrome, Firefox, Safari, Edge 浏览器上正常工作。
* **可维护性**: 代码结构应清晰，JavaScript、CSS、HTML分离。方便未来添加新功能或修改设计。

---

#### **4. 技术栈推荐 (Technology Stack)**

* **后端**:
    * Web服务器: **Nginx** (用于托管静态文件和HLS流)
    * 视频处理: **FFmpeg**
* **前端**:
    * 基础: **HTML5, CSS3, JavaScript (ES6+)**
    * CSS框架 (强烈推荐): **Bootstrap 5** 或 **Tailwind CSS**。这能让你快速构建出漂亮的响应式布局，无需从零开始写大量CSS。
    * 视频播放器: **HLS.js**
    * 图标库 (可选): **Font Awesome** 或 **Bootstrap Icons**，用于播放/暂停等图标。

---

#### **5. 开发实施步骤 (Development Roadmap)**

**第一阶段：环境准备与内容处理**

1.  **服务器设置**: 确保 Nginx 已安装并正确配置，能提供静态文件服务。
2.  **视频转码**:
    * 为每个源视频创建一个单独的输出目录，例如 `/var/www/html/videos/intro-to-python/`。
    * 使用 `FFmpeg` 将视频转码为HLS，并把 `.m3u8` 和 `.ts` 文件输出到对应目录。
3.  **创建封面**: 为每个视频制作一张封面图 (例如 `640x360` 的 `.jpg` 文件)，并上传到 `/var/www/html/thumbnails/` 目录。
4.  **构建数据源**: 在网站根目录 (`/var/www/html/`) 创建 `videos.json` 文件，并按照 `2.1` 中定义的格式，手动录入所有视频的信息。

**第二阶段：构建画廊页 (`index.html`)**

1.  创建 `index.html` 的基本HTML结构，引入选择的CSS框架和自定义的CSS文件。
2.  编写 `gallery.js`。使用 `fetch('videos.json')` 获取数据。
3.  在 `.then()` 回调中，遍历返回的视频数组。
4.  对于每个视频对象，动态创建HTML元素（例如 `<div>` 卡片），填充封面图、标题等信息。
5.  将生成的卡片包裹在一个链接 `<a>` 中，`href` 设置为 `player.html?id=VIDEO_ID`。
6.  使用CSS框架的网格系统来布局这些卡片。

**第三阶段：构建播放页 (`player.html`)**

1.  创建 `player.html` 的基本结构，包含一个 `<video>` 元素和用于显示标题/描述的区域。引入 `hls.js` 和自定义的 `player.js`。
2.  在 `player.js` 中：
    * 使用 `URLSearchParams` API 获取URL中的 `id`。
    * 再次 `fetch('videos.json')`。
    * 使用 `.find()` 方法在视频数组中找到与 `id` 匹配的对象。
    * 如果找到视频，则初始化 `Hls.js` 播放器，将视频的 `hls_url` 加载进去。
    * 同时，将视频的 `title` 和 `description` 填充到页面的相应位置。
    * 如果未找到视频，显示一个“视频未找到”的错误消息。

**第四阶段：样式美化与测试**

1.  编写自定义CSS (`style.css`)，调整卡片样式、页面边距、字体、颜色等，使其达到“漂亮”的标准。
2.  在多种设备（或使用浏览器的开发者工具模拟）上测试响应式布局是否正常。
3.  测试所有链接和视频播放是否流畅。

---

#### **示例 `videos.json` 文件结构**

```json
[
  {
    "id": "intro-to-python",
    "title": "Python入门快速教程",
    "description": "这是一段关于Python基础语法的快速入门介绍，适合零基础的初学者观看。内容涵盖变量、数据类型和循环。",
    "thumbnail": "/thumbnails/intro-to-python.jpg",
    "hls_url": "/videos/intro-to-python/index.m3u8",
    "duration": "15:30"
  },
  {
    "id": "nginx-basic-setup",
    "title": "Nginx 基础配置指南",
    "description": "学习如何在Linux服务器上安装和配置Nginx，作为你的第一个Web服务器。",
    "thumbnail": "/thumbnails/nginx-basic-setup.jpg",
    "hls_url": "/videos/nginx-basic-setup/index.m3u8",
    "duration": "22:05"
  },
  {
    "id": "cooking-with-ai",
    "title": "当AI开始学做菜",
    "description": "一个有趣的实验，看看AI生成的菜谱是否真的美味。",
    "thumbnail": "/thumbnails/cooking-with-ai.jpg",
    "hls_url": "/videos/cooking-with-ai/index.m3u8",
    "duration": "08:42"
  }
]
```