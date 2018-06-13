# Works with the below configuration
# Ubuntu 16.04 LTS 64 bit (Guest running on VmWare)
# Tensorflow 1.7.0 
# Python 2.7.12

import sys
import matplotlib.pyplot as plt

def ProcessCommandline():
    if (len(sys.argv) == 1):
        print("Please provide image_index number")
        exit()
            
    else:
	global image_index	
        image_index = int(sys.argv[1])
        print("image_index = %s"%image_index)
	return image_index

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

   
    # Plot the first 9 images.
    plot_images(pred_result,images=images, cls_true=cls_true, img_shape=img_shape, cls_pred=cls_pred)


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


# Plot a greyscale image of size (pix_width_height x pix_width_height)
def plot_grayscale_image(image, pix_width_height):

    # This array will be of 1D with length 784
    # The pixel intensity values are integers from 0 to 255
    # Reshape the array into 28 x 28 array (2-dimensional array)
    pixels = image.reshape((pix_width_height, pix_width_height))

    plt.imshow(pixels, cmap='binary')
    plt.show()
