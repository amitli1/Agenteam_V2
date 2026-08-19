from faster_whisper import WhisperModel
import time

def run_whisper_service(model, file_name):

    start_time = time.time()
    segments, info = model.transcribe(
        file_name,
        language="he",
        task="translate",
        beam_size=5,
    )
    end_time = time.time()
    print(f"Time: {(end_time - start_time):.2f}s")
    for segment in segments:
        print(segment.text)


if __name__ == "__main__":

    #model_name = "ivrit-ai/whisper-large-v3-turbo-ct2"
    #model_name = "ivrit-ai/whisper-large-v3-ct2"
    #model_name = "large-v3"
    #model_name = "large-v3-turbo"
    model_name = "faster-whisper-large-v3"

    model = WhisperModel(
        model_name,
        device="cuda",
        compute_type="float16"
    )
    print(f"Model: {model_name}")
    print(f"---------------------")

    run_whisper_service(model, "/home/amitli/repo/Hebrew/Files/out_1.wav")
    run_whisper_service(model, "/home/amitli/repo/Hebrew/Files/out_2.wav")

    print(f"---------------------")
    run_whisper_service(model, "/home/amitli/repo/Hebrew/Files/out_1.wav")
    run_whisper_service(model, "/home/amitli/repo/Hebrew/Files/out_2.wav")

    #           translate        transcribe
    # large:    0.04/0.03  (x)
    # turbo:    0.04       (x)
    # large-v3  0.04/0.06  (V)
    # large-v3-turbo        (x)