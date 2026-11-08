FROM dustynv/pytorch:2.7-r36.4.0

RUN apt-get update && apt-get install -y \
    libasound2-dev \
    #python3-pyaudio \
    python3-numpy \
    python3-pip \
    portaudio19-dev \
    && apt-get clean

RUN apt-get install -y libspeexdsp-dev
RUN apt-get install -y ffmpeg
RUN apt-get update && apt-get install -y alsa-utils pulseaudio pulseaudio-utils libasound2-plugins

RUN pip install --no-cache-dir fastapi --index-url https://pypi.org/simple
RUN pip install --no-cache-dir uvicorn --index-url https://pypi.org/simple
RUN pip install --no-cache-dir openai --index-url https://pypi.org/simple
RUN pip install --no-cache-dir pyproj --index-url https://pypi.org/simple
RUN pip install --no-cache-dir PyAudio==0.2.14 --index-url https://pypi.org/simple
RUN pip install --no-cache-dir sounddevice --index-url https://pypi.org/simple
RUN pip install --no-cache-dir silero_vad --index-url https://pypi.org/simple
RUN pip install --no-cache-dir openwakeword --index-url https://pypi.org/simple
RUN pip install --no-cache-dir websockets --index-url https://pypi.org/simple
RUN pip install --no-cache-dir pydub --index-url https://pypi.org/simple


# Ground: \
RUN pip install --no-cache-dir google-genai --index-url https://pypi.org/simple
RUN pip install --no-cache-dir google-adk --index-url https://pypi.org/simple

WORKDIR /app