# Works with the below configuration
# Ubuntu 16.04 LTS 64 bit (Guest running on VmWare)
# Tensorflow 1.7.0 
# Python 2.7.12

import sys
import matplotlib.pyplot as plt
import os
import numpy as np
import shutil
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from PIL import Image
from skimage import color
from skimage import io
from scipy.misc import imread, imsave, imresize
from scipy.misc import toimage

def ProcessCommandline():
    if (len(sys.argv) == 1):
        print("Please provide image_index number")
        exit()
            
    else:
	global image_index	
        image_index = int(sys.argv[1])
        print("image_index = %s"%image_index)
	return image_index

# Plot a greyscale image of size (pix_width_height x pix_width_height)
def plot_grayscale_image(image, pix_width_height):
    
    # This array will be of 1D with length 784
    # The pixel intensity values are integers from 0 to 255
    # Reshape the array into 28 x 28 array (2-dimensional array)
    pixels = image.reshape((pix_width_height, pix_width_height))

    plt.imshow(pixels, cmap='binary')

    plt.show()
    
def plot_grayscale_image_label(image, pix_width_height, label):

    # This array will be of 1D with length 784
    # The pixel intensity values are integers from 0 to 255
    # Reshape the array into 28 x 28 array (2-dimensional array)
    pixels = image.reshape((pix_width_height, pix_width_height))

    plt.imshow(pixels, cmap='binary')
    plt.title('Recognized Image = %s'%label)
    plt.show()

def optimize(num_iterations, data, session, optimizer, batch_size, x, y_true):
    for i in range(num_iterations):
        # Get a batch of training examples.
        # x_batch now holds a batch of images and
        # y_true_batch are the true labels for those images.
        x_batch, y_true_batch = data.train.next_batch(batch_size)
        
        # Put the batch into a dict with the proper names
        # for placeholder variables in the TensorFlow graph.
        # Note that the placeholder for y_true_cls is not set
        # because it is not used during training.
        feed_dict_train = {x: x_batch,
                           y_true: y_true_batch}

        # Run the optimizer using this batch of training data.
        # TensorFlow assigns the variables in feed_dict_train
        # to the placeholder variables and then runs the optimizer.
        session.run(optimizer, feed_dict=feed_dict_train)


def optimize_custom(num_iterations, data, session, optimizer, batch_size, x, y_true):
    for i in range(num_iterations):
        # Get a batch of training examples.
        # x_batch now holds a batch of images and
        # y_true_batch are the true labels for those images.
        x_batch, y_true_batch = data.train.next_batch(batch_size)

        # Put the batch into a dict with the proper names
        # for placeholder variables in the TensorFlow graph.
        # Note that the placeholder for y_true_cls is not set
        # because it is not used during training.
        feed_dict_train = {x: x_batch,
                           y_true: y_true_batch}

        # Run the optimizer using this batch of training data.
        # TensorFlow assigns the variables in feed_dict_train
        # to the placeholder variables and then runs the optimizer.
        session.run(optimizer, feed_dict=feed_dict_train)



def plot_images(pred_result, images, cls_true, img_shape, cls_pred=None):

    len_images = len(images)
    len_cls_true = len(cls_true)
    print("len(images) = %s"%len_images)
    print("len(cls_true) = %s"%(len_cls_true))
    assert len(images) == len(cls_true)
    
    # Create figure with 3x3 sub-plots.
    fig, axes = plt.subplots(3, 3)
    fig.subplots_adjust(hspace=0.3, wspace=0.3)

    for i, ax in enumerate(axes.flat):
        # Plot image.
        if(i < len_images):
            ax.imshow(images[i].reshape(img_shape), cmap='binary')

            # Show true and predicted classes.
            if cls_pred is None:
                xlabel = "True: {0}".format(cls_true[i])
            else:
                xlabel = "True: {0}, Pred: {1}".format(cls_true[i], cls_pred[i])

            ax.set_xlabel(xlabel)
        
            # Remove ticks from the plot.
            ax.set_xticks([])
            ax.set_yticks([])
        else:
            print("Exceeded index")
        
    # Ensure the plot is shown correctly with multiple plots
    # in a single Notebook cell.
    fig = plt.gcf()
    fig.canvas.set_window_title(pred_result) 
    plt.show()

def recognizeandplotimage(dictonary,test_images,test_classes, session, correct_prediction, y_pred_cls,img_shape):
    # Use TensorFlow to get a list of boolean values
    # whether each test-image has been correctly classified,
    # and a list for the predicted class of each image.
    correct, cls_pred = session.run([correct_prediction, y_pred_cls],
                                    feed_dict=dictonary)

    pred_result = "PREDICTION_TRUE"

    # Negate the boolean array.
    incorrect = (correct == True)
    
    # Get the images from the test-set that have been
    # incorrectly classified.
    images = (test_images)[incorrect]
    len_images = len(images)

    if(len_images == 0):
        pred_result = "PREDICTION_FALSE"
        incorrect = (correct == False)
        images = (test_images)[incorrect]
        len_images = len(images)
    
    # Get the predicted classes for those images.
    cls_pred = cls_pred[incorrect]

    # Get the true classes for those images.
    cls_true = (test_classes)[incorrect]

   
    # Plot the first 9 images.
    #plot_images(pred_result,images=images, cls_true=cls_true, img_shape=img_shape, cls_pred=cls_pred)
    print("Result : Recognized No = %s"%cls_pred[0])
    plot_grayscale_image_label(images[0], 28, cls_pred[0])



# Plot a grayscale  Image from MNIST Dataset
def plot_mnist_test_image_at_index(dataset, index):

    label = dataset.test.labels[index]
    label = label.argmax()

    # The rest of columns are pixels
    pixels = dataset.test.images[index]

    # Make those columns into a array of 8-bits pixels
    # This array will be of 1D with length 784
    # The pixel intensity values are integers from 0 to 255
    #pixels = np.array(pixels, dtype='uint8')

    # Reshape the array into 28 x 28 array (2-dimensional array)
    pixels = pixels.reshape((28, 28))

    # Plot
    plt.title('Label is {label}'.format(label=label))
    plt.imshow(pixels, cmap='binary')
    plt.show()


# Save a grayscale png image of size (pix_width_height x pix_width_height)
def save_grayscale_image_as_png(image, pix_width_height, path):

    # This array will be of 1D with length 784
    # The pixel intensity values are integers from 0 to 255
    # Reshape the array into 28 x 28 array (2-dimensional array)
    pixels = image.reshape((pix_width_height, pix_width_height))

    plt.imshow(pixels, cmap='binary')
    plt.axis('off')
    plt.savefig(path+'.png')
    plt.close()


# Extract & Save Dataset Images

def extract_save_numeric_dataset_images(dataset, image_count, dataset_path, size):


    if os.path.exists(dataset_path):
        shutil.rmtree(dataset_path)
        os.mkdir(dataset_path)
    else:
        os.mkdir(dataset_path)

    for i in range(0, 10):
        os.mkdir(dataset_path + str(i))


    x_batch, y_true_batch = dataset.train.next_batch(image_count)

    for index, im in enumerate(x_batch):
        print("index = %s"%index)
        lbl = y_true_batch[index].argmax()
        print("label = %s"%lbl)
        save_path = (dataset_path + str(lbl) + '/' + str(lbl) +'_' + str(index))
        save_grayscale_image_as_png(im, size, save_path)



def get_label_one_hot_array(value, width):

    value = int(value)
    no_columns = width
    a = np.array([value])
    b = np.zeros((1, no_columns))
    b[np.arange(1), a] = 1
    return b


def load_plot_get_greyscale_image(fname):

    image = imread(fname)

    if(len(image.shape)<3):
          print '\nImage Type :  Image is gray'
    elif len(image.shape)==3:
          print 'Image Type :  Image is Color(RGB)'
    else:
          print 'Image Type :  Image is others'


    #plt.gray()

    image = Image.open(fname).convert("L")
    arr = np.asarray(image)
    plt.imshow(arr, cmap='gray')
    flat_array = arr.reshape(1, 784)
    #print("len(flat_array) = %s"%len(flat_array))
    plt.title('Loaded Image = %s'%fname)
    plt.show()

    return flat_array