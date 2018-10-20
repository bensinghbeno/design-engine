#ifndef HTTPGETCLIENT_H
#define HTTPGETCLIENT_H

#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include "backgroundworker.h"

class HttpGetClient
{

public:

    HttpGetClient();
    void SendNetworkGetRequest(QString getRequest);
    void StopSendNetworkGetRequest();

    BackGroundWorker m_WorkerThread;
};


#endif // HTTPGETCLIENT_H
