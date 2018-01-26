#include "perceptroncontroller.h"
#include "perceptronwidget.h"
#include "perceptronweightwidget.h"
#include "perceptronjsonmodel.h"
#include <QDebug>

PerceptronController::PerceptronController(PerceptronWidget& perceptronWidget, PerceptronWeightWidget& perceptronWeightWidget, PerceptronJsonModel& perceptronJsonModel)
    : m_perceptronWidget(perceptronWidget)
    , m_perceptronWeightWidget(perceptronWeightWidget)
    , m_perceptronJsonModel(perceptronJsonModel)
{
    createConnections();
}

void PerceptronController::createConnections()
{
    // Master Tool Box Items to Model
    QObject::connect((&m_perceptronWidget.m_SpinBoxLayerCount), SIGNAL(valueChanged(int)),&m_perceptronJsonModel,SLOT(sltLayerCountUpdate(int)));
    QObject::connect((&m_perceptronWidget.m_sbLayerMasterInputCount), SIGNAL(valueChanged(int)),&m_perceptronJsonModel,SLOT(sltMasterInputCountUpdate(int)));
    QObject::connect((&m_perceptronWidget.m_pbCreateMatrix), SIGNAL(clicked(bool)),&m_perceptronJsonModel,SLOT(sltCreatePerceptronNetworkModel()));

    // From Model to widgets
    QObject::connect((&m_perceptronJsonModel), SIGNAL(sgnJsonModelUpdated()),&m_perceptronWidget,SLOT(sltCreatePerceptronWidgets()));
    QObject::connect((&m_perceptronJsonModel), SIGNAL(sgnJsonModelUpdated()),&m_perceptronWeightWidget,SLOT(sltCreatePerceptronWeightWidgets()));
}

void PerceptronController::sltSendLayerCount()
{
    qDebug() << "PerceptronController::sltSendLayerCount() = " << m_perceptronWidget.m_SpinBoxLayerCount.value();
}

