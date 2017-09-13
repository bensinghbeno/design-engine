#include "perceptronconnectors.h"

PerceptronConnectors::PerceptronConnectors(QWidget *parent)
  : QFrame(parent)
  , m_pConnectorsVLayout(new QVBoxLayout())
{
  this->setLayout(m_pConnectorsVLayout);
  this->setObjectName("myObject");
  this->setStyleSheet("#myObject { border: 5px solid grey; }");
}

