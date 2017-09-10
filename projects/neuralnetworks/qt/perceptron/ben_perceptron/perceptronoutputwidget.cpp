#include "perceptronoutputwidget.h"

PerceptronWidget::PerceptronWidget(QWidget *parent)
  : QWidget(parent)
{
    qDebug() << "PerceptronOutPutWidget()";
    m_pOutputLabel = new QPushButton();
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

    QHBoxLayout* pPerceptronLayout = new QHBoxLayout();
    QLabel* pInputLabel = new QLabel("Input_1");
    QSpinBox* pInputBox = new QSpinBox();
    QLabel* WeightLabel= new QLabel("Weight_1");
    QSpinBox* pWeightBox = new QSpinBox();


    QSpacerItem* pPerceptronSpacer1 = new QSpacerItem(100,1, QSizePolicy::Expanding, QSizePolicy::Ignored);
    QSpacerItem* pPerceptronSpacer2 = new QSpacerItem(100,1, QSizePolicy::Expanding, QSizePolicy::Ignored);
    QSpacerItem* pPerceptronSpacer3 = new QSpacerItem(100,1, QSizePolicy::Expanding, QSizePolicy::Ignored);
    pPerceptronLayout->addWidget(pInputLabel);
    pPerceptronLayout->addWidget(pInputBox);
    pPerceptronLayout->addSpacerItem(pPerceptronSpacer1);
    pPerceptronLayout->addWidget(WeightLabel);
    pPerceptronLayout->addWidget(pWeightBox);
    pPerceptronLayout->addSpacerItem(pPerceptronSpacer2);
    pPerceptronLayout->addWidget(m_pOutputLabel);
    pPerceptronLayout->addSpacerItem(pPerceptronSpacer3);
    this->setLayout(pPerceptronLayout);
}

bool PerceptronWidget::eventFilter(QObject *watched, QEvent *event)
{
}


void PerceptronWidget::paintEvent(QPaintEvent *event)
{
}

