from pathlib import Path
import sys
from fastapi import FastAPI, UploadFile, File, Request
from faster_whisper import WhisperModel
import numpy as np
import time
import math
#import torch
import logging
import os
import glob

import uvicorn

from project_code.app_config.settings import app_settings

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))



app    = FastAPI()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

#logger.info(f"CUDA: {torch.cuda.is_available()}")

# Load model once at startup
NUM_BEAMS  = app_settings.audio.stt.num_beams
language   = app_settings.audio.language
model_size = app_settings.audio.stt.model_size

logging.info(f"Run with: {model_size}, NUM_BEAMS: {NUM_BEAMS}, language: {language}")


logger.info(f'Load: {model_size}')
model_path = os.environ.get(
    "WHISPER_MODEL_DIR",
    "/models/whisper-large-v3-turbo"
)
model = WhisperModel(
    model_path, # /mnt/nvme/models/whisper-large-v3-turbo/
    device="cuda",
    compute_type="float16"
)


@app.post("/transcribe/")
async def transcribe_api(file: UploadFile = File(None), request: Request = None):
    start = time.perf_counter()
    if file:
        logging.info("Received file to transcribe")
        temp_path = f"{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(await file.read())
        audio_input = temp_path

    elif request:
        logging.info("Received audio request to transcribe")
        data             = await request.json()
        audio_input_data = data.get("audio_input")

        if isinstance(audio_input_data, str):
            audio_input = audio_input_data  # treat as path
        elif isinstance(audio_input_data, list):
            audio_input = np.array(audio_input_data, dtype=np.float32)
        else:
            return {"error": "Invalid audio_input format. Must be path or list of floats."}
    else:
        return {"error": "No input provided."}

    # === Actual transcription logic starts here ===
    try:
        logging.info('Starting transcription')
        segments, info = model.transcribe(audio_input, beam_size=NUM_BEAMS, language=language)
        
        # Get first segment separately if needed
        try:
            first_segment = next(segments)
        except StopIteration:
            return {"error": "No speech detected."}

        logging.info(f"[{first_segment.start:.2f}s -> {first_segment.end:.2f}s] {first_segment.text}")

        transcription      = first_segment.text + " "
        log_probs          = [first_segment.avg_logprob]
        compression_ratios = [first_segment.compression_ratio]

        for segment in segments:
            logging.info(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
            transcription += segment.text + " "
            log_probs.append(segment.avg_logprob)
            compression_ratios.append(segment.compression_ratio)

        avg_logprob       = sum(log_probs) / len(log_probs) if log_probs else 0
        compression_ratio = sum(compression_ratios) / len(compression_ratios) if compression_ratios else 0
        confidence        = math.exp(avg_logprob)

        result = {
            "transcription"    : transcription.strip(),
            "compression_ratio": compression_ratio,
            "confidence"       : confidence
        }

        end = time.perf_counter()
        logging.info(f"Elapsed time: {end - start:.3f} seconds")
        
        return result

    except Exception as e:
        return {"error": str(e)}



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8013)
