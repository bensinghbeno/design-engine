#ifndef TCPCLIENT_H
#define TCPCLIENT_H

#include <QTcpSocket>


class TcpClient : public QObject
{
    Q_OBJECT

public:
    explicit TcpClient();
    ~TcpClient();

public slots:
    void onReadyRead();

private:
    QTcpSocket  _socket;
    QString ip;
    quint16 port;
};


#endif // TCPCLIENT_H
