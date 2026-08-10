#!/usr/bin/env bash
#
# run_vision_quad_sim.sh
#
# Opens a single terminal window with 2 named tabs, each starting one of the
# simulation docker services:
#
#   1. vision sim -> VisionSimulator/
#   2. quad 1 sim -> DroneSimulation/
#
# Usage:
#   ./scripts/run_vision_quad_sim.sh
#
# Requires `gnome-terminal`.

set -euo pipefail

# Resolve the Agenteam_V2 repo root (this script lives in <repo>/scripts).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

VISION_SIM_DIR="${REPO_ROOT}/VisionSimulator"
QUAD_SIM_DIR="${REPO_ROOT}/DroneSimulation"

if ! command -v gnome-terminal >/dev/null 2>&1; then
    echo "Error: gnome-terminal is required to run this script." >&2
    exit 1
fi

# NOTE: gnome-terminal treats "--" as "execute the rest of the entire command
# line", not "execute until the next --tab" - so chaining multiple
# `--tab ... -- cmd` groups on one command line only ever runs the FIRST
# command (later --tab/-- groups get swallowed as extra arguments to it).
# To run a different command per tab we must use the (deprecated but still
# supported) per-terminal `-e` option instead, once for each tab.
CMD_VISION_SIM="bash -c 'cd \"${VISION_SIM_DIR}\" && sudo docker compose up --build; exec bash'"
CMD_QUAD_SIM="bash -c 'cd \"${QUAD_SIM_DIR}\" && sudo docker compose up --build; exec bash'"

gnome-terminal \
    --tab --title="vision sim" -e "${CMD_VISION_SIM}" \
    --tab --title="quad 1 sim" -e "${CMD_QUAD_SIM}"

