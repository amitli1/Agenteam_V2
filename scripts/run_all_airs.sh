#!/usr/bin/env bash
#
# run_all_airs.sh
#
# Opens a single terminal window with 2 named tabs, each starting one of the
# air docker services:
#
#   1. air 1 -> dockers/air/intel/air_1
#   2. air 2 -> dockers/air/intel/air_2
#
# Usage:
#   ./scripts/run_all_airs.sh
#
# Requires `gnome-terminal`.

set -euo pipefail

# Resolve the Agenteam_V2 repo root (this script lives in <repo>/scripts).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

AIR_1_DIR="${REPO_ROOT}/dockers/air/intel/air_1"
AIR_2_DIR="${REPO_ROOT}/dockers/air/intel/air_2"

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
CMD_AIR_1="bash -c 'cd \"${AIR_1_DIR}\" && sudo docker compose -f docker-compose.air-intel.yml up --build; exec bash'"
CMD_AIR_2="bash -c 'cd \"${AIR_2_DIR}\" && sudo docker compose -f docker-compose.air-intel_2.yml up --build; exec bash'"

gnome-terminal \
    --tab --title="air 1" -e "${CMD_AIR_1}" \
    --tab --title="air 2" -e "${CMD_AIR_2}"

