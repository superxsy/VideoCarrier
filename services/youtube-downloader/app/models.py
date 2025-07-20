from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class VideoQuality(str, Enum):
    """视频质量选项"""

    BEST = "best"
    WORST = "worst"
    HD720 = "720p"
    HD1080 = "1080p"
    HD1440 = "1440p"
    HD2160 = "2160p"


class DownloadRequest(BaseModel):
    """下载请求模型"""

    url: HttpUrl = Field(..., description="YouTube视频URL")
    quality: VideoQuality = Field(default=VideoQuality.BEST, description="视频质量")
    audio_only: bool = Field(default=False, description="仅下载音频")
    subtitle_langs: Optional[List[str]] = Field(
        default=["zh-CN", "en"], description="字幕语言列表"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "quality": "best",
                "audio_only": False,
                "subtitle_langs": ["zh-CN", "en"],
            }
        }


class DownloadResponse(BaseModel):
    """下载响应模型"""

    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="响应消息")


class TaskStatus(BaseModel):
    """任务状态模型"""

    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="状态消息")
    progress: Optional[int] = Field(default=None, description="进度百分比")
    current_step: Optional[str] = Field(default=None, description="当前步骤")
    result: Optional[Dict[str, Any]] = Field(default=None, description="任务结果")
    error: Optional[str] = Field(default=None, description="错误信息")
    created_at: Optional[datetime] = Field(default=None, description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")


class VideoInfo(BaseModel):
    """视频信息模型"""

    id: str = Field(..., description="视频ID")
    title: str = Field(..., description="视频标题")
    description: Optional[str] = Field(default=None, description="视频描述")
    duration: Optional[int] = Field(default=None, description="视频时长（秒）")
    view_count: Optional[int] = Field(default=None, description="观看次数")
    like_count: Optional[int] = Field(default=None, description="点赞数")
    channel: Optional[str] = Field(default=None, description="频道名称")
    channel_id: Optional[str] = Field(default=None, description="频道ID")
    upload_date: Optional[str] = Field(default=None, description="上传日期")
    thumbnail: Optional[str] = Field(default=None, description="缩略图URL")
    tags: Optional[List[str]] = Field(default=None, description="标签列表")
    categories: Optional[List[str]] = Field(default=None, description="分类列表")
    available_qualities: Optional[List[str]] = Field(default=None, description="可用质量")
    available_subtitles: Optional[List[str]] = Field(default=None, description="可用字幕语言")


class DownloadResult(BaseModel):
    """下载结果模型"""

    video_path: Optional[str] = Field(default=None, description="视频文件路径")
    audio_path: Optional[str] = Field(default=None, description="音频文件路径")
    subtitle_paths: Optional[Dict[str, str]] = Field(default=None, description="字幕文件路径")
    thumbnail_path: Optional[str] = Field(default=None, description="缩略图路径")
    metadata: Optional[VideoInfo] = Field(default=None, description="视频元数据")
    file_size: Optional[int] = Field(default=None, description="文件大小（字节）")
    download_time: Optional[float] = Field(default=None, description="下载耗时（秒）")


class HealthCheck(BaseModel):
    """健康检查模型"""

    status: str = Field(..., description="服务状态")
    service: str = Field(..., description="服务名称")
    timestamp: str = Field(..., description="检查时间")
    version: str = Field(..., description="服务版本")
    dependencies: Optional[Dict[str, str]] = Field(default=None, description="依赖服务状态")
