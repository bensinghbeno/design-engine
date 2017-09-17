#ifndef PERCEPTRONCONNECTORS_H
#define PERCEPTRONCONNECTORS_H

#include <QtGui>

class PerceptronConnectors : public QFrame
{
  Q_OBJECT
public:
  explicit PerceptronConnectors(QWidget *parent = 0);
  QHBoxLayout* m_pConnectorsHLayout;

signals:

public slots:
};

#endif // PERCEPTRONCONNECTORS_H
