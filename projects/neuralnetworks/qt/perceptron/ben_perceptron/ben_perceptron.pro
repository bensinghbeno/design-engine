#-------------------------------------------------
#
# Project created by QtCreator 2017-09-03T21:27:49
#
#-------------------------------------------------

QT       += core gui

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

TARGET = ben_perceptron
TEMPLATE = app
QMAKE_CXXFLAGS += -std=c++11

SOURCES += main.cpp\
        mainwindow.cpp \
    perceptronconnector.cpp \
    perceptronconnectors.cpp \
    datamodel.cpp \
    controller.cpp \
    perceptronwidget.cpp

HEADERS  += mainwindow.h \
    perceptronconnector.h \
    perceptronconnectors.h \
    datamodel.h \
    controller.h \
    interfaces/idatamodel.h \
    perceptronwidget.h \
    ../../../../qt/MyQtUtils/myqttypes.h

FORMS    += mainwindow.ui
