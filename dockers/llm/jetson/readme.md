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

# Tiktoken download (~5.3MB):
```
mkdir -p $HOME/.cache/tiktoken
wget -q https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken -O $HOME/.cache/tiktoken/cl100k_ba
wget -q https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken -O $HOME/.cache/tiktoken/o200k_base
```

# Docker params:
```
docker run -d \
  --name gpt-oss-20b \
  --runtime=nvidia \
  --ipc=host \
  -p 8090:8000 \
  -v $HOME/.cache/huggingface:/root/.cache/huggingface \
  -v $HOME/.cache/tiktoken:/etc/encodings \
  -e TIKTOKEN_ENCODINGS_BASE=/etc/encodings \
  ghcr.io/nvidia-ai-iot/vllm:latest-jetson-orin \
  vllm serve openai/gpt-oss-20b \
    --gpu-memory-utilization 0.85
    
    
-d 	   	                             - detach mode (docker logs -f gpt-oss-20b)
--name      	                             - Assigns the container the name (docker stop gpt-oss-20b, docker logs gpt-oss-20b) (Without --name, Docker generates a random name.)
--runtime=nvidia                             - Tells Docker to use the NVIDIA container runtime (not CPU)
--ipc=host                                   - (PyTorch/vLLM that use shared memory for communication between processes.)
-p 8090:8000                                 - HOST_PORT:CONTAINER_PORT (listen to 8000 inside the container)
-v HOST_PATH:CONTAINER_PATH                  - bind mount
-e TIKTOKEN_ENCODINGS_BASE=/etc/encodings    - (Sets an environment variable inside the container.)
vllm serve                                   - Starts the vLLM inference server.


1. The first time you run the container, the model may be downloaded into $HOME/.cache/huggingface
2. ghcr.io/nvidia-ai-iot/vllm:latest-jetson-orin (This is the Docker image from which the container is created.)
3. vllm serve openai/gpt-oss-20b 
	3.1  It tells vLLM to load the gpt-oss-20b model from the openai namespace on Hugging Face.
	3.2 The first time it is needed, the model is downloaded into the Hugging Face cache you mounted earlier
```
