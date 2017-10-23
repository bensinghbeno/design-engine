#ifndef DATAMODEL_H
#define DATAMODEL_H

#include <QObject>
#include <QMap>

typedef struct
{
  uint weight;
  uint input;
}TPerceptronConnector;

typedef std::vector<TPerceptronConnector*> TVecPerceptronConnectors;

class DataModel : public QObject
{
  Q_OBJECT
public:
  explicit DataModel(QObject *parent = 0);
  ~DataModel();
  unsigned int m_PerceptronCount;
  typedef std::vector<int> TVecPerceptronInputs;
  typedef std::vector<int> TVecPerceptronOutputs;
  typedef QMap<QString,int> TMapPerceptronConnections;

  TVecPerceptronInputs  m_vecInputs;
  TVecPerceptronOutputs m_vecOutputs;
  TMapPerceptronConnections m_mapConnections;

signals:
  void SgnOnPerceptronCountChanged(int aCount);
  void SgnPerceptronOutPutChanged(int aIndex, int aOutputVal);
  void SgnPerceptronInputChanged();

public slots:
  void SltOnPerceptronCountSet(int aCount);
  void SltOnPerceptronInputSet(int aIndex, int aValue);
  void SltStartNetworkComputation();
};

#endif // DATAMODEL_H
