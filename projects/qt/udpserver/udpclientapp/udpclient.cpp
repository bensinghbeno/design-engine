#include "udpclient.h"
#include <QDebug>

UdpClient::UdpClient(QString ip, quint16 port)
    : m_Ip(ip)
    , m_Port(port)
{
    startConnection();
}

void UdpClient::startConnection()
{
    //m_pUdpSocket->bind(45454, QUdpSocket::ShareAddress);
    m_UdpSocket.connectToHost(m_Ip, m_Port);
    QObject::connect(&m_UdpSocket,SIGNAL(readyRead()),this,SLOT(sltReadDatagram()));
}

void UdpClient::sltWriteDatagram(QString data)
{
    qDebug() << "UdpClient::sltWriteDatagram : " << data;
    QByteArray bdata;
    bdata.append(data);
    m_UdpSocket.writeDatagram(bdata, QHostAddress(m_Ip), m_Port);
}


void UdpClient::sltReadDatagram()
{
    m_byteArrayBuffer.resize(m_UdpSocket.pendingDatagramSize());

    QHostAddress sender;
    quint16 senderPort;

    m_UdpSocket.readDatagram(m_byteArrayBuffer.data(), m_byteArrayBuffer.size(),&sender, &senderPort);
    qDebug() << "UdpServer::sltReadDatagram() = " << m_byteArrayBuffer;
}

void UdpClient::sltSetIp(QString ip)
{
    qDebug() << "UdpClient::sltSetIp()  = " << ip;

    m_Ip = ip;
}

void UdpClient::sltSetPort(quint16 port)
{
    qDebug() << "UdpClient::sltSetPort()  = " << port;

    m_Port = port;
}

