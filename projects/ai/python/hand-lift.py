import cv2
import mediapipe as mp
import subprocess
import threading
import queue
import argparse

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Hand detection with throttled TTS')
parser.add_argument('--throttle', type=int, default=10, help='Number of detections before TTS is triggered')
args = parser.parse_args()

# Create a queue for speech requests
speech_queue = queue.Queue()

# Function to speak text using espeak
def speak_text(text):
    subprocess.run(['espeak', text])

# Function to handle speech queue
def speech_worker():
    while True:
        text = speech_queue.get()
        if text is None:
            break
        speak_text(text)
        speech_queue.task_done()

# Start the speech worker thread
speech_thread = threading.Thread(target=speech_worker)
speech_thread.start()

# Function to add text to the speech queue
def queue_speech(text):
    # Clear the queue and add new text
    while not speech_queue.empty():
        try:
            speech_queue.get_nowait()
        except queue.Empty:
            break
    speech_queue.put(text)

# Initialize mediapipe pose model
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Capture video from webcam
cap = cv2.VideoCapture(0)

# Function to detect if the hand is above the head
def detect_hand_above_head(pose_landmarks):
    left_wrist_y = pose_landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y
    right_wrist_y = pose_landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y
    nose_y = pose_landmarks[mp_pose.PoseLandmark.NOSE].y
    left_shoulder_y = pose_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y
    right_shoulder_y = pose_landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y

    left_hand_up = left_wrist_y < nose_y and left_wrist_y < left_shoulder_y
    right_hand_up = right_wrist_y < nose_y and right_wrist_y < right_shoulder_y

    return left_hand_up, right_hand_up

# Counters for throttling
left_hand_counter = 0
right_hand_counter = 0

try:
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results_pose = pose.process(image)

        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results_pose.pose_landmarks:
            mp_drawing.draw_landmarks(image, results_pose.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            left_hand_up, right_hand_up = detect_hand_above_head(results_pose.pose_landmarks.landmark)

            if left_hand_up:
                left_hand_counter += 1
                cv2.putText(image, f"Left hand up: {left_hand_counter}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                if left_hand_counter % args.throttle == 0:
                    queue_speech("Left hand is up")
            else:
                left_hand_counter = 0

            if right_hand_up:
                right_hand_counter += 1
                cv2.putText(image, f"Right hand up: {right_hand_counter}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                if right_hand_counter % args.throttle == 0:
                    queue_speech("Right hand is up")
            else:
                right_hand_counter = 0

        cv2.imshow('Hand Above Head Detection', image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    pose.close()

    # Stop the speech worker thread
    speech_queue.put(None)
    speech_thread.join()