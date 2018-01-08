#include "mainwindow.h"
#include <QApplication>
#include"udpclient.h"
#include "/home/ben/engine/design-engine/projects/neuralnetworks/qt/perceptron2/perceptronjsonmodel.h"

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

    PerceptronJsonModel m_jsonmodel("");
    m_jsonmodel.demo();
    m_jsonmodel.insertvalue("CMD_MOVE","FWD");
    qDebug() << "send CMD_MOVE = " << m_jsonmodel.getvalue("CMD_MOVE");

    UdpClient objUdpClient;
    QByteArray Data;
    Data.append(m_jsonmodel.getJsonStringbuffer().toStdString().c_str());
    objUdpClient.m_UdpSocket.writeDatagram(Data, QHostAddress("192.168.2.167"), 7777);


    //MainWindow w;

    return a.exec();
}
