# ----------------------
# Whisper Docker - Jetson AGX Orin
# ----------------------
FROM dustynv/faster-whisper:r36.4.0-cu128-24.04

# ---------------------------------------------------------
# Python dependencies
# ---------------------------------------------------------
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    python-multipart \
    huggingface_hub \
    --index-url https://pypi.org/simple

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
ENV WHISPER_MODEL_REPO=mobiuslabsgmbh/faster-whisper-large-v3-turbo
ENV WHISPER_MODEL_DIR=/models/whisper-large-v3-turbo

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
COPY dockers/whisper/jetson/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

# ---------------------------------------------------------
# Start Whisper service
# ---------------------------------------------------------
ENTRYPOINT ["/entrypoint.sh"]
