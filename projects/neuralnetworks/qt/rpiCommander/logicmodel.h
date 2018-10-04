#ifndef LOGICMODEL_H
#define LOGICMODEL_H

#include <QObject>
#include"udpclient.h"
#include "/home/ben/engine/design-engine/projects/neuralnetworks/qt/perceptron2/perceptronjsonmodel.h"
#include "interfaceenums.h"
#include <QNetworkRequest>
#include <QNetworkAccessManager>

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

signals:

public slots:
    void sltSendCommand();

private:
    QNetworkAccessManager m_netAccessMgr;


};

#endif // LOGICMODEL_H
