#ifndef DATAMODEL_H
#define DATAMODEL_H

#include <QObject>

typedef struct
{
  uint m_Index;
  uint m_InputVal;
  uint m_OutPutVal;
}PerceptronDataStructure;

class DataModel : public QObject
{
  Q_OBJECT
public:
  explicit DataModel(QObject *parent = 0);
  ~DataModel();
  unsigned int m_PerceptronCount;
  std::vector<PerceptronDataStructure*> m_vecPerceptronDataStructure;


signals:
  void SgnOnPerceptronCountChanged(int aCount);
  void SgnPerceptronOutPutChanged(int aIndex, int aOutputVal);

public slots:
  void SltOnPerceptronCountSet(int aCount);
  void SltOnPerceptronInputSet(int aIndex, int aValue);
};

#endif // DATAMODEL_H
