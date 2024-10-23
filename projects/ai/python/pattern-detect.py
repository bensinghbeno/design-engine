import cv2
from ultralytics import YOLO

# Load YOLO model (replace 'yolov8n.pt' with a QR-code specific model if available)
model = YOLO('yolov8n.pt')  # This can be a custom model trained on QR codes

# Initialize the webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

while True:
    # Capture frame-by-frame from the webcam
    ret, frame = cap.read()

    if not ret:
        print("Failed to capture image.")
        break

    # Use the YOLO model to detect objects (QR codes) in the frame
    results = model(frame)

    # Extract results: bounding boxes, class labels, and confidence scores
    for result in results:
        boxes = result.boxes
        for box in boxes:
            # Get the coordinates of the detected box (x1, y1, x2, y2)
            x1, y1, x2, y2 = box.xyxy[0].int().numpy()

            # Get the class label (use a custom-trained YOLO model for detecting QR codes)
            label = box.cls[0]

            # If 'label' matches 'QR code' class, draw the line (customize this index based on your model)
            if label == 0:  # Replace 0 with your QR code class index
                # Calculate the center of the QR code
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2

                # Draw a vertical yellow line at the center of the detected QR code
                cv2.line(frame, (center_x, 0), (center_x, frame.shape[0]), (0, 255, 255), 2)

                # Draw the bounding box for visualization
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Display the resulting frame
    cv2.imshow('YOLO QR Code Detection', frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()
