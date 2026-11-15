import cv2
def get_video(address):
    cap = cv2.VideoCapture(address)

    if not cap.isOpened():
        print(f"Error: Unable to open stream {address}")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to read frame (stream ended or lost connection)")
            break

        cv2.imshow("RTSP Stream", frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    addr_1 = 'rtsp://localhost:8554/gazebo_cam1'
    addr_2 = 'rtsp://localhost:8554/gazebo_cam2'
    get_video(addr_1)