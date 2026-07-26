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

# Load the TTS model once
if in_docker():
    logging.info(f"Start loading kokoro model (in docker)")
    pipeline = KPipeline(lang_code='a',
                         #model='/models/tts/kokoro-v1_0.pth',
                         device="cuda"
                         )
    logging.info(f"\tloaded")
else:
    logging.info('Start loading kokoro model (not docker)')
    pipeline = KPipeline(lang_code='a', device='cuda')
    #pipeline = KPipeline(lang_code='h', device='cuda')
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
