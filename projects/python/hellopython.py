#!/usr/bin/python
## @file hellopython.py
##
## @brief
## A demo script for python dummies.
##
## Copyright Bensingh Beno / GNU-GPL

## declare import packages
import sys

## declare global variables
global GLOBAL_VAR

## define functions

def disp_python_version(): 
  GLOBAL_VAR=sys.version
  return  GLOBAL_VAR;

  

## Main Script

print('Hello Python')
print('disp_python_version() = %s' %disp_python_version());




