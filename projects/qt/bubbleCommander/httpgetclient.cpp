#include "httpgetclient.h"

HttpGetClient::HttpGetClient()
{

}

void HttpGetClient::SendNetworkGetRequest(QString getRequest)
{
    StopSendNetworkGetRequest();

    auto lambda = [getRequest]
    {
        QNetworkAccessManager netAccessMgr;
        QNetworkRequest networkRequest;
        networkRequest.setUrl(QUrl(getRequest));
        netAccessMgr.get(networkRequest);

        qDebug() << "Lambda thread SendHttpCommand = " << getRequest;

    };

    m_WorkerThread.StartJob(lambda);
}

void HttpGetClient::StopSendNetworkGetRequest()
{
    m_WorkerThread.SetWorkerState(EN_WORKER_STATE::STATE_STOP);
}

