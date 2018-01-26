#include "perceptronweightwidget.h"
#include "perceptronjsonmodel.h"

PerceptronWeightWidget::PerceptronWeightWidget(PerceptronJsonModel& perceptronJsonModel,QWidget *parent)
      : QWidget(parent)
      , m_PerceptronJsonModel(perceptronJsonModel)
{
    this->setLayout(&m_modelMainHLayout);
    this->setWindowTitle("Perceptron Weights Widget");
}

////////////////////// Main Weight Matrix Creation/////////////////////

void PerceptronWeightWidget::sltCreatePerceptronWeightWidgets()
{
    // Cleanup Existing Weight Widgets
    for(QSpinBox* pSpinBox: m_listWeightWidgets)
    {
        delete(pSpinBox);
    }
    m_listWeightWidgets.clear();


    int masterInputCount   =   m_PerceptronJsonModel.getvalue("MASTERINPUTCOUNT").toInt();
    int layerCount           =   m_PerceptronJsonModel.getvalue("LAYERCOUNT").toInt();

    for(int layernum = 0; layernum < layerCount; layernum++)
    {
        for(int weightcolumn = 0; weightcolumn < masterInputCount; weightcolumn++)
        {
            QGridLayout* playoutgridLayer = new QGridLayout();

            for(int weightrow = 0; weightrow < masterInputCount; weightrow++)
            {

                QSpinBox* pLayerDataSpinBox = new QSpinBox();
                playoutgridLayer->addWidget(pLayerDataSpinBox,weightrow, weightcolumn);
                pLayerDataSpinBox->setMaximumWidth(50);
                pLayerDataSpinBox->setObjectName("L" + QString::number(layernum) + "_W" + QString::number(weightrow) +  QString::number(weightcolumn));
                m_listWeightWidgets.push_back(pLayerDataSpinBox);
            }

            m_modelMainHLayout.addLayout(playoutgridLayer);
        }

    }

    show();
}

