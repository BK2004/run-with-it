import pyaudio
import wave
from pynput import keyboard
from ASR import transcribe

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"

record = True
p = pyaudio.PyAudio()

def on_press(key):
    if key.char == ('d'):
        global record 
        record = not record

def on_release(key):
    pass

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()
print("Recording")

frames = []

for i in range(100000):
    if record:
        data = stream.read(CHUNK)
        frames.append(data)
    else:
        exit

listener.stop()
listener.join()
print("Stopped Recording")


stream.stop_stream()
stream.close()
p.terminate()

wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(p.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames))
wf.close()

try:
    print("Transcription:")
    print(transcribe())
except:
    print("transcription failed")
