# ----------------------
# TTS Docker - Jetson AGX Orin (Kokoro)
# ----------------------
FROM dustynv/pytorch:2.7-r36.4.0-cu128-24.04

# ---------------------------------------------------------
# System dependencies
#
# espeak-ng is required by kokoro/misaki for phonemization
# fallback (out-of-vocabulary words).
# ---------------------------------------------------------
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    espeak-ng \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------
# Python dependencies
# ---------------------------------------------------------
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pydantic \
    huggingface_hub \
    sounddevice \
    kokoro \
    --index-url https://pypi.org/simple

RUN pip install --no-cache-dir \
    https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl

# ---------------------------------------------------------
# Hugging Face cache
#
# This is only used during the FIRST startup/download.
# The actual model is stored in /models.
# ---------------------------------------------------------
ENV HF_HOME=/root/.cache/huggingface
ENV HF_HUB_CACHE=/root/.cache/huggingface/hub
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface/transformers

# ---------------------------------------------------------
# Model configuration
# ---------------------------------------------------------
ENV TTS_MODEL_REPO=hexgrad/Kokoro-82M
ENV TTS_MODEL_DIR=/models/kokoro-82m

# ---------------------------------------------------------
# TTS device (cuda/cpu). Leave unset for auto-detect.
# ---------------------------------------------------------
ENV TTS_DEVICE=cuda

# ---------------------------------------------------------
# Python package root
# ---------------------------------------------------------
ENV PYTHONPATH=/app

# ---------------------------------------------------------
# Directories
# ---------------------------------------------------------
RUN mkdir -p \
    /root/.cache/huggingface \
    /root/.cache/huggingface/hub \
    /root/.cache/huggingface/transformers \
    /models \
    /app

# ---------------------------------------------------------
# Copy application
# Build context:
#   /mnt/nvme/repo/Agenteam_V2
#
# Source:
#   project_code/
#
# Destination:
#   /app/project_code/
# ---------------------------------------------------------
COPY project_code/ /app/project_code/

# ---------------------------------------------------------
# Working directory
# ---------------------------------------------------------
WORKDIR /app/project_code

# ---------------------------------------------------------
# Startup script
# ---------------------------------------------------------
COPY dockers/tts/jetson/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

# ---------------------------------------------------------
# Start TTS service
# ---------------------------------------------------------
ENTRYPOINT ["/entrypoint.sh"]
