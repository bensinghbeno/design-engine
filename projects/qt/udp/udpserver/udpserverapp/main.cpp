#include "mainwindow.h"
#include <QApplication>
#include "udpserver.h"
#include <QDebug>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
    MainWindow w;

    UdpServer objUdpServer(7777);

    w.sltSetIp(objUdpServer.getDeviceIpString());
    w.sltSetPort(objUdpServer.getDevicePort());
    w.show();

    QObject::connect(&objUdpServer,SIGNAL(sgnUdpMessageReceived(QString)),&w,SLOT(sltSetMessage(QString)));

    return a.exec();
}
