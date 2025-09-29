#!/usr/bin/env python3
"""
Main entry point for the YouTube Space Video Pipeline
"""
import os
import sys
import logging
import argparse
import json
from datetime import datetime

# Add pipeline to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline import WorkflowOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='YouTube Space Video Pipeline')
    parser.add_argument('--duration', type=int, default=120, 
                       help='Target video duration in seconds (default: 120)')
    parser.add_argument('--voice', type=str, default='alloy',
                       choices=['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer'],
                       help='TTS voice to use (default: alloy)')
    parser.add_argument('--news-service', type=str, default='http://localhost:5000',
                       help='News scraping service URL')
    parser.add_argument('--video-service', type=str, default='http://localhost:5000',
                       help='Video production service URL')
    parser.add_argument('--health-check', action='store_true',
                       help='Only run health check on all services')
    parser.add_argument('--output', type=str, default='workflow_result.json',
                       help='Output file for workflow results')
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = WorkflowOrchestrator(
        news_service_url=args.news_service,
        video_service_url=args.video_service
    )
    
    if args.health_check:
        logger.info("Running health check on all services...")
        health_status = orchestrator.health_check_all_services()
        
        print("\n=== Service Health Check ===")
        for service, status in health_status.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {service}: {'OK' if status else 'FAILED'}")
        
        all_healthy = all(health_status.values())
        print(f"\nOverall Status: {'✅ All services healthy' if all_healthy else '❌ Some services failed'}")
        return 0 if all_healthy else 1
    
    # Check required environment variables
    required_env_vars = [
        'TTS_OPENAI_API_KEY',
        'PEXELS_API_KEY', 
        'UNSPLASH_ACCESS_KEY'
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set the following environment variables:")
        for var in missing_vars:
            print(f"  export {var}=your_api_key_here")
        return 1
    
    # Run the complete workflow
    logger.info("Starting YouTube Space Video Pipeline...")
    logger.info(f"Configuration: duration={args.duration}s, voice={args.voice}")
    
    try:
        results = orchestrator.run_complete_workflow(
            target_duration=args.duration,
            voice=args.voice
        )
        
        # Save results to file
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print(f"\n=== Workflow Results ===")
        print(f"Status: {results['status'].upper()}")
        print(f"Duration: {results.get('total_duration_seconds', 0):.2f} seconds")
        print(f"Results saved to: {args.output}")
        
        if results['status'] == 'completed':
            final_video = results.get('final_video', {})
            if 'video_url' in final_video:
                print(f"🎬 Video URL: {final_video['video_url']}")
            print("✅ Pipeline completed successfully!")
            return 0
        else:
            print("❌ Pipeline failed!")
            if results.get('errors'):
                print("Errors:")
                for error in results['errors']:
                    print(f"  - {error}")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        print("\n⏹️  Pipeline stopped by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())