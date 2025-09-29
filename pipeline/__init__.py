"""
YouTube Space Video Pipeline

An automated workflow for creating space-themed YouTube videos using:
- TTS OpenAI for narration
- Pexels, Unsplash, and NASA for media
- Docker services for news scraping and video production
"""

from .workflow_orchestrator import WorkflowOrchestrator
from .config import api_config, video_config, content_config

__version__ = "1.0.0"
__all__ = ['WorkflowOrchestrator', 'api_config', 'video_config', 'content_config']