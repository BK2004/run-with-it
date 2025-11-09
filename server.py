from fastapi import FastAPI
from fastapi.responses import Response
from edge.tts import text_to_speech
from pydantic import BaseModel

app = FastAPI()

class Mode(BaseModel):
	mode: str

@app.get("/mode")
async def read_mode(mode: Mode, response_class=Response):
	audio = text_to_speech(mode.mode)
	return Response(content=audio, media_type="audio/wav")