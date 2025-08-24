import cv2
import sys
import time
import numpy as np
from ultralytics import YOLO

# Constants
MOVE_THRESHOLD = 50  # pixels of center shift
WAIT_TIME = 5  # seconds to wait for possible movement
DISPLAY_TIME = 1000  # milliseconds per person display

# Read camera index from command line
if len(sys.argv) < 2:
    print("Usage: python3 simple_movement_detector.py <camera_index>")
    sys.exit(1)

cam_index = int(sys.argv[1])
cap = cv2.VideoCapture(cam_index)
if not cap.isOpened():
    print(f"Error: Cannot open camera {cam_index}")
    sys.exit(1)

# Load YOLOv8
model = YOLO("yolov8n.pt")  # or yolov8s.pt for better accuracy

def get_person_boxes(frame):
    results = model(frame)
    boxes = []
    for r in results:
        for box in r.boxes:
            cls = int(box.cls.item())
            if cls == 0:  # class 0 = person
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                boxes.append({'bbox': (x1, y1, x2, y2), 'center': (cx, cy)})
    return boxes

print("Detecting people... Stand still.")
ret, initial_frame = cap.read()
if not ret:
    print("Error reading initial frame.")
    cap.release()
    sys.exit(1)

initial_people = get_person_boxes(initial_frame)
print(f"Detected {len(initial_people)} people initially.")

print(f"Waiting {WAIT_TIME} seconds for movement...")
time.sleep(WAIT_TIME)

ret, later_frame = cap.read()
if not ret:
    print("Error reading later frame.")
    cap.release()
    sys.exit(1)

later_people = get_person_boxes(later_frame)

# Compare initial and later boxes
moved_people = []
for i, person1 in enumerate(initial_people):
    (cx1, cy1) = person1['center']
    matched = False
    for person2 in later_people:
        (cx2, cy2) = person2['center']
        dist = np.linalg.norm([cx2 - cx1, cy2 - cy1])
        if dist > MOVE_THRESHOLD:
            moved_people.append(person2['bbox'])
            matched = True
            break
    if matched:
        continue

# Show each moved person
print(f"{len(moved_people)} people moved.")
for idx, (x1, y1, x2, y2) in enumerate(moved_people):
    cropped = later_frame[y1:y2, x1:x2]
    if cropped.size > 0:
        win_name = f"Moved Person {idx+1}"
        cv2.imshow(win_name, cropped)
        cv2.waitKey(DISPLAY_TIME)
        cv2.destroyWindow(win_name)

cap.release()
cv2.destroyAllWindows()
