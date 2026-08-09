# ----------------------
#
#   Whisper Docker
#
# ----------------------
#
#     https://github.com/OpenNMT/CTranslate2/issues/1378
#
# ----------------------

#FROM uyiosaamadasun/ctranslate2_faster_whisper_v0:latest
FROM dustynv/faster-whisper:r36.4.0-cu128-24.04

RUN pip install --no-cache-dir fastapi --index-url https://pypi.org/simple
RUN pip install --no-cache-dir uvicorn --index-url https://pypi.org/simple
RUN pip install --no-cache-dir python-multipart --index-url https://pypi.org/simple


ENV HF_HOME=/root/.cache/huggingface
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface/transformers
RUN mkdir -p /root/.cache/huggingface/transformers

WORKDIR /app

COPY AgenTeam/ ./AgenTeam/

WORKDIR /app/AgenTeam

CMD ["python3", "audio/services/whisper_service.py"]

