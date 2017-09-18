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
  this->setWindowTitle("Ezra's Perceptron .. !!");
  this->setGeometry(600,300,1200,1200);
  ui->spinBoxPerceptronCount->setStyleSheet("QSpinBox::up-button { width: 32px; height: 40px}"
                                            "QSpinBox::down-button { width: 32px; height: 40px }");
  centralWidget()->setMouseTracking(true);
}

void MainWindow::SltAddPerceptron(int aCount)
{
  qDebug() << "SltAddPerceptron aCount = " << aCount;
  if (!mVecPerceptronWidgets.empty())
  {
    std::for_each(mVecPerceptronWidgets.begin(), mVecPerceptronWidgets.end(), [](PerceptronWidget* iter)
    {
      s_ui->verticalLayout->removeWidget(iter);
      delete iter;
    });

  }

  mVecPerceptronWidgets.clear();
  for (uint i = 1; i <= aCount ; i++)
  {
    PerceptronWidget* perceptronWidget = new PerceptronWidget(this, i);
    perceptronWidget->setMinimumSize(100,400);
    ui->verticalLayout->addWidget(perceptronWidget);
    mVecPerceptronWidgets.push_back(perceptronWidget);
    perceptronWidget->show();
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
