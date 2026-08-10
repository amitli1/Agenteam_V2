#!/usr/bin/env bash
#
# run_all_scripts.sh
#
# Opens a single terminal window with named tabs, each starting one of the
# project docker services:
#
#   1. whisper    -> dockers/whisper/intel
#   2. tts        -> dockers/tts/intel
#   3. monitor    -> dockers/monitor/intel
#   4. air 1      -> dockers/air/intel/air_1
#   5. air 2      -> dockers/air/intel/air_2
#   6. vision     -> VisionSimulator
#   7. quad_sim_1 -> DroneSimulation
#
# Usage:
#   ./scripts/run_all_scripts.sh
#
# To skip a tab, simply flip its flag below to false.
#
# Requires `gnome-terminal`.

set -euo pipefail

# ---------------------------------------------------------------------------
# Toggle which tabs to run. Set to false to skip a service.
# ---------------------------------------------------------------------------
RUN_WHISPER=true
RUN_TTS=true
RUN_MONITOR=true
RUN_AIR_1=true
RUN_AIR_2=true
RUN_VISION=true
RUN_QUAD_SIM_1=true

# Resolve the Agenteam_V2 repo root (this script lives in <repo>/scripts).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

WHISPER_DIR="${REPO_ROOT}/dockers/whisper/intel"
TTS_DIR="${REPO_ROOT}/dockers/tts/intel"
MONITOR_DIR="${REPO_ROOT}/dockers/monitor/intel"
AIR_1_DIR="${REPO_ROOT}/dockers/air/intel/air_1"
AIR_2_DIR="${REPO_ROOT}/dockers/air/intel/air_2"
VISION_SIM_DIR="${REPO_ROOT}/VisionSimulator"
QUAD_SIM_DIR="${REPO_ROOT}/DroneSimulation"

if ! command -v gnome-terminal >/dev/null 2>&1; then
    echo "Error: gnome-terminal is required to run this script." >&2
    exit 1
fi

CMD_WHISPER="bash -c 'cd \"${WHISPER_DIR}\" && sudo docker compose -f docker-compose.whisper-intel.yml up --build; exec bash'"
CMD_TTS="bash -c 'cd \"${TTS_DIR}\" && sudo docker compose -f docker-compose.tts-intel.yml up --build; exec bash'"
CMD_MONITOR="bash -c 'cd \"${MONITOR_DIR}\" && sudo docker compose up --build; exec bash'"
CMD_AIR_1="bash -c 'cd \"${AIR_1_DIR}\" && sudo docker compose -f docker-compose.air-intel.yml up --build; exec bash'"
CMD_AIR_2="bash -c 'cd \"${AIR_2_DIR}\" && sudo docker compose -f docker-compose.air-intel_2.yml up --build; exec bash'"
CMD_VISION="bash -c 'cd \"${VISION_SIM_DIR}\" && sudo docker compose up --build; exec bash'"
CMD_QUAD_SIM_1="bash -c 'cd \"${QUAD_SIM_DIR}\" && sudo docker compose up --build; exec bash'"

# ---------------------------------------------------------------------------
# Build the gnome-terminal argument list, honoring the RUN_* toggles above.
#
# NOTE: gnome-terminal treats "--" as "execute the rest of the entire command
# line", not "execute until the next --tab" - so chaining multiple
# `--tab ... -- cmd` groups on one command line only ever runs the FIRST
# command (later --tab/-- groups get swallowed as extra arguments to it).
# To run a different command per tab we must use the (deprecated but still
# supported) per-terminal `-e` option instead, once for each tab.
# ---------------------------------------------------------------------------
TERM_ARGS=()

add_tab() {
    local title="$1"
    local cmd="$2"
    TERM_ARGS+=(--tab --title="${title}" -e "${cmd}")
}

if [ "${RUN_WHISPER}" = true ];    then add_tab "whisper"    "${CMD_WHISPER}";    fi
if [ "${RUN_TTS}" = true ];        then add_tab "tts"        "${CMD_TTS}";        fi
if [ "${RUN_MONITOR}" = true ];    then add_tab "monitor"    "${CMD_MONITOR}";    fi
if [ "${RUN_AIR_1}" = true ];      then add_tab "air 1"      "${CMD_AIR_1}";      fi
if [ "${RUN_AIR_2}" = true ];      then add_tab "air 2"      "${CMD_AIR_2}";      fi
if [ "${RUN_VISION}" = true ];     then add_tab "vision"     "${CMD_VISION}";     fi
if [ "${RUN_QUAD_SIM_1}" = true ]; then add_tab "quad_sim_1" "${CMD_QUAD_SIM_1}"; fi

if [ "${#TERM_ARGS[@]}" -eq 0 ]; then
    echo "No tabs enabled - nothing to run. Enable at least one RUN_* flag." >&2
    exit 1
fi

gnome-terminal "${TERM_ARGS[@]}"


