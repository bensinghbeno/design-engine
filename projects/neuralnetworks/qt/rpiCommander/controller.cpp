#include "controller.h"

Controller::Controller(LogicModel& logicModel, MainWindow& mainWindow, QObject *parent) : QObject(parent)
  , m_LogicModel(logicModel)
  , m_MainWindow(mainWindow)
{
    connect(m_MainWindow.ui->FORWARD,SIGNAL(pressed()),&m_LogicModel,SLOT(sltSendCommand()));
    connect(m_MainWindow.ui->REVERSE,SIGNAL(pressed()),&m_LogicModel,SLOT(sltSendCommand()));
    connect(m_MainWindow.ui->LEFT,SIGNAL(pressed()),&m_LogicModel,SLOT(sltSendCommand()));
    connect(m_MainWindow.ui->RIGHT,SIGNAL(pressed()),&m_LogicModel,SLOT(sltSendCommand()));
    connect(m_MainWindow.ui->STOP,SIGNAL(pressed()),&m_LogicModel,SLOT(sltSendCommand()));
}

