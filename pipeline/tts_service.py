"""
Text-to-Speech service using TTS OpenAI
"""
import requests
import logging
import tempfile
import os
from typing import Optional

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://ttsopenai.com/api/v1"
        
    def generate_speech(self, text: str, voice: str = "alloy", speed: float = 1.0) -> Optional[str]:
        """
        Generate speech from text and return path to audio file
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            speed: Speech speed (0.25 to 4.0)
            
        Returns:
            Path to generated audio file or None if failed
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': 'tts-1',
                'input': text,
                'voice': voice,
                'speed': speed,
                'response_format': 'mp3'
            }
            
            response = requests.post(
                f"{self.base_url}/audio/speech",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_file.write(response.content)
                temp_path = temp_file.name
            
            logger.info(f"Generated speech audio: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test if the TTS service is accessible"""
        try:
            # Try a simple request to test the API
            test_text = "Testing connection"
            result = self.generate_speech(test_text)
            
            if result:
                # Clean up test file
                try:
                    os.unlink(result)
                except:
                    pass
                return True
            return False
            
        except Exception as e:
            logger.error(f"TTS connection test failed: {e}")
            return False