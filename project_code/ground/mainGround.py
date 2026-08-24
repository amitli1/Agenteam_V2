import json

from pydub import AudioSegment

from project_code.app_config.settings import app_settings, log_app_settings
from project_code.audio.audio_pipeline import AudioPipeline
from project_code.db.database_manager import DatabaseManager
from project_code.ground.monitor_collector import MonitorCollector
from project_code.llm.drone_navigation_agent import DroneNavigationAgent
from project_code.llm.llm_command_parser import LlmCommandParser
from project_code.llm.llm_command_parser_v2 import LlmCommandParser_V2
from project_code.llm.llm_mission_planner import MissionPlannerAgent
from project_code.llm.llm_vision_parser import VisionParser
from project_code.utils.logger_utils import init_logger
from project_code.utils.sound_player import SoundPlayerManager
from project_code.utils.utils import create_output_folder, check_models, warmup, get_running_ip, \
    prepare_audio_for_speech, is_intel, log_version, log_distances
import logging
import threading
import time
import requests
import numpy as np
from flask import Flask, jsonify, request
import re

init_logger(jetson_type="ground")
logging.getLogger("werkzeug").setLevel(logging.ERROR)

app = Flask(__name__)

class MainGround:

    def __init__(self):
        self.audioPipeline        = AudioPipeline(self.handle_user_text_2)
        self.llmCommandParser     = LlmCommandParser()
        self.llmCommandParser_v2  = LlmCommandParser_V2()
        self.llmMissionPlanner    = MissionPlannerAgent()
        self.databaseManager      = DatabaseManager()
        self.DroneNavigationAgent = DroneNavigationAgent()
        self.vision_parser        = VisionParser()
        self.monitorCollector     = MonitorCollector()
        self.monitorCollector.start()

        self.last_master_quad_data = None
        self.last_slave_quad_data  = None
        self.flask_groundthread    = None

        app.add_url_rule("/get_to_destination" , view_func=self.on_air_get_to_destination  , methods=["POST"], )
        app.add_url_rule("/status"             , view_func=self.on_air_status_message      ,methods=["POST"],)
        app.add_url_rule("/text_to_user"       , view_func=self.on_air_text_to_user        , methods=["POST"], )
        self.status_received_event = threading.Event()

        self.master_drone_location = None
        self.slave_drone_location  = None

        self.master_drone_url = f"http://{app_settings.general.master_air_ip}:{app_settings.general.master_air_port}/ground_command"
        self.slave_drone_url  = f"http://{app_settings.general.slave_air_ip}:{app_settings.general.slave_air_port}/ground_command"

        self.get_to_destination        = False
        self.fnc_test_callback         = None
        self.last_fly_command          = None
        self.last_vision_command       = None
        self.last_text_command         = None
        self.last_destination          = None
        self.log_master_drone_distance = False
        self.log_slave_drone_distance  = False

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

            if self.log_master_drone_distance is False:
                log_distances("Master Drone Distances:", self.master_drone_location, self.databaseManager.get_db())
                self.log_master_drone_distance = True


        elif air_status_msg['drone_role'] == 'slave':
            self.last_slave_quad_data = json.loads(air_status_msg['last_quad_msg'])

            self.slave_drone_location = {'lat': self.last_slave_quad_data['lat'],
                                          'lon': self.last_slave_quad_data['lon'],
                                          'alt': self.last_slave_quad_data['alt'],
                                          'yaw': self.last_slave_quad_data['yaw']}

            if self.log_slave_drone_distance is False:
                log_distances("Slave Drone Distances:", self.slave_drone_location, self.databaseManager.get_db())
                self.log_slave_drone_distance = True

        else:
            logging.error(f"Got unknown drone role: {air_status_msg['drone_role']}")



        self.status_received_event.set()
        return "OK", 200

    def run_tts(self, text_to_user, drone_role=""):

        self.monitorCollector.update_text_to_user(drone_role, text_to_user)

        if self.fnc_test_callback is not None:
            self.fnc_test_callback(text_to_user)

        if "Startup finished" in text_to_user:
            SoundPlayerManager().get_file_queue().put(f"{app_settings.database.audio_files}/Startup_finished.wav")
            return True

        if "OK Flying to the destination" in text_to_user:
            SoundPlayerManager().get_file_queue().put(f"{app_settings.database.audio_files}/OK_Flying_to_the_destination.wav")
            return True
        elif "Hold on, still flying" in text_to_user:
            SoundPlayerManager().get_file_queue().put(f"{app_settings.database.audio_files}/hold_on_still_flying.wav")
            return True
        elif "I have reached the destination." in text_to_user:
            logging.info(f'Put I_have_reached_the_destination.wav into the Q')
            SoundPlayerManager().get_file_queue().put(f"{app_settings.database.audio_files}/I_have_reached_the_destination.wav")
            return True
        elif "what should I look for ?" in text_to_user:
            SoundPlayerManager().get_file_queue().put(f"{app_settings.database.audio_files}/What_should_I_look_for.wav")
            return True
        elif "I dont understand please repeat command" in text_to_user:
            SoundPlayerManager().get_file_queue().put(f"{app_settings.database.audio_files}/I_dont_understand_please_repeat_command.wav")
            return True
        elif text_to_user.lower() == "NO_MASTER_DRONE: master drone location is not available.".lower():
            SoundPlayerManager().get_file_queue().put(f"{app_settings.database.audio_files}/No_master_drone.wav")
            return True
        elif text_to_user.lower() == "NO_SLAVE_DRONE: slave drone is not available.".lower():
            SoundPlayerManager().get_file_queue().put(f"{app_settings.database.audio_files}/No_slave_drone.wav")
            return True
        elif "DESTINATION_NOT_FOUND".lower() in text_to_user.lower():
            SoundPlayerManager().get_file_queue().put(f"{app_settings.database.audio_files}/Destination_not_found.wav")
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

        if not self.run_tts(text_to_user, drone_role):
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
        """
           command = {
               "fly_command": "home",
               "team_member": "team"
           }
        """

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
                self.run_tts(result['error'], "ground")
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

    def handle_vision_command(self, text):

        result_obj = {
            "success"       : True,
            "need_more_data": False,
            "vision_command": None
        }

        # {'vision_commands': [{'command': 'point', 'need_more_data': False, 'objects': 'red car, blue truck'}]}
        llm_result       = self.vision_parser.parse(text)
        try:
            llm_result       = llm_result['vision_commands'][0]
            vision_command   = llm_result['command']
            need_more_data   = llm_result['need_more_data']
            objects_to_focus = llm_result['objects']
        except Exception as e:
            logging.error(f"Error while parsing vision command: {e}")
            result_obj['success']        = False
            result_obj['need_more_data'] = False
            return result_obj

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

    def remove_wakewords(self, current_text):
        # remove wake word from last text command
        wake_words = ["hey buddy", "buddy", "jarvis", "team"]
        cleaned_current_text = current_text.lower()
        for w in wake_words:
            cleaned_current_text = re.sub(rf"\b{re.escape(w)}\b", "", cleaned_current_text, flags=re.IGNORECASE)
        cleaned_current_text = re.sub(r"\s+", " ", cleaned_current_text).strip()
        return cleaned_current_text

    def merge_current_and_previous_commands(self, l_current_command, current_text):
        if self.last_fly_command is None and self.last_vision_command is None:
            return l_current_command, current_text

        l_current_command[0]['fly_command']    = self.last_fly_command
        l_current_command[0]['vision_command'] = f"{self.last_vision_command} {current_text}"

        # remove wake word from last text command
        cleaned_current_text = self.remove_wakewords(current_text)

        # return values
        return l_current_command, f"{self.last_text_command} {cleaned_current_text}"

    def log_wait_for_next_command(self):

        text = "Waiting for next user speech command"
        lines = str(text).splitlines()
        width = max(len(line) for line in lines)

        logging.info("┌" + "─" * (width + 2) + "┐")
        for line in lines:
            logging.info(f"│ {line:<{width}} │")
        logging.info("└" + "─" * (width + 2) + "┘")

    def handle_user_text_2(self, text):
        self.monitorCollector.update_user_command("", text)

        text        = f"{self.last_text_command} {text}"
        llm_command = self.llmCommandParser_v2.split_user_command(text)

        if llm_command['need_more_data']:
            if (llm_command['vision_command']['vision_cmd_type'] == "") and (llm_command['vision_command']['vision_cmd_type'] == ""):
                self.last_text_command = ""
                self.log_wait_for_next_command()
                return

            self.run_tts("what should I look for ?", "ground")
            text                     = self.remove_wakewords(text)
            self.last_text_command   = text
            self.log_wait_for_next_command()
            return

        if llm_command['vision_command']['vision_cmd_type'] != "":
            command_to_air = {
                "vision_command"  : llm_command['vision_command']['vision_cmd_type'],
                "objects_to_focus": llm_command['vision_command']['objects']
            }

            r = requests.post(self.master_drone_url, json={"command": "vision", "vision_command": command_to_air})
            r.raise_for_status()

        if llm_command['fly_command']['fly_cmd_type'] != "":
            fly_command_to_air                 = {}
            fly_command_to_air['team_member']  = llm_command['team_member']
            fly_command_to_air['fly_command']  = f"{llm_command['fly_command']['fly_cmd_type']} {llm_command['fly_command']['location']}"
            self.handle_fly_command(fly_command_to_air)

        logging.info(f'Clear last_text_command')
        self.last_text_command = ""
        self.log_wait_for_next_command()

    def handle_user_text(self, text):

        self.monitorCollector.update_user_command("", text)


        l_commands       = self.llmCommandParser.split_user_command(text)
        l_commands, text = self.merge_current_and_previous_commands(l_commands, text)

        for command in l_commands:
            logging.info(command)

            if command['vision_command'] != '':
                vision_result_ = self.handle_vision_command(text)
                if vision_result_['need_more_data']:
                    self.run_tts("what should I look for ?", "ground")
                    self.last_fly_command    = command['fly_command']
                    self.last_vision_command = vision_result_['vision_command']
                    self.last_text_command   = text
                    self.log_wait_for_next_command()
                    return

            if command['fly_command'] != '':
                self.handle_fly_command(command)

        logging.info(f'Clear last_fly_command and last_vision_command')
        self.last_fly_command    = None
        self.last_vision_command = None
        self.last_text_command   = None

        self.log_wait_for_next_command()





def run_ground():

    log_version()
    create_output_folder()

    if check_models() is False:
        if is_intel() is False:
            #logging.info('EXIT')
            #exit(0)
            None
    else:
        warmup()

    SoundPlayerManager().start()
    time.sleep(0.1)

    mainGround = MainGround()
    mainGround.flask_groundthread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=app_settings.general.ground_port, use_reloader=False),
        daemon=True,
    )
    mainGround.flask_groundthread.start()
    if app_settings.general.wait_for_first_air_message:
        logging.info('Waiting for first message from AIR, before continue')
        mainGround.status_received_event.wait()
        logging.info('Got first message from AIR, continue')
    else:
        logging.info("I'm not waiting for first message from AIR")

    mainGround.run_tts("Startup finished")
    return mainGround




if __name__ == "__main__":
    log_version()
    log_app_settings()
    mainGround = run_ground()
    mainGround.start_ground()
    mainGround.flask_groundthread.join()
    mainGround.audio_thread.join()

    #time.sleep(10)
    #logging.info('finished')
