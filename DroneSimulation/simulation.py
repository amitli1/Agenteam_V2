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
from typing import Any, List, Optional

import uvicorn
import yaml
from fastapi import Body, FastAPI, HTTPException, WebSocket, WebSocketDisconnect

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



def _normalize_waypoint(wp) -> dict:
    """Accept a waypoint either as {"lat":.., "lon":.., "alt":..} or as a
    plain (lat, lon, alt) list/tuple (as sent by QuadManager.fly_to_wp)."""
    if isinstance(wp, dict):
        return {"lat": float(wp["lat"]), "lon": float(wp["lon"]), "alt": float(wp["alt"])}
    if isinstance(wp, (list, tuple)) and len(wp) == 3:
        lat, lon, alt = wp
        return {"lat": float(lat), "lon": float(lon), "alt": float(alt)}
    raise HTTPException(
        status_code=422,
        detail=f"Invalid waypoint format: {wp!r}. Expected {{lat, lon, alt}} or [lat, lon, alt].",
    )


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



@app.post("/mission")
async def post_mission(waypoints: List[Any] = Body(...)):
    wp_dicts = [_normalize_waypoint(wp) for wp in waypoints]
    await drone.start_mission(wp_dicts)
    return {"status": "ok", "total_waypoints": len(wp_dicts)}


@app.post("/return")
async def post_return():
    await drone.return_home()
    return {"status": "ok"}


@app.websocket("/ws/drone-status")
async def ws_drone_status(websocket: WebSocket):
    await websocket.accept()
    logger.info("Telemetry client connected")
    try:
        while True:
            await websocket.send_json(drone.telemetry())
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        logger.info("Telemetry client disconnected")


def main():
    port = int(config["quad_port"])
    logger.info(f"Starting drone simulation on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

