import torch, torchaudio
from torchaudio.functional import resample

path = "output.wav"
wave, sr = torchaudio.load(path)          # shape: (channels, time)

# downmix to mono
if wave.size(0) > 1:
    wave = wave.mean(dim=0, keepdim=True) # (1, time)

# resample to 16 kHz if needed
target_sr = 16000
if sr != target_sr:
    wave = resample(wave, sr, target_sr)
    sr = target_sr

# write back as WAV for NeMo to read
torchaudio.save("audio_mono16k.wav", wave, sr)

import nemo.collections.asr as nemo_asr
asr_model = nemo_asr.models.ASRModel.from_pretrained("stt_en_fastconformer_transducer_large")
print(asr_model.transcribe(["audio_mono16k.wav"]))
