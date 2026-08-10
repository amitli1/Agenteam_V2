#!/usr/bin/env bash
#
# run_whisper_tts.sh
#
# Opens a single terminal window with 2 named tabs, each starting one of the
# whisper/tts docker services:
#
#   1. whisper -> dockers/whisper/intel
#   2. TTS     -> dockers/tts/intel
#
# Usage:
#   ./scripts/run_whisper_tts.sh
#
# Requires `gnome-terminal`.

set -euo pipefail

# Resolve the Agenteam_V2 repo root (this script lives in <repo>/scripts).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

WHISPER_DIR="${REPO_ROOT}/dockers/whisper/intel"
TTS_DIR="${REPO_ROOT}/dockers/tts/intel"

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

gnome-terminal \
    --tab --title="whisper" -e "${CMD_WHISPER}" \
    --tab --title="TTS" -e "${CMD_TTS}"

