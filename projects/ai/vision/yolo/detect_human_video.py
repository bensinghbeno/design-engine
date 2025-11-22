import argparse
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
    parser = argparse.ArgumentParser(description="YOLO Human Detection")
    parser.add_argument("--image", help="Path to the image file")
    parser.add_argument("--video", help="Path to the video file")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second for video processing")
    parser.add_argument("--weights", required=True, help="Path to YOLOv5 weights file")
    parser.add_argument("--output", default=None, help="Optional output video path for saving results")
    parser.add_argument("--yolov8m", action="store_true", help="Use YOLOv8m model")
    parser.add_argument("--yolov8n", action="store_true", help="Use YOLOv8n model")
    parser.add_argument("--yolov11n", action="store_true", help="Use YOLOv11n model")
    parser.add_argument("--yolov5", action="store_true", help="Use YOLOv5 model")
    args = parser.parse_args()

    # Ensure only one of --image or --video is provided
    if not args.image and not args.video:
        print("Error: You must specify either --image or --video.")
        sys.exit(1)
    if args.image and args.video:
        print("Error: You cannot specify both --image and --video at the same time.")
        sys.exit(1)

    # Load the appropriate model based on the command-line arguments
    if args.yolov8m:
        model_path = "yolov8m.pt"
        print(f"Using YOLOv8m model: {model_path}")
        model = YOLO(model_path)
        model.conf = 0.2
        model.iou = 0.6
        model.classes = [0]
    elif args.yolov8n:
        model_path = "/home/ben/Documents/toyo/ulpc/dev/mobilenet-custom/gemini/yolov8n/runs/detect/train/weights/best.pt"
        print(f"Using YOLOv8n model: {model_path}")
        model = YOLO(model_path)
        model.conf = 0.2
        model.iou = 0.6
        model.classes = [0]
    elif args.yolov11n:
        model_path = "yolo11n.pt"
        print(f"Using YOLOv11n model: {model_path}")
        model = YOLO(model_path)
        model.conf = 0.25
    elif args.yolov5:
        print(f"Using YOLOv5 model: {args.weights}")
        model = torch.hub.load("ultralytics/yolov5", "custom", path=args.weights)
        model.classes = [0]
    else:
        print("Error: No valid model specified. Use --yolov8m, --yolov8n, --yolov11n, or --yolov5.")
        sys.exit(1)

    # Process video or image based on the arguments
    if args.video:
        process_video(args.video, model, 800, args.fps, args.yolov8m or args.yolov8n, args.yolov11n)
    elif args.image:
        process_image(args.image, model, 800, args.yolov8m or args.yolov8n, args.yolov11n)

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
                detections = results.pandas().xyxy[0]  # YOLOv5 pandas output

            for _, det in detections.iterrows():
                xmin, ymin, xmax, ymax = int(det.xmin), int(det.ymin), int(det.xmax), int(det.ymax)
                conf = det.confidence

                # Draw bounding box
                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
                cv2.putText(frame, f"Human {conf:.2f}", (xmin, ymin - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

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
        detections = results.pandas().xyxy[0]  # YOLOv5 pandas output

    for _, det in detections.iterrows():
        xmin, ymin, xmax, ymax = int(det.xmin), int(det.ymin), int(det.xmax), int(det.ymax)
        conf = det.confidence

        # Draw bounding box
        cv2.rectangle(image, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
        cv2.putText(image, f"Human {conf:.2f}", (xmin, ymin - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

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

def process_yolov5(weights, video_path, output_path=None):
    """Process video using YOLOv5."""
    print("[INFO] Loading YOLOv5 model...")
    model = torch.hub.load("ultralytics/yolov5", "custom", path=weights)

    # Only detect class 0 ("person")
    model.classes = [0]

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("[ERROR] Cannot open video:", video_path)
        return

    # Prepare writer if output is required
    writer = None
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    print("[INFO] Processing video... Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Run YOLOv5 inference
        results = model(frame)

        # Convert to pandas-friendly format
        detections = results.pandas().xyxy[0]  # xmin, ymin, xmax, ymax, confidence, class

        # Draw bounding boxes
        for _, det in detections.iterrows():
            xmin, ymin, xmax, ymax = int(det.xmin), int(det.ymin), int(det.xmax), int(det.ymax)
            conf = det.confidence

            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
            cv2.putText(frame,
                        f"Human {conf:.2f}",
                        (xmin, ymin - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2)

        # Show frame
        cv2.imshow("Human Detection", frame)

        # Save output if writer exists
        if writer:
            writer.write(frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

