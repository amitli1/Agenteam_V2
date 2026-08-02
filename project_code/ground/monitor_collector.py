import json

from project_code.air.quad_manager import QuadManager
from project_code.db.database_manager import DatabaseManager
import requests
import logging
from project_code.utils.utils import get_running_ip


class MonitorCollector:
    def __init__(self):
        None

    def start(self):
        databaseManager = DatabaseManager()
        df = databaseManager.get_db()
        response = requests.post(f"http://{get_running_ip()}:7031/get_dataset/", json=df.to_dict())
        if response.status_code != 200:
            logging.error(f'Error while sending data to Monitor (get_dataset): {response.status_code}')
            return False
        return True

    def update_air_status_msg(self, air_status_msg):


        quad_data = json.loads(air_status_msg['last_quad_msg'])

        drone_location = {'lat': quad_data['lat'],
                          'lon': quad_data['lon'],
                          'alt': quad_data['alt']}

        if air_status_msg['drone_role'] == 'master':
            response = requests.post(f"http://{get_running_ip()}:7031/get_master_status/", json=drone_location)
        elif air_status_msg['drone_role'] == 'slave':
            response = requests.post(f"http://{get_running_ip()}:7031/get_slave_status/", json=drone_location)
        else:
            logging.error(f"Got unkown drone_role: {air_status_msg['drone_role']}")
            return False

        if response.status_code != 200:
            logging.error(f'Error while sending data to Monitor (update_air_status_msg): {response.status_code}')
            return False
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


