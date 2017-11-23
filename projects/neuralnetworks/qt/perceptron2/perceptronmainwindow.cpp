#include "perceptronmainwindow.h"

PerceptronMainWindow::PerceptronMainWindow(QWidget *parent) : QWidget(parent)
{
    m_MainWindowHToolBarLayout.addWidget(new QLabel("   Perceptron Main Window    "));
    m_MainWindowHToolBarLayout.addWidget(new QLabel("Count = "));
    m_pQSpinBoxLayerCount = new QSpinBox();
    m_MainWindowHToolBarLayout.addWidget(m_pQSpinBoxLayerCount);
    m_MainWindowVLayout.addLayout(&m_MainWindowHToolBarLayout);

}

void PerceptronMainWindow::addPerceptronWidget(PerceptronWidget& pWidget)
{
    m_VecPerceptronWidgets.push_back(&pWidget);
    m_MainWindowVLayout.addLayout(&pWidget.getMainLayout());
    this->setLayout(&m_MainWindowVLayout);
}
