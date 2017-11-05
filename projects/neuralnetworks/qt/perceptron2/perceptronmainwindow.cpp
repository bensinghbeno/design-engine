#include "perceptronmainwindow.h"

PerceptronMainWindow::PerceptronMainWindow(QWidget *parent) : QWidget(parent)
{

}

void PerceptronMainWindow::addPerceptronWidget(PerceptronWidget& pWidget)
{
    m_VecPerceptronWidgets.push_back(&pWidget);
    m_MainWindowVLayout.addLayout(&pWidget.getBoxLayout());
    this->setLayout(&m_MainWindowVLayout);
}


