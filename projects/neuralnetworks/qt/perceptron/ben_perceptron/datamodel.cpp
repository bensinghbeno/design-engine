#include "datamodel.h"
#include "/home/ben/engine/design-engine/projects/qt/MyQtUtils/myqttypes.h"

DataModel::DataModel(QObject *parent)
  : QObject(parent)
  , m_PerceptronCount(0)
  , m_vecInputs(3, 0) //TBM
  , m_vecOutputs(3, 0) //TBM
{
  connect(this,SIGNAL(SgnPerceptronInputChanged()),this,SLOT(SltStartNetworkComputation()));
}

void DataModel::SltOnPerceptronInputSet(int aIndex, int aValue)
{
  qDebug() << "DataModel::SltOnPerceptronInputSet aIndex = " << aIndex << "aValue = " << aValue;
  m_vecInputs[--aIndex]  = aValue;
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

  int i=0;
  for(TVecPerceptronOutputs::iterator it = m_vecOutputs.begin(); it != m_vecOutputs.end(); it++)
  {
    //(it)[i] = m_vecInputs[i];
    //emit SgnPerceptronOutPutChanged(i, (it)[i]);
    myconsoledisp << "m_vecInputs[i] = " << m_vecInputs[i];



   ++i;
  }


}


DataModel::~DataModel()
{

}


