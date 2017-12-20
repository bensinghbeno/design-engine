#-------------------------------------------------
#
# Project created by QtCreator 2017-11-05T10:47:09
#
#-------------------------------------------------

QT       += core gui

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

TARGET = perceptron2
TEMPLATE = app
QMAKE_CXXFLAGS += -std=c++11


SOURCES += main.cpp\
    perceptronwidget.cpp \
    perceptroncontroller.cpp \
    perceptronjsonmodel.cpp \
    perceptronjsonterminal.cpp

HEADERS  += \
    perceptronwidget.h \
    perceptroncontroller.h \
    perceptronjsonmodel.h \
    perceptronjsonterminal.h
