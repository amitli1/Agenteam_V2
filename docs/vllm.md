# Notes:
1. run twice (for warmup) to get more accurate timing
2. on my laptop qwen is faster ~40% than gpt-oss-20b
3. on my laptop phi3 is faster ~25% than gpt-oss-20b
4. on my laptop qwen3 is faster ~20% than phi3

# Notes 2:
1. sudo docker start vllm_gpt_oss  (or sudo docker stop vllm_gpt_oss)

# Notes 3:
1. On RTX5000 (ADA) PHI         total time: 11.48 seconds
2. On RTX5000 (ADA) GEMMA3      total time: 15.05 seconds
3. On RTX5000 (ADA) GPT-OSS-20B total time: 19.81 seconds

# Intel (VLLM) (GPT-OSS-20B) on NVIDIA RTX 5000 ADA:
        ```
        sudo docker run --rm \
            --runtime=nvidia \
            -e NVIDIA_VISIBLE_DEVICES=all \
            -e VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS=0 \
            -v ~/.cache/huggingface:/root/.cache/huggingface \
            -p 8090:8000 \
            --ipc=host \
            vllm/vllm-openai:latest \
            --model openai/gpt-oss-20b \
            --served-model-name openai/gpt-oss-20b \
            --host 0.0.0.0 \
            --port 8000 \
            --gpu-memory-utilization 0.98 \
            --max-model-len 3000 \
            --max-num-seqs 1 \
            --max-num-batched-tokens 1024
        ```
        
# Intel (VLLM) (Qwen/Qwen3-4B-AWQ) on NVIDIA RTX 5000 ADA:

 ```
 sudo docker run --rm \
    --runtime=nvidia \
    -e NVIDIA_VISIBLE_DEVICES=all \
    -e VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS=0 \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -p 8090:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --model Qwen/Qwen3-4B-AWQ \
    --served-model-name Qwen/Qwen3-4B-AWQ \
    --host 0.0.0.0 \
    --port 8000 \
    --gpu-memory-utilization 0.98 \
    --max-model-len 4096 \
    --max-num-seqs 1 \
    --max-num-batched-tokens 1024
 ```
 ```
llm_model: Qwen/Qwen3-4B-AWQ
 ```


## Intel: Phi-3-mini-4k-instruct-AWQ
 ```
 
  sudo docker run --rm \
    --runtime=nvidia \
    -e NVIDIA_VISIBLE_DEVICES=all \
    -e VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS=0 \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -p 8090:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --model Sreenington/Phi-3-mini-4k-instruct-AWQ \
    --served-model-name Sreenington/Phi-3-mini-4k-instruct-AWQ \
    --host 0.0.0.0 \
    --port 8000 \
    --gpu-memory-utilization 0.95 \
    --max-model-len 4096 \
    --max-num-seqs 1 \
    --max-num-batched-tokens 1024
 ```

## Intel: gaunernst/gemma-3-4b-it-qat-autoawq
 ```
sudo docker run --rm \
    --runtime=nvidia \
    -e NVIDIA_VISIBLE_DEVICES=all \
    -e VLLM_MEMORY_PROFILER_ESTIMATE_CUDAGRAPHS=0 \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -p 8090:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --model gaunernst/gemma-3-4b-it-qat-autoawq \
    --served-model-name gaunernst/gemma-3-4b-it-qat-autoawq \
    --host 0.0.0.0 \
    --port 8000 \
    --gpu-memory-utilization 0.95 \
    --max-model-len 4096 \
    --max-num-seqs 1 \
    --max-num-batched-tokens 1024
```