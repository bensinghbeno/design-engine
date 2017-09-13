#ifndef PERCEPTRONCONNECTORS_H
#define PERCEPTRONCONNECTORS_H

#include <QtGui>

class PerceptronConnectors : public QFrame
{
  Q_OBJECT
public:
  explicit PerceptronConnectors(QWidget *parent = 0);
  QVBoxLayout* m_pConnectorsVLayout;

signals:

public slots:
};

#endif // PERCEPTRONCONNECTORS_H
