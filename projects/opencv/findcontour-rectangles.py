# Find Contours and Draw Rectangles to indicate it on images.

# Import the modules
import sys
import cv2
from matplotlib import pyplot as plt

# Define Methods

# Greeting

def display_greeting():
  print("----------- Welcome to Ben's countour indicator ------------");


# Process Commandline arguments

def process_commandline():
  if (len(sys.argv) == 1):
    sys.exit('  No Arguments provided, Please provide image path')
  else:	
    global image_path;
    image_path = sys.argv[1];
    print('  image path = %s'%image_path);


# Main Script

display_greeting()
process_commandline()

# Grayscale the image with Gaussian filter
im = cv2.imread(image_path)
im_gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
im_gray = cv2.GaussianBlur(im_gray, (5, 5), 0)

# Perform THRESH_BINARY_INV
ret, im_th = cv2.threshold(im_gray, 90, 255, cv2.THRESH_BINARY_INV)

# Find contours
ctrs, hier = cv2.findContours(im_th.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Find the rectangles of each contour
rects = [cv2.boundingRect(ctr) for ctr in ctrs]

for rect in rects:
    # Draw rectangles
    cv2.rectangle(im, (rect[0], rect[1]), (rect[0] + rect[2], rect[1] + rect[3]), (0, 255, 0), 3) 
    # Create rectangular region around contour image
    leng = int(rect[3] * 1.6)
    pt1 = int(rect[1] + rect[3] // 2 - leng // 2)
    pt2 = int(rect[0] + rect[2] // 2 - leng // 2)
    roi = im_th[pt1:pt1+leng, pt2:pt2+leng]

    roi = cv2.resize(roi, (28, 28), interpolation=cv2.INTER_AREA)
    roi = cv2.dilate(roi, (3, 3))

cv2.imshow("Image with Contour Rectangles", im)
cv2.waitKey()

