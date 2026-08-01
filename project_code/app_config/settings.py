from typing import Dict
from pydantic import BaseModel
import yaml

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

# amitli
def load_config(path: str = "app_config/conf.yaml") -> Settings:
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return Settings(**data)

app_settings = load_config()
