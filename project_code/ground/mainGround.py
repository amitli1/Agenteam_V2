import json

from pydub import AudioSegment

from project_code.air.main_air import MainAir
from project_code.app_config.settings import app_settings
from project_code.audio.audio_pipeline import AudioPipeline
from project_code.db.database_manager import DatabaseManager
from project_code.ground.monitor_collector import MonitorCollector
from project_code.llm.drone_navigation_agent import DroneNavigationAgent
from project_code.llm.llm_command_parser import LlmCommandParser
from project_code.llm.llm_mission_planner import MissionPlannerAgent
from project_code.llm.llm_vision_parser import VisionParser
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
logging.getLogger("werkzeug").setLevel(logging.ERROR)

app = Flask(__name__)

class MainGround:

    def __init__(self):
        self.audioPipeline        = AudioPipeline(self.handle_user_text)
        self.llmCommandParser     = LlmCommandParser()
        self.llmMissionPlanner    = MissionPlannerAgent()
        self.databaseManager      = DatabaseManager()
        self.DroneNavigationAgent = DroneNavigationAgent()
        self.vision_parser        = VisionParser()
        self.monitorCollector     = MonitorCollector()
        self.monitorCollector.start()

        self.last_master_quad_data = None
        self.last_slave_quad_data  = None
        self.flask_groundthread    = None

        app.add_url_rule("/get_to_destination", view_func=self.on_air_get_to_destination, methods=["POST"], )
        app.add_url_rule("/status",view_func=self.on_air_status_message,methods=["POST"],)
        app.add_url_rule("/text_to_user", view_func=self.on_air_text_to_user, methods=["POST"], )
        self.status_received_event = threading.Event()

        self.master_drone_location = None
        self.slave_drone_location  = None

        self.master_drone_url = f"http://{app_settings.general.master_air_ip}:{app_settings.general.master_air_port}/ground_command"
        self.slave_drone_url  = f"http://{app_settings.general.slave_air_ip}:{app_settings.general.slave_air_port}/ground_command"

        self.get_to_destination  = False
        self.fnc_test_callback   = None
        self.last_fly_command    = None
        self.last_vision_command = None
        self.last_text_command   = None
        self.last_destination    = None

    def set_fnc_test_callback(self, fnc):
        self.fnc_test_callback = fnc

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

        self.monitorCollector.update_air_status_msg(air_status_msg)

        if air_status_msg['drone_role'] == 'master':
            self.last_master_quad_data = json.loads(air_status_msg['last_quad_msg'])

            self.master_drone_location = {'lat': self.last_master_quad_data['lat'],
                                          'lon': self.last_master_quad_data['lon'],
                                          'alt': self.last_master_quad_data['alt'],
                                          'yaw': self.last_master_quad_data['yaw']}


        elif air_status_msg['drone_role'] == 'slave':
            self.last_slave_quad_data = json.loads(air_status_msg['last_quad_msg'])

            self.slave_drone_location = {'lat': self.last_slave_quad_data['lat'],
                                          'lon': self.last_slave_quad_data['lon'],
                                          'alt': self.last_slave_quad_data['alt'],
                                          'yaw': self.last_slave_quad_data['yaw']}

        else:
            logging.error(f"Got unknown drone role: {air_status_msg['drone_role']}")



        self.status_received_event.set()
        return "OK", 200

    def run_tts(self, text_to_user):

        if self.fnc_test_callback is not None:
            self.fnc_test_callback(text_to_user)

        if "OK Flying to the destination" in text_to_user:
            SoundPlayerManager().get_file_queue().put(f"{app_settings.database.audio_files}/OK_Flying_to_the_destination.wav")
            return True
        elif "Hold on, still flying" in text_to_user:
            SoundPlayerManager().get_file_queue().put(f"{app_settings.database.audio_files}/hold_on_still_flying.wav")
            return True
        elif "I have reached the destination." in text_to_user:
            SoundPlayerManager().get_file_queue().put(f"{app_settings.database.audio_files}/I_have_reached_the_destination.wav")
            return True

        try:
            response = requests.post(f"http://{get_running_ip()}:8002/synthesize/", json={"text": text_to_user})
            data = response.json()
            if response.status_code != 200:
                return False
        except Exception as e:
            logging.error(f'Error while sending text: {text_to_user} to TTS tool')
            return False

        prepare_audio_for_speech(data)

        return True

    def on_air_text_to_user(self):

        msg          = request.get_json(silent=True)
        drone_role   = msg['drone_role']
        text_to_user = msg['text_to_user']
        logging.info(f'Got text: {text_to_user} from: {drone_role}')

        self.monitorCollector.update_text_to_user(drone_role, text_to_user)
        if not self.run_tts(text_to_user):
            return f"Error while sending text: {text_to_user} to TTS tool", 400

        return "OK", 200

    def start_ground(self):

        if self.databaseManager.check_if_db_is_valid() is False:
            logging.error('Fix Dataset and then try again')
            return

        self.audio_thread = threading.Thread(
            target=self.audioPipeline.run_audio_pipeline,
            daemon=True,
        )
        self.audio_thread.start()

    def handle_fly_command(self, command):
        if 'home' in command['fly_command']:
            if (command['team_member'] == "team") or (command['team_member'] == "buddy"):
                r = requests.post(self.master_drone_url, json={"command": "home"})

            if (command['team_member'] == "team") or (command['team_member'] == "jarvis"):
                r = requests.post(self.slave_drone_url, json={"command": "home"})
        else:
            result = self.llmMissionPlanner.get_way_points(text_command          = command['fly_command'],
                                                           team_member           = command['team_member'],
                                                           master_drone_location = self.master_drone_location,
                                                           slave_drone_location  = self.slave_drone_location,
                                                           database_manager      = self.databaseManager,
                                                           ALT_DEFAULT           = app_settings.flightPath.default_drone_altitude,
                                                           SPATIAL_DISTANCE      = app_settings.flightPath.spatial_distance,
                                                           DELTA_ALT_SLAVE_DRONE = app_settings.flightPath.slave_drone_altitude_offset,
                                                           last_destination      = self.last_destination)

            if result['status'] == "error":
                logging.error(f"Got error llmMissionPlanner.get_way_points: {result['error']}")
            else:
                logging.info(f"Got plan from LLM. status: {result['status']}, action: {result['action']}, team_member: {result['team_member']}")
            if result['status'] == "success":

                self.last_destination = result['target']

                try:
                    if (result['team_member'] == "team") or (result['team_member'] == "buddy"):
                        plan_list = result['plan']['buddy']
                        r         = requests.post(self.master_drone_url, json={"command": "plan", "plan_list": plan_list})
                        r.raise_for_status()
                    if (result['team_member'] == "team") or (result['team_member'] == "jarvis"):
                        plan_list = result['plan']['jarvis']
                        r         = requests.post(self.slave_drone_url, json={"command": "plan", "plan_list": plan_list})
                except Exception as e:
                    logging.error(f"Error while sending plan to drone: {e}")

    def handle_vision_command(self, text, command):

        result_obj = {
            "success"       : True,
            "need_more_data": False,
            "vision_command": None
        }

        # {'vision_commands': [{'command': 'point', 'need_more_data': False, 'objects': 'red car, blue truck'}]}
        llm_result       = self.vision_parser.parse(text)
        llm_result       = llm_result['vision_commands'][0]
        vision_command   = llm_result['command']
        need_more_data   = llm_result['need_more_data']
        objects_to_focus = llm_result['objects']

        # save vision command in the return result
        result_obj['vision_command'] = vision_command

        if need_more_data:
            result_obj['success']        = False
            result_obj['need_more_data'] = True
            return result_obj

        command_to_air = {
            "vision_command": vision_command,
            "objects_to_focus": objects_to_focus
        }

        r = requests.post(self.master_drone_url, json={"command": "vision", "vision_command": command_to_air})
        r.raise_for_status()

        if r.status_code != 200:
            logging.error(f"Unexpected status when sending command to air: {r.status_code}")
            result_obj['success'] = False
            result_obj['need_more_data'] = False
            return result_obj

        return result_obj

    def merge_current_and_previous_commands(self, l_current_command, current_text):
        if self.last_fly_command is None and self.last_vision_command is None:
            return l_current_command, current_text

        l_current_command[0]['fly_command']    = self.last_fly_command
        l_current_command[0]['vision_command'] = f"{self.last_vision_command} {current_text}"

        return l_current_command, f"{self.last_text_command} {current_text}"

    def handle_user_text(self, text):

        self.monitorCollector.update_user_command("", text)


        l_commands       = self.llmCommandParser.split_user_command(text)
        l_commands, text = self.merge_current_and_previous_commands(l_commands, text)

        for command in l_commands:
            logging.info(command)

            if command['vision_command'] != '':
                vision_result_ = self.handle_vision_command(text, command)
                if vision_result_['need_more_data']:
                    self.run_tts("what should I look for ?")
                    self.last_fly_command    = command['fly_command']
                    self.last_vision_command = vision_result_['vision_command']
                    self.last_text_command   = text
                    return

            if command['fly_command'] != '':
                self.handle_fly_command(command)

        logging.info(f'Clear last_fly_command and last_vision_command')
        self.last_fly_command    = None
        self.last_vision_command = None
        self.last_text_command   = None





def run_ground():
    create_output_folder()
    if check_models() is False:
        # exit(0)
        None
    else:
        warmup()

    SoundPlayerManager().start()

    mainGround = MainGround()
    mainGround.flask_groundthread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=app_settings.general.ground_port, use_reloader=False),
        daemon=True,
    )
    mainGround.flask_groundthread.start()
    logging.info('Waiting for first message from AIR, before continue')
    mainGround.status_received_event.wait()
    logging.info('Got first message from AIR, continue')
    return mainGround




if __name__ == "__main__":
    mainGround = run_ground()
    mainGround.start_ground()
    mainGround.flask_groundthread.join()
    mainGround.audio_thread.join()

    #time.sleep(10)
    #logging.info('finished')
