#include "perceptronwidget.h"

PerceptronWidget::PerceptronWidget(QWidget *parent)
    : QWidget(parent)
    , mRowSize(0)
{    
}


void PerceptronWidget::createLayout()
{
    m_layoutHboxMenu.addWidget(&m_SpinBoxRowCount);
    m_layoutHboxMenu.addWidget(&m_labelLayerName);

    m_layoutVboxMain.addLayout(&m_layoutHboxMenu);
    m_layoutVboxMain.addLayout(&m_layoutgridLayer);
}

void PerceptronWidget::createControllerConnections()
{
    //Controller Connections
    connect((&m_SpinBoxRowCount), SIGNAL(valueChanged(int)),this,SLOT(sltCreateInputWidgets(int)));
}

void PerceptronWidget::initializeUI(int rowcount, QString layername)
{
    m_SpinBoxRowCount.setValue(rowcount);
    m_labelLayerName.setText(layername);
}

void PerceptronWidget::sltCreateInputWidgets(int rows)
{
    cleanupInputs();

    for(int it = 0; it < rows; it++)
    {
        QSpinBox* pSpinBox = new QSpinBox();
        m_VecSpinBoxInputs.push_back(pSpinBox);
        m_layoutgridLayer.addWidget(pSpinBox,it, 0);
    }

}


QVBoxLayout& PerceptronWidget::getMainLayout()
{
    return m_layoutVboxMain;
}


inline void PerceptronWidget::cleanupInputs()
{
    for (QVector<QSpinBox*>::iterator it = m_VecSpinBoxInputs.begin() ; it != m_VecSpinBoxInputs.end(); ++it)
    {
      delete (*it);
    }
    m_VecSpinBoxInputs.clear();
}

inline void PerceptronWidget::cleanupOutputs()
{

    for (QVector<QLabel*>::iterator it = m_VecLabelOutputs.begin() ; it != m_VecLabelOutputs.end(); ++it)
    {
      delete (*it);
    }
    m_VecLabelOutputs.clear();

}

void PerceptronWidget::PlaceOutputWidgets()
{

}

PerceptronWidget::~PerceptronWidget()
{

    cleanupInputs();
    cleanupOutputs();

}
