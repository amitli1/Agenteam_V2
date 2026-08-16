# first time (jetson)

# Step I:
```
mkdir -p /mnt/nvme/models/tiktoken_encodings

wget -O /mnt/nvme/models/tiktoken_encodings/o200k_base.tiktoken \
  https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken

wget -O /mnt/nvme/models/tiktoken_encodings/cl100k_base.tiktoken \
  https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken
```

# Step II:
```
mkdir -p /mnt/nvme/models/gpt-oss-20b
```

# Step III (Download model to /mnt/nvme/models/gpt-oss-20b-local/):

```
docker run --rm \
  --network host \
  -v /mnt/nvme/models:/models \
  python:3.10-slim \
  bash -c '
    pip install --no-cache-dir -U huggingface_hub &&
    python -c "
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id=\"openai/gpt-oss-20b\",
    local_dir=\"/models/gpt-oss-20b-local\"
)
"
  '
```

# Step IV :


this:
```
docker run --rm \
  --runtime nvidia \
  -p 8090:8000 \
  --network host \
  -v /mnt/nvme/models/gpt-oss-20b-local:/models:ro \
  -v /mnt/nvme/models/tiktoken_encodings:/root/.cache/tiktoken_encodings:ro \
  -e TIKTOKEN_ENCODINGS_BASE=/root/.cache/tiktoken_encodings \
  --ipc=host \
  ghcr.io/nvidia-ai-iot/vllm:latest-jetson-orin \
  vllm serve /models \
  --host 0.0.0.0 \
  --port 8000 \
  --gpu-memory-utilization 0.5
```

not this:
```
docker run --rm \
  --runtime nvidia \
  -p 8090:8000 \
  -v /mnt/nvme/models/gpt-oss-20b:/models \
  -v /mnt/nvme/models/tiktoken_encodings:/root/.cache/tiktoken_encodings:ro \
  -e TIKTOKEN_ENCODINGS_BASE=/root/.cache/tiktoken_encodings \
  --ipc=host \
  ghcr.io/nvidia-ai-iot/vllm:latest-jetson-orin \
  vllm serve openai/gpt-oss-20b \
  --download-dir /models \
  --host 0.0.0.0 \
  --port 8000 \
  --gpu-memory-utilization 0.5

```


# Step V (no internet) :
this:
```
docker run -d \
  --restart unless-stopped \
  --name vllm_gpt_oss \
  --runtime nvidia \
  -p 8090:8000 \
  --network none \
  -v /mnt/nvme/models/gpt-oss-20b-local:/models:ro \
  -v /mnt/nvme/models/tiktoken_encodings:/root/.cache/tiktoken_encodings:ro \
  -e HF_HUB_OFFLINE=1 \
  -e TRANSFORMERS_OFFLINE=1 \
  -e TIKTOKEN_ENCODINGS_BASE=/root/.cache/tiktoken_encodings \
  --ipc=host \
  ghcr.io/nvidia-ai-iot/vllm:latest-jetson-orin \
  vllm serve /models \
  --host 0.0.0.0 \
  --port 8000 \
  --gpu-memory-utilization 0.5
```

not this:
```
docker run -d \
  --restart unless-stopped \
  --name vllm_gpt_oss \
  --runtime nvidia \
  -p 8090:8000 \
  --network none \
  -v /mnt/nvme/models/gpt-oss-20b:/models:ro \
  -v /mnt/nvme/models/tiktoken_encodings:/root/.cache/tiktoken_encodings:ro \
  -e TIKTOKEN_ENCODINGS_BASE=/root/.cache/tiktoken_encodings \
  --ipc=host \
  ghcr.io/nvidia-ai-iot/vllm:latest-jetson-orin \
  vllm serve /models \
  --host 0.0.0.0 \
  --port 8000 \
  --gpu-memory-utilization 0.5

```




# Step VI (Test):
```
curl http://127.0.0.1:8090/v1/models
```

or

```
curl http://127.0.0.1:8090/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-oss-20b",
    "messages": [
      {
        "role": "user",
        "content": "What is the capital of France?"
      }
    ],
    "max_tokens": 100
  }'

```



# Params:
```
-p HOST_PORT:CONTAINER_PORT
-v HOST_PATH:CONTAINER_PATH
--ipc=host (PyTorch/vLLM can use shared memory between processes)
```