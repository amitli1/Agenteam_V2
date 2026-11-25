```
curl -X POST http://localhost:8013/transcribe/   -F "file=@/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/English/Destination_not_found.wav"
```

```
curl -X POST http://localhost:8002/synthesize/ \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test."}'
```