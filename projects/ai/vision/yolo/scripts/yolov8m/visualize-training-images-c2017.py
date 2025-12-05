#!/usr/bin/env python3
import cv2
import os
import random

# -------------------------------
# CONFIG
# -------------------------------
IMG_DIR = "/home/ben/dev/ai/vision/datasets/coco-2017/images/train"
LBL_DIR = "/home/ben/dev/ai/vision/datasets/coco-2017/labels/train"

# Load class names from COCO (80 classes)
CLASS_NAMES = [
    "person","bicycle","car","motorcycle","airplane","bus","train","truck","boat",
    "traffic light","fire hydrant","stop sign","parking meter","bench",
    "bird","cat","dog","horse","sheep","cow","elephant","bear","zebra","giraffe",
    "backpack","umbrella","handbag","tie","suitcase","frisbee","skis","snowboard",
    "sports ball","kite","baseball bat","baseball glove","skateboard","surfboard",
    "tennis racket","bottle","wine glass","cup","fork","knife","spoon","bowl",
    "banana","apple","sandwich","orange","broccoli","carrot","hot dog","pizza",
    "donut","cake","chair","couch","potted plant","bed","dining table","toilet",
    "tv","laptop","mouse","remote","keyboard","cell phone","microwave","oven",
    "toaster","sink","refrigerator","book","clock","vase","scissors","teddy bear",
    "hair drier","toothbrush"
]

# Assign random colors for each class
random.seed(42)
COLORS = [tuple([int(c) for c in random.choices(range(0,256), k=3)]) for _ in CLASS_NAMES]

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
# Draw bounding boxes
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

        # Safety: skip invalid class ids
        if class_id < 0 or class_id >= len(CLASS_NAMES):
            continue

        x_c = x_center * w
        y_c = y_center * h
        bw = width * w
        bh = height * h

        x1 = int(x_c - bw / 2)
        y1 = int(y_c - bh / 2)
        x2 = int(x_c + bw / 2)
        y2 = int(y_c + bh / 2)

        color = COLORS[class_id]
        class_name = CLASS_NAMES[class_id]

        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        cv2.putText(img, class_name, (x1, y1-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
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

