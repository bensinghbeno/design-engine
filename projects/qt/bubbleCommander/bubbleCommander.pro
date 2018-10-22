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
    ../perceptron2/perceptronjsonterminal.cpp \
    ../perceptron2/perceptronjsonmodel.cpp \
    udpclient.cpp \
    logicmodel.cpp \
    controller.cpp \
    httpgetclient.cpp \
    backgroundworker.cpp

HEADERS  += mainwindow.h \
    ../perceptron2/perceptronjsonterminal.h \
    ../perceptron2/perceptronjsonmodel.h \
    udpclient.h \
    logicmodel.h \
    interfaceenums.h \
    controller.h \
    httpgetclient.h \
    backgroundworker.h

FORMS    += mainwindow.ui
