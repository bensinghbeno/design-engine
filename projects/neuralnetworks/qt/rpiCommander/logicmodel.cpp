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
    switch(strCommand.toStdString().c_str()[0])
    {
        case 'R':
        {
            qDebug() << "strCommand = RIGHT";
            break;
        }

        case 'L':
        {
            qDebug() << "strCommand = LEFT";
            break;
        }

        case 'F':
        {
            qDebug() << "strCommand = FORWARD";

            QNetworkRequest request(QUrl("http://192.168.4.1/5/on"));
            m_netAccessMgr.get(request);

            break;
        }

        case 'B':
        {
            qDebug() << "strCommand = BACK";
            break;
        }

        case 'S':
        {
            qDebug() << "strCommand = STOP";

            QNetworkRequest request(QUrl("http://192.168.4.1/5/off"));
            m_netAccessMgr.get(request);

            break;
        }

        default:
        {
            qDebug() << "strCommand = DEFAULT";
            break;
        }

    }







}


