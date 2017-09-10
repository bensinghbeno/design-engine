#include "mainwindow.h"
#include <QApplication>
#include <QtGui>
#include "perceptronoutputwidget.h"


int main(int argc, char *argv[])
{
  QApplication a(argc, argv);
  MainWindow w;


  PerceptronWidget* pPerceptronOutPutWidget = new PerceptronWidget();
  pPerceptronOutPutWidget->setMinimumSize(400,400);

  w.setGeometry(1300,100,900,1000);
  w.setCentralWidget(pPerceptronOutPutWidget);
  w.show();
  return a.exec();
}
