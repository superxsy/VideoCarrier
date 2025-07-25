import pytest
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import os
import time
from celery import current_app

from app.tasks import (
    download_video_task,
    cleanup_task,
    get_video_info_task,
    health_check_task
)
from app.models import VideoInfo, DownloadResult


class TestCeleryTasks:
    """Celery任务测试类"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @patch('app.tasks.downloader')
    def test_download_video_task_success(self, mock_downloader, temp_dir):
        """测试成功的视频下载任务"""
        # mock_downloader 已经是模拟的下载器实例
        mock_downloader.validate_url.return_value = True
        
        # 模拟下载结果
        mock_result = DownloadResult(
            video_path=f"{temp_dir}/test_video.mp4",
            audio_path=None,
            subtitle_paths={"en": f"{temp_dir}/test_video.en.srt"},
            thumbnail_path=f"{temp_dir}/test_video.jpg",
            description_path=None,
            file_size=1024000,
            metadata=VideoInfo(
                id="test_video",
                title="Test Video",
                description="Test description",
                duration=120,
                view_count=1000,
                like_count=100,
                channel="TestChannel",
                upload_date="2023-12-01",
                thumbnail_url="https://example.com/thumb.jpg",
                tags=["test"],
                categories=["Education"],
                available_qualities=["720p", "1080p"],
                available_subtitles=["en", "zh-CN"]
            )
        )
        
        mock_downloader.download_video.return_value = mock_result
        
        # 使用 apply() 方法执行任务，提供任务上下文
        result = download_video_task.apply(
            args=(),
            kwargs={
                "url": "https://www.youtube.com/watch?v=test_video",
                "quality": "720p",
                "audio_only": False,
                "subtitle_langs": ["en"]
            }
        ).result
        
        # 验证结果
        assert result["video_path"] == f"{temp_dir}/test_video.mp4"
        assert result["subtitle_paths"]["en"] == f"{temp_dir}/test_video.en.srt"
        assert result["file_size"] == 1024000
        assert result["metadata"]["title"] == "Test Video"
        
        # 验证下载器被正确调用
        mock_downloader.download_video.assert_called_once()
        call_args = mock_downloader.download_video.call_args
        assert call_args[1]['url'] == "https://www.youtube.com/watch?v=test_video"
        assert call_args[1]['quality'] == "720p"
        assert call_args[1]['audio_only'] == False
        assert call_args[1]['subtitle_langs'] == ["en"]
        assert call_args[1]['download_thumbnail'] == False
        assert call_args[1]['download_description'] == False
        assert callable(call_args[1]['progress_callback'])  # 验证progress_callback是一个函数
    
    @patch('app.tasks.downloader')
    def test_download_video_task_with_progress(self, mock_downloader):
        """测试带进度回调的视频下载任务"""
        # mock_downloader 已经是模拟的下载器实例
        mock_downloader.validate_url.return_value = True
        
        # 模拟下载结果
        mock_result = DownloadResult(
            video_path="/downloads/test.mp4",
            audio_path=None,
            subtitle_paths={},
            thumbnail_path=None,
            description_path=None,
            file_size=2048000,
            metadata=VideoInfo(
                id="test_progress",
                title="Test Progress Video",
                description="",
                duration=180,
                view_count=500,
                like_count=50,
                channel="TestChannel",
                upload_date="2023-12-01",
                thumbnail_url="",
                tags=[],
                categories=[],
                available_qualities=["720p"],
                available_subtitles=[]
            )
        )
        
        # 模拟进度回调
        def mock_download_with_progress(*args, **kwargs):
            progress_callback = kwargs.get('progress_callback')
            if progress_callback:
                # 模拟进度更新
                progress_callback({
                    'status': 'downloading',
                    'downloaded_bytes': 1024000,
                    'total_bytes': 2048000,
                    'filename': 'test.mp4'
                })
                progress_callback({
                    'status': 'finished',
                    'filename': 'test.mp4'
                })
            return mock_result
        
        mock_downloader.download_video.side_effect = mock_download_with_progress
        
        # 使用 apply() 方法执行任务
        result = download_video_task.apply(
            args=(),
            kwargs={
                "url": "https://www.youtube.com/watch?v=test_progress",
                "quality": "720p"
            }
        ).result
        
        # 验证结果
        assert result["video_path"] == "/downloads/test.mp4"
        assert result["file_size"] == 2048000
    
    @patch('app.tasks.downloader')
    def test_download_video_task_failure(self, mock_downloader):
        """测试下载任务失败"""
        # mock_downloader 已经是模拟的下载器实例
        mock_downloader.validate_url.return_value = True
        
        # 模拟下载失败
        mock_downloader.download_video.side_effect = Exception("Download failed: Video not available")
        
        # 执行任务并验证异常
        with pytest.raises(Exception, match="Download failed: Video not available"):
            download_video_task.apply(
                args=(),
                kwargs={
                    "url": "https://www.youtube.com/watch?v=invalid",
                    "quality": "720p"
                }
            ).result
    
    @patch('app.tasks.downloader')
    def test_download_video_task_audio_only(self, mock_downloader, temp_dir):
        """测试仅音频下载任务"""
        # mock_downloader 已经是模拟的下载器实例
        mock_downloader.validate_url.return_value = True
        
        # 模拟音频下载结果
        mock_result = DownloadResult(
            video_path=None,
            audio_path=f"{temp_dir}/test_audio.m4a",
            subtitle_paths={},
            thumbnail_path=None,
            description_path=None,
            file_size=512000,
            metadata=VideoInfo(
                id="test_audio",
                title="Test Audio",
                description="",
                duration=240,
                view_count=2000,
                like_count=200,
                channel="AudioChannel",
                upload_date="2023-12-01",
                thumbnail_url="",
                tags=[],
                categories=[],
                available_qualities=[],
                available_subtitles=[]
            )
        )
        
        mock_downloader.download_video.return_value = mock_result
        
        # 使用 apply() 方法执行任务
        result = download_video_task.apply(
            args=(),
            kwargs={
                "url": "https://www.youtube.com/watch?v=test_audio",
                "audio_only": True
            }
        ).result
        
        # 验证结果
        assert result["video_path"] is None
        assert result["audio_path"] == f"{temp_dir}/test_audio.m4a"
        assert result["file_size"] == 512000
        
        # 验证下载器被正确调用
        mock_downloader.download_video.assert_called_once()
        call_args = mock_downloader.download_video.call_args
        assert call_args[1]['url'] == "https://www.youtube.com/watch?v=test_audio"
        assert call_args[1]['quality'] == "best"
        assert call_args[1]['audio_only'] == True
        assert call_args[1]['subtitle_langs'] == ["zh-CN", "en"]  # 默认值
        assert call_args[1]['download_thumbnail'] == False
        assert call_args[1]['download_description'] == False
        assert callable(call_args[1]['progress_callback'])  # 验证progress_callback是一个函数
    
    @patch('app.tasks.downloader')
    def test_get_video_info_task_success(self, mock_downloader):
        """测试成功获取视频信息任务"""
        # mock_downloader 已经是模拟的下载器实例
        
        # 模拟视频信息
        mock_info = VideoInfo(
            id="info_test",
            title="Info Test Video",
            description="Test video description",
            duration=300,
            view_count=5000,
            like_count=500,
            channel="InfoChannel",
            upload_date="2023-12-01",
            thumbnail_url="https://example.com/thumb.jpg",
            tags=["info", "test"],
            categories=["Education"],
            available_qualities=["480p", "720p", "1080p"],
            available_subtitles=["en", "zh-CN", "ja"]
        )
        
        # 模拟异步方法
        async def mock_get_info(url):
            return mock_info
        
        mock_downloader.get_video_info.return_value = mock_get_info("test_url")
        
        # 执行任务
        result = get_video_info_task(url="https://www.youtube.com/watch?v=info_test")
        
        # 验证结果
        assert result["id"] == "info_test"
        assert result["title"] == "Info Test Video"
        assert result["duration"] == 300
        assert result["view_count"] == 5000
        assert result["channel"] == "InfoChannel"
        assert "720p" in result["available_qualities"]
        assert "zh-CN" in result["available_subtitles"]
    
    @patch('app.tasks.downloader')
    def test_get_video_info_task_failure(self, mock_downloader):
        """测试获取视频信息任务失败"""
        # mock_downloader 已经是模拟的下载器实例
        
        # 模拟获取信息失败
        async def mock_get_info_fail(url):
            raise Exception("Video not found")
        
        mock_downloader.get_video_info.return_value = mock_get_info_fail("test_url")
        
        # 执行任务并验证异常
        with pytest.raises(Exception, match="Video not found"):
            get_video_info_task(url="https://www.youtube.com/watch?v=invalid")
    
    @patch('app.tasks.downloader')
    def test_cleanup_task(self, mock_downloader, temp_dir):
        """测试清理任务"""
        # mock_downloader 已经是模拟的下载器实例
        
        # 模拟清理前的统计信息
        stats_before = {
            "total_files": 5,
            "total_size_bytes": 1024000,
            "total_size_mb": 1.0,
            "download_path": temp_dir
        }
        
        # 模拟清理后的统计信息
        stats_after = {
            "total_files": 4,
            "total_size_bytes": 1000000,
            "total_size_mb": 0.95,
            "download_path": temp_dir
        }
        
        # 设置get_download_stats的返回值序列
        mock_downloader.get_download_stats.side_effect = [stats_before, stats_after]
        
        # 执行清理任务
        result = cleanup_task(max_age_hours=24)
        
        # 验证结果
        assert result["status"] == "completed"
        assert result["deleted_files"] == 1  # 5 - 4 = 1
        assert result["freed_space_mb"] == 0.02  # (1024000 - 1000000) / (1024*1024) ≈ 0.02
        assert result["remaining_files"] == 4
        assert result["max_age_hours"] == 24
        
        # 验证方法被正确调用
        mock_downloader.cleanup_old_files.assert_called_once_with(24)
        assert mock_downloader.get_download_stats.call_count == 2
    
    @patch('app.tasks.downloader')
    @patch('shutil.disk_usage')
    def test_health_check_task(self, mock_disk_usage, mock_downloader, temp_dir):
        """测试健康检查任务"""
        # mock_downloader 已经是模拟的下载器实例
        
        # 模拟磁盘使用情况
        mock_disk_usage.return_value = (100 * 1024**3, 80 * 1024**3, 20 * 1024**3)  # total, used, free
        
        # 模拟下载统计
        mock_stats = {
            "total_files": 10,
            "total_size_bytes": 1024000000,
            "total_size_mb": 976.56,
            "download_path": temp_dir
        }
        mock_downloader.get_download_stats.return_value = mock_stats
        
        # 执行健康检查任务
        result = health_check_task()
        
        # 验证结果
        assert result["status"] == "healthy"
        assert result["disk_usage"]["free_gb"] == 20.0
        assert result["disk_usage"]["used_percent"] == 80.0
        assert result["download_stats"]["total_files"] == 10
        assert result["download_stats"]["total_size_mb"] == 976.56
        assert "timestamp" in result
    
    @patch('app.tasks.downloader')
    @patch('shutil.disk_usage')
    def test_health_check_task_low_disk_space(self, mock_disk_usage, mock_downloader):
        """测试磁盘空间不足的健康检查"""
        # mock_downloader 已经是模拟的下载器实例
        
        # 模拟磁盘空间不足
        mock_disk_usage.return_value = (100 * 1024**3, 95 * 1024**3, 5 * 1024**3)  # 95% used
        
        # 模拟下载统计
        mock_stats = {
            "total_files": 5,
            "total_size_bytes": 512000000,
            "total_size_mb": 488.28,
            "download_path": "/downloads"
        }
        mock_downloader.get_download_stats.return_value = mock_stats
        
        # 执行健康检查任务
        result = health_check_task()
        
        # 验证结果
        assert result["status"] == "warning"
        assert result["disk_usage"]["used_percent"] == 95.0
        assert "Low disk space" in result["warnings"]
    
    @patch('app.tasks.downloader')
    def test_download_video_task_with_all_options(self, mock_downloader, temp_dir):
        """测试包含所有选项的下载任务"""
        # mock_downloader 已经是模拟的下载器实例
        mock_downloader.validate_url.return_value = True
        
        # 模拟完整下载结果
        mock_result = DownloadResult(
            video_path=f"{temp_dir}/full_test.mp4",
            audio_path=None,
            subtitle_paths={
                "en": f"{temp_dir}/full_test.en.srt",
                "zh-CN": f"{temp_dir}/full_test.zh-CN.srt"
            },
            thumbnail_path=f"{temp_dir}/full_test.jpg",
            description_path=f"{temp_dir}/full_test.description",
            file_size=3072000,
            metadata=VideoInfo(
                id="full_test",
                title="Full Test Video",
                description="Complete test video with all options",
                duration=600,
                view_count=10000,
                like_count=1000,
                channel="FullTestChannel",
                upload_date="2023-12-01",
                thumbnail_url="https://example.com/full_thumb.jpg",
                tags=["full", "test", "complete"],
                categories=["Education", "Technology"],
                available_qualities=["480p", "720p", "1080p"],
                available_subtitles=["en", "zh-CN", "ja"]
            )
        )
        
        mock_downloader.download_video.return_value = mock_result
        
        # 使用 apply() 方法执行任务
        result = download_video_task.apply(
            args=(),
            kwargs={
                "url": "https://www.youtube.com/watch?v=full_test",
                "quality": "1080p",
                "audio_only": False,
                "subtitle_langs": ["en", "zh-CN"],
                "download_thumbnail": True,
                "download_description": True
            }
        ).result
        
        # 验证结果
        assert result["video_path"] == f"{temp_dir}/full_test.mp4"
        assert result["subtitle_paths"]["en"] == f"{temp_dir}/full_test.en.srt"
        assert result["subtitle_paths"]["zh-CN"] == f"{temp_dir}/full_test.zh-CN.srt"
        assert result["thumbnail_path"] == f"{temp_dir}/full_test.jpg"
        assert result["description_path"] == f"{temp_dir}/full_test.description"
        assert result["file_size"] == 3072000
        
        # 验证下载器被正确调用
        mock_downloader.download_video.assert_called_once()
        call_args = mock_downloader.download_video.call_args
        assert call_args[1]['url'] == "https://www.youtube.com/watch?v=full_test"
        assert call_args[1]['quality'] == "1080p"
        assert call_args[1]['audio_only'] == False
        assert call_args[1]['subtitle_langs'] == ["en", "zh-CN"]
        assert call_args[1]['download_thumbnail'] == True
        assert call_args[1]['download_description'] == True
        assert callable(call_args[1]['progress_callback'])  # 验证progress_callback是一个函数