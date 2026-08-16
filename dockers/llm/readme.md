# first time (intel)
```
docker run --gpus all \
  -p 8090:8000 \
  -v /mnt/nvme/models:/root/.cache/huggingface \
  --ipc=host \
  vllm/vllm-openai:latest \
  --model openai/gpt-oss-20b \
  --gpu-memory-utilization 0.5
```

# first time (jetson)
```
mkdir -p /mnt/nvme/models/tiktoken_encodings

wget -O /mnt/nvme/models/tiktoken_encodings/o200k_base.tiktoken \
  https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken

wget -O /mnt/nvme/models/tiktoken_encodings/cl100k_base.tiktoken \
  https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken
```

```
docker run --rm \
  --runtime nvidia \
  -p 8090:8000 \
  -v /mnt/nvme/models:/root/.cache/huggingface \
  -v /mnt/nvme/models/tiktoken_encodings:/root/.cache/tiktoken_encodings:ro \
  -e TIKTOKEN_ENCODINGS_BASE=/root/.cache/tiktoken_encodings \
  --ipc=host \
  ghcr.io/nvidia-ai-iot/vllm:latest-jetson-orin \
  vllm serve openai/gpt-oss-20b \
  --host 0.0.0.0 \
  --port 8000 \
  --gpu-memory-utilization 0.5

```

# Params:
```
-p HOST_PORT:CONTAINER_PORT
-v HOST_PATH:CONTAINER_PATH
--ipc=host (PyTorch/vLLM can use shared memory between processes)
```

# second time
```
docker run -d \
  --restart unless-stopped \
  --name vllm_gpt_oss \
  --gpus all \
  -p 8090:8000 \
  -e HF_HUB_OFFLINE=1 \
  -e TRANSFORMERS_OFFLINE=1 \
  -v /mnt/nvme/models:/root/.cache/huggingface \
  --ipc=host \
  vllm/vllm-openai:latest \
  --model openai/gpt-oss-20b \
  --gpu-memory-utilization 0.5
```
