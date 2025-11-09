import asyncio
import speech_recognition as sr
from typing import Optional, Dict

class VoiceCommandProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.activity_goals = {
            "gen1": (90, 110),  # Light activity
            "gen2": (110, 130), # Moderate activity
            "gen3": (130, 150), # Vigorous activity
            "gen4": (150, 170), # High intensity
            "gen5": (170, 190)  # Maximum effort
        }
        
    async def process_voice_command(self, audio_data: bytes) -> Optional[Dict[str, tuple]]:
        """Process voice command and return activity goal heart rate range"""
        try:
            text = await self.speech_to_text(audio_data)
            return self.classify_activity_goal(text)
        except Exception as e:
            print(f"Error processing voice command: {e}")
            return None
            
    async def speech_to_text(self, audio_data: bytes) -> str:
        """Convert speech to text using speech recognition"""
        try:
            with sr.AudioFile(audio_data) as source:
                audio = self.recognizer.record(source)
                return self.recognizer.recognize_google(audio)
        except Exception as e:
            print(f"Speech recognition error: {e}")
            raise