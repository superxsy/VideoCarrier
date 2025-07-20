"""YouTube Downloader Service Tests

这个包包含了YouTube下载服务的所有测试用例，包括：
- 单元测试：测试各个组件的独立功能
- 集成测试：测试组件间的交互
- API测试：测试FastAPI端点
- Celery任务测试：测试异步任务处理

测试结构：
- test_downloader.py: YouTubeDownloader类的单元测试
- test_api.py: FastAPI应用的API测试
- test_tasks.py: Celery任务的测试
- conftest.py: 共享的pytest fixtures

运行测试：
    # 运行所有测试
    pytest
    
    # 运行特定测试文件
    pytest tests/test_downloader.py
    
    # 运行特定测试类
    pytest tests/test_api.py::TestAPI
    
    # 运行特定测试方法
    pytest tests/test_downloader.py::TestYouTubeDownloader::test_validate_url_valid_youtube_urls
    
    # 运行带标记的测试
    pytest -m "not slow"
    pytest -m "unit"
    pytest -m "api"
    
    # 生成覆盖率报告
    pytest --cov=app --cov-report=html
    
    # 并行运行测试
    pytest -n auto

测试标记：
- @pytest.mark.unit: 单元测试
- @pytest.mark.integration: 集成测试
- @pytest.mark.api: API测试
- @pytest.mark.celery: Celery任务测试
- @pytest.mark.slow: 慢速测试
- @pytest.mark.network: 需要网络访问的测试
- @pytest.mark.download: 需要实际下载的测试
"""

__version__ = "1.0.0"
__author__ = "VideoCarrier Team"
__email__ = "dev@videocarrier.com"

# 测试配置
TEST_CONFIG = {
    "redis_url": "redis://localhost:6379/1",
    "download_path": "/tmp/test_downloads",
    "log_level": "DEBUG",
    "test_timeout": 300,
    "mock_downloads": True,
    "cleanup_after_tests": True
}

# 测试用的YouTube URL
TEST_URLS = {
    "valid": [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "https://www.youtube.com/v/dQw4w9WgXcQ"
    ],
    "invalid": [
        "https://www.bilibili.com/video/BV1234567890",
        "https://www.google.com",
        "not_a_url",
        "",
        "https://youtube.com/invalid"
    ]
}

# 测试用的视频信息
TEST_VIDEO_INFO = {
    "id": "dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up (Official Video)",
    "description": "The official video for Rick Astley's Never Gonna Give You Up.",
    "duration": 212,
    "view_count": 1000000000,
    "like_count": 10000000,
    "channel": "RickAstleyVEVO",
    "upload_date": "2009-10-25",
    "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    "tags": ["rick astley", "never gonna give you up", "music", "pop"],
    "categories": ["Music"],
    "available_qualities": ["144p", "240p", "360p", "480p", "720p", "1080p"],
    "available_subtitles": ["en", "zh-CN", "ja", "es", "fr"]
}

# 导出测试工具
__all__ = [
    "TEST_CONFIG",
    "TEST_URLS",
    "TEST_VIDEO_INFO"
]