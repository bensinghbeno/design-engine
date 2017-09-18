#include "controller.h"
#include "ui_mainwindow.h"


Controller::Controller(QObject *parent, DataModel *aDataModel, MainWindow *aMainWindow)
  : QObject(parent)
  , m_pDataModel(aDataModel)
  , m_pMainWindow(aMainWindow)
{
  //TBM Add interfaces & protect ui
  connect(m_pMainWindow->ui->spinBoxPerceptronCount,SIGNAL(valueChanged(int)),m_pDataModel,SLOT(SltOnPerceptronCountSet(int)));
  connect(m_pDataModel,SIGNAL(SgnOnPerceptronCountChanged(int)),m_pMainWindow,SLOT(SltAddPerceptron(int)));
  connect(m_pMainWindow,SIGNAL(SigInputSet(int,int)),m_pDataModel,SLOT(SltOnPerceptronInputSet(int,int)));
  connect(m_pDataModel,SIGNAL(SgnPerceptronOutPutChanged(int,int)),m_pMainWindow,SLOT(SltPerceptronOutputSet(int,int)));
}

