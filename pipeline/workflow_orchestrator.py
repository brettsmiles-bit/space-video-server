"""
Main workflow orchestrator that coordinates all services
"""
import logging
import time
import os
from typing import Dict, Any, Optional
from datetime import datetime

from .config import api_config, video_config, content_config
from .news_scraper import NewsScraperService
from .media_collector import MediaCollector
from .tts_service import TTSService
from .script_generator import ScriptGenerator
from .video_producer import VideoProducer

logger = logging.getLogger(__name__)

class WorkflowOrchestrator:
    def __init__(self, 
                 news_service_url: str = "http://localhost:5000",
                 video_service_url: str = "http://localhost:5000"):
        
        # Initialize services
        self.news_scraper = NewsScraperService(news_service_url)
        self.media_collector = MediaCollector(
            api_config.pexels_api_key,
            api_config.unsplash_access_key,
            api_config.nasa_api_key
        )
        self.tts_service = TTSService(api_config.tts_openai_api_key)
        self.script_generator = ScriptGenerator()
        self.video_producer = VideoProducer(video_service_url)
        
    def health_check_all_services(self) -> Dict[str, bool]:
        """Check health of all services"""
        return {
            'news_scraper': self.news_scraper.health_check(),
            'video_producer': self.video_producer.health_check(),
            'tts_service': self.tts_service.test_connection(),
            'media_apis': bool(api_config.pexels_api_key and api_config.unsplash_access_key)
        }
    
    def generate_video_title(self, news_items: list) -> str:
        """Generate an engaging video title"""
        if news_items:
            # Use the first news item for title inspiration
            first_item = news_items[0]
            source = first_item.get('source', 'Space')
            return f"Latest Space News: {source} Updates & More!"
        else:
            titles = [
                "Amazing Space Discoveries This Week!",
                "Space Exploration Updates You Need to Know",
                "Incredible Cosmic News and Updates",
                "This Week in Space: Amazing Discoveries",
                "Space News: Latest Updates from the Cosmos"
            ]
            import random
            return random.choice(titles)
    
    def run_complete_workflow(self, 
                            target_duration: int = 120,
                            voice: str = "alloy") -> Dict[str, Any]:
        """
        Run the complete video generation workflow
        
        Args:
            target_duration: Target video duration in seconds
            voice: TTS voice to use
            
        Returns:
            Dictionary with workflow results
        """
        workflow_start = time.time()
        results = {
            'status': 'started',
            'timestamp': datetime.now().isoformat(),
            'steps': {},
            'errors': []
        }
        
        try:
            # Step 1: Health check
            logger.info("Step 1: Checking service health...")
            health_status = self.health_check_all_services()
            results['steps']['health_check'] = health_status
            
            failed_services = [service for service, status in health_status.items() if not status]
            if failed_services:
                error_msg = f"Services not available: {', '.join(failed_services)}"
                results['errors'].append(error_msg)
                logger.warning(error_msg)
            
            # Step 2: Scrape news
            logger.info("Step 2: Scraping latest space news...")
            news_items = self.news_scraper.get_latest_space_news()
            results['steps']['news_scraping'] = {
                'items_found': len(news_items),
                'sources': list(set(item.get('source', 'Unknown') for item in news_items))
            }
            
            # Step 3: Generate script
            logger.info("Step 3: Generating video script...")
            news_content = self.news_scraper.format_news_for_script(news_items)
            script = self.script_generator.create_full_script(news_content, target_duration)
            results['steps']['script_generation'] = {
                'word_count': len(script.split()),
                'estimated_duration': len(script.split()) / 150 * 60  # 150 words per minute
            }
            
            # Step 4: Generate TTS audio
            logger.info("Step 4: Generating text-to-speech audio...")
            audio_file_path = self.tts_service.generate_speech(script, voice)
            if not audio_file_path:
                raise Exception("Failed to generate TTS audio")
            
            results['steps']['tts_generation'] = {
                'audio_file': audio_file_path,
                'voice_used': voice
            }
            
            # Step 5: Collect media
            logger.info("Step 5: Collecting media from various sources...")
            media_items = self.media_collector.get_curated_space_media(15)
            results['steps']['media_collection'] = {
                'total_items': len(media_items),
                'sources': list(set(item.get('source', 'Unknown') for item in media_items)),
                'types': list(set(item.get('type', 'Unknown') for item in media_items))
            }
            
            if not media_items:
                raise Exception("No media items collected")
            
            # Step 6: Prepare for video production
            logger.info("Step 6: Preparing for video production...")
            media_urls = self.video_producer.prepare_media_urls(media_items)
            video_title = self.generate_video_title(news_items)
            
            # For now, we'll assume the audio file is web-accessible
            # In production, you'd upload it to a hosting service
            audio_url = audio_file_path  # This would be a web URL in production
            
            results['steps']['video_preparation'] = {
                'media_urls_count': len(media_urls),
                'video_title': video_title,
                'audio_ready': bool(audio_url)
            }
            
            # Step 7: Create video
            logger.info("Step 7: Creating final video...")
            video_result = self.video_producer.create_video(
                audio_url=audio_url,
                media_urls=media_urls,
                title=video_title
            )
            
            if video_result:
                results['steps']['video_production'] = video_result
                results['status'] = 'completed'
                results['final_video'] = video_result
            else:
                raise Exception("Video production failed")
            
        except Exception as e:
            error_msg = f"Workflow failed: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            results['status'] = 'failed'
        
        finally:
            # Cleanup temporary files
            if 'tts_generation' in results['steps']:
                audio_file = results['steps']['tts_generation'].get('audio_file')
                if audio_file and os.path.exists(audio_file):
                    try:
                        os.unlink(audio_file)
                        logger.info(f"Cleaned up temporary audio file: {audio_file}")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup audio file: {e}")
        
        workflow_duration = time.time() - workflow_start
        results['total_duration_seconds'] = workflow_duration
        results['completed_at'] = datetime.now().isoformat()
        
        logger.info(f"Workflow completed in {workflow_duration:.2f} seconds with status: {results['status']}")
        return results
    
    def run_scheduled_workflow(self, schedule_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run workflow on a schedule with specific configuration
        
        Args:
            schedule_config: Configuration for scheduled run
            
        Returns:
            Workflow results
        """
        logger.info(f"Starting scheduled workflow: {schedule_config}")
        
        # Extract configuration
        target_duration = schedule_config.get('duration', 120)
        voice = schedule_config.get('voice', 'alloy')
        
        return self.run_complete_workflow(target_duration, voice)