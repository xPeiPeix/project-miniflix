// Project Miniflix - 播放器页面脚本

// 全局缓存对象
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
    initializeVideoPlayer();
});

async function initializeVideoPlayer() {
    const loading = document.getElementById('loading');
    const playerContainer = document.getElementById('playerContainer');
    const errorMessage = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    
    try {
        // 获取URL参数
        const urlParams = new URLSearchParams(window.location.search);
        const videoId = urlParams.get('id');
        
        if (!videoId) {
            throw new Error('缺少视频ID参数');
        }
        
        // 加载视频数据 - 使用缓存机制
        let videos = window.ProjectMiniflix.getCachedVideos();
        
        if (!videos) {
            console.log('Loading video data from server');
            const response = await fetch('videos.json');
            if (!response.ok) {
                throw new Error(`无法加载视频数据: HTTP ${response.status}`);
            }
            
            videos = await response.json();
            window.ProjectMiniflix.setCachedVideos(videos);
        } else {
            videos = await videos; // 处理 Promise 返回
        }
        const video = videos.find(v => v.id === videoId);
        
        if (!video) {
            throw new Error(`未找到ID为 "${videoId}" 的视频`);
        }
        
        // 设置视频信息
        document.getElementById('videoTitle').textContent = video.title;
        document.getElementById('videoDescription').textContent = video.description;
        document.title = `${video.title} - Project Miniflix`;
        
        // 构造优化后的HLS URL
        const optimizedHlsUrl = video.hls_url.replace('hls_videos/', 'hls_videos_optimized/');
        
        // 初始化HLS播放器
        await setupHLSPlayer(optimizedHlsUrl, video.hls_url);
        
        // 隐藏加载提示，显示播放器
        loading.style.display = 'none';
        playerContainer.style.display = 'block';
        
    } catch (error) {
        console.error('Video player error:', error);
        loading.style.display = 'none';
        
        // 设置友好的错误信息
        const errorTitle = document.getElementById('errorTitle');
        const errorActions = document.getElementById('errorActions');
        
        if (error.message.includes('网络')) {
            errorTitle.textContent = '🌐 网络连接问题';
            errorText.textContent = '网络连接不稳定，请检查网络后重试。';
            errorActions.style.display = 'flex';
        } else if (error.message.includes('HLS')) {
            errorTitle.textContent = '📺 播放器问题';
            errorText.textContent = error.message;
            errorActions.style.display = 'flex';
        } else if (error.message.includes('不支持')) {
            errorTitle.textContent = '⚠️ 浏览器兼容性问题';
            errorText.textContent = error.message;
            errorActions.style.display = 'flex';
        } else {
            errorTitle.textContent = '😔 播放失败';
            errorText.textContent = error.message || '无法加载视频，请检查网络连接或稍后再试。';
            errorActions.style.display = 'flex';
        }
        
        errorMessage.style.display = 'block';
        
        // 保存当前状态用于重试
        window.lastVideoError = {
            error: error,
            timestamp: Date.now()
        };
    }
}

async function setupHLSPlayer(hlsUrl, fallbackUrl) {
    const video = document.getElementById('videoPlayer');
    
    // 增强的HLS库加载检测
    if (typeof Hls === 'undefined') {
        console.error('HLS.js library not loaded');
        throw new Error('HLS播放器加载失败，请刷新页面重试');
    }
    
    // 检查浏览器是否支持HLS
    if (Hls.isSupported()) {
        console.log('Using HLS.js for playback with optimized settings');
        
        // 使用HLS.js - 优化后的配置
        const hls = new Hls({
            debug: false,
            enableWorker: true,
            lowLatencyMode: false,
            
            // --- 缓冲与加载策略优化 ---
            maxBufferLength: 60,          // 增加最大缓冲区长度到60秒
            maxMaxBufferLength: 180,      // 允许的最大缓冲区，防止无限缓冲
            maxBufferSize: 120 * 1000 * 1000, // 120MB的缓冲区大小
            backBufferLength: 90,         // 向后缓冲长度，支持更流畅的回退
            
            // --- 启动与预加载优化 ---
            startFragPrefetch: true,      // 启动时预取第一个分片
            maxFragLookUpTolerance: 0.25, // 寻找关键帧的容忍度，加速seek
            
            // --- 并发与网络优化 ---
            fragLoadingMaxRetry: 5,       // 分片加载重试次数
            levelLoadingMaxRetry: 3,      // 播放列表加载重试次数
            
            // --- 实验性功能，提升性能 ---
            p2p_enabled: false, // 如果未来要支持P2P加速，可以开启此项
        });
        
        // 加载源
        hls.loadSource(hlsUrl);
        hls.attachMedia(video);
        
        // 设置加载超时检测
        const loadTimeout = setTimeout(() => {
            console.warn('HLS loading timeout, attempting recovery');
            if (hls && !video.readyState) {
                hls.stopLoad();
                hls.startLoad();
            }
        }, 15000);
        
        // 监听HLS事件
        hls.on(Hls.Events.MANIFEST_PARSED, function() {
            clearTimeout(loadTimeout);
            console.log('HLS manifest loaded successfully');
            if (hls.levels && hls.levels.length > 0) {
                console.log('Available quality levels:', hls.levels.length);
            }
        });
        
        // 增强的错误处理
        hls.on(Hls.Events.ERROR, function(event, data) {
            console.error('HLS error occurred:', {
                type: data.type,
                details: data.details,
                fatal: data.fatal,
                url: data.url,
                response: data.response
            });
            
            if (data.fatal) {
                clearTimeout(loadTimeout);

                // 尝试使用原始(未优化)的URL进行恢复
                if (fallbackUrl) {
                    console.warn(`Optimized URL failed. Attempting fallback to: ${fallbackUrl}`);
                    hls.destroy(); // 销毁当前实例
                    // 递归调用，但移除fallbackUrl避免无限循环
                    setupHLSPlayer(fallbackUrl, null); 
                    return; // 终止当前错误处理流程
                }
                
                switch (data.type) {
                    case Hls.ErrorTypes.NETWORK_ERROR:
                        console.log('Network error - attempting recovery');
                        setTimeout(() => {
                            if (hls && !hls.destroyed) {
                                hls.startLoad();
                            }
                        }, 1000);
                        break;
                        
                    case Hls.ErrorTypes.MEDIA_ERROR:
                        console.log('Media error - attempting recovery');
                        setTimeout(() => {
                            if (hls && !hls.destroyed) {
                                hls.recoverMediaError();
                            }
                        }, 1000);
                        break;
                        
                    default:
                        console.log('Fatal error - falling back to native playback');
                        hls.destroy();
                        window.hlsPlayer = null;
                        
                        // 尝试降级到原生播放
                        if (video.canPlayType('application/vnd.apple.mpegurl')) {
                            console.log('Falling back to native HLS support');
                            video.src = hlsUrl;
                        } else {
                            throw new Error('播放器遇到严重错误，且浏览器不支持原生HLS播放');
                        }
                        break;
                }
            } else {
                // 非致命错误，记录但继续播放
                console.warn('Non-fatal HLS error:', data.details);
            }
        });
        
        // 保存hls实例以便后续使用
        window.hlsPlayer = hls;
        
        // 监听视频加载事件
        video.addEventListener('loadedmetadata', function() {
            clearTimeout(loadTimeout);
            console.log('Video metadata loaded via HLS.js');
        });
        
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        // 原生HLS支持（Safari等）
        console.log('Using native HLS support');
        video.src = hlsUrl;
        
        video.addEventListener('loadedmetadata', function() {
            console.log('Video metadata loaded via native HLS');
        });
        
        video.addEventListener('error', function(e) {
            console.error('Native HLS playback error:', e);
            throw new Error('原生HLS播放失败');
        });
        
    } else {
        console.error('No HLS support available');
        throw new Error('您的浏览器不支持HLS视频播放，请使用最新版本的Chrome、Firefox或Safari');
    }
    
    // 增强的视频事件监听器
    video.addEventListener('loadstart', function() {
        console.log('Video load started');
    });
    
    video.addEventListener('progress', function() {
        if (video.buffered.length > 0) {
            const bufferedEnd = video.buffered.end(video.buffered.length - 1);
            const duration = video.duration;
            if (duration > 0) {
                const bufferedPercent = (bufferedEnd / duration) * 100;
                console.log(`Video buffered: ${bufferedPercent.toFixed(1)}%`);
            }
        }
    });
    
    video.addEventListener('canplay', function() {
        console.log('Video can start playing');
    });
    
    video.addEventListener('waiting', function() {
        console.log('Video is waiting for more data');
    });
    
    video.addEventListener('playing', function() {
        console.log('Video started playing');
    });
    
    video.addEventListener('error', function(e) {
        console.error('Video element error:', {
            error: e,
            code: video.error ? video.error.code : 'unknown',
            message: video.error ? video.error.message : 'unknown error'
        });
        
        // 提供更友好的错误信息
        let errorMessage = '视频播放出错';
        if (video.error) {
            switch (video.error.code) {
                case 1:
                    errorMessage = '视频加载被用户中止';
                    break;
                case 2:
                    errorMessage = '网络错误导致视频下载失败';
                    break;
                case 3:
                    errorMessage = '视频解码失败';
                    break;
                case 4:
                    errorMessage = '视频格式不受支持';
                    break;
                default:
                    errorMessage = '未知的播放错误';
            }
        }
        
        throw new Error(errorMessage);
    });
}

// 页面卸载时清理资源
window.addEventListener('beforeunload', function() {
    console.log('Page unloading, cleaning up resources');
    
    // 清理HLS播放器
    if (window.hlsPlayer) {
        try {
            window.hlsPlayer.destroy();
            window.hlsPlayer = null;
            console.log('HLS player destroyed');
        } catch (error) {
            console.warn('Error destroying HLS player:', error);
        }
    }
    
    // 清理视频元素
    const video = document.getElementById('videoPlayer');
    if (video) {
        try {
            video.pause();
            video.removeAttribute('src');
            video.load();
            console.log('Video element cleaned up');
        } catch (error) {
            console.warn('Error cleaning up video element:', error);
        }
    }
    
    // 清理缓存（如果需要）
    if (window.ProjectMiniflix) {
        window.ProjectMiniflix.clearCache();
    }
});

// 页面隐藏时暂停播放（节省资源）
document.addEventListener('visibilitychange', function() {
    const video = document.getElementById('videoPlayer');
    if (video) {
        if (document.hidden) {
            if (!video.paused) {
                video.pause();
                video.dataset.wasPlaying = 'true';
                console.log('Video paused due to page visibility change');
            }
        } else {
            if (video.dataset.wasPlaying === 'true') {
                video.play().catch(e => {
                    console.warn('Auto-resume failed:', e);
                });
                delete video.dataset.wasPlaying;
                console.log('Video resumed after page became visible');
            }
        }
    }
});

// 重试视频加载功能
function retryVideo() {
    console.log('Retrying video load...');
    
    // 隐藏错误信息
    const errorMessage = document.getElementById('errorMessage');
    const loading = document.getElementById('loading');
    const playerContainer = document.getElementById('playerContainer');
    
    errorMessage.style.display = 'none';
    playerContainer.style.display = 'none';
    loading.style.display = 'block';
    
    // 清理当前状态
    if (window.hlsPlayer) {
        try {
            window.hlsPlayer.destroy();
            window.hlsPlayer = null;
        } catch (e) {
            console.warn('Error destroying HLS player during retry:', e);
        }
    }
    
    // 清理视频元素
    const video = document.getElementById('videoPlayer');
    if (video) {
        video.pause();
        video.removeAttribute('src');
        video.load();
    }
    
    // 清除缓存，强制重新加载
    if (window.ProjectMiniflix) {
        window.ProjectMiniflix.clearCache();
    }
    
    // 重新初始化播放器
    setTimeout(() => {
        initializeVideoPlayer();
    }, 500);
}

// 网络状态检测
if ('onLine' in navigator) {
    window.addEventListener('online', function() {
        console.log('Network back online');
        const errorMessage = document.getElementById('errorMessage');
        if (errorMessage.style.display !== 'none') {
            const errorText = document.getElementById('errorText');
            errorText.textContent = '网络已恢复，点击重试按钮重新加载视频。';
        }
    });
    
    window.addEventListener('offline', function() {
        console.log('Network went offline');
        const errorMessage = document.getElementById('errorMessage');
        const errorTitle = document.getElementById('errorTitle');
        const errorText = document.getElementById('errorText');
        
        if (errorMessage.style.display !== 'none') {
            errorTitle.textContent = '📱 网络已断开';
            errorText.textContent = '检测到网络连接已断开，请检查网络设置。';
        }
    });
} 