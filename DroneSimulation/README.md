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
cd DroneSimulation && docker compose down && docker compose up -d
```

## Troubleshooting: "quad_manager.py can't connect to the WebSocket"

Almost always this is **not** a code problem in `quad_manager.py`, it's a
stale/misconfigured Docker container. Root causes seen in practice, in
order of likelihood:

1. **The container isn't running at all.**
   `restart: unless-stopped` in `docker-compose.yml` means Docker will
   restart it after a crash or a host reboot, but a manual
   `docker stop` / Ctrl+C leaves it stopped until you start it again.
   Check with:
   ```bash
   docker compose ps
   ```
   If it shows `Exited`, start it: `docker compose up -d`.

2. **The container is "Up", but the port was never actually published.**
   `docker compose up -d` on a container that already exists only
   *starts* it - it does **not** re-apply changes from
   `docker-compose.yml` (like the `ports: - "8001:8001"` mapping). If the
   container was originally created before a compose-file/port change (or
   created via a plain `docker run`), it can look perfectly healthy
   (`Up`, logs show `Uvicorn running on http://0.0.0.0:8001`) while having
   **no port bound on the host at all** - `ws://localhost:8001/...` then
   fails to even open a TCP connection. This is the failure mode that hit
   us on 2026-08-10.

   Verify with:
   ```bash
   docker compose ps            # PORTS column should show 0.0.0.0:8001->8001/tcp
   docker port agenteam-drone-simulation
   ```
   If `PORTS` is empty, **recreate** the container (a restart is not
   enough, it must be recreated):
   ```bash
   docker compose down
   docker compose up -d
   ```

3. **Wrong host/port on the client side.** If `quad_manager.py` runs
   *outside* Docker, it must use `ws://localhost:<quad_port>`. If it runs
   *inside another container*, `localhost` refers to that other
   container, not this one - use the service name (`drone-simulation`) or
   put both containers on the same Docker network and use the container
   name/hostname instead.

4. **`quad_port` mismatch** between `simulation.yaml` and the
   `ports:` mapping in `docker-compose.yml` (they must match, e.g. both
   `8001`).

### One-shot check/fix script

Use `check_and_start.sh` to recreate the container (guaranteeing the
current `docker-compose.yml` settings are applied) and verify both the
REST `/health` endpoint and the `/ws/drone-status` WebSocket actually
respond, before you go debug `quad_manager.py`:

```bash
cd DroneSimulation
./check_and_start.sh
```

If this script reports `OK - received telemetry: ...`, the Docker side is
confirmed working and any remaining connection issue is on the client
(`quad_manager.py`) side - e.g. wrong host/port, or client running inside
another container's isolated network.

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

