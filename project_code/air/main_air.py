import json

from project_code.air import air_share_fields
from project_code.air.air_share_fields import quad_last_status_data
from project_code.air.quad_manager import QuadManager
from project_code.app_config.settings import app_settings
import logging
from flask import Flask, jsonify, request
import threading
import time
import requests
from project_code.vision.vision_manager import VisionManager

app = Flask(__name__)


class MainAir:

    def __init__(self):

        # --- quad
        quad_port          = app_settings.general.master_quad_port if app_settings.general.run_as_master else app_settings.general.slave_quad_port
        self.quadManager   = QuadManager(quad_port, self.send_text_to_user)

        # ground rest api:
        app.add_url_rule("/ground_command", view_func=self.on_ground_command, methods=["POST"], )
        app.add_url_rule("/handle_message_from_master_drone", view_func=self.handle_message_from_master_drone, methods=["POST"], )


        # --- vision
        self.visionManager = VisionManager(self.on_hold_objects, self.send_text_to_user)
        self.visionManager.start_collect_vision_telemetry()

        # --- main air logic
        self._logic_thread = threading.Thread(
            target=self.main_air_logic,
            daemon=True,  # thread dies when main program exits
        )
        self._logic_thread.start()
        self.drone_role = "master" if app_settings.general.run_as_master else "slave"
        logging.info(f'Drone role: {self.drone_role}')

    def send_text_to_user(self, text_to_user):
        address    = f"http://{app_settings.general.ground_ip}:{app_settings.general.ground_port}/text_to_user"
        drone_role = "Master" if app_settings.general.run_as_master else "Slave"
        response   = requests.post(f"{address}", json={"drone_role": drone_role, "text_to_user": text_to_user})
        logging.info(f"Send text: {text_to_user} to ground, response: {response.status_code}")


    def on_hold_objects(self, hold_status):
        if app_settings.general.run_as_master:
            None

    def handle_message_from_master_drone(self):
        payload = request.get_json(silent=True)
        logging.info(f"Received request for message from master drone: {payload}")
        return "OK", 200

    def start_air(self):
        air_port = app_settings.general.master_air_port if app_settings.general.run_as_master else app_settings.general.slave_air_port
        app.run(host="0.0.0.0", port=air_port, debug=False)

    def main_air_logic(self):

        while True:
            time.sleep(1) # get message every second
            with air_share_fields.quad_last_status_data_lock:
                last_quad_msg = json.dumps(dict(quad_last_status_data))

            if last_quad_msg is None:
                continue
            if last_quad_msg == '{}':
                continue

            try:
                ground_url = f"http://{app_settings.general.ground_ip}:{app_settings.general.ground_port}/status"

                r = requests.post(ground_url, json={"drone_role": self.drone_role, "last_quad_msg": last_quad_msg})
                r.raise_for_status()

            except Exception as e:
                logging.error(f'Got exception while sending status to ground: {e}')

    def on_ground_command(self):
        data = request.get_json(silent=True)
        logging.info(f"Received request for command: {data}")

        if data['command'] == 'plan':
            plan_list = data['plan_list']
            res = self.quadManager.fly_to_wp(plan_list)
            if res is False:
                return jsonify({"error": "error while sending wp to quad manager"}), 400

        elif data['command'] == 'home':
            res = self.quadManager.call_back_home()
            if res is False:
                return jsonify({"error": "error while sending wp to quad manager"}), 400

        elif data['command'] == 'vision':
            vision_command   =  data['vision_command']['vision_command']
            objects_to_focus = data['vision_command']['objects_to_focus']
            self.visionManager.handle_vision_command(vision_command, objects_to_focus)


        return "OK", 200



if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,  # or DEBUG
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    mainAir = MainAir()
    mainAir.start_air()

