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
docker run --rm \
  --runtime nvidia \
  -p 8090:8000 \
  -v /mnt/nvme/models:/root/.cache/huggingface \
  --ipc=host \
  ghcr.io/nvidia-ai-iot/vllm:latest-jetson-orin \
  vllm serve openai/gpt-oss-20b \
  --host 0.0.0.0 \
  --port 8000 \
  --gpu-memory-utilization 0.5
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
