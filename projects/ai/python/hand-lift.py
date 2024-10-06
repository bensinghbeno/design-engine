import cv2
import mediapipe as mp

# Initialize mediapipe pose model to detect full body pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Capture video from webcam
cap = cv2.VideoCapture(0)

def detect_hand_above_head(pose_landmarks):
    # Get the Y position of the wrist, head (nose), and shoulder
    left_wrist_y = pose_landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y
    right_wrist_y = pose_landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y
    nose_y = pose_landmarks[mp_pose.PoseLandmark.NOSE].y
    left_shoulder_y = pose_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y
    right_shoulder_y = pose_landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y

    # Left hand above head check: wrist above head and above shoulder
    left_hand_up = left_wrist_y < nose_y and left_wrist_y < left_shoulder_y

    # Right hand above head check: wrist above head and above shoulder
    right_hand_up = right_wrist_y < nose_y and right_wrist_y < right_shoulder_y

    return left_hand_up, right_hand_up

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # Convert the image color to RGB for mediapipe
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False  # For better performance
    results_pose = pose.process(image)

    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    if results_pose.pose_landmarks:
        # Draw the full-body landmarks
        mp_drawing.draw_landmarks(image, results_pose.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        # Detect if either hand is above the head
        left_hand_up, right_hand_up = detect_hand_above_head(results_pose.pose_landmarks.landmark)

        if left_hand_up:
            cv2.putText(image, "Left hand is above head", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        if right_hand_up:
            cv2.putText(image, "Right hand is above head", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Display the resulting frame
    cv2.imshow('Hand Above Head Detection', image)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture and close windows
cap.release()
cv2.destroyAllWindows()
pose.close()
