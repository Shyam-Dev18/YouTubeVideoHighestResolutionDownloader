<<<<<<< HEAD
# YouTubeVideoDownloader
=======
# YouTube Video Manager

## Overview
The YouTube Video Manager is a Python-based tool designed to download YouTube videos, upload them to Google Drive, and update a Google Sheets spreadsheet with video data. It supports various YouTube URL formats and provides robust error handling.

## Features
- Download videos from YouTube using yt-dlp
- Upload videos to Google Drive
- Update Google Sheets with video information
- Supports multiple YouTube URL formats
- Configurable to keep or delete downloaded files

## Requirements
- Python 3.7+
- Google API credentials
- FFmpeg

## Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```bash
   cd <project-directory>
   ```
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration
1. Set up your Google API credentials and save the `credentials.json` file in the project root.
2. Update the `config/config.py` file with your configuration settings, including `SPREADSHEET_ID` and `GOOGLE_DRIVE_FOLDER_ID`.
3. Set `KEEP_FILE` to `True` or `False` in `config/config.py` to control whether downloaded files are kept.

## Usage
Run the YouTube Video Manager:
```bash
python src/youtube_manager.py
```

## License
This project is licensed under the MIT License. See `LICENSE.txt` for more details.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## Contact
For questions or support, please contact [Sanjay Darshanam] at [darshanamshyam17@gmail.com].
>>>>>>> 106faaa (Initial commit)
