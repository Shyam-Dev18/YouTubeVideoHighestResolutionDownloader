# YouTube Video Manager

A Python application for managing YouTube videos, including downloading, processing, and uploading to Google Drive.

## Features

- Download YouTube videos with metadata
- Process videos with FFmpeg
- Upload to Google Drive
- Track video status in Google Sheets
- Built-in FFmpeg support
- Progress tracking and logging
- Error handling and retries

## Prerequisites

- Python 3.8 or higher
- Google Cloud Project with YouTube Data API and Google Drive API enabled
- Google Sheets spreadsheet for tracking videos
- Google Drive folder for video uploads

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd youtube-manager
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Mac/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up FFmpeg:
   - Download FFmpeg for your platform:
     - Windows: [FFmpeg Windows Build](https://github.com/BtbN/FFmpeg-Builds/releases)
     - Mac: `brew install ffmpeg`
     - Linux: `sudo apt-get install ffmpeg`
   - For Windows:
     - Extract the downloaded archive
     - Copy `ffmpeg.exe` and `ffprobe.exe` to the `ffmpeg/bin` directory in your project
   - For Mac/Linux:
     - Copy `ffmpeg` and `ffprobe` to the `ffmpeg/bin` directory
     - Make them executable: `chmod +x ffmpeg/bin/ffmpeg ffmpeg/bin/ffprobe`

5. Set up Google credentials:
   - Create a Google Cloud Project
   - Enable YouTube Data API and Google Drive API
   - Create OAuth 2.0 credentials
   - Download the credentials JSON file
   - Place it in the `storage/credentials` directory as `google_creds.json`

6. Create a `.env` file in the project root:
   ```env
   SPREADSHEET_ID=your_spreadsheet_id
   DRIVE_FOLDER_ID=your_drive_folder_id
   PLAYLIST_ID=optional_playlist_id
   LOG_LEVEL=INFO
   UPLOAD_TO_DRIVE=true
   ```

## Project Structure

```
youtube-manager/
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── downloader.py
│   │   └── exceptions.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── google_drive.py
│   │   └── google_sheets.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── helpers.py
│   │   └── validators.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   └── __init__.py
├── storage/
│   ├── credentials/
│   ├── logs/
│   └── videos/
│       ├── temp/
│       └── processed/
├── ffmpeg/
│   └── bin/
│       ├── ffmpeg.exe
│       └── ffprobe.exe
├── .env
├── .gitignore
├── main.py
├── requirements.txt
└── README.md
```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

2. Enter a YouTube URL when prompted

3. The application will:
   - Download the video
   - Extract metadata
   - Add entry to Google Sheets
   - Upload to Google Drive (if enabled)
   - Clean up temporary files

## Configuration

The application can be configured through environment variables in the `.env` file:

- `SPREADSHEET_ID`: Google Sheets spreadsheet ID
- `DRIVE_FOLDER_ID`: Google Drive folder ID
- `PLAYLIST_ID`: Optional YouTube playlist ID
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `UPLOAD_TO_DRIVE`: Whether to upload videos to Google Drive

## Error Handling

The application includes comprehensive error handling:
- Invalid URLs
- Download failures
- API errors
- File system errors
- FFmpeg processing errors

All errors are logged with appropriate context and handled gracefully.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 