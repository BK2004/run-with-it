from fastapi import FastAPI, Request
from fastapi.responses import Response
from edge.tts import text_to_speech
from pydantic import BaseModel
from agent.states import RunningState
from agent.llm import make_decisions, classify
import edge.record as record
import edge.ASR as asr
import io
import csv
import uvicorn
import datetime
import threading
import json
from agent import strava_api
import random
from pydub import AudioSegment
from pydub.playback import play

beep = AudioSegment.from_file("beep-06.wav")


app = FastAPI()

data = []
mode_txt = None

running_state: RunningState | None = None
last_button_state = False
		

def retrieve_metrics():
	global data
	out = {
		"ax": 0,
		"ay": 0,
		"az": 0,
		"temperature": 0
	}
	# average out metrics
	if len(data) > 0:
		retrieved = data
		data = []
		for datapoint in retrieved:
			out["ax"] += abs(datapoint["ax"]) # Use abs to get measure of movement
			out["ay"] += abs(datapoint["ay"])
			out["az"] += abs(datapoint["az"])
			out["temperature"] += datapoint["temperature"]
		
		out["ax"] /= len(retrieved)
		out["ay"] /= len(retrieved)
		out["az"] /= len(retrieved)
		out["temperature"] /= len(retrieved)
	return out

def run_agent():
	global running_state
	global mode_txt
	while True:
		goal = classify(mode_txt)
		if goal == 'Stop':
			strava_api.create_strava_post(data = {
				"name": "11/9",
				"type": "Run",
				"start_date_local": running_state.starttime,
				"elapsed_time": random.randint(900, 3000),
				"private": True,
				"description": "Something light",
				"distance": random.randint(10, 23),
			})
			running_state = None
			return
			
		running_state.goal = goal
		decisions = make_decisions(running_state)
		if 'get_metrics' in decisions:
			metrics = retrieve_metrics()
			running_state.ax = metrics.ax
			running_state.ay = metrics.ay
			running_state.az = metrics.az
			running_state.metrics_timestamp = datetime.datetime.now()
		if 'send_feedback' in decisions:
			running_state.feedback_timestamp = datetime.datetime.now()
			text_to_speech("You're missing your goal!")

class Mode(BaseModel):
	mode: str

@app.get("/mode", response_class=Response)
async def read_mode(mode: Mode):
	audio = text_to_speech(mode.mode)
	return Response(content=audio, media_type="audio/wav")

@app.get("/press", response_class=Response)
async def read_press():
	play(beep)
	await record.start_recording(True)
	return Response(content="Success", media_type="text/plain")

@app.get("/release", response_class=Response)
async def read_stop():
	global mode_txt
	global running_state
	record.stop_recording()
	mode_txt = asr.transcribe()
	if running_state is None:
		metrics = retrieve_metrics()
		running_state = RunningState(
			feedback_timestamp=datetime.datetime.now(),
			metrics_timestamp=datetime.datetime.now(),
			ax=metrics["ax"],
			ay=metrics["ay"],
			az=metrics["az"],
			temperature=metrics["temperature"],
			goal=mode_txt,
			starttime=datetime.datetime.now()
		)

		threading.Thread(target=run_agent).run()
	return Response(content="Success", media_type="text/plain")

@app.post("/data")
async def read_data(request: Request):
	global last_button_state
	global data
	global mode_txt
	body = await request.body()
	decoded = body.decode()
	reader = csv.reader(io.StringIO(decoded))
	for row in reader:
		data.append({
			"ax": float(row[0]),
			"ay": float(row[1]),
			"az": float(row[2]),
			"temperature": float(row[3]),
			"button_pressed": int(row[4]),
		})
		button_state = data[-1]['button_pressed'] == 0
		if last_button_state != button_state:
			if button_state == True:
				await record.start_recording(True)
			else:
				record.stop_recording()
				mode_txt = asr.transcribe()
				if running_state is None:
					metrics = retrieve_metrics()
					running_state = RunningState(
						feedback_timestamp=datetime.datetime.now(),
						metrics_timestamp=datetime.datetime.now(),
						ax=metrics["ax"],
						ay=metrics["ay"],
						az=metrics["az"],
						temperature=metrics["temperature"],
						goal=mode_txt
					)

					threading.Thread(target=run_agent).run()

	return { "message": "Success" }

@app.get("/recent")
def read_recent():
	global data
	old = data
	data = []
	return old

@app.get("/mode")
def read_mode():
	global mode_txt
	old = mode_txt
	mode_txt = None
	return old

@app.post("/say")
def say(message: str):
	text_to_speech(message)

if __name__ == "__main__":
	uvicorn.run(
		"server:app",
		host='0.0.0.0',
		port=8000,
		reload=False,
		workers=1,
	)
