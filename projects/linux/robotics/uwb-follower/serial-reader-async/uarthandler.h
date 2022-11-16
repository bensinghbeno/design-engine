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
    SerialPortReader* mSerialPortReader1;
    QMutex mutex;
    QSerialPort* mSerial0;
    QSerialPort* mSerial1;
    QString  mRange0;
    QString  mRange1;
    QThread* mThread;
    QThread* mThread1;




signals:

public slots:

    void handleDataUpdate0(QString data);
    void handleDataUpdate1(QString data);

};

#endif // UARTHANDLER_H
