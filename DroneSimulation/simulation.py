"""
Drone simulation server.

Implements (see system_requirements.md):
  - REST API (FastAPI):
      POST /mission  - list of waypoints [{lat, lon, alt}, ...]
      POST /return   - no body, sends the drone back to the home position
  - WebSocket server:
      GET  /ws/drone-status - pushes a telemetry JSON message every 1 second

Configuration is read from simulation.yaml (next to this file).

Run directly:
    python simulation.py
"""

import asyncio
import logging
import math
import time
from pathlib import Path
from typing import List, Optional

import uvicorn
import yaml
from fastapi import Body, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, model_validator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("drone_simulation")

CONFIG_PATH = Path(__file__).parent / "simulation.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        cfg = yaml.safe_load(f)
    return cfg["general"]



class Waypoint(BaseModel):
    """A single mission waypoint: {"lat": .., "lon": .., "alt": ..}.

    Also accepts the plain [lat, lon, alt] list/tuple form (as sent by
    QuadManager.fly_to_wp / some legacy callers) for backward compatibility.
    """

    lat: float
    lon: float
    alt: float

    @model_validator(mode="before")
    @classmethod
    def _accept_list_form(cls, value):
        if isinstance(value, (list, tuple)):
            if len(value) != 3:
                raise ValueError(
                    f"Invalid waypoint format: {value!r}. Expected [lat, lon, alt]."
                )
            lat, lon, alt = value
            return {"lat": lat, "lon": lon, "alt": alt}
        return value


def _bearing(a: dict, b: dict) -> float:
    """Initial bearing in degrees (0-360) from point a to point b."""
    lat1 = math.radians(a["lat"])
    lat2 = math.radians(b["lat"])
    d_lon = math.radians(b["lon"] - a["lon"])

    x = math.sin(d_lon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(d_lon)
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360.0) % 360.0


def _lerp(a: float, b: float, frac: float) -> float:
    return a + (b - a) * frac


class DroneState:
    """Holds the simulated drone position/mission state.

    All time based math is computed on demand (no background stepping thread
    is required) based on wall-clock timestamps, so the state is always
    correct whenever it's read (REST response / telemetry tick).
    """

    def __init__(self, config: dict):
        self.step_duration = float(config["mission_step_duration"])
        self.home = {
            "lat": float(config["start_lat"]),
            "lon": float(config["start_lon"]),
            "alt": float(config["start_alt"]),
        }

        # generic movement schedule, used to compute current lat/lon/alt/yaw
        self._move_start_pos = dict(self.home)
        self._move_segments: List[dict] = []  # [{end_pos, start_time, end_time}]
        self._last_yaw = 0.0

        # mission specific tracking (only /mission touches these fields)
        self._mission_total = 0
        self._mission_start_time: Optional[float] = None
        self.last_mission_waypoint: Optional[dict] = None

        # flight_mode goes to MISSION for 3 seconds after every /mission call
        self._mission_mode_until: Optional[float] = None

        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # position / movement
    # ------------------------------------------------------------------
    def _current_position_and_yaw(self):
        now = time.time()

        if not self._move_segments:
            return dict(self._move_start_pos), self._last_yaw

        prev_pos = self._move_start_pos
        for seg in self._move_segments:
            if now < seg["end_time"]:
                start_time = seg["start_time"]
                end_time = seg["end_time"]
                if end_time <= start_time:
                    frac = 1.0
                else:
                    frac = (now - start_time) / (end_time - start_time)
                frac = max(0.0, min(1.0, frac))

                pos = {
                    "lat": _lerp(prev_pos["lat"], seg["end_pos"]["lat"], frac),
                    "lon": _lerp(prev_pos["lon"], seg["end_pos"]["lon"], frac),
                    "alt": _lerp(prev_pos["alt"], seg["end_pos"]["alt"], frac),
                }
                self._last_yaw = _bearing(prev_pos, seg["end_pos"])
                return pos, self._last_yaw

            prev_pos = seg["end_pos"]

        # all segments finished, sit at the last waypoint
        last_pos = dict(self._move_segments[-1]["end_pos"])
        return last_pos, self._last_yaw

    def _start_movement(self, waypoints: List[dict]):
        now = time.time()
        start_pos, _ = self._current_position_and_yaw()

        segments = []
        for i, wp in enumerate(waypoints):
            seg_start = now + i * self.step_duration
            seg_end = seg_start + self.step_duration
            segments.append({"end_pos": wp, "start_time": seg_start, "end_time": seg_end})

        self._move_start_pos = start_pos
        self._move_segments = segments

    # ------------------------------------------------------------------
    # public API used by the REST endpoints
    # ------------------------------------------------------------------
    async def start_mission(self, waypoints: List[dict]):
        async with self._lock:
            self._start_movement(waypoints)

            self._mission_total = len(waypoints)
            self._mission_start_time = time.time()
            self.last_mission_waypoint = waypoints[-1] if waypoints else None
            self._mission_mode_until = time.time() + 3.0
            logger.info(f"Mission started with {len(waypoints)} waypoints")

    async def return_home(self):
        async with self._lock:
            self._start_movement([dict(self.home)])
            logger.info("Returning to home position")

    # ------------------------------------------------------------------
    # telemetry
    # ------------------------------------------------------------------
    def _mission_progress(self):
        if self._mission_total == 0 or self._mission_start_time is None:
            return "0/0", True

        elapsed = time.time() - self._mission_start_time
        completed = int(elapsed // self.step_duration)
        completed = max(0, min(self._mission_total, completed))
        finished = completed >= self._mission_total
        return f"{completed}/{self._mission_total}", finished

    def _flight_mode(self):
        if self._mission_mode_until is not None and time.time() < self._mission_mode_until:
            return "MISSION"
        return "HOLD"

    def telemetry(self) -> dict:
        pos, yaw = self._current_position_and_yaw()
        progress, finished = self._mission_progress()

        return {
            "timestamp": int(time.time() * 1000),
            "is_armed": False,
            "flight_mode": self._flight_mode(),
            "lat": pos["lat"],
            "lon": pos["lon"],
            "alt": pos["alt"],
            "yaw": yaw,
            "horizontal_velocity": 1.0,
            "vertical_velocity": 1.0,
            "battery_voltage": 50.0,
            "in_air": True,
            "is_mission_finished": finished,
            "mission_progress": progress,
            "last_mission_waypoint": self.last_mission_waypoint,
        }


config = load_config()
drone = DroneState(config)

app = FastAPI(title="Drone Simulation")

# Allow any origin/host to connect (REST + WebSocket). Without this, some
# browser based clients would be blocked; it has no effect on plain python
# `websockets`/`requests` clients but is a safe, harmless default here.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Simple liveness/readiness probe, also useful to verify the REST API
    (and therefore the port/network path) is reachable before debugging the
    WebSocket endpoint."""
    return {"status": "ok"}



MISSION_EXAMPLE = [
    {"lat": 47.641467, "lon": -122.140165, "alt": 10.0},
    {"lat": 47.642796, "lon": -122.139558, "alt": 20.0},
]


@app.post("/mission")
async def post_mission(
    waypoints: List[Waypoint] = Body(
        ...,
        openapi_examples={
            "default": {
                "summary": "List of waypoints",
                "value": MISSION_EXAMPLE,
            }
        },
    )
):
    """Start a mission. Body must be a JSON array of waypoints, e.g.:

    [{"lat": .., "lon": .., "alt": ..}, {"lat": .., "lon": .., "alt": ..}, ...]
    """
    wp_dicts = [wp.model_dump() for wp in waypoints]
    await drone.start_mission(wp_dicts)
    return {"status": "ok", "total_waypoints": len(wp_dicts)}


@app.post("/return")
async def post_return():
    await drone.return_home()
    return {"status": "ok"}


@app.websocket("/ws/drone-status")
async def ws_drone_status(websocket: WebSocket):
    client = websocket.client
    try:
        await websocket.accept()
    except Exception:
        logger.exception(f"Failed to accept WebSocket handshake from {client}")
        return

    logger.info(f"Telemetry client connected: {client}")
    try:
        while True:
            await websocket.send_json(drone.telemetry())
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        logger.info(f"Telemetry client disconnected: {client}")
    except Exception:
        logger.exception(f"Telemetry loop error for client {client}")


def main():
    port = int(config["quad_port"])
    logger.info(f"Starting drone simulation on port {port}")
    logger.info(
        f"REST:      http://0.0.0.0:{port}/mission | /return | /health\n"
        f"WebSocket: ws://0.0.0.0:{port}/ws/drone-status"
    )
    uvicorn.run(app, host="0.0.0.0", port=port, ws="auto", log_level="info")


if __name__ == "__main__":
    main()

