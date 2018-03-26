QT       += core gui websockets widgets

TARGET = ForeviewIotWebServer

TEMPLATE = app

SOURCES += \
    main.cpp \
    mainwindow.cpp \
    webserver.cpp

HEADERS += \
    mainwindow.h \
    webserver.h

OTHER_FILES += echoclient.html

FORMS += \
    dialog.ui
