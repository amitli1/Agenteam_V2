from piper.voice import PiperVoice
import wave
import time
import os
import torch
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import logging
#
#
app    = FastAPI()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ---------------------------------------------------------
# Model path.
#
# In docker (jetson/hebrew_tts) the model file is mapped from
# the host disk into the container, e.g.:
#
#   /models/hebrew_tts/he_IL-saspeech-medium.onnx
#
# Locally (outside docker) it defaults to the path used during
# development.
# ---------------------------------------------------------
HEBREW_TTS_MODEL_PATH = os.environ.get(
    "HEBREW_TTS_MODEL_PATH",
    "/home/amitli/Documents/Hebrew_TTS_Model/he_IL-saspeech-medium.onnx"
)

logging.info(f"Loading Hebrew TTS model from: {HEBREW_TTS_MODEL_PATH}")
voice_model = PiperVoice.load(HEBREW_TTS_MODEL_PATH)

class TTSRequest(BaseModel):
    text: str

@app.post("/synthesize/")
async def synthesize_tts(request: TTSRequest):
    text = request.text
    try:
        chunks = list(voice_model.synthesize(text))
        if not chunks:
            return {"error": "No audio generated"}

        sample_rate = chunks[0].sample_rate
        audio_int16 = np.concatenate([chunk.audio_int16_array for chunk in chunks])

        # Convert to float32 samples in range [-1, 1] and return as a JSON
        # serializable list of floats (wrapped in a list so that callers can
        # do data["audio"][0] to get the actual samples array, e.g. in
        # create_hebrew_tts.py).
        audio_float32 = (audio_int16.astype(np.float32) / 32767.0)

        return {
            "audio": [audio_float32.tolist()],
            "sample_rate": sample_rate
        }
    except Exception as e:
        return {"error": str(e)}

def run_with_piper(voice_model, text, output_path):


    start_time = time.time()
    with wave.open(output_path, "wb") as wav_file:
        # synthesize_wav writes the audio frames and sets the wav format
        # (sample rate/width/channels) automatically based on the model.
        voice_model.synthesize_wav(text, wav_file)
    end_time = time.time()

    print(f"[{(end_time-start_time):.2f} seconds] Created: {output_path}")

def test_hebrew_piper_tts():

    # download from:
    # https://huggingface.co/rhasspy/piper-voices/tree/main/he/he_IL/saspeech/medium
    voice_model = PiperVoice.load(HEBREW_TTS_MODEL_PATH)

    run_with_piper(voice_model, "הגעתי ליעד", "/home/amitli/Documents/Hebrew_TTS/I_have_reached_the_destination.wav")
    run_with_piper(voice_model, "יעד לא נמצא", "/home/amitli/Documents/Hebrew_TTS/Destination_not_found.wav")
    run_with_piper(voice_model, "חכה רגע, אני עדיין בטיסה, ","/home/amitli/Documents/Hebrew_TTS/hold_on_still_flying.wav")
    run_with_piper(voice_model, "אני לא מבין, בבקשה תחזור על הפקודה, ",  "/home/amitli/Documents/Hebrew_TTS/I_dont_understand_please_repeat_command.wav")
    run_with_piper(voice_model, "אני מסתכל סביב הבניין", "/home/amitli/Documents/Hebrew_TTS/Destination_not_found.wav")
    run_with_piper(voice_model, "לא קיים רחפן ראשי, ", "/home/amitli/Documents/Hebrew_TTS/No_master_drone.wav")
    run_with_piper(voice_model, "לא קיים רחפן משני, ", "/home/amitli/Documents/Hebrew_TTS/No_slave_drone.wav")
    run_with_piper(voice_model, "מה עלי לחפש", "/home/amitli/Documents/Hebrew_TTS/What_should_I_look_for.wav")


if __name__ == "__main__":
    #test_hebrew_piper_tts()
    logging.info("CUDA: {}".format(torch.cuda.is_available()))
    uvicorn.run(app, host="0.0.0.0", port=8002)

