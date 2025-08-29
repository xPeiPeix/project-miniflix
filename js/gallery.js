// Project Miniflix - 画廊页面脚本

// 确保全局缓存对象存在
window.ProjectMiniflix = window.ProjectMiniflix || {
    videosCache: null,
    cacheTimestamp: 0,
    CACHE_DURATION: 5 * 60 * 1000, // 5分钟缓存
    
    // 获取缓存的视频数据
    getCachedVideos: function() {
        const now = Date.now();
        if (this.videosCache && (now - this.cacheTimestamp) < this.CACHE_DURATION) {
            console.log('Using cached video data');
            return Promise.resolve(this.videosCache);
        }
        return null;
    },
    
    // 设置视频数据缓存
    setCachedVideos: function(videos) {
        this.videosCache = videos;
        this.cacheTimestamp = Date.now();
        console.log('Video data cached');
    },
    
    // 清除缓存
    clearCache: function() {
        this.videosCache = null;
        this.cacheTimestamp = 0;
        console.log('Video cache cleared');
    }
};

document.addEventListener('DOMContentLoaded', function() {
    loadVideoGallery();
});

async function loadVideoGallery() {
    const loading = document.getElementById('loading');
    const videoGrid = document.getElementById('videoGrid');
    const errorMessage = document.getElementById('errorMessage');
    
    try {
        // 获取视频数据 - 使用缓存机制
        let videos = window.ProjectMiniflix.getCachedVideos();
        
        if (!videos) {
            console.log('Loading video data from server for gallery');
            const response = await fetch('videos.json');
            if (!response.ok) {
                throw new Error(`Failed to fetch videos.json: HTTP ${response.status}`);
            }
            
            videos = await response.json();
            window.ProjectMiniflix.setCachedVideos(videos);
        } else {
            videos = await videos; // 处理 Promise 返回
        }
        
        // 隐藏加载提示
        loading.style.display = 'none';
        
        // 生成视频卡片
        if (videos.length > 0) {
            renderVideoCards(videos);
            videoGrid.style.display = 'grid';
        } else {
            throw new Error('No videos found');
        }
        
    } catch (error) {
        console.error('Error loading videos:', error);
        loading.style.display = 'none';
        errorMessage.style.display = 'block';
    }
}

function renderVideoCards(videos) {
    const videoGrid = document.getElementById('videoGrid');
    
    videos.forEach(video => {
        const card = createVideoCard(video);
        videoGrid.appendChild(card);
    });
}

function createVideoCard(video) {
    // 创建卡片容器
    const card = document.createElement('a');
    card.className = 'video-card';
    card.href = `player.html?id=${video.id}`;
    
    // 创建封面容器
    const thumbnailContainer = document.createElement('div');
    thumbnailContainer.className = 'thumbnail-container';
    
    // 创建封面图片
    const thumbnail = document.createElement('img');
    thumbnail.className = 'video-thumbnail';
    thumbnail.src = video.thumbnail;
    thumbnail.alt = video.title;
    thumbnail.loading = 'lazy';
    
    // 图片加载失败时使用默认图片
    thumbnail.onerror = function() {
        this.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxOCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuinhumikeWwgemdouWbvjwvdGV4dD48L3N2Zz4=';
    };
    
    // 创建时长标签
    const duration = document.createElement('div');
    duration.className = 'video-duration';
    duration.textContent = video.duration;
    
    // 创建视频信息容器
    const videoInfo = document.createElement('div');
    videoInfo.className = 'video-info';
    
    // 创建标题
    const title = document.createElement('h3');
    title.className = 'video-title';
    title.textContent = video.title;
    
    // 创建描述
    const description = document.createElement('p');
    description.className = 'video-description';
    description.textContent = video.description;
    
    // 组装卡片
    thumbnailContainer.appendChild(thumbnail);
    thumbnailContainer.appendChild(duration);
    
    videoInfo.appendChild(title);
    videoInfo.appendChild(description);
    
    card.appendChild(thumbnailContainer);
    card.appendChild(videoInfo);
    
    return card;
} 