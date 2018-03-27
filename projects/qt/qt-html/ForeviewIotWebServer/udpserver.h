#ifndef UDPSERVER_H
#define UDPSERVER_H

#include <QObject>
#include <QUdpSocket>

class UdpServer : public QObject
{
    Q_OBJECT
public:
    explicit UdpServer(QObject *parent = 0);
    QUdpSocket m_UdpSocket;
    QByteArray m_byteArrayBuffer;


public slots:
    void sltReadDatagram();
signals:

public slots:
};

#endif // UDPSERVER_H
