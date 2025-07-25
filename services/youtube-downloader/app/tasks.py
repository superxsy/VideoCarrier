from celery import current_task
from celery.exceptions import Retry
from typing import List, Optional, Dict, Any
import time
import os
from loguru import logger

from .celery_app import celery_app
from .downloader import YouTubeDownloader
from .models import DownloadResult

# 初始化下载器
downloader = YouTubeDownloader(download_path="downloads")





@celery_app.task(bind=True, name="app.tasks.download_video_task")
def download_video_task(
    self,
    url: str,
    quality: str = "best",
    audio_only: bool = False,
    subtitle_langs: Optional[List[str]] = None,
    download_thumbnail: bool = False,
    download_description: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """异步视频下载任务"""

    if subtitle_langs is None:
        subtitle_langs = ["zh-CN", "en"]

    # 获取任务ID
    task_id = self.request.id if self.request else 'unknown-task-id'
    start_time = time.time()

    def progress_hook(d):
        """下载进度回调"""
        if d["status"] == "downloading":
            try:
                # 计算进度百分比
                if "total_bytes" in d and d["total_bytes"]:
                    progress = int((d["downloaded_bytes"] / d["total_bytes"]) * 100)
                elif "total_bytes_estimate" in d and d["total_bytes_estimate"]:
                    progress = int(
                        (d["downloaded_bytes"] / d["total_bytes_estimate"]) * 100
                    )
                else:
                    progress = 0

                # 更新任务状态
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "progress": progress,
                        "current_step": f"Downloading: {d.get('filename', 'video')}",
                        "downloaded_bytes": d.get("downloaded_bytes", 0),
                        "total_bytes": d.get(
                            "total_bytes", d.get("total_bytes_estimate", 0)
                        ),
                        "speed": d.get("speed", 0),
                        "eta": d.get("eta", 0),
                    },
                )

                logger.info(f"Task {task_id}: Download progress {progress}%")

            except Exception as e:
                logger.error(f"Error updating progress: {str(e)}")

        elif d["status"] == "finished":
            self.update_state(
                state="PROGRESS",
                meta={
                    "progress": 100,
                    "current_step": f"Finished downloading: {d.get('filename', 'video')}",
                },
            )

    try:
        logger.info(f"Starting download task {task_id} for URL: {url}")

        # 验证URL
        if not downloader.validate_url(url):
            raise ValueError(f"Invalid YouTube URL: {url}")

        # 更新状态：开始处理
        self.update_state(
            state="PROGRESS",
            meta={
                "progress": 0,
                "current_step": "Validating URL and extracting metadata",
            },
        )

        # 执行下载
        result = downloader.download_video(
            url=url,
            quality=quality,
            audio_only=audio_only,
            subtitle_langs=subtitle_langs,
            download_thumbnail=download_thumbnail,
            download_description=download_description,
            progress_callback=progress_hook,
        )

        # 计算下载时间
        download_time = time.time() - start_time

        # 构建返回结果
        task_result = {
            "task_id": task_id,
            "status": "completed",
            "download_time": round(download_time, 2),
            "video_path": result.video_path,
            "audio_path": result.audio_path,
            "subtitle_paths": result.subtitle_paths,
            "thumbnail_path": result.thumbnail_path,
            "description_path": result.description_path,
            "file_size": result.file_size,
            "metadata": result.metadata.model_dump() if result.metadata else None,
        }

        logger.info(f"Task {task_id} completed successfully in {download_time:.2f}s")
        return task_result

    except Exception as exc:
        logger.error(f"Task {task_id} failed: {str(exc)}")

        # 重试逻辑
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task {task_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=60, max_retries=3)

        # 最终失败
        self.update_state(
            state="FAILURE", meta={"error": str(exc), "task_id": task_id, "url": url}
        )
        raise exc


@celery_app.task(name="app.tasks.cleanup_task")
def cleanup_task(max_age_hours: int = 24) -> Dict[str, Any]:
    """清理旧文件任务"""
    try:
        logger.info(
            f"Starting cleanup task, removing files older than {max_age_hours} hours"
        )

        # 获取清理前的统计信息
        stats_before = downloader.get_download_stats()

        # 执行清理
        downloader.cleanup_old_files(max_age_hours)

        # 获取清理后的统计信息
        stats_after = downloader.get_download_stats()

        result = {
            "status": "completed",
            "deleted_files": stats_before["total_files"] - stats_after["total_files"],
            "freed_space_mb": round(
                (stats_before["total_size_bytes"] - stats_after["total_size_bytes"])
                / (1024 * 1024),
                2,
            ),
            "remaining_files": stats_after["total_files"],
            "max_age_hours": max_age_hours,
        }

        logger.info(f"Cleanup completed: {result}")
        return result

    except Exception as exc:
        logger.error(f"Cleanup task failed: {str(exc)}")
        raise exc


@celery_app.task(name="app.tasks.get_video_info_task")
def get_video_info_task(url: str) -> Dict[str, Any]:
    """异步获取视频信息任务"""
    try:
        logger.info(f"Getting video info for URL: {url}")

        # 验证URL
        if not downloader.validate_url(url):
            raise ValueError(f"Invalid YouTube URL: {url}")

        # 获取视频信息（需要在同步上下文中调用）
        import asyncio
        import inspect

        info_result = downloader.get_video_info(url)
        
        # 检查是否是协程对象
        if inspect.iscoroutine(info_result):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                info = loop.run_until_complete(info_result)
            finally:
                loop.close()
        else:
            # 在测试环境中，可能直接返回结果
            info = info_result
            
        return info.model_dump()

    except Exception as exc:
        logger.error(f"Get video info task failed: {str(exc)}")
        raise exc


@celery_app.task(name="app.tasks.health_check_task")
def health_check_task() -> Dict[str, Any]:
    """健康检查任务"""
    try:
        # 检查下载目录
        download_path = downloader.download_path
        if not download_path.exists():
            raise Exception(f"Download directory does not exist: {download_path}")

        # 检查磁盘空间
        import shutil

        total, used, free = shutil.disk_usage(download_path)
        free_gb = free // (1024**3)

        if free_gb < 1:  # 少于1GB空间
            logger.warning(f"Low disk space: {free_gb}GB remaining")

        # 获取统计信息
        stats = downloader.get_download_stats()

        # 计算磁盘使用百分比
        used_percent = round((used / total) * 100, 1)
        
        # 确定状态
        status = "healthy"
        warnings = []
        if used_percent > 90:
            status = "warning"
            warnings.append("Low disk space")
        
        return {
            "status": status,
            "disk_usage": {
                "free_gb": round(free / (1024**3), 1),
                "used_percent": used_percent,
            },
            "download_stats": stats,
            "warnings": warnings,
            "timestamp": time.time(),
        }

    except Exception as exc:
        logger.error(f"Health check failed: {str(exc)}")
        return {"status": "unhealthy", "error": str(exc), "timestamp": time.time()}


# 定期任务配置
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # 每天凌晨2点清理旧文件
    "cleanup-old-files": {
        "task": "app.tasks.cleanup_task",
        "schedule": crontab(hour="2", minute="0"),
        "args": (24,),  # 清理24小时前的文件
    },
    # 每5分钟进行健康检查
    "health-check": {
        "task": "app.tasks.health_check_task",
        "schedule": crontab(minute="*/5"),
    },
}
