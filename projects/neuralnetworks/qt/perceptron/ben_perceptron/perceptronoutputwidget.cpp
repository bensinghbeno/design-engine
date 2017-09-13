#include "perceptronoutputwidget.h"

PerceptronWidget::PerceptronWidget(QWidget *parent)
  : QWidget(parent)
  , m_pPerceptronConnectors(new PerceptronConnectors(this))
  , m_pPerceptronConnector(new PerceptronConnector(this))
  , m_pOutputLabel(new QPushButton(parent))
  , m_pPerceptronHLayout(new QHBoxLayout())
  , m_pPerceptronVLayout(new QVBoxLayout())
  , m_pWeightBoxLayout(new QHBoxLayout())
  , m_pInputLabel(new QLabel("Input_1",parent))
  , m_pInputSpinBox(new QSpinBox())
  , m_pWeightLabel(new QLabel("Weight_1"))
  , m_pWeightSpinBox(new QSpinBox())
  , m_pPerceptronSpacer1(new QSpacerItem(100,1, QSizePolicy::Expanding, QSizePolicy::Ignored))
  , m_pPerceptronSpacer2(new QSpacerItem(100,1, QSizePolicy::Expanding, QSizePolicy::Ignored))
  , m_pPerceptronSpacer3(new QSpacerItem(100,1, QSizePolicy::Expanding, QSizePolicy::Ignored))
{
    m_pOutputLabel->setText("77");
    m_pOutputLabel->setStyleSheet("QPushButton {"
                                "background-color: lightgreen;"
                                "border-style: solid;"
                                "border-width:3px;"
                                "border-radius:50px;"
                                "border-color: black;"
                                "max-width:100px;"
                                "max-height:100px;"
                                "min-width:100px;"
                                "min-height:100px;"
                                  "}");

    m_pPerceptronHLayout->addWidget(m_pInputLabel);
    m_pInputLabel->setProperty("index","0");

    m_pPerceptronHLayout->addWidget(m_pInputSpinBox);

    m_pWeightBoxLayout->addSpacerItem(m_pPerceptronSpacer1);
    m_pWeightBoxLayout->addSpacerItem(m_pPerceptronSpacer2);
    m_pPerceptronHLayout->addLayout(m_pWeightBoxLayout);
    m_VecWeightBoxLayouts.push_back(m_pWeightBoxLayout);
    m_Input2WeightBoxLayouts_HashMap["0"] = m_VecWeightBoxLayouts;
    m_pPerceptronHLayout->addWidget(m_pOutputLabel);
    m_pPerceptronHLayout->addSpacerItem(m_pPerceptronSpacer3);

    m_pPerceptronVLayout->addLayout(m_pPerceptronHLayout);
    this->setLayout(m_pPerceptronVLayout);
    m_pInputLabel->setMouseTracking(true);
    installEventFilter(this);

    m_pPerceptronConnectors->m_pConnectorsVLayout->addWidget(m_pPerceptronConnector);

    m_pPerceptronConnectors->setVisible(false);
}

bool PerceptronWidget::eventFilter(QObject* object, QEvent* event)
{

  switch (event->type())
  {
    case (QEvent::Enter):
    {
      qDebug() << "PerceptronWidget Enter Event";
      m_pPerceptronConnectors->setGeometry(m_pInputLabel->geometry().x(), m_pInputLabel->geometry().y() + m_pInputLabel->geometry().height() + 10, 200, 140);
      qDebug() << "ip label x = " << m_pInputLabel->geometry().x();
      qDebug() << "ip label y = " << m_pInputLabel->geometry().y();
      m_pPerceptronConnectors->show();
      break;
    }
    case (QEvent::Leave):
    {
      qDebug() << "PerceptronWidget Leave Event";
      m_pPerceptronConnectors->hide();
      break;
    }
    case (QEvent::ToolTip):
    {
    }
    default:
    {
      //qDebug() << "PerceptronWidget default Event";
    }

  }

  return true;
}


PerceptronWidget::~PerceptronWidget()
{
  delete m_pOutputLabel;
  delete m_pPerceptronHLayout;
  delete m_pInputLabel;
  delete m_pInputSpinBox;
  delete m_pWeightLabel;
  delete m_pWeightSpinBox;
  delete m_pPerceptronSpacer1;
  delete m_pPerceptronSpacer2;
  delete m_pPerceptronSpacer3;
}
