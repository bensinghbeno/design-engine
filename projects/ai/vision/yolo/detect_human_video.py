import cv2
import torch
import sys
from ultralytics import YOLO

# Global variables for play/pause, rewind, seek, and save functionality
is_paused = False
rewind_frames = 100
seek_forward_frames = 100  # Number of frames to seek forward
save_frame_count = 0  # Counter for saved frames

def main():
    if len(sys.argv) < 4:
        print("Usage: python detect_human_video.py <mode> <path> <fps> [--yolov8m | --yolov8n | --yolov11n]")
        print("Modes: --video <video_path>, --image <image_path>")
        sys.exit(1)

    mode = sys.argv[1]
    path = sys.argv[2]
    fps = int(sys.argv[3])  # Read FPS from command-line argument

    # Check for model selection flags
    use_yolov8m = '--yolov8m' in sys.argv
    use_yolov8n = '--yolov8n' in sys.argv
    use_yolov11 = '--yolov11n' in sys.argv

    if use_yolov8m:
        model_path = "yolov8m.pt"  # YOLOv8 Medium model path
        print(f"Using YOLOv8m model: {model_path}")
        print(f"Loading YOLOv8m model from {model_path} ...")
        model = YOLO(model_path)  # Load YOLOv8m model

        # Configure YOLOv8m model for partial body detection
        model.conf = 0.2   # Lower confidence threshold
        model.iou = 0.6    # Allow more overlap
        model.classes = [0]  # Detect only 'person' (class 0 in COCO)
    elif use_yolov8n:
        model_path = "/home/ben/Documents/toyo/ulpc/dev/mobilenet-custom/gemini/yolov8n/runs/detect/train/weights/best.pt"  # Custom YOLOv8 Nano model path
        print(f"Using YOLOv8n model: {model_path}")
        print(f"Loading YOLOv8n model from {model_path} ...")
        model = YOLO(model_path)  # Load YOLOv8n model

        # Configure YOLOv8n model for partial body detection
        model.conf = 0.2   # Lower confidence threshold
        model.iou = 0.6    # Allow more overlap
        model.classes = [0]  # Detect only 'person' (class 0 in COCO)
    elif use_yolov11:
        model_name = "yolo11n.pt"  # YOLOv11n model path
        print(f"Using YOLOv11n model: {model_name}")
        print(f"Loading YOLOv11n model from {model_name} ...")
        model = YOLO(model_name)  # Automatically downloads if not available

        # YOLOv11-specific settings
        conf_threshold = 0.25  # Lower confidence threshold to catch partial bodies
        frame_resize = 0.75    # Resize factor for large videos
    else:
        model_path = "/home/ben/dev/ai/vision/exports/yolov5-coco2017/weights/yv5-320-4g.pt"
        print(f"Using YOLOv5 model: {model_path}")
        print(f"Loading YOLOv5 model from {model_path} ...")
        model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, force_reload=False)

        # Configure YOLOv5 model for partial body detection
        model.conf = 0.05      # Lower confidence threshold
        model.iou = 0.15       # Retain overlapping boxes
        model.agnostic = True
        model.multi_label = True
        model.augment = True   # Multi-scale + flip inference

    MAX_BOX_SIZE = 800  # Maximum box size in pixels

    if mode == '--video':
        process_video(path, model, MAX_BOX_SIZE, fps, use_yolov8m or use_yolov8n, use_yolov11)
    elif mode == '--image':
        process_image(path, model, MAX_BOX_SIZE, use_yolov8m or use_yolov8n, use_yolov11)
    else:
        print("Error: Invalid mode. Use --video or --image.")
        sys.exit(1)

def process_video(video_path, model, max_box_size, fps, use_yolov8, use_yolov11):
    global is_paused, rewind_frames, seek_forward_frames, save_frame_count

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Error: Could not open video {video_path}")
        sys.exit(1)

    cv2.namedWindow("Partial Human Detection", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Partial Human Detection", 1280, 720)

    frame_delay = int(1000 / fps)  # Delay in milliseconds between frames

    while True:
        if not is_paused:
            ret, frame = cap.read()
            if not ret:
                break

            # Optional resize for YOLOv11n
            if use_yolov11:
                frame = cv2.resize(frame, None, fx=0.75, fy=0.75)

            # Run inference
            if use_yolov8:
                results = model(frame, imgsz=1280, verbose=False)
                detections = results[0].boxes
            elif use_yolov11:
                results = model.predict(frame, conf=0.25, verbose=False)
                detections = results[0].boxes
            else:
                results = model(frame, size=640)
                detections = results.xyxy[0].cpu().numpy()

            for box in detections:
                if use_yolov8 or use_yolov11:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                else:
                    x1, y1, x2, y2, conf, cls = map(int, box[:4]) + box[4:]

                if cls_id == 0:  # 'person'
                    # Filter out extremely large boxes
                    if (x2 - x1) > max_box_size or (y2 - y1) > max_box_size:
                        continue

                    # Draw bounding box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"person {conf:.2f}",
                                (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                                0.6, (0, 255, 0), 2)

            cv2.imshow("Partial Human Detection", frame)

        key = cv2.waitKey(frame_delay) & 0xFF
        if key == ord('q'):  # Quit
            break
        elif key == ord('p'):  # Play/Pause
            is_paused = not is_paused
        elif key == ord('r'):  # Rewind
            rewind_video(cap, rewind_frames)
        elif key == ord('f'):  # Seek forward
            seek_forward(cap, seek_forward_frames)
        elif key == ord('s'):  # Save current frame
            save_current_frame(frame)

    cap.release()
    cv2.destroyAllWindows()

def process_image(image_path, model, max_box_size, use_yolov8, use_yolov11):
    if not os.path.exists(image_path):
        print(f"❌ Error: Image file {image_path} does not exist.")
        sys.exit(1)

    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Error: Could not read image {image_path}")
        sys.exit(1)

    # Run inference
    if use_yolov8:
        results = model(image, imgsz=1280, verbose=False)
        detections = results[0].boxes
    elif use_yolov11:
        results = model.predict(image, conf=0.25, verbose=False)
        detections = results[0].boxes
    else:
        results = model(image, size=640)
        detections = results.xyxy[0].cpu().numpy()

    for box in detections:
        if use_yolov8 or use_yolov11:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
        else:
            x1, y1, x2, y2, conf, cls = map(int, box[:4]) + box[4:]

        if cls == 0:  # 'person'
            if (x2 - x1) > max_box_size or (y2 - y1) > max_box_size:
                continue

            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(image, f"person {conf:.2f}",
                        (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 255, 0), 2)

    cv2.imshow("Partial Human Detection", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def seek_forward(cap, frames_to_seek):
    """Seek forward in the video by a specified number of frames."""
    current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    new_frame = min(total_frames - 1, current_frame + frames_to_seek)
    cap.set(cv2.CAP_PROP_POS_FRAMES, new_frame)

def rewind_video(cap, frames_to_rewind):
    """Rewind the video by a specified number of frames."""
    current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
    new_frame = max(0, current_frame - frames_to_rewind)
    cap.set(cv2.CAP_PROP_POS_FRAMES, new_frame)

def save_current_frame(frame):
    """Save the current frame as an image."""
    global save_frame_count
    save_frame_count += 1
    filename = f"saved_frame_{save_frame_count}.jpg"
    cv2.imwrite(filename, frame)
    print(f"✅ Frame saved as {filename}")

if __name__ == "__main__":
    main()

