# Works with the below configuration
# Ubuntu 16.04 LTS 64 bit (Guest running on VmWare)
# Tensorflow 1.7.0 
# Python 2.7.12

import matplotlib.pyplot as plt
import tensorflow as tf
import numpy as np
import sys

# Process Commandline
image_index = 0
if (len(sys.argv) == 1):
    print("Please provide image_index number")
    exit()
	
else:	
    image_index = int(sys.argv[1])
    print("image_index = %s"%image_index)


# Import Input data Images
from tensorflow.examples.tutorials.mnist import input_data
data = input_data.read_data_sets("data/MNIST/", one_hot=True)
data.test.cls = np.array([label.argmax() for label in data.test.labels])

# We know that MNIST images are 28 pixels in each dimension.
img_size = 28

# Images are stored in one-dimensional arrays of this length.
img_size_flat = img_size * img_size

# Tuple with height and width of images used to reshape arrays.
img_shape = (img_size, img_size)

# Number of classes, one class for each of 10 digits.
num_classes = 10

# Placeholder variables

x = tf.placeholder(tf.float32, [None, img_size_flat])

y_true = tf.placeholder(tf.float32, [None, num_classes])

y_true_cls = tf.placeholder(tf.int64, [None])


# Variables to be optimizeda

weights = tf.Variable(tf.zeros([img_size_flat, num_classes]))

biases = tf.Variable(tf.zeros([num_classes]))

#Model

logits = tf.matmul(x, weights) + biases

y_pred = tf.nn.softmax(logits)

y_pred_cls = tf.argmax(y_pred, axis=1)

cross_entropy = tf.nn.softmax_cross_entropy_with_logits(logits=logits,
                                                        labels=y_true)
# Cost-function to be optimized
cost = tf.reduce_mean(cross_entropy)

# Optimization method
optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.5).minimize(cost)

# Performance measures

correct_prediction = tf.equal(y_pred_cls, y_true_cls)

accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))



session = tf.Session()
session.run(tf.global_variables_initializer())



feed_dict_test = {x: data.test.images,
                  y_true: data.test.labels,
                  y_true_cls: data.test.cls}


def plot_images(images, cls_true, cls_pred=None):

    print("len(images) = %s"%(len(images)))
    print("len(cls_true) = %s"%(len(cls_true)))
    assert len(images) == len(cls_true) == 9
    
    # Create figure with 3x3 sub-plots.
    fig, axes = plt.subplots(3, 3)
    fig.subplots_adjust(hspace=0.3, wspace=0.3)

    for i, ax in enumerate(axes.flat):
        # Plot image.
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
        
    # Ensure the plot is shown correctly with multiple plots
    # in a single Notebook cell.
    plt.show()


def disp_img(img):
    plt.imshow(img, cmap='binary')




batch_size = 100

def optimize(num_iterations):
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

def print_accuracy():
    # Use TensorFlow to compute the accuracy.
    acc = session.run(accuracy, feed_dict=feed_dict_test)
    
    # Print the accuracy.
    print("Accuracy on test-set: {0:.1%}".format(acc))

def plot_example_errors():
    # Use TensorFlow to get a list of boolean values
    # whether each test-image has been correctly classified,
    # and a list for the predicted class of each image.
    correct, cls_pred = session.run([correct_prediction, y_pred_cls],
                                    feed_dict=feed_dict_test)

    # Negate the boolean array.
    incorrect = (correct == False)
    
    # Get the images from the test-set that have been
    # incorrectly classified.
    images = data.test.images[incorrect]
    
    # Get the predicted classes for those images.
    cls_pred = cls_pred[incorrect]

    # Get the true classes for those images.
    cls_true = data.test.cls[incorrect]
    
    # Plot the first 9 images.
    plot_images(images=images[0:9],
                cls_true=cls_true[0:9],
                cls_pred=cls_pred[0:9])


def plot_weights():
    # Get the values for the weights from the TensorFlow variable.
    w = session.run(weights)
    
    # Get the lowest and highest values for the weights.
    # This is used to correct the colour intensity across
    # the images so they can be compared with each other.
    w_min = np.min(w)
    w_max = np.max(w)

    # Create figure with 3x4 sub-plots,
    # where the last 2 sub-plots are unused.
    fig, axes = plt.subplots(3, 4)
    fig.subplots_adjust(hspace=0.3, wspace=0.3)

    for i, ax in enumerate(axes.flat):
        # Only use the weights for the first 10 sub-plots.
        if i<10:
            # Get the weights for the i'th digit and reshape it.
            # Note that w.shape == (img_size_flat, 10)
            image = w[:, i].reshape(img_shape)

            # Set the label for the sub-plot.
            ax.set_xlabel("Weights: {0}".format(i))

            # Plot the image.
            ax.imshow(image, vmin=w_min, vmax=w_max, cmap='seismic')

        # Remove ticks from each sub-plot.
        ax.set_xticks([])
        ax.set_yticks([])
        
    # Ensure the plot is shown correctly with multiple plots
    # in a single Notebook cell.
    plt.show()


# Performance after 10 optimization iterations

optimize(num_iterations=10)
#print_accuracy()

def plot_images2(pred_result, images, cls_true, cls_pred=None):

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


def disp_img(img):
    plt.imshow(img, cmap='binary')

def plot_example_true(dictonary,test_images,test_classes):
    # Use TensorFlow to get a list of boolean values
    # whether each test-image has been correctly classified,
    # and a list for the predicted class of each image.
    correct, cls_pred = session.run([correct_prediction, y_pred_cls],
                                    feed_dict=dictonary)

    pred_result = "PREDICTION_TRUE"

    # Negate the boolean array.
    incorrect = (correct == True)
    print("len(incorrect) = %s"%(len(incorrect)))
    
    # Get the images from the test-set that have been
    # incorrectly classified.
    images = (test_images)[incorrect]
    len_images = len(images)
    print("len(images) = %s"%len_images)

    if(len_images == 0):
        print("INFO: PREDICTION_FALSE")
        pred_result = "PREDICTION_FALSE"
        incorrect = (correct == False)
        images = (test_images)[incorrect]
        len_images = len(images)
        print("len(images) = %s"%len_images)
    
    # Get the predicted classes for those images.
    cls_pred = cls_pred[incorrect]
    print("len(cls_pred) = %s"%(len(cls_pred)))

    # Get the true classes for those images.
    cls_true = (test_classes)[incorrect]
    print("len(cls_true) = %s"%(len(cls_true)))

    #plt.imshow(images[0].reshape(28,28), cmap='binary')
    #plt.xlabel("LABEL")
    #plt.show()
    
    # Plot the first 9 images.
    plot_images2(pred_result,
                images=images,
                cls_true=cls_true,
                cls_pred=cls_pred)


test_images = data.test.images[(image_index-1):image_index]
test_labels = data.test.labels[(image_index-1):image_index]
test_classes = data.test.cls[(image_index-1):image_index]
feed_dict_test2 = {x: test_images,
                  y_true: test_labels,
                  y_true_cls: test_classes}

plot_example_true(feed_dict_test2,test_images,test_classes)



#plt.imshow(data.test.images[0].reshape(28,28), cmap='binary')
#plt.show()

#save
saver = tf.train.Saver()
save_path = saver.save(session, "/home/ben/engine/design-engine/projects/tensorflow/saved_models/ben_model_1.ckpt")

# Finish
#session.close()
exit()
