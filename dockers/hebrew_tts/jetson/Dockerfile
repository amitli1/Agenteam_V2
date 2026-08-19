# ----------------------
# Hebrew TTS Docker - Jetson AGX Orin (Piper)
# ----------------------
FROM dustynv/pytorch:2.7-r36.4.0-cu128-24.04

# ---------------------------------------------------------
# System dependencies
# ---------------------------------------------------------
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------
# Python dependencies
# ---------------------------------------------------------
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pydantic \
    piper-tts \
    --index-url https://pypi.org/simple

# ---------------------------------------------------------
# Model configuration
#
# The Hebrew Piper model (.onnx + .onnx.json) is NOT downloaded
# or baked into the image. It lives on the host disk and is
# mapped into the container at runtime (see docker-compose.yml).
# ---------------------------------------------------------
ENV HEBREW_TTS_MODEL_DIR=/models/hebrew_tts
ENV HEBREW_TTS_MODEL_FILE=he_IL-saspeech-medium.onnx
ENV HEBREW_TTS_MODEL_PATH=/models/hebrew_tts/he_IL-saspeech-medium.onnx

# ---------------------------------------------------------
# Python package root
# ---------------------------------------------------------
ENV PYTHONPATH=/app

# ---------------------------------------------------------
# Directories
# ---------------------------------------------------------
RUN mkdir -p \
    /models/hebrew_tts \
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
COPY dockers/hebrew_tts/jetson/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

# ---------------------------------------------------------
# Start Hebrew TTS service
# ---------------------------------------------------------
ENTRYPOINT ["/entrypoint.sh"]

