import json

from project_code.air.quad_manager import QuadManager
from project_code.db.database_manager import DatabaseManager
import requests
import logging
from project_code.utils.utils import get_running_ip
import threading
import queue

class MonitorCollector:
    def __init__(self):
        # FIFO queue for discrete messages (order + delivery matters)
        self._msg_queue = queue.Queue()
        threading.Thread(target=self._process_msg_queue, daemon=True).start()

        # Latest-value slot for high-frequency telemetry (only newest matters)
        self._status_lock   = threading.Lock()
        self._status_cond   = threading.Condition(self._status_lock)
        self._latest_status = None  # (url, json_data)
        threading.Thread(target=self._process_status, daemon=True).start()

    def start(self):

        self._clear_monitor()

        databaseManager = DatabaseManager()
        df              = databaseManager.get_db()
        try:
            response = requests.post(f"http://{get_running_ip()}:7031/get_dataset/", json=df.to_dict())
            if response.status_code != 200:
                logging.error(f'Error while sending data to Monitor (get_dataset): {response.status_code}')
                return False
        except Exception as e:
            logging.error(f'Error while sending data to Monitor (get_dataset): {e}')
            return False
        return True

    def _clear_monitor(self):
        try:
            response = requests.post("http://localhost:7031/clear")
            if response.status_code != 200:
                logging.error(f'Error while sending clear to Monitor: {response.status_code}')
        except Exception as e:
            logging.error(f"Error while sending clear to Monitor: {e}")


    # ---------- FIFO worker (user_command / text_to_user) ----------
    def _process_msg_queue(self):
        while True:
            url, json_data, label = self._msg_queue.get()
            self._safe_post(url, json_data, label)
            self._msg_queue.task_done()

    # ---------- Latest-wins worker (air status telemetry) ----------
    def _process_status(self):
        while True:
            with self._status_cond:
                while self._latest_status is None:
                    self._status_cond.wait()
                url, json_data = self._latest_status
                self._latest_status = None
            self._safe_post(url, json_data, "update_air_status_msg")

    def _safe_post(self, url, json_data, label):
        try:
            response = requests.post(url, json=json_data, timeout=5)
            if response.status_code != 200:
                logging.error(f'Error while sending data to Monitor ({label}): {response.status_code}')
        except Exception as e:
            logging.error(f'Error while sending data to Monitor ({label}): {e}')

    # ---------- Public API (unchanged signatures, non-blocking) ----------
    def update_user_command(self, drone_role, user_command):
        msg = {"drone_role": drone_role, "text": user_command}
        self._msg_queue.put((f"http://{get_running_ip()}:7031/user_command/", msg, "user_command"))
        return True

    def update_text_to_user(self, drone_role, text_to_user):
        msg = {"drone_role": drone_role, "text": text_to_user}
        self._msg_queue.put((f"http://{get_running_ip()}:7031/text_to_user/", msg, "text_to_user"))
        return True

    def update_air_status_msg(self, air_status_msg):
        try:
            quad_data = json.loads(air_status_msg['last_quad_msg'])
        except Exception as e:
            logging.error(f'Error parsing last_quad_msg: {e}')
            return False

        role = air_status_msg.get('drone_role')
        if role == 'master':
            endpoint = 'get_master_status'
        elif role == 'slave':
            endpoint = 'get_slave_status'
        else:
            logging.error(f"Got unknown drone_role: {role}")
            return False

        url = f"http://{get_running_ip()}:7031/{endpoint}/"
        with self._status_cond:
            self._latest_status = (url, quad_data)
            self._status_cond.notify()
        return True

if __name__ == "__main__":
    monitor_collector = MonitorCollector()
    monitor_collector.start()

    quadManager = QuadManager(8001, None)
    l_wp = [[47.640141, -122.1415707, 20.0],
            [47.640141, -122.1415707, 20.0],
            [47.640141, -122.1409465, 20.0],
            [47.6397875, -122.1409465, 20.0],
            [47.6397875, -122.1415707, 20.0],
            [47.640141, -122.1415707, 20.0]]
    res = quadManager.fly_to_wp(l_wp)
    if res != True:
        print(f'Error while sending fly_to_wp')


