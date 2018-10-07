#include "httpgetclient.h"

HttpGetClient::HttpGetClient()
{

}

void HttpGetClient::SendNetworkGetRequest(QString getRequest)
{
//    m_NetworkRequest.setUrl(QUrl(getRequest));
//    m_netAccessMgr.get(m_NetworkRequest);

    m_WorkerThread.SetString(getRequest);
    m_WorkerThread.start();
}

void HttpGetClient::SendNetworkGetRequest2(QString getRequest)
{
    m_NetworkRequest.setUrl(QUrl(getRequest));
    m_netAccessMgr.get(m_NetworkRequest);
}

void HttpGetClient::StopSendNetworkGetRequest()
{
    std::this_thread::sleep_for(std::chrono::milliseconds(300));

    if (m_WorkerThread.isRunning())
    {
        m_WorkerThread.terminate();
    }
}


void WorkerThread::run()
{
    HttpGetClient objHttpGetClient;
    QString objHttpString = m_str;

    forever
    {
        objHttpGetClient.SendNetworkGetRequest2(objHttpString);

        qDebug() << "Worker thread SendHttpCommand = " << m_str;

        std::this_thread::sleep_for(std::chrono::milliseconds(300));

    }

}

