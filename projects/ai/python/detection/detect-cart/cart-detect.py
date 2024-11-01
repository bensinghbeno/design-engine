import cv2
import sys
from ultralytics import YOLO

# Load the pre-trained YOLOv8 model (using YOLOv8n for faster inference)
model = YOLO("yolov8n.pt")  # You can try "yolov8m.pt" or "yolov8l.pt" for more accuracy if needed

# Define the classes to filter
target_classes = {"motorcycle", "truck", "suitcase", "chair"}

# Read video input from the command line
video_path = sys.argv[1] if len(sys.argv) > 1 else 0  # Default to webcam if no path is provided
cap = cv2.VideoCapture(video_path)

# Check if the video was opened successfully
if not cap.isOpened():
    print("Error: Could not open video.")
    sys.exit()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Perform detection
    results = model(frame)
    
    # Draw bounding boxes for each detected object in the target classes
    for result in results:
        for box in result.boxes:
            # Get box coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])  # Convert tensor to integer
            class_name = model.names.get(class_id, "Unknown")  # Get the class name, or "Unknown" if not found
            
            # Only draw the box if the class is in target_classes
            if class_name in target_classes:
                # Draw green bounding box for each detected object
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Set label at middle-left side of the bounding box
                label = f"{class_name}: {confidence:.2f}"
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                label_x = x1  # Left side of the bounding box
                label_y = y1 + (y2 - y1) // 2 + label_size[1] // 2  # Middle of the bounding box vertically
                cv2.putText(frame, label, (label_x, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Display the result
    cv2.imshow('Object Detection', frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
