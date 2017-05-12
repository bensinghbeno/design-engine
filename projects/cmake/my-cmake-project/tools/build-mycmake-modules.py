## @file build-mycmake-modules.py
##
## @brief
## Cross Platform Python Script to build modules from  my-cmake-project.
##
## Copyright Bensingh Beno / GNU-GPL

## declare import packages
import os
import sys
import shutil
from sys import platform

## declare global variables
global CMD_CMAKE
global CMAKE_GEN_FLAG
global MAKE_GEN_TYPE
global CMD_MAKE

## define the Build function blocks
def find_platform():
	if platform == "linux" or platform == "linux2":
		print("\n OS = Linux")
		#global CMD_CMAKE
		#global CMAKE_GEN_FLAG
		#global MAKE_GEN_TYPE
		#global CMD_MAKE
		CMD_CMAKE="cmake "
		CMAKE_GEN_FLAG=""
		CMAKE_GEN_TYPE=""
		CMD_MAKE="make "
	elif platform == "darwin":
		print("\n OS = OS X")
	elif platform == "win32":
		print("\n OS = win32")
		#global CMD_CMAKE
		#global CMAKE_GEN_FLAG
		#global MAKE_GEN_TYPE
		#global CMD_MAKE
		CMAKE_GEN_FLAG="-G "
		CMAKE_GEN_TYPE='"MinGW Makefiles" '
		CMD_MAKE="mingw32-make "
		CMD_CMAKE="cmake "

	
def build_default():
	print " build_default().\n"
	os.chdir("../build/")
	os.system(CMD_CMAKE+CMAKE_GEN_FLAG+CMAKE_GEN_TYPE+"../modules/ ")
	os.system(CMD_MAKE)
	
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
find_platform()
	
if (len(sys.argv) == 1):
	options["default"]()
else:	
	options[sys.argv[1]]()






## Backups
##print "This is the name of the script: ", sys.argv[0]
##print "Number of arguments: ", len(sys.argv)
##print "The arguments are: " , str(sys.argv)
#cmake='cmake -G "MinGW Makefiles"'
