#include "datamodel.h"
#include "/home/ben/engine/design-engine/projects/qt/MyQtUtils/myqttypes.h"

DataModel::DataModel(QObject *parent)
  : QObject(parent)
  , m_PerceptronCount(0)
  , m_vecPerceptronDataStructure(10, new PerceptronDataStructure) //TBM
{
  connect(this,SIGNAL(SgnPerceptronInputChanged()),this,SLOT(SltStartNetworkComputation()));
}

void DataModel::SltOnPerceptronInputSet(int aIndex, int aValue)
{
  qDebug() << "DataModel::SltOnPerceptronInputSet aIndex = " << aIndex << "aValue = " << aValue;
  m_vecPerceptronDataStructure[aIndex]->m_InputVal  = aValue;
  emit SgnPerceptronInputChanged();

}


void DataModel::SltOnPerceptronCountSet(int aCount)
{
  qDebug() << "DataModel::OnPerceptronCountSet = " << aCount;
  m_PerceptronCount = aCount;
  emit SgnOnPerceptronCountChanged(m_PerceptronCount);

}

void DataModel::SltStartNetworkComputation()
{
  myconsoledisp << "SltStartNetworkComputation()";
  //m_vecPerceptronDataStructure[aIndex]->m_OutPutVal = aValue;
  //SgnPerceptronOutPutChanged(aIndex, m_vecPerceptronDataStructure[aIndex]->m_OutPutVal);
}


DataModel::~DataModel()
{

}


