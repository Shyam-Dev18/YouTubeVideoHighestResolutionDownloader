import os
from pathlib import Path

# Project root directory
ROOT_DIR = Path(__file__).parent.parent

# Google API Configuration
SERVICE_ACCOUNT_FILE = ROOT_DIR / 'data' / 'credentials.json'
SPREADSHEET_ID = '1Zi0Pjsdnd6rOCRuFA-pwKrXlzuGKCaLFebD51fnKDqU'  # Replace with your spreadsheet ID
GOOGLE_DRIVE_FOLDER_ID = '1ZpYOI7VzZVhxtu8B6RGhQTjUbKNyKXwA'

# API Scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

# Spreadsheet Headers
HEADERS = [
    'Title', 'Description', 'Tags', 'Category', 
    'Thumbnail', 'Playlist', 'Video ID', 'Upload Date',
    'Drive File ID', 'Download Status'
]

# Download Settings
MAX_RETRIES = 3
RETRY_DELAY = 2  # Base delay in seconds
CHUNK_SIZE = 50 * 1024 * 1024  # 50MB chunks for upload 

# FFmpeg Settings
FFMPEG_PATH = ROOT_DIR / 'ffmpeg' / 'bin' / 'ffmpeg.exe'

# Logging Configuration
LOG_DIR = ROOT_DIR / 'logs'
LOG_FORMAT = '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'

# Create necessary directories
LOG_DIR.mkdir(exist_ok=True)
(ROOT_DIR / 'data').mkdir(exist_ok=True)

PLAYLIST_ID = 'NOTHINHG' # Change the PlayList ID to your Actual Playlist ID
KEEP_FILE = True  # Set to False to delete downloaded files after processing 