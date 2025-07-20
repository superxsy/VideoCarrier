import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

from app.downloader import YouTubeDownloader
from app.models import VideoInfo, DownloadResult


class TestYouTubeDownloader:
    """YouTube下载器测试类"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def downloader(self, temp_dir):
        """创建下载器实例"""
        return YouTubeDownloader(download_path=temp_dir)
    
    def test_validate_url_valid_youtube_urls(self, downloader):
        """测试有效的YouTube URL验证"""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "https://www.youtube.com/v/dQw4w9WgXcQ",
            "http://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "www.youtube.com/watch?v=dQw4w9WgXcQ",
            "youtube.com/watch?v=dQw4w9WgXcQ"
        ]
        
        for url in valid_urls:
            assert downloader.validate_url(url), f"URL should be valid: {url}"
    
    def test_validate_url_invalid_urls(self, downloader):
        """测试无效URL验证"""
        invalid_urls = [
            "https://www.bilibili.com/video/BV1234567890",
            "https://www.google.com",
            "not_a_url",
            "",
            "https://youtube.com/invalid",
            "https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMHjMZOz59Oq8B9yQe"
        ]
        
        for url in invalid_urls:
            assert not downloader.validate_url(url), f"URL should be invalid: {url}"
    
    @pytest.mark.asyncio
    async def test_get_video_info_success(self, downloader):
        """测试成功获取视频信息"""
        mock_info = {
            'id': 'dQw4w9WgXcQ',
            'title': 'Rick Astley - Never Gonna Give You Up',
            'description': 'Official video description',
            'duration': 212,
            'view_count': 1000000,
            'like_count': 50000,
            'uploader': 'RickAstleyVEVO',
            'uploader_id': 'RickAstleyVEVO',
            'upload_date': '20091025',
            'thumbnail': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
            'tags': ['music', 'pop'],
            'categories': ['Music'],
            'formats': [
                {'height': 720, 'ext': 'mp4'},
                {'height': 1080, 'ext': 'mp4'}
            ],
            'subtitles': {'en': [], 'zh-CN': []},
            'automatic_captions': {'en': [], 'zh-CN': []}
        }
        
        with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl
            mock_ydl.extract_info.return_value = mock_info
            
            url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            info = await downloader.get_video_info(url)
            
            assert isinstance(info, VideoInfo)
            assert info.id == 'dQw4w9WgXcQ'
            assert info.title == 'Rick Astley - Never Gonna Give You Up'
            assert info.duration == 212
            assert info.view_count == 1000000
            assert info.channel == 'RickAstleyVEVO'
            assert '720p' in info.available_qualities
            assert '1080p' in info.available_qualities
            assert 'en' in info.available_subtitles
            assert 'zh-CN' in info.available_subtitles
    
    @pytest.mark.asyncio
    async def test_get_video_info_failure(self, downloader):
        """测试获取视频信息失败"""
        with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl
            mock_ydl.extract_info.side_effect = Exception("Video not found")
            
            url = "https://www.youtube.com/watch?v=invalid"
            
            with pytest.raises(Exception, match="Video not found"):
                await downloader.get_video_info(url)
    
    def test_download_video_success(self, downloader, temp_dir):
        """测试成功下载视频"""
        mock_info = {
            'id': 'test_video',
            'title': 'Test Video',
            'description': 'Test description',
            'duration': 120,
            'view_count': 1000,
            'like_count': 100,
            'uploader': 'TestChannel',
            'uploader_id': 'testchannel',
            'upload_date': '20231201',
            'thumbnail': 'https://example.com/thumb.jpg',
            'tags': ['test'],
            'categories': ['Education']
        }
        
        # 创建模拟的下载文件
        video_file = Path(temp_dir) / "test_video.mp4"
        subtitle_file = Path(temp_dir) / "test_video.zh-CN.srt"
        thumbnail_file = Path(temp_dir) / "test_video.jpg"
        
        video_file.write_text("fake video content")
        subtitle_file.write_text("fake subtitle content")
        thumbnail_file.write_text("fake thumbnail content")
        
        with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl
            mock_ydl.extract_info.return_value = mock_info
            mock_ydl.download.return_value = None
            
            url = "https://www.youtube.com/watch?v=test_video"
            result = downloader.download_video(
                url=url,
                quality="best",
                audio_only=False,
                subtitle_langs=["zh-CN"]
            )
            
            assert isinstance(result, DownloadResult)
            assert result.video_path == str(video_file)
            assert result.subtitle_paths["zh-CN"] == str(subtitle_file)
            assert result.thumbnail_path == str(thumbnail_file)
            assert result.metadata.id == "test_video"
            assert result.file_size > 0
    
    def test_download_video_audio_only(self, downloader, temp_dir):
        """测试仅下载音频"""
        mock_info = {
            'id': 'test_audio',
            'title': 'Test Audio',
            'uploader': 'TestChannel'
        }
        
        # 创建模拟的音频文件
        audio_file = Path(temp_dir) / "test_audio.m4a"
        audio_file.write_text("fake audio content")
        
        with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl
            mock_ydl.extract_info.return_value = mock_info
            mock_ydl.download.return_value = None
            
            url = "https://www.youtube.com/watch?v=test_audio"
            result = downloader.download_video(
                url=url,
                audio_only=True
            )
            
            assert result.audio_path == str(audio_file)
            assert result.video_path is None
    
    def test_download_video_failure(self, downloader):
        """测试下载失败"""
        with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl
            mock_ydl.extract_info.side_effect = Exception("Download failed")
            
            url = "https://www.youtube.com/watch?v=invalid"
            
            with pytest.raises(Exception, match="Download failed"):
                downloader.download_video(url)
    
    def test_cleanup_old_files(self, downloader, temp_dir):
        """测试清理旧文件"""
        # 创建一些测试文件
        old_file = Path(temp_dir) / "old_file.mp4"
        new_file = Path(temp_dir) / "new_file.mp4"
        
        old_file.write_text("old content")
        new_file.write_text("new content")
        
        # 修改旧文件的时间戳
        import time
        old_time = time.time() - 25 * 3600  # 25小时前
        os.utime(old_file, (old_time, old_time))
        
        # 执行清理（清理24小时前的文件）
        downloader.cleanup_old_files(max_age_hours=24)
        
        # 验证结果
        assert not old_file.exists(), "Old file should be deleted"
        assert new_file.exists(), "New file should remain"
    
    def test_get_download_stats(self, downloader, temp_dir):
        """测试获取下载统计信息"""
        # 创建一些测试文件
        file1 = Path(temp_dir) / "file1.mp4"
        file2 = Path(temp_dir) / "file2.mp4"
        
        file1.write_text("content1" * 100)  # 800 bytes
        file2.write_text("content2" * 200)  # 1600 bytes
        
        stats = downloader.get_download_stats()
        
        assert stats["total_files"] == 2
        assert stats["total_size_bytes"] == 2400
        assert stats["total_size_mb"] == round(2400 / (1024 * 1024), 2)
        assert stats["download_path"] == temp_dir
    
    def test_progress_callback(self, downloader):
        """测试进度回调功能"""
        progress_data = []
        
        def mock_progress_callback(d):
            progress_data.append(d)
        
        mock_info = {
            'id': 'test_progress',
            'title': 'Test Progress Video'
        }
        
        with patch('yt_dlp.YoutubeDL') as mock_ydl_class:
            mock_ydl = MagicMock()
            mock_ydl_class.return_value.__enter__.return_value = mock_ydl
            mock_ydl.extract_info.return_value = mock_info
            
            # 模拟下载过程中的进度回调
            def mock_download(urls):
                # 模拟进度更新
                mock_progress_callback({
                    'status': 'downloading',
                    'downloaded_bytes': 1024,
                    'total_bytes': 2048,
                    'filename': 'test.mp4'
                })
                mock_progress_callback({
                    'status': 'finished',
                    'filename': 'test.mp4'
                })
            
            mock_ydl.download.side_effect = mock_download
            
            url = "https://www.youtube.com/watch?v=test_progress"
            downloader.download_video(
                url=url,
                progress_callback=mock_progress_callback
            )
            
            # 验证进度回调被调用
            assert len(progress_data) == 2
            assert progress_data[0]['status'] == 'downloading'
            assert progress_data[1]['status'] == 'finished'