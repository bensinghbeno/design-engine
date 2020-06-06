#include "mytcpserver.h"

MyTcpServer::MyTcpServer(QObject *parent) :
    QObject(parent)
  , ip("192.168.0.74")
//  , ip("127.0.0.1")
  , port(4444)
{
    server = new QTcpServer(this);

    // whenever a user connects, it will emit signal
    connect(server, SIGNAL(newConnection()),
            this, SLOT(newConnection()));

    if(!server->listen(QHostAddress(ip), port))
    {
        qDebug() << "Server could not start";
    }
    else
    {
        qDebug() << "Server started!";
        qDebug() << "Listening on ip :" << ip.toStdString().c_str() << " port : " << port;

    }
}

void MyTcpServer::newConnection()
{
    qDebug() << "MyTcpServer::newConnection()!";

    // need to grab the socket
    QTcpSocket *socket = server->nextPendingConnection();

    socket->write("Hello client\r\n");
    socket->flush();

    socket->waitForBytesWritten(3000);

    socket->close();
}
