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
    this->setLayout(&m_layoutVboxMain);
}

void PerceptronWidget::createControllerConnections()
{
    //Controller Connections
    connect((&m_SpinBoxRowCount), SIGNAL(valueChanged(int)),this,SLOT(sltCreateInputWidgets(int)));
}

void PerceptronWidget::initializeUI(int rowcount, QString layername)
{
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

    m_SpinBoxRowCount.setMaximumWidth(70);
    m_SpinBoxRowCount.setValue(rowcount);
    m_SpinBoxRowCount.setFocus();
    m_labelLayerName.setText(layername);
}

void PerceptronWidget::sltCreateInputWidgets(int rows)
{
    cleanupLayerWidgets();
    list.clear();

    for(int it = 0; it < rows; it++)
    {
        QSpinBox* pSpinBox = new QSpinBox();
        m_VecSpinBoxInputs.push_back(pSpinBox);
        m_layoutgridLayer.addWidget(pSpinBox,it, 0);
        pSpinBox->setMaximumWidth(50);

        QPushButton* pbtnOutput = new QPushButton();
        m_vecbtnOutputs.push_back(pbtnOutput);
        m_layoutgridLayer.addWidget(pbtnOutput,it, 1);
        pbtnOutput->setText("77");
        pbtnOutput->setStyleSheet(m_strOutputLabelStylesheet);

        addWidgets(pSpinBox, pbtnOutput);

    }
    m_layoutgridLayer.setColumnMinimumWidth(0,100);
}


QVBoxLayout& PerceptronWidget::getMainLayout()
{
    return m_layoutVboxMain;
}

void PerceptronWidget::addWidgets(const QWidget * from, const QWidget * to)
{
    list.append(WidgetsConnected{from , to});
    update();
}

void PerceptronWidget::paintEvent(QPaintEvent *event)
{
    qDebug() << "PerceptronWidget::paintEvent()";
//    QPainter painter(this);



//        auto from = m_VecSpinBoxInputs.at(0);
//        auto to = m_vecbtnOutputs.at(0);

//        QPoint start =  from->mapToGlobal(from->rect().topRight() +  QPoint(0, from->height()/2));
//        QPoint end = to->mapToGlobal(to->rect().topLeft() +  QPoint(0, to->height()/2));

//        painter.drawLine(mapFromGlobal(start), mapFromGlobal(end));

    QPainter painter(this);
    for(const WidgetsConnected el: list){
        const QWidget* from = el.from;
        const QWidget* to = el.to;

        QPoint start =  from->mapToGlobal(from->rect().topRight() +  QPoint(0, from->height()/2));
        QPoint end = to->mapToGlobal(to->rect().topLeft() +  QPoint(0, to->height()/2));

        painter.drawLine(mapFromGlobal(start), mapFromGlobal(end));
    }

}



inline void PerceptronWidget::cleanupLayerWidgets()
{
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

    cleanupLayerWidgets();

}
