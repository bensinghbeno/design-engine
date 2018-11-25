

import numpy as np

import cv2


global_prev_dir = "STRAIGHT"

#video_capture = cv2.VideoCapture(-1)
video_capture = cv2.VideoCapture("http://192.168.178.45:8080/video")

#video_capture.set(3, 1920)

#video_capture.set(4, 1080)



while(True):



    # Capture the frames

    ret, frame = video_capture.read()



    # Crop the image

    crop_img = frame[0:120, 0:1080]



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
            cy = int(M['m01']/den)



        cv2.line(crop_img,(cx,0),(cx,720),(255,0,0),1)

        cv2.line(crop_img,(0,cy),(1280,cy),(255,0,0),1)



        cv2.drawContours(crop_img, contours, -1, (0,255,0), 1)


        if cx <= 10 or cx >= 1000:
           print "I don't see the line"
           print("====== Previous Dir = %s"%global_prev_dir)


        if cx > 400 and cx < 600:
            print " =========== DRIVE STRAIGHT! ===================="
            global_prev_dir = "STRAIGHT"


        if cx <= 400 and cx > 10:
            print " =========== Turn LEFT! ===================="
            global_prev_dir = "LEFT"


        if cx >= 600 and cx < 1000:
            print " =========== Turn RIGHT! ===================="
            global_prev_dir = "RIGHT"





    print("################## CX = %s"%(cx))




    #Display the resulting frame

    cv2.imshow('frame',crop_img)

    if cv2.waitKey(1) & 0xFF == ord('q'):

        break
