#! /usr/bin/python

import sys
import numpy as np
import json

def processCmdLine():
	if (len(sys.argv) == 2):
		print "arg1 = ",sys.argv[1]
		global gRawJsonStringBuffer
		gRawJsonStringBuffer = sys.argv[1]
	else:	
		print "arg1 is invalid "


def displayRawJsonBuffer():
	print "gRawJsonStringBuffer = ",gRawJsonStringBuffer


## Main Routine ##
<<<<<<< fdfb206807633139196c8c4815bee3ac2b171628
print "\n\n----Matrix Dot Prod Python Script Launched--\n"
processCmdLine()
displayRawJsonBuffer()
=======
print "\n----Matrix Dot Prod Python Script Launched--\n"
processCmdLine()
displayRawJsonBuffer()
print "\n----Matrix Dot Prod Python Script Completed--\n"
sys.exit()
>>>>>>> perceptron2: qt-> python init via json


#json_string = '{\n    \"w00\": \"77\",\n    \"w01\": \"19\"\n}\n'
#print "json_string = ",json_string

json_string =  gRawJsonStringBuffer
parsed_json = json.loads(json_string)
print "parsed_json['w00'] = ",parsed_json['w00']

w = np.array([[ 5, 1 ,3], 
              [ 1, 1 ,1], 
              [ 1, 2 ,1]])

x = np.array([1, 2, 3])


x = np.empty((1, 3), dtype=int)

x[0,0] = 1;
x[0,1] = 2;
x[0,2] = 3;

#print x.dot(w)

