QT       += core gui websockets widgets

TARGET = ForeviewIotWebServer

TEMPLATE = app

SOURCES += \
    main.cpp \
    mainwindow.cpp \
    webserver.cpp \
    udpserver.cpp \
    ../../../neuralnetworks/qt/perceptron2/perceptronjsonmodel.cpp \
    ../../../neuralnetworks/qt/perceptron2/perceptronjsonterminal.cpp

HEADERS += \
    mainwindow.h \
    webserver.h \
    udpserver.h \
    ../../../neuralnetworks/qt/perceptron2/perceptronjsonmodel.h \
    ../../../neuralnetworks/qt/perceptron2/perceptronjsonterminal.h

OTHER_FILES += echoclient.html

FORMS += \
    dialog.ui
