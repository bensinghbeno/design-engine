# Works with the below configuration
# Ubuntu 16.04 LTS 64 bit (Guest running on VmWare)
# ImageMagick 6.8.9-9 Q16 x86_64 2018-06-11
# Python 2.7.12

import tensorflow as tf
import numpy as np
import sys
import os
import shutil
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from PIL import Image
from skimage import color, io
from scipy.misc import imread, imsave, imresize, toimage



print(" === Start Converion to Grayscale =====")

images_root_path = ""

if (len(sys.argv) == 1):
    print("Please provide images_root_path")
    exit()
            
else:
    images_root_path = str(sys.argv[1])
    
print(" images_root_path = %s"%images_root_path)

dir_list = os.listdir(images_root_path)

i = 0

for dir in dir_list:
   print("Directory = %s"%dir)
   files_dir = images_root_path + "/" + dir
   file_list = os.listdir(files_dir)
   i = i+1
   for file in file_list:
       i = i+1
       print("Converting Found File = %s"%file)
       file2convert = files_dir + "/" + file
       command = "convert -resize 28X28 " + file2convert + " converted2grayscale28/resized/" + dir + "/" + dir +"_" + str(i) + ".jpg"
       print("Conversion Command = %s"%command)
       os.system(command)

