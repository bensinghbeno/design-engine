# Works with the below configuration
# Ubuntu 16.04 LTS 64 bit (Guest running on VmWare)
# Tensorflow 1.7.0 
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

from PIL import Image
from min_ben_mnist_functions import ProcessCommandline
from min_ben_mnist_functions import plot_images
from min_ben_mnist_functions import optimize
from min_ben_mnist_functions import recognizeandplotimage
from min_ben_mnist_functions import plot_mnist_test_image_at_index
from min_ben_mnist_functions import plot_grayscale_image
from min_ben_mnist_functions import save_grayscale_image_as_png
from min_ben_mnist_functions import extract_save_numeric_dataset_images
from min_ben_mnist_functions import get_label_one_hot_array
from min_ben_mnist_functions import load_plot_get_greyscale_image

# ======= Start ! ==================================================================================================================================


image_index = 555 # Remove this

 # Process Command line

image_file = ProcessCommandline()

# Import Input data Images
from tensorflow.examples.tutorials.mnist import input_data
data = input_data.read_data_sets("data/MNIST/", one_hot=True)
data.test.cls = np.array([label.argmax() for label in data.test.labels])

# Variables
img_size = 28
img_size_flat = img_size * img_size
img_shape = (img_size, img_size)
num_classes = 10
batch_size = 100



# ========================================================== TEST AREA ==================================================================

# x_batch, y_true_batch = data.train.next_batch(3)
# imarray = np.array(x_batch[0])
# imarray = imarray.reshape(28, 28)
# 
# plt.gray()
# plt.imshow(imarray)
# plt.show()
# plt.close()
#  
# im = toimage(imarray)
# im.save("number.png")
# 
# exit()

#print(" =%s"%)


# =======================================================================================================================================



# Placeholder variables

x = tf.placeholder(tf.float32, [None, img_size_flat])
y_true = tf.placeholder(tf.float32, [None, num_classes])
y_true_cls = tf.placeholder(tf.int64, [None])


# Variables to be optimized

weights = tf.Variable(tf.zeros([img_size_flat, num_classes]))

biases = tf.Variable(tf.zeros([num_classes]))

#Model

logits = tf.matmul(x, weights) + biases

y_pred = tf.nn.softmax(logits)

y_pred_cls = tf.argmax(y_pred, axis=1)

cross_entropy = tf.nn.softmax_cross_entropy_with_logits(logits=logits,
                                                        labels=y_true)
cost = tf.reduce_mean(cross_entropy)

optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.5).minimize(cost)

# Performance measures

correct_prediction = tf.equal(y_pred_cls, y_true_cls)
accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))


# Session & detection

session = tf.Session()
session.run(tf.global_variables_initializer())

optimize(num_iterations=10, data=data, session=session, optimizer=optimizer, batch_size=batch_size, x=x, y_true=y_true)

#test_image = data.test.images[(image_index-1):image_index]
#test_labels = data.test.labels[(image_index-1):image_index]
test_classes = data.test.cls[(image_index-1):image_index]
#feed_dict_test2 = {x: test_image, y_true: test_labels, y_true_cls: test_classes}


## test custom ############
test_image = load_plot_get_greyscale_image(image_file)
test_labels = get_label_one_hot_array(0,10)
#test_classes = [0]

feed_dict_test2 = {x: test_image, y_true: test_labels, y_true_cls: test_classes}


recognizeandplotimage(feed_dict_test2,test_image,test_classes,session,correct_prediction,y_pred_cls,img_shape)

# Finish
session.close()
exit()


# ================ Stop ! ===============================================================================================================================


##plot_mnist_test_image_at_index(data, image_index)
#exit()

## Test Dataset
#plot_mnist_test_image_at_index(data, image_index)

## Test Batch
#x_batch, y_true_batch = data.train.next_batch(3)
#print("label = %s"%y_true_batch[0].argmax())
#img = x_batch[0]
#save_grayscale_image_as_png(img, 28)
#plot_grayscale_image(img, 28)
#exit()


## Extract MNIST Numeric Training Images from Dataset

#extract_save_numeric_dataset_images(data, 100,'dataset_images/train/', 28)
#exit()
