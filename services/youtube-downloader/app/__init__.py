"""YouTube Downloader Service

Video Carrier Platform - YouTube视频下载服务
提供基于yt-dlp的YouTube视频下载功能，支持异步任务处理和进度跟踪。

主要功能：
- YouTube URL验证和视频信息提取
- 多质量视频下载
- 字幕和缩略图下载
- 异步任务处理
- 下载进度跟踪
- 文件清理和维护
"""

__version__ = "1.0.0"
__author__ = "Video Carrier Platform Team"
__email__ = "dev@videocarrier.com"

from .main import app
from .downloader import YouTubeDownloader
from .celery_app import celery_app
from .models import (
    DownloadRequest,
    DownloadResponse,
    TaskStatus,
    VideoInfo,
    DownloadResult,
    HealthCheck,
)

__all__ = [
    "app",
    "YouTubeDownloader",
    "celery_app",
    "DownloadRequest",
    "DownloadResponse",
    "TaskStatus",
    "VideoInfo",
    "DownloadResult",
    "HealthCheck",
]
