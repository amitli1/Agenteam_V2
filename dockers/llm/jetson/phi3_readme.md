 ```
hf download \
    Sreenington/Phi-3-mini-4k-instruct-AWQ \
    --local-dir /mnt/nvme/repo/Agenteam_V2/dockers/llm/phi-3-mini-4k-instruct-AWQ
 ```

 ```
services:
  vllm-phi-3-mini:
    container_name: vllm-phi-3-mini
    build:
      context: ..
      dockerfile: Dockerfile

    ports:
      - "8090:8090"

    environment:
      - NVIDIA_VISIBLE_DEVICES=all

    runtime: nvidia

    command:
      - bash
      - -c
      - |
          sleep 1
          python3 -m vllm.entrypoints.openai.api_server \
            --model /models/phi-3-mini-4k-instruct-AWQ \
            --quantization awq \
            --gpu-memory-utilization 0.90 \
            --max-model-len 4096 \
            --port 8090

    volumes:
      - /mnt/nvme/repo/Agenteam_V2/dockers/llm:/models

    shm_size: "16gb"
    restart: always
 ```

 ```
 model="/models/phi-3-mini-4k-instruct-AWQ"
 ```

 ```
 curl http://localhost:8090/v1/models
 ```