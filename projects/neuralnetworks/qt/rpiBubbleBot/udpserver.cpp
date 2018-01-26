#include "udpserver.h"
#include <QDebug>
#include "pigpio.h"
#include <stdio.h>

UdpClient::UdpClient()
{
    m_pJsonmodel = new PerceptronJsonModel("");


    m_UdpSocket.bind(QHostAddress("192.168.2.167"), 7777);
    QObject::connect(&m_UdpSocket,SIGNAL(readyRead()),this,SLOT(sltReadDatagram()));

    if (gpioInitialise() < 0)
    {
        fprintf(stderr, "pigpio initialisation failed\n");
    }
    else
    {
        /* Set GPIO modes */
        gpioSetMode(2, PI_OUTPUT);
        gpioSetMode(3, PI_OUTPUT);
        gpioSetMode(4, PI_OUTPUT);
        gpioSetMode(17, PI_OUTPUT);
    }

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

    QString cmd = m_pJsonmodel->getvalue("CMD_MOVE");



    if(cmd == "STOP")
    {
        qDebug() << "Execute GPIO Command = STOP" ;

        gpioWrite(2, 0); /* on */
        gpioWrite(3, 0); /* on */
        gpioWrite(4, 0); /* on */
        gpioWrite(17, 0); /* on */
    }
    else if(cmd == "FWD")
    {
        qDebug() << "Execute GPIO Command = FWD" ;

        gpioWrite(2, 1); /* on */
        gpioWrite(3, 0); /* on */
        gpioWrite(4, 1); /* on */
        gpioWrite(17, 0); /* on */
    }
    else if(cmd == "REV")
    {
        qDebug() << "Execute GPIO Command = REV" ;

        gpioWrite(2, 0); /* on */
        gpioWrite(3, 1); /* on */
        gpioWrite(4, 0); /* on */
        gpioWrite(17,1); /* on */
    }

}
