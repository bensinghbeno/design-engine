import cv2
import argparse
import time

def main():
    parser = argparse.ArgumentParser(description="Record video from webcam.")
    parser.add_argument("index", type=int, help="Camera index (e.g., 0, 1, 2...)")
    parser.add_argument("duration", type=int, help="Duration of recording in seconds")
    args = parser.parse_args()

    cam_index = args.index
    duration = args.duration

    cap = cv2.VideoCapture(cam_index)

    if not cap.isOpened():
        print(f"❌ Unable to open camera with index {cam_index}")
        return

    # Get frame size
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Define codec and output filename
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('output.avi', fourcc, 20.0, (width, height))

    print(f"🎥 Recording for {duration} seconds from camera {cam_index}...")

    start_time = time.time()

    while time.time() - start_time < duration:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to grab frame")
            break
        out.write(frame)
        cv2.imshow('Recording', frame)
        if cv2.waitKey(1) == ord('q'):
            print("❗ Interrupted by user")
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print("✅ Done! Saved as output.avi")

if __name__ == "__main__":
    main()

