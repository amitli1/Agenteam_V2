# Whisper docker

## step 1:
```
sudo docker compose -f docker-compose.yml up --build
```
Model download to: '/mnt/nvme/models/whisper-large-v3-turbo/'

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
  http://localhost:8013/transcribe \
  -F "file=@/mnt/nvme/repo/Agenteam_V2/dockers/whisper/jetson/1.wav"
```
   



