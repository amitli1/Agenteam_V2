import os
import threading
import time

from flask import Flask

from project_code.air.main_air import MainAir
from project_code.app_config.settings import app_settings
from project_code.ground.mainGround import MainGround, run_ground
from project_code.utils.logger_utils import init_logger, CURRENT_DATE
from project_code.utils.sound_player import SoundPlayerManager
from project_code.utils.utils import create_output_folder
import logging

app                 = Flask(__name__)



def run_air():
    mainAir = MainAir()
    air_thread = threading.Thread(target=mainAir.start_air, daemon=True)
    air_thread.start()


class FullSystemTest():

    def __init__(self, mainGround):
        self.wait_for_text = ""
        self.text_from_air = ""
        self.mainGround    = mainGround
        self.wait_event    = threading.Event()

    def check_errors_in_log(self):
        log_file_path = f"{app_settings.logging_and_records.output_path}/log_{CURRENT_DATE}.txt"
        with open(log_file_path, 'r') as log_file:
            log_contents = log_file.read()
            if "ERROR" in log_contents:
                logging.error(f"❌ Errors found in the log file ❌ (log: {os.path.basename(log_file_path)})")
                return False
            else:
                logging.info(f"✅ No errors found in the log file ✅ (log: {os.path.basename(log_file_path)})")
                return True

    def wait_for_text_from_air(self, text_to_user):
        self.text_from_air = text_to_user
        self.wait_event.set()



    def check_if_step_finished_successfully(self, text_to_wait):

        start_time = time.time()
        while True:
            if self.wait_event.wait(timeout=90) is False:
                if text_to_wait != '':
                    logging.error("❌ (1) Timeout waiting for text from air ❌")
                return False

            if text_to_wait == self.text_from_air:
                break

            if (time.time() - start_time) > 90:
                logging.error("❌ (2) Timeout waiting for text from air ❌")
                return False

        return True


    def test_1(self):

        self.mainGround.handle_user_text("Hey buddy go to building number one")
        if self.check_if_step_finished_successfully('I have reached the destination.') is False:
            return False

        mainGround.handle_user_text("Hey buddy point to the car or weapons")

        mainGround.handle_user_text("buddy, surround the building and tell me what you see")
        if self.check_if_step_finished_successfully('what should I look for ?') is True:

            mainGround.handle_user_text("buddy, look for people and weapons")

            if self.check_if_step_finished_successfully('I have reached the destination.') is False:
                return False

            mainGround.handle_user_text("buddy, describe")

            mainGround.handle_user_text("buddy, return home")

            result = self.check_errors_in_log()
        else:

            result = False


        logging.info( "✅ ✅ ✅ ✅ ✅ ✅ ✅ ✅ ")
        logging.info(f"✅ Logs: {result} ✅ ")
        logging.info( "✅ TEST FINISHED  ✅ ")
        logging.info( "✅ ✅ ✅ ✅ ✅ ✅ ✅ ✅ ")
        return result

    def test_team(self):
        self.mainGround.handle_user_text("Hey team go to building number one")
        if self.check_if_step_finished_successfully('I have reached the destination.') is False:
            return False
        mainGround.handle_user_text("team, return home")
        result = self.check_errors_in_log()

        logging.info("✅ ✅ ✅ ✅ ✅ ✅ ✅ ✅ ")
        logging.info(f"✅ Logs: {result} ✅ ")
        logging.info("✅ TEST FINISHED  ✅ ")
        logging.info("✅ ✅ ✅ ✅ ✅ ✅ ✅ ✅ ")

    def test_fly_to_the_moon(self):
        self.mainGround.handle_user_text("Hey jarvis fly to the moon")
        time.sleep(30)


if __name__ == "__main__":


    #run_air()
    mainGround = run_ground()
    fullSystemTest = FullSystemTest(mainGround)
    mainGround.set_fnc_test_callback(fullSystemTest.wait_for_text_from_air)
    #result = fullSystemTest.test_1()
    #result = fullSystemTest.test_team()
    result = fullSystemTest.test_fly_to_the_moon()
    logging.info(f'\nResult: {result}')