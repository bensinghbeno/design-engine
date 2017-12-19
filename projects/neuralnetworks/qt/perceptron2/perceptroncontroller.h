#ifndef PERCEPTRONCONTROLLER_H
#define PERCEPTRONCONTROLLER_H

#include <QObject>

class PerceptronWidget;

class PerceptronController : public QObject
{
    Q_OBJECT

public:
    PerceptronController(PerceptronWidget& perceptronWidget);
    void createConnections();

    PerceptronWidget& m_perceptronWidget;

public slots:
    void sltSendLayerCount();

};

#endif // PERCEPTRONCONTROLLER_H
