#-------------------------------------------------
#
# Project created by QtCreator 2018-01-07T21:11:25
#
#-------------------------------------------------

QT       += core gui network

CONFIG += c++11

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

TARGET = bubbleCommander
TEMPLATE = app


SOURCES += main.cpp\
        mainwindow.cpp \
    logicmodel.cpp \
    controller.cpp \
    httpgetclient.cpp \
    backgroundworker.cpp \
    ../udp/udpclient/udpclientapp/udpclient.cpp

HEADERS  += mainwindow.h \
    logicmodel.h \
    interfaceenums.h \
    controller.h \
    httpgetclient.h \
    backgroundworker.h \
    ../udp/udpclient/udpclientapp/udpclient.h

FORMS    += mainwindow.ui
