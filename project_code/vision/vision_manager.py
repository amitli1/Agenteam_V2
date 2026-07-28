from project_code.app_config.settings import app_settings
import logging
import time
import requests
import threading
from project_code.utils.utils import get_running_ip
import json

class VisionManager(object):

    def __init__(self):
        self.is_online = app_settings.vision.use_online
        self.summary_port = app_settings.vision.summary_port
        self.hold_port    = app_settings.vision.hold_port
        self.point_port   = app_settings.vision.point_port

        # start point thread
        self.point_status_thread = threading.Thread(
            target=self.receive_vision_point_status,
            daemon=True
        )
        self.point_status_thread.start()

        # start hold thread
        self.hold_status_thread = threading.Thread(
            target=self.receive_vision_hold_status,
            daemon=True
        )
        self.hold_status_thread.start()

        # start summary thread
        self.summary_status_thread = threading.Thread(
            target=self.receive_vision_summary_status,
            daemon=True
        )
        self.summary_status_thread.start()

    def open_video_window(self):

        if self.is_online is False:
            return
        try:
            stop_url = f"http://{get_running_ip()}:{app_settings.vision.point_port}/api/pointing-agent/stop"
            logging.info(f'Send pointing-agent/stop (to: {stop_url})')
            r = requests.post(stop_url, json={})
            r.raise_for_status()
            r = r.json()
        except Exception as e:
            #logging.error(f'\nError sending request for pointing-agent/stop, res:\n {e}\n')
            return False

        try:
            with open("pointing_settings.json", "r") as f:
                payload_img = json.load(f)

            r = requests.post(f"http://{get_running_ip()}:{app_settings.vision.point_port}/api/pointing-agent/start", json=payload_img)
            r.raise_for_status()
            res = r.json()
            success = res['success']
            logging.info(f'------------------------------------------------------------')
            logging.info(f'Send request for process-video (open windows), res: {success}')
            logging.info(f'------------------------------------------------------------')
            return success
        except Exception as e:
            logging.error(f'Error sending request for process-video: {e}')


    def handle_point_status(self, data, last_is_active, last_agent_status):
        if 'session' in data:
            if 'is_active' in data['session']:
                current_is_active = data['session']['is_active']
                if current_is_active != last_is_active:
                    logging.info(f'Point is_active change from: {last_is_active} to: {current_is_active}')
                last_is_active = current_is_active

        if 'agent' in data:
            if 'status' in data['agent']:
                current_agent_staus = data['agent']['status']

                if current_agent_staus == "locked":
                    None

                if current_agent_staus != last_agent_status:
                    point_status = f'Point agent status change from: {last_agent_status} to: {current_agent_staus}'
                    logging.info(point_status)
                last_agent_status = current_agent_staus

        return last_is_active, last_agent_status


    def receive_vision_point_status(self):
        if self.is_online is False:
            return

        logging.info('Start listing for pointing status')
        got_status_msg    = False
        send_video_window = False
        last_is_active    = None
        last_agent_status = None

        while True:

            time.sleep(0.1)  # 100ms

            if send_video_window is False:
                send_video_window = self.open_video_window()

            try:
                r = requests.get(f"http://{get_running_ip()}:{self.point_port}/api/pointing-agent/status", json={})
                r.raise_for_status()
                data = r.json()
                last_is_active, last_agent_status = self.handle_point_status(data, last_is_active, last_agent_status)

                if got_status_msg is False:
                    logging.info(f"Got pointing status message")
                got_status_msg = True
            except Exception as e:
                if got_status_msg is True:
                    logging.error(f"Error in receiving point status: {e}")
                got_status_msg = False


    def handle_vision_hold_status(self, hold_status):
        if len(hold_status) != 0:
            # 1. check we are master
            # 2. check we are in team mission
            # 3. send to slave
            # if config_mp.is_in_hold_state.value and (len(hold_status['msg']) > 0):
            #     hold_msg = f'Hold status: {hold_status}'
            #     logging.info(hold_msg)
            None

    def receive_vision_hold_status(self):
        if self.is_online is False:
            return

        logging.info('Start listing for hold status')
        got_status_msg    = False

        while True:

            time.sleep(0.1)  # 100ms

            try:
                r = requests.get(f"http://{get_running_ip()}:{self.hold_port}/alert-get", json={})
                r.raise_for_status()
                data = r.json()
                self.handle_vision_hold_status(data)

                if got_status_msg is False:
                    logging.info(f"Got hold status message")
                got_status_msg = True
            except Exception as e:
                if got_status_msg is True:
                    logging.error(f"Error in receiving hold status: {e}")
                got_status_msg = False

    def receive_vision_summary_status(self):

        if self.is_online is False:
            return

        logging.info('Start listing for summery status')
        got_status_msg = False

        while True:

            time.sleep(1)

            try:
                r = requests.get(f"http://{get_running_ip()}:{self.summary_port}/status", json={})
                r.raise_for_status()
                data = r.json()
                if got_status_msg is False:
                    logging.info(f"Got summary status message")
                got_status_msg = True
            except Exception as e:
                if got_status_msg is True:
                    logging.error(f"Error in summary hold status: {e}")
                got_status_msg = False

    def start_point(self, text):
        if self.is_online is False:
            return None

        try:

            payload_video = {
                "prompt": text,
            }
            req_path = f"http://{get_running_ip()}:{self.point_port}/api/agent/set-lock-request"
            logging.info(f'Send point request to: {req_path}')
            r = requests.post(req_path, json=payload_video)
            r.raise_for_status()
            res = r.json()
            logging.info(f'Send: {req_path} With: {payload_video}')
        except Exception as e:
            logging.info(f'Failed to send point message (set-lock-request), error:\n{e}\n')
            res = {"status": "failed", "msg": f"Cant point"}

        return res

    def stop_point(self):
        if self.is_online is False:
            return None

        try:
            payload_video = {
                "": "",
            }
            req_path = f"http://{get_running_ip()}:{self.point_port}/api/pointing-agent/stop"
            logging.info(f'Send stop point request to: {req_path}')
            r = requests.post(req_path, json=payload_video)
            r.raise_for_status()
            res = r.json()
            logging.info(f'Send: {req_path} With: {payload_video}')
        except Exception as e:
            logging.error(f'Error while sending stop point request: {e}')
            res = None
        return res

    def start_hold(self, text):
        if self.is_online is False:
            return None

        if self.is_online is False:
            return None


        description = "hold vehicles or persons or weapons"
        logging.info(f'Change hold description to hardcoded: {description}')

        try:
            logging.info(f'Send start hold message, description: {description}')
            payload = {"task": "hold", "description": description}
            r = requests.post(f"http://{get_running_ip()}:{self.hold_port}/alert-start", json=payload)
            r.raise_for_status()
            res = r.json()
        except Exception as e:
            logging.info(f'Failed to send alert-start (start hold), error:\n{e}\n')
            res = None

        return res

    def stop_hold(self, text):
        if self.is_online is False:
            return None

        try:
            logging.info(f'Send stop hold message')
            payload = {"task": "stop_hold"}
            r = requests.post(f"http://{get_running_ip()}:{self.hold_port}/alert-stop", json=payload)
            r.raise_for_status()
            res = r.json()

        except Exception as e:
            logging.error(f'Error while sending stop hold(alert-stop) message: {e}')
            res = None
        return res

    def call_summary_to_get_ready(self):

        if self.is_online is False:
            return True

        try:
            payload = {"task": "get_ready"}
            url = f"http://{get_running_ip()}:{self.summary_port}/get_ready"
            logging.info(f'Send message to: {url} with: {payload}')
            r = requests.post(url, json=payload)
            r.raise_for_status()
            res = r.json()
            logging.info(f'Get ready response: {res}')
            if res['status'] == 'ready':
                res = True
            else:
                res = False
        except Exception as e:
            logging.error(f'Error while sending get_ready message: {e}')
            res = False
        return res

    def start_summary(self, objects_to_focus):
        if self.is_online is False:
            return None

        try:
            payload = {"task": "start_summarizing",
                       "objects_to_focus": objects_to_focus}

            url = f"http://{get_running_ip()}:{self.summary_port}/start_sum"
            logging.info(f'Send message to: {url} with: {payload}')
            r = requests.post(url, json=payload)
            r.raise_for_status()
            res = r.json()
            logging.info(f'Start summary response: {res}')
        except Exception as e:
            logging.error(f'Error while sending start_summarizing message: {e}')
            res = None
        return res

    def stop_summary(self):
        if not self.use_online:
            return

        try:
            payload = {"task": "stop_summarizing"}
            url = f"http://{get_running_ip()}:{app_settings.vision.summary_port}/stop_sum"
            logging.info(f'Send message to: {url} with: {payload}')
            r = requests.post(url, json=payload)
            r.raise_for_status()
            res = r.json()
        except Exception as e:
            logging.error(f'Error sending stop_summarizing: {e}')
            res = ""

        logging.info(f'Got stop_summarizing message: {res}')
        return res

    def describe_summerization(self, text):

        if self.is_online is False:
            return

        try:
            start_time = time.time()
            payload = {"task": "describe", "transcription": text}
            url = f"http://{get_running_ip()}:{self.summary_port}/describe"
            logging.info(f'Send message to: {url} with: {payload}')
            r = requests.post(url, json=payload)
            r.raise_for_status()
            res = r.json()
            end_time = time.time()
            logging.info(f'describe took: {(end_time - start_time):.2f} sec')
        except Exception as e:
            logging.error(f'Error while sending describe message: {e}')
            res = None
        return res







if __name__ == "__main__":
    vision_manager = VisionManager()
    vision_manager.point_status_thread.join()


