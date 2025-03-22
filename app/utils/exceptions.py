"""
Custom exceptions for the YouTube Video Manager application.
"""

class YouTubeManagerError(Exception):
    """Base exception for all application errors."""
    pass

class ValidationError(YouTubeManagerError):
    """Raised when input validation fails."""
    pass

class ConfigurationError(YouTubeManagerError):
    """Raised when there's an issue with configuration."""
    pass

class DownloadError(YouTubeManagerError):
    """Raised when video download fails."""
    pass

class ProcessingError(YouTubeManagerError):
    """Raised when video processing fails."""
    pass

class UploadError(YouTubeManagerError):
    """Raised when upload to Google Drive fails."""
    pass

class GoogleAPIError(YouTubeManagerError):
    """Base class for Google API related errors."""
    pass

class GoogleSheetsError(GoogleAPIError):
    """Raised when there's an issue with Google Sheets operations."""
    pass

class GoogleDriveError(GoogleAPIError):
    """Raised when there's an issue with Google Drive operations."""
    pass

class CleanupError(YouTubeManagerError):
    """Raised when cleanup operations fail."""
    pass 