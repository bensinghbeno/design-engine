#ifndef PERCEPTRONCONNECTOR_H
#define PERCEPTRONCONNECTOR_H

#include <QtGui>

class PerceptronConnector : public QWidget
{
  Q_OBJECT
public:
  explicit PerceptronConnector(QWidget *parent = 0);
  QSpinBox*       m_pInputSpinBox;
  QLabel*         m_pWeightLabel;
  QHBoxLayout*    m_pConnectorHLayout;


signals:

public slots:
};

#endif // PERCEPTRONCONNECTOR_H
