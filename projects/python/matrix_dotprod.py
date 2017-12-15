#! /usr/bin/python

import sys
import numpy as np
import json

def processCmdLine():
	if (len(sys.argv) == 2):
		#print "arg1 = ",sys.argv[1]
		global gRawJsonStringBuffer
		gRawJsonStringBuffer = sys.argv[1]
	else:	
		print "arg1 is invalid "


def displayRawJsonBuffer():
	print "gRawJsonStringBuffer = ",gRawJsonStringBuffer

def procesRawJsonBuffer():
	parsedJsonString = json.loads(gRawJsonStringBuffer)
	print "parsed_json['LAYERCOUNT'] = ",parsedJsonString['LAYERCOUNT']
	print "parsed_json['ROWCOUNT_L1'] = ",parsedJsonString['ROWCOUNT_L1']
	print "parsed_json['COLOUMNCOUNT_L1'] = ",parsedJsonString['COLOUMNCOUNT_L1']

def createNumpyArray(rows,coloumns):
	x = np.empty((1, 3), dtype=int)





#json_string = '{\n    \"w00\": \"77\",\n    \"w01\": \"19\"\n}\n'
#print "json_string = ",json_string



w = np.array([[ 5, 1 ,3], 
              [ 1, 1 ,1], 
              [ 1, 2 ,1]])

print(np.matrix(w))
sys.exit()

x = np.array([1, 2, 3])


x = np.empty((1, 3), dtype=int)

x[0,0] = 1;
x[0,1] = 2;
x[0,2] = 3;

#print x.dot(w)

## Main Routine ##
print "\n----Matrix Dot Prod Python Script Launched--\n"
processCmdLine()
#displayRawJsonBuffer()
procesRawJsonBuffer()

print "\n----Matrix Dot Prod Python Script Completed--\n"

