"""
Configuration settings for the YouTube Space Video Pipeline
"""
import os
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class APIConfig:
    """API configuration settings"""
    tts_openai_api_key: str = os.getenv('TTS_OPENAI_API_KEY', '')
    pexels_api_key: str = os.getenv('PEXELS_API_KEY', '')
    unsplash_access_key: str = os.getenv('UNSPLASH_ACCESS_KEY', '')
    nasa_api_key: str = os.getenv('NASA_API_KEY', 'DEMO_KEY')
    
@dataclass
class VideoConfig:
    """Video production settings"""
    output_resolution: tuple = (1920, 1080)
    fps: int = 30
    video_duration_range: tuple = (60, 180)  # 1-3 minutes
    transition_duration: float = 0.5
    image_display_duration: float = 4.0
    
@dataclass
class ContentConfig:
    """Content generation settings"""
    space_keywords: List[str] = None
    news_sources: List[str] = None
    max_headlines: int = 5
    script_length_words: int = 200
    
    def __post_init__(self):
        if self.space_keywords is None:
            self.space_keywords = [
                'space exploration', 'nasa', 'mars', 'moon', 'astronaut',
                'rocket launch', 'space station', 'galaxy', 'nebula',
                'satellite', 'spacecraft', 'astronomy', 'cosmos'
            ]
        
        if self.news_sources is None:
            self.news_sources = [
                'https://rss.cnn.com/rss/cnn_space.rss',
                'https://www.nasa.gov/rss/dyn/breaking_news.rss',
                'https://www.esa.int/rssfeed/Our_Activities',
                'https://www.space.com/feeds/all'
            ]

# Global configuration instances
api_config = APIConfig()
video_config = VideoConfig()
content_config = ContentConfig()