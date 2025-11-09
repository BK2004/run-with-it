import pyaudio
import wave
from pynput import keyboard
import threading

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
WAVE_OUTPUT_FILENAME = "output.wav"

record = True
p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

frames = []
record = False

async def start_recording(INPT):
    global frames
    frames = []
    p = pyaudio.PyAudio()
    global stream
    stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)
    global record
    record = INPT
    threading.Thread(target=update).start()

def update():
    while record: 
        data = stream.read(CHUNK)
        frames.append(data)

def stop_recording():
    global record
    record = False
    stream.stop_stream()
    stream.close()
    p.terminate()
    get_wav()

def get_wav():
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()