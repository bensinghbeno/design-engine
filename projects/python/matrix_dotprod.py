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

def quitProg():
	print "\n----Matrix Dot Prod Python Script Completed--\n"
	sys.exit()	

def displayRawJsonBuffer():
	print "gRawJsonStringBuffer = ",gRawJsonStringBuffer

def processRawJsonBuffer():
	global gLayerCount
	global gMasterInputCount
	global gRowCount
	global gColoumnCount

	parsedJsonString = json.loads(gRawJsonStringBuffer)
	gLayerCount = parsedJsonString['LAYERCOUNT'] 
	gMasterInputCount = parsedJsonString['MASTERINPUTCOUNT'] 
	#gRowCount = parsedJsonString['ROWCOUNT_L1']
	#gColoumnCount = parsedJsonString['COLOUMNCOUNT_L1']

	print "parsed_json['LAYERCOUNT'] = ",gLayerCount
	print "parsed_json['MASTERINPUTCOUNT'] = ",gMasterInputCount
	#print "parsed_json['ROWCOUNT_L1'] = ",gRowCount
	#print "parsed_json['COLOUMNCOUNT_L1'] = ",gColoumnCount

def evaluateMatrixComputation():
	print "START evaluateMatrixComputation()"

	if( (int(gLayerCount) < 1) or (int(gMasterInputCount) < 2)):
		print "evaluateMatrixComputation() failed, Please provide LAYERCOUNT >1 & MASTERINPUTCOUNT > 2"
		quitProg()
	else:
		print "evaluateMatrixComputation() success"



def createMasterInputArray(rows,coloumns):
	x = np.empty((1, 3), dtype=int)






## Main Routine ##
print "\n----Matrix Dot Prod Python Script Launched--\n"
processCmdLine()
processRawJsonBuffer()
evaluateMatrixComputation()
quitProg()


#json_string = '{\n    \"w00\": \"77\",\n    \"w01\": \"19\"\n}\n'
#print "json_string = ",json_string


x = np.array([ 1, 1 ,1])

w = np.array([[ 5, 1 ,3], 
              [ 1, 1 ,1], 
              [ 1, 2 ,1]])

#print w.dot(x)

#print(np.matrix(w))
#sys.exit()

x = np.array([1, 2, 3])


x = np.empty((1, 3), dtype=int)

x[0,0] = 1;
x[0,1] = 2;
x[0,2] = 3;

#print x.dot(w)

