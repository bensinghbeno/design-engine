import urllib
import cv2
import numpy as np
import time

url='http://192.168.178.45:8080/shot.jpg'


while True:

    imgResp = urllib.urlopen(url)
    

    imgNp = np.array(bytearray(imgResp.read()),dtype=np.uint8)
    
    # convert the array to OpenCV format 
    img = cv2.imdecode(imgNp,-1)
	

    cv2.imshow('IPWebcam',img)


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
