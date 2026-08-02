# Airsim:
```
./Blocks.sh -windowed -ResX=640 -ResY=480 -scalability=1 -t.MaxFPS=30

Steps:
1. Run Q_Ground (remote controller)
2. cd /home/amitli/Agent_Team_Prj/Q_Ground/LinuxNoEditor
3. ./Block ./runh -windowed -ResX=640 -ResY=480 -scalability=1 -t.MaxFPS=30
4. cd /home/amitli/Agent_Team_Prj/Q_Ground/QuadAPI_airsim
5.  sudo ./run_all.sh 

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