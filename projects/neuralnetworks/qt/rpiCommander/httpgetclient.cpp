#include "httpgetclient.h"

HttpGetClient::HttpGetClient()
{

}

void HttpGetClient::SendNetworkGetRequest(QString getRequest)
{
    m_NetworkRequest.setUrl(QUrl(getRequest));
    m_netAccessMgr.get(m_NetworkRequest);
}
