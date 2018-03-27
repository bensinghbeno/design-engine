#include "udpserver.h"

UdpServer::UdpServer(QObject *parent) : QObject(parent)
{
    m_UdpSocket.bind(QHostAddress::Any, 7777);
    QObject::connect(&m_UdpSocket,SIGNAL(readyRead()),this,SLOT(sltReadDatagram()));
}

void UdpServer::sltReadDatagram()
{
    m_byteArrayBuffer.resize(m_UdpSocket.pendingDatagramSize());

    m_UdpSocket.readDatagram(m_byteArrayBuffer.data(), m_byteArrayBuffer.size(),&sender, &senderPort);
    qDebug() << "UdpServer::sltReadDatagram() = " << m_byteArrayBuffer;

    QString datagram = m_byteArrayBuffer.toStdString().c_str();

    emit sigDatagramReceived(datagram);
}


void UdpServer::sltWriteDatagram(QString datagram)
{
    QByteArray sendDatagram = datagram.toStdString().c_str();
    m_UdpSocket.writeDatagram(sendDatagram,sender, senderPort);
}
