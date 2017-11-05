#include "perceptronmainwindow.h"

PerceptronMainWindow::PerceptronMainWindow(QWidget *parent) : QWidget(parent)
{
    m_MainWindowHToolBarLayout.addWidget(new QLabel("   Perceptron Main Window    "));
    m_MainWindowHToolBarLayout.addWidget(new QLabel("Count = "));
    m_pQSpinBoxCount = new QSpinBox();
    m_MainWindowHToolBarLayout.addWidget(m_pQSpinBoxCount);
    m_MainWindowVLayout.addLayout(&m_MainWindowHToolBarLayout);

}

void PerceptronMainWindow::addPerceptronWidget(PerceptronWidget& pWidget)
{
    m_VecPerceptronWidgets.push_back(&pWidget);
    m_MainWindowVLayout.addLayout(&pWidget.getBoxLayout());
    this->setLayout(&m_MainWindowVLayout);

    //Controller Connections
    connect((m_pQSpinBoxCount), SIGNAL(valueChanged(int)),&pWidget,SLOT(sltCreateInputWidgets(int)));
}
