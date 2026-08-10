#!/usr/bin/env bash
#
# Diagnose + (re)start the drone-simulation container so that
# ws://localhost:<quad_port>/ws/drone-status is actually reachable.
#
# Why this script exists:
#   `docker compose up -d` on a container that already exists only *starts*
#   it - it does NOT re-apply changes from docker-compose.yml (e.g. the
#   `ports: - "8001:8001"` mapping). If the container was created before a
#   compose-file change (or via a plain `docker run`), it can be "Up" and
#   healthy INSIDE the container while having NO port published to the
#   host at all. From quad_manager.py's point of view this looks exactly
#   like "can't connect to the websocket", even though nothing is wrong
#   with quad_manager.py.
#
# This script always recreates the container so the current
# docker-compose.yml (ports, volumes, etc.) is guaranteed to be in effect,
# then verifies the REST health endpoint and the WebSocket both respond.
#
# Usage:
#   ./check_and_start.sh

set -euo pipefail
cd "$(dirname "$0")"

CONTAINER_NAME="agenteam-drone-simulation"
PORT="$(python3 - <<'PY'
import yaml
print(yaml.safe_load(open("simulation.yaml"))["general"]["quad_port"])
PY
)"

DC="docker compose"
if ! docker info >/dev/null 2>&1; then
  # Current user has no access to the docker daemon socket (common cause
  # of "permission denied ... docker.sock"); fall back to sudo.
  DC="sudo docker compose"
fi

echo "== Current container state =="
$DC ps || true

echo
echo "== Recreating container (guarantees docker-compose.yml settings, incl. port mapping, are applied) =="
$DC down --remove-orphans || true
$DC up -d --build

echo
echo "== Waiting for container to come up =="
sleep 2
$DC ps

echo
echo "== Published ports for ${CONTAINER_NAME} =="
if [ "$DC" = "sudo docker compose" ]; then
  PORTS=$(sudo docker port "${CONTAINER_NAME}" 2>&1 || true)
else
  PORTS=$(docker port "${CONTAINER_NAME}" 2>&1 || true)
fi
if [ -z "$PORTS" ]; then
  echo "!! No published ports found. Check docker-compose.yml 'ports:' section and re-run this script."
  exit 1
fi
echo "$PORTS"

echo
echo "== REST health check (http://localhost:${PORT}/health) =="
if curl -sf "http://localhost:${PORT}/health"; then
  echo
else
  echo "!! REST health check failed. Inspect logs with: $DC logs -f drone-simulation"
  exit 1
fi

echo
echo "== WebSocket check (ws://localhost:${PORT}/ws/drone-status) =="
python3 - "$PORT" <<'PY'
import asyncio
import sys

try:
    import websockets
except ImportError:
    print("!! The 'websockets' python package is required for this check: pip install websockets")
    sys.exit(1)

port = sys.argv[1]

async def main():
    uri = f"ws://localhost:{port}/ws/drone-status"
    async with websockets.connect(uri, open_timeout=5) as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=5)
        print(f"OK - received telemetry: {msg}")

asyncio.run(main())
PY

echo
echo "All good - quad_manager.py should now be able to reach the WebSocket."

