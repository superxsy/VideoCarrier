"""Pytest配置和共享fixtures

这个文件包含了所有测试共享的pytest fixtures和配置。
"""

import pytest
import tempfile
import os
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Generator, Dict, Any

from fastapi.testclient import TestClient

# 导入应用组件
from app.main import app
from app.downloader import YouTubeDownloader
from app.models import VideoInfo, DownloadResult
from tests import TEST_CONFIG, TEST_URLS, TEST_VIDEO_INFO


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """创建临时目录用于测试"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def test_download_path(temp_dir: str) -> str:
    """创建测试下载目录"""
    download_path = Path(temp_dir) / "downloads"
    download_path.mkdir(exist_ok=True)
    return str(download_path)


@pytest.fixture
def mock_downloader(test_download_path: str) -> Mock:
    """创建模拟的YouTubeDownloader实例"""
    downloader = Mock(spec=YouTubeDownloader)
    downloader.download_path = test_download_path
    
    # 设置默认的模拟行为
    downloader.validate_url.return_value = True
    downloader.get_download_stats.return_value = {
        "total_files": 0,
        "total_size_bytes": 0,
        "total_size_mb": 0.0,
        "download_path": test_download_path
    }
    
    return downloader


@pytest.fixture
def sample_video_info() -> VideoInfo:
    """创建示例视频信息"""
    return VideoInfo(**TEST_VIDEO_INFO)


@pytest.fixture
def sample_download_result(test_download_path: str, sample_video_info: VideoInfo) -> DownloadResult:
    """创建示例下载结果"""
    return DownloadResult(
        video_path=f"{test_download_path}/test_video.mp4",
        audio_path=None,
        subtitle_paths={"en": f"{test_download_path}/test_video.en.srt"},
        thumbnail_path=f"{test_download_path}/test_video.jpg",
        description_path=None,
        file_size=1024000,
        metadata=sample_video_info
    )


@pytest.fixture
def api_client() -> TestClient:
    """创建FastAPI测试客户端"""
    return TestClient(app)


@pytest.fixture
def mock_celery_task():
    """模拟Celery任务"""
    task_mock = Mock()
    task_mock.id = "test-task-id-123"
    task_mock.state = "PENDING"
    task_mock.info = None
    task_mock.result = None
    return task_mock


@pytest.fixture
def mock_redis():
    """模拟Redis连接"""
    with patch('redis.Redis') as mock_redis_class:
        mock_redis_instance = Mock()
        mock_redis_class.return_value = mock_redis_instance
        
        # 设置默认行为
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.return_value = None
        mock_redis_instance.set.return_value = True
        mock_redis_instance.delete.return_value = 1
        
        yield mock_redis_instance


@pytest.fixture
def mock_yt_dlp():
    """模拟yt-dlp"""
    with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
        mock_ydl = Mock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        
        # 设置默认的extract_info行为
        mock_ydl.extract_info.return_value = {
            'id': TEST_VIDEO_INFO['id'],
            'title': TEST_VIDEO_INFO['title'],
            'description': TEST_VIDEO_INFO['description'],
            'duration': TEST_VIDEO_INFO['duration'],
            'view_count': TEST_VIDEO_INFO['view_count'],
            'like_count': TEST_VIDEO_INFO['like_count'],
            'uploader': TEST_VIDEO_INFO['channel'],
            'uploader_id': TEST_VIDEO_INFO['channel'].lower(),
            'upload_date': TEST_VIDEO_INFO['upload_date'].replace('-', ''),
            'thumbnail': TEST_VIDEO_INFO['thumbnail_url'],
            'tags': TEST_VIDEO_INFO['tags'],
            'categories': TEST_VIDEO_INFO['categories'],
            'formats': [
                {'height': 720, 'ext': 'mp4'},
                {'height': 1080, 'ext': 'mp4'}
            ],
            'subtitles': {'en': [], 'zh-CN': []},
            'automatic_captions': {'en': [], 'zh-CN': []}
        }
        
        # 设置默认的download行为
        mock_ydl.download.return_value = None
        
        yield mock_ydl


@pytest.fixture
def create_test_files():
    """创建测试文件的工厂函数"""
    created_files = []
    
    def _create_files(directory: str, files: Dict[str, str]) -> Dict[str, Path]:
        """在指定目录创建测试文件
        
        Args:
            directory: 目标目录
            files: 文件名到内容的映射
            
        Returns:
            文件名到Path对象的映射
        """
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        
        file_paths = {}
        for filename, content in files.items():
            file_path = dir_path / filename
            file_path.write_text(content)
            file_paths[filename] = file_path
            created_files.append(file_path)
        
        return file_paths
    
    yield _create_files
    
    # 清理创建的文件
    for file_path in created_files:
        if file_path.exists():
            file_path.unlink()


@pytest.fixture
def mock_disk_usage():
    """模拟磁盘使用情况"""
    with patch('shutil.disk_usage') as mock_usage:
        # 默认返回100GB总空间，80GB已用，20GB可用
        mock_usage.return_value = (
            100 * 1024**3,  # total
            80 * 1024**3,   # used
            20 * 1024**3    # free
        )
        yield mock_usage


@pytest.fixture
def mock_environment_variables():
    """模拟环境变量"""
    original_env = os.environ.copy()
    
    # 设置测试环境变量
    test_env = {
        'TESTING': 'true',
        'CELERY_TASK_ALWAYS_EAGER': 'true',
        'CELERY_TASK_EAGER_PROPAGATES': 'true',
        'REDIS_URL': TEST_CONFIG['redis_url'],
        'DOWNLOAD_PATH': TEST_CONFIG['download_path'],
        'LOG_LEVEL': TEST_CONFIG['log_level']
    }
    
    os.environ.update(test_env)
    
    yield test_env
    
    # 恢复原始环境变量
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def valid_youtube_urls() -> list[str]:
    """返回有效的YouTube URL列表"""
    return TEST_URLS['valid'].copy()


@pytest.fixture
def invalid_youtube_urls() -> list[str]:
    """返回无效的YouTube URL列表"""
    return TEST_URLS['invalid'].copy()


@pytest.fixture(autouse=True)
def setup_test_environment(mock_environment_variables, temp_dir):
    """自动设置测试环境"""
    # 确保测试目录存在
    test_dirs = [
        'downloads',
        'logs',
        'temp'
    ]
    
    for dir_name in test_dirs:
        dir_path = Path(temp_dir) / dir_name
        dir_path.mkdir(exist_ok=True)
    
    yield
    
    # 测试后清理（如果需要）
    if TEST_CONFIG.get('cleanup_after_tests', True):
        # 这里可以添加清理逻辑
        pass


@pytest.fixture
def mock_progress_callback():
    """模拟进度回调函数"""
    progress_data = []
    
    def callback(data: Dict[str, Any]):
        progress_data.append(data)
    
    callback.progress_data = progress_data
    return callback


# 测试标记
pytestmark = [
    pytest.mark.asyncio,
]


# 测试配置钩子
def pytest_configure(config):
    """Pytest配置钩子"""
    # 注册自定义标记
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API test"
    )
    config.addinivalue_line(
        "markers", "celery: mark test as Celery task test"
    )
    config.addinivalue_line(
        "markers", "download: mark test as requiring actual downloads"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    # 为没有标记的测试添加默认标记
    for item in items:
        if not any(item.iter_markers()):
            item.add_marker(pytest.mark.unit)


def pytest_runtest_setup(item):
    """测试运行前的设置"""
    # 跳过需要网络的测试（如果在离线环境中）
    if item.get_closest_marker("network"):
        if os.environ.get("OFFLINE_TESTING", "false").lower() == "true":
            pytest.skip("Skipping network test in offline mode")
    
    # 跳过需要实际下载的测试（如果在快速测试模式中）
    if item.get_closest_marker("download"):
        if os.environ.get("FAST_TESTING", "false").lower() == "true":
            pytest.skip("Skipping download test in fast mode")