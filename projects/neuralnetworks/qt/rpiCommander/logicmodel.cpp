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
    SendJsonCommand(sender()->objectName());
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



