#-------------------------------------------------
#
# Project created by QtCreator 2017-04-05T09:27:22
#
#-------------------------------------------------

QT       += core

QT       -= gui

TARGET = myconsole
CONFIG   += console
CONFIG   -= app_bundle

TEMPLATE = app


SOURCES += main.cpp \
    cmyclass.cpp

INCLUDEPATH += /home/ben/engine/design-engine/projects/qt/TestCpp

HEADERS += \
    backtracelogger.h \
    cmyclass.h \
    ../utils.h

#QMAKE_CXXFLAGS += -rdynamic
#QMAKE_LFLAGS   += -g -rdynamic
DEFINES += _CPP_UTIL_GENERIC

