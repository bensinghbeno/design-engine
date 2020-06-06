#include <QCoreApplication>
#include <QDebug>
#include "tcpclient.h"

int main(int argc, char *argv[])
{
    QCoreApplication a(argc, argv);

    qDebug() << "Launched TcpClient";

    TcpClient objTcpClient;

    return a.exec();
}
