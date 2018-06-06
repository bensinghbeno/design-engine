# Works with the below configuration
# Ubuntu 16.04 LTS 64 bit (Guest running on VmWare)
# Tensorflow 1.7.0 
# Python 2.7.12

import matplotlib.pyplot as plt
import tensorflow as tf
import numpy as np
import sys



def ProcessCommandline():

    if (len(sys.argv) == 1):
        print("Please provide image_index number")
        exit()
    else:
        image_index = int(sys.argv[1])
        print("image_index = %s"%image_index)
