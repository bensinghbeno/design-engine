import cv2

# Load model
MODEL_PATH = "/home/ben/models/face-dnn"
net = cv2.dnn.readNetFromCaffe(
    f"{MODEL_PATH}/deploy.prototxt",
    f"{MODEL_PATH}/res10_300x300_ssd_iter_140000.caffemodel"
)

video_capture = cv2.VideoCapture(0)
FRAME_WIDTH = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
FRAME_HEIGHT = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
CENTER_TOLERANCE = 40

print("[INFO] DNN-based face tracking started...")

while True:
    ret, frame = video_capture.read()
    if not ret:
        break

    # Prepare blob for DNN
    blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300),
                                 (104.0, 177.0, 123.0), swapRB=False, crop=False)
    net.setInput(blob)
    detections = net.forward()

    command = "NO FACE"

    # Loop through detections
    h, w = frame.shape[:2]
    max_conf = 0
    best_box = None

    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.5 and confidence > max_conf:
            box = detections[0, 0, i, 3:7] * [w, h, w, h]
            best_box = box.astype("int")
            max_conf = confidence

    if best_box is not None:
        x1, y1, x2, y2 = best_box
        face_center_x = (x1 + x2) // 2
        frame_center_x = FRAME_WIDTH // 2
        offset = face_center_x - frame_center_x

        if abs(offset) <= CENTER_TOLERANCE:
            command = "CENTERED"
        elif offset < 0:
            command = "TURN LEFT"
        else:
            command = "TURN RIGHT"

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, command, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    cv2.imshow("DNN Face Tracker", frame)
    print("[COMMAND]", command)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

video_capture.release()
cv2.destroyAllWindows()
