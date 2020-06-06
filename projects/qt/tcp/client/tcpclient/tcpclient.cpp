#include "tcpclient.h"
#include <QDebug>
#include <QHostAddress>

TcpClient::TcpClient() :
    _socket(this)
  , ip("192.168.0.74")
//  , ip("127.0.0.1")
  , port(4444)
{
    qDebug() << "TcpClient::TcpClient()";

    _socket.connectToHost(QHostAddress(ip), port);
    connect(&_socket, SIGNAL(readyRead()), this, SLOT(onReadyRead()));

    qDebug() << "Connecting on ip :" << ip.toStdString().c_str() << " port : " << port;
}

TcpClient::~TcpClient()
{
}

void TcpClient::onReadyRead()
{
    qDebug() << "TcpClient::onReadyRead()";

    QByteArray datas = _socket.readAll();
    qDebug() << "Received From Server " << datas;
    _socket.write(QByteArray("ok !\n"));
}
