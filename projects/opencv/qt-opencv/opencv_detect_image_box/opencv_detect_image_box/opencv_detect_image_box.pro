QT += core
QT -= gui

TARGET = opencv_detect_image_box
CONFIG += console
CONFIG -= app_bundle

TEMPLATE = app

SOURCES += main.cpp

CONFIG += link_pkgconfig
PKGCONFIG += opencv

