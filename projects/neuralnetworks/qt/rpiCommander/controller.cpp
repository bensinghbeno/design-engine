#include "controller.h"

Controller::Controller(LogicModel& logicModel, MainWindow& mainWindow, QObject *parent) : QObject(parent)
  , m_LogicModel(logicModel)
  , m_MainWindow(mainWindow)
{
    connect(m_MainWindow.ui->F,SIGNAL(pressed()),&m_LogicModel,SLOT(sltSendCommand()));
    connect(m_MainWindow.ui->B,SIGNAL(pressed()),&m_LogicModel,SLOT(sltSendCommand()));
    connect(m_MainWindow.ui->L,SIGNAL(pressed()),&m_LogicModel,SLOT(sltSendCommand()));
    connect(m_MainWindow.ui->R,SIGNAL(pressed()),&m_LogicModel,SLOT(sltSendCommand()));
    connect(m_MainWindow.ui->S,SIGNAL(pressed()),&m_LogicModel,SLOT(sltSendCommand()));
    connect(m_MainWindow.ui->G,SIGNAL(pressed()),&m_LogicModel,SLOT(sltSendCommand()));
    connect(m_MainWindow.ui->r,SIGNAL(pressed()),&m_LogicModel,SLOT(sltSendCommand()));
    connect(m_MainWindow.ui->T,SIGNAL(pressed()),&m_LogicModel,SLOT(sltSendCommand()));
    connect(m_MainWindow.ui->f,SIGNAL(pressed()),&m_LogicModel,SLOT(sltSendCommand()));

    connect(m_MainWindow.ui->F,SIGNAL(released()),&m_LogicModel,SLOT(sltStopSendCommand()));
    connect(m_MainWindow.ui->B,SIGNAL(released()),&m_LogicModel,SLOT(sltStopSendCommand()));
    connect(m_MainWindow.ui->L,SIGNAL(released()),&m_LogicModel,SLOT(sltStopSendCommand()));
    connect(m_MainWindow.ui->R,SIGNAL(released()),&m_LogicModel,SLOT(sltStopSendCommand()));
    connect(m_MainWindow.ui->S,SIGNAL(released()),&m_LogicModel,SLOT(sltStopSendCommand()));
    connect(m_MainWindow.ui->G,SIGNAL(released()),&m_LogicModel,SLOT(sltStopSendCommand()));
    connect(m_MainWindow.ui->r,SIGNAL(released()),&m_LogicModel,SLOT(sltStopSendCommand()));
    connect(m_MainWindow.ui->T,SIGNAL(released()),&m_LogicModel,SLOT(sltStopSendCommand()));
    connect(m_MainWindow.ui->f,SIGNAL(released()),&m_LogicModel,SLOT(sltStopSendCommand()));
}
