#include "perceptronconnectors.h"

PerceptronConnectors::PerceptronConnectors(QWidget *parent)
  : QFrame(parent)
  , m_pConnectorsHLayout(new QHBoxLayout())
{
  this->setLayout(m_pConnectorsHLayout);
  this->setObjectName("myObject");
  this->setStyleSheet("#myObject { border: 5px solid grey; }");
  this->setMaximumHeight(100);
}

