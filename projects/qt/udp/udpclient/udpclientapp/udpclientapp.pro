#-------------------------------------------------
#
# Project created by QtCreator 2018-12-27T21:01:43
#
#-------------------------------------------------

QT       += core gui network

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

TARGET = udpclientapp
TEMPLATE = app


SOURCES += main.cpp\
        mainwindow.cpp \
    udpclient.cpp

HEADERS  += mainwindow.h \
    udpclient.h

FORMS    += mainwindow.ui
