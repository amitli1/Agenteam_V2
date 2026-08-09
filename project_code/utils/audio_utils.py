
import logging
import pyaudio

def get_support_sample_rate():
    p = pyaudio.PyAudio()

    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:  # is input device
            logging.info(f"Device {i}: {dev['name']}")
            # Try common sample rates
            for rate in [8000, 16000, 22050, 44100, 48000, 96000]:
                try:
                    if p.is_format_supported(rate,
                                             input_device=dev['index'],
                                             input_channels=int(dev['maxInputChannels']),
                                             input_format=pyaudio.paInt16):
                        logging.info(f"  Supported rate: {rate} Hz")
                except ValueError:
                    pass

    p.terminate()


def get_input_device():
    p = pyaudio.PyAudio()

    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:  # is input device
            logging.info(f"Found input Device {i}: {dev['name']}")
            # Try common sample rates
            try:
                if p.is_format_supported(16000,
                                         input_device   = dev['index'],
                                         input_channels = int(dev['maxInputChannels']),
                                         input_format   = pyaudio.paInt16):
                    logging.info(f"\tInput Device {i}: {dev['name']} support SR=16000")
                    p.terminate()
                    return i
            except ValueError:
                pass

    logging.error(f"There is not input device which support SR=16000")
    p.terminate()
    return None


def get_output_device():
    p = pyaudio.PyAudio()

    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev['maxOutputChannels'] > 0:  # is input device
            logging.info(f"Device {i}: {dev['name']}")
            # Try common sample rates
            try:
                if p.is_format_supported(48000,
                                         input_device=dev['index'],
                                         input_channels=int(dev['maxInputChannels']),
                                         input_format=pyaudio.paInt16):
                    p.terminate()
                    return i
            except ValueError:
                pass

    p.terminate()