import numpy as np
import requests
from pydub import AudioSegment
from pydub.effects import speedup

def run_tts(text, output_path):
    response = requests.post(f"http://127.0.0.1:8002/synthesize/", json={"text": text})
    data = response.json()
    if response.status_code != 200:
        print(f"Error while sending text: {data}")

    audio = data['audio'][0]
    sr    = data['sample_rate']

    # Convert float samples (assumed range [-1, 1]) to 16-bit PCM
    audio_array = np.array(audio, dtype=np.float32)
    audio_int16 = (audio_array * 32767).astype(np.int16)

    segment = AudioSegment(
        audio_int16.tobytes(),
        frame_rate=sr,
        sample_width=2,  # 16-bit
        channels=1
    )

    # Apply 1.15x speed
    speed_factor = 1.01
    sped_up = speedup(segment, playback_speed=speed_factor)

    sped_up.export(output_path, format="wav")
    print(f"Saved sped-up audio to {output_path}")

if __name__ == "__main__":

    run_tts( "הגעתי ליעד", "/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/Hebrew/I_have_reached_the_destination.wav")
    run_tts( "יעד לא נמצא", "/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/Hebrew/Destination_not_found.wav")
    run_tts( "חכה רגע, אני עדיין בטיסה, ","/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/Hebrew/hold_on_still_flying.wav")
    run_tts( "אני לא מבין, בבקשה תחזור על הפקודה, ",  "/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/Hebrew/I_dont_understand_please_repeat_command.wav")
    run_tts( "אני מסתכל סביב הבניין", "/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/Hebrew/Looking_around_the_building.wav")
    run_tts( "לא קיים רחפן ראשי, ", "/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/Hebrew/No_master_drone.wav")
    run_tts( "לא קיים רחפן משני, ", "/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/Hebrew/No_slave_drone.wav")
    run_tts( "מה עלי לחפש", "/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/Hebrew/What_should_I_look_for.wav")
    run_tts("אוקי, אני בדרך ליעד, ","/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/Hebrew/OK_Flying_to_the_destination.wav")
