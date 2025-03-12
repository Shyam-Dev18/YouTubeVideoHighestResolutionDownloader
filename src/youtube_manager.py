import os
import sys
import logging
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import yt_dlp
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError as GoogleDriveError

from config.config import (
    SERVICE_ACCOUNT_FILE, SPREADSHEET_ID, GOOGLE_DRIVE_FOLDER_ID,
    SCOPES, HEADERS, MAX_RETRIES, RETRY_DELAY, CHUNK_SIZE,
    FFMPEG_PATH, LOG_DIR, LOG_FORMAT , PLAYLIST_ID, KEEP_FILE
)
from utils.exceptions import (
    YouTubeManagerError, YouTubeDataError, GoogleSheetsError,
    GoogleDriveError, ValidationError, ConfigurationError
)
from utils.validators import (
    validate_credentials, validate_ffmpeg,
    validate_file_exists, validate_directory_exists, validate_youtube_url
)

# Configure logging
def setup_logging():
    """Configure logging with proper formatting and handlers"""
    log_file = LOG_DIR / f"youtube_manager_{datetime.now().strftime('%Y%m%d')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

# Define Videos directory
VIDEOS_DIR = project_root / 'Videos'

def sanitize_filename(filename: str) -> str:
    """
    Sanitize the filename by removing/replacing invalid characters
    and ensuring proper length
    """
    # Replace invalid characters with underscore
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove any other non-ASCII characters
    filename = re.sub(r'[^\x00-\x7F]+', '_', filename)
    # Replace multiple underscores with single one
    filename = re.sub(r'_+', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    # Limit length to 200 characters (including extension)
    if len(filename) > 200:
        filename = filename[:196] + '...'
    return filename

def ensure_video_dir() -> Path:
    """Ensure Videos directory exists and return its path"""
    try:
        VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
        return VIDEOS_DIR
    except Exception as e:
        raise ConfigurationError(f"Failed to create Videos directory: {str(e)}")

class YouTubeManager:
    """Main class to handle YouTube video operations"""
    
    def __init__(self):
        """Initialize the YouTube Manager with proper setup"""
        self.logger = setup_logging()
        self._setup_google_services()
        self._setup_yt_dlp()
        
    def _setup_google_services(self):
        """Setup Google Sheets and Drive services"""
        try:
            validate_credentials()
            credentials = Credentials.from_service_account_file(
                str(SERVICE_ACCOUNT_FILE),
                scopes=SCOPES
            )
            self.sheets_service = gspread.authorize(credentials)
            self.drive_service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
            self.logger.info("Successfully authenticated with Google services")
        except Exception as e:
            self.logger.error(f"Google services setup failed: {str(e)}")
            raise ConfigurationError(f"Google services setup failed: {str(e)}")
    
    def _setup_yt_dlp(self):
        """Setup yt-dlp with optimized settings"""
        try:
            validate_ffmpeg()
            self.ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
                'outtmpl': '%(id)s',
                'ffmpeg_location': str(FFMPEG_PATH),
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'merge_output_format': 'mp4',
                'progress_hooks': [self._download_progress_hook]
            }
        except Exception as e:
            self.logger.error(f"yt-dlp setup failed: {str(e)}")
            raise ConfigurationError(f"yt-dlp setup failed: {str(e)}")
    
    def _download_progress_hook(self, d):
        """Hook for download progress updates"""
        if d['status'] == 'downloading':
            self.logger.info(f"Download progress: {d.get('_percent_str', '0%')}")
    
    def get_or_create_sheet(self) -> gspread.Worksheet:
        """Get or create the spreadsheet with proper headers"""
        try:
            # Open spreadsheet by ID instead of name
            spreadsheet = self.sheets_service.open_by_key(SPREADSHEET_ID)
            self.logger.info(f"Spreadsheet found with ID: {SPREADSHEET_ID}")
        except gspread.SpreadsheetNotFound:
            # Get the service account email from credentials
            with open(SERVICE_ACCOUNT_FILE) as f:
                import json
                credentials_data = json.load(f)
                service_account_email = credentials_data.get('client_email', 'Unknown')
            
            error_msg = (
                f"Spreadsheet with ID '{SPREADSHEET_ID}' not found. "
                f"Please make sure:\n"
                f"1. The spreadsheet exists\n"
                f"2. The spreadsheet is shared with this service account: {service_account_email}\n"
                f"3. The spreadsheet ID is correct"
            )
            self.logger.error(error_msg)
            raise GoogleSheetsError(error_msg)
        except Exception as e:
            self.logger.error(f"Error accessing spreadsheet: {str(e)}")
            raise GoogleSheetsError(f"Spreadsheet access error: {str(e)}")

        try:
            sheet = spreadsheet.sheet1
            current_headers = sheet.row_values(1)
            
            if not current_headers:
                self.logger.info("No headers found. Adding default headers")
                sheet.insert_row(HEADERS, 1)
            elif current_headers != HEADERS:
                self.logger.warning("Headers mismatch. Updating headers")
                sheet.clear()
                sheet.insert_row(HEADERS, 1)
            
            return sheet
        except Exception as e:
            self.logger.error(f"Error accessing worksheet: {str(e)}")
            raise GoogleSheetsError(f"Worksheet error: {str(e)}")
    
    def get_video_data(self, video_url: str) -> Optional[List[str]]:
        """Extract video metadata using yt-dlp"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                if not info:
                    raise YouTubeDataError("Failed to extract video information")
                
                # Format data for spreadsheet
                tags = ', '.join(info.get('tags', [])) if info.get('tags') else ''
                category = info.get('categories', [''])[0] if info.get('categories') else ''
                upload_date = info.get('upload_date', '')
                if upload_date:
                    upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
                
                video_data = [
                    info.get('title', ''),
                    info.get('description', ''),
                    tags,
                    category,
                    info.get('thumbnail', ''),
                    PLAYLIST_ID, #info.get('playlist_id', ''),
                    info.get('id', ''),
                    upload_date,
                    '',  # Drive File ID (will be updated after upload)
                    'Pending'  # Download Status
                ]
                
                self.logger.info(f"Successfully extracted data for video: {info.get('title', 'Unknown')}")
                return video_data
                
        except yt_dlp.utils.DownloadError as e:
            self.logger.error(f"Error downloading video info: {str(e)}")
            raise YouTubeDataError(f"Download error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error fetching video data: {str(e)}")
            raise YouTubeDataError(f"Data extraction error: {str(e)}")
    
    def download_video(self, video_url: str) -> Optional[Path]:
        """Download the video using yt-dlp and store in Videos directory"""
        try:
            # Ensure Videos directory exists
            videos_dir = ensure_video_dir()
            
            # Modify yt-dlp options for the new location
            download_opts = self.ydl_opts.copy()
            download_opts['outtmpl'] = str(videos_dir / '%(id)s.%(ext)s')
            
            with yt_dlp.YoutubeDL(download_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                video_id = info.get('id')
                video_title = info.get('title', video_id)
                
                if not video_id:
                    raise YouTubeDataError("Could not extract video ID")
                
                # Get the downloaded file path
                temp_video_path = videos_dir / f"{video_id}.mp4"
                if not temp_video_path.exists():
                    raise YouTubeDataError("Download completed but file was not created")
                
                # Create final filename with video title
                final_filename = f"{sanitize_filename(video_title)}_{video_id}.mp4"
                final_video_path = videos_dir / final_filename
                
                # Rename the file
                try:
                    temp_video_path.rename(final_video_path)
                except Exception as e:
                    self.logger.warning(f"Failed to rename video file: {str(e)}")
                    final_video_path = temp_video_path
                
                # Create a copy in the same directory
                backup_path = final_video_path.with_name(f"backup_{final_video_path.name}")
                try:
                    shutil.copy2(final_video_path, backup_path)
                    self.logger.info(f"Created backup copy at: {backup_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to create backup copy: {str(e)}")
                
                # Cleanup downloaded file if KEEP_FILE is False
                if not KEEP_FILE and final_video_path.exists():
                    try:
                        final_video_path.unlink()
                        self.logger.info("Deleted downloaded file as per KEEP_FILE setting")
                    except Exception as e:
                        self.logger.warning(f"Failed to delete downloaded file: {str(e)}")
                
                return final_video_path
                
        except Exception as e:
            self.logger.error(f"Error downloading video: {str(e)}")
            raise YouTubeDataError(f"Video download failed: {str(e)}")
    
    def upload_to_drive(self, file_path: Path) -> Optional[str]:
        """Upload video to Google Drive"""
        try:
            validate_file_exists(file_path)
            
            file_metadata = {
                'name': file_path.name,
                'parents': [GOOGLE_DRIVE_FOLDER_ID]
            }
            
            media = MediaFileUpload(
                str(file_path),
                mimetype='video/mp4',
                chunksize=CHUNK_SIZE,
                resumable=True
            )
            
            self.logger.info("Starting upload to Google Drive")
            request = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            )
            
            response = None
            last_progress = 0
            while response is None:
                try:
                    status, response = request.next_chunk()
                    if status:
                        current_progress = int(status.progress() * 100)
                        if current_progress > last_progress:
                            self.logger.info(f"Upload progress: {current_progress}%")
                            last_progress = current_progress
                except GoogleDriveError as e:
                    self.logger.error(f"Error during upload: {str(e)}")
                    raise
            
            file_id = response.get('id')
            self.logger.info(f"Successfully uploaded to Google Drive! File ID: {file_id}")
            return file_id
            
        except Exception as e:
            self.logger.error(f"Error uploading to Google Drive: {str(e)}")
            raise GoogleDriveError(f"Upload failed: {str(e)}")
    
    def update_spreadsheet(self, sheet: gspread.Worksheet, video_data: List[str], drive_file_id: str):
        """Update spreadsheet with video data and Drive file ID"""
        try:
            # Update Drive File ID and Download Status
            video_data[8] = drive_file_id  # Drive File ID
            video_data[9] = 'Completed'   # Download Status
            
            # Check for duplicate video ID
            video_id = video_data[6]
            existing_ids = sheet.col_values(7)  # Column G contains video IDs
            
            if video_id in existing_ids:
                self.logger.warning(f"Video ID {video_id} already exists in spreadsheet")
                return False
            
            # Append the new row
            sheet.append_row(video_data)
            self.logger.info("Video data added successfully to spreadsheet")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating spreadsheet: {str(e)}")
            raise GoogleSheetsError(f"Spreadsheet update failed: {str(e)}")
    
    def process_video(self, url: str):
        """Process a single video: download, upload, and update spreadsheet"""
        try:
            # Validate URL and extract video ID
            video_id = validate_youtube_url(url)
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            
            # Get spreadsheet
            sheet = self.get_or_create_sheet()
            
            # Get video data
            self.logger.info(f"Fetching data for video: {video_url}")
            video_data = self.get_video_data(video_url)
            
            if not video_data:
                raise YouTubeDataError("Failed to get video data")
            
            # Download video
            self.logger.info("Downloading video...")
            video_path = self.download_video(video_url)
            
            if not video_path:
                raise YouTubeDataError("Failed to download video")
            
            # Upload to Drive
            self.logger.info("Uploading to Google Drive...")
            drive_file_id = self.upload_to_drive(video_path)
            
            if not drive_file_id:
                raise GoogleDriveError("Failed to upload to Google Drive")
            
            # Update spreadsheet
            if self.update_spreadsheet(sheet, video_data, drive_file_id):
                self.logger.info("Video processing completed successfully")
                return True
            else:
                self.logger.warning("Video already exists in spreadsheet")
                return False
                
        except Exception as e:
            self.logger.error(f"Error processing video: {str(e)}")
            raise
        finally:
            # Cleanup downloaded file
            if 'video_path' in locals() and video_path.exists():
                try:
                    video_path.unlink()
                    self.logger.info("Cleaned up downloaded file")
                except Exception as e:
                    self.logger.warning(f"Failed to clean up downloaded file: {str(e)}")

def main():
    """Main function to run the YouTube Manager"""
    try:
        print("\nYouTube Video Manager")
        print("=" * 30)
        print("\nSupported URL formats:")
        print("- https://www.youtube.com/watch?v=VIDEO_ID")
        print("- https://youtu.be/VIDEO_ID")
        print("- https://youtube.com/shorts/VIDEO_ID")
        print("- VIDEO_ID (11 characters)")
        print("\n" + "=" * 30)
        
        manager = YouTubeManager()
        
        while True:
            try:
                url = input("\nEnter YouTube URL or video ID (or 'q' to quit): ").strip()
                if url.lower() == 'q':
                    print("\nGoodbye!")
                    break
                
                if manager.process_video(url):
                    print("✅ Video processed successfully")
                else:
                    print("⚠️ Video already exists in spreadsheet")
                
                print("\n" + "-" * 30)
                
            except ValidationError as e:
                print(f"Validation Error: {str(e)}")
                continue
            except YouTubeDataError as e:
                print(f"YouTube Error: {str(e)}")
                continue
            except GoogleSheetsError as e:
                print(f"Google Sheets Error: {str(e)}")
                continue
            except GoogleDriveError as e:
                print(f"Google Drive Error: {str(e)}")
                continue
            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
                break
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 