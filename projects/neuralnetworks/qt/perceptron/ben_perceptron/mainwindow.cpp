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
//  QHBoxLayout* lay2 = new QHBoxLayout();
//  QVBoxLayout* lay = new QVBoxLayout();
//  QPushButton* btn1 = new QPushButton("btn1");
//  QPushButton* btn2 = new QPushButton("btn1");
//  lay2->addWidget(m_pPerceptronOutPutWidget);
//  lay1->addWidget(btn1);
//  lay1->addWidget(btn2);
//  lay->addLayout(lay1);
//  lay->addLayout(lay2);
  this->setCentralWidget(m_pPerceptronOutPutWidget);
  centralWidget()->setMouseTracking(true);
  //installEventFilter(m_pPerceptronOutPutWidget->getInputLabel());
}

bool MainWindow::eventFilter(QObject* object, QEvent* event)
{
    if(event->type() == QEvent::Enter)
    {
        //QMouseEvent *mEvent = (QMouseEvent*)event;
        qDebug() << "Mainwindow Event";
    }
    return true;
}

MainWindow::~MainWindow()
{
  delete ui;
  delete m_pPerceptronOutPutWidget;
}
