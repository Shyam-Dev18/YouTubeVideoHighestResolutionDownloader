"""
Google Drive service for file uploads and management.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from app.config.settings import Settings
from app.utils.exceptions import GoogleDriveError
from app.utils.validators import validate_file_exists

class GoogleDriveService:
    """Handles Google Drive operations."""
    
    def __init__(self, settings: Settings):
        """
        Initialize the Google Drive service.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self._setup_service()
        
    def _setup_service(self) -> None:
        """
        Set up the Google Drive API service.
        
        Raises:
            GoogleDriveError: If service setup fails
        """
        try:
            credentials = Credentials.from_service_account_file(
                str(self.settings.GOOGLE_CREDS_PATH),
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            
            self.service = build(
                'drive',
                'v3',
                credentials=credentials,
                cache_discovery=False
            )
            
            self.logger.info("Google Drive service initialized successfully")
            
        except Exception as e:
            raise GoogleDriveError(f"Failed to initialize Drive service: {str(e)}")
    
    async def upload_file(
        self,
        file_path: Path,
        title: Optional[str] = None,
        mime_type: str = 'video/mp4',
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> str:
        """
        Upload a file to Google Drive.
        
        Args:
            file_path: Path to the file to upload
            title: Optional title for the file (defaults to filename)
            mime_type: MIME type of the file
            progress_callback: Optional callback for upload progress
            
        Returns:
            ID of the uploaded file
            
        Raises:
            GoogleDriveError: If upload fails
        """
        try:
            validate_file_exists(file_path)
            
            file_metadata = {
                'name': title or file_path.name,
                'parents': [self.settings.DRIVE_FOLDER_ID]
            }
            
            media = MediaFileUpload(
                str(file_path),
                mimetype=mime_type,
                resumable=True,
                chunksize=self.settings.CHUNK_SIZE
            )
            
            # Create the file
            request = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            )
            
            print("\nUploading to Google Drive...")
            self.logger.info("Starting file upload to Google Drive")
            
            response = None
            last_progress = -1  # Start at -1 to ensure first update is shown
            
            def _print_progress(progress: int) -> None:
                """Print progress to both console and log."""
                print(f"\rUpload Progress: {progress}%", end="", flush=True)
                self.logger.info(f"Upload progress: {progress}%")
            
            while response is None:
                try:
                    status, response = request.next_chunk()
                    if status:
                        current_progress = int(status.progress() * 100)
                        # Always show 0% at start
                        if last_progress == -1:
                            _print_progress(0)
                            
                        # Show progress when it increases
                        if current_progress > last_progress:
                            _print_progress(current_progress)
                            last_progress = current_progress
                            if progress_callback:
                                progress_callback(status.progress())
                                
                except HttpError as e:
                    error_msg = f"Error during upload chunk: {str(e)}"
                    self.logger.error(error_msg)
                    raise GoogleDriveError(error_msg)
            
            # Always show 100% at completion
            if last_progress < 100:
                _print_progress(100)
            
            print("\nUpload completed!")
            self.logger.info("File upload completed successfully")
            
            file_id = response.get('id')
            if not file_id:
                raise GoogleDriveError("Upload successful but file ID not received")
            
            self.logger.info(f"File uploaded successfully. ID: {file_id}")
            return file_id
            
        except HttpError as e:
            raise GoogleDriveError(f"Drive API error: {str(e)}")
        except Exception as e:
            raise GoogleDriveError(f"Upload failed: {str(e)}")
    
    async def delete_file(self, file_id: str) -> None:
        """
        Delete a file from Google Drive.
        
        Args:
            file_id: ID of the file to delete
            
        Raises:
            GoogleDriveError: If deletion fails
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            self.logger.info(f"File deleted successfully. ID: {file_id}")
            
        except HttpError as e:
            raise GoogleDriveError(f"Failed to delete file: {str(e)}")
    
    async def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """
        Get information about a file.
        
        Args:
            file_id: ID of the file
            
        Returns:
            Dictionary containing file information
            
        Raises:
            GoogleDriveError: If retrieval fails
        """
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, createdTime'
            ).execute()
            
            return {
                'id': file.get('id'),
                'name': file.get('name'),
                'mime_type': file.get('mimeType'),
                'size': int(file.get('size', 0)),
                'created_time': file.get('createdTime')
            }
            
        except HttpError as e:
            raise GoogleDriveError(f"Failed to get file info: {str(e)}") 