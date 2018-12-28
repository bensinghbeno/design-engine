#ifndef UDPSERVER_H
#define UDPSERVER_H

#include <QString>
#include <QObject>
#include <QUdpSocket>

class UdpServer: public QObject
{
    Q_OBJECT

public:
    UdpServer(quint16 port);
    virtual ~UdpServer();

    QHostAddress getDeviceIp();
    quint16 getDevicePort();
    QString getDeviceIpString() const;

signals:
    void sgnUdpMessageReceived(QString msg);

public slots:
    void readyRead();

private:
    QUdpSocket * m_pUdpSocket;
    quint16 m_Port;
    QString m_Ip;

};

#endif // UDPSERVER_H
