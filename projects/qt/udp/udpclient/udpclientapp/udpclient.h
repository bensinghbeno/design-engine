#ifndef UDPCLIENT_H
#define UDPCLIENT_H


#include <QObject>
#include <QUdpSocket>

class UdpClient : public QObject
{
    Q_OBJECT

public:
    UdpClient(QString ip, quint16 port);
    UdpClient(){}
    QUdpSocket m_UdpSocket;
    QByteArray m_byteArrayBuffer;

    void startConnection();

    QByteArray bdata;


public slots:
    void sltReadDatagram();
    void sltSetIp(QString ip);
    void sltSetPort(quint16 port);
    void sltWriteDatagram(QString data);

private:
    QString m_Ip;
    quint16 m_Port;

};

#endif // UDPCLIENT_H
