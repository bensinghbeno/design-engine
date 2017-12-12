#! /usr/bin/python

import numpy as np

w = np.array([[ 5, 1 ,3], 
              [ 1, 1 ,1], 
              [ 1, 2 ,1]])

x = np.array([1, 2, 3])

print w.dot(x)

