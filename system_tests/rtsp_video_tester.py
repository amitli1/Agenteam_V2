import os
import cv2
#
# cv2 - computer vision 2 (open source openCV)
#

DEFAULT_RTSP_ADDRESS = "rtsp://localhost:8554/gazebo_cam1"
DEFAULT_SCREEN_SIZE_PERCENT = 100.0


def get_screen_resolution(default=(1920, 1080)):
    """
    Best-effort detection of the host screen resolution (through the X
    server, e.g. when DISPLAY / /tmp/.X11-unix are forwarded into a
    container). Falls back to `default` if detection fails.
    """
    try:
        from screeninfo import get_monitors
        monitor = get_monitors()[0]
        return monitor.width, monitor.height
    except Exception as e:
        print(f"Warning: could not detect screen resolution ({e}), using default {default}")
        return default


def get_video(address, screen_size_percent=100.0):
    cap = cv2.VideoCapture(address)

    if not cap.isOpened():
        print(f"Error: Unable to open stream {address}")
        return

    screen_size_percent = max(1.0, min(100.0, screen_size_percent))
    screen_w, screen_h = get_screen_resolution()
    window_w = int(screen_w * screen_size_percent / 100.0)
    window_h = int(screen_h * screen_size_percent / 100.0)

    window_name = "RTSP Stream"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, window_w, window_h)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to read frame (stream ended or lost connection)")
            break

        cv2.imshow(window_name, frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    rtsp_address = os.environ.get("RTSP_ADDRESS", DEFAULT_RTSP_ADDRESS)

    try:
        screen_percent = float(os.environ.get("SCREEN_SIZE_PERCENT", DEFAULT_SCREEN_SIZE_PERCENT))
    except ValueError:
        print(f"Warning: invalid SCREEN_SIZE_PERCENT, using default {DEFAULT_SCREEN_SIZE_PERCENT}")
        screen_percent = DEFAULT_SCREEN_SIZE_PERCENT

    print(f"Opening RTSP stream: {rtsp_address} (window size: {screen_percent}% of screen)")
    get_video(rtsp_address, screen_percent)
