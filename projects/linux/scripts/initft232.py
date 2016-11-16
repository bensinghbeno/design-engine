#!/usr/bin/python

import subprocess
import sys
import os



#string = sys.argv[1]
#print string

array = []

cmd = subprocess.Popen('lsusb', shell=True, stdout=subprocess.PIPE)
for line in cmd.stdout:

    if "FT232" in line:
	        print line
	        array.append(line.split(' '))
	        usbctrlno = array[0][1] 
		print "usbctrlno = "+usbctrlno
	        #print usbctrlno
	        usbdevno = array[0][3] 
		usbdevno = usbdevno[:-1] # remove last character
		print "usbdevno = "+usbdevno
		

os.system('sudo chmod 777 /dev/bus/usb/'+usbctrlno+'/'+usbdevno)
