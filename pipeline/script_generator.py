"""
Script generation service for creating engaging video content
"""
import random
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ScriptGenerator:
    def __init__(self):
        self.intro_templates = [
            "Welcome back to our space exploration journey!",
            "Greetings, space enthusiasts!",
            "Today we're diving into the fascinating world of space!",
            "Get ready for another incredible space adventure!",
            "Welcome to today's cosmic update!"
        ]
        
        self.transition_phrases = [
            "But that's not all...",
            "Speaking of space exploration...",
            "This brings us to our next story...",
            "In related news...",
            "Meanwhile, in space...",
            "Let's explore this further...",
            "This discovery leads us to..."
        ]
        
        self.outro_templates = [
            "That's all for today's space update. Keep looking up!",
            "Thanks for joining us on this cosmic journey. Until next time!",
            "Stay curious about the universe around us. See you next time!",
            "The universe never stops amazing us. Thanks for watching!",
            "Keep exploring, keep wondering. We'll see you in the next video!"
        ]
    
    def generate_intro(self) -> str:
        """Generate an engaging intro"""
        return random.choice(self.intro_templates)
    
    def generate_transition(self) -> str:
        """Generate a transition phrase"""
        return random.choice(self.transition_phrases)
    
    def generate_outro(self) -> str:
        """Generate an engaging outro"""
        return random.choice(self.outro_templates)
    
    def enhance_news_content(self, news_content: str) -> str:
        """Enhance news content with engaging language"""
        if not news_content:
            return self.generate_fallback_content()
        
        # Add engaging elements
        enhanced_parts = []
        sentences = news_content.split('. ')
        
        for i, sentence in enumerate(sentences):
            enhanced_parts.append(sentence)
            
            # Add transitions between major points
            if i > 0 and i < len(sentences) - 1 and random.random() < 0.3:
                enhanced_parts.append(self.generate_transition())
        
        return '. '.join(enhanced_parts)
    
    def generate_fallback_content(self) -> str:
        """Generate fallback content when no news is available"""
        fallback_topics = [
            "Space exploration continues to push the boundaries of human knowledge. From the International Space Station orbiting 400 kilometers above Earth, astronauts conduct groundbreaking research that benefits all of humanity.",
            
            "The search for life beyond Earth remains one of our most compelling quests. Mars, with its ancient riverbeds and polar ice caps, holds tantalizing clues about the possibility of past or present life.",
            
            "Our understanding of the universe expands daily through powerful telescopes like Hubble and James Webb. These incredible instruments reveal distant galaxies, nebulae, and exoplanets that challenge our understanding of cosmic evolution.",
            
            "Commercial space companies are revolutionizing access to space. Reusable rockets and private space stations are making space more accessible than ever before, opening new frontiers for exploration and discovery."
        ]
        
        selected_topics = random.sample(fallback_topics, min(2, len(fallback_topics)))
        return " ".join(selected_topics)
    
    def create_full_script(self, news_content: str, target_duration: int = 120) -> str:
        """
        Create a complete video script
        
        Args:
            news_content: Content from news sources
            target_duration: Target duration in seconds (for pacing)
            
        Returns:
            Complete script text
        """
        script_parts = []
        
        # Intro
        script_parts.append(self.generate_intro())
        
        # Main content
        if news_content:
            enhanced_content = self.enhance_news_content(news_content)
            script_parts.append(enhanced_content)
        else:
            script_parts.append(self.generate_fallback_content())
        
        # Add some space facts or insights
        space_insights = [
            "Did you know that a day on Venus is longer than its year?",
            "The International Space Station travels at 28,000 kilometers per hour.",
            "There are more possible games of chess than atoms in the observable universe.",
            "One million Earths could fit inside the Sun.",
            "Neutron stars are so dense that a teaspoon would weigh 6 billion tons."
        ]
        
        if random.random() < 0.7:  # 70% chance to include a space fact
            script_parts.append(random.choice(space_insights))
        
        # Outro
        script_parts.append(self.generate_outro())
        
        # Join all parts
        full_script = " ".join(script_parts)
        
        # Ensure appropriate length (roughly 150 words per minute for speech)
        words_per_minute = 150
        target_words = (target_duration / 60) * words_per_minute
        current_words = len(full_script.split())
        
        if current_words < target_words * 0.8:
            # Add more content if too short
            additional_content = self.generate_fallback_content()
            script_parts.insert(-1, additional_content)
            full_script = " ".join(script_parts)
        
        return full_script