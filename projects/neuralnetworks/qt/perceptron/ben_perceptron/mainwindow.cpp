#include "mainwindow.h"
#include "ui_mainwindow.h"
#include <QDebug>

MainWindow::MainWindow(QWidget *parent)
  :  QMainWindow(parent)
  ,  ui(new Ui::MainWindow)
  ,  m_pPerceptronOutPutWidget(new PerceptronWidget(this))
{
  ui->setupUi(this);
  m_pPerceptronOutPutWidget->setMinimumSize(400,400);
  this->setGeometry(1300,100,900,1000);
  ui->verticalLayout->addWidget(m_pPerceptronOutPutWidget);
  centralWidget()->setMouseTracking(true);
}

bool MainWindow::eventFilter(QObject* object, QEvent* event)
{
    if(event->type() == QEvent::Enter)
    {
        qDebug() << "Mainwindow Event";
    }
    return true;
}

MainWindow::~MainWindow()
{
  delete ui;
  delete m_pPerceptronOutPutWidget;
}
