import argparse
import cv2
import torch

def main():
    parser = argparse.ArgumentParser(description="YOLOv5 Human Detector")
    parser.add_argument("--weights", required=True, help="Path to YOLOv5 .pt weights")
    parser.add_argument("--video", required=True, help="Input video path")
    parser.add_argument("--output", default=None, help="Optional output video path")
    args = parser.parse_args()

    # Load YOLOv5 model
    print("[INFO] Loading model...")
    model = torch.hub.load("ultralytics/yolov5", "custom", path=args.weights)

    # Only detect class 0 ("person")
    model.classes = [0]

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        print("[ERROR] Cannot open video:", args.video)
        return

    # Prepare writer if output is required
    writer = None
    if args.output:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        writer = cv2.VideoWriter(args.output, fourcc, fps, (w, h))

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
    print("[INFO] Done.")

if __name__ == "__main__":
    main()

