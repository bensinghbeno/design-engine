#include "mainwindow.h"
#include "ui_mainwindow.h"
#include <QDebug>

static Ui::MainWindow *s_ui;
static const char* PropertyIndex = "PropertyIndex"; //TBM

MainWindow::MainWindow(QWidget *parent)
  :  QMainWindow(parent)
  ,  ui(new Ui::MainWindow)
{
  ui->setupUi(this);
  s_ui = ui;
  this->setWindowTitle("Ezra's Perceptron .. !!");
  this->setGeometry(600,300,600,700);
  ui->spinBoxPerceptronCount->setStyleSheet("QSpinBox::up-button { width: 32px; height: 40px}"
                                            "QSpinBox::down-button { width: 32px; height: 40px }");
  centralWidget()->setMouseTracking(true);
}

void MainWindow::SltInputSet(int aInputVal)
{
  //qDebug() << "SltInputSet , PropertyIndex = " << sender()->property(PropertyIndex) << " aInputVal = " << aInputVal;
  QVariant index = sender()->property(PropertyIndex);
  emit SigInputSet(index.toString().toInt(), aInputVal);
}

void MainWindow::SltPerceptronOutputSet(int aIndex, int aOutputVal)
{
   mVecPerceptronWidgets[aIndex]->m_pOutputLabel->setText(QString::number(aOutputVal));
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
  for (uint i = 0; i < aCount ; i++)
  {
    PerceptronWidget* perceptronWidget = new PerceptronWidget(this, i);
    perceptronWidget->setMinimumSize(100,150);
    ui->verticalLayout->addWidget(perceptronWidget);
    connect(perceptronWidget->m_pInputSpinBox,SIGNAL(valueChanged(int)),this,SLOT(SltInputSet(int)));
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
