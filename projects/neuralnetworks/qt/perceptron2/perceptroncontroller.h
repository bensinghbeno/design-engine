#ifndef PERCEPTRONCONTROLLER_H
#define PERCEPTRONCONTROLLER_H

#include <QObject>

class PerceptronWidget;
class PerceptronJsonModel;

class PerceptronController : public QObject
{
    Q_OBJECT

public:
    PerceptronController(PerceptronWidget& perceptronWidget, PerceptronJsonModel& perceptronJsonModel);
    void createConnections();

    PerceptronWidget& m_perceptronWidget;
    PerceptronJsonModel& m_perceptronJsonModel;

public slots:
    void sltSendLayerCount();

};

#endif // PERCEPTRONCONTROLLER_H
