#include "perceptronconnector.h"

PerceptronConnector::PerceptronConnector(QWidget *parent)
  : QWidget(parent)
  , m_pConnectorHLayout(new QHBoxLayout())
  , m_pInputSpinBox(new QSpinBox())
  , m_pWeightLabel(new QLabel(""))
{
  m_pConnectorHLayout->addWidget(m_pWeightLabel);
  m_pConnectorHLayout->addWidget(m_pInputSpinBox);
  this->setLayout(m_pConnectorHLayout);
}

