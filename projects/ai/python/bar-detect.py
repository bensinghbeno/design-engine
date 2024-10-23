import cv2
import numpy as np

# Initialize the video capture (0 for the default camera)
cap = cv2.VideoCapture(0)

# Get frame width and height
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Convert frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Apply threshold to detect the black bar (assuming it's darker than the background)
    _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # Find the largest contour (assuming it's the black bar)
        largest_contour = max(contours, key=cv2.contourArea)

        # Get bounding rectangle of the largest contour
        x, y, w, h = cv2.boundingRect(largest_contour)

        # Calculate the center of the bar
        center_x = x + w // 2

        # Draw a vertical yellow line at the center of the bar
        cv2.line(frame, (center_x, 0), (center_x, frame_height), (0, 255, 255), 2)

        # Draw the rectangle around the detected bar (for visualization)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Show the frame with the tracking line
    cv2.imshow('Lateral Movement Detection', frame)

    # Break the loop when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture and close windows
cap.release()
cv2.destroyAllWindows()
