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
    void sltWriteDatagram(QString datagram);

signals:
    void sigDatagramReceived(QString datagram);

public slots:

private:
    QHostAddress sender;
    quint16 senderPort;
};

#endif // UDPSERVER_H
