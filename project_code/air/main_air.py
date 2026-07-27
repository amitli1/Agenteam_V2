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
        self.quadManager   = QuadManager(quad_port)

        # ground rest api:
        app.add_url_rule("/ground_command", view_func=self.on_ground_command, methods=["POST"], )

        # --- vision
        self.visionManager = VisionManager()

        # --- main air logic
        self._logic_thread = threading.Thread(
            target=self.main_air_logic,
            daemon=True,  # thread dies when main program exits
        )
        self._logic_thread.start()
        self.drone_role = "master" if app_settings.general.run_as_master else "slave"
        logging.info(f'Drone role: {self.drone_role}')


    def start_air(self):
        air_port = app_settings.general.master_air_port if app_settings.general.run_as_master else app_settings.general.slave_air_port
        app.run(host="0.0.0.0", port=air_port, debug=False)

    def main_air_logic(self):

        while True:
            time.sleep(1) # get message every second
            last_quad_msg = self.quadManager.get_last_quad_message()
            if last_quad_msg is None:
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

        return "OK", 200



if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,  # or DEBUG
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    mainAir = MainAir()
    mainAir.start_air()

