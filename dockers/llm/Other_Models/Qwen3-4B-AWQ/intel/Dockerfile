# Dockerfile for serving Qwen/Qwen3-4B-AWQ via vLLM's OpenAI-compatible API
# server (vllm serve).
#
# Intel / x86_64 variant - built on top of the official vLLM image, which
# requires an NVIDIA GPU + the NVIDIA Container Toolkit on the host (see
# docker-compose.yml: "runtime: nvidia").
FROM vllm/vllm-openai:latest

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models/.cache/huggingface

WORKDIR /app

# Bake the model weights into the image at build time (network access is
# available during `docker build`), so the container can serve the model
# fully offline afterwards - no Hugging Face Hub access needed at runtime.
ARG MODEL_ID=Qwen/Qwen3-4B-AWQ
ENV MODEL_DIR=/models/Qwen3-4B-AWQ
RUN python3 -c "\
from huggingface_hub import snapshot_download; \
snapshot_download(repo_id='${MODEL_ID}', local_dir='${MODEL_DIR}')"

# Force fully offline mode at runtime: never attempt network calls to the
# HuggingFace Hub, always use the weights baked in above.
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

EXPOSE 8000

# Wrapper script so knobs like --gpu-memory-utilization can be overridden at
# runtime via environment variables (see docker-compose.yml
# "GPU_MEMORY_UTILIZATION"), since exec-form CMD/ENTRYPOINT args are not
# shell-expanded.
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

