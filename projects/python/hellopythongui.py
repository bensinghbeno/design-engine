#!/usr/bin/python
## @file hellopython.py
##
## @brief
## A demo script for python dummies.
##
## Copyright Bensingh Beno / GNU-GPL

## declare import packages
from PyQt4 import QtGui
import sys



  

## Main Script

print('Hello PythonGui')

def window():
 app = QtGui.QApplication(sys.argv)
 w = QtGui.QWidget()
 b = QtGui.QLabel(w)
 b.setText("Hello World!")
 w.setGeometry(100,100,200,50)
 b.move(50,20)
 w.setWindowTitle("PyQt")
 w.show()
 sys.exit(app.exec_())

if __name__ == '__main__':
 window()





