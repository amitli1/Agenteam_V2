# Notes:
1. run twice (for warmup) to get more accurate timing
2. on my laptop qwen is faster ~40% than gpt-oss-20b
3. on my laptop phi3 is faster ~25% than gpt-oss-20b
4. on my laptop qwen3 is faster ~20% than phi3

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
        

## llm_coommand_parser_v2_tester (on RTX 5000 ADA):
        
        [PASS] [1.0 sec] hey buddy fly to building number two
        [PASS] [1.0 sec] hey team fly home
        [PASS] [1.0 sec] hey jarvis surround the junction
        [PASS] [0.8 sec] hey jarvis surround the building and look for people and vehicles
        [PASS] [1.0 sec] hey jarvis hold the junction
        [PASS] [1.0 sec] buddy hold the junction and tell me if you see red car or blue truck
        [PASS] [0.9 sec] buddy follow the yellow car
        [PASS] [0.8 sec] hey team follow
        [PASS] [1.0 sec] buddy describe
        [PASS] [0.9 sec] buddy describe the person in the car
        [PASS] [0.9 sec] hey jarvis point at the yellow car
        [PASS] [1.4 sec] hey jarvis surround the building and tell me what you see hey jarvis look for birds
        [PASS] [1.8 sec] Hey team, walk around the building and describe to me what you see
        [PASS] [0.9 sec] Hey jarvis stop pointing
        [PASS] [2.0 sec] Hey team, hold the junction, if you see any vehicle follow it
        [PASS] [1.2 sec] Hey buddy stop following
        [PASS] [0.8 sec] Hey buddy hold
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

## llm_coommand_parser_v2_tester (on RTX 5000 ADA):
 ```

 
[PASS] [0.7 sec] hey buddy fly to building number two
[PASS] [0.5 sec] hey team fly home
[PASS] [0.5 sec] hey jarvis surround the junction
[PASS] [0.6 sec] hey jarvis surround the building and look for people and vehicles
[PASS] [0.5 sec] hey jarvis hold the junction
[PASS] [0.6 sec] buddy hold the junction and tell me if you see red car or blue truck
[PASS] [0.6 sec] buddy follow the yellow car
[PASS] [0.5 sec] hey team follow
[PASS] [0.6 sec] buddy describe
[PASS] [0.6 sec] buddy describe the person in the car
[PASS] [0.5 sec] hey jarvis point at the yellow car
[FAIL] [0.6 sec] hey jarvis surround the building and tell me what you see hey jarvis look for birds
    expected: {'fly_command': {'fly_cmd_type': 'surround', 'location': 'building'}, 'vision_command': {'vision_cmd_type': 'summary', 'vision_cmd_action': 'start', 'objects': 'birds'}, 'team_member': 'jarvis', 'need_more_data': False}
    actual  : {'fly_command': {'fly_cmd_type': 'surround', 'location': 'building'}, 'vision_command': {'vision_cmd_type': 'summary', 'vision_cmd_action': 'start', 'objects': ''}, 'team_member': 'jarvis', 'need_more_data': True}
[PASS] [0.6 sec] Hey team, walk around the building and describe to me what you see
[PASS] [0.5 sec] Hey jarvis stop pointing
[FAIL] [0.6 sec] Hey team, hold the junction, if you see any vehicle follow it
    expected: {'fly_command': {'fly_cmd_type': 'follow', 'location': 'vehicle'}, 'vision_command': {'vision_cmd_type': 'hold', 'vision_cmd_action': 'start', 'objects': 'vehicle'}, 'team_member': 'team', 'need_more_data': False}
    actual  : {'fly_command': {'fly_cmd_type': 'follow', 'location': 'vehicle'}, 'vision_command': {'vision_cmd_type': 'hold', 'vision_cmd_action': 'start', 'objects': 'junction'}, 'team_member': 'team', 'need_more_data': False}
[PASS] [0.6 sec] Hey buddy stop following
[PASS] [0.6 sec] Hey buddy hold

15/17 tests passed.

 ```

## Phi-3-mini-4k-instruct-AWQ
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
    
    
    
[PASS] [0.9 sec] hey buddy fly to building number two
[PASS] [0.7 sec] hey team fly home
[PASS] [0.7 sec] hey jarvis surround the junction
[PASS] [0.7 sec] hey jarvis surround the building and look for people and vehicles
[PASS] [0.6 sec] hey jarvis hold the junction
[PASS] [0.8 sec] buddy hold the junction and tell me if you see red car or blue truck
[PASS] [0.8 sec] buddy follow the yellow car
[PASS] [0.6 sec] hey team follow
[PASS] [0.6 sec] buddy describe
[PASS] [0.7 sec] buddy describe the person in the car
[PASS] [0.6 sec] hey jarvis point at the yellow car
[PASS] [0.7 sec] hey jarvis surround the building and tell me what you see hey jarvis look for birds
[PASS] [0.7 sec] Hey team, walk around the building and describe to me what you see
[PASS] [0.6 sec] Hey jarvis stop pointing
[PASS] [0.8 sec] Hey team, hold the junction, if you see any vehicle follow it
[PASS] [0.6 sec] Hey buddy stop following
[PASS] [0.6 sec] Hey buddy hold
 ```