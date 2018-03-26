QT       += core gui websockets

QT += widgets

TARGET = echoserver

TEMPLATE = app

SOURCES += \
    main.cpp \
    echoserver.cpp \
    mainwindow.cpp

HEADERS += \
    echoserver.h \
    mainwindow.h

OTHER_FILES += echoclient.html

FORMS += \
    dialog.ui
