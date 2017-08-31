import sys
import numpy as np
import cv2
from matplotlib import pyplot as plt

if (len(sys.argv) == 1):
    sys.exit('  No Arguments provided, Please provide image directory path')
else:	
	image_path = sys.argv[1];

print('  image dir path = %s'%image_path);

img = cv2.imread(image_path,0)
plt.imshow(img, cmap = 'gray', interpolation = 'bicubic')
plt.xticks([]), plt.yticks([])  # to hide tick values on X and Y axis
plt.show()
