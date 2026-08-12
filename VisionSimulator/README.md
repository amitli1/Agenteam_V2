# VisionSimulator

A lightweight Python/Flask simulator for the three real vision microservices
that `project_code/vision/vision_manager.py` (`VisionManager`) talks to over
REST:

| Service  | Purpose                                   | Default port (see `conf.yaml`) |
|----------|--------------------------------------------|---------------------------------|
| point    | pointing-agent / lock-on tracking service  | `8003`                           |
| hold     | alert / hold-fire service                  | `6000`                           |
| summary  | scene summarization / description service  | `8080`                           |

All three services run as independent Flask apps inside the **same**
container/process, each bound to its own port, so it can be dropped in as a
drop-in replacement for the real backends during development/testing
(set `vision.use_online: true` and point `general`/`vision` ports at this
simulator's host).

## Endpoints

### Point service (port `8003`)
| Method | Path                              | Body                              | Notes |
|--------|-----------------------------------|------------------------------------|-------|
| POST   | `/api/pointing-agent/start`       | pointing config json (see `project_code/app_config/pointing_settings.json`) | marks session active |
| POST   | `/api/pointing-agent/stop`        | `{}`                                | marks session inactive |
| GET    | `/api/pointing-agent/status`      | -                                   | returns `{"session": {"is_active": bool}, "agent": {"status": "idle|searching|locked", "prompt": str}}`. Status transitions from `searching` to `locked` a couple of seconds after a lock request. |
| POST   | `/api/agent/set-lock-request`     | `{"prompt": "<text>"}`             | starts a simulated lock/search sequence |

### Hold service (port `6000`)
| Method | Path            | Body                                             | Notes |
|--------|-----------------|---------------------------------------------------|-------|
| POST   | `/alert-start`  | `{"task": "hold", "description": "<text>"}`      | starts generating fake periodic alerts |
| POST   | `/alert-stop`   | `{"task": "stop_hold"}`                          | stops generating alerts |
| GET    | `/alert-get`    | -                                                 | returns `{}` when idle, or a fake detection message (e.g. `{"msg": "Detected vehicle matching: ..."}`) periodically while active |

### Summary service (port `8080`)
| Method | Path         | Body                                                              | Notes |
|--------|--------------|--------------------------------------------------------------------|-------|
| POST   | `/get_ready` | `{"task": "get_ready"}`                                            | returns `{"status": "ready"}` |
| POST   | `/start_sum` | `{"task": "start_summarizing", "objects_to_focus": [...]}`        | returns `{"status": "started", ...}` |
| POST   | `/stop_sum`  | `{"task": "stop_summarizing"}`                                     | returns `{"status": "stopped"}` |
| GET    | `/status`    | -                                                                   | returns current ready/summarizing state |
| POST   | `/describe`  | `{"task": "describe", "transcription": "<text>"}`                 | returns a fake description string based on the last `objects_to_focus` and the transcription |

Each service also exposes `GET /health` for basic liveness checks.

## Running locally (no docker)

```bash
cd VisionSimulator
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.main
```

Ports can be overridden with the `POINT_PORT`, `HOLD_PORT`, `SUMMARY_PORT`
and `HOST` environment variables.

## Running with Docker

```bash
cd VisionSimulator
docker compose up --build
```

This exposes `8003`, `6000` and `8080` on the host, matching the defaults in
`project_code/app_config/conf.yaml`.

## Quick smoke test

```bash
# point service
curl -X POST http://localhost:8003/api/pointing-agent/start -H 'Content-Type: application/json' -d '{"prompt": ""}'
curl -X POST http://localhost:8003/api/agent/set-lock-request -H 'Content-Type: application/json' -d '{"prompt": "focus on person"}'
curl http://localhost:8003/api/pointing-agent/status

# hold service
curl -X POST http://localhost:6000/alert-start -H 'Content-Type: application/json' -d '{"task": "hold", "description": "hold vehicles or persons or weapons"}'
curl http://localhost:6000/alert-get

# summary service
curl -X POST http://localhost:8080/get_ready -H 'Content-Type: application/json' -d '{"task": "get_ready"}'
curl -X POST http://localhost:8080/start_sum -H 'Content-Type: application/json' -d '{"task": "start_summarizing", "objects_to_focus": ["car"]}'
curl -X POST http://localhost:8080/describe -H 'Content-Type: application/json' -d '{"task": "describe", "transcription": "what do you see?"}'
```

