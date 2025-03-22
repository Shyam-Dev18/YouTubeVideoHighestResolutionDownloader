"""
Helper functions for common operations across the application.
"""

import logging
import sys
import re
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from app.config.settings import Settings

def setup_logging(settings: Settings) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        settings: Application settings instance
        
    Returns:
        Configured logger instance
    """
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = settings.LOG_DIR / f"youtube_manager_{timestamp}.log"
    
    # Ensure the directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging with UTF-8 encoding for file output
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(settings.LOG_FORMAT))
    
    # Configure console output with proper encoding
    console_handler = logging.StreamHandler(sys.stdout)
    if sys.platform == 'win32':
        # On Windows, ensure console can handle Unicode
        if sys.version_info >= (3, 7):
            sys.stdout.reconfigure(encoding='utf-8')  # Python 3.7+
        else:
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    console_handler.setFormatter(logging.Formatter(settings.LOG_FORMAT))
    
    # Set up the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return logging.getLogger("youtube_manager")

def sanitize_filename(filename: str) -> str:
    """
    Clean filename by removing invalid characters and limiting length.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Replace invalid characters with underscore
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove any non-ASCII characters
    filename = ''.join(char if ord(char) < 128 else '_' for char in filename)
    
    # Replace multiple underscores with single one
    filename = re.sub(r'_+', '_', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    
    # Limit length to 200 characters (including extension)
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:196] + '...' + ext
    
    return filename

def get_video_path(
    video_id: str,
    title: str,
    directory: Path,
    temp: bool = False
) -> Path:
    """
    Generate full path for video file.
    
    Args:
        video_id: YouTube video ID
        title: Video title
        directory: Base directory for video storage
        temp: Whether this is a temporary file
        
    Returns:
        Path object for the video file
    """
    clean_title = sanitize_filename(title)
    filename = f"{clean_title}_{video_id}.mp4"
    
    if temp:
        return directory / "temp" / filename
    return directory / filename

def format_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.23 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"

def format_duration(seconds: int) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string (e.g., "1:23:45")
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}" 