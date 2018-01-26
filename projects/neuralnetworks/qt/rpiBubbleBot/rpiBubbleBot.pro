QT += core
QT -= gui
QT += network

TARGET = rpiBubbleBot
CONFIG += console
CONFIG -= app_bundle

TEMPLATE = app

SOURCES += main.cpp \
    udpserver.cpp \
    ../perceptron2/perceptronjsonterminal.cpp \
    ../perceptron2/perceptronjsonmodel.cpp

target.path = /home/pi
INSTALLS += target

HEADERS += \
    udpserver.h \
    ../perceptron2/perceptronjsonterminal.h \
    ../perceptron2/perceptronjsonmodel.h \
    pigpio.h

QMAKE_LFLAGS += -lpigpio -lrt -lpthread

