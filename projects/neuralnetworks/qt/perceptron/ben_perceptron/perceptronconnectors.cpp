#include "perceptronconnectors.h"

PerceptronConnectors::PerceptronConnectors(QWidget *parent)
  : QWidget(parent)
  , m_pConnectorsVLayout(new QVBoxLayout())
{
  this->setLayout(m_pConnectorsVLayout);
}

