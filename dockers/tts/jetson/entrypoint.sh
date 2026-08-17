#!/bin/bash

set -e

MODEL_DIR="${TTS_MODEL_DIR:-/models/kokoro-82m}"
MODEL_REPO="${TTS_MODEL_REPO:-hexgrad/Kokoro-82M}"
MODEL_FILE="kokoro-v1_0.pth"

echo "=============================================="
echo " TTS (Kokoro) Service"
echo "=============================================="
echo "Model repository : ${MODEL_REPO}"
echo "Model directory   : ${MODEL_DIR}"
echo "HF_HOME           : ${HF_HOME}"
echo "HF_HUB_CACHE      : ${HF_HUB_CACHE}"
echo "HF_HUB_OFFLINE    : ${HF_HUB_OFFLINE:-0}"
echo "TTS_DEVICE        : ${TTS_DEVICE:-auto}"
echo "=============================================="

# ---------------------------------------------------------
# Check whether the actual Kokoro model exists.
#
# The .pth weights file is the important indicator that the
# model has been downloaded completely.
# ---------------------------------------------------------

if [ ! -f "${MODEL_DIR}/${MODEL_FILE}" ]; then

    echo ""
    echo "Kokoro model not found."
    echo "Downloading:"
    echo "  ${MODEL_REPO}"
    echo ""
    echo "Destination:"
    echo "  ${MODEL_DIR}"
    echo ""

    # If offline mode was explicitly requested, fail clearly
    # instead of attempting any network connection.
    if [ "${HF_HUB_OFFLINE:-0}" = "1" ]; then
        echo "ERROR: HF_HUB_OFFLINE=1 but the Kokoro model"
        echo "does not exist at:"
        echo "  ${MODEL_DIR}"
        echo ""
        echo "Run once with internet access and HF_HUB_OFFLINE=0."
        exit 1
    fi

    mkdir -p "${MODEL_DIR}"

    python3 - <<PY
from huggingface_hub import snapshot_download

repo_id = "${MODEL_REPO}"
local_dir = "${MODEL_DIR}"

print("Downloading Hugging Face model...")
print(f"Repository: {repo_id}")
print(f"Local dir : {local_dir}")

snapshot_download(
    repo_id=repo_id,
    local_dir=local_dir,
)

print("Model download completed.")
PY

else

    echo ""
    echo "Kokoro model already exists."
    echo "Using local model:"
    echo "  ${MODEL_DIR}"
    echo ""

fi

# ---------------------------------------------------------
# Verify required files
# ---------------------------------------------------------

if [ ! -f "${MODEL_DIR}/${MODEL_FILE}" ]; then
    echo "ERROR: ${MODEL_FILE} is missing."
    echo "The Kokoro model download appears incomplete."
    exit 1
fi

if [ ! -f "${MODEL_DIR}/config.json" ]; then
    echo "ERROR: config.json is missing."
    echo "The Kokoro model download appears incomplete."
    exit 1
fi

echo "=============================================="
echo " Kokoro model verified"
echo "=============================================="
echo "Model: ${MODEL_DIR}"
echo ""

# ---------------------------------------------------------
# Start application
# ---------------------------------------------------------

exec python3 audio/tts_service.py

