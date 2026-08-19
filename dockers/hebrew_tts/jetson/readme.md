# Hebrew TTS docker (Piper)

## step 1:

Make sure the Hebrew Piper model files exist on the host at:
```
/home/amitli/Documents/Hebrew_TTS_Model/he_IL-saspeech-medium.onnx
/home/amitli/Documents/Hebrew_TTS_Model/he_IL-saspeech-medium.onnx.json
```
Download from:
https://huggingface.co/rhasspy/piper-voices/tree/main/he/he_IL/saspeech/medium

## step 2:
```
sudo docker compose -f docker-compose.yml up --build
```

## step 3:
```
curl -X POST \
  http://localhost:8003/synthesize/ \
  -H "Content-Type: application/json" \
  -d '{"text": "הגעתי ליעד"}'
```

```
curl -v http://localhost:8003/docs
```

