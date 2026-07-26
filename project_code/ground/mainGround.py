import json

from project_code.air.main_air import MainAir
from project_code.app_config.settings import app_settings
from project_code.audio.audio_pipeline import AudioPipeline
from project_code.db.database_manager import DatabaseManager
from project_code.llm.drone_navigation_agent import DroneNavigationAgent
from project_code.llm.llm_command_parser import LlmCommandParser
from project_code.llm.llm_mission_planner import MissionPlannerAgent
from project_code.utils.logger_utils import init_logger
from project_code.utils.utils import create_output_folder, check_models, warmup
import logging
import threading
import multiprocessing
import time

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

        self.last_quad_data = None
        app.add_url_rule("/status",view_func=self.on_air_status_message,methods=["POST"],)
        app.add_url_rule("/text_to_user", view_func=self.on_air_text_to_user, methods=["POST"], )

        self.master_drone_location = None
        self.slave_drone_location = None

    def on_air_status_message(self):
        last_quad_data      = request.get_json(silent=True)
        self.last_quad_data = last_quad_data
        logging.info(f'Got air quad msg: {last_quad_data}')

        self.master_drone_location = {'lat': self.last_quad_data['lat'],
                                    'lon': self.last_quad_data['lon'],
                                    'alt': self.last_quad_data['alt'],
                                    'yaw': self.last_quad_data['yaw']}

        return "OK", 200

    def on_air_text_to_user(self):
        text_to_user = request.get_json(silent=True)
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
            if command['fly_command'] != '':
                result = self.llmMissionPlanner.get_way_points(text_command=command['fly_command'],
                                                      team_member=command['team_member'],
                                                      master_drone_location=self.master_drone_location,
                                                      slave_drone_location=self.slave_drone_location,
                                                      database_manager=self.databaseManager,
                                                      ALT_DEFAULT=app_settings.flightPath.default_drone_altitude,
                                                      SPATIAL_DISTANCE=app_settings.flightPath.spatial_distance,
                                                      DELTA_ALT_SLAVE_DRONE=app_settings.flightPath.slave_drone_altitude_offset)

                print(json.dumps(result, indent=2))


if __name__ == "__main__":
    create_output_folder()
    if check_models() is False:
        #exit(0)
        None
    else:
        warmup()

    mainAir    = MainAir()
    air_process = multiprocessing.Process(target=mainAir.start_air, daemon=True)
    air_process.start()

    mainGround = MainGround()
    mainGround.handle_user_text("Hey jarvis go to building number one")

    # flask_groundthread = threading.Thread(
    #     target=lambda: app.run(host="0.0.0.0", port=app_settings.general.groud_port, use_reloader=False),
    #     daemon=True,
    # )
    # flask_groundthread.start()
    #
    #
    # #mainGround.start_ground()
    # mainGround.handle_user_text("Hey jarvis go to building number one")
    #
    # time.sleep(100000)