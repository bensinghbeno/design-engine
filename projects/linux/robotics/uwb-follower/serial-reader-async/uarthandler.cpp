#include "uarthandler.h"
#include <QDebug>
#include <QThread>
#include <wiringPi.h> // Include WiringPi library!


UartHandler::UartHandler(int argumentCount, QStringList &argumentList, QObject *parent) : QObject(parent)
{
    qDebug() << "Launch Serial Handler";
    wiringPiSetupGpio(); // Initialize wiringPi -- using Broadcom pin numbers
    
    pinMode(20, OUTPUT);     // Set regular LED as output
    pinMode(21, OUTPUT);     // Set regular LED as output

    mThread = new QThread();
    mSerialPortReader0 = new SerialPortReader("ttyUSB0");
    mSerialPortReader0->moveToThread(mThread);

    mThread1 = new QThread();
    mSerialPortReader1 = new SerialPortReader("ttyUSB1");
    mSerialPortReader1->moveToThread(mThread1);


    connect( mThread, &QThread::started, mSerialPortReader0, &SerialPortReader::process);
    connect( mSerialPortReader0, &SerialPortReader::updateData, this, &UartHandler::handleDataUpdate0);

    connect( mThread1, &QThread::started, mSerialPortReader1, &SerialPortReader::process);
    connect( mSerialPortReader1, &SerialPortReader::updateData, this, &UartHandler::handleDataUpdate1);


    mThread->start();
    mThread1->start();
    
    //mThread->wait();
    //mThread1->wait();
}

void UartHandler::handleDataUpdate0(QString data)
{
    mutex.lock();
    //mRange0 = data;

    nRange0 = data.toFloat();

    //qDebug() << "Range 0 :: "  << nRange0;

    mutex.unlock();
}

void UartHandler::handleDataUpdate1(QString data)
{
    mutex.lock();
    //mRange1 = data;

    nRange1 = data.toFloat();

    //qDebug() << "Range 1 :: "  << nRange1;
    
    float diff = (nRange0 - nRange1);
    
    qDebug() << "DIFF :: "  << diff;

    // // DIRECTION // //
    if ((nRange0 > 2.5) || (nRange1 > 2.5))
    {
        if (diff > 0.33)
        {
            qDebug() << "LEFT ";
        }
        else if (diff< (-(0.33)))
        {
            qDebug() << "RIGHT";
        }
        else
        {
            qDebug() << "FORWARD";
            digitalWrite(20, HIGH);  
            digitalWrite(21, HIGH);    
        }
    }
    else
        {
            qDebug() << "STOP";
            digitalWrite(20, LOW);  
            digitalWrite(21, LOW); 
        }


    mutex.unlock();
}


