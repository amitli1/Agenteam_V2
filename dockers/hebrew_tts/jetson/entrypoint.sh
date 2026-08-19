#!/bin/bash

set -e

MODEL_PATH="${HEBREW_TTS_MODEL_PATH:-/models/hebrew_tts/he_IL-saspeech-medium.onnx}"
MODEL_CONFIG="${MODEL_PATH}.json"

echo "=============================================="
echo " Hebrew TTS (Piper) Service"
echo "=============================================="
echo "Model file   : ${MODEL_PATH}"
echo "Model config : ${MODEL_CONFIG}"
echo "=============================================="

# ---------------------------------------------------------
# The model file lives on the host disk and is mapped into
# the container. It is NOT downloaded automatically.
# ---------------------------------------------------------

if [ ! -f "${MODEL_PATH}" ]; then
    echo ""
    echo "ERROR: Hebrew TTS model not found at:"
    echo "  ${MODEL_PATH}"
    echo ""
    echo "Make sure the model file (.onnx) exists on the host"
    echo "and is mapped into the container via docker-compose.yml."
    echo ""
    exit 1
fi

if [ ! -f "${MODEL_CONFIG}" ]; then
    echo ""
    echo "ERROR: Hebrew TTS model config not found at:"
    echo "  ${MODEL_CONFIG}"
    echo ""
    echo "Piper models require a matching '<model>.onnx.json' file"
    echo "next to the '.onnx' weights file."
    echo ""
    exit 1
fi

echo "Hebrew TTS model verified."
echo ""

# ---------------------------------------------------------
# Start application
# ---------------------------------------------------------

exec python3 audio/hebrew_tts_service.py

