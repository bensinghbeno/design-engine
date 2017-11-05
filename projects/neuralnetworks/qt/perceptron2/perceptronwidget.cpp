#include "perceptronwidget.h"

PerceptronWidget::PerceptronWidget(int rows, QWidget *parent)
    : QWidget(parent)
    , mRowSize(rows)
{
    //m_VecLabelOutputs = new QVector<QLabel>(2);
    createInputWidgets(mRowSize);


}

void PerceptronWidget::createInputWidgets(int rows)
{
    for(int it = 0; it < rows; it++)
    {
        QSpinBox* pSpinBox = new QSpinBox();
        m_VecSpinBoxInputs.push_back(pSpinBox);
        m_PerceptronGridLayout.addWidget(pSpinBox,it, 0);
    }

    this->setLayout(&m_PerceptronGridLayout);

}

QGridLayout& PerceptronWidget::getBoxLayout()
{
    return m_PerceptronGridLayout;
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
