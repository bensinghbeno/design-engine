#-------------------------------------------------
#
# Project created by QtCreator 2018-01-07T21:11:25
#
#-------------------------------------------------

QT       += core gui network


greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

TARGET = rpiCommander
TEMPLATE = app


SOURCES += main.cpp\
        mainwindow.cpp \
    ../perceptron2/perceptronjsonterminal.cpp \
    ../perceptron2/perceptronjsonmodel.cpp \
    udpclient.cpp

HEADERS  += mainwindow.h \
    ../perceptron2/perceptronjsonterminal.h \
    ../perceptron2/perceptronjsonmodel.h \
    udpclient.h

FORMS    += mainwindow.ui
