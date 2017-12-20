#include "perceptronjsonmodel.h"
#include "perceptronjsonterminal.h"
#include <QDebug>

PerceptronJsonModel::PerceptronJsonModel(PerceptronJsonTerminal& perceptronJsonTerminal, QObject *parent)
    : QObject(parent)
    , m_perceptronJsonTerminal(perceptronJsonTerminal)
{
    perceptronJsonTerminal.demo();
}

void PerceptronJsonModel::sltLayerCountUpdate(int layerCount)
{
    qDebug() << "PerceptronJsonModel::sltLayerCountUpdate() = " << layerCount;
}
