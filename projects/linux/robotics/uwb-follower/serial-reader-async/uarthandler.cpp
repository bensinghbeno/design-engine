#include "uarthandler.h"
#include <QDebug>
#include <QThread>

UartHandler::UartHandler(int argumentCount, QStringList &argumentList, QObject *parent) : QObject(parent)
{
    qDebug() << "Launch Serial Handler";
    mThread = new QThread();
    mSerialPortReader0 = new SerialPortReader("ttyUSB0");
    mSerialPortReader0->moveToThread(mThread);

//    mThread1 = new QThread();
//    mSerialPortReader1 = new SerialPortReader();
//    mSerialPortReader1->moveToThread(mThread1);


    connect( mThread, &QThread::started, mSerialPortReader0, &SerialPortReader::process);
    connect( mSerialPortReader0, &SerialPortReader::updateData, this, &UartHandler::handleDataUpdate0);

//    connect( mThread1, &QThread::started, mSerialPortReader1, &SerialPortReader::process);
//    connect( mSerialPortReader1, &SerialPortReader::updateData, this, &UartHandler::handleDataUpdate1);


    mThread->start();
    //mThread1->start();
}

void UartHandler::handleDataUpdate0(QString data)
{
    mutex.lock();
    mRange0 = data;

    qDebug() << "==== UartHandler - Range 0 :: "  << mRange0;

    mutex.unlock();

}

