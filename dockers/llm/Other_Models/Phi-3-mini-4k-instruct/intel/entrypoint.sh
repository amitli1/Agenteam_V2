#!/bin/sh
# Wrapper so gpu_memory_utilization (and other knobs) can be overridden at
# `docker run` / docker-compose time via environment variables, since Docker's
# exec-form ENTRYPOINT/CMD does not expand env vars on its own.
set -e

exec vllm serve /models/Phi-3-mini-4k-instruct \
  --host "${VLLM_HOST:-0.0.0.0}" \
  --port "${VLLM_PORT:-8000}" \
  --trust-remote-code \
  --gpu-memory-utilization "${GPU_MEMORY_UTILIZATION:-0.5}" \
  --max-model-len "${MAX_MODEL_LEN:-4096}" \
  --served-model-name "${SERVED_MODEL_NAME:-Phi-3-mini-4k-instruct}"

