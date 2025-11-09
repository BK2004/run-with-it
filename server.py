from time import sleep
from fastapi import FastAPI
from fastapi.responses import Response
from edge.tts import text_to_speech
from pydantic import BaseModel
import edge.record as record
import edge.ASR as asr
from pydub import AudioSegment
from pydub.playback import play

beep = AudioSegment.from_file("beep-06.wav")


app = FastAPI()

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
	record.stop_recording()
	asr_output = asr.transcribe()
	play(beep)
	return Response(content="Success", media_type="text/plain")