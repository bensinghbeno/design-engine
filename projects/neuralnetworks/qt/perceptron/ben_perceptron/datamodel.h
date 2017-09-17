#ifndef DATAMODEL_H
#define DATAMODEL_H

#include <QObject>

class DataModel : public QObject
{
  Q_OBJECT
public:
  explicit DataModel(QObject *parent = 0);
  ~DataModel();
  unsigned int m_PerceptronCount;

signals:
  void SgnOnPerceptronCountChanged(int aCount);

public slots:
  void SltOnPerceptronCountSet(int aCount);
};

#endif // DATAMODEL_H
