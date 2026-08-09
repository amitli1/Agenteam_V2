# Whisper docker

## 🧪 Introduction

1. Download model with huggingface-cli (via venv):
   ``` 
    huggingface-cli download mobiuslabsgmbh/faster-whisper-large-v3-turbo --cache-dir /mnt/nvme/models/faster-whisper-large-v3-turbo
   ```
   ```
    huggingface-cli download openai/whisper-large-v3-turbo --cache-dir /mnt/nvme/models/huggingface
   ```
2. Assumptions:
    ```
    1. Folder: /mnt/nvme/repo/Jetson
    2. Models: /mnt/nvme/models/ 
    ```

3.  build:
```
     docker compose up --build
```

4.  Test (online):
    ```
    run test_docker_whisper.py
    ```
    
6.  Test (offline):
    ```
    1. turn off wifi & restart jetson
    2. run test_docker_whisper.py (to be sure it run without internet)
    ```
   



