#ifndef LOGICMODEL_H
#define LOGICMODEL_H

#include <QObject>
#include"udpclient.h"
#include "/home/ben/engine/design-engine/projects/neuralnetworks/qt/perceptron2/perceptronjsonmodel.h"
#include "interfaceenums.h"
#include "httpgetclient.h"

class LogicModel : public QObject
{
    Q_OBJECT
public:
    explicit LogicModel(QObject *parent = 0);
    ~LogicModel();
    PerceptronJsonModel* m_pPerceptronJsonModel;

    UdpClient m_UdpClient;
    QByteArray m_UdpData;

    void SendJsonCommand(QString strCommand);
    void SendHttpCommand(QString strCommand);


public slots:
    void sltSendCommand();


private:
    HttpGetClient m_HttpGetClient;

};

#endif // LOGICMODEL_H
