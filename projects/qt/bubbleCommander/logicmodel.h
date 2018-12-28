#ifndef LOGICMODEL_H
#define LOGICMODEL_H

#include <QObject>
#include "../udp/udpclient/udpclientapp/udpclient.h"
#include "interfaceenums.h"
#include "httpgetclient.h"

class LogicModel : public QObject
{
    Q_OBJECT
public:
    explicit LogicModel(QObject *parent = 0);
    ~LogicModel();

    QByteArray m_UdpData;

    void SendJsonCommand(QString strCommand);
    void SendHttpCommand(QString strCommand);


public slots:
    void sltSendCommand();
    void sltStopSendCommand();
    void sltSetIp();
    void sltSetPort();


private:
    HttpGetClient m_HttpGetClient;
    UdpClient m_UdpClient;
    QString m_Ip;
    quint16 m_Port;

};

#endif // LOGICMODEL_H
