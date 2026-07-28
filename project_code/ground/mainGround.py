import json

from pydub import AudioSegment

from project_code.air.main_air import MainAir
from project_code.app_config.settings import app_settings
from project_code.audio.audio_pipeline import AudioPipeline
from project_code.db.database_manager import DatabaseManager
from project_code.llm.drone_navigation_agent import DroneNavigationAgent
from project_code.llm.llm_command_parser import LlmCommandParser
from project_code.llm.llm_mission_planner import MissionPlannerAgent
from project_code.utils.logger_utils import init_logger
from project_code.utils.sound_player import SoundPlayerManager
from project_code.utils.utils import create_output_folder, check_models, warmup, get_running_ip, \
    prepare_audio_for_speech
import logging
import threading
import time
import requests
import numpy as np
from flask import Flask, jsonify, request

init_logger()

app = Flask(__name__)

class MainGround:

    def __init__(self):
        self.audioPipeline        = AudioPipeline(self.handle_user_text)
        self.llmCommandParser     = LlmCommandParser()
        self.llmMissionPlanner    = MissionPlannerAgent()
        self.databaseManager      = DatabaseManager()
        self.DroneNavigationAgent = DroneNavigationAgent()

        self.last_master_quad_data = None
        self.last_slave_quad_data = None

        app.add_url_rule("/get_to_destination", view_func=self.on_air_get_to_destination, methods=["POST"], )
        app.add_url_rule("/status",view_func=self.on_air_status_message,methods=["POST"],)
        app.add_url_rule("/text_to_user", view_func=self.on_air_text_to_user, methods=["POST"], )
        self.status_received_event = threading.Event()

        self.master_drone_location = None
        self.slave_drone_location  = None

        self.master_drone_url = f"http://{app_settings.general.master_air_ip}:{app_settings.general.master_air_port}/ground_command"
        self.slave_drone_url  = f"http://{app_settings.general.slave_air_ip}:{app_settings.general.slave_air_port}/ground_command"

        self.get_to_destination = False

    def on_air_get_to_destination(self):
        air_msg = request.get_json(silent=True)

        self.get_to_destination = True
        if air_msg['drone_role'] == 'master':
            None
        else:
            None
        return "OK", 200

    def on_air_status_message(self):
        air_status_msg = request.get_json(silent=True)
        if air_status_msg['drone_role'] == 'master':
            self.last_master_quad_data = json.loads(air_status_msg['last_quad_msg'])

            self.master_drone_location = {'lat': self.last_master_quad_data['lat'],
                                          'lon': self.last_master_quad_data['lon'],
                                          'alt': self.last_master_quad_data['alt'],
                                          'yaw': self.last_master_quad_data['yaw']}


        elif air_status_msg['drone_role'] == 'slave':
            self.last_slave_quad_data = air_status_msg['last_quad_msg']

            self.slave_drone_location = {'lat': self.last_master_quad_data['lat'],
                                          'lon': self.last_master_quad_data['lon'],
                                          'alt': self.last_master_quad_data['alt'],
                                          'yaw': self.last_master_quad_data['yaw']}

        else:
            logging.error(f"Got unknown drone role: {air_status_msg['drone_role']}")



        self.status_received_event.set()
        return "OK", 200


    def on_air_text_to_user(self):

        msg          = request.get_json(silent=True)
        drone_role   = msg['drone_role']
        text_to_user = msg['text_to_user']
        logging.info(f'Got text: {text_to_user} from: {drone_role}')

        response = requests.post(f"http://{get_running_ip()}:8002/synthesize/", json={"text": text_to_user})
        data = response.json()
        if response.status_code != 200:
            return f"Error while sending text: {text_to_user} to TTS tool", 400

        prepare_audio_for_speech(data)
        return "OK", 200

    def start_ground(self):
        self.audio_thread = threading.Thread(
            target=self.audioPipeline.run_audio_pipeline,
            daemon=True,
        )
        self.audio_thread.start()

    def handle_user_text(self, text):
        l_commands = self.llmCommandParser.split_user_command(text)
        for command in l_commands:
            logging.info(command)

            if 'home' in command['fly_command']:
                if (command['team_member'] == "team") or (command['team_member'] == "buddy"):
                    r = requests.post(self.master_drone_url,json={"command": "home"})

                if (command['team_member'] == "team") or (command['team_member'] == "jarvis"):
                    r = requests.post(self.slave_drone_url, json={"command": "home"})

            elif command['fly_command'] != '':
                result = self.llmMissionPlanner.get_way_points(text_command=command['fly_command'],
                                                      team_member=command['team_member'],
                                                      master_drone_location=self.master_drone_location,
                                                      slave_drone_location=self.slave_drone_location,
                                                      database_manager=self.databaseManager,
                                                      ALT_DEFAULT=app_settings.flightPath.default_drone_altitude,
                                                      SPATIAL_DISTANCE=app_settings.flightPath.spatial_distance,
                                                      DELTA_ALT_SLAVE_DRONE=app_settings.flightPath.slave_drone_altitude_offset)

                logging.info(f"Got plan from LLM. status: {result['status']}, action: {result['action']}, team_member: {result['team_member']}")
                if result['status'] == "success":
                    #(result['action'] == "goto") or (result['action'] == "surround")
                    if (result['team_member'] == "team") or (result['team_member'] == "buddy"):
                        plan_list = result['plan']['buddy']
                        r         = requests.post(self.master_drone_url,json={"command": "plan","plan_list": plan_list})
                        r.raise_for_status()
                    if (result['team_member'] == "team") or (result['team_member'] == "jarvis"):
                        plan_list = result['plan']['jarvis']
                        r         = requests.post(self.slave_drone_url,json={"command": "plan","plan_list": plan_list})



def run_ground_test():

    mainAir    = MainAir()
    air_thread = threading.Thread(target=mainAir.start_air, daemon=True)
    air_thread.start()

    mainGround = MainGround()

    flask_groundthread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=app_settings.general.ground_port, use_reloader=False),
        daemon=True,
    )
    flask_groundthread.start()

    logging.info('Wait till getting messages from air')
    mainGround.status_received_event.wait()
    logging.info('Got messages from air - continue')
    mainGround.handle_user_text("Hey buddy go to building number one")
    while True:
        time.sleep(1)
        if mainGround.get_to_destination:
            mainGround.handle_user_text("Hey buddy hold the junction")
            time.sleep(5)

            mainGround.handle_user_text("Hey buddy return home")
            time.sleep(5)
            break



def run_ground():
    create_output_folder()
    if check_models() is False:
        # exit(0)
        None
    else:
        warmup()

    SoundPlayerManager().start()

if __name__ == "__main__":
    run_ground()
    run_ground_test()
    time.sleep(10)
    logging.info('finished')
