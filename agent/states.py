from pydantic import BaseModel
from datetime import datetime

class RunningState(BaseModel):
	feedback_timestamp: datetime
	metrics_timestamp: datetime
	goal: str | None
	temperature: float
	ax: int
	ay: int
	az: int
	starttime: datetime