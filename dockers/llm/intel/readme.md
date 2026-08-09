# Run openai/gpt-oss-20b on GPU & Intel CPU:

## Step I: Download the model
```
hf download openai/gpt-oss-20b --local-dir ~/repo/Agenteam_V2/dockers/llm/model/
```


## Step II: Download the tokenizer files
```
mkdir -p $HOME/.cache/tiktoken
wget -q https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken -O $HOME/.cache/tiktoken/cl100k_ba
wget -q https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken -O $HOME/.cache/tiktoken/o200k_base
```

## Step III: Run model (port 8090 & --gpu-memory-utilization 0.90)
```
sudo docker rm -f gpt-oss-20b

sudo docker run -d \
  --name gpt-oss-20b \
  --runtime=nvidia \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -e NVIDIA_DRIVER_CAPABILITIES=compute,utility \
  -e VLLM_ATTENTION_BACKEND=TRITON_ATTN_VLLM_V1 \
  -e PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
  -e HF_HUB_OFFLINE=1 \
  -e TRANSFORMERS_OFFLINE=1 \
  -e TIKTOKEN_CACHE_DIR=/root/.cache/tiktoken \
  -e TIKTOKEN_RS_CACHE_DIR=/root/.cache/tiktoken/harmony \
  -p 8090:8090 \
  -v /home/amitli/repo/Agenteam_V2/dockers/llm/model:/model:ro \
  -v /home/amitli/.cache/tiktoken:/root/.cache/tiktoken:ro \
  vllm/vllm-openai:gptoss \
  --model /model \
  --served-model-name gpt-oss-20b \
  --host 0.0.0.0 \
  --port 8090 \
  --gpu-memory-utilization 0.95 \
  --max-model-len 32768 \
  --max-num-seqs 32
```


## Step IV: Test:
```
curl http://localhost:8090/v1/models
```
```
curl http://127.0.0.1:8090/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-oss-20b",
    "messages": [
      {
        "role": "user",
        "content": "What is 17 multiplied by 23? Explain briefly."
      }
    ],
    "max_tokens": 100,
    "temperature": 0
  }'

```


## Parms:
```
1. "max-model-len" → how long one request is allowed to be (prompt + generated output). 
2. "max-num-seqs" → how many requests can be processed in parallel.
```