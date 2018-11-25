import numpy as np
import cv2
import time
import urllib
import time

url='http://192.168.178.45:8080/shot.jpg'
 

while(True):


    imgResp = urllib.urlopen(url)
    

    imgNp = np.array(bytearray(imgResp.read()),dtype=np.uint8)
    
    # convert the array to OpenCV format 
    frame = cv2.imdecode(imgNp,-1) 

    # Capture the frames

    # ret, frame = video_capture.read()

 

    # Crop the image

    crop_img = frame[60:120, 0:160]

 

    # Convert to grayscale

    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)

 

    # Gaussian blur

    blur = cv2.GaussianBlur(gray,(5,5),0)

 

    # Color thresholding

    ret,thresh = cv2.threshold(blur,60,255,cv2.THRESH_BINARY_INV)

 

    # Find the contours of the frame

    contours,hierarchy = cv2.findContours(thresh.copy(), 1, cv2.CHAIN_APPROX_NONE)

 

    # Find the biggest contour (if detected)

    if len(contours) > 0:

        c = max(contours, key=cv2.contourArea)

        M = cv2.moments(c)

 
	den = M['m00']
	if den <= 0:
            cx = 0
            cy = 0
        else:
            cx = int(M['m10']/den)
            cy = int(M['m01']/M['m00'])

 

        cv2.line(crop_img,(cx,0),(cx,720),(255,0,0),1)

        cv2.line(crop_img,(0,cy),(1280,cy),(255,0,0),1)

 

        cv2.drawContours(crop_img, contours, -1, (0,255,0), 1)

 

        if cx >= 120:

            print "Turn Left!"

 

        if cx < 120 and cx > 50:

            print "On Track!"

        if cx == 0:
            current_milli_time = lambda: int(round(time.time() * 1000))
            print("I don't see the line - time = %s"%(current_milli_time()))


        if cx <= 50:

            print "Turn Right" 

        else:
            current_milli_time = lambda: int(round(time.time() * 1000))
            print("I don't see the line - time = %s"%(current_milli_time()))

 

    #Display the resulting frame

    cv2.imshow('frame',crop_img)

    if cv2.waitKey(1) & 0xFF == ord('q'):

        break
