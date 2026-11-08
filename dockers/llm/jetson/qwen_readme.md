```
hf download \
    Qwen/Qwen3-4B-AWQ \
    --local-dir /mnt/nvme/models/Qwen3-4B-AWQ
```

```
sudo docker run --rm \
    --name qwen3-vllm \
    --runtime=nvidia \
    -e NVIDIA_VISIBLE_DEVICES=all \
    -e HF_HUB_OFFLINE=1 \
    -e TRANSFORMERS_OFFLINE=1 \
    -e VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS=0 \
    -v /mnt/nvme/models:/models:ro \
    -p 8090:8000 \
    --ipc=host \
    ghcr.io/nvidia-ai-iot/vllm:r36.4.tegra-aarch64-cu126-22.04 \
    vllm serve /models/Qwen3-4B-AWQ \
    --host 0.0.0.0 \
    --port 8000 \
    --gpu-memory-utilization 0.50 \
    --max-model-len 4096 \
    --max-num-seqs 1 \
    --max-num-batched-tokens 1024

```