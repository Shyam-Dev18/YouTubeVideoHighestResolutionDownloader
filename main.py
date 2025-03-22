"""
YouTube Video Manager
A professional tool for downloading and managing YouTube videos with Google Drive integration.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to Python path to ensure imports work in any context
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from app.core.processor import VideoProcessor
from app.config.settings import Settings
from app.utils.helpers import setup_logging
from app.utils.exceptions import YouTubeManagerError

# Global logger instance
logger = None

async def process_videos(processor: VideoProcessor):
    """Process videos in a loop until user quits."""
    global logger
    while True:
        try:
            url = input("\nEnter YouTube URL (q to quit): ").strip()
            
            if url.lower() == 'q':
                print("\nExiting...")
                break
                
            if not url:
                print("URL cannot be empty!")
                continue
            
            print("\nProcessing video... Please wait.")
            await processor.process_video(url)
            print("\nVideo processed successfully!")
            
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            break
            
        except YouTubeManagerError as e:
            print(f"\nError: {str(e)}")
            logger.error(str(e))
            
        except Exception as e:
            print(f"\nUnexpected error: {str(e)}")
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)

def main():
    """Main entry point."""
    global logger
    
    try:
        # Initialize settings and logging
        settings = Settings()
        logger = setup_logging(settings)
        logger.info("Starting YouTube Video Manager...")
        
        # Initialize processor once
        processor = VideoProcessor(settings)
        
        # Run the async event loop
        asyncio.run(process_videos(processor))
        
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)
        
    finally:
        if logger:
            logger.info("Application shutdown complete.")

if __name__ == "__main__":
    main() 