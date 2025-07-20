import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
import json
import httpx

from app.main import app
from app.models import DownloadRequest, VideoQuality


class TestAPI:
    """API端点测试类"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "youtube-downloader"
        assert "timestamp" in data
        assert "version" in data
    
    def test_root_endpoint(self, client):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        
        # 根端点返回HTML文件，不是JSON
        assert "text/html" in response.headers.get("content-type", "")
        assert "<!DOCTYPE html>" in response.text
    
    @patch('app.main.celery_app.send_task')
    def test_download_video_success(self, mock_task, client):
        """测试成功下载视频"""
        # 模拟任务返回
        mock_task.return_value.id = "test-task-id-123"
        
        response = client.post("/download", json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "quality": "720p",
            "audio_only": False,
            "subtitle_langs": ["en", "zh-CN"]
        })
        
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert len(data["task_id"]) == 36  # UUID length
        assert data["status"] == "pending"
        assert "message" in data
        
        # 验证任务被正确调用
        assert mock_task.called
        # send_task的第一个参数是任务名，第二个参数是kwargs
        call_kwargs = mock_task.call_args.kwargs["kwargs"]
        assert call_kwargs["url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert call_kwargs["quality"] == "720p"
        assert call_kwargs["audio_only"] == False
        assert call_kwargs["subtitle_langs"] == ["en", "zh-CN"]
    
    def test_download_video_invalid_url(self, client):
        """测试无效URL"""
        with patch('app.main.downloader.validate_url', return_value=False):
            response = client.post("/download", json={
                "url": "https://invalid-url.com"
            })
            
            assert response.status_code == 400
            
            data = response.json()
            assert "detail" in data
            assert "Invalid YouTube URL" in data["detail"]
    
    def test_download_video_missing_url(self, client):
        """测试缺少URL的下载请求"""
        request_data = {
            "quality": "720p"
        }
        
        response = client.post("/download", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_download_video_invalid_quality(self, client):
        """测试无效质量参数的下载请求"""
        request_data = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "quality": "invalid_quality"
        }
        
        response = client.post("/download", json=request_data)
        assert response.status_code == 422  # Validation error
    
    @patch('app.main.celery_app.AsyncResult')
    def test_get_task_status_pending(self, mock_async_result, client):
        """测试获取待处理任务状态"""
        # 模拟Celery任务结果
        mock_result = Mock()
        mock_result.state = "PENDING"
        mock_result.info = None
        mock_async_result.return_value = mock_result
        
        response = client.get("/status/test-task-id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "pending"
        assert "message" in data
    
    @patch('app.main.celery_app.AsyncResult')
    def test_get_task_status_progress(self, mock_async_result, client):
        """测试获取进行中任务状态"""
        # 模拟Celery任务结果
        mock_result = Mock()
        mock_result.state = "PROGRESS"
        mock_result.info = {
            "progress": 50,
            "current_step": "Downloading video"
        }
        mock_async_result.return_value = mock_result
        
        response = client.get("/status/test-task-id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "processing"
        assert data["progress"] == 50
        assert data["current_step"] == "Downloading video"
    
    @patch('app.main.celery_app.AsyncResult')
    def test_get_task_status_success(self, mock_async_result, client):
        """测试获取成功完成任务状态"""
        # 模拟Celery任务结果
        mock_result = Mock()
        mock_result.state = "SUCCESS"
        mock_result.result = {
            "video_path": "/downloads/video.mp4",
            "subtitle_paths": {"en": "/downloads/video.en.srt"},
            "thumbnail_path": "/downloads/video.jpg",
            "file_size": 1024000,
            "metadata": {
                "id": "dQw4w9WgXcQ",
                "title": "Test Video",
                "duration": 212
            }
        }
        mock_async_result.return_value = mock_result
        
        response = client.get("/status/test-task-id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "completed"
        assert "result" in data
        assert data["result"]["video_path"] == "/downloads/video.mp4"
        assert data["result"]["file_size"] == 1024000
    
    @patch('app.main.celery_app.AsyncResult')
    def test_get_task_status_failure(self, mock_async_result, client):
        """测试获取失败任务状态"""
        # 模拟Celery任务结果
        mock_result = Mock()
        mock_result.state = "FAILURE"
        mock_result.info = "Download failed: Video not available"
        mock_async_result.return_value = mock_result
        
        response = client.get("/status/test-task-id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "failed"
        assert "error" in data
    
    @patch('app.main.downloader.get_video_info')
    def test_get_video_info_success(self, mock_get_info, client):
        """测试成功获取视频信息"""
        # 模拟视频信息
        mock_info = {
            "id": "dQw4w9WgXcQ",
            "title": "Test Video",
            "duration": 212,
            "uploader": "Test Channel"
        }
        mock_get_info.return_value = mock_info
        
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        response = client.get(f"/info?url={url}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == "dQw4w9WgXcQ"
        assert data["title"] == "Test Video"
        
        # 验证方法被正确调用
        mock_get_info.assert_called_once_with(url)
    
    def test_get_video_info_invalid_url(self, client):
        """测试获取无效URL的视频信息"""
        with patch('app.main.downloader.validate_url', return_value=False):
            response = client.get("/info?url=https://invalid-url.com")
            
            assert response.status_code == 400
            
            data = response.json()
            assert "detail" in data
            assert "Invalid YouTube URL" in data["detail"]
    
    def test_get_video_info_missing_url(self, client):
        """测试缺少URL参数的视频信息请求"""
        response = client.get("/info")
        assert response.status_code == 422  # Validation error
    
    @patch('app.main.celery_app.send_task')
    def test_download_video_with_all_options(self, mock_task, client):
        """测试带所有选项的下载"""
        # 模拟任务返回
        mock_task.return_value.id = "full-options-task-id"
        
        response = client.post("/download", json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "quality": "1080p",
            "audio_only": False,
            "subtitle_langs": ["en", "zh-CN", "ja"]
        })
        
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert len(data["task_id"]) == 36  # UUID length
        
        # 验证任务被正确调用
        assert mock_task.called
        call_kwargs = mock_task.call_args.kwargs["kwargs"]
        assert call_kwargs["url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert call_kwargs["quality"] == "1080p"
        assert call_kwargs["audio_only"] == False
        assert call_kwargs["subtitle_langs"] == ["en", "zh-CN", "ja"]
    
    @patch('app.main.celery_app.send_task')
    def test_download_audio_only(self, mock_task, client):
        """测试仅音频下载"""
        # 模拟任务返回
        mock_task.return_value.id = "audio-only-task-id"
        
        response = client.post("/download", json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "audio_only": True
        })
        
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert len(data["task_id"]) == 36  # UUID length
        
        # 验证任务被正确调用
        assert mock_task.called
        call_kwargs = mock_task.call_args.kwargs["kwargs"]
        assert call_kwargs["url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert call_kwargs["audio_only"] == True
    
    def test_cors_headers(self, client):
        """测试CORS头部设置"""
        response = client.options("/download")
        # FastAPI会自动处理CORS，这里主要测试端点可访问性
        assert response.status_code in [200, 405]  # OPTIONS可能不被支持，但不应该是500错误
    
    def test_api_documentation_accessible(self, client):
        """测试API文档可访问性"""
        # 测试OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        
        # 验证主要端点在schema中
        paths = schema["paths"]
        assert "/download" in paths
        assert "/status/{task_id}" in paths
        assert "/info" in paths
        assert "/health" in paths
    
    @patch('app.main.celery_app.control.inspect')
    def test_worker_health_check(self, mock_inspect, client):
        """测试工作节点健康检查"""
        # 模拟Celery inspect结果
        mock_inspector = Mock()
        mock_inspector.active.return_value = {'worker1': []}
        mock_inspector.stats.return_value = {'worker1': {'total': 10}}
        mock_inspect.return_value = mock_inspector
        
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_request_validation_edge_cases(self, client):
        """测试请求验证的边界情况"""
        # 测试空字符串URL
        response = client.post("/download", json={"url": ""})
        assert response.status_code == 422
        
        # 测试非常长的URL（模拟验证失败）
        with patch('app.main.downloader.validate_url', return_value=False):
            long_url = "https://www.youtube.com/watch?v=" + "a" * 1000
            response = client.post("/download", json={"url": long_url})
            assert response.status_code == 400  # 应该被URL验证拒绝
        
        # 测试空的字幕语言列表
        with patch('app.main.celery_app.send_task') as mock_task:
            mock_task.return_value.id = "test-task-id"
            response = client.post("/download", json={
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "subtitle_langs": []
            })
            assert response.status_code == 200  # 空列表应该被接受