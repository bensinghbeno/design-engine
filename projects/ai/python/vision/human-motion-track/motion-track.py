import cv2
import mediapipe as mp
import sys

# Mediapipe pose setup
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

def detect_human_movement(video_file=None):
    # Use webcam if no video file is provided
    if video_file:
        cap = cv2.VideoCapture(video_file)
    else:
        cap = cv2.VideoCapture(0)

    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            # Calculate the center x position of the person
            left_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x
            right_shoulder = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x
            person_center_x = int((left_shoulder + right_shoulder) / 2 * FRAME_WIDTH)

            # Draw the vertical line in the middle of the person
            cv2.line(frame, (person_center_x, 0), (person_center_x, FRAME_HEIGHT), (0, 255, 255), 2)

        # Display the frame
        cv2.imshow("Human Detection", frame)

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Check if a video file argument was provided
    video_file = sys.argv[1] if len(sys.argv) > 1 else None
    detect_human_movement(video_file)
