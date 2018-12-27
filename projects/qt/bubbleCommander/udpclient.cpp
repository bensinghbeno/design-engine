#include "udpclient.h"
#include <QDebug>

UdpClient::UdpClient()
{
    m_pJsonmodel = new PerceptronJsonModel("");

    m_UdpSocket.bind(QHostAddress("192.168.2.167"), 7777);
    QObject::connect(&m_UdpSocket,SIGNAL(readyRead()),this,SLOT(sltReadDatagram()));

}



void UdpClient::sltReadDatagram()
{
    m_byteArrayBuffer.resize(m_UdpSocket.pendingDatagramSize());

    QHostAddress sender;
    quint16 senderPort;

    m_UdpSocket.readDatagram(m_byteArrayBuffer.data(), m_byteArrayBuffer.size(),&sender, &senderPort);
    qDebug() << "UdpServer::sltReadDatagram() = " << m_byteArrayBuffer;

    m_pJsonmodel->insertJsonStringbuffer(m_byteArrayBuffer.toStdString().c_str());
    qDebug() << "receive CMD_MOVE = " << m_pJsonmodel->getvalue("CMD_MOVE");

}
