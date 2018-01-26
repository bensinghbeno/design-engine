#ifndef PERCEPTRONCONTROLLER_H
#define PERCEPTRONCONTROLLER_H

#include <QObject>

class PerceptronWidget;
class PerceptronWeightWidget;
class PerceptronJsonModel;

class PerceptronController : public QObject
{
    Q_OBJECT

public:
    PerceptronController(PerceptronWidget& perceptronWidget, PerceptronWeightWidget& perceptronWeightWidget, PerceptronJsonModel& perceptronJsonModel);
    void createConnections();

    PerceptronWidget& m_perceptronWidget;
    PerceptronWeightWidget& m_perceptronWeightWidget;
    PerceptronJsonModel& m_perceptronJsonModel;

public slots:
    void sltSendLayerCount();

};

#endif // PERCEPTRONCONTROLLER_H
