# Download:
```
hf download hexgrad/Kokoro-82M --local-dir /mnt/nvme/models/kokoro_model
```

# Test:
```
 curl -X POST 192.168.144.113:8123/text_to_user   -H "Content-Type: application/json"   -d '{"text": "Hello, this is a test message!"}'
```
```
curl -v http://localhost:8002/docs
``` 