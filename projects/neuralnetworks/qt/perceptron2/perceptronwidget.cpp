#include "perceptronwidget.h"

PerceptronWidget::PerceptronWidget(QWidget *parent)
    : QWidget(parent)
    , mRowSize(0)
    , m_magicCount(0)
{}

void PerceptronWidget::createLayerLayout()
{
    //MainToolBox
    m_MainWindowHToolBarLayout.addWidget(new QLabel("   Perceptron Toolbox    "));
    m_MainWindowHToolBarLayout.addWidget(new QLabel("Total Layers = "));
    m_MainWindowHToolBarLayout.addWidget(&m_SpinBoxLayerCount);
    m_layoutVboxMain.addLayout(&m_MainWindowHToolBarLayout);

    m_pFrameLineSepMainToolBox = new QFrame(this);
    m_pFrameLineSepMainToolBox->setFrameShape(QFrame::HLine);
    m_pFrameLineSepMainToolBox->setFrameShadow(QFrame::Sunken);
    m_layoutVboxMain.addWidget(m_pFrameLineSepMainToolBox);

    //LayerToolBox
    m_layoutHboxMenu.addWidget(&m_labelLayerName);
    m_layoutHboxMenu.addWidget(&m_labelMagicCount);
    m_layoutHboxMenu.addWidget(&m_sbLayerMagicCount);
    m_layoutHboxMenu.addWidget(&m_labelInputCount);
    m_layoutHboxMenu.addWidget(&m_sbLayerInputCount);
    m_layoutHboxMenu.addWidget(&m_labelOutputCount);
    m_layoutHboxMenu.addWidget(&m_sbLayerOutputCount);

    m_pSpacerLayerToolBox = new QSpacerItem(100,50);
    m_layoutHboxMenu.addSpacerItem(m_pSpacerLayerToolBox);

    m_layoutVboxMain.addLayout(&m_layoutHboxMenu);
    m_layoutVboxMain.addLayout(&m_LayersHLayout);
    m_LayersHLayout.addLayout(&m_layoutgridLayer);

    this->setLayout(&m_layoutVboxMain);
}

void PerceptronWidget::createMasterLayout()
{
    createLayerLayout();

    mp_pbMasterOutput = new QPushButton();
    m_LayersHLayout.addWidget(mp_pbMasterOutput);
}


void PerceptronWidget::createControllerConnections()
{
    connect((&m_sbLayerInputCount), SIGNAL(valueChanged(int)),this,SLOT(sltCreateInputWidgets()));
    connect((&m_sbLayerOutputCount), SIGNAL(valueChanged(int)),this,SLOT(sltCreateInputWidgets()));
    connect((&m_sbLayerMagicCount), SIGNAL(valueChanged(int)),this,SLOT(sltCreatePerceptronMagicWidgets(int)));
}

void PerceptronWidget::initializeUI(int rowcount)
{
    QString layername = "Layer 1   |   ";
    QString strlayerMagiccount = "Magic Inputs = ";
    QString strlayerInputcount = "Inputs = ";
    QString strlayerOutputcount = "Outputs = ";

    m_strOutputLabelStylesheet = ("QPushButton {"
                                 "background-color: lightgreen;"
                                 "border-style: solid;"
                                 "border-width:3px;"
                                 "border-radius:20px;"
                                 "border-color: black;"
                                 "max-width:40px;"
                                 "max-height:40px;"
                                 "min-width:40px;"
                                 "min-height:40px;"
                                   "}");

    m_sbLayerInputCount.setMaximumWidth(70);
    m_sbLayerInputCount.setValue(rowcount);
    m_labelLayerName.setText(layername);
    m_labelMagicCount.setText(strlayerMagiccount);
    m_labelInputCount.setText(strlayerInputcount);
    m_labelOutputCount.setText(strlayerOutputcount);
    m_sbLayerMagicCount.setFocus();

    mp_pbMasterOutput->setStyleSheet(m_strOutputLabelStylesheet);
    mp_pbMasterOutput->setText("100");
}

void PerceptronWidget::sltCreatePerceptronMagicWidgets(int count)
{
    m_magicCount = count;
    emit sltCreateInputWidgets();
}


void PerceptronWidget::sltCreateInputWidgets()
{
    cleanupDynamicWidgets();

    int inputrows;
    int outputrows;

    if (m_magicCount != 0)
    {
        inputrows = outputrows = m_magicCount;
    }
    else
    {
        inputrows = m_sbLayerInputCount.value();
        outputrows = m_sbLayerOutputCount.value();
    }

    for(int it = 0; it < inputrows; it++)
    {
        QSpinBox* pSpinBox = new QSpinBox();
        m_VecSpinBoxInputs.push_back(pSpinBox);
        m_layoutgridLayer.addWidget(pSpinBox,it, 0);
        pSpinBox->setMaximumWidth(50);
        list_inputs.append(pSpinBox);
    }

    for(int it = 0; it < outputrows; it++)
    {
        QPushButton* pbtnOutput = new QPushButton();
        m_vecbtnOutputs.push_back(pbtnOutput);
        m_layoutgridLayer.addWidget(pbtnOutput,it, 1);
        pbtnOutput->setText("77");
        pbtnOutput->setStyleSheet(m_strOutputLabelStylesheet);
        list_outputs.append(pbtnOutput);
    }

    m_layoutgridLayer.setColumnMinimumWidth(0,100);
    update();
}


void PerceptronWidget::addWidgets(const QWidget * from, const QWidget * to)
{
    list.append(sLayerLineWidgets{from , to});
    update();
}

void PerceptronWidget::paintEvent(QPaintEvent* /*event*/)
{
    qDebug() << "PerceptronWidget::paintEvent()";


    QPainter painter(this);
    for(const QWidget* from: list_inputs)
    {
        for(const QWidget* to: list_outputs)
        {
            QPoint start =  from->mapToGlobal(from->rect().topRight() +  QPoint(0, from->height()/2));
            QPoint end = to->mapToGlobal(to->rect().topLeft() +  QPoint(0, to->height()/2));
            painter.drawLine(mapFromGlobal(start), mapFromGlobal(end));

            QPoint start2 = to->mapToGlobal(to->rect().topRight() +  QPoint(0, to->height()/2));
            QPoint end2 = mp_pbMasterOutput->mapToGlobal(mp_pbMasterOutput->rect().topLeft() +  QPoint(0, to->height()/2));
            painter.drawLine(mapFromGlobal(start2), mapFromGlobal(end2));
        }
    }
}


inline void PerceptronWidget::cleanupDynamicWidgets()
{
    list_inputs.clear();
    list_outputs.clear();

    for (QVector<QSpinBox*>::iterator it = m_VecSpinBoxInputs.begin() ; it != m_VecSpinBoxInputs.end(); ++it)
    {
        delete (*it);
    }
    m_VecSpinBoxInputs.clear();

    for (QVector<QPushButton*>::iterator it = m_vecbtnOutputs.begin() ; it != m_vecbtnOutputs.end(); ++it)
    {
        delete (*it);
    }
    m_vecbtnOutputs.clear();
}


void PerceptronWidget::PlaceOutputWidgets()
{

}

PerceptronWidget::~PerceptronWidget()
{

    cleanupDynamicWidgets();

}
