from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import HttpUrl
from loguru import logger
import os
import uuid
from typing import Dict, Any
from datetime import datetime

from .models import DownloadRequest, DownloadResponse, TaskStatus, HealthCheck
from .celery_app import celery_app
from .tasks import download_video_task
from .downloader import YouTubeDownloader

# Initialize FastAPI app
app = FastAPI(
    title="YouTube Downloader Service",
    description="Video Carrier Platform - YouTube下载服务",
    version="1.0.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/downloads", StaticFiles(directory="downloads"), name="downloads")

# Initialize downloader
downloader = YouTubeDownloader(download_path="downloads")


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "youtube-downloader",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    """前端页面"""
    return FileResponse("static/index.html")


@app.get("/test")
async def test_page():
    """测试页面"""
    return FileResponse("test_frontend.html")


@app.get("/api")
async def api_info():
    """API信息"""
    return {
        "message": "YouTube Downloader Service API",
        "docs": "/docs",
        "health": "/health",
        "frontend": "/",
    }


@app.post("/download", response_model=DownloadResponse)
async def download_video(request: DownloadRequest):
    """提交视频下载任务"""
    try:
        # 验证URL
        if not downloader.validate_url(str(request.url)):
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")

        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 提交异步任务
        task = celery_app.send_task(
            "app.tasks.download_video_task",
            kwargs={
                "task_id": task_id,
                "url": str(request.url),
                "quality": request.quality,
                "audio_only": request.audio_only,
                "subtitle_langs": request.subtitle_langs,
            },
        )

        logger.info(f"Download task submitted: {task_id} for URL: {request.url}")

        return DownloadResponse(
            task_id=task_id,
            status="pending",
            message="Download task submitted successfully",
        )

    except HTTPException:
        # 重新抛出HTTPException，保持原始状态码
        raise
    except Exception as e:
        logger.error(f"Error submitting download task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """获取任务状态"""
    try:
        # 从Celery获取任务状态
        task = celery_app.AsyncResult(task_id)

        current_time = datetime.utcnow()

        if task.state == "PENDING":
            response = {
                "task_id": task_id,
                "status": "pending",
                "message": "Task is waiting to be processed",
                "created_at": current_time,
                "updated_at": current_time,
            }
        elif task.state == "PROGRESS":
            progress = task.info.get("progress", 0) if task.info else 0
            current_step = task.info.get("current_step", "") if task.info else ""
            response = {
                "task_id": task_id,
                "status": "processing",
                "message": "Task is being processed",
                "progress": (
                    int(progress)
                    if isinstance(progress, (int, float, str))
                    and str(progress).isdigit()
                    else None
                ),
                "current_step": str(current_step) if current_step else None,
                "created_at": current_time,
                "updated_at": current_time,
            }
        elif task.state == "SUCCESS":
            result = task.result if isinstance(task.result, dict) else None
            response = {
                "task_id": task_id,
                "status": "completed",
                "message": "Task completed successfully",
                "result": result,
                "created_at": current_time,
                "updated_at": current_time,
            }
        else:  # FAILURE
            error_info = str(task.info) if task.info else "Unknown error"
            response = {
                "task_id": task_id,
                "status": "failed",
                "message": error_info,
                "error": error_info,
                "created_at": current_time,
                "updated_at": current_time,
            }

        return TaskStatus(**response)

    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/info")
async def get_video_info(url: HttpUrl):
    """获取视频信息（不下载）"""
    try:
        if not downloader.validate_url(str(url)):
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")

        info = await downloader.get_video_info(str(url))
        return info

    except HTTPException:
        # 重新抛出HTTPException，保持原始状态码
        raise
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    # 不处理HTTPException，让FastAPI自己处理
    if isinstance(exc, HTTPException):
        raise exc

    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
