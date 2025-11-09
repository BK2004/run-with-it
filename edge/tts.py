import gtts
import io
import os
from pydub import AudioSegment
from pydub.playback import play

def text_to_speech(text: str) -> list[int] | None:
	try:
		TMP = "AUDIO_TMP.mp3"
		gtts.gTTS(text, slow=False).save(TMP)

		with open(TMP, "rb") as f:
			audio_data = io.BytesIO(f.read())

		sound = AudioSegment.from_file(TMP, format="mp3")
		play(sound)
		# os.remove(TMP)
		return audio_data.getvalue()
		
	except Exception as _:
		os.remove(TMP) if os.path.exists(TMP) else None
		return FileNotFoundError("Text could not be converted to speech.")
	
text_to_speech("Run faster you fat piece of shit")