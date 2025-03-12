class YouTubeManagerError(Exception):
    """Base exception for YouTube Manager errors"""
    pass

class YouTubeDataError(YouTubeManagerError):
    """Exception for YouTube data related errors"""
    pass

class GoogleSheetsError(YouTubeManagerError):
    """Exception for Google Sheets related errors"""
    pass

class GoogleDriveError(YouTubeManagerError):
    """Exception for Google Drive related errors"""
    pass

class ValidationError(YouTubeManagerError):
    """Exception for validation errors"""
    pass

class ConfigurationError(YouTubeManagerError):
    """Exception for configuration errors"""
    pass 