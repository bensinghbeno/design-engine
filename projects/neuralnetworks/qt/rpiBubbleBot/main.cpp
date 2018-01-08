#include <QCoreApplication>
#include <QDebug>
#include "udpserver.h"


int main(int argc, char *argv[])
{
    QCoreApplication a(argc, argv);
    qDebug() << "----  Hello from Rpi Bubble Bot !! ------ \n Awaiting Udp Json Commands .. " ;

    UdpClient objUdpServer;

    return a.exec();
}

