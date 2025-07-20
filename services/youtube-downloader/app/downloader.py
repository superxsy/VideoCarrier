import os
import re
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path
import yt_dlp
from loguru import logger

from .models import VideoInfo, DownloadResult

class YouTubeDownloader:
    """YouTube视频下载器"""
    
    def __init__(self, download_path: str = "/app/downloads"):
        self.download_path = Path(download_path)
        self.download_path.mkdir(parents=True, exist_ok=True)
        
        # yt-dlp基础配置
        self.base_opts = {
            'outtmpl': str(self.download_path / '%(id)s.%(ext)s'),
            'writesubtitles': True,
            'writeautomaticsub': True,
            'writethumbnail': True,
            'ignoreerrors': True,
            'no_warnings': False,
            'extractflat': False,
        }
        
    def validate_url(self, url: str) -> bool:
        """验证YouTube URL"""
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([\w-]+)',
            r'(?:https?://)?(?:www\.)?youtu\.be/([\w-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([\w-]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/v/([\w-]+)'
        ]
        
        for pattern in youtube_patterns:
            if re.match(pattern, url):
                return True
        return False
    
    async def get_video_info(self, url: str) -> VideoInfo:
        """获取视频信息（异步）"""
        def _extract_info():
            opts = self.base_opts.copy()
            opts.update({
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            })
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=False)
        
        try:
            # 在线程池中运行阻塞操作
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, _extract_info)
            
            # 提取可用格式信息
            available_qualities = []
            available_subtitles = []
            
            if info is not None and isinstance(info, dict) and 'formats' in info:
                qualities = set()
                for fmt in info['formats']:
                    if fmt.get('height'):
                        qualities.add(f"{fmt['height']}p")
                available_qualities = sorted(list(qualities), key=lambda x: int(x[:-1]), reverse=True)
            
            if info is not None and isinstance(info, dict) and 'subtitles' in info:
                available_subtitles = list(info['subtitles'].keys())
            if info is not None and isinstance(info, dict) and 'automatic_captions' in info:
                available_subtitles.extend(list(info['automatic_captions'].keys()))
                available_subtitles = list(set(available_subtitles))
            
            return VideoInfo(
                id=info['id'] if info and isinstance(info, dict) and 'id' in info else '',
                title=info.get('title', '') or '' if info and isinstance(info, dict) else '',
                description=info.get('description') if info and isinstance(info, dict) and info.get('description') else None,
                duration=int(info.get('duration', 0)) if info and isinstance(info, dict) and info.get('duration') is not None else None,
                view_count=int(info.get('view_count', 0)) if info and isinstance(info, dict) and info.get('view_count') is not None and str(info.get('view_count')).isdigit() else None,
                like_count=int(info.get('like_count', 0)) if info and isinstance(info, dict) and info.get('like_count') is not None and str(info.get('like_count')).isdigit() else None,
                channel=info.get('uploader') if info and isinstance(info, dict) and info.get('uploader') else None,
                channel_id=info.get('uploader_id') if info and isinstance(info, dict) and info.get('uploader_id') else None,
                upload_date=info.get('upload_date') if info and isinstance(info, dict) and info.get('upload_date') else None,
                thumbnail=info.get('thumbnail') if info and isinstance(info, dict) and info.get('thumbnail') else None,
                tags=info.get('tags') if info and isinstance(info, dict) and isinstance(info.get('tags'), list) else None,
                categories=info.get('categories') if info and isinstance(info, dict) and isinstance(info.get('categories'), list) else None,
                available_qualities=available_qualities,
                available_subtitles=available_subtitles
            )
            
        except Exception as e:
            logger.error(f"Error extracting video info: {str(e)}")
            raise
    
    def download_video(
        self, 
        url: str, 
        quality: str = "best",
        audio_only: bool = False,
        subtitle_langs: Optional[List[str]] = None,
        progress_callback=None
    ) -> DownloadResult:
        """下载视频"""
        
        if subtitle_langs is None:
            subtitle_langs = ["zh-CN", "en"]
            
        # 构建下载选项
        opts = self.base_opts.copy()
        
        # 设置质量
        if audio_only:
            opts['format'] = 'bestaudio/best'
        elif quality == "best":
            opts['format'] = 'best[height<=1080]'
        elif quality == "worst":
            opts['format'] = 'worst'
        else:
            # 解析质量设置 (如 "720p")
            height = quality.replace('p', '')
            opts['format'] = f'best[height<={height}]'
        
        # 字幕设置
        if subtitle_langs:
            opts['subtitleslangs'] = subtitle_langs
            opts['writesubtitles'] = True
            opts['writeautomaticsub'] = True
        
        # 进度回调
        if progress_callback:
            opts['progress_hooks'] = [progress_callback]
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                # 先获取信息
                info = ydl.extract_info(url, download=False)
                video_id = info.get('id') if info and isinstance(info, dict) else ''
                
                # 执行下载
                ydl.download([url])
                
                # 查找下载的文件
                video_path = None
                audio_path = None
                subtitle_paths = {}
                thumbnail_path = None
                
                # 查找视频/音频文件
                for ext in ['mp4', 'webm', 'mkv', 'm4a', 'mp3']:
                    file_path = self.download_path / f"{video_id}.{ext}"
                    if file_path.exists():
                        if ext in ['m4a', 'mp3']:
                            audio_path = str(file_path)
                        else:
                            video_path = str(file_path)
                        break
                
                # 查找字幕文件
                for lang in subtitle_langs:
                    for ext in ['vtt', 'srt']:
                        subtitle_file = self.download_path / f"{video_id}.{lang}.{ext}"
                        if subtitle_file.exists():
                            subtitle_paths[lang] = str(subtitle_file)
                            break
                
                # 查找缩略图
                for ext in ['jpg', 'png', 'webp']:
                    thumb_file = self.download_path / f"{video_id}.{ext}"
                    if thumb_file.exists():
                        thumbnail_path = str(thumb_file)
                        break
                
                # 计算文件大小
                file_size = 0
                if video_path and os.path.exists(video_path):
                    file_size = os.path.getsize(video_path)
                elif audio_path and os.path.exists(audio_path):
                    file_size = os.path.getsize(audio_path)
                
                # 构建视频信息
                video_info = VideoInfo(
                    id=info.get('id', '') or '' if info and isinstance(info, dict) else '',
                    title=info.get('title', '') or '' if info and isinstance(info, dict) else '',
                    description=info.get('description') if info and isinstance(info, dict) and info.get('description') else None,
                    duration=int(info.get('duration', 0)) if info and isinstance(info, dict) and info.get('duration') is not None else None,
                    view_count=int(info.get('view_count', 0)) if info and isinstance(info, dict) and info.get('view_count') is not None and str(info.get('view_count')).isdigit() else None,
                    like_count=int(info.get('like_count',0)) if info and isinstance(info, dict) and info.get('like_count') and str(info.get('like_count')).isdigit() else None,
                    channel=info.get('uploader') if info and isinstance(info, dict) and info.get('uploader') else None,
                    channel_id=info.get('uploader_id') if info and isinstance(info, dict) and info.get('uploader_id') else None,
                    upload_date=info.get('upload_date') if info and isinstance(info, dict) and info.get('upload_date') else None,
                    thumbnail=info.get('thumbnail') if info and isinstance(info, dict) and info.get('thumbnail') else None,
                    tags=info.get('tags') if info and isinstance(info, dict) and isinstance(info.get('tags'), list) else None,
                    categories=info.get('categories') if info and isinstance(info, dict) and isinstance(info.get('categories'), list) else None
                )
                
                return DownloadResult(
                    video_path=video_path,
                    audio_path=audio_path,
                    subtitle_paths=subtitle_paths,
                    thumbnail_path=thumbnail_path,
                    metadata=video_info,
                    file_size=file_size,
                    download_time=None  # 将在调用方计算
                )
                
        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            raise
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """清理旧文件"""
        import time
        current_time = time.time()
        
        for file_path in self.download_path.iterdir():
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_hours * 3600:
                    try:
                        file_path.unlink()
                        logger.info(f"Cleaned up old file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error cleaning up file {file_path}: {str(e)}")
    
    def get_download_stats(self) -> Dict[str, Any]:
        """获取下载统计信息"""
        total_files = 0
        total_size = 0
        
        for file_path in self.download_path.iterdir():
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size
        
        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "download_path": str(self.download_path)
        }