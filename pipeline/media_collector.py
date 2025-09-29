"""
Media collection service for gathering images and videos from multiple sources
"""
import requests
import logging
import random
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class MediaCollector:
    def __init__(self, pexels_key: str, unsplash_key: str, nasa_key: str = "DEMO_KEY"):
        self.pexels_key = pexels_key
        self.unsplash_key = unsplash_key
        self.nasa_key = nasa_key
        
    def search_pexels(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        """Search for images on Pexels"""
        try:
            headers = {'Authorization': self.pexels_key}
            params = {
                'query': query,
                'per_page': min(count, 80),
                'orientation': 'landscape'
            }
            
            response = requests.get(
                'https://api.pexels.com/v1/search',
                headers=headers,
                params=params,
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            media_items = []
            
            for photo in data.get('photos', []):
                media_items.append({
                    'url': photo['src']['large'],
                    'source': 'pexels',
                    'type': 'image',
                    'photographer': photo.get('photographer', 'Unknown'),
                    'alt': photo.get('alt', query)
                })
            
            return media_items
            
        except Exception as e:
            logger.error(f"Pexels search failed: {e}")
            return []
    
    def search_unsplash(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        """Search for images on Unsplash"""
        try:
            headers = {'Authorization': f'Client-ID {self.unsplash_key}'}
            params = {
                'query': query,
                'per_page': min(count, 30),
                'orientation': 'landscape'
            }
            
            response = requests.get(
                'https://api.unsplash.com/search/photos',
                headers=headers,
                params=params,
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            media_items = []
            
            for photo in data.get('results', []):
                media_items.append({
                    'url': photo['urls']['regular'],
                    'source': 'unsplash',
                    'type': 'image',
                    'photographer': photo['user']['name'],
                    'alt': photo.get('alt_description', query)
                })
            
            return media_items
            
        except Exception as e:
            logger.error(f"Unsplash search failed: {e}")
            return []
    
    def search_nasa(self, query: str, count: int = 10) -> List[Dict[str, Any]]:
        """Search NASA image and video library"""
        try:
            params = {
                'q': query,
                'media_type': 'image,video',
                'page_size': min(count, 100)
            }
            
            response = requests.get(
                'https://images-api.nasa.gov/search',
                params=params,
                timeout=20
            )
            response.raise_for_status()
            
            data = response.json()
            media_items = []
            
            for item in data.get('collection', {}).get('items', []):
                item_data = item.get('data', [{}])[0]
                links = item.get('links', [])
                
                if links:
                    media_url = links[0].get('href', '')
                    media_type = 'video' if 'mp4' in media_url.lower() else 'image'
                    
                    media_items.append({
                        'url': media_url,
                        'source': 'nasa',
                        'type': media_type,
                        'photographer': 'NASA',
                        'alt': item_data.get('title', query),
                        'description': item_data.get('description', '')
                    })
            
            return media_items
            
        except Exception as e:
            logger.error(f"NASA search failed: {e}")
            return []
    
    def collect_media_for_keywords(self, keywords: List[str], total_count: int = 20) -> List[Dict[str, Any]]:
        """Collect media from all sources for given keywords"""
        all_media = []
        count_per_source = max(1, total_count // (len(keywords) * 3))  # 3 sources
        
        for keyword in keywords:
            # Collect from each source
            pexels_media = self.search_pexels(keyword, count_per_source)
            unsplash_media = self.search_unsplash(keyword, count_per_source)
            nasa_media = self.search_nasa(keyword, count_per_source)
            
            all_media.extend(pexels_media)
            all_media.extend(unsplash_media)
            all_media.extend(nasa_media)
        
        # Shuffle and limit to requested count
        random.shuffle(all_media)
        return all_media[:total_count]
    
    def get_curated_space_media(self, count: int = 15) -> List[Dict[str, Any]]:
        """Get a curated selection of space-related media"""
        space_queries = [
            'space exploration', 'astronaut', 'rocket launch', 'mars',
            'galaxy', 'nebula', 'space station', 'moon landing'
        ]
        
        selected_queries = random.sample(space_queries, min(4, len(space_queries)))
        return self.collect_media_for_keywords(selected_queries, count)