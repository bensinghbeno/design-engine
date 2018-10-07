#ifndef HTTPGETCLIENT_H
#define HTTPGETCLIENT_H

#include <QNetworkAccessManager>
#include <QNetworkRequest>

class HttpGetClient
{
public:
    HttpGetClient();
    void SendNetworkGetRequest(QString getRequest);

    QNetworkAccessManager m_netAccessMgr;
    QNetworkRequest m_NetworkRequest;
};

#endif // HTTPGETCLIENT_H
