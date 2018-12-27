#include "udpserver.h"
#include <QHostAddress>
#include <QNetworkInterface>

UdpServer::UdpServer(quint16 port)
    : m_Port(port)
{
    m_pUdpSocket = new QUdpSocket(this);

    m_pUdpSocket->bind(getDeviceIp(), port);
    connect(m_pUdpSocket, SIGNAL(readyRead()), this, SLOT(readyRead()));
}

void UdpServer::readyRead()
{
    // when data comes in
    QByteArray buffer;
    buffer.resize(m_pUdpSocket->pendingDatagramSize());

    QHostAddress sender;
    quint16 port;

    while (m_pUdpSocket->hasPendingDatagrams())
    {
        QByteArray datagram;
        datagram.resize(m_pUdpSocket->pendingDatagramSize());
        m_pUdpSocket->readDatagram(datagram.data(),datagram.size(),&sender,&port);
        qDebug() <<"Message From :: " << sender.toString();
        qDebug() <<"Port From :: "<< port;
        qDebug() <<"Message :: " << datagram;
        sgnUdpMessageReceived(datagram);
    }
}

QString UdpServer::getDeviceIpString() const
{
    return m_Ip;
}

quint16 UdpServer::getDevicePort()
{
    return m_Port;
}

QHostAddress UdpServer::getDeviceIp()
{
    QHostAddress ip;
    QList<QHostAddress> list = QNetworkInterface::allAddresses();

    for(int nIter=0; nIter<list.count(); nIter++)

    {
        if (list[nIter].protocol() == QAbstractSocket::IPv4Protocol )
        {
            if(list[nIter].toString() != "127.0.0.1")
            {
                //qDebug() << list[nIter].toString();
                ip = list[nIter];
            }
        }
    }

    m_Ip = ip.toString();
    return ip;
}

UdpServer::~UdpServer()
{
    delete m_pUdpSocket;
}



