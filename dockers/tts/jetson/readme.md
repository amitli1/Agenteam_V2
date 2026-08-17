# TTS docker (Kokoro)

## step 1:
```
sudo docker compose -f docker-compose.yml up --build
```
Model download to: '/mnt/nvme/models/kokoro-82m/'

## step 2:
```
Under docker-compose.yaml change HF_HUB_OFFLINE to 1
```

## step 3:
```
sudo docker compose -f docker-compose.yml up
```

## step 4:
```
curl -X POST \
  http://localhost:8002/synthesize/ \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test message!"}'
```

```
curl -v http://localhost:8002/docs
```

