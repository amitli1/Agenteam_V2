import requests
import numpy as np
import sounddevice as sd
from project_code.utils.utils import get_running_ip


def test_tts():
    response = requests.post(f"http://{get_running_ip()}:8002/synthesize/", json={"text": "this is a test"})
    data = response.json()
    if response.status_code != 200:
        print(f"Error while sending text: {data}")

    audio = data['audio'][0]
    sr = data['sample_rate']
    audio = np.asarray(audio, dtype=np.float32)
    print("play")
    sd.play(audio, sr)
    sd.wait()
    print("OK")


if __name__ == '__main__':
    test_tts()