# Airsim:
```
./Blocks.sh -windowed -ResX=640 -ResY=480 -scalability=1 -t.MaxFPS=30
```

# Jetson:
```
ssh -L 8090:10.42.0.1:8090 amitli@l-p-amitli-ww
ssh -L 8090:10.42.0.1:8002 amitli@l-p-amitli-ww
ssh -L 8090:10.42.0.1:8013 amitli@l-p-amitli-ww
```

# Docker:
```
sudo docker compose -f docker-compose.tts-intel.yml up
``` 

# failed to set up container networking:
```
docker compose down --remove-orphans
```