#!/usr/bin/env bash
#
# run_monitor.sh
#
# Opens a terminal window titled "monitor" running the monitor docker
# service located at dockers/monitor/intel.
#
# Usage:
#   ./scripts/run_monitor.sh
#
# Requires `gnome-terminal`.

set -euo pipefail

# Resolve the Agenteam_V2 repo root (this script lives in <repo>/scripts).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

MONITOR_DIR="${REPO_ROOT}/dockers/monitor/intel"

if ! command -v gnome-terminal >/dev/null 2>&1; then
    echo "Error: gnome-terminal is required to run this script." >&2
    exit 1
fi

CMD_MONITOR="bash -c 'cd \"${MONITOR_DIR}\" && sudo docker compose up --build; exec bash'"

gnome-terminal \
    --tab --title="monitor" -e "${CMD_MONITOR}"

