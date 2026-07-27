# Drone Simulation

Simulates a drone that can be controlled via REST API and reports telemetry
over a WebSocket, matching the interface expected by
`project_code/air/quad_manager.py`.

## Configuration

Settings are read from `simulation.yaml`:

```yaml
general:
  quad_port: 8001
  start_lat: 47.641467
  start_lon: -122.14016489999999
  start_alt: 0.0
  mission_step_duration: 3
```

## Run locally

```bash
pip install -r requirements.txt
python simulation.py
```

## Run with Docker

```bash
docker compose up --build
```

## REST API

- `POST /mission` - body: JSON array of `{ "lat": .., "lon": .., "alt": .. }`.
  The drone flies to each waypoint in order, spending `mission_step_duration`
  seconds per leg.
- `POST /return` - no body. Sends the drone back to the home position
  (`start_lat`, `start_lon`, `start_alt`) over `mission_step_duration` seconds.

## WebSocket

- `ws://<host>:<quad_port>/ws/drone-status` - pushes a telemetry JSON message
  every second:

```json
{
  "timestamp": 1737963600000,
  "is_armed": false,
  "flight_mode": "HOLD",
  "lat": 47.641467,
  "lon": -122.140164,
  "alt": 0.0,
  "yaw": 0.0,
  "horizontal_velocity": 1.0,
  "vertical_velocity": 1.0,
  "battery_voltage": 50.0,
  "in_air": true,
  "is_mission_finished": true,
  "mission_progress": "0/0",
  "last_mission_waypoint": null
}
```

