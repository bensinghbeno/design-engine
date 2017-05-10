## @file build-mycmake-modules.py
##
## @brief
## Cross Platform Python Script to build modules from  my-cmake-project.
##
## Copyright Bensingh Beno / GNU-GPL

import os
import sys
import shutil


## define the Build function blocks
def build_default():
	print " build_default().\n"
	os.chdir("../build/")
	os.system("cmake ../modules/")
	os.system("make")
def build_clean():
	print " build_clean().\n"
	shutil.rmtree('../build')
	os.makedirs('../build')
	
	
## Map the command line options to the build function blocks
options = { "clean" 	: build_clean,
			"default"	: build_default
}


## Main Routine
print("\n ===== Warm Greetings from Ben's CMAKE Project Build System ====")

if (len(sys.argv) == 1):
	options["default"]()
else:	
	options[sys.argv[1]]()






## Backups
##print "This is the name of the script: ", sys.argv[0]
##print "Number of arguments: ", len(sys.argv)
##print "The arguments are: " , str(sys.argv)
