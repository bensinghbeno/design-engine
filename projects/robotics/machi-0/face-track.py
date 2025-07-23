import cv2
import face_recognition
import subprocess
import psutil
import pygame

# Load reference face encoding
reference_image = face_recognition.load_image_file("reference.jpg")
reference_encoding = face_recognition.face_encodings(reference_image)[0]

video_capture = cv2.VideoCapture(0)
FRAME_WIDTH = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
CENTER_TOLERANCE = 40

# Paths to wav files (or mp3 if supported)
LEFT_WAV = "/home/ben/Music/left.wav"
RIGHT_WAV = "/home/ben/Music/right.wav"
FORWARD_WAV = "/home/ben/Music/forward.wav"
APPROACHED_WAV = "/home/ben/Music/approached.wav"
# Initialize pygame mixer
pygame.mixer.init()

def is_audio_playing():
    return pygame.mixer.music.get_busy()

def play_wav(path):
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()

print("[INFO] Specific face tracking started...")

last_command = None

while True:
    ret, frame = video_capture.read()
    if not ret:
        break

    # Detect faces and get encodings
    face_locations = face_recognition.face_locations(frame)
    face_encodings = face_recognition.face_encodings(frame, face_locations)

    command = "NO FACE"
    best_box = None

    for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
        match = face_recognition.compare_faces([reference_encoding], encoding, tolerance=0.5)[0]
        if match:
            best_box = (left, top, right, bottom)
            break  # Only track the first matching face

    if best_box is not None:
        left, top, right, bottom = best_box
        face_center_x = (left + right) // 2
        face_center_y = (top + bottom) // 2

        # Custom command logic based on X and Y
        if 400 <= face_center_x <= 500:
            command = "TURN RIGHT"
        elif 0 <= face_center_x <= 200:
            command = "TURN LEFT"
        elif 201 <= face_center_x <= 399:
            if face_center_y > 250:
                command = "FORWARD"
            elif face_center_y <= 250:
                command = "APPROACHED"
        else:
            command = "NO FACE"

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(
            frame,
            f"{command} ({face_center_x},{face_center_y})",
            (left, top - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2,
        )
        # Draw a small circle at the center of the bounding box
        cv2.circle(frame, (face_center_x, face_center_y), 5, (255, 0, 0), -1)

    # Play audio if command changed and no audio is playing
    if command in ["TURN LEFT", "TURN RIGHT", "APPROACHED", "FORWARD"] and command != last_command:
        if not is_audio_playing():
            if command == "TURN LEFT":
                play_wav(LEFT_WAV)
            elif command == "TURN RIGHT":
                play_wav(RIGHT_WAV)
            elif command == "APPROACHED":
                play_wav(APPROACHED_WAV)
            elif command == "FORWARD":
                play_wav(FORWARD_WAV)                
            last_command = command  # Set only if audio was played
    elif command not in ["TURN LEFT", "TURN RIGHT", "APPROACHED","FORWARD"]:
        last_command = None

    cv2.imshow("Specific Face Tracker", frame)
    print("[COMMAND]", command)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

video_capture.release()
cv2.destroyAllWindows()
