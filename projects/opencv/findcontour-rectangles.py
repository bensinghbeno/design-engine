# Find Contours and Draw Rectangles to indicate it on images.

# Import the modules
import sys
import cv2
import numpy as np
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

# Display image

def display_image(image_path, image_mode):
    cv2.imshow("Image_mode :: %s"%image_mode, image_path)
    cv2.waitKey()
    #cv2.destroyAllWindows()

# Main Script

display_greeting()
process_commandline()

# create blank image

blank_image = np.ones((500,800,3), np.uint8)
blank_image[:] = (255, 255, 255)
image=cv2.cv.fromarray(blank_image)
#display_image(blank_image,"blank_image : ")

im = cv2.imread(image_path)
display_image(im, "normal")

# Grayscale the image with Gaussian filter
im_gray = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
im_gray = cv2.GaussianBlur(im_gray, (5, 5), 0)
display_image(im_gray, "Grayscale the image with Gaussian filter")

# Perform THRESH_BINARY_INV
ret, im_th = cv2.threshold(im_gray, 90, 255, cv2.THRESH_BINARY_INV)
display_image(im_th, "Perform THRESH_BINARY_INV")


# Find contours
ctrs, _ = cv2.findContours(im_th.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
contours1, _ = cv2.findContours(im_th.copy(),cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)

cv2.drawContours(blank_image, contours1, 2, (0, 0, 0), 3)
cv2.imshow("my contour1", blank_image)
cv2.waitKey()


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

