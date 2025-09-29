# YouTube Space Video Pipeline

An automated workflow system for creating engaging space-themed YouTube videos using AI-powered narration, curated media from multiple sources, and automated video production.

## Features

- **Automated News Scraping**: Fetches latest space news from CNN, NASA, ESA, and Space.com RSS feeds
- **AI-Powered Narration**: Uses TTS OpenAI for high-quality text-to-speech generation
- **Multi-Source Media**: Collects images and videos from Pexels, Unsplash, and NASA's media library
- **Intelligent Script Generation**: Creates engaging video scripts with smooth transitions
- **Automated Video Production**: Combines audio and visuals into polished videos
- **Scheduled Execution**: Run workflows on autopilot with intelligent scheduling
- **Health Monitoring**: Built-in service health checks and error handling

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   News Sources  │    │   Media Sources  │    │   TTS Service   │
│   (RSS Feeds)   │    │ (Pexels/Unsplash │    │  (TTS OpenAI)   │
│                 │    │     /NASA)       │    │                 │
└─────────┬───────┘    └─────────┬────────┘    └─────────┬───────┘
          │                      │                       │
          ▼                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Workflow Orchestrator                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │    News     │ │   Script    │ │    Media    │ │    Video    ││
│  │  Scraper    │ │ Generator   │ │ Collector   │ │  Producer   ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌─────────────────────┐
                    │   Final Video       │
                    │   (MP4 Output)      │
                    └─────────────────────┘
```

## Quick Start

### 1. Prerequisites

- Docker and Docker Compose
- Python 3.10+
- API keys for:
  - [TTS OpenAI](https://ttsopenai.com/)
  - [Pexels](https://www.pexels.com/api/)
  - [Unsplash](https://unsplash.com/developers)
  - [NASA](https://api.nasa.gov/) (optional - DEMO_KEY works)

### 2. Setup

1. **Clone and setup environment**:
   ```bash
   git clone <repository-url>
   cd youtube-space-pipeline
   cp .env.example .env
   ```

2. **Configure API keys** in `.env`:
   ```bash
   TTS_OPENAI_API_KEY=your_tts_openai_api_key_here
   PEXELS_API_KEY=your_pexels_api_key_here
   UNSPLASH_ACCESS_KEY=your_unsplash_access_key_here
   NASA_API_KEY=DEMO_KEY
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-pipeline.txt
   ```

### 3. Start Services

**Option A: Docker Compose (Recommended)**
```bash
# Start the video production service
docker-compose up -d

# Run a single workflow
docker-compose --profile pipeline up pipeline-orchestrator
```

**Option B: Local Development**
```bash
# Start the video service
python app.py

# In another terminal, run the pipeline
python main.py --duration 120 --voice alloy
```

### 4. Run Workflows

**Single Run**:
```bash
python main.py --duration 120 --voice nova
```

**Health Check**:
```bash
python main.py --health-check
```

**Scheduled Runs**:
```bash
python scheduler.py
```

## Usage Examples

### Basic Video Generation
```bash
# Generate a 2-minute video with default settings
python main.py --duration 120

# Use a different voice
python main.py --duration 90 --voice echo

# Custom service URLs
python main.py --news-service http://localhost:5000 --video-service http://localhost:5001
```

### Programmatic Usage
```python
from pipeline import WorkflowOrchestrator

# Initialize orchestrator
orchestrator = WorkflowOrchestrator()

# Run complete workflow
results = orchestrator.run_complete_workflow(
    target_duration=120,
    voice='alloy'
)

if results['status'] == 'completed':
    video_url = results['final_video']['video_url']
    print(f"Video ready: {video_url}")
```

### Scheduled Automation
```python
from scheduler import VideoScheduler

scheduler = VideoScheduler()

# Run every 4 hours
import schedule
schedule.every(4).hours.do(scheduler.run_scheduled_video_generation)

# Keep running
while True:
    schedule.run_pending()
    time.sleep(60)
```

## Configuration

### Video Settings
```python
# In pipeline/config.py
video_config = VideoConfig(
    output_resolution=(1920, 1080),
    fps=30,
    video_duration_range=(60, 180),
    transition_duration=0.5,
    image_display_duration=4.0
)
```

### Content Settings
```python
content_config = ContentConfig(
    space_keywords=[
        'space exploration', 'nasa', 'mars', 'moon',
        'astronaut', 'rocket launch', 'galaxy'
    ],
    max_headlines=5,
    script_length_words=200
)
```

## API Endpoints

The Docker service provides these endpoints:

- `GET /health` - Health check
- `GET /scrape-news` - Get latest space news
- `POST /process` - Create video from audio and media URLs

## Workflow Steps

1. **Health Check**: Verify all services are running
2. **News Scraping**: Fetch latest space news from RSS feeds
3. **Script Generation**: Create engaging video script from news
4. **TTS Generation**: Convert script to high-quality audio
5. **Media Collection**: Gather relevant images/videos from multiple sources
6. **Video Production**: Combine audio and visuals into final video

## Output

The pipeline generates:
- **MP4 video file**: Final produced video
- **Workflow results**: JSON file with detailed execution information
- **Logs**: Comprehensive logging of all operations

Example output structure:
```json
{
  "status": "completed",
  "timestamp": "2025-01-27T10:30:00",
  "steps": {
    "news_scraping": {"items_found": 5},
    "script_generation": {"word_count": 180},
    "tts_generation": {"audio_file": "/tmp/audio.mp3"},
    "media_collection": {"total_items": 15},
    "video_production": {"video_url": "https://..."}
  },
  "final_video": {
    "video_url": "https://example.com/video.mp4",
    "duration": 125.5,
    "title": "Latest Space News: NASA Updates & More!"
  }
}
```

## Monitoring and Logging

- **Health Checks**: Built-in service monitoring
- **Comprehensive Logging**: All operations logged with timestamps
- **Error Handling**: Graceful failure handling with detailed error messages
- **Cleanup**: Automatic temporary file cleanup

## Customization

### Adding New Media Sources
```python
# In pipeline/media_collector.py
def search_new_source(self, query: str) -> List[Dict[str, Any]]:
    # Implement new media source
    pass
```

### Custom Script Templates
```python
# In pipeline/script_generator.py
self.intro_templates.append("Your custom intro template")
```

### Voice Options
Available TTS voices: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`

## Troubleshooting

### Common Issues

1. **Service Health Check Failures**:
   ```bash
   python main.py --health-check
   ```

2. **Missing API Keys**:
   - Check `.env` file configuration
   - Verify API key validity

3. **Docker Service Not Running**:
   ```bash
   docker-compose up -d
   docker-compose logs space-video-server
   ```

4. **TTS Generation Fails**:
   - Verify TTS OpenAI API key
   - Check internet connectivity
   - Review script length (very long scripts may fail)

### Debug Mode
```bash
# Enable verbose logging
export PYTHONPATH=.
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from pipeline import WorkflowOrchestrator
orchestrator = WorkflowOrchestrator()
results = orchestrator.run_complete_workflow()
"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs in `pipeline.log`
3. Open an issue with detailed error information