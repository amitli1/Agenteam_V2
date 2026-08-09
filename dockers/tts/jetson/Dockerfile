# ----------------------
#
#   TTS Docker
#
# ----------------------
FROM dustynv/pytorch:2.7-r36.4.0-cu128-24.04

RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    && apt-get clean

RUN pip install --no-cache-dir fastapi --index-url https://pypi.org/simple
RUN pip install --no-cache-dir uvicorn --index-url https://pypi.org/simple
RUN pip install --no-cache-dir pydantic --index-url https://pypi.org/simple
RUN pip install --no-cache-dir kokoro --index-url https://pypi.org/simple
RUN pip install --no-cache-dir sounddevice --index-url https://pypi.org/simple
RUN pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
WORKDIR /app
COPY AgenTeam/ ./AgenTeam/

WORKDIR /app/AgenTeam
CMD ["python3", "audio/services/tts_service.py"]
