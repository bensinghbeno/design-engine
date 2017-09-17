#include "datamodel.h"
#include <QDebug>

DataModel::DataModel(QObject *parent)
  : QObject(parent)
  , m_PerceptronCount(0)
{

}

void DataModel::SltOnPerceptronCountSet(int aCount)
{
  qDebug() << "DataModel::OnPerceptronCountSet = " << aCount;
  m_PerceptronCount = aCount;
  emit SgnOnPerceptronCountChanged(m_PerceptronCount);

}

DataModel::~DataModel()
{

}


