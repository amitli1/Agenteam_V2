# Download (openai/gpt-oss-20b):
```

pip install -U "huggingface_hub[cli]"
pip install vllm
hf auth login

hf download \
    openai/gpt-oss-20b \
    --local-dir /mnt/nvme/repo/Agenteam_V2/dockers/llm/openai-gpt-oss-20b


docker run --rm -it \
  --network host \
  --shm-size=16g \
  --ulimit memlock=-1 \
  --ulimit stack=67108864 \
  --runtime=nvidia \
  --name=vllm-orin \
  -e HF_HUB_OFFLINE=1 \
  -e TRANSFORMERS_OFFLINE=1 \
  -v /mnt/nvme/repo/Agenteam_V2/dockers/llm/openai-gpt-oss-20b:/model \
  -v $HOME/data/vllm_cache:/root/.cache/vllm \
  ghcr.io/nvidia-ai-iot/vllm:latest-jetson-orin \
  vllm serve /model \
    --host 0.0.0.0 \
    --port 8000 \
    --gpu-memory-utilization 0.85 \
    --max-model-len 8192


```

# Run:
```
???
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1


vllm serve \
    /mnt/nvme/repo/Agenteam_V2/dockers/llm/openai-gpt-oss-20b \
    --host 0.0.0.0 \
    --port 8090 \
    --gpu-memory-utilization 0.2



```

# Test:

```
curl http://localhost:8090/v1/models
```