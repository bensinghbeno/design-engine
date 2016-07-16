QT += core
QT -= gui

CONFIG += c++11

TARGET = TestCpp
CONFIG += console
CONFIG -= app_bundle

TEMPLATE = app

SOURCES += main.cpp \
    utils.cpp \
    myclass.cpp \
    observerAlpha.cpp \
    observerBeta.cpp \
    base.cpp \
    derived.cpp \
    mainapplication.cpp \
    eventengine.c

HEADERS += \
    utils.h \
    myclass.h \
    observerAlpha.h \
    observerBeta.h \
    base.h \
    derived.h \
    mainapplication.h \
    eventengine.h

INCLUDEPATH += /usr/include/dbus-1.0/
INCLUDEPATH += /usr/lib/x86_64-linux-gnu/dbus-1.0/include/
INCLUDEPATH += /usr/include/glib-2.0/
INCLUDEPATH += /usr/lib/x86_64-linux-gnu/glib-2.0/include/

LIBS += -ldbus-1
LIBS += -ldbus-glib-1
