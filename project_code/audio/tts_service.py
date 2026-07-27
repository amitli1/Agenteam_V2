from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List
import numpy as np
from kokoro import KPipeline
import uvicorn
import os
import torch
import logging
import glob

def in_docker():
 return os.path.exists("/.dockerenv") or os.path.exists("/run/.dockerenv")

app    = FastAPI()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

logging.info("CUDA: {}".format(torch.cuda.is_available()))

# Device can be forced via the TTS_DEVICE env var (e.g. "cpu" on Intel/CPU-only
# hosts). If not set, fall back to cuda when available, otherwise cpu.
TTS_DEVICE = os.environ.get("TTS_DEVICE") or ("cuda" if torch.cuda.is_available() else "cpu")

# Load the TTS model once
if in_docker():
    logging.info(f"Start loading kokoro model (in docker, device={TTS_DEVICE})")
    pipeline = KPipeline(lang_code='a',
                         #model='/models/tts/kokoro-v1_0.pth',
                         device=TTS_DEVICE
                         )
    logging.info(f"\tloaded")
else:
    logging.info(f'Start loading kokoro model (not docker, device={TTS_DEVICE})')
    pipeline = KPipeline(lang_code='a', device=TTS_DEVICE)
    #pipeline = KPipeline(lang_code='h', device=TTS_DEVICE)
SAMPLE_RATE = 24000

class TTSRequest(BaseModel):
    text: str

@app.post("/synthesize/")
async def synthesize_tts(request: TTSRequest):
    text = request.text
    try:
        generator = pipeline(text, voice='am_adam')
        #generator = pipeline(text, voice='hm_omega', speed=1, split_pattern=r'\n+')
        audios = [audio.tolist() for _, _, audio in generator]
        return {
            "audio": audios,
            "sample_rate": SAMPLE_RATE
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    logging.info("CUDA: {}".format(torch.cuda.is_available()))
    uvicorn.run(app, host="0.0.0.0", port=8002)
