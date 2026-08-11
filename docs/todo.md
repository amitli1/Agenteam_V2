1. cant find lcation
2. 'go to another one'' (whisper)
3. 'go to Bill 1'''
4. "ok flying to the destination x2"
5. I have reached the destination x2
6. what should I look for
7. 'body' 

4. monitor
3. vision
4. on jetson
5. system tests
6. check handle_message_from_master_drone (air to air)
7. handle hold (team and master
9. hold ? say on what ? ("Hold the junction and look for weapons))
10. vision and fly - async (call to llm and run) (not sure - what to focus on)
12. LLM params from config file
13. run wtih wake word (buddy and team) 
14. stop summary and describe
15. instead of TTS use - wav (save what you can)
16. take the alt (drone 1 and 2) to get into from jetson_1
17. monitor - dockers
18.     #
    # download open wake word models to:
    # /mnt/nvme/python_venvs/agentVenv/lib/python3.10/site-packages/openwakeword/resources/models/
    #
    openwakeword.utils.download_models()
19. remove SINGLE_MODEL
 

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

