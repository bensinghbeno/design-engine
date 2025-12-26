import cv2
import mediapipe as mp
import numpy as np
import time
import argparse
import vlc

mp_pose = mp.solutions.pose
mp_face = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

pose = mp_pose.Pose(min_detection_confidence=0.5)
face = mp_face.FaceMesh(max_num_faces=1)

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--video", type=str, required=True, help="Path to mp4 video")
args = parser.parse_args()

cap = cv2.VideoCapture(0)

# Setup VLC Player
vlc_instance = vlc.Instance("--input-repeat=65535") # Loop video indefinitely
player = vlc_instance.media_player_new()
media = vlc_instance.media_new(args.video)
player.set_media(media)

HAND_MOUTH_THRESHOLD = 0.55   # normalized distance
HAND_MOUTH_VISUAL_THRESHOLD = 0.55
CHEW_THRESHOLD = 0.00005      # Variance threshold: Increase (e.g. 0.0001) if too sensitive
CHEW_FRAMES = 10
PLAY_DURATION = 60

mouth_movement = []
chewing_detected = False
play_until = 0

def distance(a, b):
    return np.linalg.norm(np.array(a) - np.array(b))

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    pose_result = pose.process(rgb)
    face_result = face.process(rgb)

    eating = False

    if pose_result.pose_landmarks and face_result.multi_face_landmarks:
        lm = pose_result.pose_landmarks.landmark
        face_lm = face_result.multi_face_landmarks[0].landmark

        # Mouth landmark (upper lip)
        mouth = [face_lm[13].x, face_lm[13].y]

        # Right & left hand
        right_hand = [lm[mp_pose.PoseLandmark.RIGHT_INDEX].x,
                      lm[mp_pose.PoseLandmark.RIGHT_INDEX].y]

        left_hand = [lm[mp_pose.PoseLandmark.LEFT_INDEX].x,
                     lm[mp_pose.PoseLandmark.LEFT_INDEX].y]

        # Hand near mouth
        if (distance(right_hand, mouth) < HAND_MOUTH_THRESHOLD or
            distance(left_hand, mouth) < HAND_MOUTH_THRESHOLD):
            eating = True

        # Chewing detection (jaw movement)
        # Use Nose (1) and Chin (152) to detect jaw movement even if lips are closed
        nose_y = face_lm[1].y
        chin_y = face_lm[152].y
        jaw_distance = abs(chin_y - nose_y)

        mouth_movement.append(jaw_distance)
        if len(mouth_movement) > CHEW_FRAMES:
            mouth_movement.pop(0)

        if len(mouth_movement) == CHEW_FRAMES:
            variance = np.var(mouth_movement)
            chewing_detected = variance > CHEW_THRESHOLD

        # Draw Hand Boxes
        box_size = 50
        # Right Hand
        rh_pixel = (int(right_hand[0] * w), int(right_hand[1] * h))
        color_r = (0, 255, 0) if distance(right_hand, mouth) < HAND_MOUTH_VISUAL_THRESHOLD else (0, 255, 255)
        cv2.rectangle(frame, (rh_pixel[0] - box_size//2, rh_pixel[1] - box_size//2),
                      (rh_pixel[0] + box_size//2, rh_pixel[1] + box_size//2), color_r, 2)

        # Left Hand
        lh_pixel = (int(left_hand[0] * w), int(left_hand[1] * h))
        color_l = (0, 255, 0) if distance(left_hand, mouth) < HAND_MOUTH_VISUAL_THRESHOLD else (0, 255, 255)
        cv2.rectangle(frame, (lh_pixel[0] - box_size//2, lh_pixel[1] - box_size//2),
                      (lh_pixel[0] + box_size//2, lh_pixel[1] + box_size//2), color_l, 2)

        if chewing_detected:
            x_list = [l.x for l in face_lm]
            y_list = [l.y for l in face_lm]
            cv2.rectangle(frame, (int(min(x_list) * w), int(min(y_list) * h)),
                          (int(max(x_list) * w), int(max(y_list) * h)), (0, 255, 0), 2)

        if eating and chewing_detected:
            cv2.putText(frame, "EATING DETECTED",
                        (50, 50), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0, 255, 0), 2)
            
            # Reset/Extend timer
            play_until = time.time() + PLAY_DURATION

    # Video Playback Logic
    if time.time() < play_until:
        if not player.is_playing():
            player.play()
        status_text = f"Time left: {int(play_until - time.time())}s"
    else:
        if player.is_playing():
            player.pause()
        status_text = "PAUSED - EAT TO RESUME"
    
    cv2.putText(frame, status_text, (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    cv2.imshow("Eating Detection", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == 27 or key == ord('q'):
        break

cap.release()
player.stop()
cv2.destroyAllWindows()
