#!/usr/bin/env python3
import argparse
import cv2
import torch
import sys
import os
from ultralytics import YOLO

# Video control globals
is_paused = False
rewind_frames = 100
seek_forward_frames = 100
save_frame_count = 0

def parse_args():
    parser = argparse.ArgumentParser(description="YOLO Human Detection")
    parser.add_argument("--image", help="Path to the image file")
    parser.add_argument("--video", help="Path to the video file")
    parser.add_argument("--weights", required=True, help="Path to YOLO weights (.pt)")
    parser.add_argument("--output", default=None, help="Optional output video path for saving results")
    parser.add_argument("--fps", type=int, default=30, help="FPS for video processing")
    parser.add_argument("--yolov5", action="store_true", help="Use YOLOv5 model")
    parser.add_argument("--yolov8", action="store_true", help="Use YOLOv8 model")
    parser.add_argument("--classes", nargs="+", type=int, help="Optional list of class IDs to detect (0=person)")
    return parser.parse_args()

def load_model(weights_path, yolov5=False, yolov8=False, classes=None):
    if yolov5:
        print(f"[INFO] Loading YOLOv5 model from {weights_path}")
        model = torch.hub.load('ultralytics/yolov5', 'custom', path=weights_path, verbose=False)
        if classes is not None:
            model.classes = classes
        return model, "yolov5"
    elif yolov8:
        print(f"[INFO] Loading YOLOv8 model from {weights_path}")
        model = YOLO(weights_path)
        if classes is not None:
            model.classes = classes
        return model, "yolov8"
    else:
        print("Error: Must specify --yolov5 or --yolov8")
        sys.exit(1)

def draw_boxes_yolov5(frame, results):
    for _, det in results.pandas().xyxy[0].iterrows():
        xmin, ymin, xmax, ymax = int(det.xmin), int(det.ymin), int(det.xmax), int(det.ymax)
        conf = det.confidence
        cls_id = int(det['class'])
        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
        cv2.putText(frame, f"{cls_id} {conf:.2f}", (xmin, ymin-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    return frame

def draw_boxes_yolov8(frame, results):
    for box in results[0].boxes:
        xyxy = box.xyxy[0].cpu().numpy().astype(int)
        conf = float(box.conf[0])
        cls_id = int(box.cls[0])
        x1, y1, x2, y2 = xyxy
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"{cls_id} {conf:.2f}", (x1, y1-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    return frame

def process_image(image_path, model, model_type):
    if not os.path.exists(image_path):
        print(f"❌ Error: Image file {image_path} does not exist.")
        sys.exit(1)
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Error: Could not read image {image_path}")
        sys.exit(1)

    if model_type == "yolov5":
        results = model(image)
        image = draw_boxes_yolov5(image, results)
    else:
        results = model(image)
        image = draw_boxes_yolov8(image, results)

    cv2.imshow("YOLO Detection", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def process_video(video_path, model, model_type, fps=30, output_path=None):
    global is_paused, rewind_frames, seek_forward_frames, save_frame_count

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Error: Could not open video {video_path}")
        sys.exit(1)

    writer = None
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    frame_delay = int(1000 / fps)
    cv2.namedWindow("YOLO Detection", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("YOLO Detection", 1280, 720)

    while True:
        if not is_paused:
            ret, frame = cap.read()
            if not ret:
                break

            if model_type == "yolov5":
                results = model(frame)
                frame = draw_boxes_yolov5(frame, results)
            else:
                results = model(frame)
                frame = draw_boxes_yolov8(frame, results)

            cv2.putText(frame, f"Frame: {int(cap.get(cv2.CAP_PROP_POS_FRAMES))}", (10,30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

            cv2.imshow("YOLO Detection", frame)
            if writer:
                writer.write(frame)

        key = cv2.waitKey(frame_delay) & 0xFF
        if key == ord('q'):  # Quit
            break
        elif key == ord('p'):  # Pause
            is_paused = not is_paused
        elif key == ord('r'):  # Rewind
            current = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, current - rewind_frames))
        elif key == ord('f'):  # Forward
            current = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.set(cv2.CAP_PROP_POS_FRAMES, min(total-1, current + seek_forward_frames))
        elif key == ord('s'):  # Save frame
            save_frame_count += 1
            filename = f"saved_frame_{save_frame_count}.jpg"
            cv2.imwrite(filename, frame)
            print(f"✅ Frame saved as {filename}")

    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    args = parse_args()

    if not args.image and not args.video:
        print("Error: Provide --image or --video")
        sys.exit(1)

    # Load model explicitly
    model, model_type = load_model(args.weights, yolov5=args.yolov5, yolov8=args.yolov8, classes=args.classes)

    # Run inference
    if args.image:
        process_image(args.image, model, model_type)
    elif args.video:
        process_video(args.video, model, model_type, fps=args.fps, output_path=args.output)
