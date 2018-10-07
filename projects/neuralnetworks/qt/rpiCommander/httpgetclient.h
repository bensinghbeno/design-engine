#ifndef HTTPGETCLIENT_H
#define HTTPGETCLIENT_H

#include <QNetworkAccessManager>
#include <QNetworkRequest>


#include <qthread.h>
#include <thread>

class HttpGetClient;

class WorkerThread : public QThread
{

public:
    WorkerThread(QObject* parent = 0)
        : QThread(parent)
    {

    }

    void SetString(QString str)
    {
        m_str = str;
    }

    void run();



    QString m_str;
};

class HttpGetClient
{
public:
    HttpGetClient();
    void SendNetworkGetRequest(QString getRequest);
    void SendNetworkGetRequest2(QString getRequest);
    void StopSendNetworkGetRequest();

    QNetworkAccessManager m_netAccessMgr;
    QNetworkRequest m_NetworkRequest;
    WorkerThread m_WorkerThread;
};




#endif // HTTPGETCLIENT_H
