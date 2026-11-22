FROM dustynv/pytorch:2.7-r36.4.0

# python3-opencv (system package) ships with GStreamer support already built
# for Jetson, which is required to decode RTSP streams - avoid pip opencv.
RUN apt-get update && apt-get install -y \
    python3-opencv \
    && apt-get clean

# Used to query the real screen resolution from the host X server so we can
# size the preview window as a percentage of the full screen.
RUN pip install --no-cache-dir screeninfo --index-url https://pypi.org/simple

WORKDIR /app

