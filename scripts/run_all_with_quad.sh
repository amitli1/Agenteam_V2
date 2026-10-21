#!/usr/bin/env bash
#
# run_all_with_quad.sh
#
# Opens a single terminal window with named tabs, each starting one of the
# project docker services:
#
#   1. whisper -> dockers/whisper/intel
#   2. tts     -> dockers/tts/intel
#   3. monitor -> dockers/monitor/intel
#   4. air 1   -> dockers/air/intel/air_1
#   5. air 2   -> dockers/air/intel/air_2
#   6. vision  -> VisionSimulator
#
# Usage:
#   ./scripts/run_all_with_quad.sh
#
# Requires `gnome-terminal`.

set -euo pipefail

# Resolve the Agenteam_V2 repo root (this script lives in <repo>/scripts).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

WHISPER_DIR="${REPO_ROOT}/dockers/whisper/intel"
TTS_DIR="${REPO_ROOT}/dockers/tts/intel"
MONITOR_DIR="${REPO_ROOT}/dockers/monitor/intel"
AIR_1_DIR="${REPO_ROOT}/dockers/air/intel/air_1"
AIR_2_DIR="${REPO_ROOT}/dockers/air/intel/air_2"
VISION_SIM_DIR="${REPO_ROOT}/VisionSimulator"

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
CMD_WHISPER="bash -c 'cd \"${WHISPER_DIR}\" && sudo docker compose -f docker-compose.whisper-intel.yml up --build; exec bash'"
CMD_TTS="bash -c 'cd \"${TTS_DIR}\" && sudo docker compose -f docker-compose.tts-intel.yml up --build; exec bash'"
CMD_MONITOR="bash -c 'cd \"${MONITOR_DIR}\" && sudo docker compose up --build; exec bash'"
CMD_AIR_1="bash -c 'cd \"${AIR_1_DIR}\" && sudo docker compose -f docker-compose.air-intel.yml up --build; exec bash'"
CMD_AIR_2="bash -c 'cd \"${AIR_2_DIR}\" && sudo docker compose -f docker-compose.air-intel_2.yml up --build; exec bash'"
CMD_VISION="bash -c 'cd \"${VISION_SIM_DIR}\" && sudo docker compose up --build; exec bash'"

gnome-terminal \
    --tab --title="whisper" -e "${CMD_WHISPER}" \
    --tab --title="tts" -e "${CMD_TTS}" \
    --tab --title="monitor" -e "${CMD_MONITOR}" \
    --tab --title="air 1" -e "${CMD_AIR_1}" \
    --tab --title="air 2" -e "${CMD_AIR_2}" \
    --tab --title="vision" -e "${CMD_VISION}"


