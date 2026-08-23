# Todo (before integration):
1. vision (air)
2. system tests
3. check handle_message_from_master_drone (air to air)
4. vision and fly - async (call to llm and run) (not sure - what to focus on)
5. stop summary and describe
6. Extract wakeword by myseld and not with LLM (faster)

# v2 LLM
1. if just "hey buddy" - no "waht sould I look for" - then just say "yes" and wait for next command

# IPs:
1. AIR(1) 192.168.144.114

Did:
1. when moving drone - first get to alt and then to destination
2. return home - works
3. test fly to the moon
4. surrund - works (fly with 2 drones)



under docs - write run_all_sim.sh which:

one terminal with 7 tabs (for each tab give name):
1. run the dockers/tts docker
2. run the VisionSimulator docker
3. run project_code/monitor docker
4. /home/amitli/Agent_Team_Prj/Q_Ground/QGroundControl-x86_64.AppImage
5.
cd /home/amitli/Agent_Team_Prj/Q_Ground/LinuxNoEditor
./Block.sh ./runh -windowed -ResX=640 -ResY=480 -scalability=1 -t.MaxFPS=30
6. cd /home/amitli/Agent_Team_Prj/Q_Ground/QuadAPI_airsim
sudo ./run_all.sh 
7. run the dockers/air docker

