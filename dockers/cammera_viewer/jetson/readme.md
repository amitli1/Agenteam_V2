# camera_viewer

Runs `system_tests/rtsp_video_tester.py` inside a container to preview an RTSP
stream (e.g. the Gazebo simulated cameras) using OpenCV.

Follows the same pattern as the other `dockers/*/jetson` services: the
repository is bind-mounted into the container (no `COPY` of application
files), so code changes on the host are picked up without rebuilding the
image.

## Configuration (via `docker-compose.yml` environment)

- `RTSP_ADDRESS` - the RTSP url to open, e.g. `rtsp://localhost:8554/gazebo_cam1`
- `SCREEN_SIZE_PERCENT` - size of the preview window as a percentage (1-100)
  of the full screen resolution (detected from the host X server)

## X11 display

The container needs access to the host's X server to show the preview
window. On the host, before `docker compose up`, allow local X connections:

```bash
xhost +local:docker
```

The `DISPLAY` environment variable and `/tmp/.X11-unix` socket are already
wired up in `docker-compose.yml` (`network_mode: host` is used, so `DISPLAY`
from the host, e.g. `:0` or `:1`, is reused as-is).

## Run

```bash
cd dockers/cammera_viewer/jetson
export UID GID
docker compose up --build
```

Press `q` in the preview window to quit.

