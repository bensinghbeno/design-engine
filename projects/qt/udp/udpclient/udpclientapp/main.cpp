#include "mainwindow.h"
#include <QApplication>
#include "udpclient.h"


int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
    MainWindow w;
    w.show();

    UdpClient objUdpClient;

    QObject::connect(&w,SIGNAL(sgnIpChanged(QString)),&objUdpClient,SLOT(sltSetIp(QString)));
    QObject::connect(&w,SIGNAL(sgnPortChanged(quint16)),&objUdpClient,SLOT(sltSetPort(quint16)));
    QObject::connect(&w,SIGNAL(sgnSendData(QString)),&objUdpClient,SLOT(sltWriteDatagram(QString)));


    return a.exec();
}
