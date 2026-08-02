import time

from project_code.air.air_share_fields import quad_last_status_data, quad_isMissionInProgress, \
    quad_last_status_data_lock
from project_code.app_config.settings import app_settings
from project_code.utils.utils import get_running_ip
import websockets
import logging
import threading
import asyncio
import json
import requests
import math

class QuadManager:
    def __init__(self, quad_port, fnc_send_text_to_user):
        self.fnc_send_text_to_user = fnc_send_text_to_user
        self.quad_port             = quad_port
        self.target_ip             = get_running_ip()

        self.quad_url  = f"ws://{self.target_ip}:{self.quad_port}/ws/drone-status"
        self._thread   = threading.Thread(
            target=self._run_status_loop,
            daemon=True,  # thread dies when main program exits
        )
        self._thread.start()

    def _run_status_loop(self):
        # each thread needs its own event loop to run async code
        asyncio.run(self.receive_drone_status())

    def call_back_home(self):
        try:
            url = f"http://{self.target_ip}:{self.quad_port}/return"
            r = requests.post(
                url,
                json=None,
                headers={"accept": "application/json", "content-type": "application/json"},
                timeout=5,
            )
            status_code = r.status_code
            logging.info(f"Status code: {status_code}")
            return status_code
        except Exception as e:
            logging.exception(f"[quad_api_return] Failed calling /return: {e}")
            return 500

    def fly_to_wp(self, l_wp):

        # [{'lat, 'lon', 'alt}]
        url = f"http://{self.target_ip}:{self.quad_port}/mission"
        try:
            r = requests.post(
                url,
                json=l_wp,
                headers={"accept": "application/json", "content-type": "application/json"},
                timeout=10,  # a bit more than 5 helps when mavsdk is slow
            )
            if r.status_code != 200:
                logging.error(f"Failed to fly to wp, status code: {r.status_code}")
                quad_isMissionInProgress.clear()
                return False
        except Exception as e:
            logging.exception(f"Failed to fly to wp: {e}")
            quad_isMissionInProgress.clear()
            return False

        quad_isMissionInProgress.set()
        return True


    def check_mission_progress(self, flight_mode, is_mission_finished, mission_progress):

        if quad_last_status_data is None:
            return

        is_in_progress = quad_isMissionInProgress.is_set()
        text_to_user = None
        if is_in_progress:
            current, total = map(int, mission_progress.split("/"))
            if (total != 0) and (current == total):
                text_to_user = "I have reached the destination."
                quad_isMissionInProgress.clear()
                self.send_get_to_destination_to_user()

            else:
                with quad_last_status_data_lock:
                    if mission_progress != quad_last_status_data.get('mission_progress'):
                        text_to_user = "Hold on, still flying"


        if text_to_user is not None:
            if self.fnc_send_text_to_user:
                self.fnc_send_text_to_user(text_to_user)


    def send_get_to_destination_to_user(self):
        address = f"http://{app_settings.general.ground_ip}:{app_settings.general.ground_port}/get_to_destination"
        drone_role = "Master" if app_settings.general.run_as_master else "Slave"
        response = requests.post(f"{address}", json={"drone_role": drone_role})
        logging.info(f"Send get_to_destination message to ground, response: {response.status_code}")

    async def receive_drone_status(self):


        flag_connection_opened = False
        flag_first_msg         = False

        while True:
            try:
                async with websockets.connect(self.quad_url) as websocket:
                    while True:
                        try:
                            flag_connection_opened = True
                            message                = await websocket.recv()

                            if flag_first_msg is False:
                                if self.fnc_send_text_to_user:
                                    self.fnc_send_text_to_user('Start getting drone status')
                                    logging.info(f'Got first quad message: {message}')

                            flag_first_msg         = True

                            current_status_data = json.loads(message)

                            # lat                   = current_status_data['lat']
                            # lon                   = current_status_data['lon']
                            # alt                   = current_status_data['alt']
                            # yaw                   = current_status_data['yaw']
                            in_air                = current_status_data['in_air']
                            flight_mode           = current_status_data['flight_mode']
                            is_armed              = current_status_data['is_armed']
                            is_mission_finished   = current_status_data['is_mission_finished']
                            mission_progress      = current_status_data['mission_progress']
                            last_mission_waypoint = current_status_data['last_mission_waypoint']
                            #print(json.loads(message))
                            self.check_mission_progress(flight_mode, is_mission_finished, mission_progress)

                            # save last msg
                            with quad_last_status_data_lock:
                                quad_last_status_data.update(json.loads(message))


                        except Exception as e:
                            logging.error(f'Error while receiving message: {e}')

            except Exception as e:
                if flag_connection_opened:
                    logging.info(f'Cant connect to: {e}')
                flag_connection_opened = False



class TesterUtils:
    def __init__(self):
        None

    def offset_wp(self, lat, lon, alt, distance_m, bearing_deg):
        """Return a new {lat, lon, alt} that is `distance_m` meters away
        from (lat, lon) along `bearing_deg` (0 = north, 90 = east)."""
        R = 6371000.0  # Earth radius in meters

        lat_rad     = math.radians(lat)
        lon_rad     = math.radians(lon)
        bearing_rad = math.radians(bearing_deg)
        ang_dist    = distance_m / R

        new_lat_rad = math.asin(
            math.sin(lat_rad) * math.cos(ang_dist)
            + math.cos(lat_rad) * math.sin(ang_dist) * math.cos(bearing_rad)
        )
        new_lon_rad = lon_rad + math.atan2(
            math.sin(bearing_rad) * math.sin(ang_dist) * math.cos(lat_rad),
            math.cos(ang_dist) - math.sin(lat_rad) * math.sin(new_lat_rad),
        )

        return {
            'lat': math.degrees(new_lat_rad),
            'lon': math.degrees(new_lon_rad),
            'alt': alt,
        }

    def get_square_points(self, start_point, radius=10):
        lat = start_point['lat']
        lon = start_point['lon']
        alt = start_point['alt']

        # first corner is the start point itself
        corners = [{'lat': lat, 'lon': lon, 'alt': alt}]

        # walk N, then E, then S to reach the other 3 corners
        bearings = [0, 90, 180]  # north, east, south
        current = corners[0]
        for bearing in bearings:
            current = self.offset_wp(current['lat'], current['lon'], current['alt'],
                                distance_m=radius, bearing_deg=bearing)
            corners.append(current)

        return corners


def simple_get_status_test():
    quadManager = QuadManager(8001)
    quadManager.quad_manager_ready.wait()
    current = quadManager.get_last_quad_message()
    print(current)


def simple_flight_test():
    quadManager = QuadManager(8011, None)
    #quadManager.quad_manager_ready.wait()
    #time.sleep(3)
    testerUtils = TesterUtils()

    while True:
        currentStatusData = quad_last_status_data
        time.sleep(1)
        if currentStatusData:
            break

    total_dist_m = 200
    climb_m = 30

    horizontal_m = math.sqrt(total_dist_m ** 2 - climb_m ** 2)  # ~45.83 m

    wp = testerUtils.offset_wp(currentStatusData['lat'], currentStatusData['lon'], currentStatusData['alt'] + climb_m,
                               distance_m=horizontal_m, bearing_deg=0)


    print(f'Fly to wp: {wp}')
    quadManager.fly_to_wp([wp])

    time.sleep(3)
    l_wp = testerUtils.get_square_points(currentStatusData, radius=15)


    quadManager.fly_to_wp(l_wp)
    time.sleep(3)

    print("Finished")


    # in_air = True, flight_mode = MISSION, is_armed = True, is_mission_finished = False, mission_progress = 0/1, last_mission_waypoint = {'lat': 47.64189659982582, 'lon': -122.139558583092, 'alt': 19.994001388549805, 'yaw': None}
    # in_air = True, flight_mode = HOLD, is_armed = True, is_mission_finished = True, mission_progress = 1/1, last_mission_waypoint = {'lat': 47.64279595161966, 'lon': -122.13955819999998, 'alt': 40.025001525878906, 'yaw': None}


def simple_fly_to_wp():
        l_wp = [(47.64146699947751, -122.13956425421526, 0.0), (47.640141, -122.1415707, 20.0)]
        url = f"http://127.0.0.1:8001/mission"
        try:
            r = requests.post(
                url,
                json=l_wp,
                headers={"accept": "application/json", "content-type": "application/json"},
                timeout=10,  # a bit more than 5 helps when mavsdk is slow
            )
            if r.status_code != 200:
                print(f"Failed to fly to wp, status code: {r.status_code}")
                return False
        except Exception as e:
            print(f"Failed to fly to wp: {e}")
            return False

        print("OK")
        return True

if __name__ == "__main__":

    # {'timestamp': 1784451253894, 'is_armed': False, 'flight_mode': 'HOLD', 'lat': 47.6414678, 'lon': -122.14016489999999, 'alt': -0.012000000104308128, 'yaw': 187.4424285888672, 'horizontal_velocity': 0.0, 'vertical_velocity': 0.0, 'battery_voltage': 16.200000762939453, 'in_air': False, 'is_mission_finished': True, 'mission_progress': '0/0', 'last_mission_estimated_time': 'No mission yet', 'last_mission_waypoint': None}
    #simple_get_status_test()
    simple_flight_test()
    #simple_fly_to_wp()

# No mistion:
# 'flight_mode': 'HOLD'
# 'is_mission_finished': True
# 'mission_progress': '0/0'

#
# px4 - drone controller (first time only, saved after restart)
# cd ~/Lin_all
# # # http:/ks.suxNoEditor
# ./Block ./runh -windowed -ResX=640 -ResY=480 -scalability=1 -t.MaxFPS=30
# # cd ~/QuadAPI_airsim
# # sud127.0.0.1:8001/docs
# qground - drone controller (remote control)
# air sim - simulation
# run_all - quad api


