"""
News scraping service that interfaces with the Docker container
"""
import requests
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class NewsScraperService:
    def __init__(self, docker_service_url: str = "http://localhost:5000"):
        self.base_url = docker_service_url
        
    def get_latest_space_news(self) -> List[Dict[str, Any]]:
        """Fetch latest space news from the Docker service"""
        try:
            response = requests.get(f"{self.base_url}/scrape-news", timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == 'success':
                return data.get('data', [])
            else:
                logger.error(f"News service returned error: {data}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch news: {e}")
            return []
    
    def health_check(self) -> bool:
        """Check if the news service is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def format_news_for_script(self, news_items: List[Dict[str, Any]], max_items: int = 3) -> str:
        """Format news items into script content"""
        if not news_items:
            return "Today we're exploring the wonders of space and the latest developments in space exploration."
        
        script_parts = ["Here are today's top space stories:"]
        
        for i, item in enumerate(news_items[:max_items], 1):
            title = item.get('headline_title', 'Unknown')
            source = item.get('source', 'Unknown Source')
            
            # Clean up the title
            title = title.replace('\n', ' ').strip()
            if len(title) > 100:
                title = title[:97] + "..."
            
            script_parts.append(f"{i}. From {source}: {title}")
        
        script_parts.append("Let's dive deeper into these fascinating developments in space exploration.")
        
        return " ".join(script_parts)