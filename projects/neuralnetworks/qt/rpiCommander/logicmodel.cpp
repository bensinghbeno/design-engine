#include "logicmodel.h"
#include <QDebug>

LogicModel::LogicModel(QObject *parent) : QObject(parent)
  , m_pPerceptronJsonModel(new PerceptronJsonModel(""))
{

}

LogicModel::~LogicModel()
{

    delete m_pPerceptronJsonModel;
}

void LogicModel::sltSendCommand()
{
    qDebug() << "Command Pressed = " << sender()->objectName();
    SendHttpCommand(sender()->objectName());
}

void LogicModel::sltStopSendCommand()
{
    m_HttpGetClient.StopSendNetworkGetRequest();
}

void LogicModel::SendJsonCommand(QString strCommand)
{
    m_pPerceptronJsonModel->insertvalue("CMD_MOVE",strCommand);
    qDebug() << "send CMD_MOVE = " << m_pPerceptronJsonModel->getvalue("CMD_MOVE");

    m_UdpData.clear();
    m_UdpData.append(m_pPerceptronJsonModel->getJsonStringbuffer().toStdString().c_str());
    m_UdpClient.m_UdpSocket.writeDatagram(m_UdpData, QHostAddress("192.168.2.167"), 7777);

    qDebug() << "BUFFER = " << m_pPerceptronJsonModel->getJsonStringbuffer();

}

void LogicModel::SendHttpCommand(QString strCommand)
{
    QString baseUrl = "http://192.168.4.1/";

    switch(strCommand.toStdString().c_str()[0])
    {
        case 'R':
        {
            qDebug() << "strCommand = RIGHT";

            m_HttpGetClient.SendNetworkGetRequest(baseUrl + "RIGHT");

            break;
        }

        case 'L':
        {
            qDebug() << "strCommand = LEFT";

            m_HttpGetClient.SendNetworkGetRequest(baseUrl + "LEFT");

            break;
        }

        case 'F':
        {
            qDebug() << "strCommand = FORWARD";

            m_HttpGetClient.SendNetworkGetRequest(baseUrl + "FORWARD");

            break;
        }

        case 'B':
        {
            qDebug() << "strCommand = BACK";

            m_HttpGetClient.SendNetworkGetRequest(baseUrl + "BACK");

            break;
        }

        case 'S':
        {
            qDebug() << "strCommand = STOP";

            m_HttpGetClient.SendNetworkGetRequest(baseUrl + "STOP");

            break;
        }

        default:
        {
            qDebug() << "strCommand = DEFAULT";

            m_HttpGetClient.SendNetworkGetRequest(baseUrl + "STOP");

            break;
        }

    }

}


