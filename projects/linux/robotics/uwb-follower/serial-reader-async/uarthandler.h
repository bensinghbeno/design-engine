#ifndef UARTHANDLER_H
#define UARTHANDLER_H

#include <QObject>
#include "serialportreader.h"
#include <QtSerialPort/QSerialPort>
#include <QTextStream>
#include <QCoreApplication>
#include <QFile>
#include <QStringList>
#include <QMutex>

class UartHandler : public QObject
{
    Q_OBJECT
public:
    explicit UartHandler(int argumentCount, QStringList& argumentList, QObject *parent = 0);
    SerialPortReader* mSerialPortReader0;
    QMutex mutex;
    QSerialPort* mSerial0;
    QString  mRange0;
    QString  mRange1;
    QThread* mThread;




signals:

public slots:

    void handleDataUpdate0(QString data);

};

#endif // UARTHANDLER_H
