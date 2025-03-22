"""
Application settings and configuration management.
Uses environment variables and .env file for configuration.
"""

import os
from pathlib import Path
from typing import Optional
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(encoding='utf-8')

class Settings:
    """Application settings with environment variable support."""
    
    def __init__(self):
        # Base Paths
        self.BASE_DIR = Path(__file__).parent.parent.parent
        self.STORAGE_DIR = self.BASE_DIR / "storage"
        
        # Storage Paths
        self.VIDEO_DIR = self.STORAGE_DIR / "videos"
        self.TEMP_DIR = self.VIDEO_DIR / "temp"
        self.PROCESSED_DIR = self.VIDEO_DIR / "processed"
        self.LOG_DIR = self.STORAGE_DIR / "logs"
        self.CREDENTIALS_DIR = self.STORAGE_DIR / "credentials"
        self.FFMPEG_DIR = self.BASE_DIR / "ffmpeg" / "bin"
        
        # FFmpeg Paths
        self.FFMPEG_PATH = self.FFMPEG_DIR / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")
        self.FFPROBE_PATH = self.FFMPEG_DIR / ("ffprobe.exe" if sys.platform == "win32" else "ffprobe")
        
        # Google API Settings
        self.GOOGLE_CREDS_PATH = self.CREDENTIALS_DIR / "google_creds.json"
        self.SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
        self.DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")
        
        # YouTube Settings
        self.PLAYLIST_ID = os.getenv("PLAYLIST_ID")
        
        # Processing Settings
        self.CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "52428800"))  # 50MB default
        self.MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
        self.KEEP_FILES = os.getenv("KEEP_FILES", "true").lower() == "true"
        self.UPLOAD_TO_DRIVE = os.getenv("UPLOAD_TO_DRIVE", "true").lower() == "true"
        
        # Logging Settings
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(levelname)s - [%(name)s] - %(message)s")
        
        # Validate required settings
        if not self.SPREADSHEET_ID:
            raise ValueError("SPREADSHEET_ID environment variable is required")
        if not self.DRIVE_FOLDER_ID:
            raise ValueError("DRIVE_FOLDER_ID environment variable is required")
        
    def initialize_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.VIDEO_DIR.mkdir(parents=True, exist_ok=True)
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        self.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
        self.FFMPEG_DIR.mkdir(parents=True, exist_ok=True) 