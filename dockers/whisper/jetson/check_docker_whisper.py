import requests
import time
import json
from  pydub import AudioSegment
import numpy as np

def test_with_api():
    file_path = "1.wav"
    with open(file_path, "rb") as f:
        files = {"file": (file_path, f, "audio/wav")}
        start_time  = time.time()
        response    = requests.post("http://0.0.0.0:8013/transcribe/", files=files)
        elapse_time = time.time() - start_time

    print(f"[{elapse_time:.2f} seconds] Response JSON: { response.json()}")

def load_file(file_name):
    audio = AudioSegment.from_file(file_name)
    samples = np.array(audio.get_array_of_samples())
    samples = samples / 32768.0
    return samples

def test_multiple_files():

    full_path = r'/home/amitli/repo/Jetson/AgenTeam/system_tests/wav_commands'
    for file_path in [rf'{full_path}/go_to_building_one.wav',
                      rf'{full_path}/surround_the_building_and_tell_what_you_see.wav',
                      rf'{full_path}/look_for_people_and_weapons.wav',
                      rf'{full_path}/describe.wav']:

        with open(file_path, "rb") as f:
            files = {"file": (file_path, f, "audio/wav")}
            start_time = time.time()
            response = requests.post("http://0.0.0.0:8013/transcribe/", files=files)
            print(f"File: {file_path}, Response: {json.loads(response.text)['transcription']}")

def test_with_audio_buffer():
    full_path = r'/mnt/nvme/repo/Agenteam_V2/dockers/whisper/jetson'
    audio_input = load_file(rf'{full_path}/1.wav')
    response = requests.post(f"http://0.0.0.0:8013/transcribe/", json={"audio_input": list(audio_input)})
    print(f"Response: {json.loads(response.text)['transcription']}")


if __name__ == "__main__":

    #simple_test()
    #test_with_api()
    #test_multiple_files()
    test_with_audio_buffer()


