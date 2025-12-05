#!/usr/bin/env python3
import cv2
import os

# -------------------------------
# CONFIG
# -------------------------------
IMG_DIR = "/home/ben/dev/ai/vision/datasets/coco-mini-yolo/images/train"
LBL_DIR = "/home/ben/dev/ai/vision/datasets/coco-mini-yolo/labels/train"

# Only show person (class 0)
PERSON_CLASS_ID = 0
PERSON_CLASS_NAME = "person"

# -------------------------------
# Get all images
# -------------------------------
images = sorted([f for f in os.listdir(IMG_DIR) if f.endswith(".jpg")])
if not images:
    print("No images found!")
    exit()

idx = 0
num_images = len(images)

# -------------------------------
# Draw bounding boxes (safe)
# -------------------------------
def draw_boxes(img, label_file):
    h, w = img.shape[:2]
    if not os.path.exists(label_file):
        return img

    with open(label_file, "r") as f:
        lines = f.readlines()

    for line in lines:
        parts = line.strip().split()
        if len(parts) != 5:
            continue
        class_id, x_center, y_center, width, height = map(float, parts)
        class_id = int(class_id)

        # Only draw person
        if class_id != PERSON_CLASS_ID:
            continue

        # Convert YOLO normalized to pixel coordinates
        x_c = x_center * w
        y_c = y_center * h
        bw = width * w
        bh = height * h

        x1 = int(x_c - bw / 2)
        y1 = int(y_c - bh / 2)
        x2 = int(x_c + bw / 2)
        y2 = int(y_c + bh / 2)

        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, PERSON_CLASS_NAME, (x1, y1-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
    return img

# -------------------------------
# Main loop
# -------------------------------
while True:
    img_name = images[idx]
    lbl_name = img_name.replace(".jpg", ".txt")

    img_path = os.path.join(IMG_DIR, img_name)
    lbl_path = os.path.join(LBL_DIR, lbl_name)

    img = cv2.imread(img_path)
    if img is None:
        print(f"Failed to load image: {img_path}")
        idx = (idx + 1) % num_images
        continue

    img_boxed = draw_boxes(img, lbl_path)
    display_name = f"{idx+1}/{num_images}: {img_name}"
    cv2.imshow(display_name, img_boxed)

    key = cv2.waitKey(0) & 0xFF
    cv2.destroyAllWindows()

    if key == ord("n"):       # Next image
        idx = (idx + 1) % num_images
    elif key == ord("p"):     # Previous image
        idx = (idx - 1) % num_images
    elif key == 27:           # Esc to exit
        break

