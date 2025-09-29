#!/usr/bin/env python3
"""
Scheduler for automated video generation
"""
import os
import sys
import time
import logging
import schedule
import json
from datetime import datetime, timedelta

# Add pipeline to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline import WorkflowOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class VideoScheduler:
    def __init__(self):
        self.orchestrator = WorkflowOrchestrator()
        self.last_run_file = 'last_run.json'
        
    def save_last_run(self, results):
        """Save information about the last run"""
        run_info = {
            'timestamp': datetime.now().isoformat(),
            'status': results.get('status'),
            'duration': results.get('total_duration_seconds'),
            'video_url': results.get('final_video', {}).get('video_url')
        }
        
        with open(self.last_run_file, 'w') as f:
            json.dump(run_info, f, indent=2)
    
    def get_last_run_info(self):
        """Get information about the last run"""
        try:
            with open(self.last_run_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
    
    def should_run_now(self):
        """Check if we should run based on last run time"""
        last_run = self.get_last_run_info()
        if not last_run:
            return True
        
        last_run_time = datetime.fromisoformat(last_run['timestamp'])
        time_since_last = datetime.now() - last_run_time
        
        # Don't run if last run was less than 2 hours ago and successful
        if time_since_last < timedelta(hours=2) and last_run.get('status') == 'completed':
            logger.info(f"Skipping run - last successful run was {time_since_last} ago")
            return False
        
        return True
    
    def run_scheduled_video_generation(self):
        """Run the video generation workflow"""
        logger.info("Scheduled video generation starting...")
        
        if not self.should_run_now():
            return
        
        try:
            # Health check first
            health_status = self.orchestrator.health_check_all_services()
            failed_services = [service for service, status in health_status.items() if not status]
            
            if failed_services:
                logger.warning(f"Some services are not healthy: {failed_services}")
                # Continue anyway - some services might recover
            
            # Run workflow with different configurations based on time of day
            current_hour = datetime.now().hour
            
            if 6 <= current_hour < 12:  # Morning
                config = {'duration': 90, 'voice': 'nova'}
            elif 12 <= current_hour < 18:  # Afternoon  
                config = {'duration': 120, 'voice': 'alloy'}
            else:  # Evening/Night
                config = {'duration': 150, 'voice': 'echo'}
            
            logger.info(f"Running workflow with config: {config}")
            results = self.orchestrator.run_scheduled_workflow(config)
            
            # Save results
            self.save_last_run(results)
            
            if results['status'] == 'completed':
                video_url = results.get('final_video', {}).get('video_url')
                logger.info(f"✅ Video generation completed successfully!")
                if video_url:
                    logger.info(f"🎬 Video URL: {video_url}")
                    
                    # Here you could add integration with YouTube API to upload
                    # or send notifications, etc.
                    
            else:
                logger.error(f"❌ Video generation failed: {results.get('errors', [])}")
                
        except Exception as e:
            logger.error(f"Scheduled run failed with exception: {e}")

def main():
    scheduler = VideoScheduler()
    
    # Schedule video generation
    # Run every 4 hours during active hours
    schedule.every(4).hours.do(scheduler.run_scheduled_video_generation)
    
    # Also run at specific times for better scheduling
    schedule.every().day.at("08:00").do(scheduler.run_scheduled_video_generation)
    schedule.every().day.at("14:00").do(scheduler.run_scheduled_video_generation)
    schedule.every().day.at("20:00").do(scheduler.run_scheduled_video_generation)
    
    logger.info("Video generation scheduler started")
    logger.info("Scheduled times: Every 4 hours, plus 8:00, 14:00, and 20:00 daily")
    
    # Run once immediately if no recent run
    if not scheduler.get_last_run_info():
        logger.info("No previous runs found, running immediately...")
        scheduler.run_scheduled_video_generation()
    
    # Keep the scheduler running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")

if __name__ == "__main__":
    main()