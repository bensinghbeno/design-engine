import cv2
import face_recognition

# Load reference face encoding
reference_image = face_recognition.load_image_file("reference.jpg")
reference_encoding = face_recognition.face_encodings(reference_image)[0]

video_capture = cv2.VideoCapture(0)
FRAME_WIDTH = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
CENTER_TOLERANCE = 40

print("[INFO] Specific face tracking started...")

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
        frame_center_x = FRAME_WIDTH // 2
        offset = face_center_x - frame_center_x

        if abs(offset) <= CENTER_TOLERANCE:
            command = "CENTERED"
        elif offset < 0:
            command = "TURN LEFT"
        else:
            command = "TURN RIGHT"

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, command, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    cv2.imshow("Specific Face Tracker", frame)
    print("[COMMAND]", command)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

video_capture.release()
cv2.destroyAllWindows()
