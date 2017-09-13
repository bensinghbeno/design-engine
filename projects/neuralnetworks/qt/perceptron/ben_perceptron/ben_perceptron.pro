#-------------------------------------------------
#
# Project created by QtCreator 2017-09-03T21:27:49
#
#-------------------------------------------------

QT       += core gui

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

TARGET = ben_perceptron
TEMPLATE = app


SOURCES += main.cpp\
        mainwindow.cpp \
    perceptronoutputwidget.cpp \
    perceptronconnector.cpp \
    perceptronconnectors.cpp \
    datamodel.cpp \
    controller.cpp

HEADERS  += mainwindow.h \
    perceptronoutputwidget.h \
    perceptronconnector.h \
    perceptronconnectors.h \
    datamodel.h \
    controller.h \
    interfaces/idatamodel.h

FORMS    += mainwindow.ui
