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
RUN pip install --no-cache-dir smolagents --index-url https://pypi.org/simple
RUN pip install --no-cache-dir SQLAlchemy --index-url https://pypi.org/simple
RUN pip install --no-cache-dir openai --index-url https://pypi.org/simple
RUN pip install --no-cache-dir shapely --index-url https://pypi.org/simple
RUN pip install --no-cache-dir pyproj --index-url https://pypi.org/simple
RUN pip install --no-cache-dir gradio --index-url https://pypi.org/simple
RUN pip install --no-cache-dir selenium --index-url https://pypi.org/simple
RUN pip install --no-cache-dir diskcache --index-url https://pypi.org/simple
RUN pip install --no-cache-dir multiprocess --index-url https://pypi.org/simple
RUN pip install --no-cache-dir opentelemetry-api --index-url https://pypi.org/simple
RUN pip install --no-cache-dir opentelemetry-sdk --index-url https://pypi.org/simple
RUN pip install --no-cache-dir openinference-instrumentation-openai --index-url https://pypi.org/simple
RUN pip install --no-cache-dir openinference-instrumentation-smolagents --index-url https://pypi.org/simple
RUN pip install --no-cache-dir opentelemetry-exporter-otlp --index-url https://pypi.org/simple
RUN pip install --no-cache-dir PyAudio==0.2.14 --index-url https://pypi.org/simple
RUN pip install --no-cache-dir sounddevice --index-url https://pypi.org/simple
RUN pip install --no-cache-dir silero_vad --index-url https://pypi.org/simple
RUN pip install --no-cache-dir speexdsp_ns --index-url https://pypi.org/simple
RUN pip install --no-cache-dir openwakeword --index-url https://pypi.org/simple
RUN pip install --no-cache-dir dash --index-url https://pypi.org/simple --ignore-installed blinker
RUN pip install --no-cache-dir dash-bootstrap-components --index-url https://pypi.org/simple
RUN pip install --no-cache-dir openai-agents --index-url https://pypi.org/simple
RUN pip install --no-cache-dir websockets --index-url https://pypi.org/simple

WORKDIR /app
