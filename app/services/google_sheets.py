"""
Google Sheets service for tracking video information.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from app.config.settings import Settings
from app.utils.exceptions import GoogleSheetsError

class GoogleSheetsService:
    """Handles Google Sheets operations."""
    
    # Default headers for the spreadsheet
    HEADERS = [
        'Title',
        'Description',
        'Tags',
        'Category',
        'Drive File ID',
        'Playlist',
        'Thumbnail',
        'Upload Date',
        'Download Status',
        'Upload Status'
    ]
    
    def __init__(self, settings: Settings):
        """
        Initialize the Google Sheets service.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self._setup_service()
        
    def _setup_service(self) -> None:
        """
        Set up the Google Sheets API service.
        
        Raises:
            GoogleSheetsError: If service setup fails
        """
        try:
            credentials = Credentials.from_service_account_file(
                str(self.settings.GOOGLE_CREDS_PATH),
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            self.client = gspread.authorize(credentials)
            self.spreadsheet = self.client.open_by_key(self.settings.SPREADSHEET_ID)
            self.worksheet = self._get_or_create_worksheet()
            
            self.logger.info("Google Sheets service initialized successfully")
            
        except Exception as e:
            raise GoogleSheetsError(f"Failed to initialize Sheets service: {str(e)}")
    
    def _get_or_create_worksheet(self) -> gspread.Worksheet:
        """
        Get or create the main worksheet.
        
        Returns:
            Worksheet object
            
        Raises:
            GoogleSheetsError: If worksheet creation fails
        """
        try:
            # Try to get the first worksheet
            worksheet = self.spreadsheet.sheet1
            
            # Check if headers exist and are correct
            headers = worksheet.row_values(1)
            if not headers:
                worksheet.append_row(self.HEADERS)
                self.logger.info("Created headers in worksheet")
            elif headers != self.HEADERS:
                # Update headers if they don't match
                worksheet.clear()
                worksheet.append_row(self.HEADERS)
                self.logger.info("Updated worksheet headers")
            
            return worksheet
            
        except Exception as e:
            raise GoogleSheetsError(f"Failed to setup worksheet: {str(e)}")
    
    async def add_video(
        self,
        metadata: Dict[str, Any],
        drive_file_id: Optional[str] = None,
        status: str = 'Pending'
    ) -> None:
        """
        Add video information to the spreadsheet.
        
        Args:
            metadata: Video metadata
            drive_file_id: Optional Google Drive file ID
            status: Current status of the video
            
        Raises:
            GoogleSheetsError: If update fails
        """
        try:
            # Format data according to requirements
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # Prepare row data
            row_data = [
                metadata.get('title', ''),                    # Title
                metadata.get('description', ''),              # Description
                metadata.get('tags', ''),                     # Tags
                metadata.get('category', ''),                 # Category
                drive_file_id or '',                         # Drive File ID
                self.settings.PLAYLIST_ID or '',             # Playlist
                metadata.get('thumbnail', ''),               # Thumbnail
                current_date,                                # Upload Date
                'Pending',                                   # Download Status
                'Pending'                                    # Upload Status
            ]
            
            # Add row to spreadsheet
            self.worksheet.append_row(row_data)
            self.logger.info(f"Added video {metadata.get('title', 'Unknown')} to spreadsheet")
            
        except Exception as e:
            raise GoogleSheetsError(f"Failed to add video to spreadsheet: {str(e)}")
    
    async def update_video_status(
        self,
        video_id: str,
        status: str,
        drive_file_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> None:
        """
        Update video status in the spreadsheet.
        
        Args:
            video_id: YouTube video ID (used for logging)
            status: New status
            drive_file_id: Optional Google Drive file ID
            title: Video title to search for in spreadsheet
            
        Raises:
            GoogleSheetsError: If update fails
        """
        try:
            if not title:
                raise GoogleSheetsError("Video title is required to update status")

            # Find the row with the video title
            cell = self.worksheet.find(title)
            if not cell:
                raise GoogleSheetsError(f"Video '{title}' not found in spreadsheet")
            
            row = cell.row
            
            # Only update Download Status to Completed when download finishes
            # Upload Status remains as Pending
            if status == "Completed":
                self.worksheet.update_cell(row, self.HEADERS.index('Download Status') + 1, "Completed")
            
            # Update Drive file ID if provided
            if drive_file_id:
                self.worksheet.update_cell(
                    row,
                    self.HEADERS.index('Drive File ID') + 1,
                    drive_file_id
                )
            
            self.logger.info(f"Updated status for video '{title}'")
            
        except Exception as e:
            raise GoogleSheetsError(f"Failed to update video status: {str(e)}")
    
    async def get_video_info(self, video_id: str) -> Optional[Dict[str, str]]:
        """
        Get video information from the spreadsheet.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Dictionary containing video information or None if not found
            
        Raises:
            GoogleSheetsError: If retrieval fails
        """
        try:
            # Find the row with the video ID
            cell = self.worksheet.find(video_id)
            if not cell:
                return None
            
            # Get all values in the row
            row_data = self.worksheet.row_values(cell.row)
            
            # Create dictionary with headers as keys
            return dict(zip(self.HEADERS, row_data))
            
        except Exception as e:
            raise GoogleSheetsError(f"Failed to get video info: {str(e)}") 