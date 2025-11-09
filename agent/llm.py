from openai import OpenAI
import os
import dotenv
from .states import RunningState
from .prompts import prompt_plan, classify_prompt
import json
import random

dotenv.load_dotenv()

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("OPENROUTER_API_KEY"),
)

def classify(goal_text: str):
	if goal_text.lower().find("stop") is not None:
		return "Stop"
	else:
		return f"Zone {random.random()}"

def make_decisions(state: RunningState):
	response = json.loads(client.chat.completions.create(
		extra_body={},
		model="nvidia/nemotron-nano-9b-v2:free",
		messages=[
			{
				"role": "user",
				"content": prompt_plan.format(goal=state.goal, ax=state.ax, ay=state.ay, az=state.az, temperature=state.temperature, metrics_timestamp=state.metrics_timestamp, feedback_timestamp=state.feedback_timestamp)
			}
		]
	).choices[0].message.content)
	return response