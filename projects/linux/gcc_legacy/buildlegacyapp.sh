#!/bin/bash
echo "========Hello Legacy Build Script====="
rm -rf app.out displayconsole.c~ displayconsole.o main.o core
echo " Cleaning Finished"
gcc -c -g main.c
gcc -c -g -fpic displayconsole.c
gcc -shared -o libdisplayconsole.so displayconsole.o
echo " Build Finished"
gcc -o app.out main.o -L. -ldisplayconsole
echo "=====Linking Finished, App is available====="
