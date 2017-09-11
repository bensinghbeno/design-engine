#include "mainwindow.h"
#include "ui_mainwindow.h"
#include <QDebug>

MainWindow::MainWindow(QWidget *parent)
  :  QMainWindow(parent)
  ,  ui(new Ui::MainWindow)
  ,  m_pPerceptronOutPutWidget(new PerceptronWidget(parent))
{
  ui->setupUi(this);
  m_pPerceptronOutPutWidget->setMinimumSize(400,400);
  this->setGeometry(1300,100,900,1000);
  this->setCentralWidget(m_pPerceptronOutPutWidget);
}

MainWindow::~MainWindow()
{
  delete ui;
  delete m_pPerceptronOutPutWidget;
}
