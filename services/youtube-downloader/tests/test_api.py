import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
import json

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
        assert "timestamp" in data
        assert "version" in data
        assert "uptime_seconds" in data
    
    def test_root_endpoint(self, client):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "service" in data
        assert "version" in data
        assert "docs_url" in data
    
    @patch('app.main.download_video_task.delay')
    def test_download_video_success(self, mock_task, client):
        """测试成功提交下载任务"""
        # 模拟Celery任务
        mock_result = Mock()
        mock_result.id = "test-task-id-123"
        mock_task.return_value = mock_result
        
        request_data = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "quality": "720p",
            "audio_only": False,
            "subtitle_langs": ["en", "zh-CN"]
        }
        
        response = client.post("/download", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == "test-task-id-123"
        assert data["status"] == "pending"
        assert "message" in data
        
        # 验证任务被正确调用
        mock_task.assert_called_once_with(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            quality="720p",
            audio_only=False,
            subtitle_langs=["en", "zh-CN"]
        )
    
    def test_download_video_invalid_url(self, client):
        """测试无效URL的下载请求"""
        request_data = {
            "url": "https://www.bilibili.com/video/invalid",
            "quality": "720p"
        }
        
        response = client.post("/download", json=request_data)
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
        assert data["progress"] == 0
    
    @patch('app.main.celery_app.AsyncResult')
    def test_get_task_status_progress(self, mock_async_result, client):
        """测试获取进行中任务状态"""
        # 模拟Celery任务结果
        mock_result = Mock()
        mock_result.state = "PROGRESS"
        mock_result.info = {
            "current": 50,
            "total": 100,
            "status": "Downloading video..."
        }
        mock_async_result.return_value = mock_result
        
        response = client.get("/status/test-task-id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "progress"
        assert data["progress"] == 50
        assert data["message"] == "Downloading video..."
    
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
        assert data["status"] == "success"
        assert data["progress"] == 100
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
        assert data["status"] == "failure"
        assert data["error"] == "Download failed: Video not available"
    
    @patch('app.main.get_video_info_task.delay')
    def test_get_video_info_success(self, mock_task, client):
        """测试成功获取视频信息"""
        # 模拟Celery任务
        mock_result = Mock()
        mock_result.id = "info-task-id-123"
        mock_task.return_value = mock_result
        
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        response = client.get(f"/info?url={url}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == "info-task-id-123"
        assert data["status"] == "pending"
        
        # 验证任务被正确调用
        mock_task.assert_called_once_with(url=url)
    
    def test_get_video_info_invalid_url(self, client):
        """测试无效URL的视频信息请求"""
        url = "https://www.bilibili.com/video/invalid"
        response = client.get(f"/info?url={url}")
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "Invalid YouTube URL" in data["detail"]
    
    def test_get_video_info_missing_url(self, client):
        """测试缺少URL参数的视频信息请求"""
        response = client.get("/info")
        assert response.status_code == 422  # Validation error
    
    @patch('app.main.download_video_task.delay')
    def test_download_video_with_all_options(self, mock_task, client):
        """测试包含所有选项的下载请求"""
        # 模拟Celery任务
        mock_result = Mock()
        mock_result.id = "full-options-task-id"
        mock_task.return_value = mock_result
        
        request_data = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "quality": "1080p",
            "audio_only": False,
            "subtitle_langs": ["en", "zh-CN", "ja"],
            "download_thumbnail": True,
            "download_description": True
        }
        
        response = client.post("/download", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == "full-options-task-id"
        
        # 验证任务被正确调用
        mock_task.assert_called_once_with(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            quality="1080p",
            audio_only=False,
            subtitle_langs=["en", "zh-CN", "ja"],
            download_thumbnail=True,
            download_description=True
        )
    
    @patch('app.main.download_video_task.delay')
    def test_download_audio_only(self, mock_task, client):
        """测试仅音频下载请求"""
        # 模拟Celery任务
        mock_result = Mock()
        mock_result.id = "audio-only-task-id"
        mock_task.return_value = mock_result
        
        request_data = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "audio_only": True,
            "quality": "best"  # 对于音频，质量参数仍然有效
        }
        
        response = client.post("/download", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == "audio-only-task-id"
        
        # 验证任务被正确调用
        mock_task.assert_called_once_with(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            quality="best",
            audio_only=True,
            subtitle_langs=None,
            download_thumbnail=False,
            download_description=False
        )
    
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
        
        # 测试非常长的URL
        long_url = "https://www.youtube.com/watch?v=" + "a" * 1000
        response = client.post("/download", json={"url": long_url})
        assert response.status_code == 400  # 应该被URL验证拒绝
        
        # 测试空的字幕语言列表
        response = client.post("/download", json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "subtitle_langs": []
        })
        assert response.status_code == 200  # 空列表应该被接受