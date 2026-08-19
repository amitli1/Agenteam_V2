# Run:
```
    sudo docker compose -f dockercomposeWhisper.yml up --build
    sudo docker compose -f dockercomposeWhisper.yml up 
```

# Error 'address already in use':
```
docker stop agenteam-whisper-intel
docker rm agenteam-whisper-intel
docker compose -f dockers/whisper/intel/docker-compose.whisper-intel.yml up --remove-orphans
```

# Delete all stopped containers
```
docker container prune
```


# make sure /etc/docker/daemon.json on the Jetson host has:
```
{
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  },
  "default-runtime": "nvidia"
}
```

