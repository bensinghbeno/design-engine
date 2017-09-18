#include "datamodel.h"
#include <QDebug>

DataModel::DataModel(QObject *parent)
  : QObject(parent)
  , m_PerceptronCount(0)
  , m_vecPerceptronDataStructure(10, new PerceptronDataStructure) //TBM
{

}

void DataModel::SltOnPerceptronInputSet(int aIndex, int aValue)
{
  qDebug() << "DataModel::SltOnPerceptronInputSet aIndex = " << aIndex << "aValue = " << aValue;
  m_vecPerceptronDataStructure[aIndex]->m_InputVal  = aValue;
  m_vecPerceptronDataStructure[aIndex]->m_OutPutVal = aValue;

  SgnPerceptronOutPutChanged(aIndex, m_vecPerceptronDataStructure[aIndex]->m_OutPutVal);
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


