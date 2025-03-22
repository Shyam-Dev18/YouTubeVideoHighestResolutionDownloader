"""
Input validation functions for the application.
"""

import re
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs

from app.utils.exceptions import ValidationError

def validate_youtube_url(url: str) -> str:
    """
    Validate and extract video ID from YouTube URL.
    
    Args:
        url: YouTube video URL
        
    Returns:
        YouTube video ID
        
    Raises:
        ValidationError: If URL is invalid
    """
    try:
        # Clean the URL
        url = url.strip()
        
        # Handle direct video IDs (11 characters)
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
            return url
            
        # Parse the URL
        parsed_url = urlparse(url)
        
        # Handle different URL patterns
        if parsed_url.hostname in ['www.youtube.com', 'youtube.com', 'm.youtube.com']:
            # Regular videos and shorts
            if parsed_url.path in ['/watch', '/shorts']:
                video_id = parse_qs(parsed_url.query).get('v', [None])[0]
            # Shorts URLs
            elif '/shorts/' in parsed_url.path:
                video_id = parsed_url.path.split('/shorts/')[1].split('?')[0]
            # Embedded URLs
            elif parsed_url.path.startswith('/embed/'):
                video_id = parsed_url.path.split('/embed/')[1].split('?')[0]
            # Share URLs
            elif parsed_url.path.startswith('/v/'):
                video_id = parsed_url.path.split('/v/')[1].split('?')[0]
            else:
                video_id = None
        # Handle youtu.be URLs
        elif parsed_url.hostname == 'youtu.be':
            video_id = parsed_url.path.lstrip('/')
            if '?' in video_id:
                video_id = video_id.split('?')[0]
        else:
            video_id = None
            
        # Validate video ID format
        if video_id and re.match(r'^[a-zA-Z0-9_-]{11}$', video_id):
            return video_id
            
        raise ValidationError("Could not extract valid video ID from URL")
            
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(
            "Invalid YouTube URL. Please provide a valid YouTube video URL."
        )

def validate_file_exists(path: Path) -> None:
    """
    Validate that a file exists.
    
    Args:
        path: Path to the file
        
    Raises:
        ValidationError: If file doesn't exist
    """
    if not path.is_file():
        raise ValidationError(f"File not found: {path}")

def validate_directory_exists(path: Path) -> None:
    """
    Validate that a directory exists.
    
    Args:
        path: Path to the directory
        
    Raises:
        ValidationError: If directory doesn't exist
    """
    if not path.is_dir():
        raise ValidationError(f"Directory not found: {path}")

def validate_video_metadata(metadata: Dict[str, Any]) -> None:
    """
    Validate video metadata contains required fields.
    
    Args:
        metadata: Video metadata dictionary
        
    Raises:
        ValidationError: If required fields are missing
    """
    required_fields = ['id', 'title', 'duration']
    missing_fields = [field for field in required_fields if field not in metadata]
    
    if missing_fields:
        raise ValidationError(
            f"Missing required video metadata fields: {', '.join(missing_fields)}"
        )

def validate_google_credentials(creds_path: Path) -> None:
    """
    Validate Google API credentials file.
    
    Args:
        creds_path: Path to credentials file
        
    Raises:
        ValidationError: If credentials are invalid
    """
    try:
        validate_file_exists(creds_path)
        
        # Basic structure validation
        import json
        with open(creds_path) as f:
            creds = json.load(f)
        
        required_fields = [
            'type',
            'project_id',
            'private_key_id',
            'private_key',
            'client_email'
        ]
        
        missing_fields = [
            field for field in required_fields
            if field not in creds
        ]
        
        if missing_fields:
            raise ValidationError(
                f"Invalid credentials file. Missing fields: {', '.join(missing_fields)}"
            )
            
    except json.JSONDecodeError:
        raise ValidationError("Invalid credentials file format. Expected valid JSON.")
    except Exception as e:
        raise ValidationError(f"Error validating credentials: {str(e)}")

def validate_spreadsheet_id(spreadsheet_id: str) -> None:
    """
    Validate Google Sheets spreadsheet ID format.
    
    Args:
        spreadsheet_id: Spreadsheet ID to validate
        
    Raises:
        ValidationError: If ID format is invalid
    """
    if not re.match(r'^[a-zA-Z0-9-_]+$', spreadsheet_id):
        raise ValidationError("Invalid spreadsheet ID format") 