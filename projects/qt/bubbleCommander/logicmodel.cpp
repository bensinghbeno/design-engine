#include "logicmodel.h"
#include <QDebug>
#include <QTextEdit>

LogicModel::LogicModel(QObject *parent) : QObject(parent)
{
}

LogicModel::~LogicModel()
{
}

void LogicModel::sltSendCommand()
{
    qDebug() << "Command Pressed = " << sender()->objectName();
    m_UdpClient.sltWriteDatagram(sender()->objectName());
    //SendHttpCommand(sender()->objectName());
}

void LogicModel::sltStopSendCommand()
{
    //m_HttpGetClient.StopSendNetworkGetRequest();
}

void LogicModel::sltSetIp()
{
    m_Ip = static_cast<QTextEdit*>(sender())->toPlainText();
    m_UdpClient.sltSetIp(m_Ip);
}

void LogicModel::sltSetPort()
{
    m_Port = static_cast<QTextEdit*>(sender())->toPlainText().toInt();
    m_UdpClient.sltSetPort(m_Port);
}

void LogicModel::SendJsonCommand(QString strCommand)
{
    //    m_pPerceptronJsonModel->insertvalue("CMD_MOVE",strCommand);
    //    qDebug() << "send CMD_MOVE = " << m_pPerceptronJsonModel->getvalue("CMD_MOVE");

    //    m_UdpData.clear();
    //    m_UdpData.append(m_pPerceptronJsonModel->getJsonStringbuffer().toStdString().c_str());
    //    m_UdpClient.m_UdpSocket.writeDatagram(m_UdpData, QHostAddress("192.168.2.167"), 7777);

    //    qDebug() << "BUFFER = " << m_pPerceptronJsonModel->getJsonStringbuffer();

}

void LogicModel::SendHttpCommand(QString strCommand)
{
    QString baseUrl = "http://192.168.4.1/";

    switch(strCommand.toStdString().c_str()[0])
    {

        case 'G':
        {
            qDebug() << "strCommand = GRAB";

            baseUrl += "GRAB";

            break;
        }

        case 'r':
        {
            qDebug() << "strCommand = RELEASE";

            baseUrl += "RELEASE";

            break;
        }

        case 'T':
        {
            qDebug() << "strCommand = TO";

            baseUrl += "TO";

            break;
        }

        case 'f':
        {
            qDebug() << "strCommand = FRO";

            baseUrl += "FRO";

            break;
        }
        case 'R':
        {
            qDebug() << "strCommand = RIGHT";

            baseUrl += "RIGHT";

            break;
        }

        case 'L':
        {
            qDebug() << "strCommand = LEFT";

            baseUrl += "LEFT";

            break;
        }

        case 'F':
        {
            qDebug() << "strCommand = FORWARD";

            baseUrl += "FORWARD";

            break;
        }

        case 'B':
        {
            qDebug() << "strCommand = BACK";

            baseUrl += "BACK";

            break;
        }

        case 'S':
        {
            qDebug() << "strCommand = STOP";

            baseUrl += "STOP";

            break;
        }

        default:
        {
            qDebug() << "strCommand = DEFAULT";

            baseUrl += "STOP";

            break;
        }

    }

    m_HttpGetClient.SendNetworkGetRequest(baseUrl);
}


