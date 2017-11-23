#include "perceptronwidget.h"

PerceptronWidget::PerceptronWidget(QWidget *parent)
    : QWidget(parent)
    , mRowSize(0)
{
}

void PerceptronWidget::initializeOutputLabelPainter()
{
    m_PixmapLayerOutputLabels = new QPixmap(45,45);
    m_PixmapLayerOutputLabels->fill(Qt::transparent);

    m_PainterLayerOutputLabels = new QPainter(m_PixmapLayerOutputLabels);
    m_PainterLayerOutputLabels->setRenderHint(QPainter::Antialiasing, true);

    m_PenLabelOutputLabels = new QPen(Qt::blue, 2);
    m_PainterLayerOutputLabels->setPen(*m_PenLabelOutputLabels);

    m_brushLayerOutputLabels = new QBrush(Qt::green);
    m_PainterLayerOutputLabels->setBrush(*m_brushLayerOutputLabels);
    m_PainterLayerOutputLabels->drawEllipse(10, 10, 30, 30);
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
    initializeOutputLabelPainter();

    m_SpinBoxRowCount.setMaximumWidth(70);
    m_SpinBoxRowCount.setValue(rowcount);
    m_labelLayerName.setText(layername);
}

void PerceptronWidget::sltCreateInputWidgets(int rows)
{
    cleanupLayerWidgets();

    for(int it = 0; it < rows; it++)
    {
        QSpinBox* pSpinBox = new QSpinBox();
        m_VecSpinBoxInputs.push_back(pSpinBox);
        m_layoutgridLayer.addWidget(pSpinBox,it, 0);
        pSpinBox->setMaximumWidth(50);

        QLabel* pLabelOutput = new QLabel("00");
        m_VecLabelOutputs.push_back(pLabelOutput);
        m_layoutgridLayer.addWidget(pLabelOutput,it, 1);
        pLabelOutput->setPixmap(*m_PixmapLayerOutputLabels);


    }
    m_layoutgridLayer.setColumnMinimumWidth(0,100);
}


QVBoxLayout& PerceptronWidget::getMainLayout()
{
    return m_layoutVboxMain;
}


inline void PerceptronWidget::cleanupLayerWidgets()
{
    for (QVector<QSpinBox*>::iterator it = m_VecSpinBoxInputs.begin() ; it != m_VecSpinBoxInputs.end(); ++it)
    {
        delete (*it);
    }
    m_VecSpinBoxInputs.clear();

    for (QVector<QLabel*>::iterator it = m_VecLabelOutputs.begin() ; it != m_VecLabelOutputs.end(); ++it)
    {
        delete (*it);
    }
    m_VecLabelOutputs.clear();
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

    cleanupLayerWidgets();
    cleanupOutputs();

}
