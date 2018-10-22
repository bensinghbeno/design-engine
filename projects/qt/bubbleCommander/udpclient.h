#ifndef UDPSERVER_H
#define UDPSERVER_H

#include <QObject>
#include <QUdpSocket>
#include "/home/ben/engine/design-engine/projects/neuralnetworks/qt/perceptron2/perceptronjsonmodel.h"

class UdpClient : public QObject
{
    Q_OBJECT

public:
    UdpClient();
    QUdpSocket m_UdpSocket;
    QByteArray m_byteArrayBuffer;
    PerceptronJsonModel* m_pJsonmodel;

public slots:
    void sltReadDatagram();


};

#endif // UDPSERVER_H
