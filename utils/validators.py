from pathlib import Path
import re
from typing import Optional
from urllib.parse import urlparse, parse_qs
from .exceptions import ValidationError, ConfigurationError
from config.config import SERVICE_ACCOUNT_FILE, FFMPEG_PATH

def extract_video_id_from_url(url: str) -> str:
    """
    Extract video ID from various YouTube URL formats.
    Supported formats:
    - Full URL: https://www.youtube.com/watch?v=VIDEO_ID
    - Short URL: https://youtu.be/VIDEO_ID
    - Embed URL: https://www.youtube.com/embed/VIDEO_ID
    - Share URL: https://youtube.com/shorts/VIDEO_ID
    - Mobile URL: https://m.youtube.com/watch?v=VIDEO_ID
    - Plain video ID
    """
    try:
        # If input is already a video ID (11 characters)
        if re.match(r'^[A-Za-z0-9_-]{11}$', url):
            return url

        # Try to parse as URL
        parsed_url = urlparse(url)
        
        # Handle youtu.be short URLs
        if parsed_url.netloc == 'youtu.be':
            return parsed_url.path.lstrip('/')
            
        # Handle youtube.com URLs
        if parsed_url.netloc in ['www.youtube.com', 'youtube.com', 'm.youtube.com']:
            # Handle /watch URLs
            if 'watch' in parsed_url.path:
                query_params = parse_qs(parsed_url.query)
                if 'v' in query_params:
                    return query_params['v'][0]
                    
            # Handle /shorts URLs
            if 'shorts' in parsed_url.path:
                return parsed_url.path.split('/')[-1]
                
            # Handle /embed URLs
            if 'embed' in parsed_url.path:
                return parsed_url.path.split('/')[-1]
        
        raise ValidationError(
            "Invalid YouTube URL format. Please provide a valid YouTube URL or video ID.\n"
            "Supported formats:\n"
            "- https://www.youtube.com/watch?v=VIDEO_ID\n"
            "- https://youtu.be/VIDEO_ID\n"
            "- https://youtube.com/shorts/VIDEO_ID\n"
            "- VIDEO_ID (11 characters)"
        )
        
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Error processing URL: {str(e)}")

def validate_youtube_url(url: str) -> str:
    """Validate YouTube URL and extract video ID"""
    if not url:
        raise ValidationError("URL cannot be empty")
    
    # Extract video ID
    video_id = extract_video_id_from_url(url.strip())
    
    # Validate video ID format
    if not re.match(r'^[A-Za-z0-9_-]{11}$', video_id):
        raise ValidationError("Invalid video ID format. YouTube video IDs are 11 characters long.")
    
    return video_id

def validate_credentials() -> bool:
    """Validate the credentials file exists and is accessible"""
    try:
        if not SERVICE_ACCOUNT_FILE.exists():
            raise FileNotFoundError(f"Credentials file '{SERVICE_ACCOUNT_FILE}' not found!")
        return True
    except Exception as e:
        raise ConfigurationError(f"Credentials validation failed: {str(e)}")

def validate_ffmpeg() -> Path:
    """Validate if ffmpeg is properly installed and accessible"""
    try:
        if not FFMPEG_PATH.exists():
            raise FileNotFoundError(f"FFmpeg not found at {FFMPEG_PATH}")
        return FFMPEG_PATH
    except Exception as e:
        raise ConfigurationError(f"FFmpeg validation failed: {str(e)}")

def validate_file_exists(file_path: Path) -> bool:
    """Validate if a file exists"""
    try:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return True
    except Exception as e:
        raise ValidationError(f"File validation failed: {str(e)}")

def validate_directory_exists(directory: Path) -> bool:
    """Validate if a directory exists"""
    try:
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        return True
    except Exception as e:
        raise ValidationError(f"Directory validation failed: {str(e)}") 