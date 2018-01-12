#include "perceptronweightwidget.h"

PerceptronWeightWidget::PerceptronWeightWidget(QWidget *parent) : QWidget(parent)
{
    for(int layercolumn = 0; layercolumn < 3; layercolumn++)
    {
        QGridLayout* playoutgridLayer = new QGridLayout();

        for(int inputrow = 0; inputrow < 3; inputrow++)
        {
            QSpinBox* pLayerDataSpinBox = new QSpinBox();
            playoutgridLayer->addWidget(pLayerDataSpinBox,inputrow, layercolumn);
            pLayerDataSpinBox->setMaximumWidth(50);
            pLayerDataSpinBox->setObjectName("SB_" + QString::number(inputrow) +  QString::number(layercolumn));
            //layerwidget->append(pPushButton);
        }

        m_modelMainHLayout.addLayout(playoutgridLayer);

        //m_listLayerOutputWidgets.push_back(layerwidget);
    }

    this->setLayout(&m_modelMainHLayout);
    this->show();
    this->setWindowTitle("Perceptron Weights Widget");
}

