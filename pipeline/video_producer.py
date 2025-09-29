"""
Video production service using the Docker container
"""
import requests
import logging
import json
import time
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class VideoProducer:
    def __init__(self, docker_service_url: str = "http://localhost:5000"):
        self.base_url = docker_service_url
        
    def create_video(self, audio_url: str, media_urls: List[str], 
                    title: str = "Space Video") -> Optional[Dict[str, Any]]:
        """
        Create a video using the Docker service
        
        Args:
            audio_url: URL to the audio file
            media_urls: List of image/video URLs
            title: Video title for metadata
            
        Returns:
            Dictionary with video information or None if failed
        """
        try:
            payload = {
                "audio_url": audio_url,
                "media_urls": media_urls,
                "title": title,
                "metadata": {
                    "created_at": time.time(),
                    "media_count": len(media_urls)
                }
            }
            
            logger.info(f"Creating video with {len(media_urls)} media items")
            
            response = requests.post(
                f"{self.base_url}/process",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=300  # 5 minutes timeout for video processing
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get('status') == 'success':
                return result.get('data', {})
            else:
                logger.error(f"Video creation failed: {result}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Video creation request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in video creation: {e}")
            return None
    
    def health_check(self) -> bool:
        """Check if the video production service is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def upload_audio_file(self, audio_file_path: str) -> Optional[str]:
        """
        Upload audio file to a temporary hosting service
        Note: In production, you'd want to use a proper file hosting service
        """
        # For now, we'll assume the audio file is accessible via URL
        # In a real implementation, you'd upload to S3, Dropbox, etc.
        logger.warning("Audio file upload not implemented - assuming file is web-accessible")
        return audio_file_path
    
    def prepare_media_urls(self, media_items: List[Dict[str, Any]]) -> List[str]:
        """Extract URLs from media items"""
        urls = []
        for item in media_items:
            if 'url' in item and item['url']:
                urls.append(item['url'])
        return urls