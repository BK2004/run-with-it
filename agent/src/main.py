import asyncio
import os
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv
from stravalib.client import Client
from sensor_stream import SensorStream
from voice_processor import VoiceCommandProcessor

class FitnessAgent:
    def __init__(self):
        load_dotenv()
        self.strava_client = Client(access_token=os.getenv('STRAVA_ACCESS_TOKEN'))
        self.sensor_stream = SensorStream()
        self.voice_processor = VoiceCommandProcessor()
        self.current_activity_goal = None
        self.workout_data = []
        
    async def process_sensor_update(self, sensor_data: Dict[str, Any]):
        """Process incoming sensor data and provide voice feedback"""
        processed_data = await self.sensor_stream.process_sensor_data(sensor_data)
        self.workout_data.append(processed_data)
        
        if self.current_activity_goal:
            await self.check_heart_rate_zone(processed_data.heartbeat)
            
    async def process_voice_command(self, audio_data: bytes):
        """Process voice commands for activity goals"""
        goal = await self.voice_processor.process_voice_command(audio_data)
        if goal:
            self.current_activity_goal = goal
            
    async def upload_to_strava(self):
        """Upload workout data to Strava at the end of session"""
        if not self.workout_data:
            return
            
        # Format workout data for Strava
        # Implementation details for Strava upload would go here
        
    async def run(self):
        """Main loop to process incoming data"""
        try:
            while True:
                # Main processing loop would go here
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            await self.upload_to_strava()

if __name__ == "__main__":
    agent = FitnessAgent()
    asyncio.run(agent.run())