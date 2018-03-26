QT       += core gui websockets widgets

TARGET = ForeviewIotWebServer

TEMPLATE = app

SOURCES += \
    main.cpp \
    mainwindow.cpp \
    webserver.cpp \
    udpserver.cpp

HEADERS += \
    mainwindow.h \
    webserver.h \
    udpserver.h

OTHER_FILES += echoclient.html

FORMS += \
    dialog.ui
