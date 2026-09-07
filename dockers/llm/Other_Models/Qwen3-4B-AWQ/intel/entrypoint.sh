#!/bin/sh
# Wrapper so gpu_memory_utilization (and other knobs) can be overridden at
# `docker run` / docker-compose time via environment variables, since Docker's
# exec-form ENTRYPOINT/CMD does not expand env vars on its own.
set -e

exec vllm serve /models/Qwen3-4B-AWQ \
  --host "${VLLM_HOST:-0.0.0.0}" \
  --port "${VLLM_PORT:-8000}" \
  --trust-remote-code \
  --quantization "${QUANTIZATION:-awq}" \
  --gpu-memory-utilization "${GPU_MEMORY_UTILIZATION:-0.8}" \
  --max-model-len "${MAX_MODEL_LEN:-4096}" \
  --served-model-name "${SERVED_MODEL_NAME:-Qwen3-4B-AWQ}"

