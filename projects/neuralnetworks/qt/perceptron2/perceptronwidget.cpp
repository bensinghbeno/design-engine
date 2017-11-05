#include "perceptronwidget.h"

PerceptronWidget::PerceptronWidget(int rows, QWidget *parent)
    : QWidget(parent)
    , mRowSize(rows)
{
    sltCreateInputWidgets(mRowSize);
}

void PerceptronWidget::sltCreateInputWidgets(int rows)
{
    cleanupInputs();

    for(int it = 0; it < rows; it++)
    {
        QSpinBox* pSpinBox = new QSpinBox();
        m_VecSpinBoxInputs.push_back(pSpinBox);
        m_PerceptronGridLayout.addWidget(pSpinBox,it, 0);
    }

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
