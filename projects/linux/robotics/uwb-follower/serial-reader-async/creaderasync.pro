QT = core
QT += serialport

CONFIG += console
CONFIG -= app_bundle

TARGET = creaderasync
TEMPLATE = app

HEADERS += \
    serialportreader.h \
    uarthandler.h

SOURCES += \
    main.cpp \
    serialportreader.cpp \
    uarthandler.cpp

target.path = $$[QT_INSTALL_EXAMPLES]/serialport/creaderasync
INSTALLS += target
