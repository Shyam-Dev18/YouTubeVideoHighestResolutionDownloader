"""
YouTube video downloader module.
"""

import logging
import socket
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from urllib.error import URLError

import yt_dlp
from yt_dlp.utils import DownloadError as YTDLError

from app.config.settings import Settings
from app.utils.exceptions import DownloadError, ConfigurationError
from app.utils.helpers import get_video_path, format_size, format_duration

class YouTubeDownloader:
    """Handles downloading videos from YouTube."""
    
    def __init__(self, settings: Settings):
        """
        Initialize the downloader.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self._validate_ffmpeg()
        
    def _validate_ffmpeg(self) -> None:
        """
        Validate FFmpeg installation.
        
        Raises:
            ConfigurationError: If FFmpeg is not found
        """
        try:
            ffmpeg_path = self.settings.FFMPEG_PATH
            ffprobe_path = self.settings.FFPROBE_PATH
            
            if not ffmpeg_path.exists():
                raise ConfigurationError(
                    f"FFmpeg not found at {ffmpeg_path}. "
                    "Please ensure FFmpeg is in the ffmpeg directory."
                )
            
            if not ffprobe_path.exists():
                raise ConfigurationError(
                    f"FFprobe not found at {ffprobe_path}. "
                    "Please ensure FFprobe is in the ffmpeg directory."
                )
                
            self.logger.debug(f"Found FFmpeg at: {ffmpeg_path}")
            self.logger.debug(f"Found FFprobe at: {ffprobe_path}")
            
        except Exception as e:
            raise ConfigurationError(f"FFmpeg validation failed: {str(e)}")
    
    def _get_ydl_opts(self, progress_hook: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Get yt-dlp options.
        
        Args:
            progress_hook: Optional callback for download progress
            
        Returns:
            Dictionary of yt-dlp options
        """
        opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
            'outtmpl': '%(id)s.%(ext)s',
            'retries': self.settings.MAX_RETRIES,
            'socket_timeout': 30,
            'extract_flat': True,
            'ignoreerrors': True,
            'ffmpeg_location': str(self.settings.FFMPEG_DIR)  # Point to directory containing ffmpeg
        }
        
        if progress_hook:
            opts['progress_hooks'] = [progress_hook]
            
        return opts
    
    async def get_video_info(self, video_url: str) -> Dict[str, Any]:
        """
        Get video metadata without downloading.
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            Dictionary containing video metadata
            
        Raises:
            DownloadError: If metadata extraction fails
        """
        try:
            with yt_dlp.YoutubeDL(self._get_ydl_opts()) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                if not info:
                    raise DownloadError("Failed to extract video information")
                
                if 'entries' in info:
                    raise DownloadError("URL appears to be a playlist. Please provide a single video URL.")
                
                # Check for common issues
                if info.get('is_live', False):
                    raise DownloadError("Live streams are not supported")
                    
                if info.get('age_limit', 0) > 0:
                    raise DownloadError("Age-restricted videos are not supported")
                
                # Format metadata according to requirements
                tags = ', '.join(info.get('tags', [])) if info.get('tags') else ''
                category = info.get('categories', [''])[0] if info.get('categories') else ''
                
                # Return only required metadata
                return {
                    'id': info['id'],
                    'title': info['title'],
                    'description': info.get('description', ''),
                    'tags': tags,
                    'category': category,
                    'thumbnail': info.get('thumbnail', '')
                }
                
        except YTDLError as e:
            if "Video unavailable" in str(e):
                raise DownloadError("Video is unavailable or has been removed")
            elif "Private video" in str(e):
                raise DownloadError("This video is private")
            elif "Sign in to confirm your age" in str(e):
                raise DownloadError("Age-restricted video - cannot download")
            else:
                raise DownloadError(f"YouTube-DL error: {str(e)}")
                
        except URLError as e:
            raise DownloadError(f"Network error: {str(e)}")
            
        except socket.timeout:
            raise DownloadError("Connection timed out. Please check your internet connection.")
            
        except Exception as e:
            raise DownloadError(f"Failed to get video info: {str(e)}")
    
    async def download_video(
        self,
        video_url: str,
        metadata: Dict[str, Any],
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Path:
        """
        Download a video from YouTube.
        
        Args:
            video_url: YouTube video URL
            metadata: Video metadata from get_video_info
            progress_callback: Optional callback for download progress
            
        Returns:
            Path to downloaded video file
            
        Raises:
            DownloadError: If download fails
        """
        def progress_hook(d):
            if d['status'] == 'downloading':
                if progress_callback and 'total_bytes' in d:
                    progress = d['downloaded_bytes'] / d['total_bytes']
                    progress_callback(progress)
            elif d['status'] == 'error':
                self.logger.error(f"Download error: {d.get('error')}")
            elif d['status'] == 'finished':
                self.logger.info("Download completed, now processing...")
        
        try:
            # Get temporary file path
            temp_path = get_video_path(
                metadata['id'],
                metadata['title'],
                self.settings.VIDEO_DIR,
                temp=True
            )
            
            # Ensure temp directory exists
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Configure yt-dlp options
            ydl_opts = self._get_ydl_opts(progress_hook)
            ydl_opts['outtmpl'] = str(temp_path)
            
            # Download video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.logger.info(f"Downloading video: {metadata['title']}")
                try:
                    ydl.download([video_url])
                except YTDLError as e:
                    if "No video formats found" in str(e):
                        raise DownloadError("No suitable video formats found for download")
                    elif "Unsupported URL" in str(e):
                        raise DownloadError("URL is not supported")
                    else:
                        raise DownloadError(f"Download failed: {str(e)}")
            
            # Move to final location if download successful
            final_path = get_video_path(
                metadata['id'],
                metadata['title'],
                self.settings.PROCESSED_DIR
            )
            final_path.parent.mkdir(parents=True, exist_ok=True)
            
            if temp_path.exists():
                if temp_path.stat().st_size == 0:
                    raise DownloadError("Downloaded file is empty")
                    
                temp_path.rename(final_path)
                self.logger.info(f"Video saved to: {final_path}")
                return final_path
            else:
                raise DownloadError("Download completed but file not found")
                
        except URLError as e:
            raise DownloadError(f"Network error during download: {str(e)}")
            
        except socket.timeout:
            raise DownloadError("Download timed out. Please check your internet connection.")
            
        except OSError as e:
            raise DownloadError(f"File system error: {str(e)}")
            
        except Exception as e:
            raise DownloadError(f"Failed to download video: {str(e)}")
            
    async def cleanup(self, video_path: Path) -> None:
        """
        Clean up downloaded video file.
        
        Args:
            video_path: Path to video file to delete
            
        Raises:
            DownloadError: If cleanup fails
        """
        try:
            if video_path.exists():
                video_path.unlink()
                self.logger.info(f"Deleted video file: {video_path}")
                
        except OSError as e:
            raise DownloadError(f"Failed to delete video file: {str(e)}") 