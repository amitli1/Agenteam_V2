import time

from project_code.utils.utils import get_running_ip
import websockets
import logging
import threading
import asyncio
import json
import requests
import math

class QuadManager:
    def __init__(self, quad_port):
        self.quad_port = quad_port
        self.target_ip = get_running_ip()
        self.quad_url  = f"ws://{self.target_ip}:{self.quad_port}/ws/drone-status"

        self._thread = threading.Thread(
            target=self._run_status_loop,
            daemon=True,  # thread dies when main program exits
        )
        self._thread.start()
        self.last_status_data = None
        self.quad_manager_ready = threading.Event()

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
                timeout=10,
            )
            status_code = r.status_code
            logging.info(f"Status code: {status_code}")
            return status_code
        except Exception as e:
            logging.exception(f"[quad_api_return] Failed calling /return: {e}")
            return 500

    def is_mission_finished(self):
        return self.last_status_data['mission_finished']


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
                return False
        except Exception as e:
            logging.exception(f"Failed to fly to wp: {e}")
            return False
        return True


    def get_current_location(self):
        lat   = self.last_status_data['lat']
        lon   = self.last_status_data['lon']
        alt   = self.last_status_data['alt']
        yaw   = self.last_status_data['yaw']
        return {'lat': lat, 'lon': lon, 'alt': alt, 'yaw': yaw}

    def get_last_quad_message(self):
        return self.last_status_data

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
                                logging.info(f'Got first quad message: {message}')

                            flag_first_msg         = True

                            self.last_status_data = json.loads(message)
                            self.quad_manager_ready.set()

                            # lat                   = status_data['lat']
                            # lon                   = status_data['lon']
                            # alt                   = status_data['alt']
                            # yaw                   = status_data['yaw']
                            in_air                = self.last_status_data['in_air']
                            flight_mode           = self.last_status_data['flight_mode']
                            is_armed              = self.last_status_data['is_armed']
                            is_mission_finished   = self.last_status_data['is_mission_finished']
                            mission_progress      = self.last_status_data['mission_progress']
                            last_mission_waypoint = self.last_status_data['last_mission_waypoint']
                            print(f"in_air = {in_air}, flight_mode = {flight_mode}, is_armed = {is_armed}, is_mission_finished = {is_mission_finished}, mission_progress = {mission_progress}, last_mission_waypoint = {last_mission_waypoint}")
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
    quadManager = QuadManager(8001)
    quadManager.quad_manager_ready.wait()

    testerUtils = TesterUtils()


    print(f'Get current location')
    current = quadManager.get_current_location()

    total_dist_m = 150
    climb_m = 20

    horizontal_m = math.sqrt(total_dist_m ** 2 - climb_m ** 2)  # ~45.83 m

    wp = testerUtils.offset_wp(current['lat'], current['lon'], current['alt'] + climb_m,
                               distance_m=horizontal_m, bearing_deg=0)

    print(f'Fly to wp: {wp}')
    # quadManager.fly_to_wp([wp])

    current = quadManager.get_current_location()

    print(f'Get current location')
    l_wp = testerUtils.get_square_points(current, radius=15)

    print(f"\tStatus: {quadManager.get_last_quad_message()}")
    print(f'Fly to square: {l_wp}')
    quadManager.fly_to_wp(l_wp)
    print(f"\tStatus: {quadManager.get_last_quad_message()}")
    print('finished')

    quadManager._thread.join()
    print("Finished")
    time.sleep(60)

    # in_air = True, flight_mode = MISSION, is_armed = True, is_mission_finished = False, mission_progress = 0/1, last_mission_waypoint = {'lat': 47.64189659982582, 'lon': -122.139558583092, 'alt': 19.994001388549805, 'yaw': None}
    # in_air = True, flight_mode = HOLD, is_armed = True, is_mission_finished = True, mission_progress = 1/1, last_mission_waypoint = {'lat': 47.64279595161966, 'lon': -122.13955819999998, 'alt': 40.025001525878906, 'yaw': None}


if __name__ == "__main__":

    # {'timestamp': 1784451253894, 'is_armed': False, 'flight_mode': 'HOLD', 'lat': 47.6414678, 'lon': -122.14016489999999, 'alt': -0.012000000104308128, 'yaw': 187.4424285888672, 'horizontal_velocity': 0.0, 'vertical_velocity': 0.0, 'battery_voltage': 16.200000762939453, 'in_air': False, 'is_mission_finished': True, 'mission_progress': '0/0', 'last_mission_estimated_time': 'No mission yet', 'last_mission_waypoint': None}
    #simple_get_status_test()
    simple_flight_test()

# No mistion:
# 'flight_mode': 'HOLD'
# 'is_mission_finished': True
# 'mission_progress': '0/0'

