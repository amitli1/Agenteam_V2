import logging
import os
from datetime import datetime
from project_code.app_config.settings import app_settings



def get_timestamp_string():
    return datetime.now().strftime("%d_%m_%Y_%H_%M_%S")


CURRENT_DATE = get_timestamp_string()

def init_logger(jetson_type):

    prefix = ""
    if jetson_type == "ground":
        prefix = "ground_"
    elif jetson_type == "air":
        drone_role = "Master" if app_settings.general.run_as_master else "Slave"
        prefix = f"air_{drone_role}_"
    else:
        prefix = f"log_"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(   '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s',
                                     datefmt='%Y-%m-%d %H:%M:%S')

    # # File handler
    #os.makedirs("logs", exist_ok=True)
    log_name     = f"{app_settings.logging_and_records.output_path}/{prefix}{CURRENT_DATE}.txt"
    file_handler = logging.FileHandler(log_name)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)