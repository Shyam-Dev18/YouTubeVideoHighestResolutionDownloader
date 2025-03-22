"""
Main video processor that orchestrates the download and upload process.
"""

import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List

from app.config.settings import Settings
from app.core.downloader import YouTubeDownloader
from app.services.google_drive import GoogleDriveService
from app.services.google_sheets import GoogleSheetsService
from app.utils.exceptions import (
    YouTubeManagerError, ValidationError, ProcessingError
)
from app.utils.validators import validate_youtube_url

class VideoProcessor:
    """Main class for processing YouTube videos."""
    
    def __init__(self, settings: Settings):
        """
        Initialize the video processor.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
        self.downloader = YouTubeDownloader(settings)
        self.drive = GoogleDriveService(settings)
        self.sheets = GoogleSheetsService(settings)
        
        # Ensure directories exist
        settings.initialize_directories()
    
    async def process_video(self, video_url: str) -> None:
        """
        Process a single video URL.
        
        Args:
            video_url: YouTube video URL to process
            
        Raises:
            ProcessingError: If video processing fails
        """
        try:
            # Extract video ID and get info
            video_id = validate_youtube_url(video_url)
            video_info = await self.downloader.get_video_info(video_url)
            
            # Add to spreadsheet first
            await self.sheets.add_video(video_info)
            
            # Download the video with metadata
            video_path = await self.downloader.download_video(
                video_url,
                video_info
            )
            
            if self.settings.UPLOAD_TO_DRIVE and self.drive:
                # Upload to Drive
                file_id = await self.drive.upload_file(
                    video_path,
                    title=video_info['title']
                )
                if file_id:
                    await self.sheets.update_video_status(
                        video_id=video_id,
                        status="Completed",
                        drive_file_id=file_id,
                        title=video_info['title']
                    )
                    
                    # Delete local file if not keeping files
                    if not self.settings.KEEP_FILES:
                        video_path.unlink()
                        self.logger.info(f"Deleted local file: {video_path}")
            else:
                # Keep local file and update status as completed locally
                await self.sheets.update_video_status(
                    video_id=video_id,
                    status="Completed Locally",
                    drive_file_id=str(video_path),  # Store local file path instead of Drive ID
                    title=video_info['title']
                )
                self.logger.info(f"Video saved locally at: {video_path}")
            
            self.logger.info(f"Successfully processed video: {video_info['title']}")
            
        except Exception as e:
            raise ProcessingError(f"Processing error: {str(e)}")
    
    async def process_playlist(self, playlist_url: str) -> List[Dict[str, Any]]:
        """
        Process all videos in a playlist.
        
        Args:
            playlist_url: YouTube playlist URL
            
        Returns:
            List of processing results for each video
            
        Raises:
            ProcessingError: If processing fails
        """
        # TODO: Implement playlist processing
        raise NotImplementedError("Playlist processing not yet implemented")
    
    def _download_progress(self, progress: float) -> None:
        """
        Handle download progress updates.
        
        Args:
            progress: Progress value between 0 and 1
        """
        self.logger.info(f"Download progress: {progress:.1%}")
    
    def _upload_progress(self, progress: float) -> None:
        """
        Handle upload progress updates.
        
        Args:
            progress: Progress value between 0 and 1
        """
        self.logger.info(f"Upload progress: {progress:.1%}") 