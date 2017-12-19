#include "perceptroncontroller.h"
#include "perceptronwidget.h"
#include <QDebug>

PerceptronController::PerceptronController(PerceptronWidget &perceptronWidget)
    : m_perceptronWidget(perceptronWidget)
{
    createConnections();
}

void PerceptronController::createConnections()
{
    QObject::connect((&m_perceptronWidget.m_SpinBoxLayerCount), SIGNAL(valueChanged(int)),this,SLOT(sltSendLayerCount()));
}

void PerceptronController::sltSendLayerCount()
{
    qDebug() << "PerceptronController::sltSendLayerCount() = " << m_perceptronWidget.m_SpinBoxLayerCount.value();
}

