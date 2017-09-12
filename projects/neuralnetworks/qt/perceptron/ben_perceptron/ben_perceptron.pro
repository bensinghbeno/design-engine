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
    perceptronconnectors.cpp

HEADERS  += mainwindow.h \
    perceptronoutputwidget.h \
    perceptronconnector.h \
    perceptronconnectors.h

FORMS    += mainwindow.ui
