import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class SensorData:
    heartbeat: float
    temperature: float
    accelerometer: Dict[str, float]
    timestamp: float

class SensorStream:
    def __init__(self):
        self.data_buffer: List[SensorData] = []
        
    async def process_sensor_data(self, raw_data: Dict[str, Any]) -> SensorData:
        """Process incoming sensor data and return structured format"""
        sensor_data = SensorData(
            heartbeat=raw_data['heartbeat'],
            temperature=raw_data['temperature'],
            accelerometer={
                'x': raw_data['accelerometer']['x'],
                'y': raw_data['accelerometer']['y'],
                'z': raw_data['accelerometer']['z']
            },
            timestamp=raw_data['timestamp']
        )
        self.data_buffer.append(sensor_data)
        return sensor_data
        
    async def get_average_heartrate(self, window_size: int = 10) -> float:
        """Calculate average heartrate over last n readings"""
        if not self.data_buffer:
            return 0.0
        recent_data = self.data_buffer[-window_size:]
        return sum(data.heartbeat for data in recent_data) / len(recent_data)