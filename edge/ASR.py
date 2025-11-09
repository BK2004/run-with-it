import nemo.collections.asr as nemo_asr
asr_model = nemo_asr.models.ASRModel.from_pretrained("nvidia/parakeet-tdt-0.6b-v2")

def transcribe(PATH):
    transcript = asr_model.transcribe([PATH])[0].text
    return transcript