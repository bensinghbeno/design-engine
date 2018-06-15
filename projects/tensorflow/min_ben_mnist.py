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
from skimage import color
from skimage import io
from scipy.misc import imread, imsave, imresize
import cv2
from scipy.misc import toimage

from PIL import Image
from min_ben_mnist_functions import ProcessCommandline
from min_ben_mnist_functions import plot_images
from min_ben_mnist_functions import optimize
from min_ben_mnist_functions import recognizeandplotimage
from min_ben_mnist_functions import plot_mnist_test_image_at_index
from min_ben_mnist_functions import plot_grayscale_image
from min_ben_mnist_functions import save_grayscale_image_as_png
from min_ben_mnist_functions import extract_save_numeric_dataset_images

# Process Commandline
image_index = ProcessCommandline()

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


x_batch, y_true_batch = data.train.next_batch(3)
imarray = np.array(x_batch[0])
imarray = imarray.reshape(28, 28)

plt.gray()
plt.imshow(imarray)
plt.show()

im = toimage(imarray)
im.save("foobar.png")
exit()



plt.axis('off')
plt.savefig('gray_plot.png')
plt.close()


im = Image.fromarray(imarray)
im.show()



def load_plot_greyscale_image(image_path):



#    img = cv2.imread(image_path)
#    img = cv2.cvtColor( img, cv2.COLOR_RGB2GRAY )
#    cv2.imwrite( "grey.png", img )

    image = imread("grey.png")

    if(len(image.shape)<3):
          print 'gray'
    elif len(image.shape)==3:
          print 'Color(RGB)'
    else:
          print 'others'


    plt.imshow(image, cmap='binary')
    plt.show()
    exit()

    #im = mpimg.imread(image_path)
    im = color.rgb2gray(io.imread(image_path))
    imarray = np.array(im)
    imarray = imarray.reshape(784, 1)
    plot_grayscale_image(imarray, 28)


load_plot_greyscale_image('dataset_images/train/2/2_11.png')
exit()

#extract_save_numeric_dataset_images(data, 100,'dataset_images/train/', 28)


#x_batch, y_true_batch = data.train.next_batch(batch_size)

#size = 3
#depth = 10

#a = np.array([])
#a = np.append(a,1)
#a = np.append(a,2)
#a = np.append(a,3)
#a = a.astype(int)

#print("array = %s"%a)

#b = np.zeros((size, 10))
#b[np.arange(size), a] = 1

#print("array = %s"%b[0])
#print("\narray[0] = %s"%b)

#exit()


## Extract & Save Dataset Images

#def extract_save_numeric_dataset_images(dataset, image_count, dataset_path, size):


#    if os.path.exists(dataset_path):
#        shutil.rmtree(dataset_path)
#        os.mkdir(dataset_path)
#    else:
#        os.mkdir(dataset_path)

#    for i in range(0, 10):
#        os.mkdir(dataset_path + str(i))


#    x_batch, y_true_batch = dataset.train.next_batch(image_count)

#    for index, im in enumerate(x_batch):
#        print("index = %s"%index)
#        lbl = y_true_batch[index].argmax()
#        print("label = %s"%lbl)
#        save_path = (dataset_path + str(lbl) + '/' + str(lbl) +'_' + str(index))
#        save_grayscale_image_as_png(im, size, save_path)

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

test_image = data.test.images[(image_index-1):image_index]
test_labels = data.test.labels[(image_index-1):image_index]
test_classes = data.test.cls[(image_index-1):image_index]
feed_dict_test2 = {x: test_images, y_true: test_labels, y_true_cls: test_classes}


recognizeandplotimage(feed_dict_test2,test_image,test_classes,session,correct_prediction,y_pred_cls,img_shape)

# Finish
session.close()
exit()





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
