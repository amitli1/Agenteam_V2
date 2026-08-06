# Download (openai/gpt-oss-20b):
```

pip install -U "huggingface_hub[cli]"
pip install vllm
hf auth login

hf download \
    openai/gpt-oss-20b \
    --local-dir /mnt/nvme/repo/Agenteam_V2/dockers/llm/openai-gpt-oss-20b

cd /mnt/nvme/repo/Agenteam_V2/dockers/llm/harmony

ls
got:






# Create a copy/symlink named with the exact SHA-256 hash tiktoken expects
cp o200k_base.tiktoken b426e515a3b19d6c297921820689e47228a2a09559c6086f685352c842790e78

docker run --rm -it \
  --network host \
  --ipc=host \
  --shm-size=16g \
  --ulimit memlock=-1 \
  --ulimit stack=67108864 \
  --runtime=nvidia \
  --name=vllm-orin \
  -e HF_HUB_OFFLINE=1 \
  -e TRANSFORMERS_OFFLINE=1 \
  -e PYTORCH_NVML_BASED_CUDA_CHECK=0 \
  -e VLLM_WORKER_MULTIPROC_METHOD=spawn \
  -e VLLM_USE_V1=0 \
  -v /mnt/nvme/repo/Agenteam_V2/dockers/llm/openai-gpt-oss-20b:/model \
  -v $HOME/data/vllm_cache:/root/.cache/vllm \
  ghcr.io/nvidia-ai-iot/vllm:latest-jetson-orin \
  vllm serve /model \
    --host 0.0.0.0 \
    --port 8090 \
    --gpu-memory-utilization 0.20 \
    --max-model-len 2048 \
    --enforce-eager
    
    
    
docker run --rm -it \
  --network host \
  --ipc=host \
  --shm-size=16g \
  --ulimit memlock=-1 \
  --ulimit stack=67108864 \
  --runtime=nvidia \
  --name=vllm-orin \    
  -e PYTORCH_NVML_BASED_CUDA_CHECK=0 \
  -e VLLM_WORKER_MULTIPROC_METHOD=spawn \
  -e VLLM_USE_V1=0 \
  -v /mnt/nvme/repo/Agenteam_V2/dockers/llm/openai-gpt-oss-20b:/model \
  -v $HOME/data/vllm_cache:/root/.cache/vllm \
  ghcr.io/nvidia-ai-iot/vllm:latest-jetson-orin \
  vllm serve /model \
    --host 0.0.0.0 \
    --port 8090 \
    --gpu-memory-utilization 0.20 \
    --max-model-len 2048 \
    --enforce-eager    

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