#include "mainwindow.h"
#include <QApplication>
#include <QtGui>
#include "perceptronoutputwidget.h"
#include "datamodel.h"
#include "controller.h"



int main(int argc, char *argv[])
{
  QApplication a(argc, argv);

  MainWindow w;
  w.show();

  DataModel   perceptronDataModel;

  Controller  perceptronController(0, &perceptronDataModel, &w);


  return a.exec();
}
