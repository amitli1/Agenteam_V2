# Airsim:
```
./Blocks.sh -windowed -ResX=640 -ResY=480 -scalability=1 -t.MaxFPS=30

Steps:
1. [Airsim]   cd /home/amitli/Agent_Team_Prj/Q_Ground/LinuxNoEditor
2. [Airsim]   ./Block.sh ./runh -windowed -ResX=640 -ResY=480 -scalability=1 -t.MaxFPS=20
3. [QuadAPI]  ~/repo/QUAD_2_DRONES/QuadAPI_airsim_dual/QuadAPI_airsim$ sudo ./run_all.sh 
4. [Q Ground] Run Q_Ground (remote controller) 

```

# Air:
```
udo docker compose -f docker-compose.air-intel.yml up --build
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

# Quad:
```
when finished:
is_mission_finished = True (and flight_mode': 'HOLD')
flight_mode = 'HOLD' (from flight_mode': 'MISSION')
mission_progress='2/2' (and flight_mode': 'HOLD')
```