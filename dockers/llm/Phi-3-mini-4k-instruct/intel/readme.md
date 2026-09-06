# Phi-3-mini-4k-instruct via vLLM (Intel / x86_64)

Serves `microsoft/Phi-3-mini-4k-instruct` behind vLLM's OpenAI-compatible API
server. Model weights are downloaded and baked into the image at build time,
so the container runs fully offline afterwards.

Requires an NVIDIA GPU on the host + the NVIDIA Container Toolkit.

# gpu_memory_utilization:
If you see `ValueError: No available memory for the cache blocks. Try
increasing gpu_memory_utilization`, raise `GPU_MEMORY_UTILIZATION` in
`docker-compose.yml` (e.g. `0.9`), or lower `MAX_MODEL_LEN`, then
`docker compose up --build`.

# run:
```
sudo docker compose up --build
sudo docker compose up
```

# test:
```
curl http://localhost:8090/v1/models
```

or

```
curl http://localhost:8090/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Phi-3-mini-4k-instruct",
    "messages": [
      {
        "role": "user",
        "content": "What is the capital of France?"
      }
    ],
    "max_tokens": 50
  }'
```

# stop:
```
sudo docker compose down
```

