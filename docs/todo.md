1. surround- not works sometimes (+ add logs to air with box)
3. vision
4. on jetson
5. system tests
6. check handle_message_from_master_drone (air to air)
7. handle hold (team and master
9. hold ? say on what ? ("Hold the junction and look for weapons))
10. vision and fly - async (call to llm and run) (not sure - what to focus on)
12. LLM params from config file
14. stop summary and describe
18.     #
    # download open wake word models to:
    # /mnt/nvme/python_venvs/agentVenv/lib/python3.10/site-packages/openwakeword/resources/models/
    #
    openwakeword.utils.download_models()

 

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

