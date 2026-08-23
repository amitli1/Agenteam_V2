from typing import Dict
from pydantic import BaseModel
import yaml

from project_code.utils.platform_utils import is_intel


class STTConfig(BaseModel):
    model_size: str
    num_beams: int
    confidence_threshold: float
    compression_ratio_threshold: float

class VadConfig(BaseModel):
    vad_threshold: float
    vad_chunk: int
    sample_rate: int

class WakewordConfig(BaseModel):
    channels: int
    chunk: int
    sample_rate: int
    models_dir: Dict[str, str]


class AudioConfig(BaseModel):
    vad_threshold: float
    language: str
    stt: STTConfig
    vad: VadConfig
    wakeword: WakewordConfig

class TestConfig(BaseModel):
    run_in_test_mode: bool

class Monitor(BaseModel):
    monitor_port: int


class LLM(BaseModel):
    api_key: str
    base_url: str
    llm_model: str

class Logging_and_records(BaseModel):
    output_path: str

class DataBase(BaseModel):
    db_path: str
    max_area_in_meters: int
    audio_files: str

class Vision(BaseModel):
    use_online: bool
    summary_port: int
    hold_port: int
    point_port: int
    pointing_settings_file: str

class General(BaseModel):
    run_as_master: bool
    master_quad_port: int
    master_air_ip: str
    master_air_port: int
    slave_quad_port: int
    slave_air_ip: str
    slave_air_port: int
    ground_ip: str
    ground_port: int
    wait_for_first_air_message: bool

class FLightPath(BaseModel):
  default_drone_altitude: float
  spatial_distance: float
  slave_drone_altitude_offset: float

class Speakers(BaseModel):
    card: int
    device: int

class Settings(BaseModel):
    audio: AudioConfig
    test: TestConfig
    flightPath: FLightPath
    llm: LLM
    logging_and_records: Logging_and_records
    database: DataBase
    general: General
    vision: Vision
    speakers: Speakers
    monitor: Monitor



def _apply_jetson_ip_overrides(data: dict) -> dict:

    if not is_intel():
        general = data.get("general", {})
        general["ground_ip"]     = "192.168.144.113"
        general["master_air_ip"] = "192.168.144.114"
        general["slave_air_ip"]  = "192.168.144.115"

        vision = data.get("vision", {})
        vision["use_online"] = True

        data["general"]          = general
        data["vision"]           = vision
    return data

def load_config(path: str = "app_config/conf.yaml") -> Settings:
    with open(path, "r") as f:
        data = yaml.safe_load(f)

    data = _apply_jetson_ip_overrides(data)

    return Settings(**data)

def _flatten_for_log(data: dict, indent: int = 0) -> list[str]:
    lines = []
    pad = "  " * indent
    for k, v in (data or {}).items():
        if isinstance(v, dict):
            lines.append(f"{pad}{k}:")
            lines.extend(_flatten_for_log(v, indent + 1))
        elif isinstance(v, list):
            lines.append(f"{pad}{k}:")
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    lines.append(f"{pad}  [{i}]:")
                    lines.extend(_flatten_for_log(item, indent + 2))
                else:
                    lines.append(f"{pad}  [{i}] {item}")
        else:
            lines.append(f"{pad}{k}: {v}")
    return lines

def log_app_settings():
    settings_dict = app_settings.model_dump()  # pydantic v2 (use .dict() if pydantic v1)
    from project_code.utils.utils import log_boxed
    log_boxed("App Settings", _flatten_for_log(settings_dict))

app_settings = load_config()
