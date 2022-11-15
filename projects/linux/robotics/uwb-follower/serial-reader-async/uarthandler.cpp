#include "uarthandler.h"
#include <QDebug>
#include <QThread>

UartHandler::UartHandler(int argumentCount, QStringList &argumentList, QObject *parent) : QObject(parent)
{
    qDebug() << "Launch Serial Handler";
    mThread = new QThread();
    mSerialPortReader0 = new SerialPortReader();
    mSerialPortReader0->moveToThread(mThread);


    connect( mThread, &QThread::started, mSerialPortReader0, &SerialPortReader::process);
    connect( mSerialPortReader0, &SerialPortReader::updateData, this, &UartHandler::handleDataUpdate0);


    mThread->start();
}

void UartHandler::handleDataUpdate0(QString data)
{
    mutex.lock();
    mRange0 = data;

    qDebug() << "==== UartHandler - Range 0 :: "  << mRange0;

    mutex.unlock();

}

