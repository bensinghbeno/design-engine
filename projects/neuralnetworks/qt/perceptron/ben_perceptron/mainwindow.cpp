#include "mainwindow.h"
#include "ui_mainwindow.h"
#include <QDebug>

static Ui::MainWindow *s_ui;


MainWindow::MainWindow(QWidget *parent)
  :  QMainWindow(parent)
  ,  ui(new Ui::MainWindow)
{
  ui->setupUi(this);
  s_ui = ui;
  this->setGeometry(600,300,700,1200);
  centralWidget()->setMouseTracking(true);
  addPerceptron(2);
  addPerceptron(3);
}

void MainWindow::addPerceptron(unsigned int aCount)
{
  if (!mVecPerceptronWidgets.empty())
  {
    std::for_each(mVecPerceptronWidgets.begin(), mVecPerceptronWidgets.end(), [](PerceptronWidget* iter)
    {
      s_ui->verticalLayout->removeWidget(iter);
      delete iter;
    });

  }

  mVecPerceptronWidgets.clear();
  for (int i = 1; i <= aCount ; i++)
  {
    PerceptronWidget* perceptronWidget = new PerceptronWidget(this);
    perceptronWidget->setMinimumSize(100,400);
    mVecPerceptronWidgets.push_back(perceptronWidget);
    ui->verticalLayout->addWidget(perceptronWidget);
  }
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
  //TBM remove vector perceptronwidgets
}
