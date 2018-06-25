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



print(" === Start Convertion to Grayscale =====")

compressed_image_dataset_path = ""

if (len(sys.argv) == 1):
    print("Please provide compressed_image_dataset_path")
    exit()
            
else:
    compressed_image_dataset_path = str(sys.argv[1])
    
print(" compressed_image_dataset_path = %s"%compressed_image_dataset_path)


sep = '.'
dataset_rel_dir = compressed_image_dataset_path.split(sep, 1)[0]
dataset_rel_dir = dataset_rel_dir.split("/",1)[1] 
print("dataset_rel_dir = %s"%dataset_rel_dir) 

training_dir = "my_training_data"
os.system('mkdir -p ' + training_dir)

print("Extract Images from archive =============")
os.system('tar -xvf ' + compressed_image_dataset_path + ' -C ' + training_dir)
print("Extract Images completed ================")

images_root_path = training_dir + '/' + dataset_rel_dir
print("images_root_path = %s"%images_root_path)




# Create Resized Images Directory
resized_images_dir = training_dir + '/' + dataset_rel_dir + '_resized'
os.system('mkdir -p ' +  resized_images_dir)

for i in range(10):
    os.system('mkdir -p ' + resized_images_dir + '/' + str(i))


# Create Greyed Images Directory

greyed_images_dir = training_dir + '/' + dataset_rel_dir + '_greyed'
os.system('mkdir -p ' +  greyed_images_dir)

for i in range(10):
    os.system('mkdir -p ' + greyed_images_dir + '/' + str(i))


# Resize & convert to  Greyed Images

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
       resized_file = " " + resized_images_dir + "/" + dir + "/" + dir +"_" + str(i) + ".jpg"
       command = "convert -resize 28X28! " + file2convert + resized_file
       print("Resize Conversion Command = %s"%command)
       os.system(command)

       command = "convert " + resized_file + " -colorspace Gray" + " " + greyed_images_dir + "/" + dir + "/" + dir +"_" + str(i)  + "_28" + "_gray"+ ".jpg"
       print("Gray Conversion Command = %s"%command)
       os.system(command)

