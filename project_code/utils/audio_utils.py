
import logging
import pyaudio

from project_code.utils.utils import is_intel


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

def get_input_device_sr(device_number):
    """Return the minimum sample rate >= 16000 supported by the given device.
       Falls back to the device's reported default sample rate if none found."""
    p = pyaudio.PyAudio()

    try:
        dev = p.get_device_info_by_index(device_number)
        candidate_rates = sorted(r for r in
                                  [8000, 16000, 22050, 24000, 32000, 44100, 48000, 96000]
                                  if r >= 16000)

        for rate in candidate_rates:
            try:
                if p.is_format_supported(rate,
                                          input_device   = dev['index'],
                                          input_channels = int(dev['maxInputChannels']),
                                          input_format   = pyaudio.paInt16):
                    logging.info(f"Device {device_number} ({dev['name']}): using SR={rate}")
                    return rate
            except ValueError:
                pass

        default_rate = int(dev['defaultSampleRate'])
        logging.warning(f"Device {device_number} ({dev['name']}): no candidate rate >= 16000 "
                         f"supported, falling back to default SR={default_rate}")
        return default_rate
    finally:
        p.terminate()


def get_input_device_all_sr():
    p = pyaudio.PyAudio()

    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:  # is input device
            logging.info(f"Found input Device {i}: {dev['name']}")

            if is_intel():
                logging.info(f"\tInput Device {i}: {dev['name']} selected")
                p.terminate()
                return i
            else:
                # jetson: only pick USB input devices
                if "usb" not in dev['name'].lower():
                    continue

                logging.info(f"\tUSB input Device {i}: {dev['name']} selected")
                p.terminate()
                return i

    logging.error("There is no suitable input device")
    p.terminate()
    return None


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

                    if is_intel():
                        logging.info(f"\tInput Device {i}: {dev['name']} support SR=16000")
                        p.terminate()
                        return i
                    else:
                        #  jetson:
                        if "usb" not in dev['name'].lower():
                            continue

                        logging.info(f"\tUSB input Device {i}: {dev['name']} support SR=16000")
                        p.terminate()
                        return i
            except ValueError:
                pass

    logging.error(f"There is not input device which support SR=16000")
    p.terminate()
    # return None
    return get_input_device_all_sr()



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