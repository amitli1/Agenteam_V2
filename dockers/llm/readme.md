# Download (openai/gpt-oss-20b):
```

pip install -U "huggingface_hub[cli]"
pip install vllm
hf auth login

hf download \
    openai/gpt-oss-20b \
    --local-dir /mnt/nvme/repo/Agenteam_V2/dockers/llm/openai-gpt-oss-20b

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