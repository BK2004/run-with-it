import soundfile as sf
import numpy as np
from scipy.signal import resample_poly
from pathlib import Path
import os

path = "output.wav"
mono_16_path = "test.wav"

def to_mono_16k(in_path, out_path, target_sr=16000, dtype="int16"):
    # Read (always_2d=True gives shape [samples, channels])
    y, sr = sf.read(in_path, always_2d=True)
    # Downmix to mono
    y = y.mean(axis=1)
    # Resample if needed (poly resampling preserves quality)
    if sr != target_sr:
        # Up/down factors for resample_poly
        from math import gcd
        g = gcd(sr, target_sr)
        up, down = target_sr // g, sr // g
        y = resample_poly(y, up, down)
    # Normalize/clamp and convert dtype
    if dtype == "int16":
        y = np.clip(y, -1.0, 1.0)
        y = (y * 32767.0).astype(np.int16)
        subtype = "PCM_16"
    else:
        y = y.astype(np.float32)
        subtype = "FLOAT"

    sf.write(out_path, y, target_sr, subtype=subtype)

import nemo.collections.asr as nemo_asr
asr_model = nemo_asr.models.ASRModel.from_pretrained("stt_en_fastconformer_transducer_large")

def transcribe():
    to_mono_16k(path, mono_16_path)
    transcription = asr_model.transcribe([mono_16_path])

    print("Transcrition:")
    print(transcription)

    os.remove(mono_16_path)
    return transcription