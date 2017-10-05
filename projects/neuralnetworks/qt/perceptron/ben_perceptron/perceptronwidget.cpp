#include "perceptronwidget.h"

static const char* PropertyIndex = "PropertyIndex";

PerceptronWidget::PerceptronWidget(QWidget *parent, uint aIndex)
  : QWidget(parent)
  , m_Index(aIndex)
  , m_pInputLabel(new QLabel(QString("Input_") + QString::number(m_Index), this))
  , m_pInputSpinBox(new QSpinBox(this))
  , m_pPerceptronConnectors(new PerceptronConnectors(this))
  , m_pPerceptronConnector(new PerceptronConnector(this))
  , m_pOutputLabel(new QPushButton(parent))
  , m_pPerceptronHLayout(new QHBoxLayout())
  , m_pPerceptronVLayout(new QVBoxLayout())
  , m_pWeightBoxLayout(new QHBoxLayout())
  , m_pPerceptronSpacer1(new QSpacerItem(100,1, QSizePolicy::Expanding, QSizePolicy::Ignored))
  , m_pPerceptronSpacer2(new QSpacerItem(100,1, QSizePolicy::Expanding, QSizePolicy::Ignored))
{
    m_pInputSpinBox->setProperty(PropertyIndex, QString::number(m_Index));
    m_pOutputLabel->setText("");
    m_pOutputLabel->setStyleSheet("QPushButton {"
                                "background-color: lightgreen;"
                                "border-style: solid;"
                                "border-width:3px;"
                                "border-radius:25px;"
                                "border-color: black;"
                                "max-width:50px;"
                                "max-height:50px;"
                                "min-width:50px;"
                                "min-height:50px;"
                                  "}");

    m_pPerceptronHLayout->addWidget(m_pInputLabel);
    m_pInputLabel->setProperty("index","0");

    m_pPerceptronHLayout->addWidget(m_pInputSpinBox);

    m_pWeightBoxLayout->addSpacerItem(m_pPerceptronSpacer1);
    m_pPerceptronHLayout->addLayout(m_pWeightBoxLayout);
    m_VecWeightBoxLayouts.push_back(m_pWeightBoxLayout);
    m_Input2WeightBoxLayouts_HashMap["0"] = m_VecWeightBoxLayouts;
    m_pPerceptronHLayout->addWidget(m_pOutputLabel);
    m_pPerceptronHLayout->addSpacerItem(m_pPerceptronSpacer2);

    m_pPerceptronVLayout->addLayout(m_pPerceptronHLayout);
    this->setLayout(m_pPerceptronVLayout);
    m_pInputLabel->setMouseTracking(true);
    installEventFilter(this);

    m_pPerceptronConnectors->m_pConnectorsHLayout->addWidget(m_pPerceptronConnector);
    m_pPerceptronConnectors->m_pConnectorsHLayout->addWidget(new PerceptronConnector(this));

    m_pPerceptronConnectors->setVisible(false);
}

bool PerceptronWidget::eventFilter(QObject* object, QEvent* event)
{

  switch (event->type())
  {
    case (QEvent::Enter):
    {
      m_pPerceptronConnectors->setGeometry(m_pInputLabel->geometry().x(), m_pInputLabel->geometry().y() - m_pInputLabel->geometry().height() + 5, 400, 65);
      m_pPerceptronConnectors->show();
      break;
    }
    case (QEvent::Leave):
    {
      m_pPerceptronConnectors->hide();
      break;
    }
    case (QEvent::ToolTip):
    {
    }
    default:
    {
    }

  }

  return true;
}


PerceptronWidget::~PerceptronWidget()
{
}
