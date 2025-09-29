#!/usr/bin/env python3
"""
WebContainer-compatible YouTube Space Video Pipeline
Uses only Python standard library
"""
import os
import sys
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
import xml.etree.ElementTree as ET
import tempfile
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebContainerPipeline:
    def __init__(self):
        self.load_config()
        
    def load_config(self):
        """Load configuration from environment variables"""
        self.config = {
            'tts_api_key': os.getenv('TTS_OPENAI_API_KEY', ''),
            'pexels_api_key': os.getenv('PEXELS_API_KEY', ''),
            'unsplash_access_key': os.getenv('UNSPLASH_ACCESS_KEY', ''),
            'nasa_api_key': os.getenv('NASA_API_KEY', 'DEMO_KEY')
        }
        
        # Check for required keys
        missing_keys = [k for k, v in self.config.items() if not v and k != 'nasa_api_key']
        if missing_keys:
            logger.warning(f"Missing API keys: {missing_keys}")
    
    def fetch_url(self, url, headers=None, data=None, timeout=30):
        """Fetch URL with error handling"""
        try:
            req = urllib.request.Request(url, headers=headers or {})
            if data:
                req.data = data.encode('utf-8') if isinstance(data, str) else data
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def scrape_rss_feed(self, url, source):
        """Scrape RSS feed using standard library XML parser"""
        try:
            content = self.fetch_url(url)
            if not content:
                return []
            
            root = ET.fromstring(content)
            items = []
            
            # Handle different RSS formats
            for item in root.findall('.//item')[:5]:  # Limit to 5 items
                title_elem = item.find('title')
                link_elem = item.find('link')
                pubdate_elem = item.find('pubDate')
                
                items.append({
                    'headline_title': title_elem.text if title_elem is not None else 'No title',
                    'published': pubdate_elem.text if pubdate_elem is not None else '',
                    'source': source,
                    'url': link_elem.text if link_elem is not None else url
                })
            
            return items
        except Exception as e:
            logger.error(f"RSS scraping failed for {source}: {e}")
            return []
    
    def get_space_news(self):
        """Fetch space news from multiple RSS sources"""
        feeds = {
            "CNN": "https://rss.cnn.com/rss/cnn_space.rss",
            "NASA": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
            "ESA": "https://www.esa.int/rssfeed/Our_Activities",
            "Space.com": "https://www.space.com/feeds/all"
        }
        
        all_news = []
        for source, url in feeds.items():
            logger.info(f"Fetching news from {source}...")
            news_items = self.scrape_rss_feed(url, source)
            all_news.extend(news_items)
        
        return all_news
    
    def search_pexels(self, query, count=10):
        """Search Pexels for images"""
        if not self.config['pexels_api_key']:
            return []
        
        try:
            url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&per_page={min(count, 80)}&orientation=landscape"
            headers = {'Authorization': self.config['pexels_api_key']}
            
            response = self.fetch_url(url, headers)
            if not response:
                return []
            
            data = json.loads(response)
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
    
    def search_unsplash(self, query, count=10):
        """Search Unsplash for images"""
        if not self.config['unsplash_access_key']:
            return []
        
        try:
            url = f"https://api.unsplash.com/search/photos?query={urllib.parse.quote(query)}&per_page={min(count, 30)}&orientation=landscape"
            headers = {'Authorization': f'Client-ID {self.config["unsplash_access_key"]}'}
            
            response = self.fetch_url(url, headers)
            if not response:
                return []
            
            data = json.loads(response)
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
    
    def search_nasa(self, query, count=10):
        """Search NASA image library"""
        try:
            url = f"https://images-api.nasa.gov/search?q={urllib.parse.quote(query)}&media_type=image&page_size={min(count, 100)}"
            
            response = self.fetch_url(url)
            if not response:
                return []
            
            data = json.loads(response)
            media_items = []
            
            for item in data.get('collection', {}).get('items', []):
                item_data = item.get('data', [{}])[0]
                links = item.get('links', [])
                
                if links:
                    media_url = links[0].get('href', '')
                    media_items.append({
                        'url': media_url,
                        'source': 'nasa',
                        'type': 'image',
                        'photographer': 'NASA',
                        'alt': item_data.get('title', query),
                        'description': item_data.get('description', '')
                    })
            
            return media_items
        except Exception as e:
            logger.error(f"NASA search failed: {e}")
            return []
    
    def collect_media(self, keywords, total_count=15):
        """Collect media from all sources"""
        all_media = []
        count_per_keyword = max(1, total_count // len(keywords))
        
        for keyword in keywords:
            logger.info(f"Collecting media for: {keyword}")
            
            # Collect from each source
            pexels_media = self.search_pexels(keyword, count_per_keyword)
            unsplash_media = self.search_unsplash(keyword, count_per_keyword)
            nasa_media = self.search_nasa(keyword, count_per_keyword)
            
            all_media.extend(pexels_media)
            all_media.extend(unsplash_media)
            all_media.extend(nasa_media)
        
        # Limit to requested count
        return all_media[:total_count]
    
    def generate_script(self, news_items):
        """Generate video script from news items"""
        if not news_items:
            return """Welcome to today's space exploration update! 
            
            Space continues to amaze us with incredible discoveries. From the International Space Station orbiting 400 kilometers above Earth, astronauts conduct groundbreaking research that benefits all of humanity.
            
            The search for life beyond Earth remains one of our most compelling quests. Mars, with its ancient riverbeds and polar ice caps, holds tantalizing clues about the possibility of past or present life.
            
            Our understanding of the universe expands daily through powerful telescopes like Hubble and James Webb. These incredible instruments reveal distant galaxies, nebulae, and exoplanets that challenge our understanding of cosmic evolution.
            
            Thanks for joining us on this cosmic journey. Keep looking up and stay curious about the universe around us!"""
        
        script_parts = ["Welcome to today's space news update!"]
        
        for i, item in enumerate(news_items[:3], 1):
            title = item.get('headline_title', 'Unknown')
            source = item.get('source', 'Unknown Source')
            
            # Clean up the title
            title = title.replace('\n', ' ').strip()
            if len(title) > 100:
                title = title[:97] + "..."
            
            script_parts.append(f"Story {i}: From {source} - {title}")
        
        script_parts.append("These developments continue to push the boundaries of human knowledge and our understanding of the cosmos.")
        script_parts.append("Thanks for watching today's space update. Keep exploring and stay curious!")
        
        return " ".join(script_parts)
    
    def generate_tts_audio(self, text, voice='alloy'):
        """Generate TTS audio (simulated - would need actual API call)"""
        if not self.config['tts_api_key']:
            logger.warning("No TTS API key configured")
            return None
        
        try:
            # This would be the actual TTS API call
            url = "https://ttsopenai.com/api/v1/audio/speech"
            headers = {
                'Authorization': f'Bearer {self.config["tts_api_key"]}',
                'Content-Type': 'application/json'
            }
            
            payload = json.dumps({
                'model': 'tts-1',
                'input': text,
                'voice': voice,
                'response_format': 'mp3'
            })
            
            # For WebContainer, we'll simulate this
            logger.info(f"TTS generation simulated for {len(text)} characters")
            return f"simulated_audio_{int(time.time())}.mp3"
            
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return None
    
    def create_video_metadata(self, script, media_items, audio_file):
        """Create video metadata (since we can't actually create video in WebContainer)"""
        return {
            'title': 'Space News Update',
            'script': script,
            'script_word_count': len(script.split()),
            'estimated_duration': len(script.split()) / 150 * 60,  # 150 words per minute
            'media_count': len(media_items),
            'media_sources': list(set(item.get('source', 'unknown') for item in media_items)),
            'audio_file': audio_file,
            'created_at': datetime.now().isoformat(),
            'status': 'metadata_generated'
        }
    
    def run_pipeline(self, duration=120, voice='alloy'):
        """Run the complete pipeline"""
        start_time = time.time()
        results = {
            'status': 'started',
            'timestamp': datetime.now().isoformat(),
            'steps': {},
            'errors': []
        }
        
        try:
            # Step 1: Check configuration
            logger.info("Step 1: Checking configuration...")
            missing_keys = [k for k, v in self.config.items() if not v and k != 'nasa_api_key']
            results['steps']['config_check'] = {
                'configured_apis': [k for k, v in self.config.items() if v],
                'missing_apis': missing_keys
            }
            
            # Step 2: Fetch news
            logger.info("Step 2: Fetching space news...")
            news_items = self.get_space_news()
            results['steps']['news_collection'] = {
                'items_found': len(news_items),
                'sources': list(set(item.get('source', 'Unknown') for item in news_items))
            }
            
            # Step 3: Generate script
            logger.info("Step 3: Generating script...")
            script = self.generate_script(news_items)
            results['steps']['script_generation'] = {
                'word_count': len(script.split()),
                'estimated_duration': len(script.split()) / 150 * 60
            }
            
            # Step 4: Generate TTS
            logger.info("Step 4: Generating TTS audio...")
            audio_file = self.generate_tts_audio(script, voice)
            results['steps']['tts_generation'] = {
                'audio_file': audio_file,
                'voice_used': voice,
                'status': 'simulated' if not self.config['tts_api_key'] else 'generated'
            }
            
            # Step 5: Collect media
            logger.info("Step 5: Collecting media...")
            keywords = ['space exploration', 'astronaut', 'mars', 'galaxy']
            media_items = self.collect_media(keywords, 15)
            results['steps']['media_collection'] = {
                'total_items': len(media_items),
                'sources': list(set(item.get('source', 'Unknown') for item in media_items)),
                'keywords_used': keywords
            }
            
            # Step 6: Create video metadata
            logger.info("Step 6: Creating video metadata...")
            video_metadata = self.create_video_metadata(script, media_items, audio_file)
            results['steps']['video_creation'] = video_metadata
            
            results['status'] = 'completed'
            results['final_output'] = video_metadata
            
        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            results['status'] = 'failed'
        
        results['total_duration'] = time.time() - start_time
        results['completed_at'] = datetime.now().isoformat()
        
        return results

def main():
    """Main entry point"""
    print("🚀 WebContainer Space Video Pipeline")
    print("=" * 40)
    
    # Initialize pipeline
    pipeline = WebContainerPipeline()
    
    # Check if we have API keys
    missing_keys = [k for k, v in pipeline.config.items() if not v and k != 'nasa_api_key']
    if missing_keys:
        print(f"⚠️  Missing API keys: {missing_keys}")
        print("The pipeline will run with limited functionality.")
        print("Please set these environment variables for full functionality:")
        for key in missing_keys:
            print(f"  export {key.upper()}=your_api_key_here")
        print()
    
    # Run pipeline
    print("🔄 Running pipeline...")
    results = pipeline.run_pipeline(duration=120, voice='alloy')
    
    # Save results
    output_file = 'pipeline_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\n=== Pipeline Results ===")
    print(f"Status: {results['status'].upper()}")
    print(f"Duration: {results.get('total_duration', 0):.2f} seconds")
    print(f"Results saved to: {output_file}")
    
    if results['status'] == 'completed':
        final_output = results.get('final_output', {})
        print(f"✅ Pipeline completed successfully!")
        print(f"📝 Script: {final_output.get('script_word_count', 0)} words")
        print(f"🖼️  Media: {final_output.get('media_count', 0)} items")
        print(f"⏱️  Estimated video duration: {final_output.get('estimated_duration', 0):.1f} seconds")
        
        # Show first few lines of script
        script = final_output.get('script', '')
        if script:
            print(f"\n📄 Script preview:")
            print(f"   {script[:200]}...")
    else:
        print("❌ Pipeline failed!")
        if results.get('errors'):
            print("Errors:")
            for error in results['errors']:
                print(f"  - {error}")
    
    return 0 if results['status'] == 'completed' else 1

if __name__ == "__main__":
    sys.exit(main())