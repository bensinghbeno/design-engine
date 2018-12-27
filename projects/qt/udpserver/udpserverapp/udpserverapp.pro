#-------------------------------------------------
#
# Project created by QtCreator 2018-12-26T20:56:19
#
#-------------------------------------------------

QT       += core gui network

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

TARGET = udpserverapp
TEMPLATE = app

CONFIG += c++11



SOURCES += main.cpp\
        mainwindow.cpp \
    udpserver.cpp

HEADERS  += mainwindow.h \
    udpserver.h

FORMS    += mainwindow.ui
