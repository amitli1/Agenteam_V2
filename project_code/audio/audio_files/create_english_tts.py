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
    speed_factor = 1.15
    sped_up = speedup(segment, playback_speed=speed_factor)

    sped_up.export(output_path, format="wav")
    print(f"Saved sped-up audio to {output_path}")


if __name__ == "__main__":
    # run_tts('Hold on, still flying', f'/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/hold_on_still_flying.wav')
    # run_tts('I have reached the destination',f'/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/I_have_reached_the_destination.wav')
    # run_tts('Im at building 1',f'/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/Im_at_building_1.wav')
    # run_tts('Im at building 2', f'/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/Im_at_building_2.wav')
    # run_tts('Im at junction 1', f'/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/Im_at_junction_1.wav')
    # run_tts('Im at junction 2', f'/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/Im_at_junction_2.wav')
    # run_tts('Looking around the building', f'/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/Looking_around_the_building.wav')
    # run_tts('OK,,, Flying to the destination',f'/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/OK_Flying_to_the_destination.wav')
    # run_tts('To hear more,,, say,,,  Buddy,  describe',f'/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/To_hear_more_say_Buddy_describe.wav')
    #run_tts("what should I look for ?",f'/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/What_should_I_look_for.wav')
    #run_tts("I don't understand, please repeat command.",f'/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/I_dont_understand_please_repeat_command.wav')

    #run_tts("no master drone: master drone location is not available.",f'/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/No_master_drone.wav')
    #run_tts("no slave drone: slave drone is not available.",f'/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/No_slave_drone.wav')
    run_tts("Destination not found",f'/home/amitli/repo/Agenteam_V2/project_code/audio/audio_files/Destination_not_found.wav')




