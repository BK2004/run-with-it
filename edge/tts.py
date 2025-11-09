import gtts
import io
import os
from pydub import AudioSegment
from pydub.playback import play

def text_to_speech(text: str) -> list[int] | None:
	try:
		gtts.gTTS(text, slow=True).save("AUDIO_TMP.wav")

		with open("AUDIO_TMP.wav", "rb") as f:
			audio_data = io.BytesIO(f.read())

		sound = AudioSegment.from_file("AUDIO_TMP.wav")

		# Play the audio
		play(sound)
		
		os.remove("AUDIO_TMP.wav")
		return audio_data.getvalue()
		
	except Exception as _:
		os.remove("AUDIO_TMP.wav") if os.path.exists("AUDIO_TMP.wav") else None
		return FileNotFoundError("Text could not be converted to speech.")
	