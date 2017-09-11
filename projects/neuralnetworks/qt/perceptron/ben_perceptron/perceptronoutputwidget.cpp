#include "perceptronoutputwidget.h"

PerceptronWidget::PerceptronWidget(QWidget *parent)
  : QWidget(parent)
  , m_pOutputLabel(new QPushButton(parent))
  , m_pPerceptronLayout(new QHBoxLayout())
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

    m_pPerceptronLayout->addWidget(m_pInputLabel);
    m_pInputLabel->setProperty("index","0");

    m_pPerceptronLayout->addWidget(m_pInputSpinBox);

    m_pWeightBoxLayout->addSpacerItem(m_pPerceptronSpacer1);
    m_pWeightBoxLayout->addWidget(m_pWeightLabel);
    m_pWeightBoxLayout->addWidget(m_pWeightSpinBox);
    m_pWeightBoxLayout->addSpacerItem(m_pPerceptronSpacer2);
    m_pPerceptronLayout->addLayout(m_pWeightBoxLayout);
    m_VecWeightBoxLayouts.push_back(m_pWeightBoxLayout);
    m_Input2WeightBoxLayouts_HashMap["0"] = m_VecWeightBoxLayouts;

    m_pPerceptronLayout->addWidget(m_pOutputLabel);
    m_pPerceptronLayout->addSpacerItem(m_pPerceptronSpacer3);
    this->setLayout(m_pPerceptronLayout);
    m_pInputLabel->setMouseTracking(true);
    installEventFilter(m_pInputLabel);
}

bool PerceptronWidget::eventFilter(QObject* object, QEvent* event)
{
    if(event->type() == QEvent::Enter)
    {
        //QMouseEvent *mEvent = (QMouseEvent*)event;
        qDebug() << "PerceptronWidget Event";
    }
    return true;
}


PerceptronWidget::~PerceptronWidget()
{
  delete m_pOutputLabel;
  delete m_pPerceptronLayout;
  delete m_pInputLabel;
  delete m_pInputSpinBox;
  delete m_pWeightLabel;
  delete m_pWeightSpinBox;
  delete m_pPerceptronSpacer1;
  delete m_pPerceptronSpacer2;
  delete m_pPerceptronSpacer3;
}
