import numpy as np
import cv2


cap = cv2.VideoCapture(0)

while(True):
    # Capture frame-by-frame
    ret, frame = cap.read()

    flip_img = cv2.flip( frame, 1 )


    # Our operations on the frame come here
    gray = cv2.cvtColor(flip_img, cv2.COLOR_BGR2GRAY)

    # Display the resulting frame
    cv2.imshow('Mirror Video Display',gray)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
