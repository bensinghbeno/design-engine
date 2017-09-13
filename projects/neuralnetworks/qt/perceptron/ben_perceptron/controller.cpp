#include "controller.h"
#include "ui_mainwindow.h"


Controller::Controller(QObject *parent, DataModel *aDataModel, MainWindow *aMainWindow)
  : QObject(parent)
  , m_pDataModel(aDataModel)
  , m_pMainWindow(aMainWindow)
{
  //TBM Add interfaces & protect ui
  connect(m_pMainWindow->ui->spinBox,SIGNAL(valueChanged(int)),m_pDataModel,SLOT(OnPerceptronCountSet(int)));

}

